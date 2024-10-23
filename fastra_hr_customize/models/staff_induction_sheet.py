from odoo import fields, models, api

class StaffInductionSheet(models.Model):
    _name = 'staff.induction.sheet'

    name = fields.Many2one('hr.employee',string="Employee Name")
    position_job = fields.Many2one('hr.job', string="Position / Job")
    department = fields.Many2one('hr.department', string="Department")
    commencement_date = fields.Date("Commencement Date")
    staff_induction_line_ids = fields.One2many('staff.induction.sheet.line','staff_induction_id',string="Line Ids")

    conducted_by = fields.Many2one('hr.employee', string="Conducted by")
    employee = fields.Many2one('hr.employee', string="Employee")
    date_conducted = fields.Date("Date Conducted")

    @api.multi
    @api.onchange('name')
    def onchange_name(self):
        self.position_job = self.name.job_id.id
        self.department = self.name.department_id.id

class StaffInductionSheetLines(models.Model):
    _name = 'staff.induction.sheet.line'

    item = fields.Many2one('staff.induction.master.data',string="Item")
    yes_checkbox = fields.Boolean("Yes")
    no_checkbox = fields.Boolean("No")
    required_action =fields.Char("Required Action")
    resposible_person = fields.Many2one('hr.employee',string="Person Responsible")
    complition_date = fields.Date("Completion Date")
    staff_induction_id = fields.Many2one('staff.induction.sheet',string="Staff Induction Id")

    @api.onchange('yes_checkbox')
    def onchange_yes_checkbox(self):
        if self.yes_checkbox == True:
            self.no_checkbox = False

    @api.onchange('no_checkbox')
    def onchange_no_checkbox(self):
        if self.no_checkbox == True:
            self.yes_checkbox = False