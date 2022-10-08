# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class InsetaAssignSdlnumberWizard(models.TransientModel):
    """Assign L No to an organisation
    """

    _name = "inseta.assignsdlno.wizard"
    _description = "Assign SDL No Wizard"


    organisation_id = fields.Many2one('inseta.organisation')
    sdl_no = fields.Char(related="organisation_id.sdl_no")
    new_sdl_no = fields.Char()

    @api.onchange("new_sdl_no")
    def _onchange_new_sdl_no(self):
        if self.new_sdl_no:
            new_sdlno = self.new_sdl_no
            org = self.env['inseta.organisation'].search([('sdl_no','=',self.new_sdl_no)])
            if org:
                self.new_sdl_no = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _(
                            "Organisation with SDL no {sdlno}' already exists"
                        ).format(
                            sdlno=new_sdlno
                        )
                    }
                }


    @api.model
    def default_get(self, fields):
        res = super(InsetaAssignSdlnumberWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'organisation_id': active_ids[0] if active_ids else False,
        })
        return res

    def assign_sdlno(self):
        self.ensure_one()
        if self.new_sdl_no:

            self.organisation_id.assign_lno(self.new_sdl_no)


        return {'type': 'ir.actions.act_window_close'}