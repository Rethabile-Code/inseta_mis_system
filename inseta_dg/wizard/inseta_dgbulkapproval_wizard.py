# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaBulkDgApproveWizard(models.TransientModel):
    """This wizard can be used for approval , rejection, query for DG 
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.dgbulkapproval.wizard"
    _description = "DG Bulk Approval Wizard"

    @api.model
    def default_get(self, fields):
        res = super(InsetaBulkDgApproveWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        dg = self.env['inseta.dgapproval'].search([('id','in', active_ids)],limit=1)

        res.update({
            'dgapproval_id': active_ids[0] if active_ids else False,
        })
        return res

    dgapproval_id = fields.Many2one('inseta.dgapproval')
    stage = fields.Char(default="recommend")
    option = fields.Selection([
        ('Approve', 'Approve'),
    ])
    comment = fields.Text(string='Comment')

    #TODO: nov 11, 2021 Delete fields below. No longer needed bcos of bulk approval workflow
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    no_learners = fields.Integer(
        'Total No. Learners Applied for', 
        #compute="_compute_no_learners",
        store=True,
        help="Grand Total no of learners"
    )

    no_learners_recommended = fields.Integer(
        'Total No. Recommended',
        #compute="_compute_no_learners_recommended",
        store=True,
    )

    amount_total_recommended =fields.Monetary(
        'Total Amt Recommended', 
        #compute="_compute_total_amount_recommended",
        store=True,
        help="Grand Total Amount"
    )

    @api.depends("dgapproval_id.dgapplication_ids")
    def _compute_no_learners(self):
        for rec in self:
            rec.no_learners = sum(self.dgapproval_id.dgapplication_ids.mapped('no_learners'))

    @api.depends("dgapproval_id.dgapplication_ids.no_learners_recommended")
    def _compute_no_learners_recommended(self):
        for rec in self:
            rec.no_learners_recommended = sum(self.dgapproval_id.dgapplication_ids.mapped('no_learners_recommended'))

    @api.depends("dgapproval_id.dgapplication_ids.amount_total_recommended")
    def _compute_total_amount_recommended(self):
        for rec in self:
            rec.amount_total_recommended = sum(self.dgapproval_id.dgapplication_ids.mapped('amount_total_recommended'))
    

    def bulk_approve(self):
        self.ensure_one()
        if self.option == 'Query': #Rework
            self.dgapproval_id.rework_application(self.comment)
        if self.option == 'Approve':
            self.dgapproval_id.approve_application(self.comment)
        if self.option == 'Reject':
            self.dgapproval_id.reject_application(self.comment)

        return {'type': 'ir.actions.act_window_close'}


