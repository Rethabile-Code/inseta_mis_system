
import json
import logging
from operator import truediv
from requests.packages.urllib3.util.retry import Retry

from odoo.tools import date_utils

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.addons.inseta_tools.converters import  dd2dms
from ..services import  sage

_logger = logging.getLogger(__name__)


class InsetaOrganisation(models.Model):
    _name = "inseta.organisation"
    _inherits = {
        'res.partner': 'partner_id',
    }
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = "Organisation"
    _order = "create_date desc"
    #_rec_name = ''

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(InsetaOrganisation, self).default_get(fields_list)
    #     context = self._context
    #     if not context.get('default_levy_status'):
    #         raise ValidationError(_('To create a Non-Levy Organisation, use the "Non-Levy Employer" menu'))

    #     return res

    def _get_default_seta(self):
        seta_data = self.env['res.seta'].search(
            [('seta_id', '=', 13)], limit=1)
        return seta_data and seta_data.id or False


    @property
    def is_childorganisation(self):
        """
        if (self.linkstartdate and not self.linkenddate) or \
            (self.linkstartdate and self.linkenddate > fields.Date.today())  or \
            self.state == 'active':
        """
        rec = self.env['inseta.organisationlinkages'].search([
            ('childorganisation_id','=',self.id),
            ('linkstartdate','!=',False)
        ], limit=1)
        if not rec:
            return False
        return rec.linkenddate and rec.linkenddate < fields.Date.today() or  rec.state =='active'
            

    @property
    def parent_company(self):
        link = self.env['inseta.organisationlinkages'].search([
            ('childorganisation_id','=',self.id)
        ], limit=1)
        return link and link.organisation_id or False


    is_confirmed = fields.Boolean('I hereby confirm that the information submitted is complete, accurate and not misleading', tracking=True)
    confirm_contact = fields.Boolean()
    confirm_training_committee = fields.Boolean()
    confirm_cfo = fields.Boolean()
    confirm_ceo = fields.Boolean()
    confirm_bank = fields.Boolean()

    state = fields.Selection([
            ('draft', 'Draft'),
            ('submit', 'Pending Verification'),
            ('rework', 'Pending Additional Information'),
            ('rework_skill_admin', 'Pending Additional Information'), #skill manager asks specilist to rework
            ('awaiting_rejection', 'Request Rejection'), #if rework stays more than 10days, skill spec can request for rejection
            ('pending_approval','Pending Approval'),
            ('awaiting_rejection', 'Request Rejection'), #if rework stays more than 10days, skill admin can request for rejection
            ('awaiting_rejection2', 'Awaiting Rejection'),
            ('approve', 'Approved'), 
            ('reject', 'Rejected'),
        ],
        default="draft",
        index=True,
        string="Stage"
    )
    register_type = fields.Selection([
        ('non_levy', 'Non Levy Paying'),
        ('levy', 'Levy Paying'),
        ('other', 'Exempt'), ],
        string="Levy/Non Levy",
        index=True,
        default="levy"
    )
    levy_status = fields.Selection([
            ('Levy Paying','Levy Paying'),
            ('Non-Levy Paying','Non-Levy Paying')
        ],
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner', 
        'Related Partner', 
        required=True, 
        index=True, 
        ondelete='cascade'
    )
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref("base.za").id)

    sdl_no = fields.Char(index=True, readonly=True)
    # trading name is same as the name
    # name = fields.Char()
    trade_name = fields.Char()
    legal_name = fields.Char()
    registration_no_type_id = fields.Many2one(
        'res.registration_no_type', 
        string="Organisation Registration No Type",
        tracking=True
    )
    registration_no = fields.Char(
        help="Organisation Registration No",
        tracking=True
    )
    organisation_status = fields.Selection(
        [
            ('Active', 'Active'), 
            ('Inactive', 'Inactive')
        ],
        tracking=True
    )
    company_status = fields.Char(tracking=True) #Value from DHET Employer update file
    seta_id = fields.Many2one('res.seta', 'SETA',tracking=True)
    is_interseta = fields.Boolean(help='Indicates if an organisation is being transfered to another SETA')
    sub_sector_id = fields.Many2one('res.sub.sector',tracking=True)
    sic_code_id = fields.Many2one('res.sic.code', string='SIC Code', tracking=True)
    sic_code_desc = fields.Char(
        'SIC Code Description', 
        compute="_compute_sic_code_desc"
    )
    user_id = fields.Many2one("res.users", "Related User")
    password = fields.Char()
    username = fields.Char(string='Username')
    core_business = fields.Text(string='Core Business',tracking=True)
    no_employees = fields.Integer('Number of Employees', tracking=True)
    current_fy_numberof_employees = fields.Integer('Number of Employees (Current FY)',tracking=True) 
    # no_employees_prev_wsp = fields.Integer('Number of Employees (previous WSP submitted)',tracking=True) 
    # no_employees_curr_emp_profile = fields.Integer('Number of Employees (Employment Profile)', tracking=True)
    # no_employees_provincial_breakdown = fields.Integer('Number of Employees (Provincial Breakdown)', tracking=True)
    annual_payroll_report = fields.Binary(string="Annual Payroll",  tracking=True)
    annual_turnover = fields.Float(tracking=True)
    organisation_size_id = fields.Many2one(
        'res.organisation.size', 
        compute="_compute_organisation_size", 
        store=True,
        tracking=True
    )
    organisation_size_desc = fields.Char(
        compute="_compute_organisation_size", 
        store=True
    )
    will_submit_wsp = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Will submit WSP - ATR?",
        tracking=True
    )
    is_unionized = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Is Unionized?",
        tracking=True
    )

    bee_status_id = fields.Many2one('res.bee.status', 'Bee Status', tracking=True)
    bee_status_document = fields.Binary(string="BEE Document", tracking=True)
    require_bee_status_doc = fields.Boolean(help="Technical fields to indicate BEE status DOC is required")
    fsp_number = fields.Char(tracking=True)
    other_sector = fields.Char(tracking=True)

    latitude_degree = fields.Char(string='Latitude Degree', size=3, tracking=True)
    latitude_minutes = fields.Char(string='Latitude Minutes', size=2, tracking=True)
    latitude_seconds = fields.Char(string='Latitude Seconds', size=6, tracking=True)
    
    longitude_degree = fields.Char(string='Longitude Degree', size=3, tracking=True)
    longitude_minutes = fields.Char(string='Longitude Minutes',size=2, tracking=True)
    longitude_seconds = fields.Char(string='Longitude Seconds', size=6, tracking=True)

    should_be_required = fields.Boolean(
        compute="_compute_should_be_required",
        help="Technical Field used to determine " 
            "if a field should be required for logged in user"
    )
    # account_holder = fields.Char() #should default to organisation
    # account_no = fields.Char()
    # account_type = fields.Selection([('normal','Normal')])
    # bank_id = fields.Many2one('res.partner.bank')
    parent_id = fields.Many2one('inseta.organisation', string='Parent Organisation', index=True, ondelete='cascade')

    parent_name = fields.Char(related='parent_id.name', readonly=True, string='Parent name')
    institution_type = fields.Selection([
        ('TVET','TVET'),
        ('UoT','UoT'),
        ('University','University')
    ])


    def _get_linkage_ids_domain(self):
       for rec in self:
            #SDF will see linked organisations after it has been approved
            if (self.env.user.has_group('inseta_skills.group_sdf_user') or \
                self.env.user.has_group('inseta_skills.group_sdf_secondary')) and \
                    self.env.user.id not in self._get_internal_users_ids():
               domain = [('state','in',('active','rework')), ('active', '=', True)]
            else:
                domain = [('active', '=', True)]
            return domain

    linkage_ids = fields.One2many(
        'inseta.organisationlinkages',
        'organisation_id',
        'Child Organisation',
        domain=lambda self: self._get_linkage_ids_domain(), 
        tracking=True
    )


    sdf_ids = fields.One2many(
        'inseta.sdf.organisation', 
        'organisation_id', 
        string="Organisation SDFs",
        tracking=True
    )
    training_committee_ids = fields.One2many(
        'inseta.organisation.training.committee', 
        'organisation_id', 
        string='Training Committee',
        domain=[('active', '=', True)],
        tracking=True
    )
    wspatr_evaluation_ids = fields.One2many('inseta.wspatr.evaluation', 'organisation_id', string='WSP Evaluations')
    wspatr_ids = fields.One2many('inseta.wspatr', 'organisation_id', string='WSP Submissions')
    parent_wspatr_ids = fields.One2many('inseta.wspatr', 'organisation_id', 'WSP Submissions', compute="_compute_parent_wspatr_ids")

    approved_date = fields.Date('Approval Date', readonly=True)
    approved_by = fields.Many2one('res.users')
    rejected_date = fields.Datetime()
    rejected_by = fields.Many2one('res.users')
    rejection_comment = fields.Text()
    rejection_date = fields.Date('Rejection Date', help="Date Skills Manger Rejects SDF registraion")
    rework_date = fields.Date('Rework Date', help="Date Skills Admin Requested the Rework")
    reworked_date = fields.Date('Reworked Date', help="Date SDF Sumbitted the Rework")
    rework_expiration_date = fields.Date('Rework Expiration Date', compute="_compute_rework_expiration", store=True)
    rework_comment = fields.Text(tracking=True)
    employer_update_id = fields.Many2one('inseta.levypayer.organisation.update', 'Levy Employer Update ID')
    
    comment_ids = fields.One2many(
        'inseta.organisationcomments',
        'organisation_id',
        'Comments',
        tracking=True
    )
    document_ids = fields.One2many(
        'inseta.organisationdocuments',
        'organisation_id',
        'Documents',
        tracking=True
    )
    me_ids = fields.One2many(
        'inseta.monitoringevaluationcomments',
        'organisation_id',
        'Monitoring & Evaluation Comments',
        tracking=True
    )

    bank_ids = fields.One2many(
        'inseta.organisationbankingdetails',
        'organisation_id',
        'Bank Details',
        tracking=True
    )
    # legacy system fields. Please do not delete
    possible_sdl_no = fields.Char()
    type_of_organisation_id = fields.Many2one(
        'res.type.organisation', 
        string="Organisation Type",
        tracking=True
    )
    date_of_registration = fields.Date('Registration Date',tracking=True, readonly=True)
    date_business_commenced = fields.Date(tracking=True)
    date_person_became_liable = fields.Date(tracking=True)

    legal_status_id = fields.Many2one('res.legal.status', 'Legal Status')
    partnership_id = fields.Many2one('res.partnership', 'Partnership')
    total_annual_payroll = fields.Float(string='Total Anual Payroll')
    sars_number = fields.Char(string='SARS No.', help="Sars Number", tracking=True)
    cipro_number = fields.Char(string='Cipro Number')
    paye_number = fields.Char(string='Paye Number')
    uif_number = fields.Char(string='UIF Number')
    levy_number_type_id = fields.Many2one(
        'res.levy.number.type', 
        'levy Number Type'
    )
    is_interested_in_communication = fields.Boolean(
        'Is Interested in Communication?'
    )
    dhet_sdl_no = fields.Char('DHET SDL No')
    dhet_legal_name = fields.Char('DHET Legal Name')
    dhet_trade_name = fields.Char('DHET Trade Name')
    dhet_registration_no_type_id = fields.Many2one(
        'res.registration_no_type', 
        string="DHET Registration No Type"
    )
    dhet_registration_no = fields.Char(
        'DHET Registration No', 
        help="Organisation Registration No"
    )
    dhet_type_of_organisation_id = fields.Many2one(
        'res.type.organisation',
        string="DHET Organisation Type"
    )
    dhet_legal_status_id = fields.Many2one(
        'res.legal.status', 'DHET Legal Status')
    dhet_partnership_id = fields.Many2one(
        'res.partnership', 'DHET Partnership')
    dhet_phone = fields.Char()
    dhet_fax_number = fields.Char()
    dhet_sic_code_id = fields.Many2one('res.sic.code', string='DHET SIC Code')
    dhet_sic_code_desc = fields.Char(
        'DHET SIC Code Description', 
        compute="_compute_sic_code_desc"
    )
    dhet_no_employees = fields.Integer(string='DHET Total Number of Employees')
    dhet_total_annual_payroll = fields.Float(string='DHET Total Anual Payroll')
    dhet_sars_number = fields.Char(string='DHET SARS No.', help="Sars Number")
    dhet_cipro_number = fields.Char(string='DHET Cipro Number')
    dhet_paye_number = fields.Char(string='DHET Paye Number')
    dhet_uif_number = fields.Char(string='DHET UIF Number')
    dhet_organisation_size_id = fields.Many2one(
        'res.organisation.size', 
        'DHET Org. Size',  
        compute="_compute_organisation_size", 
        store=True
    )
    dhet_bee_status_id = fields.Many2one('res.bee.status', 'DHET Bee Status')
    dhet_organisation_status = fields.Selection(
        [('Active', 'Active'), ('Inactive', 'Inactive')], 
        'DHET Org. Status'
    )
    dhet_other_sector = fields.Char()
    dhet_annual_turnover = fields.Float()
    
    #client relationship fields
    communication_type = fields.Selection([
        ('Comment','Comments'),
        ('Documents','Documents'),
        ('ME', 'Monitoring & Evalutaion')
    ], default="Documents")
    #extra fields
    legacy_system_id = fields.Integer(readonly=True, index=True)
    active = fields.Boolean(default=True)
    wspatr_count = fields.Integer(compute="_compute_wspatr_count")

    #levy and grant reports
    financial_year_id = fields.Many2one('res.financial.year')
    financial_year_id2 = fields.Many2one('res.financial.year')
    financial_year_id3 = fields.Many2one('res.financial.year')

    residential_address = fields.Char(compute="_compute_residential_address")
    levy_history_html = fields.Html("Levy History")
    levy_history_ids = fields.One2many('inseta.levy.history','organisation_id')
    grant_history_html = fields.Html('Grant History')

    #other fields 
    display_child_link_message = fields.Html(
        compute="_compute_display_child_link_message",
        help="Technical fields to display if a company is linked to a child organisation in WSP submission section"
    )


    @api.onchange("financial_year_id")
    def _onchange_financial_year_id(self):
        if self.financial_year_id:
            environment = self.env['ir.config_parameter'].sudo().get_param('mis_environment', 'development')
            if environment == "development":
                year = self.financial_year_id.date_from.year
                res = sage._get_mandatory_grant_payments(self.sdl_no, fiscal_yr=year)
                _logger.info(f"Mandatory Payments =>  {json.dumps(res, indent=4)}")

                if res.get("error"):
                    error = res.get("error")
                    messgage = error['message']['value']
                    html =  f"""<div class="alert alert-danger"> Error while retrieving payment history from the server. Try again.</div>"""
                else:
                    payments = res.get('value')
                    if not payments:
                        html =  f"""<div class="alert alert-info"> No Records Found! </div>"""
                    else:
                        header = f"""
                            <div class="row" >
                                <div class="col col-md-12">
                                    <table class="table table-stripped">
                                        <thead >
                                            <tr class="bg-primary">
                                                <th> Date</th>
                                                <th> Fiscal Year</th>
                                                <th> Description</th>
                                                <th> Amount</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                        """
                        row = ""
                        total_amount, formated_amount, formated_total_amount = 0.00, 0.00, 0.00
                        sorted_payments = sorted(payments, key=lambda k: k['FiscalYear']) if payments else []
                        for payment in sorted_payments:
                            date = fields.Date.from_string(payment.get('PostingDate'))
                            amount = payment.get('PaymentAmount')
                            formated_amount = '{0:,.2f}'.format(amount).replace(',', ' ')
                            total_amount += amount
                            formated_total_amount = '{0:,.2f}'.format(total_amount).replace(',', ' ')
                            row += f"""<tr>
                                            <td>{date}</td>
                                            <td>{payment.get('FiscalYear')}</td>
                                            <td>Mandatory Grant</td>
                                            <td>R{formated_amount}</td>
                                        </tr>
                                    """

                        footer = f"""
                                        </tbody>
                                        <tfoot>
                                            <tr>
                                                <td colspan="3" style="text-align:right">Total</td>
                                                <td>R{formated_total_amount}</td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            </div>
                        """
                        html = header + row + footer

                self.grant_history_html = html
            else:
                self.grant_history_html =  f"""<div class="alert alert-info"> No Records Found! </div>"""


    @api.onchange("financial_year_id2")
    def _onchange_financial_year_id2(self):
        if self.financial_year_id2:
            date_from = self.financial_year_id2.date_from

            levy_history = self.levy_history_ids.filtered(lambda x: x.date_posted >= date_from)

            _logger.info(f"history {levy_history}")


            if not levy_history:
                html =  f"""<div class="alert alert-info"> No Records Found! </div>"""
            else:
                header = f"""
                    <div class="row" >
                        <div class="col col-md-12">
                            <table class="table table-stripped">
                                <thead>
                                    <tr class="bg-primary">
                                        <th style='width:100px'> SARS Arrival Date</th>
                                        <th style='width:100px'> Date Posted</th>
                                        <th style='width:150px'> Stakeholder Levy <br/>Calculated (100%) </th>
                                        <th> NSF Calculation (20%)</th>
                                        <th> Total Received by SETA (80%)</th>
                                        <th> Mandatory Levy (20%)</th>
                                        <th> Discretionary (49.5%)</th>
                                        <th style='width:100px'> Admin (10.5%)</th>
                                        <th> Penalty (80%)</th>
                                        <th> Interest (80%)</th>
                                    </tr>
                                </thead>
                                <tbody>
                """
                row = ""
                tot_mand_amt  = 0.00
                tot_stakeholder_amt = 0.00
                tot_nsf = 0.00
                tot_seta = 0.00
                tot_desc_amt = 0.00
                tot_admin_amt = 0.00
                tot_penalties = 0.00
                tot_interest  = 0.00
                for payment in levy_history:
                    tot_stakeholder_amt += payment.stakeholder_levy_cal
                    tot_nsf += payment.nsf_cal
                    tot_seta += payment.total_amt
                    tot_mand_amt += payment.mand_grant_amt
                    tot_desc_amt += payment.desc_grant_amt
                    tot_admin_amt += payment.admn_grant_amt
                    tot_penalties += payment.penalties
                    tot_interest += payment.interest

                    row += f"""<tr>
                                    <td>{payment.sars_arrival_date}</td>
                                    <td>{payment.date_posted}</td>
                                    <td>R{'{0:,.2f}'.format(payment.stakeholder_levy_cal).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.nsf_cal).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.total_amt).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.mand_grant_amt).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.desc_grant_amt).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.admn_grant_amt).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.penalties or 0).replace(',', ' ')}</td>
                                    <td>R{'{0:,.2f}'.format(payment.interest or 0).replace(',', ' ')}</td>
                                </tr>
                            """

                footer = f"""
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <td colspan="2" style="text-align:right">Total</td>
                                        <td>R{'{0:,.2f}'.format(tot_stakeholder_amt).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_nsf).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_seta).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_mand_amt).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_desc_amt).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_admin_amt).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_penalties).replace(',', ' ')}</td>
                                        <td>R{'{0:,.2f}'.format(tot_interest).replace(',', ' ')}</td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </div>
                """
                html = header + row + footer
            self.levy_history_html = html


    def action_print_levysummary(self):
        pass


    def action_print_grantsummary(self):
        pass

    def get_sage_posted_documents(self):
        # url = self.env['ir.config_parameter'].sudo().get_param('bulksms.api')
        # token_id = self.env['ir.config_parameter'].sudo().get_param('bulksms.token.id')
        # token_secret = self.env['ir.config_parameter'].sudo().get_param('bulksms.token.secret')
        sage.get_levy_invoices()


