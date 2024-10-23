
from odoo import models, fields, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64
from io import BytesIO

Months = [('January', 'January'),
          ('february', 'February'),
          ('march', 'March'),
          ('april', 'April'),
          ('may', 'May'),
          ('june', 'June'),
          ('july', 'July'),
          ('august', 'August'),
          ('september', 'September'),
          ('october', 'October'),
          ('november', 'November'),
          ('december', 'December')]


class HRPayslipCustom(models.Model):
    _name = 'hr.payslip.custom'

    name = fields.Char("Payslip Name")
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], string="State", default='draft')
    location_id = fields.Many2one('stock.location', "Location")
    date_from = fields.Date(string='Date From', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            )
    date_to = fields.Date(string='Date To', required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          )
    month = fields.Selection(Months, string="Month")
    employee_tag = fields.Char("Employee Tag")
    account_analytic_id = fields.Many2one('account.analytic.account', "Analytic Account")
    payslip_custom_line_ids = fields.One2many('hr.payslip.custom.line','payslip_custom_id',string="Lines")

    account_tax_id = fields.Many2one('account.tax', 'Tax')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal', states={'validated': [('readonly', True)]},)
    move_ids = fields.Many2many('account.move', 'hr_custom_move_rel', 'hr_custom_id', 'move_id', string="Moves")
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')

    def set_line_employee_ref(self):
        count = 1
        sort_month = ''
        if self.month == 'January':
            sort_month = 'JAN'
        elif self.month == 'february':
            sort_month = 'FEB'
        elif self.month == 'march':
            sort_month = 'MAR'
        elif self.month == 'april':
            sort_month = 'APR'
        elif self.month == 'may':
            sort_month = 'MAY'
        elif self.month == 'june':
            sort_month = 'JUN'
        elif self.month == 'july':
            sort_month = 'JUL'
        elif self.month == 'august':
            sort_month = 'AUG'
        elif self.month == 'september':
            sort_month = 'SEP'
        elif self.month == 'october':
            sort_month = 'OCT'
        elif self.month == 'november':
            sort_month = 'NOV'
        elif self.month == 'december':
            sort_month = 'DEC'
        for line in self.payslip_custom_line_ids:
            line.update({'employee_code': sort_month + "{:03d}".format(count)})
            count += 1

    @api.model
    def create(self, values):
        res = super(HRPayslipCustom, self).create(values)
        res.set_line_employee_ref()
        return res

    @api.multi
    def write(self, vals):
        res = super(HRPayslipCustom, self).write(vals)
        self.set_line_employee_ref()
        return res

    @api.multi
    def action_validate(self):
        if not self.journal_id:
            raise UserError(_('Journal is not set!! Please Set Journal.'))
        if not self.account_credit or not self.account_debit:
            raise UserError(_('You need to set debit/credit account for validate.'))

        gross_amount = 0.0
        for line in self.payslip_custom_line_ids:
            gross_amount += line.gross

        debit_vals = {
            'name': self.name,
            'debit': gross_amount,
            'credit': 0.0,
            'account_id': self.account_debit.id,
        }
        credit_vals = {
            'name': self.name,
            'debit': 0.0,
            'credit': gross_amount,
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
        self.write({'move_ids': [(4, move.id)],
                    'state': 'validated'})

        vals = {'name': self.name,
                'location_id': self.location_id and self.location_id.id or False,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'month': self.month,
                'employee_tag': self.employee_tag,
                'account_analytic_id': self.account_analytic_id and self.account_analytic_id.id or False,
                'line_ids': []}
        for line in self.payslip_custom_line_ids:
            vals['line_ids'].append((0, 0, {'beneficiary_name': line.employee_id and line.employee_id.name or False,
                                            'payment_amount': line.pay_amount,
                                            'transaction_reference_number': line.employee_code}))
        self.env['salaries.excel.sheet'].sudo().create(vals)
        return

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

    def generate_excel(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)

        worksheet = workbook.add_worksheet('Payroll Report')

        bold = workbook.add_format({'bold': True})
        border = workbook.add_format({'border': 1})
        format1 = workbook.add_format({'bold': True, 'border': 1})

        row = 0
        worksheet.write(row, 0, 'Employee', format1)
        worksheet.write(row, 1, 'Employee ID', format1)
        worksheet.write(row, 2, 'Working Hours', format1)
        worksheet.write(row, 3, 'OT Hours', format1)
        worksheet.write(row, 4, 'SUN OT Hours', format1)
        worksheet.write(row, 5, 'PUB OT Hours', format1)
        worksheet.write(row, 6, 'Basic Salary', format1)
        worksheet.write(row, 7, 'Annual Leave', format1)
        worksheet.write(row, 8, 'Feeding', format1)
        worksheet.write(row, 9, 'Furniture', format1)
        worksheet.write(row, 10, 'Housing', format1)
        worksheet.write(row, 11, 'Medical', format1)
        worksheet.write(row, 12, 'Ordinary Over-Time', format1)
        worksheet.write(row, 13, 'Public Over-Time', format1)
        worksheet.write(row, 14, 'Sunday Over-Time', format1)
        worksheet.write(row, 15, 'Transport', format1)
        worksheet.write(row, 16, 'Utility', format1)
        worksheet.write(row, 17, 'Bonus', format1)
        worksheet.write(row, 18, 'Gross', format1)
        worksheet.write(row, 19, 'Pension', format1)
        worksheet.write(row, 20, 'Other Statutory Deduction', format1)
        worksheet.write(row, 21, 'Tax-Free Allowance', format1)
        worksheet.write(row, 22, 'Consolidated Relief (CRA)', format1)
        worksheet.write(row, 23, 'Gross Income Relief', format1)
        worksheet.write(row, 24, 'Taxable amount', format1)
        worksheet.write(row, 25, 'PAYE', format1)
        worksheet.write(row, 26, 'Net', format1)
        worksheet.write(row, 27, 'ABSENT DEDUCTION', format1)
        worksheet.write(row, 28, 'Loan', format1)
        worksheet.write(row, 29, 'Payroll DEDUCTION', format1)
        worksheet.write(row, 30, 'Non Taxable Payroll DEDUCTION', format1)
        worksheet.write(row, 31, 'Union Dues', format1)
        worksheet.write(row, 32, 'Pay Amount', format1)

        row += 1
        for line in self.payslip_custom_line_ids:
            worksheet.write(row, 0, line.employee_id and line.employee_id.name or '')
            worksheet.write(row, 1, line.employee_code or '')
            worksheet.write(row, 2, line.working_hours or '')
            worksheet.write(row, 3, line.ot_hours or '')
            worksheet.write(row, 4, line.sun_ot_hours or '')
            worksheet.write(row, 5, line.pub_ot_hours or '')
            worksheet.write(row, 6, line.basic_salary or '')
            worksheet.write(row, 7, line.annual_leave or '')
            worksheet.write(row, 7, line.feeding or '')
            worksheet.write(row, 7, line.furniture or '')
            worksheet.write(row, 7, line.housing or '')
            worksheet.write(row, 7, line.medical or '')
            worksheet.write(row, 7, line.ordinary_overtime or '')
            worksheet.write(row, 7, line.public_overtime or '')
            worksheet.write(row, 7, line.sunday_overtime or '')
            worksheet.write(row, 7, line.transport or '')
            worksheet.write(row, 7, line.utility or '')
            worksheet.write(row, 7, line.bonus or '')
            worksheet.write(row, 7, line.gross or '')
            worksheet.write(row, 7, line.pension or '')
            worksheet.write(row, 7, line.other_statutory_deduction or '')
            worksheet.write(row, 7, line.tax_free_allowance or '')
            worksheet.write(row, 7, line.consolidated_relief or '')
            worksheet.write(row, 7, line.gross_income_relief or '')
            worksheet.write(row, 7, line.taxable_amount or '')
            worksheet.write(row, 7, line.paye or '')
            worksheet.write(row, 7, line.net or '')
            worksheet.write(row, 7, line.absent_deduction or '')
            worksheet.write(row, 7, line.loan_deduction or '')
            worksheet.write(row, 7, line.payroll_deduction or '')
            worksheet.write(row, 7, line.non_taxable_payroll_deduction or '')
            worksheet.write(row, 7, line.union_dues or '')
            worksheet.write(row, 7, line.pay_amount or '')

        workbook.close()
        file_data.seek(0)
        self.write(
            {'excel_file': base64.encodebytes(file_data.read()),
             'file_name': 'Payroll.xlsx'})

        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=hr.payslip.custom&field=%s&filename_field=%s&id=%s' % (
                'excel_file', 'file_name', self.id),
            'target': 'current'
        }

    # def line_onchange_methods(self):
    #     for line in self.payslip_custom_line_ids:
    #         line.get_gross_amount()
    #         line.get_gross_income_relief()
    #         line.get_taxable_amount()
    #         line.onchange_paye_amount()
    #         line.get_net()
    #         line.get_pay_amount()


