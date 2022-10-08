# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from xlwt import easyxf
import datetime
import logging
from odoo.addons.inseta_dg.models.inseta_dgapplication import DG_STATES
_logger = logging.getLogger(__name__)

DG_STATES2 = [
    ('submit','Submitted'),
    ('pending_approval', 'Pending Evaluation'),
    ('pending_adjudication','Pending Adjudication'),
    ('pending_approval2', 'Pending CEO Approval'),
    ('approve','Approved'),
    ('reject','Rejected'),
]

class DgReportWizard(models.TransientModel):
    _name='wizard.dg.report'
    _description ="DG Report Wizard"

    name = fields.Char()
    report_name = fields.Char()
    print_time = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year')
    dgfundingwindow_id = fields.Many2one('inseta.dgfunding.window')
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with future.')

class DgReportLineWizard(models.TransientModel):
    _name='wizard.dg.report.line'
    _order = 'id'
    _description = 'DG Report Line'

    report_id = fields.Many2one('wizard.dg.report')
    date = fields.Date()
    report_type = fields.Char()
    sic_code_id = fields.Many2one('res.sic.code', string='SIC Code')
    sic_code_desc = fields.Char(
        'SIC Code Description', 
        compute="_compute_sic_code_desc"
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    sn = fields.Integer()
    state = fields.Char()
    legal_name = fields.Char() 
    organisation_id = fields.Many2one("inseta.organisation")
    sdl_no = fields.Char() 
    organisation_size_id = fields.Many2one('res.organisation.size','CompanySize')
    province_id = fields.Many2one(
        'res.country.state', 
        string='Physical Province', 
        domain=[('country_id.code', '=', 'ZA')]
    )
    province = fields.Char()
    submitted_date = fields.Datetime('Application Date')
    socio_economic_status_id = fields.Many2one(
        'res.socio.economic.status', 
        'Socio Economic Status',
    )
    fundingtype_id = fields.Many2one('res.fundingtype','SETA/Industry Funded')
    provider_id = fields.Many2one('inseta.provider','Provider') 

    provider_name = fields.Char()
    learnership_id = fields.Many2one('inseta.learner.programme', 'Learnership Title')
    learnership_code = fields.Char()
    start_date = fields.Date('Actuary')
    end_date = fields.Date('Completion Date')
    no_learners = fields.Integer('No. Learners')
    disabled = fields.Integer('No. Disabled')
    total_learners = fields.Integer("Total number applied for")
    firsttime_applicant = fields.Char()
    contact_person_name = fields.Char('Contact Firstname')
    contact_person_surname = fields.Char('Contact Surname')
    contact_person_email = fields.Char('Email Address')
    contact_person = fields.Char()

    curr_fy_no_employees = fields.Integer() 
    financial_year_id = fields.Many2one('res.financial.year')
    total_youth = fields.Integer()
    total_youth_recommended = fields.Integer()
    amount_youth_recommended = fields.Monetary()
    total_workers = fields.Integer() 
    total_workers_recommended = fields.Integer() 
    amount_workers_recommended = fields.Monetary()
    no_learners_rural = fields.Integer()  
    no_rural_recommended = fields.Integer() 
    amount_learners_rural_recommended  = fields.Monetary()
    no_disabled_rural = fields.Integer() 
    no_disabled_rural_recommended = fields.Integer() 
    amount_disabled_rural_recommended  = fields.Monetary()
    total_pwd = fields.Integer() 
    total_pwd_recommended = fields.Integer() 
    amount_pwd_recommended = fields.Monetary()
    total_itmatric = fields.Integer() 
    total_itmatric_recommended = fields.Integer() 
    amount_itmatric_recommended  = fields.Monetary()
    total_itdegree = fields.Integer() 
    total_itdegree_recommended  = fields.Integer() 
    amount_itdegree_recommended = fields.Monetary()
    total_skillsprogramme = fields.Integer() 
    total_skillsprogramme_recommended = fields.Integer() 
    amount_skillsprogramme_recommended = fields.Monetary()
    total_bursary_workers = fields.Integer() 
    total_bursary_workers_recommended = fields.Integer() 
    amount_bursary_workers_recommended = fields.Monetary()
    total_wiltvet = fields.Integer() 
    total_wiltvet_recommended = fields.Integer() 
    amount_wiltvet_recommended = fields.Monetary()
    total_unemployed = fields.Integer()
    total_amount_unemployed = fields.Monetary()
    total_employed = fields.Integer()
    total_amount_employed = fields.Monetary()
    total_recommended_employer = fields.Integer()
    dgec_comments = fields.Text()
    has_submitted_wspatr = fields.Char()
    is_fsca_compliant = fields.Char()
    comments = fields.Text()
    state = fields.Char()


    @api.depends('sic_code_id')
    def _compute_sic_code_desc(self):
        for rec in self:
            if rec.sic_code_id:
                rec.sic_code_desc = rec.sic_code_id.name
            else:
                rec.sic_code_desc = False

class DgReportFilter(models.TransientModel):
    _name = "wizard.dg.report.filter"
    _description ="DG Report Filter"

    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date

    report_type = fields.Selection(
        [
            ('DGEC', 'DGEC Recommendation'),
            ('all_learnership', 'All Learnership'),
        ],
    )

    financial_year_id = fields.Many2one('res.financial.year')
    dgfundingwindow_id = fields.Many2one(
        'inseta.dgfunding.window', 
        'Funding Window',
        domain="[('state','=','approve'),('financial_year_id','=',financial_year_id)]",
    )
    dgtype_id = fields.Many2one('res.dgtype', 'Programme type')
    state = fields.Selection(DG_STATES)
    state2 = fields.Selection(DG_STATES2)
    date_from = fields.Date(string='From Date',default=_get_from_date)
    date_to = fields.Date(string='To Date',default=datetime.date.today())
    report_name = fields.Char('Report Name')
    report_id = fields.Many2one('wizard.dg.report')

    def action_view_lines(self):
        self.ensure_one()
        self._compute_data()

        view = False
        if self.report_type == "DGEC":
            view = self.env.ref('inseta_dg.view_dgec_recommendation_line_tree')
        elif self.report_type == "all_learnership":
            view = self.env.ref("inseta_dg.view_all_learnership_tree")

        view_id = view and view.id or False
        context = dict(self._context or {})
        return {
            'name': self.report_id.name,
            'view_mode': 'tree,form',
            'views':[(view_id, 'tree'), (False, 'form')],
            'res_model': 'wizard.dg.report.line',
            'type': 'ir.actions.act_window',
            'domain': [('report_id', '=', self.report_id.id)],
            'target': 'current',
            'context':context,
        }

    
    def _get_report_name(self):
        name = ''
        report_type = self.report_type
        if report_type == 'DGEC':
            name = 'DGEC Recommendation'
        elif report_type == 'all_learnership':
            name = 'Learnerships'
        else:
            name="DG applications"
        return name

    def _pre_compute(self):
        lang_code = self.env.context.get('lang') or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format

        vals = {'report_name': self._get_report_name(),
                'name': self._get_report_name(),
                'print_time': '%s' % fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), fields.Datetime.now()).strftime(('%s %s') % (date_format, time_format)),
                'date_to': self.date_to if self.date_to else "2099-01-01",
                'date_from': self.date_from if self.date_from else "1970-01-01",
                'financial_year_id': self.financial_year_id.id
            }
        self.report_id = self.env['wizard.dg.report'].create(vals).id

    def _compute_data(self):
        self._pre_compute()
        if self.report_type == 'DGEC':
            # self._sql_organisations()
            self._sql_dgec_recommendation()
        elif self.report_type == 'all_learnership':
            self._sql_learnership_applications()
        self.refresh()


    def _sql_learnership_applications(self):
        """
            Employer Name	SDL Number	Application Date	Application Status	Socio Economic Status	SETA/Industry Funded	
            Province	Provider Name	Learnership Title	Learnership Code	actuary	Completion Date	Disabled	Able bodied	
            Total number applied for	First Time Applicant(Yes/No)	Contact Person	TelephoneNumber	Email Address	CompanySize						
        """
        query = """
        INSERT INTO wizard_dg_report_line
            (report_id, report_type, create_uid, create_date, date, financial_year_id, organisation_id, sdl_no, submitted_date, 
                state, socio_economic_status_id, fundingtype_id, province_id, provider_name, 
                learnership_id, learnership_code, start_date, end_date, disabled, no_learners, total_learners,
                firsttime_applicant, contact_person, contact_person_email, organisation_size_id
            )
		SELECT 
            %s AS report_id,
            %s AS report_type,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS date,
			application.financial_year_id, organisation.id AS organisation_id, organisation.sdl_no AS sdl_no,
            application.submitted_date as submitted_date, application.state as state,
            applicationdetail.socio_economic_status_id AS socio_economic_status_id, applicationdetail.fundingtype_id AS fundingtype_id,
            applicationdetail.province_id, 
            applicationdetail.provider_name,
            applicationdetail.learnership_id, applicationdetail.learnership_code, 
            applicationdetail.start_date, applicationdetail.end_date,
            applicationdetail.disabled, applicationdetail.no_learners, applicationdetail.total_learners,
            applicationdetail.firsttime_applicant, CONCAT(applicationdetail.contact_person_name, ' ', applicationdetail.contact_person_surname) AS contact_person,
            applicationdetail.contact_person_email, 
            organisation.organisation_size_id 
		FROM 
            inseta_dgapplicationdetails applicationdetail 
            LEFT JOIN inseta_dgapplication application ON application.id = applicationdetail.dgapplication_id
            LEFT JOIN inseta_organisation organisation ON application.organisation_id = organisation.id
		WHERE 
			application.financial_year_id = %s AND
            application.dgtype_code in ('LRN-Y','LRN-R','LRN-W')
        """
        self.state and (self.state,) or DG_STATES
        params = [
            self.report_id.id,
            self.report_type,
            self.env.uid,
            self.report_id.date_from,
            self.financial_year_id.id,
        ]
        _logger.info(f"QUERY {query}")
        self.env.cr.execute(query, tuple(params))

    def _sql_dgec_recommendation(self):
        """
        Generate DGEC recommendation sheet
        -- 			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-D' THEN applicationdetail.total_learners  END),0) AS total_pwd,
        -- 			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-D' THEN applicationdetail.no_learners_recommended END),0.00) AS total_pwd_recommended,
        -- 			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-D' THEN applicationdetail.amount_total_recommended END),0.00) AS amount_pwd_recommended,
        """

        query = """
        INSERT INTO wizard_dg_report_line
            (report_id, report_type, create_uid, create_date, date, sn, financial_year_id, legal_name, organisation_size_id, 
                sdl_no, province_id, curr_fy_no_employees,
                total_youth,total_youth_recommended,amount_youth_recommended,
                total_pwd,total_pwd_recommended,amount_pwd_recommended,
                total_workers, total_workers_recommended, amount_workers_recommended,
                no_learners_rural, no_rural_recommended,amount_learners_rural_recommended,
                no_disabled_rural, no_disabled_rural_recommended, amount_disabled_rural_recommended,
                total_itmatric,total_itmatric_recommended,amount_itmatric_recommended,
                total_itdegree,total_itdegree_recommended,  amount_itdegree_recommended,
                total_skillsprogramme, total_skillsprogramme_recommended, amount_skillsprogramme_recommended,
                total_bursary_workers, total_bursary_workers_recommended, amount_bursary_workers_recommended,
                total_wiltvet, total_wiltvet_recommended, amount_wiltvet_recommended,
                total_unemployed,total_amount_unemployed, total_employed, total_amount_employed, total_recommended_employer,
                dgec_comments, has_submitted_wspatr, is_fsca_compliant,comments, state
            )

		SELECT 
            %s AS report_id,
            %s AS report_type,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS date,
            row_number() over (order by organisation.id) as sn,
			application.financial_year_id AS financial_year_id, organisation.legal_name AS legal_name, organisation.organisation_size_id AS organisation_size_id, 
            organisation.sdl_no AS sdl_no, partner.state_id AS province_id, organisation.current_fy_numberof_employees AS curr_fy_no_employees,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-D') THEN applicationdetail.no_learners END),0) AS no_learners_youth,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-D') THEN applicationdetail.no_learners_recommended END),0) AS no_learners_youth_recommended, 
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-D') THEN applicationdetail.amount_learners_recommended END),0.00) AS amount_learners_youth_recommended, 
			
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-D') THEN applicationdetail.disabled END),0) AS no_disabled_youth,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-D') THEN applicationdetail.disabled_recommended END),0) AS no_disabled_youth_recommended, 
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-D') THEN applicationdetail.amount_disabled_recommended END),0.00) AS amount_disabled_youth_recommended, 
			
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-W' THEN applicationdetail.total_learners END),0) AS total_workers,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-W' THEN applicationdetail.no_learners_recommended END),0) AS total_workers_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-W' THEN applicationdetail.amount_total_recommended END),0.00) AS amount_workers_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.no_learners END),0) AS no_learners_rural,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.no_learners_recommended END),0) AS no_rural_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.amount_learners_recommended END),0.00) AS amount_learners_rural_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.disabled END),0) AS no_disabled_rural,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.disabled_recommended END),0) AS no_disabled_rural_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.amount_disabled_recommended END),0.00) AS amount_disabled_rural_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-MATRIC' THEN applicationdetail.total_learners  END),0) AS total_itmatric,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-MATRIC' THEN applicationdetail.no_learners_recommended END),0) AS total_itmatric_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-MATRIC' THEN applicationdetail.amount_total_recommended END),0.00) AS amount_itmatric_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-DEGREE' THEN applicationdetail.total_learners END),0) AS total_itdegree,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-DEGREE' THEN applicationdetail.no_learners_recommended END),0) AS total_itdegree_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-DEGREE' THEN applicationdetail.amount_total_recommended END),0.00) AS amount_itdegree_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'SP' THEN applicationdetail.total_learners  END),0) AS total_skillsprogramme,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'SP' THEN applicationdetail.no_learners_recommended END),0) AS total_skillsprogramme_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'SP' THEN applicationdetail.amount_total_recommended END),0.00) AS amount_skillsprogramme_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'BUR' THEN applicationdetail.total_learners  END),0) AS total_bursary_workers,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'BUR' THEN applicationdetail.no_learners_recommended END),0) AS total_bursary_workers_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'BUR' THEN applicationdetail.amount_total_recommended END),0.00) AS amount_bursary_workers_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'WIL' THEN applicationdetail.total_learners  END),0) AS total_wiltvet,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'WIL' THEN applicationdetail.no_learners_recommended END),0) AS total_wiltvet_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'WIL' THEN applicationdetail.amount_total_recommended END),0) AS amount_wiltvet_recommended,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-R','LRN-W','LRN-D') and applicationdetail.socio_economic_status_id = 2  THEN applicationdetail.no_learners_recommended END),0) + 
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-R','LRN-W','LRN-D') and applicationdetail.socio_economic_status_id = 2  THEN applicationdetail.disabled_recommended END),0)
			AS total_unemployed,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-R','LRN-W','LRN-D') and applicationdetail.socio_economic_status_id = 2  THEN applicationdetail.amount_total_recommended END),0.00) + 
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-Y','LRN-R','LRN-W','LRN-D') and applicationdetail.socio_economic_status_id = 2  THEN applicationdetail.amount_disabled_recommended END),0.00) 
			AS total_amount_unemployed,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-W','BUR','SP','IT-MATRIC','IT-DEGREE') THEN applicationdetail.no_learners_recommended END),0) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-W','BUR','SP','IT-MATRIC','IT-DEGREE') THEN applicationdetail.disabled_recommended END),0)
			AS total_employed,
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-W','BUR','SP','IT-MATRIC','IT-DEGREE') THEN applicationdetail.amount_total_recommended END),0.00) + 
			COALESCE(SUM(CASE WHEN dgtype.saqacode in ('LRN-W','BUR','SP','IT-MATRIC','IT-DEGREE') THEN applicationdetail.amount_disabled_recommended END),0.00)
			AS total_amount_employed,
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-Y' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-W' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-R' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'LRN-D' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-MATRIC' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'IT-DEGREE' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'SP' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'BUR' THEN applicationdetail.amount_total_recommended END),0.00) +
			COALESCE(SUM(CASE WHEN dgtype.saqacode = 'WIL' THEN applicationdetail.amount_total_recommended END),0)
			AS total_recommended_employer,
			null as dgec_comments,
			CASE WHEN 
				(SELECT id from inseta_wspatr wspatr 
				WHERE wspatr.organisation_id = organisation.id AND 
				wspatr.financial_year_id = application.financial_year_id AND
				wspatr.state = 'approve')
			  	is not null THEN 'YES' ELSE 'NO' END AS has_submitted_wspatr,
			null AS is_fsca_compliant,
			null AS comments,
			application.state AS state
		FROM 
			inseta_dgapplication application
        LEFT JOIN inseta_organisation organisation ON application.organisation_id = organisation.id
		LEFT JOIN res_partner partner ON partner.id = organisation.partner_id
		LEFT JOIN res_dgtype dgtype ON dgtype.id = application.dgtype_id
        LEFT JOIN inseta_dgapplicationdetails applicationdetail ON application.id = applicationdetail.dgapplication_id
		WHERE 
			application.financial_year_id = %s AND
			application.state in (%s)		
		GROUP BY
			organisation.legal_name,
			organisation.id,
			partner.state_id,
			application.financial_year_id,
			application.state
        """
        fy = self.env['res.financial.year']._get_current_financial_year()
        year = fy and fy.date_from.year or fields.Date.today().year
        fy_start = fy and fy.date_from or False
        fy_end = fy and fy.date_to or False
        state = self.state or self.state2
        params = [
            # SELECT
            self.report_id.id,
            self.report_type,
            self.env.uid,
            self.report_id.date_from,
            self.financial_year_id.id,
            state
        ]
        #_logger.info(f"QUERY {query}")
        self.env.cr.execute(query, tuple(params))


