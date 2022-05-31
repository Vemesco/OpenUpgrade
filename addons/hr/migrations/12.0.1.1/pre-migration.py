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
    users = env['res.users'].search([], order='id asc')
    for user in users:
        if user.has_group('base.group_user') and (
                user.has_group('base.group_private_addresses')
        ):
            _logger.warning('Conflict in user groups: %s' % user.name)
            user.write({'groups_id': [
                (3, env.ref('base.group_private_addresses').id),
            ]})

@openupgrade.migrate()
def migrate(env, version):
    fix_users_belong_two_groups(env)
    if openupgrade.column_exists(env.cr, 'hr_employee', 'vehicle_distance'):
        openupgrade.rename_fields(env, _field_renames)
    openupgrade.rename_xmlids(env.cr, xmlid_renames)
    
