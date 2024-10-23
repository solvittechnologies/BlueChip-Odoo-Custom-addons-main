# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    tin_no = fields.Char("Tin No")


    # Bank information
    sort_code = fields.Char('Sort Code')
    bank_name = fields.Char('Bank Name')
    bank_address = fields.Char('Bank Address')
    account_name = fields.Char('Account Name')
    account_no = fields.Char('Account No')
