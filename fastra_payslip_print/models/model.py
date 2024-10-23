# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ReportHRPayslipCustomLineReportWizard(models.TransientModel):
    _name = 'report.fastra_payslip_print.report.wizard'

    basic_salary = fields.Boolean("Basic")
    housing_allowance = fields.Boolean("Housing")
    transport_allowance = fields.Boolean("Transport")
    meal_allowance = fields.Boolean("Meal Allowance")
    dressing = fields.Boolean("Dressing")
    employer_pension = fields.Boolean("Employer's Pension")
    paye = fields.Boolean('Paye')
    medical_plan = fields.Boolean("Medical plan")
    leave_allowance = fields.Boolean("Leave Allowance")
    gratutity_plan = fields.Boolean("Gratutity Plan")
    monthly_gross = fields.Boolean('Monthly Gross/ Monthly emolument')
    life_assurance_plan = fields.Boolean('Life Assurance Plan')
    resid = fields.Integer("res id")

    @api.multi
    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'values':self.id
        }
        return self.env.ref('fastra_payslip_print.hr_payslip_custom_report').report_action(self,data)

class ReportHRPayslipCustomLibeReportView(models.AbstractModel):
    _name = 'report.fastra_payslip_print.hr_payslip_custom_report_view'
    
    @api.model
    def _get_report_values(self, docids, data):

        getwizardValue=self.env['report.fastra_payslip_print.report.wizard'].sudo().search([('id','=',data['values'])])


        doc= self.env['fastra.hr.payroll.line'].sudo().search([('id','=',getwizardValue.resid)])
        currency=self.env.ref("base.main_company").currency_id
        company=self.env.user.company_id
        
        return {
            'doc_ids': data['ids'],
            'doc_model': "fastra.hr.payroll.line",
            'docs':doc,
            'currency':currency,
            'company':company,
            'o':doc,
            'getwizardValue':getwizardValue
        }

class HRPayslipCustomLibeReport(models.Model):
    _inherit = "fastra.hr.payroll.line"

    def launch_wizard(self):
        wizard_id = self.env['report.fastra_payslip_print.report.wizard'].create({"resid":self.id}).id
        return {
            'name': 'Salary Payroll',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'report.fastra_payslip_print.report.wizard',
            'res_id': wizard_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
 

    
    

# class HRPayslipCustomLibeReport(models.Model):
#     _inherit = "hr.payslip.custom"
    
 

#     @api.multi
#     def get_all_report(self):
#         _logger.error(self.payslip_custom_line_ids)
#         for d in self.payslip_custom_line_ids:
#             _logger.error("_logger.error(d)_logger.error(d)_logger.error(d)")
#             _logger.error(d)
#             return self.env.ref('fastra_payslip_print.hr_payslip_custom_report').report_action(d.id)