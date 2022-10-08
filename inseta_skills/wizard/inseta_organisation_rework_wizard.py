# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsetaOrganisationReworkWizard(models.TransientModel):
    """This wizard can be used for rework or rejection
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.organisation.rework.wizard"
    _description = "Organisation Rework Reason Wizard"

    comment_type = fields.Selection([('Rework', 'Rework'),('Reject', 'Reject')])
    comment = fields.Text(string='Comment')
    organisation_id = fields.Many2one('inseta.organisation')
    organisationist_id = fields.Many2one('inseta.organisation.ist')

    @api.model
    def default_get(self, fields):
        res = super(InsetaOrganisationReworkWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'organisation_id': active_ids[0] if active_ids else False,
        })
        return res

    def organisation_refuse_reason(self):
        self.ensure_one()
        if self.comment_type == 'Rework':
            if self.organisationist_id:
                self.organisationist_id.rework_registration(self.comment)
            else:
                self.organisation_id.rework_registration(self.comment)
        if self.comment_type == 'Reject':
            if self.organisationist_id:
                self.organisationist_id.reject_registration(self.comment)
            else:
                self.organisation_id.reject_registration(self.comment)

        return {'type': 'ir.actions.act_window_close'}