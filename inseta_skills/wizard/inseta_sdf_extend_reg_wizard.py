# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class InsetaSdfExtendRegWizard(models.TransientModel):
    """This wizard can be used for rework or rejection
    'action' must be passed in the context to differentiate
    the right action to perform.
    """

    _name = "inseta.sdf.extend.reg.wizard" #sdf_extend_reg_wizard
    _description = "SDF Extend Registration Wizard"

    @api.model
    def default_get(self, fields):
        res = super(InsetaSdfExtendRegWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        active_id =  active_ids[0] if active_ids else False
        sdf_org = self.env['inseta.sdf.organisation'].browse([active_id])

        res.update({
            'sdforg_id': active_id,
            'start_date': sdf_org and sdf_org.registration_start_date or False,
            'current_end_date': sdf_org and sdf_org.registration_end_date or False,
        })
        return res

    start_date = fields.Datetime()
    end_date = fields.Datetime()
    current_end_date  = fields.Datetime(
        help="Technical field used to save current end. " 
        "We will use it for validation"
    )
    sdforg_id = fields.Many2one('inseta.sdf.organisation')

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.current_end_date:
            end_date = self.end_date
            if end_date and end_date < self.current_end_date:
                self.end_date = False
                return {
                    'warning': {
                        'title': "Validation Error",
                        'message': _(
                            "Registration end date '{end_date}' cannot be less than the current end date '{curr_end_date}'"
                        ).format(
                            end_date=end_date,
                            curr_end_date=self.current_end_date
                        )
                    }
                }

    def sdf_extend_registration(self):
        self.ensure_one()
        self.sdforg_id.extend_registration(self.start_date, self.end_date)

        return {'type': 'ir.actions.act_window_close'}