from odoo import fields, models, api

class EmployeeChecklistForStaff(models.Model):
    _name = 'employee.checklist.for.staff'

    name = fields.Char("Name")
