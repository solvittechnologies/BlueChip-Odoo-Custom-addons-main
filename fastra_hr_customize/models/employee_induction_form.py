from odoo import fields, models, api

class EmployeeInductionForm(models.Model):
    _name = 'employee.induction.from'

    name = fields.Many2one('hr.employee',string="Employee Name")
    designation = fields.Many2one('hr.job',string="Designation")
    level = fields.Char("Level")
    department = fields.Many2one('hr.department',string="Department")
    supervisor_name = fields.Many2one('hr.employee', string="Supervisor’s Name")
    date =fields.Date("Date")
    employee_induction_form_line_ids = fields.One2many('employee.induction.from.line','employee_induction_form_id',string="Induction Form Ids")
    hod_signature_date = fields.Date("HOD – Signature and Date")
    head_admin_signature_date = fields.Many2one('hr.employee',string="Head, Human Resources & Admin")
    @api.multi
    @api.onchange('name')
    def onchange_name(self):
        self.designation = self.name.job_id.id
        self.level = self.name.job_title
        self.department = self.name.department_id.id


class EmployeeInductionFormLines(models.Model):
    _name = 'employee.induction.from.line'

    basic_process = fields.Many2one('employee.induction.master.data',string="Basic Process")
    process_action = fields.Char(string="Process Action")
    status = fields.Char(string="Status")
    hr_officer_signature_date = fields.Date("HR Officer Signature/Date")
    employee_induction_form_id = fields.Many2one('employee.induction.from',string="Employee Induction Form Id")

    @api.multi
    @api.onchange('basic_process')
    def onchange_basic_process(self):
        self.process_action = self.basic_process.action
        self.status = self.basic_process.status
