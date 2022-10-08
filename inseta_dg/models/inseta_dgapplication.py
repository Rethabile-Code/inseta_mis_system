# -*- coding: utf-8 -*-
import logging

from odoo.addons.inseta_tools import date_tools

from odoo.tools import date_utils
from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

DG_STATES = [
    ('draft', 'Draft'),
    ('submit','Submitted'),
    ('rework','Pending Outstanding Information'),
    ('pending_approval', 'Pending Evaluation'),
    ('rework_eval_committee', 'Pending Outstanding Information'),
    ('pending_adjudication','Pending Adjudication'),
    ('rework_adjud_committee', 'Pending Outstanding Information'),
    ('pending_approval2', 'Pending Approval'),
    ('approve','Approved'),
    ('reject','Rejected'),
    ('recommend','Recommended'),
    ('awaiting_sign1','Awaiting Mgr Signature'),
    ('awaiting_sign2','Awaiting COO Signature'),
    ('signed','Signed')

]



class InsetaDgApplication(models.Model):
    _name = 'inseta.dgapplication'  # dbo.dgapplication.csv
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'INSETA DG application'
    _order= "create_date desc"


    @api.model
    def default_get(self, fields_list):
        """Compute list of organisations where the SDF is the primary SDF.
            According to the SPEC only primary SDFs can fill WSP/ATR forms
        """
        res = super(InsetaDgApplication, self).default_get(fields_list)
        
        financial_yr = self.env['res.financial.year']._get_current_financial_year()
        if not financial_yr:
            curr_year = fields.Date.today().year
            raise ValidationError(f"Financial Year is not yet opened for the current year {curr_year}.\n"
                "Please contact the system administrator. ")

        dgfundingwindow = self.env['inseta.dgfunding.window'].search([
            ('financial_year_id','=',financial_yr.id)
        ]) if financial_yr else False

        if not dgfundingwindow:
            raise ValidationError(f"DG Application Window is not yet opened for the current financial year '{financial_yr.name}' ")

        user = self.env.user
        sdf = self.env['inseta.sdf'].sudo().search([('partner_id','=', user.partner_id.id)], order="id desc", limit=1)


        #filter organisations where the SDF is the primary SDF
        user_allowed_organisations = user.allowed_organisation_ids
        sdf_organisations = sdf.organisation_ids.filtered(lambda r: r.sdf_role == "primary" or r.sdf_role == "secondary")

        sdf_org_ids =  [o.organisation_id.id for o in sdf_organisations]
        user_org_ids = [o.id for o in user_allowed_organisations]
        allowed_org_ids = list(set(sdf_org_ids + user_org_ids))         #use set to retrieve unique organisation ids
        #HEI
        is_hei = self._context.get('default_is_hei')
        if is_hei and not user.has_group('inseta_dg.group_hei_representative'):
            raise ValidationError("Only HEI Representatives can create HEI Application.")

        hei_rep = self.env['mis.hei.representative'].sudo().search([('user_id','=', user.id)], order="id desc", limit=1)
        if is_hei:
            dgtype_domain = ['|',('for_hei','=','yes'),('for_hei','=','both')]
            allowed_org_ids = hei_rep and [hei_rep.organisation_id.id] or []
        else: 
           dgtype_domain = ['|',('for_hei','=','no'),('for_hei','=','both')]
        allowed_dgtypes = self.env['res.dgtype'].search(dgtype_domain)
        
        res.update({
            'sdf_id': sdf and sdf.id or False,
            'hei_rep_id': hei_rep and hei_rep.id or False,
            'sdf_allowed_organisation_ids':allowed_org_ids,
            'allowed_dgtype_ids': allowed_dgtypes,
            'financial_year_id': financial_yr and financial_yr.id or False,
        })
        return res

    name = fields.Char(index=True)
    active =  fields.Boolean(default=True)
    state = fields.Selection(DG_STATES, 
        default='draft', 
        index=True, 
        tracking=True,
        store=True
    )

    organisation_id = fields.Many2one(
        'inseta.organisation', 
        domain="[('state','=','approve')]", 
        required=True, 
        tracking=True
    )
    sdl_no = fields.Char('SDL No', related="organisation_id.sdl_no")

    sic_code_id = fields.Many2one(
        'res.sic.code', 
        'SIC Code',
        compute="_compute_sic_code_desc",
        store=True
    )
    sic_code_desc = fields.Char(
        'SIC Code Description', 
        compute="_compute_sic_code_desc",
        store=True
    )
    sdf_id = fields.Many2one("inseta.sdf")
    hei_rep_id = fields.Many2one("mis.hei.representative")
    is_hei = fields.Boolean(help="Indicates if an application is for HEI")

    sdf_allowed_organisation_ids = fields.Many2many(
        'inseta.organisation', 
        'inseta_dgapplication_organisation_rel', 
        'dgapplication_id', 
        'organisation_id', 
        string="Primary SDF Organisations",
        help="Technical List of Primary/secondary SDF Organisation" 
            "used as domain in the organisation_id field"
    )
    allowed_dgtype_ids = fields.Many2many(
        'res.dgtype', 
        'inseta_dgapplication_dgtype_rel', 
        'dgapplication_id', 
        'dgtype_id', 
        string="Allowed Dgtyps",
        help="Technical List of allowed dgtypes for HEI or 'normal' dg application"
    )
    financial_year_id = fields.Many2one('res.financial.year', required=True,tracking=True)
    # programmetype_id = fields.Many2one('inseta.programme.type', 'Programme type')
    dgtype_id = fields.Many2one('res.dgtype', 'DG type', tracking=True)
    dgtype_code = fields.Char(compute="_compute_dgtype_code", store=True)
    is_learnership = fields.Boolean(compute="_compute_is_learnership")

    dgfundingwindow_id = fields.Many2one(
        'inseta.dgfunding.window', 
        'Funding Window',
        domain="[('state','=','approve'),('financial_year_id','=',financial_year_id)]",
    )
    due_date = fields.Datetime()

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    no_learners = fields.Integer(
        'Tot. Learners Applied',
        compute="_compute_total_learners"
    )
    disabled = fields.Integer(
        'Tot. Disabled Applied',
        compute="_compute_total_learners"
    )
    total_learners = fields.Integer(
        compute="_compute_total_learners", 
        store=True, 
        string="Tot. Applied"
    )

    amount_learners_applied =fields.Monetary(
        'Total Amt. Learners Applied', 
        compute="_compute_amount_total_applied",
        store=True,
        help="Amount in user currency"
    )
    amount_disabled_applied =fields.Monetary(
        'Total Amt. Disabled Applied', 
        compute="_compute_amount_total_applied",
        store=True,
        help="Amount in user currency"
    )

    amount_total_applied =fields.Monetary(
        'Total Amt. Applied', 
        compute="_compute_amount_total_applied",
        store=True,
        help="Amount in user currency"
    )

    no_learners_approved = fields.Integer(
        'Tot. Learners Approved',
        compute="_compute_total_learners_approved"
    )
    disabled_approved = fields.Integer(
        'Tot. Disabled Approved',
        compute="_compute_total_learners_approved"
    )
    total_learners_approved = fields.Integer(
        'Total Learners Approved',
        compute="_compute_total_learners_approved"
    )

    amount_learners_approved =fields.Monetary(
        'Tot. Amt. Learners Approved',
        compute="_compute_amount_total_approved"
    )
    amount_disabled_approved =fields.Monetary(
        'Tot. Amt. Disabled Approved',
        compute="_compute_amount_total_approved"
    )
    amount_total_approved =fields.Monetary(
        'Total Amt. Approved',
        compute="_compute_amount_total_approved"
    )

    submitted_date = fields.Datetime()
    submitted_by = fields.Many2one('res.users')
    rework_comment = fields.Text()
    rework_by = fields.Many2one('res.users')
    rework_date = fields.Date('Rework Date', help="Date PMO Admin Requested the Rework")
    rework_expiration_date = fields.Date(
        'Rework Expiration Date', 
        compute="_compute_rework_expiration", 
        store=True
    )
    approved_date = fields.Datetime()
    approved_by = fields.Many2one('res.users')
    rejected_date = fields.Datetime()
    rejected_by = fields.Many2one('res.users')

    #recommendation workflow fields
    # is_awaiting_mgr_signature = fields.Boolean("Is awaiting Mgr. Signature?")
    # is_awaiting_coo_signature = fields.Boolean("Is awaiting COO Signature?",)
    # is_signed = fields.Boolean(help="Indicates that an application has been signed by manager and COO")
    # signed_mgr_date = fields.Datetime()
    # signed_by_mgr = fields.Many2one('res.users')
    # signed_coo_date = fields.Datetime()
    # signed_by_coo = fields.Many2one('res.users')
    #DGEC / DGAC
    dgrecommend_id = fields.Many2one('inseta.dgrecommendation', string='DG Bulk Recommendation')
    dgec_recommendation = fields.Selection([
            ('Recommended','Recommended'),
            ('Not Recommended','Not Recommended'),
        ],
    )
    dgac_recommendation = fields.Selection([
            ('Recommended','Recommended'),
            ('Not Recommended','Not Recommended'),
        ],
    )
    is_dgec_recommended = fields.Boolean(
        'Is DGEC Recommended?',
        default=True, 
        help="Used during DGEC recommendation to Indicate " 
        "if DGEC wants to recommend or Not"
    )
    is_dgac_recommended = fields.Boolean(
        'Is DGAC Recommended?',
        default=True, 
        help="Used during DGAC recommendation to Indicate " 
        "if DGAC wants to recommend or Not"
    )
    dgac_comment = fields.Text()
    dgec_comment = fields.Text()

    #CEO Approval and PMO admin recommendation
    is_ceo_approved = fields.Boolean(
        'Do you want to Approve?',
        default=True, 
        help="Used during Bulk approval to Indicate " 
        "if CEO wants to approve a DG or not"
    )
    decline_comment = fields.Text()
    dgapproval_id = fields.Many2one('inseta.dgapproval', string='DG Bulk approval')

    applicationdetails_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Application Details',
        domain="[('dgtype_id','=',dgtype_id)]"
    )

    learnershipdetails_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Learnership Details',
        domain="[('dgtype_id','=',dgtype_id)]"
    )

    internshipdetails_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Internship Details',
        domain="[('dgtype_id','=',dgtype_id)]"
    )
    burlearnerdetails_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Bursary Details',
        domain=[('dgtype_code','=','BUR')]
    )
    burlearnerdetails_youth_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Bursary Details',
        domain=[('dgtype_code','=','BUR-Y')]
    )
    splearnerdetails_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Skills Programme Details',
        domain=[('dgtype_code','=','SP')]
    )
    splearnerdetails_hei_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Skills Programme Details',
        domain=[('dgtype_code','=','SP-Y')]
    )
    willearnerdetails_ids = fields.One2many(
        'inseta.dgapplicationdetails',
        'dgapplication_id', 
        'Work Integrated Learning',
        domain=[('dgtype_code','=','WIL')]
    )
    evaluation_count = fields.Integer(compute="_compute_evaluation_count")
    #evaluation, recommendation and approval fields
    upload_ids = fields.One2many(
        'inseta.dgdocumentuploads', 
        'dgapplication_id', 
        'Document Uploads'
    )
    contact_ids = fields.One2many(
        'inseta.dgorganisationcontacts', 
        'dgapplication_id', 
        'OrganisationContacts'
    )
    evaluation_ids = fields.One2many(
        'inseta.dgevaluation', 
        'dgapplication_id', 
        'DG Evaluation'
    )
    legacy_system_id = fields.Integer()

