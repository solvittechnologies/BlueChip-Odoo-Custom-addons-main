from odoo import models,fields,api

class AccountInherit(models.Model):
    _inherit = 'account.account'

    active = fields.Boolean("Active", default=True)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'


    def test(self):
        all_data = self.search([])
        if all_data:
            for data in all_data:
                try:
                    data.unlink()
                except:
                    pass
