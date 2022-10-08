# -*- coding: utf-8 -*-
import logging

from odoo.addons.inseta_tools import date_tools

from odoo.tools import date_utils
from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class InsetaDgIndustryFundedWindow(models.Model):
    _name = 'inseta.dgindustryfunded.window' #=>dbo.dgfundingwindow.csv
    _description = "DG Industry Funded window"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order= "create_date desc"

    name = fields.Char('Name')
    opening_date = fields.Datetime(string='Opening Date')
    closing_date = fields.Datetime(string='Closing Date')
    request_letter = fields.Binary(string='Request Letter')
    employer = fields.Many2one('res.dgtype', 'Employer')
    comments = fields.Text('Name')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer()
    state = fields.Selection([ 
            ('draft','Draft'),
            ('submit','Submitted'),
            ('rework','Rework'),
            ('approve','Approved'),
            ('reject','Rejected')
        ],
        default="draft"
    )
    @api.constrains("opening_date", "closing_date")
    def _check_dates(self):
        """Check intersection with existing wsp years."""
        for fy in self:
            # Starting date must be prior to the ending date
            date_open = fy.opening_date
            date_close = fy.closing_date
            if date_close < date_open:
                raise ValidationError(
                    _("The closing date must not be prior to the opening date.")
                )

    
    def write(self, vals):
        for rec in self:
            if not vals.get('legacy_system_id'): #a bypass for importing legacy system dg funding window
                if not self._context.get('allow_write') and rec.state in ('approve',):
                    raise ValidationError(_('You cannot modify approved DG funding window'))
        return super(InsetaDgIndustryFundedWindow, self).write(vals)
    
    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You can not delete an approved or rejected'))
        return super(InsetaDgIndustryFundedWindow, self).unlink()

# --------------------------------------------
# Business Logic
# --------------------------------------------
    def action_set_to_draft(self):
        self.with_context(allow_write=True).write({'state':'draft'})

    def action_submit(self):
        self.write({'state':'submit'})
        self.activity_update()

    def action_approve(self):
        self.write({'state':'approve'})
        self.activity_update()

    def action_rework(self):
        if not self.comment:
            raise ValidationError("Please provide a comment")
        self.write({'state':'rework'})
        self.activity_update()

    def _get_ceo(self):
        return self.env['res.users'].sudo().search([('is_ceo','=',True)]) or []

    def _get_pmo_mgr(self):
        grp_pmo_mgr = self.env.ref('inseta_dg.group_pmo_manager',raise_if_not_found=False)
        return self.env['res.groups'].sudo().browse([grp_pmo_mgr.id]).users if grp_pmo_mgr else False

    def get_ceo_email(self):
        emails =  [str(ceo.partner_id.email) for ceo in self._get_ceo()]
        return ",".join(emails) if emails else ''

    def get_pmo_mgr_email(self):
        emails =  [str(pmo_mgr.partner_id.email) for pmo_mgr in self._get_pmo_mgr()] if self._get_pmo_mgr() else []
        return ",".join(emails) if emails else ''

# --------------------------------------------
# Mail Thread
# --------------------------------------------
    def _message_post(self, template):
        """Wrapper method for message_post_with_template
        Args:
            template (str): email template
        """
        if template:
            for rec in self:
                rec.message_post_with_template(
                    template.id, composition_mode='comment',
                    model='inseta.dgindustryfunded.window', res_id=rec.id,
                    email_layout_xmlid='mail.mail_notification_light',
                )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template = False 
        if self.state == 'rework':
            mail_template =  self.env.ref('inseta_dg.mail_template_notify_dgwindow_rework_pmomgr', raise_if_not_found=False)
        if self.state == 'submit':
            mail_template =  self.env.ref('inseta_dg.mail_template_notify_dgwindow_approvalrequest_ceo', raise_if_not_found=False)
        if self.state == 'approve':
            mail_template =  self.env.ref('inseta_dg.mail_template_notify_dgwindow_approved_pmomgr', raise_if_not_found=False)
            
        self.with_context(allow_write=True)._message_post(mail_template)

    def name_get(self):
        arr = []
        for rec in self:
            name = f"{rec.name} {rec.closing_date.strftime('%B %d, %Y')} - {rec.opening_date.strftime('%B %d, %Y')}"
            arr.append((rec.id, name))
        return arr