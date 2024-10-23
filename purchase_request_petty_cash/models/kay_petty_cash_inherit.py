# -*- coding: utf-8 -*-

from datetime import datetime

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('validate', 'Validated'),
    ('posted', 'Posted'),
    ('done', 'Done'),
    ('rejected', 'Rejected'),
    ('closed', 'Closed'),
]


class Kay_petty_cash(models.Model):
    _name = "kay.petty.cash"
    _inherit = ['kay.petty.cash', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(selection=_STATES, default='draft')
    custodian = fields.Many2one('res.users', string="Custodian")
    custodian_id = fields.Many2one('hr.employee', 'Custodian')
    partner_id = fields.Many2one('res.partner', string="Partner")
    location = fields.Many2one('stock.location', 'Location')
    purchase_request_petty_cash_lines = fields.One2many('purchase.request.kay.petty.cash', 'key_petty_cash_id',
                                                        string="Lines")
    cancel_reason = fields.Char(
        string="Reason for Rejection",
        readonly=True)
    account_tax_id = fields.Many2one('account.tax', 'Tax')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    move_ids = fields.Many2many('account.move', 'kay_petty_cash_move_rel', 'kay_petty_cash_id', 'move_id',
                                string="Moves", compute='get_move_ids')
    invoice_count = fields.Integer(compute='_invoice_count', string='# Invoice', copy=False)
    petty_cash_breakdown_lines = fields.One2many('petty.cash.breakdown', 'key_petty_cash_id', string="Breakdown Lines")
    amount_issued = fields.Float("Amount Issued", compute="get_amount_issued")
    amount_expended = fields.Float("Amount Expended", compute='get_amount_expended')
    balance = fields.Float("Balance", compute='get_balance')
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")

    @api.multi
    @api.depends('petty_cash_breakdown_lines')
    def get_amount_issued(self):
        for rec in self:
            rec.amount_issued = sum(rec.purchase_request_petty_cash_lines.filtered(lambda l: l.state == 'post').mapped('amount'))

    @api.multi
    @api.depends('petty_cash_breakdown_lines')
    def get_amount_expended(self):
        for rec in self:
            rec.amount_expended = sum(rec.petty_cash_breakdown_lines.filtered(lambda l: l.status == 'post').mapped('amount'))

    @api.multi
    @api.depends('amount_issued', 'amount_expended')
    def get_balance(self):
        for rec in self:
            rec.balance = rec.amount_issued - rec.amount_expended

    @api.multi
    @api.depends('purchase_request_petty_cash_lines','petty_cash_breakdown_lines')
    def get_move_ids(self):
        for rec in self:
            move_ids_list = []
            for line in rec.purchase_request_petty_cash_lines:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            for line in rec.petty_cash_breakdown_lines:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            rec.move_ids = [(6, 0, move_ids_list)]

    @api.multi
    def button_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def button_to_approve(self):
        return self.write({'state': 'to_approve'})

    @api.multi
    def button_approved(self):
        return self.write({'state': 'approved'})

    @api.multi
    def button_rejected(self):
        return self.write({'state': 'rejected'})

    @api.multi
    def button_post(self):
        return self.write({'state': 'posted'})

    @api.multi
    def _invoice_count(self):
        self.invoice_count = len(self.move_ids.ids)

    @api.multi
    def button_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }


class PurchaseRequestKayPettyCash(models.Model):
    _name = "purchase.request.kay.petty.cash"

    key_petty_cash_id = fields.Many2one('kay.petty.cash', string="Petty Cash")
    name = fields.Char('Request Description')
    date = fields.Date('Request Date')
    amount = fields.Float('Request Amount')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    state = fields.Selection([('draft', 'Draft'),
                              ('request_for_approval', 'Request For Approval'),
                              ('send_for_approval', 'Send For Approval'),
                              ('approved', 'Approved'),
                              ('post', 'Posted')], default='draft', string="Status")
    move_id = fields.Many2one('account.move', string="Move")
    project_id = fields.Many2one('account.analytic.account', string="Project")

    @api.model
    def create(self, vals):
        res = super(PurchaseRequestKayPettyCash, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': res.name,
                'debit': res.amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': res.name,
                'debit': 0.0,
                'credit': res.amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(PurchaseRequestKayPettyCash, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': self.name,
                'debit': self.amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': self.name,
                'debit': 0.0,
                'credit': self.amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
        if vals.get('state', False) and vals['state'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': self.name,
                'debit': self.amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': self.name,
                'debit': 0.0,
                'credit': self.amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res


class PettyCashBreakdown(models.Model):
    _name = "petty.cash.breakdown"

    key_petty_cash_id = fields.Many2one('kay.petty.cash', string="Petty Cash")
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    status = fields.Selection([('draft', 'Draft'),
                              ('request_for_approval', 'Request For Approval'),
                              ('send_for_approval', 'Send For Approval'),
                               ('approved', 'Approved'),
                              ('post', 'Posted')], default='draft', string="Status")
    move_id = fields.Many2one('account.move', string="Move")
    project_id = fields.Many2one('account.analytic.account', string="Project")
    date = fields.Date("Date")

    @api.model
    def create(self, vals):
        res = super(PettyCashBreakdown, self).create(vals)
        if res and res.status == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': res.name,
                'debit': res.amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': res.name,
                'debit': 0.0,
                'credit': res.amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],

            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(PettyCashBreakdown, self).write(vals)
        if vals.get('status', False) and vals['status'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': self.name,
                'debit': self.amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': self.name,
                'debit': 0.0,
                'credit': self.amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],

            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
        if vals.get('status', False) and vals['status'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': self.name,
                'debit': self.amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': self.name,
                'debit': 0.0,
                'credit': self.amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    delivery_cost = fields.Monetary('Delivery')

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'date', 'delivery_cost')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        self.amount_total = self.amount_total + self.delivery_cost

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id or line.display_type:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_rate > 0 or line.discount_fixed > 0:
                taxes = line.invoice_line_tax_ids.compute_all(line.price_subtotal, self.currency_id, 1, line.product_id,
                                                              self.partner_id)['taxes']
            else:
                taxes = \
                line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id,
                                                      self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount_type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     default='amount')
    discount_rate = fields.Float(string='Discount Rate', digits=dp.get_precision('Product Price'), default=0.0)
    discount_fixed = fields.Monetary(string='Discount', digits=dp.get_precision('Product Price'), default=0.0,
                                     track_visibility='always')

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date', 'discount_type', 'discount_fixed', 'discount_rate')
    def _compute_price(self):
        for rec in self:
            currency = rec.invoice_id and rec.invoice_id.currency_id or None
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            taxes = False
            if rec.invoice_line_tax_ids:
                taxes = rec.invoice_line_tax_ids.compute_all(price, currency, rec.quantity, product=rec.product_id,
                                                             partner=rec.invoice_id.partner_id)

            subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else rec.quantity * price
            discount = 0.0
            if rec.discount_type == 'amount':
                discount = rec.discount_fixed
            if rec.discount_type == 'percentage':
                discount = (rec.price_unit * rec.quantity * rec.discount_rate) / 100
            rec.price_subtotal = subtotal - discount
            rec.price_total = taxes['total_included'] if taxes else rec.price_subtotal
            if rec.invoice_id.currency_id and rec.invoice_id.currency_id != rec.invoice_id.company_id.currency_id:
                currency = rec.invoice_id.currency_id
                date = rec.invoice_id._get_currency_rate_date()
                price_subtotal_signed = currency._convert(price_subtotal_signed, rec.invoice_id.company_id.currency_id,
                                                          rec.company_id or rec.env.user.company_id,
                                                          date or fields.Date.today())
            sign = rec.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            rec.price_subtotal_signed = price_subtotal_signed * sign