# --------------------------------------------
# Compute methods
# --------------------------------------------

    @api.depends('dgtype_id','dgtype_code')
    def _compute_is_learnership(self):
        for rec in self:
            if rec.dgtype_code and 'LRN' in rec.dgtype_code:
                rec.is_learnership = True
            else:
                rec.is_learnership = False

    def _compute_evaluation_count(self):
        for rec in self:
            rec.evaluation_count = self.env['inseta.dgevaluation'] \
                .sudo() \
                .search_count([('dgapplication_id','=',rec.id)])
        return True


    @api.depends('organisation_id')
    def _compute_sic_code_desc(self):
        for rec in self:
            if rec.organisation_id and rec.organisation_id.sic_code_id:
                rec.sic_code_id = rec.organisation_id.sic_code_id.id
                rec.sic_code_desc = rec.organisation_id.sic_code_id.name
            else:
                rec.sic_code_desc =  False
                rec.sic_code_id = False


    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            rec.rework_expiration_date = False
            if rec.rework_date:
                rec.rework_expiration_date = date_utils.add(rec.rework_date, days=10)
    

    def _get_applicationdetails_o2m_field(self):
        if self.dgtype_code:
            if 'LRN' in self.dgtype_code:
                return self.learnershipdetails_ids
            elif self.dgtype_code in ('INT','IT-DEGREE','IT-MATRIC'):
                return self.internshipdetails_ids
            elif self.dgtype_code in ('SP',):
                return self.splearnerdetails_ids
            elif self.dgtype_code in ('SP-Y',):
                return self.splearnerdetails_hei_ids
            elif self.dgtype_code in ('WIL',):
                return self.willearnerdetails_ids
            elif self.dgtype_code in ('BUR',):
                return self.burlearnerdetails_ids
            elif self.dgtype_code == 'BUR-Y':
                return self.burlearnerdetails_youth_ids
            else: #TVET
                return False

    @api.depends(
        'learnershipdetails_ids.amount_total_approved',
        'internshipdetails_ids.amount_total_approved',
        'burlearnerdetails_ids.amount_total_approved',
        'splearnerdetails_ids.amount_total_approved',
        'splearnerdetails_hei_ids.amount_total_approved',
        'willearnerdetails_ids.amount_total_approved',
        'burlearnerdetails_youth_ids.amount_total_approved'
    )
    def _compute_amount_total_approved(self):
        for rec in self:
            applicationdetails = rec._get_applicationdetails_o2m_field()
            if applicationdetails:
                rec.amount_total_approved = sum(applicationdetails.mapped('amount_total_approved'))
                rec.amount_disabled_approved = sum(applicationdetails.mapped('amount_disabled_approved'))
                rec.amount_learners_approved = sum(applicationdetails.mapped('amount_learners_approved'))
            else:
                rec.amount_total_approved = 0.00
                rec.amount_disabled_approved = 0.00
                rec.amount_learners_approved = 0.00


    @api.depends(
        'learnershipdetails_ids.total_learners',
        'internshipdetails_ids.total_learners',
        'burlearnerdetails_ids.total_learners',
        'splearnerdetails_ids.total_learners',
        'splearnerdetails_hei_ids.total_learners',
        'willearnerdetails_ids.total_learners',
        'burlearnerdetails_youth_ids.total_learners',
        'learnershipdetails_ids.no_learners_approved',
        'internshipdetails_ids.no_learners_approved',
        'burlearnerdetails_ids.no_learners_approved',
        'splearnerdetails_ids.no_learners_approved',
        'splearnerdetails_hei_ids.no_learners_approved',
        'willearnerdetails_ids.no_learners_approved',
        'burlearnerdetails_youth_ids.no_learners_approved',
        'learnershipdetails_ids.disabled_approved',
        'internshipdetails_ids.disabled_approved',
        'burlearnerdetails_ids.disabled_approved',
        'splearnerdetails_ids.disabled_approved',
        'splearnerdetails_hei_ids.disabled_approved',
        'willearnerdetails_ids.disabled_approved',
    )
    def _compute_total_learners_approved(self):
        for rec in self:
            applicationdetails = rec._get_applicationdetails_o2m_field()
            if applicationdetails:
                rec.disabled_approved = sum(applicationdetails.mapped('disabled_approved'))
                rec.no_learners_approved = sum(applicationdetails.mapped('no_learners_approved'))
                rec.total_learners_approved = sum(applicationdetails.mapped('total_learners_approved'))
            else:
                rec.disabled_approved = 0
                rec.no_learners_approved = 0
                rec.total_learners_approved = 0


    @api.depends(
        'learnershipdetails_ids.total_learners',
        'internshipdetails_ids.total_learners',
        'burlearnerdetails_ids.total_learners',
        'splearnerdetails_ids.total_learners',
        'splearnerdetails_hei_ids.total_learners',
        'willearnerdetails_ids.total_learners',
        'burlearnerdetails_youth_ids.total_learners'
    )
    def _compute_total_learners(self):
        for rec in self:
            applicationdetails = rec._get_applicationdetails_o2m_field()
            if applicationdetails:
                rec.total_learners = sum(applicationdetails.mapped('total_learners'))
                rec.disabled = sum(applicationdetails.mapped('disabled'))
                rec.no_learners = sum(applicationdetails.mapped('no_learners'))
            else:
                rec.total_learners = 0
                rec.disabled = 0
                rec.no_learners = 0

    @api.depends(
        'learnershipdetails_ids.amount_applied',
        'internshipdetails_ids.amount_applied',
        'burlearnerdetails_ids.amount_applied',
        'splearnerdetails_ids.amount_applied',
        'splearnerdetails_hei_ids.amount_applied',
        'willearnerdetails_ids.amount_applied',
        'burlearnerdetails_youth_ids.amount_applied',
        'learnershipdetails_ids.amount_learners_applied',
        'internshipdetails_ids.amount_learners_applied',
        'burlearnerdetails_ids.amount_learners_applied',
        'splearnerdetails_ids.amount_learners_applied',
        'splearnerdetails_hei_ids.amount_learners_applied',
        'willearnerdetails_ids.amount_learners_applied',
        'burlearnerdetails_youth_ids.amount_learners_applied',
        'learnershipdetails_ids.amount_disabled_applied',
        'internshipdetails_ids.amount_disabled_applied',
        'burlearnerdetails_ids.amount_disabled_applied',
        'splearnerdetails_ids.amount_disabled_applied',
        'splearnerdetails_hei_ids.amount_disabled_applied'
    )
    def _compute_amount_total_applied(self):
        for rec in self:
            applicationdetails = rec._get_applicationdetails_o2m_field()
            if applicationdetails:
                rec.amount_total_applied = sum(applicationdetails.mapped('amount_applied'))
                rec.amount_learners_applied = sum(applicationdetails.mapped('amount_learners_applied'))
                rec.amount_disabled_applied = sum(applicationdetails.mapped('amount_disabled_applied'))
            else:
                rec.amount_total_applied = 0
                rec.amount_learners_applied = 0
                rec.amount_disabled_applied = 0


    @api.depends('dgtype_id')
    def _compute_dgtype_code(self):
        for rec in self:
            _logger.info(f"saqacode {rec.dgtype_id.saqacode}")
            if rec.dgtype_id:
                rec.dgtype_code = rec.dgtype_id.saqacode
            else:
                rec.dgtype_code = False

