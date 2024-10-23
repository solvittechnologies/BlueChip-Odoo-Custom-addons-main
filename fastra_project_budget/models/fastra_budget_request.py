# -*- coding: utf-8 -*-
from odoo import models, fields, api , _

class ProjectbudgetRequest(models.Model):
    _name = 'fastra.budget.request'
    _inherit = ['mail.thread']
    _rec_name ='project_detail_id'

    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True,
                                 readonly=True, states={'draft': [('readonly', False)]},
                                 track_visibility='always', ondelete='restrict',
                                 help="You can find a contact by its Name, TIN, Email or Internal Reference.")
    state = fields.Selection([('draft', 'Draft'), ('to_approval', 'Send for Approval'), ('approved', 'Approved'),  ('reject', 'Rejected') ],
                             string='Status', index=True, readonly=True, default='draft',
                             copy=False,
                            )
    project_detail_id = fields.Many2one('account.analytic.account', string="Project")
    project_manager = fields.Many2one('hr.employee', "Project Manager")
    project_description = fields.Char("Project Description")
    project_duration = fields.Char("Project Duraion")
    request_date = fields.Date("Request Date",)
    project_account_code = fields.Char("Project Code")
    project_location = fields.Many2many('stock.location',string="Project Location")
    site = fields.Char("Site ID")
    project_details = fields.Char("Details")
    po_number_id = fields.Many2one('fastra.project.master.data',string = 'Customer PO', domain=[('is_customer_po','=',True)])
    po_amount = fields.Float("PO amount",related = 'po_number_id.po_amount')
    project_number = fields.Char("Project  Number")
    project_narration = fields.Char("Project Narration") 
    file_attachment = fields.Binary("File Attachment")  


    def action_button_send_for_approval(self):
        self.write({'state': 'to_approval'})

    def action_button_project_budget_approve(self):
        self.write({'state': 'approved'})
        self.po_number_id.state = 'approved'

    def action_button_project_budget_reject(self):
        self.write({'state': 'reject'})
        view_id = self.env.ref('fastra_project_budget.update_rejection_reason_note_form').id
        context={'default_project_analysis_request_id': self.id,
                }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'res_model': 'rejection.reason.popup.wizard',
            'target': 'new',
            'context': context,
            'views': [[view_id, 'form']],  
        }
