# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaBulkDgRecommendWizard(models.TransientModel):
    """This wizard can be used for bulk recommendation for DG 
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.dgbulkrecommend.wizard"
    _description = "DG Bulk Recommend Wizard"

    @api.model
    def default_get(self, fields):
        res = super(InsetaBulkDgRecommendWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        res.update({
            'dgrecommendation_id': active_ids[0] if active_ids else False,
        })
        return res

    dgrecommendation_id = fields.Many2one('inseta.dgrecommendation')
    stage = fields.Char(default="evaluation")
    option = fields.Selection([
        ('Recommend', 'Recommend'),
    ])
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    dgec_recommendation_sheet = fields.Binary(string="DGEC Recommendation Sheet")
    dgac_recommendation_sheet = fields.Binary(string="DGAC Recommendation Sheet")

    file_name = fields.Char()
    file_name2 = fields.Char()

    comment = fields.Text(string='Comment')

    

    def bulk_recommend(self):
        self.ensure_one()
        if self.stage == "evaluation": #evaluation committee DGEC
            if self.option == 'Query': #Rework
                self.dgrecommendation_id.rework_application(self.comment)
            if self.option == 'Recommend':
                if self.dgec_recommendation_sheet:
                    self.dgrecommendation_id.write({
                        'dgec_recommendation_sheet': self.dgec_recommendation_sheet,
                        'file_name': self.file_name
                    })
                self.dgrecommendation_id.recommend_application(self.comment)
        if self.stage == "adjudication": #evaluation committee DGEC
            if self.option == 'Query': #Rework
                self.dgrecommendation_id.with_context(is_adjudication=True).rework_application(self.comment)
            if self.option == 'Recommend':
                if self.dgac_recommendation_sheet:
                    self.dgrecommendation_id.write({
                        'dgac_recommendation_sheet': self.dgac_recommendation_sheet,
                        'file_name2': self.file_name2
                    })
                self.dgrecommendation_id.with_context(is_adjudication=True).recommend_application(self.comment)
            

        return {'type': 'ir.actions.act_window_close'}