# --------------------------------------------
# Onchange and API Constraints
# --------------------------------------------

    @api.onchange('dgfundingwindow_id')
    def _onchange_dgfundingwindow_id(self):
        if self.dgfundingwindow_id: 
            dgwindow = self.dgfundingwindow_id
            if self.dgfundingwindow_id.state != 'approve':
                self.dgfundingwindow_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"DG Funding Window '{dgwindow.name}' is not yet approved, please contact the System Administrator."
                    }
                }

            if fields.Datetime.now() > self.dgfundingwindow_id.end_date:
                self.dgfundingwindow_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"DG Funding Window '{dgwindow.name}' is closed, please contact the System Administrator."
                    }
                }
            self.due_date = self.dgfundingwindow_id.end_date


# --------------------------------------------
# ORM Methods Override
# --------------------------------------------
    @api.model
    def create(self, vals):
        res = super(InsetaDgApplication, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('inseta.application.code') or '/'
        if 'name' in vals and vals.get('name'):
            sequence = vals.get("name")
        else:
            fy = self.env['res.financial.year'].search([('id','=',vals.get('financial_year_id'))])
            fy_start = fy.date_from.year if fy else False
            fy_end = fy.date_to.year if fy else False
            dgperiod = f"{fy_start}-{fy_end}"
            dgtype = self.env['res.dgtype'].search([('id','=',vals.get('dgtype_id'))])
            dgtype_code = dgtype and dgtype.saqacode or False
            sequence1 = seq.replace('dgtype',str(dgtype_code))
            sequence = sequence1.replace('dgperiod',str(dgperiod))

        res.write({'name': sequence})
        return res

    # def write(self, vals):
    #     if not self._context.get('allow_write') and self.state not in ('draft',):
    #         raise ValidationError(_('You cannot modify a submitted DG Application'))
    #     return super(InsetaDgApplication, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft',):
                raise ValidationError(_('You cannot delete a submitted DG Application'))
        return super(InsetaDgApplication, self).unlink()

    def copy(self):
        res = super(InsetaDgApplication, self).copy()

        ''' Inherited to avoid duplicating records '''
        raise Warning(
            _('Forbidden! You are not allowed to duplicate DG Application, please create the new one.!'))


# --------------------------------------------
# Business Logic
# --------------------------------------------
    def action_set_to_draft(self):
        # self._reset_recommendation_workflow_fields()
        self.with_context(allow_write=True).write({"state":"draft"})
        
        
    def action_send_to_programme_mgr(self):
        """ Send recommendation/decline letter to the Programme/Intervention Manager for signature
        """
        self.with_context(allow_write=True).write({'state':'awaiting_sign1'})
        self.activity_update()


    def action_send_to_coo(self):
        """ Send recommendation/decline letter to the COO for signature
        """
        self.with_context(allow_write=True).write({'state':'awaiting_sign2'})
        self.activity_update()


    def action_submit(self):
        _logger.info('Submitting DG application...')

        if self.is_hei:
            if not self.hei_rep_id:
                raise ValidationError(_('Only HEI Representatives are allowed to submit application for HEIs'))
            if self.hei_rep_id.state != 'approve':
                raise ValidationError(_('The HEI Representative registration is not yet approved. Please contact support.'))
   
        if self.dgtype_code in ('LRN-Y','LRN-W','LRN-D','LRN-R') and not self.learnershipdetails_ids:
            raise ValidationError(_("Please Provide Learnerhsip details before submission"))

        if self.dgtype_code in ('IT-MATRIC','IT-DEGREE') and not self.internshipdetails_ids:
            raise ValidationError(_("Please Provide Internship Programme details before submission"))

        if self.dgtype_code in ('SP',) and not self.splearnerdetails_ids:
                raise ValidationError(_("Please Provide Skills Programme details before submission"))

        if self.dgtype_code in ('SP-Y',) and not self.splearnerdetails_hei_ids:
                raise ValidationError(_("Please Provide Skills Programme Youth details before submission"))


        if self.dgtype_code in ('WIL',) and not self.willearnerdetails_ids:
                raise ValidationError(_("Please Provide Work Integrated Learning details before submission"))

        if self.dgtype_code in ('BUR',) and not self.burlearnerdetails_ids:
                raise ValidationError(_("Please Provide Bursary details before submission"))

        if self.dgtype_code in ('BUR-Y',) and not self.burlearnerdetails_youth_ids:
                raise ValidationError(_("Please Provide Bursary details before submission"))
                
        #According to henry, the required Document uploads is done from skills during SDF registration
        #may be, we could check the documents from their
        # if not self.upload_ids:
        #     raise ValidationError(_('Please Upload the Requisite Documents before submission'))

        #Generate evalutaion lines 
        self.evaluation_ids = False
        vals = {
            'state': 'submit', 
            'submitted_date': fields.Date.today(),
            'submitted_by': self.env.user.id,
            'evaluation_ids':[(
                0,0,
                line
            ) for line in  self._prepare_evaluation_vals()],
        }
        #TODO: Do not delete existing evaluation, when submiting
        self.with_context(allow_write=True).write(vals)
        self.activity_update()


    def dgapplication_evaluate(self):
        self.ensure_one()
        if self.state == "submit":
            #Desktop Evaluation is done for each line item in a DG application
            query_list = []
            for line in self.evaluation_ids:
                if line.option == "Query":
                    query_list.append(line.comment)

            if len(query_list) > 0:
                self.rework_application(", \n".join(query_list)) 
            else:
                for line in self.evaluation_ids:
                    if line.total_recommended < 1:
                        programme = line.learnership_id.name or line.programme_name or  line.fullqualification_title or line.skillsprogramme_id.name
                        raise ValidationError(_(
                            'Please recommend No of learners/Disabled for programme "{prg}"'
                        ).format(
                             prg= programme   
                        ))
                    line.state = "pending_approval"
                self.verify_application()
        

    def verify_application(self):
        """Desktop Evaluator evaluates the application.
        When the application is verified change the state
        to " Pending Approval".
        This method is called from the dgapplication evaluate wizard

        Args:
            comment (str): comment
        """

        #Check if organisation has submitted a WSP/ATR for current window
        #According to henry this check is to be done when pmo admin want to recommend
        wsp = self.env['inseta.wspatr'].search([
            ('financial_year_id','=',self.financial_year_id.id),
            ('organisation_id','=',self.organisation_id.id),
            ('state','=','approve'),
        ])
        # if not wsp:
        #     raise ValidationError(
        #         _(
        #             '{org} has not submitted WSP/ATR for '
        #             'the financial year {fy}!'
        #         ).format(
        #             fy=self.financial_year_id.name,
        #             org=self.organisation_id.trade_name
        #         )
        #     )

        self.write({'state': 'pending_approval', })
        self.activity_update()


    def recommend_application(self, comment, status):
        """DGEC/DGAC recommend or not recommend the application.
        When the application is verified change the state
        to " Pending Approval".
        This method is called from the dgapplication evaluate wizard

        Args:
            comment (str): comment
        """
        if self._context.get('is_adjudication'):
            self.write({'state': 'pending_approval2', 'dgac_recommendation': status})
        else:
            self.write({'state': 'pending_adjudication', 'dgec_recommendation': status})
        self.activity_update()


    def rework_application(self, comment):
        """Pmo admin reworks submission.
        This method is called from the dgapplication evaluate wizard

        Args:
            comment (str): Reason for rework
        """

        # self._reset_recommendation_workflow_fields()

        if self.state == "pending_approval2": #rework adjudication committee by CEO
            self.write({
                'state': 'rework_adjud_committee',
            })
        elif self.state == 'pending_adjudication': #rework for eval committee by Adjud committee
            self.write({
                'state': 'rework_eval_committee',
            })
        else:
            self.write({
                'state': 'rework',
                'rework_date': fields.Date.today(),
                'rework_by': self.env.user.id,
                'rework_comment': comment
            })
        self.activity_update()
    
    def reject_application(self, comment):
        """CEO rejects DG. change status to "rejected".
        This method is called from the dgapplication approve wizard

        Args:
            comment (str): Reason for rejection
        """
        _logger.info('Rejecting dg application...')

        self.with_context(allow_write=True).write({
            'state': 'reject',
            'rejected_date': fields.Date.today(),
            'rejected_by': self.env.user.id,
        })
        self.activity_update()


    def approve_application(self, comment):
        """CEO approves DG. change status to "approved".
        This method is called from the dgapplication approve wizard

        Args:
            comment (str): Reason for approval
        """
        _logger.info('Approving DG application...')
        self.with_context(allow_write=True).write({
            'state': 'approve',
            'approved_date': fields.Date.today(),
            'approved_by': self.env.user.id,
        })
        self.activity_update()


    # def action_print_approval_letter(self):
    #     return self.env.ref('inseta_dg.action_dgapplication_recommendation_letter_report').report_action(self)

    # def action_print_rejection_letter(self):
    #     return self.env.ref('inseta_dg.action_dgapplication_decline_letter_report').report_action(self)

    # def action_print_recommendation_letter(self):
    #     return self.env.ref('inseta_dg.action_dgapplication_submission_report').with_context(landscape=True).report_action(self)

    def action_send_letter_employer(self):
        self.evaluation_ids.action_send_letter_employer()


    def action_print_letter(self):
        for rec in self.evaluation_ids:
            if rec.dgapplication_id.is_ceo_approved:
                return rec.action_print_recommendation_letter()
            else:
                return rec.action_print_rejection_letter()


    @api.model
    def _prepare_evaluation_vals(self):
        
        line_ids = []
        if 'LRN' in self.dgtype_code:
            applicationdetails = self.learnershipdetails_ids
        elif self.dgtype_code in ('IT-DEGREE','IT-MATRIC'):
            applicationdetails = self.internshipdetails_ids
        elif self.dgtype_code in ('BUR',):
            applicationdetails = self.burlearnerdetails_ids
        elif self.dgtype_code in ('BUR-Y',):
            applicationdetails = self.burlearnerdetails_youth_ids
        elif self.dgtype_code in ('SP-Y',):
            applicationdetails = self.splearnerdetails_hei_ids
        elif self.dgtype_code in ('WIL',):
            applicationdetails = self.willearnerdetails_ids
        else: #skills programme
            #dg.dgtype_code in ('SP',):
            applicationdetails = self.splearnerdetails_ids

        for dtl in applicationdetails:
            desktop_evals = dtl.evaluation_ids.sorted(key=lambda z: z.id, reverse=True)
            desktop_eval = desktop_evals and desktop_evals[0] or False

            line_ids.append({
                'dgapplication_id': self.id,
                'organisation_id': self.organisation_id.id,
                'financial_year_id': self.financial_year_id.id,
                'dgtype_id': self.dgtype_id.id,
                # 'state': self.state,
                'state': 'submit',
                'dgapplicationdetails_id': dtl.id,
                'learnership_id': dtl.learnership_id and dtl.learnership_id.id or False,
                'programme_name': dtl.programme_name or dtl.skillsprogramme_id.name,
                'fullqualification_title': dtl.fullqualification_title, 
                'qualification_ids': dtl.qualification_ids,
                'cost_per_student': dtl.cost_per_student,
                'cost_per_disabled': dtl.cost_per_disabled,
                'actual_cost_per_student': dtl.actual_cost_per_student,
                'no_learners': dtl.no_learners,
                'disabled': dtl.disabled,
                'total_learners': dtl.total_learners,
                'amount_applied': dtl.amount_applied,
                'no_learners_recommended': desktop_eval and desktop_eval.no_learners_recommended or 0,
                'disabled_recommended': desktop_eval and desktop_eval.disabled_recommended or 0,
                'total_recommended': desktop_eval and desktop_eval.total_recommended or 0, 
                'amount_total_recommended': desktop_eval and desktop_eval.amount_total_recommended or 0,
                'no_learners_approved': desktop_eval and desktop_eval.no_learners_approved or 0,
                'disabled_approved': desktop_eval and desktop_eval.disabled_approved or 0,
                'total_learners_approved': desktop_eval and desktop_eval.total_learners_approved or 0,
                'amount_disabled_approved': desktop_eval and desktop_eval.amount_disabled_approved or 0.00,
                'amount_learners_approved': desktop_eval and desktop_eval.amount_learners_approved or 0.00,
                'amount_total_approved': desktop_eval and desktop_eval.amount_total_approved or 0.00,
                'option': desktop_eval and desktop_eval.option or False,
                'comment': desktop_eval and desktop_eval.comment or False,
            })
        _logger.info(f"Selected details {line_ids}")

        return line_ids


    def action_update_organisation_details(self):
        view = self.env.ref('inseta_skills.view_organization_address_contact_form')
        view_id = view and view.id or False
        context = dict(self._context or {})

        return {
            'name':'Update Organisation details/Contact',
            'type':'ir.actions.act_window',
            'view_type':'form',
            'res_model':'inseta.organisation',
            'views':[(view_id, 'form')],
            'view_id':view_id,
            'res_id': self.organisation_id.id,
            'target':'new',
            'context':context,
        }

    # def _reset_recommendation_workflow_fields(self):
    #     """These flags are used during recommendation review by PMO admin,
    #         Reset the fields False
    #     """
    #     self.with_context(allow_write=True).write({
    #         "is_awaiting_mgr_signature": False,
    #         "is_awaiting_coo_signature": False
    #     })

    def _get_ceo(self):
        return self.env['res.users'].sudo().search([('is_ceo','=',True)]) or []


    def get_ceo_email(self):
        emails =  [str(ceo.partner_id.email) for ceo in self._get_ceo()]
        return ",".join(emails) if emails else ''

    def _get_pmo_mgr(self):
        grp_pmo_mgr = self.env.ref('inseta_dg.group_pmo_manager',raise_if_not_found=False)
        return self.env['res.groups'].sudo().browse([grp_pmo_mgr.id]).users if grp_pmo_mgr else False

    def get_pmo_mgr_email(self):
        emails =  [str(pmo_mgr.partner_id.email) for pmo_mgr in self._get_pmo_mgr()] 
        return ",".join(emails) if emails else ''

    def get_programme_mgr_email(self):
        if self.is_learnership:
            # users = self.env['res.users'].sudo().search([('is_learning_mgr','=',True)]) or []
            # emails =  [str(user.partner_id.email) for user in users]            
            return ",".join([self.dgtype_id.seta_mail_to]) if self.dgtype_id.seta_mail_to else ''

    def _get_coo(self):
        return self.env['res.users'].sudo().search([('is_coo','=',True)]) or []

    def get_coo_email(self):
        emails =  [str(coo.partner_id.email) for coo in self._get_coo()] if self._get_coo() else []
        return ",".join(emails) if emails else ''

    def get_adjudication_committee_email(self):
        grp_adjud_committee = self.env.ref('inseta_dg.group_adjudication_committee',raise_if_not_found=False)
        emails =  [str(ac.partner_id.email) for ac in self.env['res.groups'].sudo().browse([grp_adjud_committee.id]).users]
        return ",".join(emails) if emails else ''

    def get_evaluation_committee_email(self):
        grp_eval_committee = self.env.ref('inseta_dg.group_evaluation_committee',raise_if_not_found=False)
        emails =  [str(ec.partner_id.email) for ec in self.env['res.groups'].sudo().browse([grp_eval_committee.id]).users]
        _logger.info(f"DGEC Emails => {emails}")
        return ",".join(emails) if emails else ''

    def _get_pmo_admin(self):
        grp_pmo_admin = self.env.ref('inseta_dg.group_pmo_admin',raise_if_not_found=False)
        return self.env['res.groups'].sudo().browse([grp_pmo_admin.id]).users if grp_pmo_admin else False

    def get_pmo_admin_email(self):
        emails =  [str(pmo_admin.partner_id.email) for pmo_admin in self._get_pmo_admin()] 
        return ",".join(emails) if emails else ''

    def get_employer_contact_email(self):
        if self.organisation_id:
            contact_emails = [str(contact.email) for contact in self.organisation_id.child_ids] 
            employer_emails = [str(self.organisation_id.email)]

            emails = contact_emails or employer_emails
            if self.is_hei:
                emails += [self.hei_rep_id.email]
        return ",".join(emails) if emails else ''

# --------------------------------------------
# Mail Thread
# --------------------------------------------
            
    def action_letter_compose(self):
        """opens a window to compose an email,
        with template message loaded by default"""
        self.ensure_one()

        if self.is_ceo_approved:
            template = self.env.ref('inseta_dg.mail_template_notify_dgappl_approval_employer_afterreview', raise_if_not_found=False)
        else:
            template = self.env.ref('inseta_dg.mail_template_notify_dgappl_rejection_employer_afterreview', raise_if_not_found=False)

        template_id = template and template.id or False
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)

        attachment_ids = []
        for evaluation in self.evaluation_ids:
            self.env['report'].sudo().get_pdf([evaluation.id],'inseta_dg.action_dgapplication_recommendation_letter_report')
            attachment = self.env['ir.attachment'].search([('res_model', '=', 'inseta.dgevaluation'), ('res_id', '=', evaluation.id)])
            if attachment:
                attachment_ids.append(attachment.id)

        ctx = {
            'default_model': 'inseta.dgapplication',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': attachment_ids
        }
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': compose_form_id and compose_form_id.id or False,
            'target': 'new',
            'context': ctx,
        }

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(InsetaDgApplication, self)._message_auto_subscribe_followers(
            updated_values, subtype_ids)
        if updated_values.get('user_id'):
            user = self.env['res.users'].browse(
                updated_values['user_id'])
            if user:
                res.append(
                    (user.partner_id.id, subtype_ids, False))
        return res

    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            for rec in self:
                rec.message_post_with_template(
                    template.id, composition_mode='comment',
                    model='inseta.dgapplication', res_id=rec.id,
                    email_layout_xmlid='mail.mail_notification_light',
                )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template, mail_template_employer = False, False
        #Specilist request rework, state chnages to rework, notify SDF and SDF Employer
        if self.state == 'rework':
            #delete existing rework activity
            self.activity_unlink(['inseta_dg.mail_act_dgapplication_rework'])
            #schedule an activity for rework expiration for  SDF user
            self.activity_schedule(
                'inseta_dg.mail_act_dgapplication_rework',
                user_id=self.env.user.id,
                date_deadline=self.rework_expiration_date)
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_rework', raise_if_not_found=False)

        if self.state == 'submit' and not self.rework_date:
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_pmoadmin', raise_if_not_found=False)
            mail_template_employer = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer', raise_if_not_found=False)
        else:
            #notify PMO admin, after rework is submitted
            mail_template = self.env.ref('mail_template_notify_dgapplication_afterrework', raise_if_not_found=False)

        if self.state == 'pending_approval':
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_evalcomm', raise_if_not_found=False)
            mail_template_employer = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)
            
        if self.state == 'pending_adjudication':
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_adjudcomm', raise_if_not_found=False)
            mail_template_employer = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)

        if self.state == "rework_eval_committee":
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_evalcomm_rework', raise_if_not_found=False)

        if self.state == "pending_approval2":
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_ceo', raise_if_not_found=False)
            mail_template_employer = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)

        if self.state == "rework_adjud_committee":
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_adjudcomm_rework', raise_if_not_found=False)
        
        if self.state in ("approve","reject"):
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_pmoadmin_afterapproval', raise_if_not_found=False)
            mail_template_employer = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)

        if self.state =="awaiting_sign1":
            if self.is_ceo_approved:
                mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_approval_mgr_afterreview', raise_if_not_found=False)
            else:
                mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_rejection_mgr_afterreview', raise_if_not_found=False) 

        if self.state =="awaiting_sign2":
            if self.is_ceo_approved:
                mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_approval_coo_afterreview1', raise_if_not_found=False)
            else:
                mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_rejection_coo_afterreview1', raise_if_not_found=False) 

        if self.state == "signed":
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_pmoadmin_after_coo_sign', raise_if_not_found=False)

        self.filtered(lambda s: s.state in ('pending_approval')).activity_unlink(['inseta_dg.mail_act_dgapplication_rework'])

        self.with_context(allow_write=True)._message_post(mail_template) #notify sdf
        self.with_context(allow_write=True)._message_post(mail_template_employer) #notify employers


