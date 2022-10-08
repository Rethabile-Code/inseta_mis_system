from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils


_logger = logging.getLogger(__name__)


class MisHeiRepresentative(models.Model):
    _name = "mis.hei.representative"
    _description = "HEI Representative"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"


    reference = fields.Char(string='Reference No.')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected')], 
        default='draft', 
        string="Status",
        index=True,
        tracking=True
    )

    organisation_id = fields.Many2one('inseta.organisation', 'HEI')
    title = fields.Many2one('res.partner.title', 'Representative title')
    first_name = fields.Char('Representative first name')
    last_name = fields.Char('Representative surname')
    mobile = fields.Char('Representative telephone number')
    email = fields.Char('Representative email')
    designation = fields.Char('Representative designation')

    signatory_title = fields.Many2one('res.partner.title', 'Signatory Title')
    signatory_first_name = fields.Char()
    signatory_last_name = fields.Char('Surname')
    signatory_mobile = fields.Char()
    signatory_email = fields.Char()
    signatory_designation = fields.Char()
    registration_date = fields.Date(default=fields.Date.today())
    user_id = fields.Many2one('res.users')
    password = fields.Char()
    submitted_date = fields.Date()
    submitted_by = fields.Many2one('res.users')
    approved_date = fields.Date()
    approved_by = fields.Many2one('res.users')
    rejected_date = fields.Date()
    rejected_by = fields.Many2one('res.users')
# --------------------------------------------
# ORM Methods Override
# --------------------------------------------
    @api.model
    def create(self, vals):
        res = super(MisHeiRepresentative, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('inseta.heirep.reference') or '/'
        res.write({'reference': seq})
        return res

    def name_get(self):
        arr = []
        for rec in self:
            name = f"{rec.first_name} {rec.last_name}"
            arr.append((rec.id, name))
        return arr

# --------------------------------------------
# Business logic
# --------------------------------------------

    def action_reset(self):
        pass

    def action_submit(self):
        for rec in self:
            rec.write({
                'state': 'submit',
                'submitted_by': self.env.user.id,
                'submitted_date': fields.Date.today()
            })
            rec.activity_update()

    def action_approve(self):
        for rec in self:
            rec.write({
                'state': 'approve',
                'approved_by': self.env.user.id,
                'approved_date': fields.Date.today()
            })
            rec.activity_update()

    def action_reject(self):
        for rec in self:
            rec.write({
                'state': 'reject',
                'rejected_by': self.env.user.id,
                'rejected_date': fields.Date.today()
            })
            rec.activity_update()


    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            for rec in self:
                rec.message_post_with_template(
                    template.id, composition_mode='comment',
                    model='mis.hei.representative', res_id=rec.id,
                    email_layout_xmlid='mail.mail_notification_light',
                )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template, mail_template2 = False, False

        if self.state == 'submit':
            mail_template = self.env.ref('inseta_dg.mail_template_notify_hei_rep', raise_if_not_found=False)
            mail_template2 = self.env.ref('inseta_dg.mail_template_notify_hei_rep_admin', raise_if_not_found=False)

        if self.state in ('approve','reject'):
            mail_template = self.env.ref('inseta_dg.mail_template_notify_hei_rep_approve', raise_if_not_found=False)

        self.with_context(allow_write=True)._message_post(mail_template)
        self.with_context(allow_write=True)._message_post(mail_template2) 

    def get_pmo_admin_email(self):
        grp_pmo_admin = self.env.ref('inseta_dg.group_pmo_admin',raise_if_not_found=False)
        pmo_admins =  self.env['res.groups'].sudo().browse([grp_pmo_admin.id]).users if grp_pmo_admin else False
        emails =  [str(pmo_admin.partner_id.email) for pmo_admin in pmo_admins] 
        return ",".join(emails) if emails else ''