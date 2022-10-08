# -*- coding: utf-8 -*-

from odoo import api, fields, models

class InsetaLearnersWizard(models.TransientModel):
    """This wizard can be used for rework or rejection
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.learner.reason.wizard"
    _description = "learners Registration Rework Reason Wizard"

    comment_type = fields.Selection([('Rework', 'Rework'),('Reject', 'Reject')])
    comment = fields.Text(string='Comment')
    learner_register_id = fields.Many2one('inseta.learner.register')

    @api.model
    def default_get(self, fields):
        res = super(InsetaLearnersWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'learner_register_id': active_ids[0] if active_ids else False,
        })
        return res

    def learner_register_refuse_reason(self):
        self.ensure_one()
        if self.comment_type == 'Rework':
            self.learner_register_id.rework_registration(self.comment)
        if self.comment_type == 'Reject':
            self.learner_register_id.reject_registration(self.comment)

        return {'type': 'ir.actions.act_window_close'}