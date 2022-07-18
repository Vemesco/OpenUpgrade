# Copyright 2021 ForgeFlow S.L.  <https://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


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


@openupgrade.migrate()
def migrate(env, version):
    """Call disable_invalid_filters in every edition of openupgrade"""
    openupgrade.disable_invalid_filters(env)
    # web_diagram has been remove in V14
    # we merge into web, if no diagram are present, to avoid to
    # have to uninstall the module manually
    if not env["ir.ui.view"].search([("type", "=", "diagram")]):
        openupgrade.update_module_names(
            env.cr, [("web_diagram", "web")], merge_modules=True
        )

    fix_double_membership(env.cr)
