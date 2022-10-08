import base64
from pkg_resources import require
from xlwt import easyxf, Workbook
import logging
from io import BytesIO
import json
import threading

from odoo.tools import date_utils
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)

WSP_ATR_FORMS_SMALL = [
    {'id':'impl_report', 'name': 'ATR 1: Implementation report'},
    {'id':'pivotal_trained','name': 'ATR 2: Pivotal trained beneficiaries'},
    {'id':'hard_to_fill','name': 'ATR 3: Hard to fill vacancies'},
    {'id':'skills_gap','name': 'ATR 4: Skills Gaps'},
    {'id':'skills_dev_consult','name': 'WSP 1: Skills Development & Consultation'},
    {'id':'curr_emp_profile','name': 'WSP 2: Current Employment Profile'},
    {'id':'high_edu_profile','name': 'WSP 3: Highest Edu. Profile'},
    {'id':'provincial_breakdown', 'name': 'WSP 4: Provincial Breakdown'},
    {'id':'pivotal_planned','name': 'WSP 5: Pivotal planned'},
    {'id':'planned_beneficiaries','name': 'WSP 6: Planned Beneficiaries of Training'},
]

WSP_ATR_FORMS_LARGE = [
    {'id':'trained_beneficiaries','name': 'ATR 1: Trained Beneficiaries Report'},
    {'id':'learning_programme','name': 'ATR 2: Learning Programmes'},
    {'id':'variance','name': 'ATR 3: Variance Report'},
    {'id':'trained_aet','name': 'ATR 4: AET Report'},
    {'id':'hard_to_fill','name': 'ATR 5A: Hard to Fill Vacancies'},
    {'id':'skills_gap','name': 'ATR 5B: Skills Gaps'},
    {'id':'pivotal_trained','name': 'ATR 6: PIVOTAL Trained Beneficiaries.'},
    {'id':'skills_dev_consult','name': 'WSP 1: Skills Development & Consultation'},
    {'id':'curr_emp_profile','name': 'WSP 2: Current Employment Profile'},
    {'id':'high_edu_profile','name': 'WSP 3: Highest Edu. Profile'},
    {'id':'provincial_breakdown','name': 'WSP 4: Provincial Breakdown'},
    {'id':'planned_aet','name': 'WSP 5: Planned AET'},
    {'id':'planned_beneficiaries','name': 'WSP 6: Planned Beneficiaries of Training'},
    {'id':'pivotal_planned','name': 'WSP 7: PIVOTAL Planned beneficiaries'},
]

