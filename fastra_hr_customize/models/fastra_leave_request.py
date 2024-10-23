from odoo import models,fields,api, _

class FastraLeaveRequest(models.Model):
    _name = "fastra.leave.request"

    employee_id = fields.Many2one('hr.employee',string="Employee Name")
    department_id= fields.Many2one('hr.department',string="Department")
    manager_reporter_id = fields.Many2one('hr.employee', string="Manager/Superior Reporting to")
    type_of_absence = fields.Selection([('sick', 'Sick'),
                                        ('bereavement', 'Bereavement'),
                                        ('time_off_without_pay', 'Time Off without pay'),
                                        ('annual_leave', 'Annual Leave'),
                                        ('maternity', 'Maternity'),
                                        ('other', 'Other')], string="Type of Absence Requested")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('send_supervisor', 'Send to Supervisor'),
        ('send_to_hr', 'Send To HR'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),

    ], string='Status', index=True, default='draft', copy=False)
    other_reason = fields.Char("Other Reason")
    date_from = fields.Datetime('Start Date',default=fields.Datetime.now)
    date_to = fields.Datetime('End Date',default=fields.Datetime.now)
    absence_reason = fields.Text("Reasons for Absence")

    def send_supervisor(self):
        self.state = 'send_supervisor'
    def send_hr(self):
        self.state = 'send_to_hr'
    def approve(self):
        self.state = 'approve'
    def reject(self):
        self.state = 'reject'
    def set_draft(self):
        self.state = 'draft'