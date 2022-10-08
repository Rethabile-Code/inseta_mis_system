from odoo import fields, models, _


class InsetaOrganisation(models.Model):
    _inherit = "inseta.organisation"

    dg_count = fields.Integer(compute="_compute_dg_count")

    def _compute_dg_count(self):
        for rec in self:
            rec.dg_count = self.env['inseta.dgapplication'] \
                .sudo() \
                .search_count([('organisation_id','=',rec.id)])
        return True