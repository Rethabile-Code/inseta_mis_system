# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaWspAtrValidateWizard(models.TransientModel):
    """This wizard can be used for recommend, not recommend , rework 
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.wspatr.validate.wizard"
    _description = "WSP/ATR Validate Wizard"

    stage = fields.Char(default="validation")
    option = fields.Selection([
        ('Evaluated', 'Evaluated'),
        # ('Not Recommend', 'Not Recommend'),
        ('Query', 'Query'),
    ])
    option2 = fields.Selection([
        ('Recommended_For_Approval', 'Recommend For Approval'),
        ('Recommended_For_Rejection', 'Recommend For Rejection'),
        ('Query', 'Query'),
    ])
    option3 = fields.Selection([
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
        ('Query', 'Query'),
    ])

    comment = fields.Text(string='Comment')
    # wspatr_id = fields.Many2one('inseta.wspatr')
    evaluation_id = fields.Many2one('inseta.wspatr.evaluation')

    @api.model
    def default_get(self, fields):
        res = super(InsetaWspAtrValidateWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'evaluation_id': active_ids[0] if active_ids else False,
        })
        return res

    def wspatr_validate(self):
        self.ensure_one()
        if self.stage == "validation":
            if self.option == 'Query': #Rework
                self.evaluation_id.rework_submission(self.comment)
            else:
                self.evaluation_id.evaluate_submission()
            # if self.option == 'Not Recommend':
            #     self.wspatr_id.recommend_submission(self.comment, status="Not Recommended")
        elif self.stage == "assessment":
            if self.option2 == 'Query': #Rework
                self.evaluation_id.with_context(is_assessment=True).rework_submission(self.comment)
            else:
                self.evaluation_id.with_context(is_assessment=True).assess_submission(self.option2)
        else: #evaluation stage
            if self.option3 == 'Query': #Rework
                self.evaluation_id.with_context(is_approval=True).rework_submission(self.comment)
            elif self.option3 == 'Reject': 
                self.evaluation_id.reject(self.comment)
            else:
                self.evaluation_id.approve()

        return {'type': 'ir.actions.act_window_close'}


    # @api.model
    # def default_get(self, fields):
    #     res = super(InsetaWspAtrValidateWizard, self).default_get(fields)
    #     active_ids = self.env.context.get('active_ids', [])

    #     res.update({
    #         'wspatr_id': active_ids[0] if active_ids else False,
    #     })
    #     return res

    # def wspatr_validate(self):
    #     self.ensure_one()
    #     if self.stage == "validation":
    #         if self.option == 'Query': #Rework
    #             self.wspatr_id.rework_submission(self.comment)
    #         if self.option == 'Recommend':
    #             self.wspatr_id.recommend_submission(self.comment, status="Recommended")
    #         if self.option == 'Not Recommend':
    #             self.wspatr_id.recommend_submission(self.comment, status="Not Recommended")
    #     elif self.stage == "assessment":
    #         if self.option == 'Query': #Rework
    #             self.wspatr_id.with_context(is_assessment=True).rework_submission(self.comment)
    #         if self.option == 'Recommend':
    #             self.wspatr_id.with_context(is_assessment=True).recommend_submission(self.comment, status="Recommended")
    #         if self.option == 'Not Recommend':
    #             self.wspatr_id.with_context(is_assessment=True).recommend_submission(self.comment, status="Not Recommended")
    #     else: #evaluation stage
    #         if self.option2 == 'Query': #Rework
    #             self.wspatr_id.with_context(is_evaluation=True).rework_submission(self.comment)
    #         elif self.option2 == 'Reject': 
    #             self.wspatr_id.reject_submission(self.comment)
    #         elif self.option2 == 'Approve':
    #             self.wspatr_id.approve_submission(self.comment)

    #     return {'type': 'ir.actions.act_window_close'}