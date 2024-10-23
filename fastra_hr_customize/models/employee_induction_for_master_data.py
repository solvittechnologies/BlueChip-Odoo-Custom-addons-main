from odoo import fields, models, api

class EmployeeInductionForMasterData(models.Model):
    _name = 'employee.induction.master.data'

    name = fields.Char("Basic Process")
    action = fields.Char("Process Action")
    status = fields.Char("Status")

class EmployeeInductionForMasterData(models.Model):
    _name = 'staff.induction.master.data'

    name = fields.Char("ITEM")