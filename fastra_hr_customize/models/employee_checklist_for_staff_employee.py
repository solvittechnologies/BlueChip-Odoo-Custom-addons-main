from odoo import fields, models, api

class EmployeeChecklistForStaffEmployee(models.Model):
    _name = 'employee.checklist.for.staff.employee'
    _rec_name = 'staff_name'
    staff_name = fields.Many2one('hr.employee', string="Staff Name")
    no = fields.Char("NO")
    employee_checklist_staff_line_ids = fields.One2many('employee.checklist.for.staff.employee.line','employee_check_staf_id',string="Name")


class EmployeeChecklistForStaffEmployeeLine(models.Model):
    _name = 'employee.checklist.for.staff.employee.line'

    employee_checklist_staff_id = fields.Many2one('employee.checklist.for.staff', string="Name")
    yes_checkbox = fields.Boolean("Yes")
    no_checkbox = fields.Boolean("No")
    recipients_sign_date = fields.Date("Recipients Sign. & Date")
    Staff_sign_date = fields.Date("Staff Sign. & Date")
    employee_check_staf_id = fields.Many2one('employee.checklist.for.staff.employee', string="Employee Checklist Staff id")

    @api.onchange('yes_checkbox')
    def onchange_yes_checkbox(self):
        if self.yes_checkbox == True:
            self.no_checkbox = False

    @api.onchange('no_checkbox')
    def onchange_no_checkbox(self):
        if self.no_checkbox == True:
            self.yes_checkbox = False