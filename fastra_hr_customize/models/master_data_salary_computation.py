from odoo import fields,models,api

class FastraMasterSalaryComputation(models.Model):
    _name = 'fastra.master.salary.computation'

    fastra_payroll_id = fields.Many2one('fastra.payroll', string="Payroll")
    job_group_id = fields.Many2one('job.group', string="Job Group")
    step_id = fields.Many2one('step.step', string="Step")
    basic_salary = fields.Float("Basic")
    housing_allowance = fields.Float("Housing")
    transport_allowance = fields.Float("Transport")
    meal_allowance = fields.Float("Meal Allowance")
    dressing = fields.Float("Dressing")
    life_assurance_plan = fields.Float('Life Assurance Plan')