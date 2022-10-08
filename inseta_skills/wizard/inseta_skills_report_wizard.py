# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import xlwt
import io
import base64
import json
from xlwt import easyxf
import datetime
import logging
_logger = logging.getLogger(__name__)


class SkillsReportWizard(models.TransientModel):
    _name='wizard.skills.report'
    _description ="Skills Report Wizard"

    name = fields.Char()
    report_name = fields.Char()
    print_time = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year')
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with future.')

class SkillsReportLineWizard(models.TransientModel):
    _name='wizard.skills.report.line'
    _order = 'id'
    _description = 'Skills Report Line'

    report_id = fields.Many2one('wizard.skills.report')
    financial_year_id = fields.Many2one('res.financial.year')

    date = fields.Date()
    report_type = fields.Char()
    year = fields.Char()
    trade_name = fields.Char() 
    legal_name = fields.Char() 
    sdl_no = fields.Char()
    dhet_sdl_no = fields.Char() 
    parent_trade_name = fields.Char()  
    parent_legal_name = fields.Char()
    parent_sdl_no = fields.Char() 
    parent_dhet_sdl_no = fields.Char()
    bee_status_id = fields.Many2one('res.bee.status', 'Bee Status')

    total_annual_payroll = fields.Float()
    no_employees = fields.Integer() 
    no_employees_curr_fy = fields.Integer() 

    phone = fields.Char()  
    fax_number = fields.Char()  
    org_reg_no = fields.Char('Registration No')  
    sic_code_id = fields.Many2one('res.sic.code', string='SIC Code')
    sic_code_desc = fields.Char(
        'SIC Code Description', 
        compute="_compute_sic_code_desc"
    )
    physical_address1  = fields.Char()   
    physical_address2  = fields.Char()   
    physical_address3 = fields.Char() 
    physical_code = fields.Char()    
    physical_municipality_id = fields.Many2one('res.municipality')
    physical_urban_rural = fields.Char()
    physical_province_id = fields.Many2one('res.country.state')
    incorrect_seta = fields.Char()  
    legal_status_id = fields.Many2one('res.legal.status', 'Legal Status')
    interested_in_communication = fields.Char() 
    financial_year_start = fields.Char() 
    financial_year_end = fields.Char()  
    employees_by_date = fields.Integer() 
    wsp_id = fields.Many2one('inseta.wspatr')
    wsp_year = fields.Char() 
    wsp_create_date = fields.Datetime() 
    wsp_status = fields.Char() 
    wsp_form_type = fields.Char('Type')
    wsp_due_date = fields.Date() 
    wsp_submitted_date = fields.Datetime()
    wsp_submitted_by = fields.Many2one('res.users')
    wsp_approved_date = fields.Datetime()
    wsp_approved_by = fields.Many2one('res.users')
    wsp_rejected_date = fields.Datetime()
    wsp_rejected_by = fields.Many2one('res.users')
    wsp_no_employees_prev_wsp = fields.Integer(
        "Number of Employees (previous WSP submitted)",
        compute="_compute_no_employees_prev_wsp",
    )
    org_contact_title = fields.Many2one('res.partner.title')  
    org_contact_firstname = fields.Char() 
    org_contact_surname = fields.Char() 
    org_contact_initials = fields.Char() 
    org_contact_jobtitle = fields.Char()
    org_contact_phone = fields.Char() 
    org_contact_faxnumber = fields.Char()
    org_contact_email = fields.Char() 
    org_contact_cell = fields.Char() 
    org_contact_address1 = fields.Char()
    org_contact_address2 = fields.Char() 
    org_contact_city_id = fields.Many2one('res.city') 
    org_contact_postal_code = fields.Char()
    org_contact_region = fields.Char() 
    apr = fields.Float() 
    may = fields.Float()  
    jun = fields.Float()  
    jul = fields.Float() 
    aug = fields.Float()  
    sep = fields.Float()  
    oct  = fields.Float() 
    nov  = fields.Float() 
    dec  = fields.Float()  
    jan = fields.Float()  
    feb = fields.Float() 
    mar = fields.Float() 	
    total = fields.Float() 
    planning_grant = fields.Float()  
    implementation_grant = fields.Float()  
    discretionary_grant = fields.Float()  
    project_grant = fields.Float()
    efacts_contact = fields.Float()  
    efacts_address = fields.Char()  
    dol_status = fields.Char()  
    linked_organisation_type = fields.Char()  
    emp_per_profile = fields.Char()  
    inter_seta_transfer = fields.Char() 
    org_id = fields.Char()  
    tmp_org_report_id = fields.Char()  
    org_size_id = fields.Many2one('res.organisation.size')
    org_registered_by = fields.Many2one('res.users')
    org_registered_date = fields.Datetime()
    #sdf
    sdf_acting_for_employer  = fields.Char() 
    appointment_procedure_id = fields.Many2one('res.sdf.appointment.procedure', 'SDF appointment Method') 
    sdf_comments = fields.Char() 
    sdf_function_id = fields.Many2one('res.sdf.function')
    sdf_title = fields.Many2one('res.partner.title') 
    sdf_firstname = fields.Char()    
    sdf_middlename = fields.Char()    

    sdf_surname = fields.Char()    
    sdf_initials = fields.Char()    
    sdf_idno = fields.Char()   
    sdf_alternate_idno = fields.Char()    
    sdf_alternateid_type_id = fields.Many2one('res.alternate.id.type', string='Alternate ID TYPE')
    sdf_gender_id = fields.Many2one('res.gender', 'Gender')
    sdf_equity_id = fields.Many2one('res.equity', 'Equity')
    sdf_highest_edu_level_id  = fields.Many2one('res.education.level')
    sdf_highest_edu_desc = fields.Text()
    sdf_current_occupation = fields.Char()
    sdf_occupation_experience = fields.Char()
    sdf_occupation_years = fields.Char() 
    sdf_phone = fields.Char() 
    sdf_cellphone = fields.Char() 
    sdf_faxnumber = fields.Char() 
    sdf_email = fields.Char()
    sdf_postal_address1 = fields.Char()
    sdf_postal_address2 = fields.Char() 
    sdf_postal_address3 = fields.Char() 
    sdf_postal_municipality_id = fields.Char() 
    sdf_postal_code = fields.Char() 
    sdf_postal_province_id = fields.Many2one('res.country.state') 
    sdf_physical_province_id = fields.Many2one('res.country.state')
    sdf_status = fields.Char()
    #all sdf
    sdf_birth_date = fields.Date(string='Birth Date')
    sdf_disability_id = fields.Many2one('res.disability', string="Disability Status")
    home_language_id = fields.Many2one('res.lang', string='Home Language',)
    nationality_id = fields.Many2one('res.nationality', string='Nationality')
    citizen_resident_status_id = fields.Many2one('res.citizen.status', string='Citizen Status')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status')
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    sdf_org_state = fields.Char()
    sdf_role = fields.Char()
    sdf_reregistration_status = fields.Char()
    has_requested_sdftraining = fields.Char()

    @api.depends('wsp_id')
    def _compute_no_employees_prev_wsp(self):
        for rec in self:
            if rec.wsp_id:
                rec.wsp_no_employees_prev_wsp = rec.wsp_id._get_previous_wsp_no_employees()
            else:
                rec.wsp_no_employees_prev_wsp = 0

    @api.depends('sic_code_id')
    def _compute_sic_code_desc(self):
        for rec in self:
            rec.sic_code_desc = False
            if rec.sic_code_id:
                rec.sic_code_desc = rec.sic_code_id.name