class HRPayslipCustomLine(models.Model):
    _name = 'hr.payslip.custom.line'

    payslip_custom_id = fields.Many2one('hr.payslip.custom', "Payslip")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    employee_code = fields.Char('Employee ID')
    working_hours = fields.Float('Working Hours')
    ot_hours = fields.Float("OT Hours")
    sun_ot_hours = fields.Float("SUN OT Hours")
    pub_ot_hours = fields.Float("PUB OT Hours")
    basic_salary = fields.Float('Basic Salary')
    annual_leave = fields.Float('Annual Leave')
    feeding = fields.Float('Feeding')
    furniture = fields.Float('Furniture')
    housing = fields.Float('Housing')
    medical = fields.Float('Medical')
    ordinary_overtime = fields.Float('Ordinary Over-Time')
    public_overtime = fields.Float('Public Over-Time')
    sunday_overtime = fields.Float('Sunday Over-Time')
    transport = fields.Float('Transport')
    utility = fields.Float('Utility')
    bonus = fields.Float('Bonus')
    gross = fields.Float('Gross')
    gross_yearly = fields.Float('Yearly Gross', compute='get_yearly_gross')
    pension = fields.Float('Pension')
    other_statutory_deduction = fields.Float('Other Statutory Deduction')
    tax_free_allowance = fields.Float('Tax-Free Allowance')
    consolidated_relief = fields.Float('Consolidated Relief (CRA)', default=200000)
    gross_income_relief = fields.Float('Gross Income Relief')
    taxable_amount = fields.Float('Taxable amount')
    paye = fields.Float('PAYE')
    net = fields.Float('Net')
    absent_deduction = fields.Float('ABSENT DEDUCTION')
    loan_deduction = fields.Float('Loan')
    payroll_deduction = fields.Float('Payroll DEDUCTION')
    non_taxable_payroll_deduction = fields.Float('Non Taxable Payroll DEDUCTION')
    union_dues = fields.Float('Union Dues')
    pay_amount = fields.Float('Pay Amount')

    leave_grant = fields.Float('Leave Grant')
    payoff = fields.Float('Payoff')
    others = fields.Float('Others')
    iou = fields.Float('IOU')
    other_deduction = fields.Float('Other DEDUCTION')
    milk = fields.Float('Milk')

    @api.multi
    @api.onchange('gross', 'consolidated_relief', 'gross_income_relief', 'pension')
    def onchange_paye_amount(self):
        paye = 0.0
        cra = self.consolidated_relief
        gross_salary_year = self.gross * 12
        if gross_salary_year < 300000:
            paye = (gross_salary_year * 1) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        gross_income_relief = (gross_salary_year * 20 ) / 100
        taxable_amount = gross_salary_year - (cra + gross_income_relief) - self.pension
        if taxable_amount > 3200000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            paye += (500000 * 15) / 100
            paye += (500000 * 19) / 100
            paye += (1600000 * 21) / 100
            taxable_amount -= 3200000
            paye += (taxable_amount * 24) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 1600000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            paye += (500000 * 15) / 100
            paye += (500000 * 19) / 100
            taxable_amount -= 1600000
            paye += (taxable_amount * 21) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 1100000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            paye += (500000 * 15) / 100
            taxable_amount -= 1100000
            paye += (taxable_amount * 19) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 600000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            taxable_amount -= 600000
            paye += (taxable_amount * 15) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 300000:
            paye += (300000 * 7) / 100
            taxable_amount -= 300000
            paye += (taxable_amount * 11) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        else:
            paye += (taxable_amount * 7) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return

    @api.multi
    @api.onchange('basic_salary', 'annual_leave', 'feeding', 'furniture', 'housing', 'medical',
                 'ordinary_overtime', 'public_overtime', 'sunday_overtime', 'transport', 'utility', 'bonus')
    def get_gross_amount(self):
        for rec in self:
            rec.gross = rec.basic_salary + rec.annual_leave + rec.feeding + rec.furniture + rec.housing + rec.medical + rec.ordinary_overtime + rec.public_overtime + rec.sunday_overtime + rec.transport + rec.utility + rec.bonus

    @api.multi
    @api.depends('gross')
    def get_yearly_gross(self):
        for rec in self:
            rec.gross_yearly = rec.gross * 12

    @api.multi
    @api.onchange('gross_yearly')
    def get_gross_income_relief(self):
        for rec in self:
            rec.gross_income_relief = (rec.gross_yearly * 20 ) / 100

    @api.multi
    @api.onchange('gross_yearly', 'pension', 'other_statutory_deduction',
                 'tax_free_allowance', 'consolidated_relief', 'gross_income_relief')
    def get_taxable_amount(self):
        for rec in self:
            if rec.gross_yearly > 300000:
                rec.taxable_amount = rec.gross_yearly - (rec.consolidated_relief + rec.gross_income_relief) - rec.pension
            else:
                rec.taxable_amount = 0.0

    @api.multi
    @api.onchange('paye', 'gross')
    def get_net(self):
        for rec in self:
            rec.net = rec.gross - rec.paye

    @api.multi
    @api.onchange('union_dues', 'net', 'absent_deduction', 'loan_deduction', 'payroll_deduction',
                 'non_taxable_payroll_deduction')
    def get_pay_amount(self):
        for rec in self:
            rec.pay_amount = rec.net - rec.absent_deduction - rec.loan_deduction - rec.payroll_deduction - rec.non_taxable_payroll_deduction - rec.union_dues