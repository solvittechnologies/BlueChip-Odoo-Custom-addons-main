from odoo import models, fields, api

class fastraHrCancel(models.TransientModel):

    """ Ask a reason for the Salary Pyroll cancellation."""
    _name = 'fastra.hr.cancel'
    _description = __doc__

    reason = fields.Text(
        string='Reason',
        required=True)

    @api.multi
    def confirm_cancel(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        pr_ids = self._context.get('active_ids')
        if pr_ids is None:
            return act_close
        pr_id = self.env['fastra.payroll'].browse(pr_ids)
        pr_id.cancel_reason = self.reason
        pr_id.reject()
        return act_close