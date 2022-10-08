
import logging

from odoo import fields, api, models, _

_logger = logging.getLogger(__name__)



class ResUsersExtension(models.Model):
    _inherit = "res.users"
    
    sdf_register_id = fields.Many2one('inseta.sdf.register', 'SDF Register')
    organisation_id = fields.Many2one('inseta.organisation', 'Organisation')
    sdf_id = fields.Many2one('inseta.sdf', 'SDF')
    is_sdf = fields.Boolean('Is SDF?', help="Indicates if a user is Facilitator")
    is_skills_mgr =fields.Boolean(string="Is Skills Mgr", 
        help="We will use this field to specifically identify skills mgr."
        "We can only have one skills Mgr at a time" 
        "Sometimes, admin or other users can assume role of skills mgr. we dont want this to affect emails sent to skills mgr"
        "or the skills mgr signature on docs.")

    wspatr_id = fields.Many2one('inseta.wspatr', 'WSP/ATR')
    allowed_organisation_ids = fields.Many2many(
        'inseta.organisation',
        'inseta_user_organisation_rel',
        'user_id',
        'organisation_id',
        string="Allowed Organisations",
        # compute="_compute_allowed_org_ids",
        store=True,
        help="Technical List of organisation allowed for users"
    )
    
    @api.depends('sdf_id','sdf_id.partner_id')
    def _compute_allowed_org_ids(self):
        for rec in self:
            rec.allowed_organisation_ids = [()]
            user_id = self.env.user.id
            sdf = self.env['inseta.sdf'].sudo().search([('user_id','=', user_id)], order="id desc", limit=1)
            if sdf:
                sdforgs = self.env['inseta.sdf.organisation'].sudo().search([('sdf_id','=', sdf.id)])
                _logger.info(
                    f"Computing allowed users partners {sdforgs}")
                org_ids = [s.organisation_id.id for s in sdforgs] if sdforgs else [()]
                rec.allowed_organisation_ids = [(6, 0, org_ids )]


    @api.depends('sdf_id','sdf_id.partner_id')
    def _inverse_allowed_org_ids(self):
        for rec in self:
            return True