class InsetaWspAtrEvaluation(models.Model):
    """This implementation is a rework of the original implementation of the WSP Evaluation.
    This class serves as a proxy to the original implementation.
    As you will find out soon, most of the methods defined in this class, will call the original methods 
    implemented in inseta.wspatr
    """
    _name = 'inseta.wspatr.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "WSP/ATR Evaluation"
    _order= "id desc"
    _rec_name = "wspatr_id"

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaWspAtrEvaluation, self).default_get(fields_list)

        wsp = self.env['inseta.wspatr'].browse([res.get("wspatr_id")])
        _logger.info(f'ORGANISATION => {wsp.organisation_id.name}')
        if wsp.organisation_id.is_childorganisation:
            raise ValidationError(
                f'{ wsp.organisation_id.legal_name} is a child organisation.\n' 
                'You cannot evaluate WSPATR submission for a child organisation.'
            )

        return res
        

    state = fields.Selection([
        ('submitted', 'Submitted'), # legacy equiv => Created  - 8
        ('Evaluated', 'Evaluated'), #legacy equiv =>  Pending 1
        ('Query', 'Query'), #legacy equiv =>  Query 5
        ('Query_Skills_Admin', 'Query'), #legacy equiv =>  Query 5
        ('Query_Skills_Specialist', 'Query'), #legacy equiv =>  Query 5
        ('Recommended_For_Approval', 'Recommend For Approval'),
        ('Recommended_For_Rejection', 'Recommend For Rejection'),
        ('Approved','Approved'), # Accepted = 6
        ('Rejected','Rejected') #Rejected = 4
    ],default="submitted")

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True, 
        ondelete='cascade'
    )

    #_compute_report_title
    atr_year = fields.Char(related="wspatr_id.atr_year")
    wsp_next_year = fields.Char(related="wspatr_id.wsp_next_year")
    wsp_year =  fields.Char(related="wspatr_id.wsp_year")

    organisation_id = fields.Many2one('inseta.organisation', related="wspatr_id.organisation_id")
    financial_year_id = fields.Many2one('res.financial.year')

    grant_id = fields.Char() #legacy system field
    authorization = fields.Char() #legacy system field

    employment_totals_comment = fields.Char("Does the number of employees on the Organization "
        "Details equal to number of employees on the Current Employment Profile, Provincial breakdown, "
        "and Highest qualification profile form? ",
        compute="_compute_employment_totals_comment",
        store=True
    )
    organisation_contacts_comment =  fields.Char("Are the organisational details and organisational "
        "contacts of all linked child companies completed and confirmed? ",
        compute="_compute_organisation_contacts_comment",
        store=True
    )
    organisation_ceo_bankdetails_comment =  fields.Char("Are the following screens completed and confirmed: "
        "Organisational Details, Organisational Contacts, Child Organisations, "
        "CFO Details, CEO Details and Employer Banking Details?",
        compute="_compute_organisation_ceo_bankdetails_comment",
        store=True
    )

    authorisation_page = fields.Selection([('Compliant','Compliant'),('Query','Query')])
    authorisation_page_link = fields.Html(compute="_compute_authorisation_page_link")
    authorisation_page_noncompliance_reason = fields.Char("Reasons for incompliant Authorization Page")
    authorisation_page_legacy = fields.Text('') #legacy field for authorization pag

    bank_confirmation = fields.Selection([('Compliant','Compliant'),('Query','Query')])
    bank_confirmation_link = fields.Html(compute="_compute_bank_confirmation_link")
    bank_confirmation_noncompliance_reason = fields.Char("Reasons for incompliant Bank Confirmation")
    bank_confirmation_legacy = fields.Text('Bank Confirmation')

    bee_certificate = fields.Selection([('Compliant','Compliant'),('Query','Query')])
    bee_certificate_link = fields.Html(compute="_compute_bee_certificate_link")
    bee_certificate_noncompliance_reason = fields.Char("Reasons for incompliant BEE Certificate")
    bee_certificate_legacy = fields.Text('BEE Certificate')

    fsp_license = fields.Selection([('Compliant','Compliant'),('Query','Query')])
    fsp_license_link = fields.Html(compute="_compute_fsp_license_link")
    fsp_license_noncompliance_reason = fields.Char("Reasons for incompliant FSP license")
    fsp_license_legacy = fields.Text('FSP License')

    evaluation_header_html = fields.Html(compute="_compute_evaluation_header")

    evaluated_date = fields.Date()
    evaluated_by = fields.Many2one('res.users')
    comment = fields.Text() #evaluation_comment in legacy system
    query_by = fields.Many2one('res.users')
    query_date = fields.Date('Rework Date', help="Date Skills Admin Requested the Rework")
    recommended_date = fields.Date()
    recommended_by = fields.Many2one('res.users')
    rejected_date = fields.Date()
    rejected_by = fields.Many2one('res.users')
    approved_date = fields.Date()
    approved_by = fields.Many2one('res.users')

    checklist_ids = fields.One2many(
        'inseta.wspatr.evaluation.checklist',
        'evaluation_id', 
        compute="_compute_checklist_ids", 
        inverse="_inverse_checklist_ids",
        store=True
    )

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'wspatr_id.organisation_id.confirm_cfo', 
        'wspatr_id.organisation_id.confirm_ceo',
        'wspatr_id.organisation_id.confirm_bank')
    def _compute_organisation_ceo_bankdetails_comment(self):
        for rec in self:
            rec.organisation_ceo_bankdetails_comment = "Yes" if rec.wspatr_id.organisation_id.confirm_cfo \
                and rec.wspatr_id.organisation_id.confirm_ceo \
                and rec.wspatr_id.organisation_id.confirm_bank else 'No'

    @api.depends(
        'wspatr_id.organisation_id.is_confirmed', 
        'wspatr_id.organisation_id.confirm_contact',
        'wspatr_id.organisation_id.child_ids')
    def _compute_organisation_contacts_comment(self):
        for rec in self:
            rec.organisation_contacts_comment = "Yes" if rec.wspatr_id.organisation_id.is_confirmed \
                and rec.wspatr_id.organisation_id.confirm_contact \
                and all([c.childorganisation_id.is_confirmed for c in rec.wspatr_id.organisation_id.linkage_ids]) else 'No'

    @api.depends(
        'wspatr_id.organisation_id.no_employees',
        'wspatr_id.provincialbreakdown_ids',
        'wspatr_id.no_employees_emp_profile',
        'wspatr_id.no_employees_highest_edu_profile')
    def _compute_employment_totals_comment(self):
        for rec in self:
            rec.employment_totals_comment = "Yes" if rec.organisation_id.no_employees  \
                == rec.wspatr_id._get_no_employees_provincial_breakdown() \
                == rec.wspatr_id.no_employees_emp_profile \
                == rec.wspatr_id.no_employees_highest_edu_profile else 'No'


    @api.depends('wspatr_id.form_type','organisation_id')
    def _compute_checklist_ids(self):
        for rec in self:
            forms = WSP_ATR_FORMS_SMALL if rec.wspatr_id.form_type == "Small" else WSP_ATR_FORMS_LARGE
            rec.checklist_ids = [(0,0, {
                "form_name": item.get('name'),
                "form_completed": self._get_form_completion_status(item.get('id')),
                "all_in_order": False,
                "comment": False
            }) for item in forms]


    @api.depends('wspatr_id','organisation_id')
    def _inverse_checklist_ids(self):
        for rec in self:
            return True

    @api.depends("wspatr_id.upload_ids")
    def _compute_fsp_license_link(self):
        for rec in self:
            doc = self.wspatr_id.upload_ids.filtered(lambda x: x.documentrelates_id.id == self.env.ref("inseta_skills.data_doctype5").id)
            if doc:
                rec.fsp_license_link = f"""<a href="{self._get_document_link(doc[0].id)}" target="_blank">{doc[0].file_name}</a>"""
            else:
                rec.fsp_license_link = """No document found"""


    @api.depends("wspatr_id.upload_ids")
    def _compute_bee_certificate_link(self):
        for rec in self:
            doc = self.wspatr_id.upload_ids.filtered(lambda x: x.documentrelates_id.id == self.env.ref("inseta_skills.data_doctype1").id)
            if doc:
                rec.bee_certificate_link = f"""<a href="{self._get_document_link(doc[0].id)}" target="_blank">{doc[0].file_name}</a>"""
            else:
                rec.bee_certificate_link = """No document found"""


    @api.depends("wspatr_id.upload_ids")
    def _compute_bank_confirmation_link(self):
        for rec in self:
            doc = self.wspatr_id.upload_ids.filtered(lambda x: x.documentrelates_id.id == self.env.ref("inseta_skills.data_doctype4").id)
            if doc:
                rec.bank_confirmation_link = f"""<a href="{self._get_document_link(doc[0].id)}" target="_blank">{doc[0].file_name}</a>"""
            else:
                rec.bank_confirmation_link = """No document found"""


    @api.depends("wspatr_id.upload_ids")
    def _compute_authorisation_page_link(self):
        for rec in self:
            authorization_page = rec.wspatr_id.upload_ids.filtered(lambda x: x.documentrelates_id.id == self.env.ref("inseta_skills.data_doctype3").id)
            if authorization_page:
                rec.authorisation_page_link = f"""<a href="{self._get_document_link(authorization_page[0].id)}" target="_blank">{authorization_page[0].file_name}</a>"""
            else:
                rec.authorisation_page_link = """No document found"""


    @api.depends('wspatr_id','organisation_id')
    def _compute_evaluation_header(self):
        for rec in self:
            prev_wps_html = """<table style="width:100%"> 
                <thead> 
                    <tr> 
                        <td> Skills Year </td> 
                        <td>  WSP/ATR Status</td> 
                    </tr> 
                </thead> 
                <tbody>
            """
            first_time_to_submit = 'No' if rec._get_organisation_previous_wsp() else 'Yes'
            for wsp in rec._get_organisation_previous_wsp():
                prev_wps_html += f"""
                    <tr> 
                        <td> {wsp.financial_year_id.name} </td>
                        <td> {wsp.state} </td>
                    </tr>
                """
            prev_wps_html += """
                        </tbody>
                    </table>
                """
            rec.evaluation_header_html = f"""
                <div class="row" >
                    <div class="col col-md-12">
                        <table class="table table-stripped table-bordered" style="width:100%">
                            <thead> 
                                <tr class="bg-primary" style="text-align:center"> 
                                    <th colspan="4"> Workplace Skills Plan {self.wspatr_id.financial_year_id.name} and Annual Training Report </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Organisation Name </td>
                                    <td>  {self.organisation_id.trade_name} </td>
                                    <td> Organisation SDL Number</td>
                                    <td>{self.organisation_id.sdl_no}</td>
                                </tr>
                                <tr>
                                    <td>Number of employees </td>
                                    <td>  {self.organisation_id.current_fy_numberof_employees} </td>
                                    <td>Levy Status</td>
                                    <td>{self.organisation_id.levy_status}</td>
                                </tr>

                                <tr>
                                    <td>Skills Year </td>
                                    <td>  {self.wspatr_id.financial_year_id.name} </td>
                                    <td> WSP ATR Status</td>
                                    <td>{self.wspatr_id.state}</td>
                                </tr>

                                <tr>
                                    <td>WSP&ATR Submission Date</td>
                                    <td>  {self.wspatr_id.submitted_date or ''} </td>
                                    <td>Submitted by</td>
                                    <td>{self.wspatr_id.submitted_by and self.wspatr_id.submitted_by.name or '' }</td>
                                </tr>

                               <tr>
                                    <td>Evaluation Status</td>
                                    <td>  {self.wspatr_id.state} </td>
                                    <td>1st time Submission to INSETA</td>
                                    <td>{first_time_to_submit}</td>
                                </tr>
                                <tr>
                                    <td>Employer Size </td>
                                    <td>  {self.organisation_id.organisation_size_id.name} </td>
                                    <td></td>
                                    <td></td>
                                </tr>

                                <tr>
                                    <td>Submission History</td>
                                    <td colspan="3">  
                                        {prev_wps_html}
                                    </td>
                                </tr>

                            </tbody>

                        </table>
                    </div>
                </div>
                <p>&nbsp; </p>
            """


    @api.onchange('wspatr_id')
    def _onchange_wspatr_id(self):
        if self.wspatr_id:
            self.financial_year_id = self.wspatr_id.financial_year_id.id


    @api.constrains("wspatr_id",)
    def _check_duplicate_evaluation(self):
        """ 
        Check if evaluation has been created for same wspatr.
        """
        for rec in self:
            # Starting date must be prior to the ending date
            domain = [('wspatr_id', '=', rec.wspatr_id.id)]
            existing_eval = self.search([('wspatr_id', '=', rec.wspatr_id.id)])
            if len(existing_eval) > 1:
                raise ValidationError(
                    _(
                        "A WSP Evaluation is already created for Organisation '{org}' "
                        "for financial year '{fy}'.\n"
                        "To continue, please go back and select the previously created WSP/ATR Evaluation"
                    ).format(
                        fy=rec.financial_year_id.display_name,
                        org=rec.organisation_id.trade_name
                    )
                )

