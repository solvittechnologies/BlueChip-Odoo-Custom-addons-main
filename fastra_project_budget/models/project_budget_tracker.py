from odoo import models, fields, api, _

class Tracker(models.Model):
    _name = 'fastra.project.budget.tracker'
    _inherit = ['mail.thread']

    project_manager = fields.Many2one('hr.employee', "Project Manager")
    project_description = fields.Char("Project Description")
    project_duration = fields.Char("Project Duration")
    project_account_code = fields.Char("Project Code")
    request_date = fields.Date("Request Date")
    site = fields.Char("Site ID")
    project_location = fields.Many2many('stock.location', string="Project Location")
    po_number_id = fields.Many2one('fastra.project.master.data', string='Customer PO',domain=[('is_customer_po','=',True)])
    po_amount = fields.Float("PO amount", related='po_number_id.po_amount')
    project_details = fields.Text("Details")
    approved_fund_allocated = fields.Float("Disburse Amount")
    approved_retirement_amount = fields.Float("Retirement Amount")
    caf_approved_amount = fields.Float("CAF Approved Amount")
    approved_amount_balance = fields.Float("Approved Amount Balance")
    move_ids = fields.Many2many('account.move', 'hr_custom_move_rel', 'hr_custom_id', 'move_id', string="Moves",
                                compute='get_move_ids')
    project_detail_id = fields.Many2one('account.analytic.account', string="Project")
    caf_id = fields.Many2one('fastra.project.analysis', string="CAF NO")
    profit_loss = fields.Float("Profit and Loss")
    disbursement_id = fields.Many2one('fastra.project.fund.request', string="Disbursement")
    state = fields.Selection([('start', 'Start'), ('complete', 'Complete')], string='State')