class SkillsReportFilter(models.TransientModel):
    _name = "wizard.skills.report.filter"
    _description ="Claims Report Filter"

    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date

    report_type = fields.Selection(
        [
            ('organisation', 'Organisation Huge File'),
            ('sdf', 'All SDFs'),
            ('wspatr_approval_list','WSP/ATR Approval List'),
            # ('wspatr', 'All WSP/ATRs'),
        ],
    )


    financial_year_id = fields.Many2one('res.financial.year')
    date_from = fields.Date(string='From Date',default=_get_from_date)
    date_to = fields.Date(string='To Date',default=datetime.date.today())
    report_name = fields.Char('Report Name')
    report_id = fields.Many2one('wizard.skills.report')

    def action_view_lines(self):
        self.ensure_one()
        self._compute_data()

        view = False
        if self.report_type == "organisation":
            view = self.env.ref('inseta_skills.view_organisation_report_line_tree')
        if self.report_type == "sdf":
            view = self.env.ref('inseta_skills.view_sdf_report_line_tree')

        if self.report_type == "wspatr_approval_list":
            view = self.env.ref('inseta_skills.view_organisation_report_line_tree_wsp_approval_list')

        if self.report_type == "wspatr":
            view = self.env.ref('inseta_skills.view_organisation_report_line_tree_wsp')



        view_id = view and view.id or False
        context = dict(self._context or {})
        #'view_mode': 'tree,form',
        #'views': [(False, 'tree'), (False, 'form')],
        return {
            'name': self.report_id.name,
            'view_mode': 'tree,form',
            'views':[(view_id, 'tree'), (False, 'form')],
            'res_model': 'wizard.skills.report.line',
            'type': 'ir.actions.act_window',
            'domain': [('report_id', '=', self.report_id.id)],
            'target': 'current',
            'context':context,
        }

    # def print_excel_report(self):
    #     self.ensure_one()
    #     self._compute_data()
    #     if self.report_type == "organisation":
    #         print(self.env.ref('inseta_skills.action_organisation_xlxs').report_action(self))
    #         return self.env.ref('inseta_skills.action_organisation_xlxs').report_action(self)   

    
    def _get_report_name(self):
        name = ''
        report_type = self.report_type
        if report_type == 'organisation':
            name = 'All Organisations'
        elif report_type == 'sdf':
            name = 'All SDFs'
        elif report_type == 'wspatr':
            name = 'All WSPATR'
        elif report_type == 'wspatr_approval_list':
            name = 'WSPATR Approval List'
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
        self.report_id = self.env['wizard.skills.report'].create(vals).id

    def _compute_data(self):
        self._pre_compute()
        if self.report_type == 'organisation':
            self._sql_organisations()
        
        if self.report_type == 'sdf':
            self._sql_sdfs()

        if self.report_type == 'wspatr':
            self._sql_wspatr()

        if self.report_type == 'wspatr_approval_list':
            self._sql_wspatr()
        self.refresh()

    def _sql_wspatr(self):
        """
        LegalName	TradeName	Province	SDLNumber	DHETSDLNumber	OrganisationSize	
        ParentSDLNumber	ParentDHETSDLNumber	FinancialYear	WSPStatus	Type	DueDate	CreatedDate	
        SubmittedDate	SubmittedBy	ApprovedDate	ApprovedBy	RejectedDate	RejectedBy	
        SDFFirstName	SDFSurname	SDFIDNumber	SDFCellPhoneNumber	SDFTelephoneNumber	SDFEMail	Number of Employees (Current FY)	
        Number of Employees (previous WSP submitted)	

            WITH organisation as(
            select   organisation.legal_name,  
                        organisation.trade_name,
                        --organisation_partner.physical_province_id,
                        organisation.sdl_no,  
                        organisation.dhet_sdl_no,
                        organisation.organisation_size_id,
                        organisation.id organisation_id ,
                        null childorganisation_id,
                        'Parent' orgtype,
                        partner_id 
            from inseta_organisation organisation
            where   exists (select 1 
                        from inseta_organisationlinkages parent_org 
                        where (organisation_id = organisation.id ))

            UNION ALL
            select organisation.legal_name,  
                        organisation.trade_name,
                        --organisation_partner.physical_province_id,
                        organisation.sdl_no,  
                        organisation.dhet_sdl_no,
                        organisation.organisation_size_id,
                        organisation_id,
                        childorganisation_id,
                        'Child',
                        organisation.partner_id 
                    
            from inseta_organisationlinkages child_org
            -- organisation
            --LEFT JOIN inseta_organisationlinkages parent_org ON org.id = parent_org.organisation_id
            LEFT JOIN  inseta_organisation organisation  ON  
            (organisation.id = child_org.childorganisation_id
            --AND child_org.active =  'true'
            )

                UNION ALL
            select   organisation.legal_name,  
                        organisation.trade_name,
                        --organisation_partner.physical_province_id,
                        organisation.sdl_no,  
                        organisation.dhet_sdl_no,
                        organisation.organisation_size_id,
                        organisation.id ,
                        null childorganisation_id,
                        'NonParentChild' orgtype,
                        partner_id
            from inseta_organisation organisation
            where 1=1
            and active =  'true'
            and not  exists (select 1 
                        from inseta_organisationlinkages parent_org 
                        where (organisation_id = organisation.id
                            OR childorganisation_id = organisation.id )		  )	

            )



            select      org.*,
                        wsp.id,
                        wsp.financial_year_id,
                        wsp.state,
                        wsp.form_type,
                        wsp.due_date,
                        wsp.create_date,
                        wsp.submitted_date,
                        wsp.submitted_by,
                        wsp.approved_date,
                        wsp.approved_by,
                        wsp.rejected_date,
                        wsp.rejected_by
                        
                        

            from 
            inseta_wspatr wsp
            LEFT JOIN organisation org  ON org.organisation_id =  wsp.organisation_id
        """
        query = """
        INSERT INTO wizard_skills_report_line
            (report_id, report_type, create_uid, create_date, date, year, legal_name, trade_name, 
            physical_province_id,sdl_no,dhet_sdl_no,org_size_id, parent_sdl_no,parent_dhet_sdl_no, 
            wsp_id, financial_year_id, wsp_status, wsp_form_type, wsp_due_date, wsp_create_date, wsp_submitted_date,
            wsp_submitted_by,wsp_approved_date,wsp_approved_by,wsp_rejected_date,wsp_rejected_by,
            sdf_firstname,sdf_surname,sdf_idno,sdf_cellphone,sdf_phone,sdf_email,no_employees_curr_fy)
        SELECT
            %s AS report_id,
            %s AS report_type,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS date,
            %s As Year,
            organisation.legal_name,  
            organisation.trade_name,
            organisation_partner.physical_province_id,
            organisation.sdl_no,  
            organisation.dhet_sdl_no,
            organisation.organisation_size_id,
			(SELECT parentorg.sdl_no from inseta_organisationlinkages linkage 
			 	LEFT JOIN inseta_organisation parentorg on parentorg.id = linkage.organisation_id
			 	WHERE organisation.id = linkage.childorganisation_id limit 1) AS parent_sdl_no,
			(SELECT parentorg.dhet_sdl_no from inseta_organisationlinkages linkage 
			 	LEFT JOIN inseta_organisation parentorg on parentorg.id = linkage.organisation_id
			 	WHERE organisation.id = linkage.childorganisation_id limit 1) AS parent_dhet_sdl_no,
            wsp.id,
            wsp.financial_year_id,
            wsp.state,
            wsp.form_type,
            wsp.due_date,
            wsp.create_date,
            wsp.submitted_date,
            wsp.submitted_by,
            wsp.approved_date,
            wsp.approved_by,
            wsp.rejected_date,
            wsp.rejected_by,
            sdf_partner.first_name,
            sdf_partner.last_name,
            sdf_partner.id_no,
            sdf_partner.mobile,
            sdf_partner.phone,
            sdf_partner.email,
            organisation.current_fy_numberof_employees
        FROM
            inseta_wspatr wsp
            LEFT JOIN inseta_organisation organisation ON wsp.organisation_id = organisation.id
            LEFT JOIN res_partner organisation_partner ON organisation.partner_id = organisation_partner.id
            LEFT JOIN inseta_sdf sdf ON wsp.sdf_id = sdf.id
            LEFT JOIN res_partner sdf_partner ON sdf.partner_id = sdf_partner.id
            WHERE wsp.financial_year_id = %s
            ORDER BY organisation.legal_name
        """
        fy = self.env['res.financial.year']._get_current_financial_year()
        year = fy and fy.date_from.year or fields.Date.today().year
        fy_start = fy and fy.date_from or False
        fy_end = fy and fy.date_to or False
        params = [
            self.report_id.id,
            self.report_type,
            self.env.uid,
            self.report_id.date_from,
            year,
            self.financial_year_id.id
        ]
        #_logger.info(f"approval list => {query}")
        self.env.cr.execute(query, tuple(params))


    def _sql_sdfs(self):
        """ TODO: Complete the implementation 
        """
        query = """
        INSERT INTO wizard_skills_report_line
            (report_id, report_type, create_uid, create_date, date, year, sdf_title, sdf_firstname, sdf_middlename, sdf_surname, sdf_initials,
            sdf_idno,sdf_alternateid_type_id,sdf_birth_date,sdf_gender_id,sdf_equity_id,sdf_disability_id, home_language_id, nationality_id,
            citizen_resident_status_id,socio_economic_status_id, sdf_physical_province_id, sdf_phone, sdf_cellphone, sdf_faxnumber, 
            sdf_email, sdf_highest_edu_level_id, sdf_highest_edu_desc, sdf_current_occupation, sdf_occupation_years, sdf_occupation_experience,
            legal_name, trade_name, sdl_no, start_date, end_date, sdf_org_state, sdf_role, sdf_reregistration_status, has_requested_sdftraining )
        SELECT
            %s AS report_id,
            %s AS report_type,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS date,
            %s As Year,
            partner.title, 
            partner.first_name, 
            partner.middle_name,
            partner.last_name,
            partner.initials,
            partner.id_no,
            partner.alternateid_type_id,
            partner.birth_date,
            partner.gender_id,
            partner.equity_id,
            partner.disability_id,
            partner.home_language_id,
            partner.nationality_id,
            partner.citizen_resident_status_id,
            partner.socio_economic_status_id,
            partner.physical_province_id,
            partner.phone,
            partner.mobile,
            partner.fax_number,
            partner.email,
            sdf.highest_edu_level_id,
            sdf.highest_edu_desc,
            sdf.current_occupation,
            sdf.occupation_years,
            sdf.occupation_experience,
            organisation.legal_name,
            organisation.trade_name,
            organisation.sdl_no,
            sdf_organisation.start_date,
            sdf_organisation.end_date,
            sdf_organisation.state,
            sdf_organisation.sdf_role,
            null AS sdf_reregistration_status,
            CASE 
                WHEN (sdf.has_requested_sdftraining = true) THEN 'Yes'
                ELSE 'No'
            END AS has_requested_sdftraining
            
        FROM
            inseta_sdf sdf
            LEFT JOIN res_partner partner ON sdf.partner_id = partner.id
            LEFT JOIN inseta_sdf_organisation sdf_organisation on sdf.id = sdf_organisation.sdf_id
            LEFT JOIN inseta_organisation organisation on organisation.id = sdf_organisation.organisation_id
        """
        fy = self.env['res.financial.year']._get_current_financial_year()
        year = fy and fy.date_from.year or fields.Date.today().year
        fy_start = fy and fy.date_from or False
        fy_end = fy and fy.date_to or False
        params = [
            self.report_id.id,
            self.report_type,
            self.env.uid,
            self.report_id.date_from,
            year
        ]
        self.env.cr.execute(query, tuple(params))
        

    
    def _sql_organisations(self):
        """
            Year	TradeName	LegalName	SDLNumber	Parent_TradeName	Parent_LegalName	Parent_SDLNumber	
            BEEStatus	TotalAnnualPayroll	NumberOfEmployees	PhoneNumber	FaxNumber	OrganisationRegistrationNumber	
            SICCode	SICCode_Description	PhysicalAddress1	PhysicalAddress2	PhysicalAddress3	
            PhysicalMunicipality	PhysicalCode	PhysicalUrbanRural	PhysicalProvince	PostalAddressLine1	PostalAddressLine2	
            PostalAddressLine3	PostalMunicipality	PostalCode	PostalUrbanRural	PostalProvince	Incorrect_SETA	
            LegalStatus	Interested_In_Communication	FinancialYearStart	FinancialYearEnd	EmployeesByDate	SDF_Acting_for_Employer	
            SDF_Appointment_Method	SDF_Comments	SDF_Function	SDF_Title	SDF_Firstname	SDF_Surname	SDF_Initials	SDF_IDNo	
            SDF_Alternate_IDNo	SDF_Alternate_ID_Type	SDF_Gender	SDF_Ethnic_Group	SDF_HighestEducation	SDF_CurrentOccupation	
            SDF_Occupation_Experience	SDF_YearsInOccupation	SDF_TelephoneNumber	SDF_CellPhoneNumber	SDF_FaxNumber	SDF_EMail	
            SDF_PostalAddressLine1	SDF_PostalAddressLine2	SDF_PostalAddressLine3	SDF_PostalMunicipality	SDF_PostalCode	SDF_PostalProvince	
            SDF_PhysicalProvince	SDF_Status	Sequence	PrimaryInd	WSPYear	WSP_CreatedDate	WSPStatus	WSP_DueDate	Org_Cnt_Title	Org_Cnt_First_name	
            Org_Cnt_Surname	Org_Cnt_Initials	Org_Cnt_Job_Title	Org_Cnt_Phone	Org_Cnt_Fax	Org_Cnt_E_Mail	Org_Cnt_Cell	Org_Cnt_Address_Line_1	
            Org_Cnt_Address_Line_2	Org_Cnt_City	Org_Cnt_Postal_Code	Org_Cnt_Region	Apr	May	Jun	Jul	Aug	Sep	Oct	Nov	Dec	Jan	Feb	Mar	Total	
            Planning_Grant	Implementation_Grant	Discretionary_Grant	Project_Grant	Efacts_Contact	Efacts_Address	DOL_Status	
            Linked_Organisation_Type	Emp_Per_Profile	Inter_Seta_Transfer	OrganisationID	tmpOrganisationReportID	OrganisationSize	
            CompanyRegisteredBy	CompanyRegisteredDate							
        """

        query = """
        INSERT INTO wizard_skills_report_line
            (report_id, report_type, create_uid, create_date, date, year, trade_name, legal_name, sdl_no, parent_trade_name, parent_legal_name,
            parent_sdl_no, bee_status_id, total_annual_payroll, no_employees, phone, fax_number, org_reg_no, sic_code_id,
            physical_address1, physical_address2, physical_address3, physical_municipality_id, physical_code, physical_urban_rural, physical_province_id,
            incorrect_seta, legal_status_id, interested_in_communication, financial_year_start, financial_year_end, employees_by_date, sdf_acting_for_employer,
            appointment_procedure_id, sdf_comments, sdf_function_id, sdf_title, sdf_firstname, sdf_surname, sdf_initials, sdf_idno,
            sdf_alternate_idno, sdf_alternateid_type_id, sdf_gender_id, sdf_equity_id, sdf_highest_edu_level_id,sdf_current_occupation, 
            sdf_occupation_experience, sdf_occupation_years, sdf_phone, sdf_cellphone, sdf_faxnumber, sdf_email,
            sdf_postal_address1,sdf_postal_address2, sdf_postal_address3, sdf_postal_municipality_id, sdf_postal_code, sdf_postal_province_id, sdf_physical_province_id,sdf_status,
            wsp_year, wsp_create_date, wsp_status, wsp_due_date, 
            org_contact_title, org_contact_firstname, org_contact_surname, org_contact_initials, org_contact_jobtitle,
            org_contact_phone, org_contact_faxnumber,org_contact_email, org_contact_cell, org_contact_address1, org_contact_address2, 
            org_contact_city_id, org_contact_postal_code,org_contact_region, 
            apr, may, jun, jul, aug, sep, oct, nov, dec, jan, feb, mar,	total, 
            planning_grant, implementation_grant, discretionary_grant, project_grant,
            efacts_contact, efacts_address, dol_status, linked_organisation_type, emp_per_profile, inter_seta_transfer,
            org_id, tmp_org_report_id, org_size_id, org_registered_by, org_registered_date)
        SELECT
            %s AS report_id,
            %s AS report_type,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS date,
            %s As Year,
            org.trade_name AS trade_name,
            org.legal_name AS legal_name,
            org.sdl_no AS sdl_no,
			(SELECT parentorg.trade_name from inseta_organisationlinkages linkage 
			 	LEFT JOIN inseta_organisation parentorg on parentorg.id = linkage.organisation_id
			 	WHERE org.id = linkage.childorganisation_id limit 1) AS parent_trade_name,
			(SELECT parentorg.legal_name from inseta_organisationlinkages linkage 
			 	LEFT JOIN inseta_organisation parentorg on parentorg.id = linkage.organisation_id
			 	WHERE org.id = linkage.childorganisation_id limit 1) AS parent_legal_name,
			(SELECT parentorg.sdl_no from inseta_organisationlinkages linkage 
			 	LEFT JOIN inseta_organisation parentorg on parentorg.id = linkage.organisation_id
			 	WHERE org.id = linkage.childorganisation_id limit 1) AS parent_sdl_no,

            org.bee_status_id bee_status_id, 
            org.total_annual_payroll total_annual_payroll, 
            org.no_employees no_employees, 
            orgpartner.phone phone, 
            orgpartner.fax_number fax_number, 
            org.registration_no org_reg_no, 
            org.sic_code_id sic_code_id,
            orgpartner.street physical_address1, 
            orgpartner.street2 physical_address2, 
            orgpartner.street3 physical_address3, 
            orgpartner.physical_municipality_id physical_municipality_id, 
            orgpartner.physical_code physical_code, 
            orgpartner.physical_urban_rural physical_urban_rural,  
            orgpartner.physical_province_id physical_province_id,
            'No' as incorrect_seta, 
            org.legal_status_id legal_status_id, 
            CASE 
                WHEN (org.is_interested_in_communication = true) THEN 'Yes'
                ELSE 'No'
            END AS interested_in_communication,
            %s as financial_year_start, 
            %s as financial_year_end, 
            null as employees_by_date, 
            CASE WHEN (SELECT sdforg.is_acting_for_employer 
					   FROM inseta_sdf_organisation sdforg 
					   WHERE organisation_id = org.id and sdf_role = 'primary'
					   order by id desc limit 1 ) 
			= true THEN 'Yes'ELSE 'No' END AS sdf_acting_for_employer,
			(SELECT sdforg.appointment_procedure_id 
				FROM inseta_sdf_organisation sdforg 
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	and state = 'approve' order by id desc limit 1 ) AS appointment_procedure_id,
			(SELECT sdforg.recommendation_comment 
				FROM inseta_sdf_organisation sdforg 
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by id desc limit 1 ) AS sdf_comments,
			(SELECT sdforg.sdf_function_id 
				FROM inseta_sdf_organisation sdforg 
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by id desc limit 1 ) AS sdf_function_id,
			(SELECT sdfpartner.title 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_title,
			(SELECT sdfpartner.first_name 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_firstname,
			(SELECT sdfpartner.last_name 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_surname,
			(SELECT sdfpartner.initials 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_initials,
			(SELECT sdfpartner.id_no 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_idno,
			(SELECT sdfpartner.passport_no
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_alternate_idno,
			(SELECT sdfpartner.alternateid_type_id 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_alternateid_type_id,
			(SELECT sdfpartner.gender_id
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_gender_id,
			(SELECT sdfpartner.equity_id 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_equity_id,
			(SELECT sdf.highest_edu_level_id 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_highest_edu_level_id,
			(SELECT sdf.current_occupation 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_current_occupation,
			(SELECT sdf.occupation_experience 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_occupation_experience,
			(SELECT sdf.occupation_years 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_occupation_years,
			(SELECT sdfpartner.phone 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_phone,
			(SELECT sdfpartner.mobile 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_cellphone,
			(SELECT sdfpartner.fax_number 
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS  sdf_faxnumber,
				
			(SELECT sdfpartner.email
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_email,
				
			(SELECT sdfpartner.postal_address1
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_postal_address1,
			(SELECT sdfpartner.postal_address2
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_postal_address2,
			(SELECT sdfpartner.postal_address3
				FROM inseta_sdf_organisation sdforg 
			 	LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
			 	LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
			 	order by sdforg.id desc limit 1 ) AS sdf_postal_address3,
			(SELECT sdfpartner.postal_municipality_id
				FROM inseta_sdf_organisation sdforg 
				LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
				LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
				order by sdforg.id desc limit 1 ) AS sdf_postal_municipality_id,
			(SELECT sdfpartner.postal_code
				FROM inseta_sdf_organisation sdforg 
				LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
				LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
				order by sdforg.id desc limit 1 ) AS sdf_postal_code,
					
			(SELECT sdfpartner.postal_province_id
				FROM inseta_sdf_organisation sdforg 
				LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
				LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
				order by sdforg.id desc limit 1 ) AS sdf_postal_province_id,	
					
			(SELECT sdfpartner.physical_province_id
				FROM inseta_sdf_organisation sdforg 
				LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
				LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
				order by sdforg.id desc limit 1 ) AS sdf_physical_province_id,
			(SELECT sdforg.state
				FROM inseta_sdf_organisation sdforg 
				LEFT JOIN inseta_sdf sdf on sdf.id = sdforg.sdf_id
				LEFT JOIN res_partner sdfpartner on sdfpartner.id = sdf.partner_id
				WHERE organisation_id = org.id and sdf_role = 'primary' 
				order by sdforg.id desc limit 1 ) AS sdf_state,

			(SELECT wsp.wsp_year from inseta_wspatr wsp 
				WHERE wsp.organisation_id = org.id AND 
				wsp.state = 'approve' order by wsp.id desc limit 1) as wsp_year,
			(SELECT wsp.create_date from inseta_wspatr wsp 
				WHERE wsp.organisation_id = org.id AND 
				wsp.state = 'approve' order by wsp.id desc limit 1) as wsp_create_date,
			(SELECT wsp.state from inseta_wspatr wsp 
				WHERE wsp.organisation_id = org.id AND 
				wsp.state = 'approve' order by wsp.id desc limit 1) as wsp_status,
			(SELECT wsp.due_date from inseta_wspatr wsp 
				WHERE wsp.organisation_id = org.id AND 
				wsp.state = 'approve' order by wsp.id desc limit 1) as wsp_due_date,

			(SELECT title from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_title,
			(SELECT first_name from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_firstname,
			(SELECT last_name from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_lastname,
			(SELECT initials from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_initials,
			(SELECT partner.function from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_jobtitle,
			(SELECT phone from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_phone,
			(SELECT fax_number from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_fax_number,
			(SELECT email from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_email,
			(SELECT mobile from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_mobile,
			(SELECT postal_address1 from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_postal_address1,
			(SELECT postal_address2 from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_postal_address2,
			(SELECT postal_city_id from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_postal_city_id,
			(SELECT postal_code from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_postal_code,
			(SELECT postal_province_id from res_partner partner WHERE partner.parent_id = orgpartner.id order by partner.id desc limit 1) AS contact_postal_province_id,
            null AS apr_levy,	
            null AS may_levy,	
            null AS june_levy,	
            null AS july_levy,	
            null AS aug_levy,	
            null AS sep_levy,	
            null AS oct_levy,	
            null AS nov_levy,	
            null AS dec_levy,	
            null AS jan_levy,	
            null AS feb_levy,	
            null AS mar_levy,	
            null AS total_levy,
            null as planning_grant, 
            null as implementation_grant, 
            null as discretionary_grant, 
            null as project_grant,
            null as efacts_contact, 
            null as efacts_address, 
            null dol_status,
            CASE WHEN (SELECT linkage.childorganisation_id FROM inseta_organisationlinkages linkage WHERE org.id = linkage.childorganisation_id and linkage.state = 'approve') is not null THEN 'Child' ELSE 'Parent' END AS linked_organisation_type, 
            org.no_employees AS emp_per_profile, 
            'No' AS inter_seta_transfer,
            org.id AS org_id, 
            null AS tmp_org_report_id, 
            org.organisation_size_id AS org_size_id, 
            org.create_uid AS org_registered_by, 
            org.create_date AS org_registered_date
        FROM
            inseta_organisation org
            LEFT JOIN res_partner orgpartner on orgpartner.id = org.partner_id
        ORDER BY
            org.id
        """
        fy = self.env['res.financial.year']._get_current_financial_year()
        year = fy and fy.date_from.year or fields.Date.today().year
        fy_start = fy and fy.date_from or False
        fy_end = fy and fy.date_to or False

        params = [
            # SELECT
            self.report_id.id,
            self.report_type,
            self.env.uid,
            self.report_id.date_from,
            year,
            fy_start,
            fy_end,
        ]
        self.env.cr.execute(query, tuple(params))