# --------------------------------------------
# ORM Methods Override
# --------------------------------------------
    # @api.model
    # def create(self, vals):
    #     """

    #     ('pending_validation', 'Evaluated'), #legacy equiv =>  Pending 1
    #     ('rework', 'Pending Additional Information'), #legacy equiv =>  Query 5
    #     ('rework_skill_admin', 'Pending Additional Information'), #skill specs asks skill admin to rework
    #     ('rework_skill_spec', 'Pending Additional Information'), #skill mgr asks skill spec to rework
    #     ('pending_assessment', 'Evaluation In Progress'), #Evaluation In Progress 18
    #     ('pending_evaluation', 'Recommended for Approval'), #Recommended for Approval 17
    #     ('approve','Approved'), # Accepted = 6
    #     ('reject','Rejected') #Rejected = 4

    #         evaluated_date = fields.Date()
    #         evaluated_by = fields.Many2one('res.users')
    #     """
    #     if 'state' in vals:
    #         if vals.get('state') == 'pending_validation':
    #             wsp = self.env['inseta.wspatr'].search([('id','=',vals.get('wspatr_id'))])
    #             wsp.action_pending_assessment()

    #             vals.update({
    #                 "evaluated_date": fields.Date.today(),
    #                 "evaluated_by": self.env.user.id
    #             })
            
    #     return super(InsetaWspAtrEvaluation, self).create(vals)


    def write(self, vals):
        for rec in self:
            if rec.state in ('Approved','Rejected') and not self._context.get("allow_write"):
                raise ValidationError(_(' Sorry you cannot update an approved or rejected evaluation'))

        return super(InsetaWspAtrEvaluation, self).write(vals)

    def unlink(self):
        for rec in self:
            if not self._context.get("force_delete") and rec.state != 'draft':
                raise ValidationError(_('This evaluation is not in draft. Sorry you cannot delete it'))
        return super(InsetaWspAtrEvaluation, self).unlink()

