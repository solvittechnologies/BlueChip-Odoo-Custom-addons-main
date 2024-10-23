# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountWHT(models.Model):
    _name = 'account.wht'

    name = fields.Float(string="Amount", digits=(16, 4))

class ModelName(models.Model):
    _name = 'project.budget.taxes'
    _description = 'Project Budget Taxes'

    tax_id = fields.Many2one('account.tax', string="Tax")
    tax_amount = fields.Float("Amount")
    budget_id = fields.Many2one('fastra.project.analysis', string="Budget")

class ProjectAnalysis(models.Model):
    _name = 'fastra.project.analysis'
    _inherit = ['fastra.project.analysis', 'mail.thread']
    _rec_name = "po_number"

    def get_default_currency(self):
        return self.env.ref('base.NGN')

    state = fields.Selection(selection_add=[
                                            ('draft', 'Draft'),
                                            ('send_to_head_of_department', 'Send to Head of Department'),
                                            ('send_to_md', 'Send to MD'),
                                            ('send_to_finance', 'Send to Finance'),
                                            ('approve', 'Approve'),
                                            ('reject', 'Rejected'),
                                            ], default='draft')
    # project_detail_id = fields.Many2one('project.details', string="Project")
    project_manager = fields.Many2one('hr.employee', "Project Manager")
    project_description = fields.Char("Project Description")
    project_duration = fields.Char("Project Duraion")
    request_date = fields.Date("Request Date")
    project_account_code = fields.Char("Project Code")
    project_location = fields.Many2many('stock.location','project_location_stock_rel','project_id','location_id',string="Project Location")
    site = fields.Char("Site ID")
    invoice_line_ids = fields.One2many('project.analysis.line', 'job_line_ids', string='Project Lines',
                                       readonly=True, states={'draft': [('readonly', False)], 'approved': [('readonly', False)]}, copy=True)
    account_id = fields.Many2one('account.account', string= 'Account Code',  domain="[('deprecated', '=', False)]")
    voucher_ids = fields.Many2many('account.voucher', string="Receipts")
    project_detail_id = fields.Many2one('account.analytic.account', string="Project")
    purchase_order_line_ids = fields.Many2many('account.invoice', string="Invoices", compute='compute_project_detail_id')
    petty_cash_line_custodian_ids = fields.Many2many('kay.petty.cash.add.line', string="Petty Cash Custodian Lines",  compute='compute_project_detail_id')
    petty_cash_line_ids = fields.Many2many('purchase.request.kay.petty.cash', string="Petty Cash Lines",  compute='compute_project_detail_id')
    purchase_total = fields.Float(string="Total", compute='compute_total_amount')
    petty_cash_line_custodian_total = fields.Float(string="Total", compute='compute_total_amount')
    petty_cash_line_total = fields.Float(string="Total", compute='compute_total_amount')
    actual_implementation_cost = fields.Monetary('Actual Implementation Cost', compute="compute_actual_implementation_cost")
    net_contract_value = fields.Monetary('Gross Contract Value', compute="get_net_contract_value")
    bill_amount = fields.Float('Bill 1')
    profit_loss = fields.Monetary(string='Profit / Loss',
                                compute='_compute_profit_loss_amount',
                                store=False,  # optional
                                )
    account_voucher_ids = fields.Many2many('account.payment', string="Other Payment",  compute='compute_project_detail_id')
    account_voucher_total = fields.Float(string="Total", compute='compute_voucher_total_amount')
    tax_id = fields.Many2many('account.tax', string="Tax")
    tax_amount = fields.Float("Tax Amount", compute='get_net_contract_value')
    tax_breakout_ids = fields.One2many('project.budget.taxes', 'budget_id', string='Tax Amount', compute='get_tax_brakout')
    # wht_id = fields.Many2one('account.wht', string="WHT")
    # wht_amount = fields.Float("WHT Amount", compute='get_net_contract_value')
    wht_amount = fields.Float("WHT")
    contingency_amount = fields.Float("Contingency")
    po_number_id = fields.Many2one('fastra.project.master.data',string = 'Customer PO', domain=[('is_customer_po','=',True)])
    po_amount = fields.Integer("PO Amount")
    project_details = fields.Char("Project rejection Detail")
    po_number = fields.Char(string='CAF NO', required=True,
                          readonly=True, default=lambda self: _('New'))
    disbursement_project_fund_ids = fields.Many2many('fastra.project.fund.request.line', 'fund_request_caf_rel', 'caf_id', 'fund_id', string="Disbursement Project Fund")
    disbursement_retirement_amount_ids = fields.Many2many('fastra.project.retirement.portion.line','retirement_portion_caf_rel','caf_id','retirement_id',string="Disbursement Retirement Amount")
    margin = fields.Float('Margin', compute='get_margin')
    currency_id = fields.Many2one('res.currency', string='Currency', default=get_default_currency,
                                  required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  track_visibility='always')
    file_name = fields.Char("File Name")
    file_attachment = fields.Binary("File Attachment")

    @api.multi
    @api.depends('po_amount', 'amount_total')
    def get_margin(self):
        for rec in self:
            try:
                rec.margin = ((rec.po_amount - rec.amount_total) / rec.po_amount) * 100
            except:
                rec.margin = 0.0

    @api.model
    def create(self, vals):
        if vals.get('po_number', _('New')) == _('New'):
            vals['po_number'] = self.env['ir.sequence'].next_by_code(
                'project.budget.caf.no') or _('New')
        return super(ProjectAnalysis, self).create(vals)

    @api.multi
    @api.depends('tax_id')
    def get_tax_brakout(self):
        for rec in self:
            rec.tax_breakout_ids = [(6, 0, [])]
            vals = []
            for tax in rec.tax_id:
                vals.append((0, 0, {'tax_id': tax.id, 'tax_amount': (rec.amount * tax.amount) / 100}))
            if vals:
                rec.tax_breakout_ids = vals

    @api.multi
    def compute_voucher_total_amount(self):
        for rec in self:
            line_total = 0.0
            for line in rec.account_voucher_ids:
                line_total += line.amount
            rec.account_voucher_total += line_total
    
    @api.depends('disbursement_retirement_amount_ids')
    def compute_actual_implementation_cost(self):
        for rec in self:
            rec.actual_implementation_cost = sum(rec.disbursement_retirement_amount_ids.mapped('fund_amount'))

    @api.multi
    @api.depends('amount', 'bill_amount', 'tax_id', 'contingency_amount')
    def get_net_contract_value(self):
        for rec in self:
            # wht_amount = rec.wht_id.name if rec.wht_id else 0.0
            # wht = (rec.amount * wht_amount) / 100
            # rec.wht_amount = wht
            # rec.net_contract_value = rec.amount - (tax + wht + rec.bill_amount)
            tax_amount = 0.0
            for tax in rec.tax_id:
                tax_amount += (rec.amount * tax.amount) / 100
            rec.tax_amount = tax_amount
            rec.net_contract_value = rec.amount + tax_amount + rec.contingency_amount

    @api.multi
    @api.depends('po_amount', 'amount_total')
    def _compute_profit_loss_amount(self):
        for rec in self:
            rec.profit_loss = rec.po_amount - rec.amount_total
    
    @api.multi
    @api.depends('purchase_order_line_ids', 'petty_cash_line_custodian_ids', 'petty_cash_line_ids')
    def compute_total_amount(self):
        for rec in self:
            po_total = 0.0
            petty_cash_costodial_total = 0.0
            petty_cash_total = 0.0
            for po_line in rec.purchase_order_line_ids:
                po_total += po_line.amount_total
            for custodial_line in rec.petty_cash_line_custodian_ids:
                petty_cash_costodial_total += custodial_line.amount
            for petty_line in rec.petty_cash_line_ids:
                petty_cash_total += petty_line.amount
            rec.purchase_total = po_total
            rec.petty_cash_line_custodian_total = petty_cash_costodial_total
            rec.petty_cash_line_total = petty_cash_total 
    
    def set_status_send_program_manager(self):
        self.write({'state': 'send_to_head_of_department'})

    def set_status_md(self):
        self.write({'state': 'send_to_md'})

    # def set_status_consultant(self):
    #     self.write({'state': 'send_to_consultant'})

    def set_status_finance(self):
        self.write({'state': 'send_to_finance'})

    def set_status_approve(self):
        self.write({'state': 'approve'})

    def set_status_draft(self):
        self.write({'state': 'draft'})

    # def action_button_project_budget_approve(self):
    #     self.write({'state': 'approved'})
    #     vals = {'po_amount':self.po_amount}
    #     if self.po_number_id:
    #         self.po_number_id.write(vals)

    def action_button_project_budget_reject(self):
        self.write({'state': 'reject'})
        view_id = self.env.ref('fastra_project_budget.update_rejection_reason_note_form').id
        context = {'default_project_analysis_id': self.id}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'res_model': 'rejection.reason.popup.wizard',
            'target': 'new',
            'context': context,
            'views': [[view_id, 'form']],  
        }
        
    def create_receipt(self):
        vals = {'account_id': self.account_id.id,
                'voucher_type': 'sale',
                }
        voucher_id = self.env['account.voucher'].create(vals)
        self.voucher_ids = [(4, voucher_id.id)]
    
    def action_view_receipts(self):
        if not self.voucher_ids:
            raise UserError(_("There is no Receipt for this Project Budget"))
        action = self.env.ref('account_voucher.action_sale_receipt').read()[0]
        action['domain'] = [('id', 'in', self.voucher_ids.ids)]
        return action

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.account_id = self.partner_id.property_account_receivable_id or self.partner_id.property_account_payable_id

    @api.multi
    @api.onchange('po_number_id')
    def onchange_po_number_id(self):
        if self.po_number_id:
            self.po_amount = self.po_number_id.po_amount or 0
            project_initiation_request_id = self.env['fastra.budget.request'].search([('po_number_id', '=', self.po_number_id.id)], order="id desc", limit=1)
            if project_initiation_request_id:
                self.partner_id = project_initiation_request_id.partner_id and project_initiation_request_id.partner_id.id or False
                self.project_manager = project_initiation_request_id.project_manager and project_initiation_request_id.project_manager.id or False
                self.project_description = project_initiation_request_id.project_description
                self.project_duration = project_initiation_request_id.project_duration
                self.project_account_code = project_initiation_request_id.project_account_code
                self.request_date = project_initiation_request_id.request_date
                self.site = project_initiation_request_id.site
                self.project_location = [(6, 0, project_initiation_request_id.project_location.ids)]
                self.project_detail_id = project_initiation_request_id.project_detail_id.id
                self.file_attachment = project_initiation_request_id.file_attachment
                self.onchange_invoice_line_amount()


    @api.onchange('amount_total')
    def onchange_invoice_line_amount(self):
        total_amount = 0
        po=self.po_number_id and self.po_number_id.po_amount or 0
        for line in self.invoice_line_ids:
            total_amount += line.amount
        # self.po_amount = po - total_amount

    @api.multi
    def get_product_fund_line(self):
        for rec in self:
            rec.disbursement_project_fund_ids = [(6, 0, [])]
            rec.disbursement_retirement_amount_ids = [(6, 0, [])]

            disbursement_project_fund_line_list = []
            disbursement_project_retirement_list = []
            for line in self.env['fastra.project.fund.request'].search([('caf_id', '=', rec.id)]):
                for rec in line.project_fund_ids:
                    disbursement_project_fund_line_list.append(rec.id)
                for retirement_id in line.retirement_line_ids:
                    disbursement_project_retirement_list.append(retirement_id.id)
            rec.disbursement_project_fund_ids = [(6, 0, disbursement_project_fund_line_list)]
            rec.disbursement_retirement_amount_ids = [(6, 0, disbursement_project_retirement_list)]

    @api.multi
    @api.depends('project_detail_id')
    def compute_project_detail_id(self):
        for record in self:
            record.purchase_order_line_ids = [(6, 0, [])]
            record.petty_cash_line_custodian_ids = [(6, 0, [])]
            record.petty_cash_line_ids = [(6, 0, [])]
            record.account_voucher_ids = [(6, 0, [])]
            if record.project_detail_id:
                invoice_list = []
                account_invoice_line_ids = self.env['account.invoice.line'].search([('account_analytic_id', '=', record.project_detail_id.id),('invoice_id.state', 'in', ['paid'])])
                for line in account_invoice_line_ids:
                    invoice_list.append(line.invoice_id.id)
                invoice_list = list(set(invoice_list))
                record.purchase_order_line_ids = [(6, 0, invoice_list)]
                # purchase_order_line_ids = self.env['purchase.order.line'].search([('account_analytic_id','=',record.project_detail_id.id),('state','in',['purchase','done'])])
                # record.purchase_order_line_ids = [(6, 0, purchase_order_line_ids.ids)]

                petty_cash_custodian_line_list = []
                petty_cash_line_list = []
                for petty_cash_id in self.env['kay.petty.cash'].search([('name','=',record.project_detail_id.id)]):
                    for line in petty_cash_id.add_cash_line:
                        if line.state == 'validate':
                            petty_cash_custodian_line_list.append(line.id)
                    for cash_line_id in petty_cash_id.purchase_request_petty_cash_lines:
                        if petty_cash_id.state == 'approved':
                            petty_cash_line_list.append(cash_line_id.id)
                    # for cash_line_id in petty_cash_id.cash_line:
                    #     if cash_line_id.state == 'posted':
                    #         petty_cash_line_list.append(cash_line_id.id)

                record.petty_cash_line_custodian_ids = [(6, 0, petty_cash_custodian_line_list)]
                record.petty_cash_line_ids = [(6, 0, petty_cash_line_list)]

                payment_ids = record.env['account.payment'].search([('project_detail_id', '=', record.project_detail_id.id)])
                record.account_voucher_ids = [(6, 0, payment_ids.ids)]






    # @api.onchange('project_detail_id')
    # def onchange_project_detail_id(self):
    #     self.outgoing_payment_ids = self.env['account.payment'].search(
    #         [('project_detail_id', '=', self.project_detail_id.id)])



class ProjectAnalysisLine(models.Model):
    _inherit = "project.analysis.line"

    state = fields.Selection(related='job_line_ids.state', store=True)
    quantity = fields.Integer("Quantity")

    @api.onchange('job_line_ids', 'job_line_ids.currency_id')
    def onchange_project_budget_currency(self):
        self.currency_id = self.job_line_ids.currency_id
