from odoo import models, fields, api
class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    project_detail_id = fields.Many2one('account.analytic.account', string="Project")