# --------------------------------------------
# Business logic
# --------------------------------------------
    
    def action_reset(self):
        self.with_context({'allow_write':True}).write({"state": "submitted"})

    def _validate_checklist(self):
        #check if forms checklist have been completed
        if any([check.all_in_order == False for check in self.checklist_ids]):
            raise ValidationError(_('Please complete the form checklist'))

        for check in  self.checklist_ids:
            if check.all_in_order == 'No' and not check.comment:
                raise ValidationError(_('Description of outstanding info per form. NO is selected, provide comment'))


    def rework_submission(self, comment):
        """    This is a refactor implementation to suit NEW requirements for WSP submission.
            This functionality was originally implemented in inseta.wspatr model.
            This method is a proxy to communicate with the actual implementation in inseta.wspatr model
        """
        #check if forms checklist have been completed
        self._validate_checklist()

        #Skills specialist, reworks WSP to skill admin
        if self._context.get('is_assessment'):
            self.wspatr_id.with_context(is_assessment=True).rework_submission()
            state = "Query_Skills_Admin"
        #Skills manager, reworks WSP to skill skills spec
        elif self._context.get('is_approval'):
            self.wspatr_id.with_context(is_evaluation=True).rework_submission()
            state = "Query_Skills_Specialist"
        else:
            #Skills admin, reworks WSP to sdf
            self.wspatr_id.rework_submission()
            state = "Query"

        self.write({
            'state':state,
            "query_date": fields.Date.today(),
            "query_by": self.env.user.id,
            "comment": comment
        })


    def evaluate_submission(self):
        """Skills Admin evaluates wsp submission.

        Args:
            option (str, optional): _description_. Defaults to "Recommended".
        """

        #check if forms checklist have been completed
        self._validate_checklist()

        #check if forms are all in order

        #check document confirmation
        if not self.authorisation_page:
            raise ValidationError(_('Please confirm upload of Authorization page'))

        if not self.bank_confirmation:
            raise ValidationError(_('Please confirm upload of Bank Confirmation'))

        # if not self.bee_certificate:
        #     raise ValidationError(_('Please confirm upload of BEE Certificate'))

        if not self.fsp_license:
            raise ValidationError(_('Please confirm upload of FSP license'))
        #this is a refactor due to the confusing requirements from INSETA.
        #Implmentation might not be as clean as I would like.

        # submit wsp for the child organisations
        self.wspatr_id._submit_child_wsp(state='pending_assessment')
            
        self.write({
            'state':'Evaluated',
            "evaluated_date": fields.Date.today(),
            "evaluated_by": self.env.user.id
        })
        self.wspatr_id.recommend_submission()

    def assess_submission(self, state):
        """Skills specialists assesses wsp submission.

        Args:
            status (str, optional): _description_. Defaults to "Recommended".
        """
        #check if forms checklist have been completed
        self._validate_checklist()
            
        self.write({
            'state': state,
            "recommended_date": fields.Date.today(),
            "recommended_by": self.env.user.id
        })
        self.wspatr_id.with_context(is_assessment=True).recommend_submission()


    def approve(self):
        """Skills manager approves the evaluation.
        """
        for rec in self:
            rec.write({
                'state': 'Approved',
                "approved_date": fields.Date.today(),
                "approved_by": self.env.user.id
            })
            rec.wspatr_id.approve_submission()


    def reject(self, comment):
        """Skills mgr rejects the evaluation
        """
        for rec in self:
            rec.write({
                'state': 'Rejected',
                "rejected_date": fields.Date.today(),
                "rejected_by": self.env.user.id,
                "comment": comment

            })
            rec.wspatr_id.reject_submission()
        

    def _get_form_completion_status(self, form_id):
        if not form_id:
            return "Not Applicable"

        if not self.wspatr_id:
            raise ValidationError(_('WSPATR Submission not found'))

        wsp =  self.wspatr_id
        if form_id == "impl_report":
            return 'Yes' if wsp.confirm_impl_report else 'No'
        elif form_id == "pivotal_trained":
            return 'Yes' if wsp.confirm_pivotaltrained else 'No'
        elif form_id == "hard_to_fill":
            return 'Yes' if wsp.confirm_hardtofillvacancies else 'No'
        elif form_id == "skills_gap":
            return 'Yes' if wsp.confirm_skillsgap else 'No'
        elif form_id == "skills_dev_consult":
            return 'Yes' if wsp.confirm_skillsdevconsult else 'No'
        elif form_id == "curr_emp_profile":
            return 'Yes' if wsp.confirm_currentemploymentprofile else 'No'
        elif form_id == "high_edu_profile":
            return 'Yes' if wsp.confirm_highesteduprofile else 'No'
        elif form_id == "provincial_breakdown":
            return 'Yes' if wsp.confirm_provincialbreakdown else 'No'
        elif form_id == "pivotal_planned":
            return 'Yes' if wsp.confirm_pivotal_planned_beneficiaries else 'No'
        elif form_id == "planned_beneficiaries":
            if self.wspatr_id.form_type == "Small":
                return 'Yes' if wsp.confirm_wpskillplan else 'No'
            else:
                return 'Yes' if wsp.confirm_planned_beneficiaries else 'No'
        elif form_id == "trained_beneficiaries":
            return 'Yes' if wsp.confirm_trained_beneficiaries else 'No'
        elif form_id == "learning_programme":
            return 'Yes' if wsp.confirm_learning_programmes else 'No'
        elif form_id == "variance":
            return 'Yes' if wsp.confirm_variance else 'No'
        elif form_id == "trained_aet":
            return 'Yes' if wsp.confirm_trained_aet else 'No'
        elif form_id == "planned_aet":
            return 'Yes' if wsp.confirm_plannedaet else 'No'
        else:
            return 'No'

    def _get_organisation_previous_wsp(self):
        if self.organisation_id:
            return self.env['inseta.wspatr'].search([
                ('organisation_id','=', self.organisation_id.id),
                ('financial_year_id','!=', self.wspatr_id.financial_year_id.id)
            ], order="id desc", limit=3)
        return []


    def _get_document_link(self, doc_id):
        return '/web/content/?model=inseta.wspatr.documentupload&id={}&field=file&filename_field=file_name&download=true'.format(doc_id)
        

    def action_save(self):
        return True

