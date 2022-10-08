# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaSDFRecommendWizard(models.TransientModel):
    """This wizard can be used for recommend, not recommend , rework 
    This wizard is called during existing SDF organisation registration
    """

    _name = "inseta.sdf.recommend.wizard" #inseta_sdf_recommend_wizard
    _description = "SDF Recommendation/Approval Wizard"

    stage = fields.Char(default="recommend")
    option = fields.Selection([
        ('Recommend', 'Recommend'),
        ('Not Recommend', 'Not Recommend'),
        ('Query', 'Rework'),
    ])
    option2 = fields.Selection([
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
        ('Query', 'Rework'),
    ])

    comment = fields.Text(string='Comment')
    sdforg_id = fields.Many2one('inseta.sdf.organisation')

    @api.model
    def default_get(self, fields):
        res = super(InsetaSDFRecommendWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'sdforg_id': active_ids[0] if active_ids else False,
        })
        return res

    def sdf_recommend(self):
        self.ensure_one()
        if self.stage == "recommend":
            if self.option == 'Query': #Rework
                self.sdforg_id.rework_submission(self.comment)
            if self.option == 'Recommend':
                self.sdforg_id.recommend_submission(self.comment, status="Recommended")
            if self.option == 'Not Recommend':
                self.sdforg_id.recommend_submission(self.comment, status="Not Recommended")
        else: #approval stage
            if self.option2 == 'Query': #Rework
                self.sdforg_id.with_context(is_approval=True).rework_submission(self.comment)
            elif self.option2 == 'Reject': 
                self.sdforg_id.reject_submission(self.comment)
            elif self.option2 == 'Approve':
                self.sdforg_id.approve_submission(self.comment)

        return {'type': 'ir.actions.act_window_close'}