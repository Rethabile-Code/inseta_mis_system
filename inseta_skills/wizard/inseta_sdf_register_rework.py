# -*- coding: utf-8 -*-

from odoo import api, fields, models

class InsetaSdWizard(models.TransientModel):
    #TODO: Delete
    _name = "inseta.sdf.wizard"

class InsetaSdfRegisterReworkWizard(models.TransientModel):
    """This wizard can be used for rework or rejection
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.sdf.register.rework.wizard"
    _description = "SDF Registration Rework Reason Wizard"

    comment_type = fields.Selection([('Rework', 'Rework'),('Reject', 'Reject')])
    comment = fields.Text(string='Comment')
    sdf_register_id = fields.Many2one('inseta.sdf.register')

    @api.model
    def default_get(self, fields):
        res = super(InsetaSdfRegisterReworkWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'sdf_register_id': active_ids[0] if active_ids else False,
        })
        return res

    def sdf_register_refuse_reason(self):
        self.ensure_one()
        if self.comment_type == 'Rework':
            self.sdf_register_id.rework_registration(self.comment)
        if self.comment_type == 'Reject':
            self.sdf_register_id.reject_registration(self.comment)

        return {'type': 'ir.actions.act_window_close'}