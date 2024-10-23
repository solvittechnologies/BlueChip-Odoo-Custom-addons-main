# -*- coding: utf-8 -*-
from odoo import models, fields, api , _
from odoo.osv import expression
class ProjectMasterData(models.Model):
    _name = 'fastra.project.master.data'
    _rec_name = 'po_number'

    po_number = fields.Char(string="PO number")
    po_amount = fields.Float("PO Amount",compute="compute_po_amount")
    project_code = fields.Char("Project Code")
    state = fields.Selection(
        [('approved', 'Approved'), ('non', 'Non Apprved')],
        string='Status', default='non',)
    master_line_ids = fields.One2many('fastra.project.master.data.line','master_data_id',string="Lines")
    is_customer_po = fields.Boolean("Is Customer PO")
    date = fields.Datetime('Datetime', default=lambda self: fields.datetime.now())


    def compute_po_amount(self):
        for rec in self:
            for lines in rec.master_line_ids:
                rec.po_amount += lines.amount

    def name_get(self):
        res = []
        for rec in self:
            name = ''
            if rec.po_number:
                if rec.project_code:
                    name = "[%s] %s" % (rec.project_code, rec.po_number)
                else:
                    name = "%s" % rec.po_number
            if rec.project_code:
                if rec.po_number:
                    name = "[%s] %s" % (rec.project_code, rec.po_number)
                else:
                    name = "%s" % rec.project_code
            res += [(rec.id, name)]
        return res


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        args = args or []
        domain = ['|', ('po_number', operator, name), ('project_code', operator, name)]
        customer_po_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(customer_po_ids).name_get()


class ProjectMasterDataLine(models.Model):
    _name = 'fastra.project.master.data.line'

    scope = fields.Char("Scope")
    unit_cost = fields.Float("Unit Cost")
    quantity = fields.Integer("Quantity")
    amount = fields.Float("Amount", compute="get_amount")
    master_data_id = fields.Many2one('fastra.project.master.data',string="Master Data Id")

    @api.multi
    @api.depends('quantity', 'unit_cost')
    def get_amount(self):
        for rec in self:
            rec.amount = rec.unit_cost * rec.quantity