class InsetaDgOrganisationContact(models.Model):
    _name = 'inseta.dgorganisationcontacts' #dbo.dgorganisationcontacts.csv
    _description = "DG Organisation Contact"
    _order= "id desc"

    dgapplication_id = fields.Many2one('inseta.dgapplication')
    title = fields.Many2one("res.partner.title")
    first_name = fields.Char()
    last_name = fields.Char()
    id_no = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()

class InsetaDgDocumentUploads(models.Model):
    _name = 'inseta.dgdocumentuploads'
    _description = "DG Document Upload"
    _order= "id desc"
    _rec_name = "dgdocumenttype_id"

    dgapplication_id = fields.Many2one('inseta.dgapplication')
    organisation_id = fields.Many2one("inseta.organisation")
    financial_year_id = fields.Many2one('res.financial.year')
    dgdocumenttype_id = fields.Many2one("res.dgdocumenttype", "Document Type")
    file = fields.Binary(string="Select File", required=True)
    file_name = fields.Char("File Name")
    legacy_filepath = fields.Char()
    comment = fields.Text()
    active = fields.Boolean(default=True)
    status = fields.Char()
    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.onchange("organisation_id")
    def _onchange_organisation_id(self):
        self.dgapplication_id = self._context.get('default_dgapplication_id')