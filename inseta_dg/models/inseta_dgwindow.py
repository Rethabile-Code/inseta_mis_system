# -*- coding: utf-8 -*-
import logging

from odoo.addons.inseta_tools import date_tools

from odoo.tools import date_utils
from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InsetaDgFundingWindow(models.Model):
    _name = 'inseta.dgfunding.window' #=>dbo.dgfundingwindow.csv
    _description = "DG Funding window"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order= "create_date desc"

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaDgFundingWindow, self).default_get(fields_list)
        #2021-08-01 yyyy-mm-dd
        financial_yr = self.env['res.financial.year']._get_current_financial_year()
        year = fields.Date.today().year
        str_start_date = f"{year}-01-01"
        str_end_date = f"{year}-04-30" #According to spec, WSP period ends every 30th April
        res.update({
            'financial_year_id': financial_yr and financial_yr.id or False,
            'start_date': str_start_date,
            'end_date': str_end_date,
        })
        return res

    state = fields.Selection([ 
            ('draft','Draft'),
            ('submit','Submitted'),
            ('rework','Rework'),
            ('approve','Approved'),
            ('reject','Rejected')
        ],
        default="draft"
    )
    name = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year')
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    proof_of_advert = fields.Binary(string="Proof of advert")
    comment = fields.Text()
    active = fields.Boolean(default=True)
    dgtype_id = fields.Many2one('res.dgtype', 'DG type')
    legacy_system_id = fields.Integer()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    @api.constrains("start_date", "end_date", "company_id")
    def _check_dates(self):
        """Check intersection with existing wsp years."""
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.start_date
            date_to = fy.end_date
            if date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting date.")
                )

            #in legacy system, dgtype is required in dg window. lets bypass this constraint for legacy system dgwindow import
            if not self.dgtype_id: 
                domain = fy._get_overlapping_domain()
                overlapping_fy = self.search(domain, limit=1)
                if overlapping_fy:
                    raise ValidationError(
                        _(
                            "This DG Funding window '{fy}' "
                            "overlaps with '{overlapping_fy}'.\n"
                            "Please correct the start and/or end dates "
                            "of the DG Funding Window."
                        ).format(
                            fy=fy.display_name,
                            overlapping_fy=overlapping_fy.display_name,
                        )
                    )

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.dgwindow.code')
        if 'name' in vals and vals.get('name'):
            vals['name'] = vals.get("name")
        else:
            vals['name'] = sequence or '/'
        return super(InsetaDgFundingWindow, self).create(vals)

    
    def write(self, vals):
        for rec in self:
            if not vals.get('legacy_system_id'): #a bypass for importing legacy system dg funding window
                if not self._context.get('allow_write') and rec.state in ('approve',):
                    raise ValidationError(_('You cannot modify approved DG funding window'))
        return super(InsetaDgFundingWindow, self).write(vals)
    
    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You can not delete an approved or rejected'))
        return super(InsetaDgFundingWindow, self).unlink()

    
    def _get_overlapping_domain(self):
        """Get domain for finding fiscal years overlapping with self.

        The domain will search only among fiscal years of this company.
        """
        self.ensure_one()
        # Compare with other fiscal years defined for this company
        company_domain = [
            ("id", "!=", self.id),
            ("company_id", "=", self.company_id.id),
        ]

        start_date = self.start_date
        end_date = self.end_date

        intersection_domain_from = [
            "&",
            ("start_date", "<=", start_date),
            ("end_date", ">=", end_date),
        ]
        # This fiscal year's `to` is contained in another fiscal year
        # other.from <= fy.to <= other.to
        intersection_domain_to = [
            "&",
            ("start_date", "<=", start_date),
            ("end_date", ">=", end_date),
        ]
        # This fiscal year completely contains another fiscal year
        # fy.from <= other.from (or other.to) <= fy.to
        intersection_domain_contain = [
            "&",
            ("start_date", ">=", start_date),
            ("end_date", "<=", end_date),
        ]
        intersection_domain = expression.OR(
            [
                intersection_domain_from,
                intersection_domain_to,
                intersection_domain_contain,
            ]
        )

        return expression.AND(
            [
                company_domain,
                intersection_domain,
            ]
        )

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
                    model='inseta.dgfunding.window', res_id=rec.id,
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
            name = f"{rec.name} {rec.start_date.strftime('%B %d, %Y')} - {rec.end_date.strftime('%B %d, %Y')}"
            arr.append((rec.id, name))
        return arr