class InsetaWspAtrEvaluationChecklist(models.Model):
    _name = 'inseta.wspatr.evaluation.checklist'
    _description = "WSP/ATR Evaluation Checklist"
    _order= "id desc"
    _rec_name = "wspatr_id"


    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True, 
        ondelete='cascade'
    )

    evaluation_id = fields.Many2one(
        'inseta.wspatr.evaluation',
        index=True, 
        ondelete='cascade'
    )
    form_id = fields.Integer() #legacy form id
    form_name = fields.Char(required="1")
    grant_id = fields.Char()
    form_completed = fields.Selection([
        ('No','Not Completed'),
        ('Yes','Completed'),
        ('Not Applicable','Not Applicable')
    ])
    all_in_order = fields.Selection([
        ('No','No'),
        ('Yes','Yes'),
    ])
    comment = fields.Text("Description of Outstanding info per Form")

    def action_open_wsp(self):
        """open the wsp form from the form checklist line
        """
        view_id = self.env.ref('inseta_skills.view_wsp_atr_form').id
        context = self._context.copy()
        return {
            'name':'WSP/ATR Submissions',
            'view_mode':'form',
            'views' : [(view_id,'form')],
            'res_model':'inseta.wspatr',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':self.wspatr_id.id,
            'target':'new',
            'context':context,
        }