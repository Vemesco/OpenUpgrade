# Copyright 2020 Andrii Skrypka
# Copyright 2020 Opener B.V. (stefan@opener.amsterdam)
# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# Copyright 2020 ForgeFlow
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


@openupgrade.migrate()
def migrate(env, version):
    fix_double_membership(env.cr)
