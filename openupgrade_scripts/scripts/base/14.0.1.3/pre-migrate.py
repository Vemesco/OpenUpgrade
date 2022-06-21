# Copyright 2020 Odoo Community Association (OCA)
# Copyright 2020 Opener B.V. <stefan@opener.am>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from openupgradelib import openupgrade

from odoo import tools

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.openupgrade_scripts.apriori import merged_modules, renamed_modules
except ImportError:
    renamed_modules = {}

    merged_modules = {}

    _logger.warning(
        "You are using openupgrade_framework without having"
        " openupgrade_scripts module available."
        " The upgrade process will not work properly."
    )

module_category_xmlid_renames = [
    # Module category renames were not detected by the analyze. These records
    # are created on the fly when initializing a new database in
    # odoo/modules/db.py
    (
        "base.module_category_accounting_expenses",
        "base.module_category_human_resources_expenses",
    ),
    ("base.module_category_discuss", "base.module_category_productivity_discuss"),
    (
        "base.module_category_localization",
        "base.module_category_accounting_localizations",
    ),
    (
        "base.module_category_localization_account_charts",
        "base.module_category_accounting_localizations_account_charts",
    ),
    ("base.module_category_marketing_survey", "base.module_category_marketing_surveys"),
    (
        "base.module_category_operations_helpdesk",
        "base.module_category_services_helpdesk",
    ),
    (
        "base.module_category_operations_inventory",
        "base.module_category_inventory_inventory",
    ),
    (
        "base.module_category_operations_inventory_delivery",
        "base.module_category_inventory_delivery",
    ),
    (
        "base.module_category_operations_maintenance",
        "base.module_category_manufacturing_maintenance",
    ),
    (
        "base.module_category_operations_project",
        "base.module_category_services_project",
    ),
    (
        "base.module_category_operations_purchase",
        "base.module_category_inventory_purchase",
    ),
    (
        "base.module_category_operations_timesheets",
        "base.module_category_services_timesheets",
    ),
]


def deduplicate_ir_properties(cr):
    # delete duplicates in ir_property due to new constrain
    # see https://github.com/odoo/odoo/commit/e85faf398659a5beb0b1570a06af64dcf78dc1c8
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM ir_property
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, row_number() over (
                    partition BY fields_id, company_id, res_id ORDER BY id DESC) AS rnum
                FROM ir_property
            ) t
            WHERE t.rnum > 1)""",
    )


def fix_double_membership(cr):
    # avoid error raised by new function '_check_one_user_type'

    # assuming that group_public < group_portal < group_user
    # this script keept the highest group, if a user belong to many
    # groups
    confs = [
        ("group_public", "group_portal"),
        ("group_public", "group_user"),
        ("group_portal", "group_user"),
    ]
    for conf in confs:
        group_to_remove = conf[0]
        group_to_keep = conf[1]
        openupgrade.logged_query(
            cr, """
                DELETE FROM res_groups_users_rel
                WHERE
                gid = (
                    SELECT res_id
                    FROM ir_model_data
                    WHERE module = 'base' AND name = %s
                )
                AND uid IN (
                    SELECT uid FROM res_groups_users_rel WHERE gid IN (
                        SELECT res_id
                        FROM ir_model_data
                        WHERE module = 'base'
                        AND name IN (%s, %s)
                    )
                    GROUP BY uid
                    HAVING count(*) > 1
                );
            """, (group_to_remove, group_to_remove, group_to_keep)
        )

    # Add features to remove relation
    openupgrade.logged_query(
        cr, """
            DELETE FROM res_groups_users_rel
                    where uid IN (
                    SELECT uid FROM res_groups_users_rel WHERE gid IN (
                        SELECT res_id
                        FROM ir_model_data
                        WHERE module = 'base'
                        AND name = 'group_public')
                        );
                """,
    )


@openupgrade.migrate(use_env=False)
def migrate(cr, version):
    """
    Don't request an env for the base pre migration as flushing the env in
    odoo/modules/registry.py will break on the 'base' module not yet having
    been instantiated.
    """
    if "openupgrade_framework" not in tools.config["server_wide_modules"]:
        logging.error(
            "openupgrade_framework is not preloaded. You are highly "
            "recommended to run the Odoo with --load=openupgrade_framework "
            "when migrating your database."
        )
    # Rename xmlids of module categories with allow_merge
    openupgrade.rename_xmlids(cr, module_category_xmlid_renames, allow_merge=True)
    # Update ir_model_data timestamps from obsolete columns
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_model_data
        SET create_date = COALESCE(date_init, create_date),
            write_date = COALESCE(date_update, write_date)
        WHERE (create_date IS NULL OR write_date IS NULL) AND
            (date_init IS NOT NULL OR date_update IS NOT NULL)
        """,
    )
    # Set default values from odoo/addons/base/data/base_data.sql
    cr.execute(
        """ ALTER TABLE ir_model_data
        ALTER COLUMN create_date
        SET DEFAULT NOW() AT TIME ZONE 'UTC',
        ALTER COLUMN write_date
        SET DEFAULT NOW() AT TIME ZONE 'UTC'
    """
    )
    # Perform module renames and merges
    openupgrade.update_module_names(cr, renamed_modules.items())
    openupgrade.update_module_names(cr, merged_modules.items(), merge_modules=True)
    # Migrate partners from Fil to Tagalog
    # See https://github.com/odoo/odoo/commit/194ed76c5cc9
    openupgrade.logged_query(
        cr, "UPDATE res_partner SET lang = 'tl_PH' WHERE lang = 'fil_PH'"
    )
    deduplicate_ir_properties(cr)
    fix_double_membership(cr)
