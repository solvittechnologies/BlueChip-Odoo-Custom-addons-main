# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductInvoice(models.Model):
    _inherit = 'account.invoice'

    total_amount_in_words_invoice = fields.Char("Total amount in words", compute='compute_total_amount_in_word_invoice')
    signechar_1 = fields.Binary("Signechar")
    signechar_2 = fields.Binary("Signechar")
    signechar_3 = fields.Binary("Signechar")


    @api.depends('amount_total')
    def compute_total_amount_in_word_invoice(self):
        for order in self:
            order.total_amount_in_words_invoice = order.currency_id.amount_to_text(order.amount_total)