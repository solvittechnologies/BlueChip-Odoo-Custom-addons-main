# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.exceptions import UserError


class ProjectFundRequest(models.Model):
    _name = 'fastra.project.fund.request'
    _inherit = ['mail.thread']

    state = fields.Selection([('draft', 'Draft'),
                              ('to_approval', 'Send for Approval'),
                              ('approved', 'Approved'),
                              ('reject', 'Rejected'),
                              ('start', 'Start'),
                              ('complete', 'Complete')],
                             string='Status', index=True, readonly=True, default='draft',
                             copy=False)
    project_manager = fields.Many2one('hr.employee', "Project Manager")
    project_description = fields.Char("Project Description")
    project_duration = fields.Char("Project Duration")
    project_account_code = fields.Char("Project Code")
    request_date = fields.Date("Request Date")
    site = fields.Char("Site ID")
    project_location = fields.Many2many('stock.location', string="Project Location")
    po_number_id = fields.Many2one('fastra.project.master.data', string='Customer PO',domain=[('is_customer_po','=',True)])
    po_amount = fields.Float("PO amount", related='po_number_id.po_amount')
    project_number = fields.Many2one('fastra.project.analysis', string="Project  Number")
    project_details = fields.Text("Details")
    project_fund_ids = fields.One2many('fastra.project.fund.request.line', 'project_fund_request_id',
                                       string="Project Fund")
    retirement_line_ids = fields.One2many('fastra.project.retirement.portion.line', 'project_fund_request_id',
                                          string="Retirement Portion Line")
    approved_fund_allocated = fields.Float("Disburse Amount")
    approved_retirement_amount = fields.Float("Retirement Amount")
    caf_approved_amount = fields.Float("CAF Approved Amount")
    approved_amount_balance = fields.Float("Approved Amount Balance")
    move_ids = fields.Many2many('account.move', 'hr_custom_move_rel', 'hr_custom_id', 'move_id', string="Moves",
                                compute='get_move_ids')
    project_detail_id = fields.Many2one('account.analytic.account', string="Project")
    caf_id = fields.Many2one('fastra.project.analysis', string="CAF NO")
    # is_edit_fund_line = fields.Boolean('Is Edit Fund Line', compute='check_edit_fund_line')
    profit_loss = fields.Float("Profit and Loss", compute='get_profit_loss')

    @api.multi
    @api.depends('approved_fund_allocated', 'po_amount')
    def get_profit_loss(self):
        for rec in self:
            rec.profit_loss = rec.po_amount - rec.approved_fund_allocated

    @api.multi
    @api.depends('retirement_line_ids', 'project_fund_ids')
    def check_edit_fund_line(self):
        for rec in self:
            rec.is_edit_fund_line = True
            edit = True
            for line in rec.retirement_line_ids:
                if line.state != 'post':
                    edit = False
            if not edit:
                rec.is_edit_fund_line = False

            p_total = 0
            r_total = 0
            for p_line in rec.project_fund_ids.filtered(lambda l: l.state == 'post'):
                p_total += p_line.fund_amount

            for r_line in rec.retirement_line_ids.filtered(lambda r: r.state == 'post'):
                r_total += r_line.fund_amount

            if p_total > r_total != 0.0:
                rec.is_edit_fund_line = False


    @api.multi
    @api.onchange('caf_id')
    def onchange_caf_id(self):
        if self.caf_id:
            self.project_manager = self.caf_id.project_manager.id
            self.project_description = self.caf_id.project_description
            self.project_duration = self.caf_id.project_duration
            self.project_account_code = self.caf_id.project_account_code
            self.request_date = self.caf_id.request_date
            self.site = self.caf_id.site
            self.project_location = [(6, 0, self.caf_id.project_location.ids)]
            self.caf_approved_amount = self.caf_id.amount_total
            self.project_detail_id = self.caf_id.project_detail_id
            self.po_number_id = self.caf_id.po_number_id and self.caf_id.po_number_id.id or False
        # set line data inside the Project Fund
            fund_ids = []
            for line in self.caf_id.invoice_line_ids:
                fund_line_id = self.env['fastra.project.fund.request.line'].create({'project_fund_request_id': self.id,
                                                                     'job': line.job_id and line.job_id.name,
                                                                     'description': line.name,
                                                                     'quantity': line.quantity,
                                                                     'amount': line.amount})
                fund_ids.append(fund_line_id.id)
            self.project_fund_ids = [(6, 0, fund_ids)]


    @api.multi
    @api.depends('retirement_line_ids', 'project_fund_ids')
    def get_move_ids(self):
        for rec in self:
            move_ids_list = []
            for line in rec.project_fund_ids:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            for line in rec.retirement_line_ids:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            rec.move_ids = [(6, 0, move_ids_list)]

    def action_change_state_to_start(self):
        self.write({'state': 'start'})

    def action_change_state_to_completed(self):
        self.write({'state': 'completed'})

    def action_button_send_for_approval(self):
        self.write({'state': 'to_approval'})

    def action_button_project_budget_approve(self):
        self.write({'state': 'approved'})

    def action_button_project_budget_start(self):
        vals = {'project_manager': self.project_manager and self.project_manager.id or False,
                'project_description': self.project_description,
                'project_duration': self.project_duration,
                'project_account_code': self.project_account_code,
                'request_date': self.request_date,
                'site': self.site,
                'project_location': [(6, 0, self.project_location.ids)],
                'po_number_id': self.po_number_id and self.po_number_id.id or False,
                'po_amount': self.po_amount,
                'project_number': self.project_number and self.project_number.id or False,
                'project_details': self.project_details,
                'approved_fund_allocated': self.approved_fund_allocated,
                'approved_retirement_amount': self.approved_retirement_amount,
                'caf_approved_amount': self.caf_approved_amount,
                'approved_amount_balance': self.approved_amount_balance,
                'project_detail_id': self.project_detail_id and self.project_detail_id.id or False,
                'caf_id': self.caf_id and self.caf_id.id or False,
                'profit_loss': self.profit_loss,
                'disbursement_id': self.id,
                'state': 'start',
                }
        tracker_id = self.env['fastra.project.budget.tracker'].create(vals)
        self.write({'state': 'start'})

    def action_button_project_budget_complete(self):
        tracker_ids = self.env['fastra.project.budget.tracker'].search([('disbursement_id', '=', self.id)])
        tracker_ids.write({'state': 'complete'})
        self.write({'state': 'complete'})

    def action_button_project_budget_reject(self):
        self.write({'state': 'reject'})
        view_id = self.env.ref('fastra_project_budget.update_rejection_reason_note_form').id
        context = {'default_project_analysis_request_fund_id': self.id,
                   }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'res_model': 'rejection.reason.popup.wizard',
            'target': 'new',
            'context': context,
            'views': [[view_id, 'form']],
        }

    @api.multi
    @api.onchange('project_fund_ids')
    def onchange_approved_fund_allocated(self):
        total_increase_amount = 0
        for fund_line in self.project_fund_ids:
            if fund_line.state == 'post':
                total_increase_amount += fund_line.fund_amount
        self.approved_fund_allocated = total_increase_amount
        self.approved_amount_balance = self.caf_approved_amount - self.approved_fund_allocated

    @api.multi
    @api.onchange('retirement_line_ids')
    def onchange_approved_retirement_amount(self):
        total_increase_amount = 0
        for fund_line in self.retirement_line_ids:
            if fund_line.state == 'post':
                total_increase_amount += fund_line.fund_amount
        self.approved_retirement_amount = total_increase_amount

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