# --------------------------------------------
# compute Methods
# --------------------------------------------

    # @api.depends('levy_history_ids')
    # def _compute_levy_status(self):
    #     """
    #         The levy status should read from the levy history on the finance system. 
    #         If the employer have monthly levies of R416.00 and above then it should be regared as levy paying, 
    #         if monthly levies are less than R416.00 then it should be regared as non-levy paying.
    #     """ 
    #     for rec in self:
    #         levies = rec.levy_history_ids.mapped('monthly_levy')
    #         monthly_levy = levies and levies[0].monthly_levy
    #         if monthly_levy > 416:
    #             rec.levy_status = 'Levy Paying'
    #         else:
    #             rec.levy_status = 'Non-Levy Paying'

    @api.depends('state')
    def _compute_parent_wspatr_ids(self):
        """Display WSP Submissions of the parent company in child company
        """
        for rec in self:
            if rec.parent_company:
                rec.parent_wspatr_ids = rec.parent_company.wspatr_ids
            else:
                rec.parent_wspatr_ids = False


    @api.depends('state')
    def _compute_display_child_link_message(self):
        for rec in self:
            if rec.is_childorganisation:
                rec.display_child_link_message = f"<P style='color:red'> * This company is link as a child company to this parent company {self.parent_company and self.parent_company.trade_name or ''}</P>"
            else:
                rec.display_child_link_message = False


    @api.depends('street','street2','street3')
    def _compute_residential_address(self):
        for rec in self:
            rec.residential_address = f"{rec.street or ''} {rec.street2 or ''} {rec.street3 or ''}"


    def _compute_wspatr_count(self):
        for rec in self:
            rec.wspatr_count = self.env['inseta.wspatr'] \
                .sudo() \
                .search_count([('organisation_id','=',rec.id)])
        return True

    @api.depends('state')
    def _compute_should_be_required(self):
        """
            Mandatory fields SHOULD NOT be required  for internal users
        """
        user = self.env.user
        for rec in self:
            rec.should_be_required = True if user.id not in self._get_internal_users_ids() else False


    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            rec.rework_expiration_date = False
            if rec.rework_date:
                rec.rework_expiration_date = date_utils.add(rec.rework_date, days=10)


    @api.depends('sic_code_id', 'dhet_sic_code_id')
    def _compute_sic_code_desc(self):
        for rec in self:
            rec.sic_code_desc, rec.dhet_sic_code_desc = False, False
            if rec.sic_code_id:
                rec.sic_code_desc = rec.sic_code_id.name
            if rec.dhet_sic_code_id:
                rec.dhet_sic_code_desc = rec.dhet_sic_code_id.name

    @api.depends(
        'no_employees',
        'dhet_no_employees',
        'levy_status')
    def _compute_organisation_size(self):
        small_levy = self.env.ref('inseta_base.data_orgsize_small_levy')
        small_non_levy = self.env.ref(
            'inseta_base.data_orgsize_small_non_levy')
        medium = self.env.ref('inseta_base.data_orgsize_medium')
        large = self.env.ref('inseta_base.data_orgsize_large')
        #            ('Levy Paying','Levy Paying'),
        #('Non-Levy Paying','Non-Levy Paying')
        for rec in self:
            if rec.no_employees <= 49:
                rec.organisation_size_id = small_levy.id \
                    if rec.levy_status == 'Levy Paying' \
                    else small_non_levy.id
                rec.organisation_size_desc = "Small"
            elif rec.no_employees > 49 and rec.no_employees <= 149:
                rec.organisation_size_id = medium.id
                rec.organisation_size_desc = "Medium"
            else:
                rec.organisation_size_id = large.id
                rec.organisation_size_desc = "Large"
            # DHET organisation size
            if rec.dhet_no_employees <= 49:
                rec.dhet_organisation_size_id = small_levy.id \
                    if rec.levy_status == 'Levy Paying' \
                    else small_non_levy.id
            elif rec.dhet_no_employees > 49 and rec.dhet_no_employees <= 149:
                rec.dhet_organisation_size_id = medium.id
            else:
                rec.dhet_organisation_size_id = large.id

