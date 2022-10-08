# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaDgApplicationRecommendWizard(models.TransientModel):
    """This wizard can be used for rework , recommend, not recommend DG 
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.dgapplication.recommend.wizard"
    _description = "DG Application Recommend Wizard"

    @api.model
    def default_get(self, fields):
        res = super(InsetaDgApplicationRecommendWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        dg = self.env['inseta.dgapplication'].search([('id','in', active_ids)],limit=1)

        res.update({
            'dgapplication_id': active_ids[0] if active_ids else False,
            # 'no_learners_recommended': dg.no_learners_recommended,
            # 'amount_total_recommended': dg.amount_total_recommended,
            # 'amount_recommended_perlearner': dg.amount_recommended_perlearner,
            # 'no_learners': dg.no_learners,
            # 'cost_per_student': dg.cost_per_student,
            'dgtype_id': dg.dgtype_id.id,
            'dgtype_code': dg.dgtype_code
        })
        return res

    dgapplication_id = fields.Many2one('inseta.dgapplication')
    dgtype_id = fields.Many2one('res.dgtype')
    dgtype_code = fields.Char()

    stage = fields.Char(default="recommend")
    option = fields.Selection([
        ('Recommend', 'Recommend'),
        ('Not Recommend', 'Not Recommend'),
        ('Query','Query')
    ])
    comment = fields.Text(string='Comment')

    #TODO: Delete fields below , nov 10, 2021
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    no_learners = fields.Integer(
        'No. of Interns/Learners', 
        help="Total no of learners as captured by employer"
    )
    no_learners_recommended = fields.Integer('No. Recommended')
    cost_per_student = fields.Monetary("Cost Per Learner") #bursary and skills
    amount_recommended_perlearner = fields.Monetary(
        'Amt. Recommended Per Learner',  #bursary and skills
    )
    amount_total_recommended =fields.Monetary(
        'Amt. Recommended', 
        help="Amount in user currency"
    )


    def dgapplication_recommend(self):
        self.ensure_one()
        if self.stage == "recommend": #evaluation committee DGEC
            if self.option == 'Query': #Rework
                self.dgapplication_id.rework_application(self.comment)
            if self.option == 'Recommend':
                self.dgapplication_id.recommend_application(self.comment, status="Recommended")
            if self.option == 'Not Recommend':
                self.dgapplication_id.recommend_application(self.comment, status="Not Recommended")

        if self.stage == "adjudication": #evaluation committee DGAC
            if self.option == 'Query': #Rework
                self.dgapplication_id.with_context(is_adjudication=True).rework_application(self.comment)
            if self.option == 'Recommend':
                self.dgapplication_id.with_context(is_adjudication=True).recommend_application(self.comment, status="Recommended")
            if self.option == 'Not Recommend':
                self.dgapplication_id.with_context(is_adjudication=True).recommend_application(self.comment, status="Not Recommended")

        return {'type': 'ir.actions.act_window_close'}