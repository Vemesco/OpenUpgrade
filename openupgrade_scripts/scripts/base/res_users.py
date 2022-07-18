from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.constrains('groups_id')
    def _check_one_user_type(self):
        print('_check_one_user_type')
