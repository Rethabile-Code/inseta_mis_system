# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaDgApplicationReviewWizard(models.TransientModel):
    """This wizard can be used for reviewing recommendation of for DG 
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.dgapplication.review.wizard"
    _description = "DG Application Review Wizard"

    @api.model
    def default_get(self, fields):
        res = super(InsetaDgApplicationReviewWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        dg = self.env['inseta.dgapplication'].search([('id','in', active_ids)],limit=1)
        comments  = []
        for ev in dg.evaluation_ids:
            if ev.comment:
                comments.append(ev.comment)

        valid_comments = '\n'.join(comments)

        res.update({
            'dgapplication_id': active_ids[0] if active_ids else False,
            'no_learners_recommended': dg.no_learners_recommended,
            'amount_total_recommended': dg.amount_total_recommended,
            'comment': valid_comments if dg.state == 'approve' else False,
            'decline_reasons': valid_comments if dg.state == 'reject' else False,
            'mandatory_documents':''.join([ doc and str(doc) or '' for doc in dg.evaluation_ids.mapped('mandatory_documents')]),
            'notice': ''.join([ notice and str(notice) or '' for notice in dg.evaluation_ids.mapped('notice')]),
        })
        return res

    
    dgapplication_id = fields.Many2one('inseta.dgapplication')
    dgtype_id = fields.Many2one('res.dgtype', related="dgapplication_id.dgtype_id")
    state = fields.Selection(related="dgapplication_id.state")
    stage = fields.Char(default="recommend")
    option = fields.Selection([
        ('Reviewed', 'Reviewed'),
    ], default="Reviewed")

    no_learners_recommended = fields.Integer('Total Number Recommended')
    no_learners = fields.Integer(
        'Total Number of Interns/Learners', 
        help="Total no of learners as captured by employer"
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    amount_total_recommended =fields.Monetary(
        'Total Amount Recommended', 
        help="Amount in user currency"
    )
    comment = fields.Text('Recommendation Comments')
    decline_reasons =  fields.Text('Decline Reasons')
    mandatory_documents = fields.Text()
    notice = fields.Text('Important Notice')


    def dgapplication_review(self):
        self.ensure_one()
        self.dgapplication_id.review_recommendation(self.comment, self.decline_reasons, self.mandatory_documents, self.notice)
        return {'type': 'ir.actions.act_window_close'}