class ProjectFundRequestLines(models.Model):
    _name = 'fastra.project.fund.request.line'

    project_fund_request_id = fields.Many2one('fastra.project.fund.request', string="Fund Request")
    job = fields.Char("Scope")
    description = fields.Char('Description')
    fund_amount = fields.Float('Disburse Amount')
    rate = fields.Integer("Rate")
    quantity = fields.Integer("Quantity")
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    state = fields.Selection([('draft', 'Pending'),
                              ('post', 'Approved')], string="Status")
    move_id = fields.Many2one('account.move', string="Move")
    amount = fields.Integer("Amount")

    @api.model
    def create(self, vals):
        res = super(ProjectFundRequestLines, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': res.job,
                'debit': res.fund_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
                'analytic_account_id': res.project_fund_request_id.project_detail_id and res.project_fund_request_id.project_detail_id.id or False
            }
            credit_vals = {
                'name': res.job,
                'debit': 0.0,
                'credit': res.fund_amount,
                'account_id': res.account_credit.id,
                'analytic_account_id': res.project_fund_request_id.project_detail_id and res.project_fund_request_id.project_detail_id.id or False
            }
            ref = "Disburse: "
            if res.project_fund_request_id.project_description:
                ref = "Disburse: " + res.project_fund_request_id.project_description
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': ref,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
            if res.project_fund_request_id.caf_id and res.id not in res.project_fund_request_id.caf_id.disbursement_project_fund_ids.ids:
                res.project_fund_request_id.caf_id.write({'disbursement_project_fund_ids': [(4, res.id)]})
        return res

    @api.multi
    def write(self, vals):
        res = super(ProjectFundRequestLines, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': self.job,
                'debit': self.fund_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            credit_vals = {
                'name': self.job,
                'debit': 0.0,
                'credit': self.fund_amount,
                'account_id': self.account_credit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': "Disburse: " + self.project_fund_request_id.project_description if self.project_fund_request_id.project_description else "",
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
            if self.project_fund_request_id.caf_id and self.id not in self.project_fund_request_id.caf_id.disbursement_project_fund_ids.ids:
                self.project_fund_request_id.caf_id.write({'disbursement_project_fund_ids': [(4, self.id)]})
        if vals.get('state', False) and vals['state'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': self.job,
                'debit': self.fund_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            credit_vals = {
                'name': self.job,
                'debit': 0.0,
                'credit': self.fund_amount,
                'account_id': self.account_credit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
            if self.project_fund_request_id.caf_id and self.id not in self.project_fund_request_id.caf_id.disbursement_project_fund_ids.ids:
                self.project_fund_request_id.caf_id.write({'disbursement_project_fund_ids': [(4, self.id)]})
        return res


class RetirementPortion(models.Model):
    _name = 'fastra.project.retirement.portion.line'

    project_fund_request_id = fields.Many2one('fastra.project.fund.request', string="Fund Request")
    retirement_description = fields.Char("Retirement Description")
    retirement_date = fields.Date('Retirement Date')
    state = fields.Selection([('draft', 'Pending'),
                              ('post', 'Approved'), ],
                             string='Status', index=True, default='draft',
                             copy=False)
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    fund_amount = fields.Float('Fund Amount')
    move_id = fields.Many2one('account.move', string="Move")
    caf_project_fund_id = fields.Many2one('fastra.project.analysis', string="Project fund id")

    @api.model
    def create(self, vals):
        res = super(RetirementPortion, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': res.retirement_description,
                'debit': res.fund_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
                'analytic_account_id': res.project_fund_request_id.project_detail_id and res.project_fund_request_id.project_detail_id.id or False
            }
            credit_vals = {
                'name': res.retirement_description,
                'debit': 0.0,
                'credit': res.fund_amount,
                'account_id': res.account_credit.id,
                'analytic_account_id': res.project_fund_request_id.project_detail_id and res.project_fund_request_id.project_detail_id.id or False
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': 'Retirement: '+res.project_fund_request_id.project_description if res.project_fund_request_id.project_description else "",
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
            if res.project_fund_request_id.caf_id and res.id not in res.project_fund_request_id.caf_id.disbursement_retirement_amount_ids.ids:
                res.project_fund_request_id.caf_id.write({'disbursement_retirement_amount_ids': [(4, res.id)]})
        return res

    @api.multi
    def write(self, vals):
        res = super(RetirementPortion, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': self.retirement_description,
                'debit': self.fund_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            credit_vals = {
                'name': self.retirement_description,
                'debit': 0.0,
                'credit': self.fund_amount,
                'account_id': self.account_credit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': 'Retirement: '+self.project_fund_request_id.project_description if self.project_fund_request_id.project_description else "",
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
            if self.project_fund_request_id.caf_id and self.id not in self.project_fund_request_id.caf_id.disbursement_retirement_amount_ids.ids:
                self.project_fund_request_id.caf_id.write({'disbursement_retirement_amount_ids': [(4, self.id)]})
        if vals.get('state', False) and vals['state'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': self.retirement_description,
                'debit': self.fund_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            credit_vals = {
                'name': self.retirement_description,
                'debit': 0.0,
                'credit': self.fund_amount,
                'account_id': self.account_credit.id,
                'analytic_account_id': self.project_fund_request_id.project_detail_id and self.project_fund_request_id.project_detail_id.id or False
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
            if self.project_fund_request_id.caf_id and self.id not in self.project_fund_request_id.caf_id.disbursement_retirement_amount_ids.ids:
                self.project_fund_request_id.caf_id.write({'disbursement_retirement_amount_ids': [(4, self.id)]})
        return res