# --------------------------------------------
# Onchange methods
# --------------------------------------------

    # @api.constrains('child_ids')
    # def _check_childs(self):
    #     '''
    #         A minimum of two contacts are required. during wsp submission
    #     '''
    #     for rec in self:
    #         records = rec.mapped('child_ids')
    #         if rec.organisation_size_desc != "Small" and  len(records) < 2:
    #             raise ValidationError("A minimum of two contacts are required") 

    @api.constrains('training_committee_ids')
    def _check_training_committee(self):
        '''
            A minimum of two committee members are required
        '''
        for rec in self:
            records = rec.mapped('training_committee_ids')
            if rec.organisation_size_desc != "Small" and  len(records) < 2:
                raise ValidationError("A minimum of two committee members are required") 

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive Partner hierarchies.'))

    @api.onchange('bee_status_id')
    def _onchange_bess_status_id(self):
        noncompliant = self.env.ref('inseta_base.data_bee_status9', raise_if_not_found=False)
        exempt =  self.env.ref('inseta_base.data_bee_status11',raise_if_not_found=False)
        non_bee = self.env.ref('inseta_base.data_bee_status10', raise_if_not_found=False)
        if self.bee_status_id.id not in (noncompliant.id, exempt.id, non_bee.id):
            self.require_bee_status_doc = True
        else:
            self.require_bee_status_doc = False


    @api.onchange('trade_name')
    def _onchange_trade_name(self):
        if self.trade_name:
            self.name = self.trade_name

    @api.onchange('physical_code')
    def _onchange_physical_code(self):
        if self.physical_code:
            phy_code = self.physical_code
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.physical_code)], limit=1)
            if not sub:
                self.physical_code = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _("Suburb with Physical Code {phycode} not found!").format(phycode=phy_code)
                    }
                } 
            if sub:
                self.physical_suburb_id = sub.id
                self.physical_municipality_id = sub.municipality_id.id
                self.physical_province_id = sub.district_id.province_id.id
                self.physical_city_id = sub.city_id.id
                #self.nationality_id = sub.nationality_id.id
                self.physical_urban_rural = sub.municipality_id.urban_rural


    @api.onchange('postal_code')
    def _onchange_postal_code(self):
        if self.postal_code:
            post_code = self.postal_code
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.postal_code)], limit=1)
            if not sub:
                self.postal_code = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _("Suburb with Postal Code {postcode} not found!").format(postcode=post_code)
                    }
                } 
            if sub:
                self.postal_suburb_id = sub.id
                self.postal_municipality_id = sub.municipality_id.id
                self.postal_province_id = sub.district_id.province_id.id
                self.postal_city_id = sub.city_id.id
                #self.nationality_id = sub.nationality_id.id
                self.postal_urban_rural = sub.municipality_id.urban_rural


    @api.onchange('use_physical_for_postal_addr')
    def _onchange_use_physical_for_postal_addr(self):
        if self.use_physical_for_postal_addr:
            self.postal_municipality_id = self.physical_municipality_id.id
            self.postal_suburb_id = self.physical_suburb_id.id
            self.postal_province_id = self.physical_province_id.id
            self.postal_city_id = self.physical_city_id.id
            self.postal_urban_rural = self.physical_urban_rural
            self.postal_address1 = self.street
            self.postal_address2 = self.street2
            self.postal_address3 = self.street3
            self.postal_code = self.physical_code
        else:
            self.postal_municipality_id = False
            self.postal_suburb_id = False
            self.postal_province_id = False
            self.postal_city_id = False
            self.postal_urban_rural = False
            self.postal_address1 = False
            self.postal_address2 = False
            self.postal_address3 = False
            self.postal_code = False


    ######### ORM method overrides ########

    @api.model
    def create(self, vals):
        #employer_update_id is set when levy org. are imported from DHET file.
        #we will use it to identify when user is creating a levy org. from backend 
        #and then raise a validation error
        if 'levy_status' not in vals:
            raise ValidationError(_(
                'Levy Status is Required' 
            ))

        if 'employer_update_id' not in vals and vals.get('levy_status') == 'Levy Paying':
            raise ValidationError(_(
                'You cannot create a Levy Paying Organisation from here.\n' 
                'Levy Organisations are Imported from DHET Employer File.\n'
                'To create a Non-Levy Organisation, select "Non-Levy Paying" as Levy Status OR\n'
                'use the "Non-Levy Employer" menu'
            ))

        if 'levy_status' in vals and vals.get('levy_status') == 'Non-Levy Paying':
            # raise ValidationError(_('You cannot register a Levey Paying Employer. ' 
            # 'Kindly Use the Update Employer Feature to Upload Employer from DHET file'))
            sequence = self.env['ir.sequence'].sudo().next_by_code('nonlevy.employer.no')
            vals['sdl_no'] = sequence
            
        #We dont want to validate GPS on create cos, the action that generates the cordinates,
        #needs to save the form first.
        # if not vals.get('latitude_degree'):
        #     raise ValidationError('Latitude is required')
        # if not vals.get('longitude_degree'):
        #     raise ValidationError('Longitude is required')

        return super(InsetaOrganisation, self).create(vals)


    def write(self, vals):
      for rec in self:
        if not self._context.get("allow_write"):
            if not (self.is_confirmed or vals.get('is_confirmed')):
                raise ValidationError(_('Please tick the confirm checkbox to validate that Organisation Details are correct')) 

        if 'latitude_degree' in vals and not vals.get('latitude_degree'):
            raise ValidationError('Latitude is required')

        if 'longitude_degree' in vals and not vals.get('longitude_degree'):
            raise ValidationError('Longitude is required')

        if 'child_ids' in vals:
            if not (self.confirm_contact or vals.get('confirm_contact')):
                raise ValidationError(_('Please tick the confirm checkbox to validate that Contact Details are correct')) 

        if 'training_committee_ids' in vals:
            if not (self.confirm_training_committee or vals.get('confirm_training_committee')):
                raise ValidationError(_('Please tick the Confirm checkbox to validate that the Training Committee details are correct')) 

        if 'cfo_ids' in vals:
            if not (self.confirm_cfo or vals.get('confirm_cfo')):
                raise ValidationError(_('Please tick the Confirm checkbox to validate that the CFO details are correct')) 

        if 'ceo_ids' in vals:
            if not (self.confirm_ceo or vals.get('confirm_ceo')):
                raise ValidationError(_('Please tick the Confirm checkbox to validate that the CEO details are correct')) 

        if 'bank_ids' in vals:
            if not (self.confirm_bank or vals.get('confirm_bank')):
                raise ValidationError(_('Please tick the Confirm checkbox to validate that the Bank details are correct')) 

        #   if not self._context.get('allow_write') and \
        #       rec.state in ('approve',):
        #       raise ValidationError(
        #           _('organisation is already approved. \n To make any changes to reset to draft.'))
      return super(InsetaOrganisation, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'rework'):
                raise ValidationError(
                    _('You can not delete an approved organisation'))
        return super(InsetaOrganisation, self).unlink()

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.sdl_no, rec.legal_name)
            arr.append((rec.id, name))
        return arr
    
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
		# optimize out the default criterion of ``ilike ''`` that matches everything
        if not (name == '' and operator == 'ilike'):
            args += ['|', (self._rec_name, operator, name), ('sdl_no', operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
        

# --------------------------------------------
# Business Logic
# --------------------------------------------
    def action_set_to_draft(self):
        self.state = 'draft'

    def assign_lno(self, new_sdl_no):
        for rec in self:
            if new_sdl_no:
                rec.with_context(allow_write=True).write({'sdl_no': new_sdl_no})


    def rework_registration(self, comment):
        """Skill admin query Registration and ask SDF to rework.
        This method is called from the rework wizard

        Args:
            comment (str): Reason for rework
        """
        #if Skills Manager, reworks a registration, workflow to skills specialist
        if self.env.user.has_group("inseta_skills.group_skills_manager") and self.state == "pending_approval":
            self.write({
                'state': 'rework_skill_admin', 
                'rework_comment': comment, 
            })
        else:        
            self.write({
                'state': 'rework', 
                'rework_comment': comment, 
                'rework_date': fields.Date.today()
            })
        self.activity_update()

    def reject_registration(self, comment):
        """Skill manger rejects Org registration.
        This method is called from the reject wizard

        Args:
            comment (str): Reason for rejection
        """
        self.write({
            'state': 'reject', 
            'rejection_comment': comment, 
            'rejection_date': fields.Date.today(),
            "rejected_by": self.env.user.id,
        })
        self.activity_update()

    def action_request_manager_rejection(self):
        """Skill admin submits to Skill manager for rejection
        if org does not rework after 10 days
        """
        self.write({'state': 'awaiting_rejection2'})
        self.activity_update()


    def action_submit(self):
        training_committee = self.mapped('training_committee_ids')
        banks = self.mapped('bank_ids')
        contacts =  self.mapped('child_ids')
        ceo = self.mapped('ceo_ids')
        cfo = self.mapped('cfo_ids')

        if self.organisation_size_desc != 'Small' and not training_committee:
            raise ValidationError('Please provide training committee members !!!')

        if not banks:
            raise ValidationError('Please provide organisation banking details')

        if not contacts:
            raise ValidationError('You must provide at least one contact person')

        if not ceo:
            raise ValidationError('Please provide organisation CEO Details')

        if not cfo:
            raise ValidationError('Please provide organisation CFO Details')

        if self.require_bee_status_doc:
            if not self.document_ids.filtered(lambda x: x.documentrelates_id.saqacode == "BEE"):
                raise ValidationError('Please upload BEE certificate in "Client Relationship Management" ')
        
        if not self.rework_date: #initial submit
            state = "pending_approval" if self.levy_status == "Levy Paying" else "submit"
            self.write({'state': state, })
        else: #if sdf resubmits registration after rework 
            self.write({'reworked_date': fields.Date.today()})

        self.activity_update()


    def action_verify(self):
        self.write({
            'state': 'pending_approval', 
        })
        self.activity_update()

    def action_approve_levy(self):
        self.write({
            'state': 'approve', 
            'approved_date': fields.Date.today(),
            'approved_by': self.env.user.id,
        })
        self.activity_update()

    def action_approve(self):
        self.with_context(allow_write=True).write({
            'state': 'approve', 
            'approved_date': fields.Date.today(),
            'approved_by': self.env.user.id,
        })
        #Add  this organisation to user profile allowed organisations
        self.user_id.sudo().write({'allowed_organisation_ids':[(4,self.id)]})
        self.activity_update()


    # def action_reject(self):
    #     self.write({
    #         'state': 'reject', 
    #         'rejected_date': fields.Date.today(),
    #         'rejected_by': self.env.user.id,
    #     })
    #     self.activity_update()


    def action_print_approval_letter(self):
        return self.env.ref('inseta_skills.action_organisation_approval_letter_report').report_action(self)

    def action_print_rejection_letter(self):
        return self.env.ref('inseta_skills.action_organisation_rejection_letter_report').report_action(self)

    def action_work_addr_map(self):
        street =  f"{self.street or ''} {self.street2 or ''} {self.street3 or ''}"
        city = self.physical_city_id
        state = self.state_id
        country = self.country_id
        zip = self.physical_code
        self.open_map(street, city, state, country, zip)

    def action_postal_addr_map(self):
        street =  f"{self.postal_address1 or ''} {self.postal_address2 or ''} {self.postal_address3 or ''}"
        city = self.postal_city_id
        state = self.state_id
        country = self.country_id
        zip = self.postal_code
        self.open_map(street, city, state, country, zip)

    def open_map(self, street, city, state, country, zip):
        url="http://maps.google.com/maps?oi=map&q="
        if street:
            url+=street.replace(' ','+')
        if city:
            url+='+'+city.name.replace(' ','+')
        if state:
            url+='+'+state.name.replace(' ','+')
        if country:
            url+='+'+country.name.replace(' ','+')
        if zip:
            url+='+'+zip.replace(' ','+')

        _logger.info(f"Partner Google Map => {url}")
        return {
            'type': 'ir.actions.act_url',
            'url':url,
            'target': 'new'
        }
            

    def get_geolocation(self):
        # We need country names in English below
        for rec in self.with_context(lang='en_US'):
            result = self.partner_id._geo_localize(
                rec.street,
                rec.physical_code,
                rec.physical_city_id.name,
                rec.state_id.name,
                rec.country_id.name
            )

            if result:
                cordinates =  dd2dms(result[0],result[1])
                if cordinates:
                    _logger.info(f"{cordinates[0]} {cordinates[1]} {cordinates[2]} {cordinates[3]} {cordinates[4]} {cordinates[5]}")
                    rec.write({
                        'latitude_degree': cordinates[0],
                        'latitude_minutes': cordinates[1],
                        'latitude_seconds': cordinates[2],
                        'longitude_degree': cordinates[3],
                        'longitude_minutes': cordinates[4],
                        'longitude_seconds': cordinates[5],
                    })
        return True

    
    def get_contact_email(self):
        if not self.child_ids:
            return [str(self.email)]
        contact_emails = [str(contact.email) for contact in self.child_ids] 
        sdf_emails = [str(item.sdf_id.partner_id.email) for item in self.sdf_ids] 
        emails = contact_emails or sdf_emails
        return ",".join(emails) if emails else ''


    def _get_skills_admin(self):
        grp = self.env.ref('inseta_skills.group_skills_admin',raise_if_not_found=False)
        return grp and self.env['res.groups'].sudo().browse([grp.id]).users or []

    def get_skill_admin_email(self):
        emails = [str(user.partner_id.email)
                  for user in self._get_skills_admin()]
        return ",".join(emails) if emails else ''

    def get_skill_spec_email(self):
        grp = self.env.ref('inseta_skills.group_skills_specialist',raise_if_not_found=False)
        users =  grp and self.env['res.groups'].sudo().browse([grp.id]).users or []
        emails = [str(user.partner_id.email)for user in users]
        return ",".join(emails) if emails else ''

    def get_skills_mgr(self):
        # grp_skills_mgr = self.env.ref(
        #     'inseta_skills.group_skills_manager', raise_if_not_found=False)
        # return grp_skills_mgr and self.env['res.groups'].sudo().browse([grp_skills_mgr.id]).users or []
        return self.env['res.users'].sudo().search([('is_skills_mgr','=',True)]) or []

    def get_skill_mgr_email(self):
        emails = [str(user.partner_id.email)
                  for user in self.get_skills_mgr()]
        return ",".join(emails) if emails else ''


    def _get_internal_users_ids(self):
        Group = self.env['res.groups']
        skill_specialist_group_id = self.env.ref('inseta_skills.group_skills_specialist').id
        skill_manager_group_id = self.env.ref('inseta_skills.group_skills_manager').id
        skill_admin_group_id = self.env.ref('inseta_skills.group_skills_admin').id
        view_only_grp_id = self.env.ref('inseta_skills.group_skills_view_only').id
        users = Group.browse([skill_specialist_group_id,skill_manager_group_id,skill_admin_group_id,view_only_grp_id]).users
        return users and users.ids or []

    def _get_external_users_ids(self):
        Group = self.env['res.groups']
        grp_primary_sdf_id = self.env.ref('inseta_skills.group_sdf_user').id
        grp_sec_sdf_id = self.env.ref('inseta_skills.group_sdf_secondary').id
        grp_emp_id = self.env.ref('inseta_skills.group_employer').id
        users = Group.browse([grp_primary_sdf_id,grp_sec_sdf_id,grp_emp_id]).users
        return users and users.ids or []

    #Server action 
    def get_filtered_record(self):
        #because SDFs will be able to link Other organisations to their account, 
        #we will use server action instead of record rule to restrict the 
        #organisations registration they are able to see

        view_id_form = self.env['ir.ui.view'].search([('name', '=', 'inseta_skills.view_organization_form')])
        view_id_tree = self.env['ir.ui.view'].search([('name', '=', 'inseta_skills.view_organisation_tree')])
        user = self.env.user
        record_ids = []
        if user.id in self._get_external_users_ids():
            _logger.info("Retrieving records for external users ...")

            sdf = self.env['inseta.sdf'].sudo().search([('partner_id','=', user.partner_id.id)], order="id desc", limit=1)
        
            #filter organisations where the SDF is approved
            sdf_organisations = sdf and sdf.organisation_ids.filtered(lambda r: r.state == "approve") or []
            all_sdf_organisations = [o.organisation_id.id for o in sdf_organisations] + [o.id for o in user.allowed_organisation_ids]
            _logger.info(f"Retrieving {all_sdf_organisations}")

            #get user sdf record
            domain = [
                '|',
                ('id', 'in', all_sdf_organisations),
                ('id', 'in', [o.childorganisation_id.id for o in user.allowed_organisation_ids.mapped('linkage_ids').filtered(lambda x: x.state=='active')]),
            ]
            record_ids = self.search(domain).ids

        if user.id in self._get_internal_users_ids():
            _logger.info("Retrieving records for internal users ...")
            record_ids = self.search([]).ids

        return {
            'type': 'ir.actions.act_window',
            'name': _('Organisations'),
            'res_model': 'inseta.organisation',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id_tree.id, 'tree'), (view_id_form.id,'form')],
            'target': 'current',
            'domain': [('id', 'in', record_ids)]
        }


    def get_filtered_record_nonlevy(self):
        #because SDFs will be able to link Other non levy organisations to their account, 
        #we will use server action instead of record rule to restrict the 
        #non levy organisations registration they are able to see
        
        view_id_form = self.env['ir.ui.view'].search([('name', '=', 'inseta_skills.view_organization_form')])
        view_id_tree = self.env['ir.ui.view'].search([('name', '=', 'inseta_skills.view_organisation_tree')])
        user = self.env.user
        record_ids = []
        if user.id in self._get_external_users_ids():
            _logger.info("Retrieving non levy records for external users ...")
            domain = [('levy_status','=','Non-Levy Paying'),('state','!=','approve')]
            domain += ['|',('id', 'in', [o.id for o in user.allowed_organisation_ids]),('id', 'in', [o.childorganisation_id.id for o in user.allowed_organisation_ids.mapped('linkage_ids').filtered(lambda x: x.state=='active')])]
            record_ids = self.search(domain).ids

        if user.id in self._get_internal_users_ids():
            domain = [('levy_status','=','Non-Levy Paying'),('state','!=','approve')]
            _logger.info(f"Retrieving non levy records for internal users ...{domain}")
            record_ids = self.search(domain).ids


        context = dict(self._context or {})
        context.update({"default_levy_status":"Non-Levy Paying"})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Organisations'),
            'res_model': 'inseta.organisation',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id_tree.id, 'tree'), (view_id_form.id,'form')],
            'target': 'current',
            'domain': [('id', 'in', record_ids)],
            'context': context
        }


    def _validate_required_fields(self):
        """Validates Mandatory Fields in Organisation.
        This method is handy when submitting a WSP. We can use it to validate that
        the organisation details are complete and correct. Child Organisations are 
        also required to be validated during WSP.
        SDL No, Legal Name, Trade Name, Registration number, FSP license, Phone number, 
        SIC code, other sector, Payroll, Annual turnover, BEE status, GPS coordinates, 
        Physical code, Physical Address Line 1 and 2, Physical suburb, Physical city, Physical municipality, 
        physical province, urban/rural status, Postal code, Postal Address Line 1 and 2, Postal suburb, Postal city, 
        Postal municipality, Postal province, Postal urban/rural status and confirmation details tic box.  

        """
        errors = []
        for rec in self:
            pass

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(InsetaOrganisation, self)._message_auto_subscribe_followers(
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
            self.message_post_with_template(
                template.id, composition_mode='comment',
                model='inseta.organisation', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template, mail_template2 = False, False
        #Skills admin request rework, state chnages to rework, notify SDF and SDF Employer
        if self.state == 'rework':
            #schedule an activity for rework expiration for  SDF user
            self.activity_schedule(
                'inseta_skills.mail_act_employerupdate_rework',
                user_id=self.env.user.id,
                date_deadline=self.rework_expiration_date)
            mail_template = self.env.ref('inseta_skills.mail_template_notify_dhet_levyemployer_rework_sdf', raise_if_not_found=False)


        if self.state == 'submit':
            mail_template =  self.env.ref('inseta_skills.mail_template_notify_nonlevy_org_skilladmin', raise_if_not_found=False)
            mail_template2 = self.env.ref('inseta_skills.mail_template_notify_nonlevy_org_contacts', raise_if_not_found=False)

        #Skill admin verifies registration, state changes to pending_approval. notify skill mgr and SDF Employer
        if self.state == 'pending_approval':
            mail_template =  self.env.ref('inseta_skills.mail_template_notify_nonlevy_org_afterverify_skillmgr', raise_if_not_found=False)
       
        #Skill Manager queries registration, and asks SKill admin to rework. state changes to rework_skill_admin 
        if self.state == 'rework_skill_admin':
            mail_template = self.env.ref('inseta_skills.mail_template_notify_skills_admin_after_mgr_rework_org', raise_if_not_found=False)       
        
        if self.state == 'approve':
            mail_template =  self.env.ref('inseta_skills.mail_template_notify_org_approval_sdf', raise_if_not_found=False)

        if self.state == 'reject':
            mail_template =  self.env.ref('inseta_skills.mail_template_notify_org_rejection_sdf', raise_if_not_found=False)
        #unlink employer rework activity if rework is submitted
        self.filtered(lambda s: s.state in ('pending_approval','approve')).activity_unlink(['inseta_skills.mail_act_employerupdate_rework'])

        self.with_context(allow_write=True)._message_post(mail_template) #notify sdf
        self.with_context(allow_write=True)._message_post(mail_template2) #notify employers


# class testingclas(models.TransientModel):
#     _name = "inseta.organisation.linkage.rework.wizard"
class InsetaOrganisationLinkages(models.Model):
    _name = "inseta.organisationlinkages" #dbo.organisationlinkages.csv
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Organisation Linkages"
    _rec_name = "childorganisation_id"

    # @api.model
    # def default_get(self, fields):
    #     res = super(InsetaOrganisationLinkages, self).default_get(fields)
    #     _logger.info(f"org ID {self._context.get('default_organisation_id')}")
    #     if 'default_organisation_id' in self._context:
    #         res.update({
    #             'organisation_id': self._context.get('default_organisation_id'),
    #         })
    #     return res


    parent_has_submitted_wsp = fields.Boolean(
        'Does parent org. has an approved WSP for the financial year?', 
        compute="_compute_has_parent_approved_wsp",
        store=True,
        readonly=False,
        help="Indicates if the parent organisation has an approved WSP for the financial year",
    )
    state = fields.Selection([
        ('draft','draft'),
        ('submit','Submitted'),
        ('rework','Reworked'),
        ('active','Active'),
        ('terminate','Terminated')
    ],default="draft")

    organisation_id = fields.Many2one('inseta.organisation', 'Parent Organisation')
    childorganisation_id = fields.Many2one('inseta.organisation','Child Organisation')
    sdl_no = fields.Char(help="Child Organisation SDL")
    trade_name = fields.Char(compute="_compute_trade_name")
    legal_name = fields.Char(compute="_compute_trade_name")
    linkstartdate = fields.Date('Link Start Date')
    linkenddate = fields.Date('Link End Date')

    # linkenddate = fields.Date('Link End Date', compute="_compute_linkenddate", store=True)
    uploaddocumentid = fields.Integer() #legacy system fields
    removedocumentid = fields.Integer() #legacy system fields
    link_request_doc = fields.Binary("Request Document")
    file_name = fields.Char("Request Document Name")

    link_termination_doc = fields.Binary("Termination Document")
    link_termination_doc_filename = fields.Char("Termination Doc. Name")

    termination_date = fields.Date(help="Date link is terminated ")

    financialyear_id = fields.Many2one('res.financial.year')
    financialyearstart_id = fields.Many2one('res.financial.year','Link Start (Financial Year)')
    financialyearend_id = fields.Many2one('res.financialyearlinkend','Link End (Financial Year) if applicable')
    active = fields.Boolean(default=True) #isdeleted
    confirm = fields.Boolean('I hereby confirm that the following information submitted is complete, accurate and not missleading')
    is_required_for_skillspec = fields.Boolean(compute="_compute_is_required_for_skillspec", store=False)
    rework_comment = fields.Text()
    rework_date = fields.Date()
    action = fields.Selection([('approve','Approve'),('rework','Rework')])

    def is_active(self):
        if (self.linkstartdate and not self.linkenddate) or \
            (self.linkstartdate and self.linkenddate > fields.Date.today())  or \
            self.state == 'active':
            return True
        return False


    @api.depends('organisation_id')
    def _compute_is_required_for_skillspec(self):
        for rec in self:
            if rec.env.user.has_group('inseta_skills.group_skills_specialist'):
                rec.is_required_for_skillspec = True
            else:
                rec.is_required_for_skillspec = False


    @api.depends("financialyearstart_id")
    def _compute_has_parent_approved_wsp(self):
        for rec in self:
            if rec.financialyearstart_id and \
                rec.organisation_id.wspatr_ids.filtered(lambda x: x.financial_year_id.id == rec.financialyearstart_id.id \
                and x.state not in ('draft,')):
                rec.parent_has_submitted_wsp = True
            else:
                rec.parent_has_submitted_wsp = False


    @api.depends('childorganisation_id')
    def _compute_trade_name(self):
        for rec in self:
            if rec.childorganisation_id:
                rec.trade_name = rec.childorganisation_id.trade_name
                rec.legal_name = rec.childorganisation_id.legal_name
            else:
                rec.trade_name = False
                rec.legal_name = False


    # @api.depends('financialyearstart_id', 'financialyearend_id')
    # def _compute_linkenddate(self):
    #     for rec in self:
    #         if rec.financialyearstart_id and rec.financialyearend_id:
    #             rec.linkenddate = rec.financialyearend_id.date_to
    #         elif rec.financialyearstart_id and not rec.financialyearend_id:
    #             rec.linkenddate = rec.financialyearstart_id.date_to
    #         else:
    #             rec.linkenddate = False

    @api.onchange('state')
    def _onchange_state(self):
        """ For some reasons, organisation_id is not being set active_id passed from  context in the view.
            Below is a workaround to set the active organisation
         """
        self.organisation_id = self._context.get('default_organisation_id')

    @api.onchange('financialyear_id')
    def _onchange_financialyear_id(self):
        if self.financialyear_id:
            self.linkstartdate = self.financialyear_id.date_from
            self.linkenddate = self.financialyear_id.date_to


    # @api.onchange('financialyearstart_id')
    # def _onchange_financialyearstart_id(self):
    #     if self.financialyearstart_id:
    #         self.linkstartdate = self.financialyearstart_id.date_from
    #         self.linkenddate = self.financialyearstart_id.date_to

    # @api.onchange('financialyearstart_id', 'financialyearend_id')
    # def _onchange_linkenddate(self):
    #     for rec in self:
    #         if rec.financialyearstart_id and rec.financialyearend_id:
    #             rec.linkenddate = rec.financialyearend_id.date_to
    #         elif rec.financialyearstart_id and not rec.financialyearend_id:
    #             rec.linkenddate = rec.financialyearstart_id.date_to
    #         else:
    #             rec.linkenddate = False


    @api.onchange('childorganisation_id','financialyear_id')
    def _onchange_childorganisation_id(self):
        if self.childorganisation_id and self.childorganisation_id.is_childorganisation:
            raise ValidationError(_('The selected company is already a child organisation. It can not be linked to multiple parent companies'))

        if self.childorganisation_id and self.financialyear_id:
            records = self.search([
                ('childorganisation_id','=',self.childorganisation_id.id),
                ('financialyear_id','=',self.financialyear_id.id)
            ])
            child_org = self.childorganisation_id
            fy = self.financialyear_id
            _logger.info(f"linked records {records}")
            if len(records):
                self.financialyear_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _(
                            "'{child_org}' has already been linked to an organisation for the selected financial year '{fy}'"
                        ).format(
                            child_org=child_org.legal_name,
                            fy=fy.name
                        )
                    }
                }

    @api.model
    def create(self, vals):
        if 'sdl_no' not in vals:
            raise ValidationError(_(
                'SDL No is Required' 
            ))

        parent_org = self.env['inseta.organisation'].search([('id', '=', vals.get('organisation_id'))])

        if parent_org  and parent_org.sdl_no == vals.get('sdl_no'):
            raise ValidationError(_(
                "You cannot link an organisation as a child to itself"
            ))

        org = self.env['inseta.organisation'].search([('sdl_no', '=', vals.get('sdl_no'))], limit=1)

        if not org:
            raise ValidationError(_(
                "Organisation with SDL NO '{sdlno}' is not found"
            ).format(
                sdlno=vals.get('sdl_no')
            ))

        if org.state != 'approve':
            self.sdl_no = False
            raise ValidationError(_(
                "Organisation with SDL NO '{sdlno}' is not yet approved. Kindly contact support"
            ).format(
                sdlno=vals.get('sdl_no')
            ))

        return super(InsetaOrganisationLinkages, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft',):
                raise ValidationError(
                    _('You can not delete a link that has been submitted or approved'))
        return super(InsetaOrganisationLinkages, self).unlink()


    def action_search_organisation(self):
        if self.sdl_no:
            _logger.info("SEARCH Called")
            org = self.env['inseta.organisation'].search([('sdl_no', '=', self.sdl_no)], limit=1)
            sdlno = self.sdl_no
            if not org:
                _logger.info("SEARCH Called nit found")

                self.sdl_no = False
                raise ValidationError(_(
                    "Organisation with SDL NO '{sdlno}' is not found"
                ).format(
                    sdlno=sdlno,
                ))

            if org.state != 'approve':
                self.sdl_no = False
                raise ValidationError(_(
                    "Organisation with SDL NO '{sdlno}' is not yet approved. Kindly contact support"
                ).format(
                    sdlno=sdlno,
                ))
            self.childorganisation_id = org.id

    def download_link_request_doc(self):
        if self.link_request_doc:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model=inseta.organisationlinkages&id={}&field=link_request_doc&filename_field=file_name&download=true'.format(self.id),
                'target': 'self',
            }

    def download_termination_doc(self):
        if self.link_termination_doc:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model=inseta.organisationlinkages&id={}&field=link_termination_doc&filename_field=link_termination_doc_filename&download=true'.format(self.id),
                'target': 'self',
            }

    def action_reset(self):
        self.write({'state':'draft'})   

    def action_submit(self):
        if self.childorganisation_id.is_childorganisation:
            raise ValidationError(_('The selected company is already a child organisation.  It can not be linked to multiple parent companies'))

        self.write({'state':'submit'})   
        self.activity_update()   

    def action_rework(self):
        if not self.action == "rework":
            raise ValidationError(_('Please select "rework" as the action'))
        self.write({
            'state':'rework',
            'rework_comment': self.rework_comment, 
            'rework_date': fields.Date.today()
        })   
        self.activity_update()   

    def action_terminate(self):
        if not self.link_termination_doc:
            raise ValidationError("Please upload termination document")

        today = fields.Date.today()
        if today > self.linkenddate and not self.env.user.has_group("inseta_skills.group_skills_manager"):
            raise ValidationError(_('Only Skills Manager can terminate a link before the link end date'))

        self.write({
            'state':'terminate', 
            'termination_date': fields.Date.today() 
        })   
        self.activity_update()  


    def action_link(self):
        """Skills Administrator, Specialist and Manager must be able to create a new link, 
            select the start and end date of the link and add supporting documents
        """

        if not self.action == "approve":
            raise ValidationError(_('Please select "approve" as the action'))

        #validate required fields
        if not self.financialyear_id:
            raise ValidationError(_('Financial year is required'))

        if not self.linkstartdate:
            raise ValidationError(_('Link start date is required'))

        if not self.linkenddate:
            raise ValidationError(_('Link end date is required'))
        #check if parent organisation has submitted WSP for the selected financial year start
        #A link will not be accepted when the WSP/ATR has been submitted and 
        #only a skill manager can force the link to the approved WSP/ATR.

        if self.financialyear_id and self.organisation_id.wspatr_ids.filtered(lambda x: x.financial_year_id.id == self.financialyear_id.id and x.state == 'approve'):
            raise ValidationError(_('A child company can not be linked to a parent after the WSP/ATR of the parent company has been approved.'))
            #if wsp_submission.state not in ('draft',) and not self.env.user.has_group("inseta_skills.group_skills_manager"):
            #     raise ValidationError(_('Only a skill manager can force the link to orgnaisation with a submitted WSP/ATR.'))

                # self.with_context(allow_write=True).write({
                #     'state': 'active', 
                # })
            #link the parent org wsp to child organisation
            # parent_wsps = self.organisation_id.wspatr_ids.filtered(lambda x: x.financial_year_id.id == self.financialyearstart_id.id and x.state not in ('draft,'))
            # self.childorganisation_id.write({'wspatr_ids': parent_wsps})

        self.with_context(allow_write=True).write({
            'state': 'active', 
        })
        self.activity_update()   


    # def action_force_link(self):
    #     """A link will not be accepted when the WSP/ATR has been submitted and 
    #     only a skill manager can force the link to the approved WSP/ATR.
    #     """
    #     if not self.env.user.has_group("inseta_skills.group_skills_manager"):
    #         raise ValidationError(_('Only a skill manager can force the link to orgnaisation with approved WSP/ATR.'))

    #     self.with_context(allow_write=True).write({
    #         'state': 'active', 
    #     })
    #     #link the parent org wsp to child organisation
    #     parent_wsps = self.organisation_id.wspatr_ids.filtered(lambda x: x.financial_year_id.id == self.financialyearstart_id.id and x.state not in ('draft,'))
    #     self.childorganisation_id.write({'wspatr_ids': parent_wsps})

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def get_parent_child_sdf_emails(self):
        """

            Termination email to be sent to the parent and child organisations SDF’s 
            and copy skills central mail: email 
        """
        parent_sdfs = self.organisation_id.sdf_ids.filtered(lambda x: x.state == 'approve' and x.sdf_role == 'primary')
        child_sdfs = self.childorganisation_id.sdf_ids.filtered(lambda x: x.state == 'approve' and x.sdf_role == 'primary')
  
        parent_sdf_emails = [str(sdforg.sdf_id.partner_id.email) for sdforg in parent_sdfs] 
        child_sdf_emails = [str(sdforg.sdf_id.partner_id.email) for sdforg in child_sdfs] 
        emails = parent_sdf_emails + child_sdf_emails + ['skills@inseta.org.za']
        return ",".join(emails) if emails else ''

    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            self.message_post_with_template(
                template.id, composition_mode='comment',
                model='inseta.organisationlinkages', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template = False
        #Skills admin request submit
        if self.state == 'submit':  
            mail_template = self.env.ref('inseta_skills.mail_template_org_linkage_submit', raise_if_not_found=False)
        #Skills admin request rework, state chnages to rework, notify SDF and SDF Employer
        if self.state == 'rework':
            mail_template = self.env.ref('inseta_skills.mail_template_org_linkage_rework', raise_if_not_found=False)

        #Skills spec approved the linking
        if self.state == 'active':
            mail_template = self.env.ref('inseta_skills.mail_template_org_linkage_approved', raise_if_not_found=False)

        #Skills mgr terminate
        if self.state == 'terminate':
            mail_template = self.env.ref('inseta_skills.mail_template_org_linkage_terminated', raise_if_not_found=False)
        #unlink employer rework activity if rework is submitted
        self.filtered(lambda s: s.state in ('active',)).activity_unlink(['inseta_skills.mail_act_employerupdate_rework'])

        self._message_post(mail_template) #notify sdf



class InsetaOrganisationME(models.Model):
    _name = "inseta.monitoringevaluationcomments" #dbo.organisationmonitoringevaluationcomments.csv
    _description = "Organisation M&E Comments"
    _order = "create_date desc"

    organisation_id = fields.Many2one('inseta.organisation')
    comment = fields.Text()
    metype_id = fields.Char()
    legacy_system_id = fields.Integer(string='Legacy System ID')

class InsetaOrganisationDocument(models.Model):
    _name = "inseta.organisationdocuments" #dbo.organisationdocuments.csv
    _description = "Organisation Documents"
    _rec_name = "documentrelates_id"

    organisation_id = fields.Many2one('inseta.organisation')
    documentrelates_id = fields.Many2one('res.crmdocumentrelates', 'Document Relates to')
    comment = fields.Text()

    file = fields.Binary(string="Select File", required=True)
    file_name = fields.Char("File Name")
    legacy_filepath = fields.Char()
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

    def unlink(self):
        for rec in self:
            if rec.organisation_id.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You can not delete a document for an approved/rejected organisation'))
        return super(InsetaOrganisationDocument, self).unlink()

class InsetaOrganisationComment(models.Model):
    _name = "inseta.organisationcomments" #dbo.organisationcomments.csv
    _description = "Organisation Comments"
    _order = "create_date desc"

    organisation_id = fields.Many2one('inseta.organisation')
    comment = fields.Text()
    legacy_system_id = fields.Integer(string='Legacy System ID')

class InsetaOrganisationBankingDetails(models.Model):
    _name = "inseta.organisationbankingdetails"
    _description = "Organisation Banking Details"
    _order = "create_date desc"

    organisation_id = fields.Many2one('inseta.organisation')
    accountholder = fields.Char()
    bank_id = fields.Many2one('inseta.bank')
    branchname = fields.Char(string='Branch Name')
    branchcode = fields.Char(string='Branch Code')
    accounttype_id = fields.Many2one('res.accounttype')
    accountnumber = fields.Char()
    verification_status = fields.Selection([
        ('Verified','Verified'),
        ('Not Verified', 'Not Verified')
    ], default="Not Verified")
    confirm = fields.Boolean('I hereby confirm that the following information submitted is complete, accurate and not missleading')

    @api.onchange('organisation_id')
    def _onchange_organisation_id(self):
        if self.organisation_id:
            self.accountholder = self.organisation_id.name

class InsetaOrganisationTrainingCommittee(models.Model):
    _name = "inseta.organisation.training.committee"
    _description = "Organisation Training Committee"
    _order = "create_date desc"

    organisation_id = fields.Many2one('inseta.organisation')
    title = fields.Many2one('res.partner.title', 'Title')
    first_name = fields.Char()
    last_name = fields.Char()
    initials = fields.Char()
    member_type = fields.Selection([
        ('Primary SDF', 'Primary SDF'),
        ('Secondary SDF', 'Secondary SDF'),
        ('HR', 'HR Manager / Officer'),
        ('Employee Representative', 'Employee Representative'),
        ('Labour', 'Labour Representative'),
        ('Senior Financial Representative', 'Senior Financial Representative'),
        ('Senior Organisation Representative',
         'Senior Organisation Representative'),
        ('Other', 'Other'), ], string="SDF Role")
    designation_id = fields.Many2one('res.designation', 'Designation')
    designation_desc = fields.Char('Designation Description')
    phone = fields.Char()
    fax_number = fields.Char()
    mobile = fields.Char()
    email = fields.Char()
    name_of_union = fields.Char()
    position_in_union = fields.Char()
    confirm = fields.Boolean('I hereby confirm that the following information submitted is complete, accurate and not missleading')
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean(default=True)

    @api.onchange('first_name')
    def _onchange_first_name(self):
        if self.first_name:
            self.initials = self.first_name[:1]

class OrganisationUpdate(models.Model):
    """
            Update Levy payer organisation by importing DHET employer file.
            If an employer with same SDL no exists, update her record, if not, create a new
    """
    _name = "inseta.levypayer.organisation.update"
    _description = "Levy Payer Organisation Update"
    _order = "id desc"
    
    name = fields.Char()
    file = fields.Binary(string="Select File", required=True)
    file_name = fields.Char("File Name")
    organisation_ids = fields.One2many(
        'inseta.organisation', 
        'employer_update_id', 
        string='Organisations',
        domain = [('state','in',('draft',))]
    )
    employer_update_count = fields.Integer(compute="_compute_employer_update_count")
    date_imported = fields.Date(default=fields.Date.today())

    @api.depends('organisation_ids')
    def _compute_employer_update_count(self):
        for rec in self:
            rec.employer_update_count = self.env['inseta.organisation'].search_count(
                [('employer_update_id', '=', self.id)])

    @api.constrains('file')
    def _check_file(self):
        ext = str(self.file_name.split(".")[1])
        if ext and ext not in ('SDL', 'sdl'):
                raise ValidationError("You can only upload files with .SDL extension")

# --------------------------------------------
# ORM Methods override
# --------------------------------------------
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('dhet.employer.update.code')
        vals['name'] = sequence or '/'
        return super(OrganisationUpdate, self).create(vals)

    # def write(self, vals):
    #     return super(OrganisationUpdate, self).write(vals)

class InterSetaTransfer(models.Model):
    """dbo.organisationist.csv
    dbo.lkpistchangereason.csv
    dbo.lkpisttransferstatus.csv
    dbo.lkpisttransfertype.csv
    dbo.lkpistuploadtype.csv
    """
    _name = "inseta.organisation.ist"
    _description = "Organisation Inter SETA transfer"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def _get_default_seta(self):
        seta_data = self.env['res.seta'].search(
            [('seta_id', '=', '13')], limit=1)
        return seta_data and seta_data.id or False

    name = fields.Char()
    state = fields.Selection([
            ('draft', 'Draft'),
            ('rework', 'Rework'),

            ('pending_approval','Pending Approval'),
            ('approve', 'Approved'), 
            ('reject', 'Rejected'),
        ],
        default="draft",
        index=True
    )
    organisation_id = fields.Many2one('inseta.organisation', 'Organisation')
    transfer_type = fields.Selection([ #dbo.lkpisttransfertype.csv
        ('transfer_in', 'Transfer in'), #legacy ID => 1
        ('transfer_out', 'Transfer Out'), #legacy ID => 2
    ])
    transferstatus_id = fields.Many2one('res.isttransferstatus', 'Transfer Status')
    date_seta_receivedapplication = fields.Date('Date received')
    date_applicationsubmitted = fields.Date('Date Submitted')
    date_organisationsignedist = fields.Date('Date Signed')
    date_advisementlettersent =  fields.Date('Date Advertisement Letter Sent')
    requestingperson_titleid = fields.Many2one('res.partner.title', 'Title')
    requestingperson_name = fields.Char('Requesting Person Name')
    requestingperson_surname = fields.Char('Surname')
    requestingperson_capacity = fields.Char('Designation')
    phone = fields.Char() #telephonenumber
    faxnumber = fields.Char()
    email = fields.Char()
    current_seta_id = fields.Many2one('res.seta', 'Current SETA', default=_get_default_seta)
    new_seta_id = fields.Many2one('res.seta', 'New SETA')
    transfer_motivation = fields.Char()
    new_sic_code_id = fields.Many2one('res.sic.code', string='New SIC Code')
    followup_comment = fields.Text()
    changereason_id = fields.Many2one('res.istchangereason','Change Reason')

    approved_date = fields.Date('Approval Date', readonly=True)
    approved_by = fields.Many2one('res.users')
    rejected_date = fields.Datetime()
    rejected_by = fields.Many2one('res.users')
    rework_date = fields.Date('Rework Date', help="Date Skills Admin Requested the Rework")
    reworked_date = fields.Date('Reworked Date', help="Date SDF Sumbitted the Rework")
    rework_expiration_date = fields.Date('Rework Expiration Date', compute="_compute_rework_expiration", store=True)
    rework_comment = fields.Text()

    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            rec.rework_expiration_date = False
            if rec.rework_date:
                rec.rework_expiration_date = date_utils.add(rec.rework_date, days=10)

# --------------------------------------------
# ORM Methods override
# --------------------------------------------
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('dhet.interseta.number')
        vals['name'] = sequence or '/'
        return super(InterSetaTransfer, self).create(vals)

# --------------------------------------------
# Business Logic
# --------------------------------------------

    def rework_registration(self, comment):
        """Skill admin query Registration and ask employer to rework.
        This method is called from the rework wizard

        Args:
            comment (str): Reason for rework
        """
        #if Skills Manager, reworks a registration, worklow to sdf specialist
        self.write({
            'state': 'rework', 
            'rework_comment': comment, 
            'rework_date': fields.Date.today()
        })
        self.organisation_id.rework_registration(comment)

        # self.activity_update()


    def action_set_to_draft(self):
        self.state = 'draft'

    def action_approve(self):
        self.write({
            'state': 'approve', 
            'approved_date': fields.Date.today(),
            'approved_by': self.env.user.id,
        })
        self.organisation_id.action_approve()


    def action_reject(self):
        self.write({
            'state': 'reject', 
            'rejected_date': fields.Date.today(),
            'rejected_by': self.env.user.id,
        })
        self.organisation_id.action_reject()


    def action_print_approval_letter(self):
        return self.env.ref('inseta_skills.organisation_approval_letter_report').report_action(self)

    # def action_print_rejection_letter(self):
    #     return self.env.ref('inseta_skills.organisation_rejection_letter_report').report_action(self)

    def get_organisation_contact_email(self):
        emails = []
        if self.child_ids:
            emails = [str(contact.email) for contact in self.child_ids]
        return ",".join(emails) if emails else ''

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    # def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
    #     res = super(InterSetaTransfer, self)._message_auto_subscribe_followers(
    #         updated_values, subtype_ids)
    #     if updated_values.get('user_id'):
    #         user = self.env['res.users'].browse(
    #             updated_values['user_id'])
    #         if user:
    #             res.append(
    #                 (user.partner_id.id, subtype_ids, False))
    #     return res

    # def _message_post(self, template):
    #     """Wrapper method for message_post_with_template

    #     Args:
    #         template (str): email template
    #     """
    #     if template:
    #         self.message_post_with_template(
    #             template.id, composition_mode='comment',
    #             model='inseta.organisation.ist', res_id=self.id,
    #             email_layout_xmlid='mail.mail_notification_light',
    #         )

    # def activity_update(self):
    #     """Updates the chatter and send neccessary email to followers or respective groups
    #     """
    #     mail_template = False
    #     #Skills admin request rework, state chnages to rework, notify SDF and SDF Employer
    #     if self.state == 'rework':
    #         #schedule an activity for rework expiration for  SDF user
    #         self.activity_schedule(
    #             'inseta_skills.mail_act_employerupdate_rework',
    #             user_id=self.env.user.id,
    #             date_deadline=self.rework_expiration_date)
    #         mail_template = self.env.ref('inseta_skills.mail_template_notify_dhet_levyemployer_rework_sdf', raise_if_not_found=False)

    #     #unlink employer rework activity if rework is submitted
    #     self.filtered(lambda s: s.state in ('pending_approval','approve')).activity_unlink(['inseta_skills.mail_act_employerupdate_rework'])

    #     self._message_post(mail_template) #notify sdf




