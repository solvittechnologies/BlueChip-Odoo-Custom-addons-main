from odoo import models,fields,api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

Months = [('Jan', 'January'),
          ('Feb', 'February'),
          ('Mar', 'March'),
          ('Apr', 'April'),
          ('May', 'May'),
          ('Jun', 'June'),
          ('Jul', 'July'),
          ('Aug', 'August'),
          ('Sep', 'September'),
          ('Oct', 'October'),
          ('Nov', 'November'),
          ('Dec', 'December')]

Payroll_Type_Selection = [('basic_salary', 'Basic Salary'),
                          ('transport_allowance', 'Transport'),
                          ('housing_allowance', 'Housing'),
                          ('meal_allowance', 'Meal Allowance'),
                          ('dressing', 'Dressing'),
                          ('employer_pension', "Employer's Pension"),
                          ('employee_pension', "Employee's Pension"),
                          ('medical_plan', 'Medical plan'),
                          ('paye', 'PAYE'),
                          ('leave_allowance', 'Leave Allowance'),
                          ('gratutity_plan', 'Gratutity Plan'),
                          ('monthly_gross', 'Monthly Gross/ Monthly emolument'),
                          ('life_assurance_plan', 'Life Assurance Plan'),
                          ]


class FastraPayroll(models.Model):
    _name = "fastra.payroll"


    name = fields.Char("Payslip Name")
    state = fields.Selection([('draft', 'Draft'),
                              ('send_to_hr', 'Send To HR'),
                              ('send_to_md', 'Send To MD'),
                              ('reject', 'Reject'),
                              ('validated', 'Approve')], string="State",  default='reject')
    location_id = fields.Many2one('stock.location', "Location")
    date_from = fields.Date(string='Date From', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            )
    date_to = fields.Date(string='Date To', required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          )
    month = fields.Selection(Months, string="Month")
    # employee_tag = fields.Char("Reference Number")

    account_analytic_id = fields.Many2one('account.analytic.account', "Project")
    fastra_hr_payroll_line_ids = fields.One2many('fastra.hr.payroll.line', 'fastra_payroll_id', string="Lines")
    fastra_hr_payroll_salary_line_ids = fields.One2many('fastra.hr.payslip.salary.line', 'fastra_payroll_id', string="Salary Lines")
    fastra_hr_payroll_account_line_ids = fields.One2many('fastra.hr.payslip.account.line', 'fastra_payroll_id',
                                                      string="Account Lines")
    fastra_hr_payroll_individual_account_line_ids = fields.One2many('fastra.hr.payslip.individual.account.line', 'fastra_payroll_id',
                                                         string="Individual Account Lines")
    move_ids = fields.Many2many('account.move', 'fastra_hr_payslip_move_rel', 'hr_payslip_id', 'move_id', string="Moves",
                                compute='get_move_ids')
    cancel_reason = fields.Text("Cancel Reason")

    def send_to_hr(self):
        self.state = 'send_to_hr'

    def send_to_md(self):
        self.state = 'send_to_md'

    def approve(self):
        self.state = 'validated'
    def reject(self):
        self.state = 'reject'

    def action_reject(self):
        form_view = self.env.ref('fastra_hr_customize.view_fastra_hr_salary_payroll_cancel')
        action = {
            'name': (_('Salary Payroll Cancel Reason')),
            'type': 'ir.actions.act_window',
            'res_model': 'fastra.hr.cancel',
            'view_mode': 'form',
            'view_id': form_view.id,
            'target': 'new',
            'context': {'active_ids': self.id}
        }
        return action


    def reset_draft(self):
        self.state = 'draft'
    # @api.model
    # def create(self, values):
    #     if not values.get('employee_tag', False):
    #         reference_code = self.env['ir.sequence'].next_by_code('employee.payroll.reference')
    #         values['employee_tag'] = reference_code[:-1]
    #     res = super(FastraPayroll, self).create(values)
    #     if res.location_id:
    #         res.employee_tag = res.employee_tag.replace("ABJ", res.location_id.name)
    #     return res

    @api.model
    def default_get(self, fields_list):
        res = super(FastraPayroll, self).default_get([])
        salary_computation_ids = self.env['fastra.master.salary.computation'].search([])
        vals = []
        for salary_id in salary_computation_ids:
            vals.append((0, 0, {'job_group_id': salary_id.job_group_id.id,
                                'step_id': salary_id.step_id.id,
                                'basic_salary': salary_id.basic_salary,
                                'housing_allowance': salary_id.housing_allowance,
                                'transport_allowance': salary_id.transport_allowance,
                                'meal_allowance': salary_id.meal_allowance,
                                'dressing': salary_id.dressing,
                                'life_assurance_plan': salary_id.life_assurance_plan}))
        res.update({'fastra_hr_payroll_salary_line_ids': vals,'state':'draft'})
        return res

    @api.multi
    @api.onchange('date_from')
    def onchange_date_of_month_selection(self):
        if self.date_from:
            month = self.date_from.strftime('%b')
            self.month = month

    @api.multi
    @api.depends('fastra_hr_payroll_account_line_ids', 'fastra_hr_payroll_individual_account_line_ids')
    def get_move_ids(self):
        for rec in self:
            move_ids_list = []
            for line in rec.fastra_hr_payroll_account_line_ids:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            for account_line in rec.fastra_hr_payroll_individual_account_line_ids:
                if account_line.move_id:
                    move_ids_list.append(account_line.move_id.id)
            rec.move_ids = [(6, 0, move_ids_list)]

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


