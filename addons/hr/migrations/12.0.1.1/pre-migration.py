# Copyright 2019 Eficent <http://www.eficent.com>
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
import logging

_logger = logging.getLogger(__name__)

_field_renames = [
    ('hr.employee', 'hr_employee', 'vehicle_distance', 'km_home_work'),
]

xmlid_renames = [
    ('hr.employee_root', 'hr.employee_admin'),
]


def fix_users_belong_two_groups(env):
    _logger.info('Fixing users with conflicting groups')
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
            env.cr, """
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


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, 'hr_employee', 'vehicle_distance'):
        openupgrade.rename_fields(env, _field_renames)
    openupgrade.rename_xmlids(env.cr, xmlid_renames)
    fix_users_belong_two_groups(env)
