from odoo import models, fields, api


class InterviewRatingGuide(models.Model):
    _name = 'interview.rating.guide'
    _description = 'Interview Rating Guide'

    date = fields.Date('Date')
    applicant = fields.Char("Applicant")
    position_id = fields.Many2one('hr.job', string="Position")
    interviewer_id = fields.Many2one('hr.employee', string="Interviewer")
    is_overall_excellent = fields.Boolean("Excellent")
    is_overall_above_average = fields.Boolean("Above Average")
    is_overall_average = fields.Boolean("Average")
    is_overall_marginal = fields.Boolean("Marginal")
    line_ids = fields.One2many('interview.rating.guide.line', 'interview_rating_id', string="Line")
    comment = fields.Text("Comment")


class InterviewRatingLine(models.Model):
    _name = 'interview.rating.guide.line'
    _description = 'Interview Rating Guide Line'

    interview_rating_id = fields.Many2one('interview.rating.guide', string="Interview Rating")
    name = fields.Char('Category')
    is_excellent = fields.Boolean("Excellent")
    is_above_average = fields.Boolean("Above Average")
    is_average = fields.Boolean("Average")
    is_marginal = fields.Boolean("Marginal")

    @api.multi
    @api.onchange('is_excellent')
    def onchange_excellent(self):
        if self.is_excellent:
            self.is_above_average = False
            self.is_average = False
            self.is_marginal = False

    @api.multi
    @api.onchange('is_above_average')
    def onchange_above_average(self):
        if self.is_above_average:
            self.is_excellent = False
            self.is_average = False
            self.is_marginal = False

    @api.multi
    @api.onchange('is_average')
    def onchange_average(self):
        if self.is_average:
            self.is_above_average = False
            self.is_excellent = False
            self.is_marginal = False

    @api.multi
    @api.onchange('is_marginal')
    def onchange_marginal(self):
        if self.is_marginal:
            self.is_above_average = False
            self.is_average = False
            self.is_excellent = False