class Payroll(models.Model):
    _name = "fastra.hr.payroll.line"

    fastra_payroll_id = fields.Many2one('fastra.payroll', string="Payroll")
    employee_id = fields.Many2one('hr.employee', string="Employee Name")
    job_group_id =fields.Many2one('job.group', string="Job Group")
    step_id = fields.Many2one('step.step',string="Step")
    basic_salary = fields.Float("Basic")
    housing_allowance = fields.Float("Housing")
    transport_allowance = fields.Float("Transport")
    meal_allowance = fields.Float("Meal Allowance")
    dressing = fields.Float("Dressing")
    employer_pension = fields.Float("Employer's Pension")
    employee_pension = fields.Float("Employee's Pension")
    paye = fields.Float('Paye')
    medical_plan = fields.Float("Medical plan")
    leave_allowance = fields.Float("Leave Allowance")
    gratutity_plan = fields.Float("Gratutity Plan")
    monthly_gross = fields.Float('Monthly Gross/ Monthly emolument')
    life_assurance_plan = fields.Float('Life Assurance Plan')

    @api.multi
    @api.onchange('job_group_id', 'step_id')
    def onchange_job_step(self):
        if self.job_group_id and self.step_id:
            for salary_line in self.fastra_payroll_id.fastra_hr_payroll_salary_line_ids:
                if salary_line.job_group_id.id == self.job_group_id.id and salary_line.step_id.id == self.step_id.id:
                    self.basic_salary = salary_line.basic_salary
                    self.housing_allowance = salary_line.housing_allowance
                    self.transport_allowance = salary_line.transport_allowance
                    self.meal_allowance = salary_line.meal_allowance
                    self.dressing = salary_line.dressing
                    self.life_assurance_plan = salary_line.life_assurance_plan
                    break

    @api.multi
    @api.onchange('basic_salary', 'housing_allowance', 'transport_allowance', 'monthly_gross', 'meal_allowance', 'dressing')
    def onchange_salary_fields(self):
        self.paye = (self.basic_salary * 7) / 100 if self.basic_salary else 0.0
        pension_total = self.basic_salary + self.housing_allowance + self.transport_allowance
        self.employer_pension = (pension_total * 10) / 100 if pension_total else 0.0
        self.employee_pension = (pension_total * 7.5) / 100 if pension_total else 0.0
        self.medical_plan = (self.monthly_gross * 35) / 100 if self.monthly_gross else 0.0
        self.leave_allowance = self.basic_salary
        self.monthly_gross = self.basic_salary + self.meal_allowance + self.housing_allowance + self.transport_allowance + self.dressing


class JobGroup(models.Model):
    _name = "job.group"

    name = fields.Char("Name")


class PayrollStep(models.Model):
    _name = "step.step"

    name = fields.Char("Name")


class FastraHrPayslipSalaryLine(models.Model):
    _name = 'fastra.hr.payslip.salary.line'

    fastra_payroll_id = fields.Many2one('fastra.payroll', string="Payroll")
    job_group_id = fields.Many2one('job.group', string="Job Group")
    step_id = fields.Many2one('step.step', string="Step")
    basic_salary = fields.Float("Basic")
    housing_allowance = fields.Float("Housing")
    transport_allowance = fields.Float("Transport")
    meal_allowance = fields.Float("Meal Allowance")
    dressing = fields.Float("Dressing")
    life_assurance_plan = fields.Float('Life Assurance Plan')




