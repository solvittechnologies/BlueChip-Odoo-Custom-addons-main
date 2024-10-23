# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice.line'

    po_number_id = fields.Many2one('account.analytic.account',string="Po Number", domain=[('is_customer_po','=',True)])

