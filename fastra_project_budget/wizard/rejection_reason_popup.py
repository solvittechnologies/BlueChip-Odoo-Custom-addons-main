# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, _


class RejactionReasonPopup(models.TransientModel):
    _name = 'rejection.reason.popup.wizard'
    
    
    project_analysis_request_id = fields.Many2one('fastra.budget.request',string="Project Request")
    project_analysis_request_fund_id = fields.Many2one('fastra.project.fund.request',string="Project Fund Request")
    project_analysis_id = fields.Many2one('fastra.project.analysis',string = "Project Analysis")
    rejection_note = fields.Char("Rejection Note")
    
    def rejection_reason_note(self):
        project_analysis_request = self.project_analysis_request_id
        if project_analysis_request:
            update_vals = {'project_details':self.rejection_note}
            project_analysis_request.write(update_vals)
        project_analysis_fund = self.project_analysis_request_fund_id
        if project_analysis_fund:
            update_vals = {'project_details':self.rejection_note}
            project_analysis_fund.write(update_vals)
        project_analysis = self.project_analysis_id
        if project_analysis:
            update_vals = {'project_details':self.rejection_note}
            project_analysis.write(update_vals)
        
        
        