class FastraHrPayslipAccountLine(models.Model):
    _name = 'fastra.hr.payslip.account.line'


    fastra_payroll_id = fields.Many2one('fastra.payroll', string="Payroll")
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    payroll_type = fields.Selection(selection=Payroll_Type_Selection, string="Payroll Type")
    type_amount = fields.Float('Type Amount', compute='get_type_amount')
    line_ids = fields.Many2many('fastra.hr.payroll.line', compute='get_line_ids')
    state = fields.Selection([('draft', 'Draft'),
                              ('post', 'Post')], string="Status")
    move_id = fields.Many2one('account.move', string="Move")


    @api.model
    def create(self, vals):
        res = super(FastraHrPayslipAccountLine, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': res.type_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': 0.0,
                'credit': res.type_amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.fastra_payroll_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(FastraHrPayslipAccountLine, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.fastra_payroll_id.name,
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
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res


    @api.multi
    @api.depends('fastra_payroll_id', 'fastra_payroll_id.fastra_hr_payroll_line_ids')
    def get_line_ids(self):
        for rec in self:
            if rec.fastra_payroll_id and rec.fastra_payroll_id.fastra_hr_payroll_line_ids:
                rec.line_ids = [(6, 0, rec.fastra_payroll_id.fastra_hr_payroll_line_ids.ids)]
            else:
                rec.line_ids = [(6, 0, [])]

    @api.multi
    @api.depends('payroll_type', 'line_ids')
    def get_type_amount(self):
        for rec in self:
            rec.type_amount = 0.0
            if rec.payroll_type == 'basic_salary':
                rec.type_amount = sum(rec.line_ids.mapped('basic_salary'))
            if rec.payroll_type == 'transport_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('transport_allowance'))
            if rec.payroll_type == 'housing_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('housing_allowance'))
            if rec.payroll_type == 'meal_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('meal_allowance'))
            if rec.payroll_type == 'dressing':
                rec.type_amount = sum(rec.line_ids.mapped('dressing'))
            if rec.payroll_type == 'employer_pension':
                rec.type_amount = sum(rec.line_ids.mapped('employer_pension'))
            if rec.payroll_type == 'employee_pension':
                rec.type_amount = sum(rec.line_ids.mapped('employee_pension'))
            if rec.payroll_type == 'medical_plan':
                rec.type_amount = sum(rec.line_ids.mapped('medical_plan'))
            if rec.payroll_type == 'paye':
                rec.type_amount = sum(rec.line_ids.mapped('paye'))
            if rec.payroll_type == 'leave_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('leave_allowance'))
            if rec.payroll_type == 'gratutity_plan':
                rec.type_amount = sum(rec.line_ids.mapped('gratutity_plan'))
            if rec.payroll_type == 'monthly_gross':
                rec.type_amount = sum(rec.line_ids.mapped('monthly_gross'))
            if rec.payroll_type == 'life_assurance_plan':
                rec.type_amount = sum(rec.line_ids.mapped('life_assurance_plan'))

class IndividualAccountLine(models.Model):
    _name = 'fastra.hr.payslip.individual.account.line'

    employee_id = fields.Many2one('hr.employee', string="Employee Name")
    fastra_payroll_id = fields.Many2one('fastra.payroll', string="Payroll")
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    payroll_type = fields.Selection(selection=Payroll_Type_Selection, string="Payroll Type")
    type_amount = fields.Float('Type Amount', compute='get_type_amount')
    line_ids = fields.Many2many('fastra.hr.payroll.line', compute='get_line_ids')
    state = fields.Selection([('draft', 'Draft'),
                              ('post', 'Post')], string="Status")
    move_id = fields.Many2one('account.move', string="Move")

    @api.model
    def create(self, vals):
        res = super(IndividualAccountLine, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': res.type_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': 0.0,
                'credit': res.type_amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.fastra_payroll_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(IndividualAccountLine, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.fastra_payroll_id.name,
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
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res

    @api.multi
    @api.depends('fastra_payroll_id', 'fastra_payroll_id.fastra_hr_payroll_line_ids')
    def get_line_ids(self):
        for rec in self:
            if rec.fastra_payroll_id and rec.fastra_payroll_id.fastra_hr_payroll_line_ids:
                rec.line_ids = [(6, 0, rec.fastra_payroll_id.fastra_hr_payroll_line_ids.ids)]
            else:
                rec.line_ids = [(6, 0, [])]

    @api.multi
    @api.depends('payroll_type', 'line_ids','employee_id')
    def get_type_amount(self):
        for rec in self:
            rec.type_amount = 0.0
            if rec.payroll_type == 'basic_salary':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('basic_salary'))
            if rec.payroll_type == 'transport_allowance':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('transport_allowance'))
            if rec.payroll_type == 'housing_allowance':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('housing_allowance'))
            if rec.payroll_type == 'meal_allowance':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('meal_allowance'))
            if rec.payroll_type == 'dressing':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('dressing'))
            if rec.payroll_type == 'employer_pension':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('employer_pension'))
            if rec.payroll_type == 'employee_pension':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('employee_pension'))
            if rec.payroll_type == 'medical_plan':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('medical_plan'))
            if rec.payroll_type == 'paye':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('paye'))
            if rec.payroll_type == 'leave_allowance':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('leave_allowance'))
            if rec.payroll_type == 'gratutity_plan':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('gratutity_plan'))
            if rec.payroll_type == 'monthly_gross':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('monthly_gross'))
            if rec.payroll_type == 'life_assurance_plan':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('life_assurance_plan'))
