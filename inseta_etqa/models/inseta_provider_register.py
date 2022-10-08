from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
from odoo.addons.inseta_tools.converters import  dd2dms

_logger = logging.getLogger(__name__)


class AccreditationQualificationLine(models.Model):
    _name = 'inseta.accreditation.qualification.line'
    _inherit = 'mail.thread'
    _description = 'Accreditation Qualification' 
    """This is the qualification line during provider accreditation"""

    qualification_id = fields.Many2one("inseta.qualification", 'Qualification', ondelete='restrict', domain=lambda act: [('active', '=', True)])
    provider_id = fields.Many2one("inseta.provider", 'Provider', ondelete='restrict')
    saqa_id = fields.Char(string='ID', related="qualification_id.saqa_id")
    provider_accreditation_qualification_id = fields.Many2one('inseta.provider.accreditation')
    verify = fields.Boolean('Verify', default=False)
    minimum_credits = fields.Integer(string="Minimum Credits")
    total_credits = fields.Integer(string="Total Credits", store=True)
    assessors_id = fields.Many2one("inseta.assessor", string='Assessor Name',
                                   domain=[('active', '=', True)])
    assessor_sla_document = fields.Many2one('ir.attachment', string="Assessor SLA Document")
    moderators_id = fields.Many2one("inseta.moderator", string='Moderator Name',
                                    domain=[('active', '=', True)])
    moderator_sla_document = fields.Many2one('ir.attachment', string="Moderator SLA Document")
    assessor_no = fields.Char(string="Assessor No", help="Provider Valid registration or SDL Number")
    moderator_no = fields.Char(string="Moderator No",help="Provider Valid registration or SDL Number")
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('qualification_id')
    def _onchange_qualification_id(self):
        if self.qualification_id:
            self.saqa_id = self.qualification_id.saqa_id

    @api.onchange('assessor_no')
    def onchange_assessor_no(self):
        if self.assessor_no and self.qualification_id:
            assessor = str(self.assessor_no).strip()
            assessor_id = self.env['inseta.assessor'].search(
                ['|',('registration_number', '=', assessor), ('id_no', '=', assessor)], limit=1)
            if not assessor_id:
                self.assessor_no = ''
                return {
                    'warning': {'title': 'Invalid Assessor Number', 'message': 'Please Enter Valid Assessor Number/ ID!!!'}}
            self.sudo().write({'assessors_id': assessor_id.id})
            
             

    @api.onchange('moderator_no')
    def onchange_moderator_no(self):
        if self.moderator_no and self.qualification_id:
            moderator = str(self.moderator_no).strip()
            moderator_id = self.env['inseta.moderator'].search(
                ['|',('registration_number', '=', moderator), ('id_no', '=', moderator)], limit=1)
            if not moderator_id:
                self.moderator_no = ''
                return {'warning': {'title': 'Invalid Moderator Number / ID',
                                    'message': 'Please Enter Valid Moderator Number / ID!!!'}}
            else:
                self.moderators_id = moderator_id.id


class AccreditationLearnershipLine(models.Model):
    _name = 'inseta.accreditation.learnership.line'
    _inherit = 'mail.thread'
    _description = 'Accreditation Qualification' 
    """This is the qualification line during provider accreditation"""

    programme_id = fields.Many2one("inseta.learner.programme", 'Programme ID', ondelete='restrict')
    provider_id = fields.Many2one("inseta.provider", 'Provider', ondelete='restrict')

    saqa_id = fields.Char(string='SAQA ID', related="programme_id.programme_code")
    parent_id = fields.Integer(string='Parent ID')
    provider_accreditation_learnership_id = fields.Many2one('inseta.provider.accreditation', 'Provider Accreditation Reference')
    verify = fields.Boolean('Verify', default=False)
    minimum_credits = fields.Integer(string="Minimum Credits")
    total_credits = fields.Integer(string="Total Credits", store=True)
    assessors_id = fields.Many2one("inseta.assessor", string='Assessor Name',
                                   domain=[('active', '=', True)])
    assessor_sla_document = fields.Many2one('ir.attachment', string="Assessor SLA Document")
    moderators_id = fields.Many2one("inseta.moderator", string='Moderator Name',
                                    domain=[('active', '=', True)])
    moderator_sla_document = fields.Many2one('ir.attachment', string="Moderator SLA Document")
    assessor_no = fields.Char(string="Assessor ID")
    moderator_no = fields.Char(string="Moderator ID")
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('programme_id')
    def _onchange_programme_id(self):
        if self.programme_id:
            self.saqa_id = self.programme_id.programme_code

    @api.onchange('assessor_no')
    def onchange_assessor_no(self):
        if self.assessor_no and self.programme_id:
            assessor = str(self.assessor_no).strip()
            assessor_id = self.env['inseta.assessor'].search(
                ['|',('registration_number', '=', assessor), ('id_no', '=', assessor)], limit=1)
            if not assessor_id:
                self.assessor_no = ''
                return {
                    'warning': {'title': 'Invalid Assessor Number', 'message': 'Please Enter Valid Assessor Number /ID!!!'}}
            self.sudo().write({'assessors_id': assessor_id.id})
            
    @api.onchange('moderator_no')
    def onchange_moderator_no(self):
        if self.moderator_no and self.programme_id:
            moderator = str(self.moderator_no).strip()
            moderator_id = self.env['inseta.moderator'].search(
                ['|',('registration_number', '=', moderator), ('id_no', '=', moderator)], limit=1)
            if not moderator_id:
                self.moderator_no = ''
                return {'warning': {'title': 'Invalid Moderator Number',
                                    'message': 'Please Enter Valid Moderator Number /ID!!!'}}
            else:
                self.moderators_id = moderator_id.id


class AccreditationUnitstandardLine(models.Model):
    _name = 'inseta.accreditation.unit_standard.line' 
    _description = 'Provider Accreditation Unit Standard' 

    programme_id = fields.Many2one("inseta.unit.standard", 'Unit standard ID', ondelete='restrict')
    provider_id = fields.Many2one("inseta.provider", 'Provider', ondelete='restrict')

    saqa_id = fields.Char(string='Code', related="programme_id.code")
    parent_id = fields.Integer(string='Parent ID')
    provider_accreditation_unit_standard_id = fields.Many2one('inseta.provider.accreditation', 'Provider Accreditation Reference')
    verify = fields.Boolean('Verify', default=False)
    minimum_credits = fields.Integer(string="Minimum Credits")
    total_credits = fields.Integer(string="Total Credits", store=True)
    assessors_id = fields.Many2one("inseta.assessor", string='Assessor Name')
    assessor_sla_document = fields.Many2one('ir.attachment', string="Assessor SLA Document")
    moderators_id = fields.Many2one("inseta.moderator", string='Moderator Name')
    moderator_sla_document = fields.Many2one('ir.attachment', string="Moderator SLA Document")
    assessor_no = fields.Char(string="Assessor ID")
    moderator_no = fields.Char(string="Moderator ID")
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('programme_id')
    def _onchange_programme_id(self):
        if self.programme_id:
            self.saqa_id = self.programme_id.programme_code

    @api.onchange('assessor_no')
    def onchange_assessor_no(self):
        if self.assessor_no and self.programme_id:
            assessor = str(self.assessor_no).strip()
            assessor_id = self.env['inseta.assessor'].search(
                ['|',('registration_number', '=', assessor), ('id_no', '=', assessor)], limit=1)
            if not assessor_id:
                self.assessor_no = ''
                return {'warning': {'title': 'Invalid Assessor Number', 'message': 'Please Enter Valid Assessor Registration or Identification Number!!!'}}
            else:
                self.sudo().write({'assessors_id': assessor_id.id})

    @api.onchange('moderator_no')
    def onchange_moderator_no(self):
        if self.moderator_no and self.programme_id:
            moderator = str(self.moderator_no).strip()
            moderator_id = self.env['inseta.moderator'].search(
                ['|',('registration_number', '=', moderator), ('id_no', '=', moderator)], limit=1)
            raise ValidationError(moderator_id)
            if not moderator_id:
                self.moderator_no = ''
                return {'warning': {'title': 'Invalid Moderator Number',
                                    'message': 'Please Enter Valid Moderator Registration or Identification Number!!!'}}
            else:
                self.moderators_id = moderator_id.id


class AccreditationSkillLine(models.Model):
    _name = 'inseta.accreditation.skill.line' 
    _description = 'Provider Accreditation Skill' 

    programme_id = fields.Many2one("inseta.skill.programme", 'Programme ID', ondelete='restrict')
    provider_id = fields.Many2one("inseta.provider", 'Provider', ondelete='restrict')

    saqa_id = fields.Char(string='SAQA ID', related="programme_id.programme_code")
    parent_id = fields.Integer(string='Parent ID')
    provider_accreditation_skill_id = fields.Many2one('inseta.provider.accreditation', 'Provider Accreditation Reference')
    verify = fields.Boolean('Verify', default=False)
    minimum_credits = fields.Integer(string="Minimum Credits")
    total_credits = fields.Integer(string="Total Credits", store=True)
    assessors_id = fields.Many2one("inseta.assessor", string='Assessor Name')
    assessor_sla_document = fields.Many2one('ir.attachment', string="Assessor SLA Document")
    moderators_id = fields.Many2one("inseta.moderator", string='Moderator Name')
    moderator_sla_document = fields.Many2one('ir.attachment', string="Moderator SLA Document")
    assessor_no = fields.Char(string="Assessor ID")
    moderator_no = fields.Char(string="Moderator ID")
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('programme_id')
    def _onchange_programme_id(self):
        if self.programme_id:
            self.saqa_id = self.programme_id.programme_code

    @api.onchange('assessor_no')
    def onchange_assessor_no(self):
        if self.assessor_no and self.programme_id:
            assessor = str(self.assessor_no).strip()
            assessor_id = self.env['inseta.assessor'].search(
                ['|',('registration_number', '=', assessor), ('id_no', '=', assessor)], limit=1)
            if not assessor_id:
                self.assessor_no = ''
                return {'warning': {'title': 'Invalid Assessor Number', 'message': 'Please Enter Valid Assessor Registration or Identification Number!!!'}}
            else:
                # assessor_ids = self.provider_accreditation_skill_id.mapped('assessor_ids').filtered(lambda ass: ass.id_no == assessor)
                # if not assessor_ids:
                # 	return {'warning': 
                # 	{'title': 'Invalid Assessor', 'message': 'The assessor is not registered for this provider'}}

                self.sudo().write({'assessors_id': assessor_id.id})

    @api.onchange('moderator_no')
    def onchange_moderator_no(self):
        if self.moderator_no and self.programme_id:
            moderator = str(self.moderator_no).strip()
            moderator_id = self.env['inseta.moderator'].search(
                ['|',('registration_number', '=', moderator), ('id_no', '=', moderator)], limit=1)
            raise ValidationError(moderator_id)
            if not moderator_id:
                self.moderator_no = ''
                return {'warning': {'title': 'Invalid Moderator Number',
                                    'message': 'Please Enter Valid Moderator Registration or Identification Number!!!'}}
            else:
                # moderator_ids = self.provider_accreditation_skill_id.mapped('moderator_ids').filtered(lambda ass: ass.id_no == moderator)
                # if not moderator_ids:
                # 	return {'warning': 
                # 	{'title': 'Invalid Moderator', 'message': 'The assessor is not registered for this provider'}}

                self.moderators_id = moderator_id.id


class TrainingMaterial(models.Model):
    _name = 'inseta.training.material'
    _description = "training material"

    name = fields.Char('Name')
    attachment_id = fields.Many2one('ir.attachment', string="Attachments")
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean(string='Active', default=True)


class ProviderRegistrationStatus(models.Model):
    _name = 'inseta.provider.registration.status'
    _description = "-"

    name = fields.Char('Name')
    code = fields.Char('Code')
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean(string='Active', default=True)
  

class ProviderAccreditation(models.Model):
    _name = 'inseta.provider.accreditation'
    _description = "Inseta Provider Accreditation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "provider_name"
    _order= "id desc"

    saqa_id = fields.Char(string='SAQA ID',)
    provider_etqa_id = fields.Char(string='ETQA ID', default="595")
    provider_id = fields.Many2one("inseta.provider", 'Provider')
    provider_status = fields.Many2one("inseta.provider.registration.status", 'Provider Status', default=lambda s: s.env.ref('inseta_etqa.data_inseta_provider_regis_status2'))
    is_existing_reg = fields.Boolean('is Existing Provider?')
    is_already_seta_member = fields.Boolean('Already Accredited by other SETA?')
    image_512 = fields.Image("Image", max_width=512, max_height=512)
    organisation_sdf_id = fields.Many2one('inseta.sdf.organisation', string='Organisation SDF ID')
    organisation_id = fields.Many2one('inseta.organisation', string='Organisation ID') 
    verifier_ids = fields.Many2many('res.users', 'provider_reg_verifier_rel', 'column1', string="Verifiers")
    provider_name = fields.Char(string='Legal Name')
    legacy_system_id = fields.Integer('Legacy System ID')
    trade_name = fields.Char(string='Trading As Name')
    password = fields.Char(string='Password')
    registration_no = fields.Char(string='Registration Number')
    training_material_id = fields.Many2one('inseta.training.material', string='Training material') # MUST EXIST IN THE SYSTEM
    vat_number = fields.Char(string='VAT Number')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    cell_phone = fields.Char(string='Cell Phone')
    campus_name = fields.Char(string='Campus Name')
    campus_phone = fields.Char(string='Campus phone')
    mobile = fields.Char(string='Campus Cell Number')
    fax = fields.Char(string='Campus Fax')
    campus_email = fields.Char(string='Campus Email')
    campus_building = fields.Char(string='Campus Building')
    campus_street_number = fields.Char(string='Street Number')
    campus_code = fields.Char(string='Campus Code')
    campus_address1 = fields.Char(string='Campus Address')
    campus_address2 = fields.Char(string='Campus Address 2')
    campus_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Campus Urban/Rural') 
    
    campus_email = fields.Char(string='Campus Email')
    campus_building = fields.Char(string='Campus Building')
    campus_street_number = fields.Char(string='Street Number')
    campus_code = fields.Char(string='Campus Code')
    campus_address1 = fields.Char(string='Campus Address')
    campus_address2 = fields.Char(string='Campus Address 2')
    campus_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Campus Urban/Rural') 

    campus2_name = fields.Char(string='Campus Name')
    campus2_phone = fields.Char(string='Campus phone')
    campus2_email = fields.Char(string='Campus Email')
    campus2_building = fields.Char(string='Campus Building')
    campus2_street_number = fields.Char(string='Street Number')
    campus2_code = fields.Char(string='Campus Code')
    campus2_address1 = fields.Char(string='Campus Address')
    campus2_address2 = fields.Char(string='Campus Address 2')
    campus2_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Campus Urban/Rural') 
      
    number_staff_members = fields.Char(string='Number of full time staff members')
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref("base.za").id)	
    sic_code = fields.Many2one('res.sic.code', string='Primary Focus') # MUST EXIST IN THE SYSTEM
    provider_approval_date = fields.Date(string='Provider Approval Date')
    provider_register_date = fields.Date(string='Provider Accreditation Date')
    provider_expiry_date = fields.Date(string='Provider Accreditation Date')
    physical_code = fields.Char(string='Physical Code')
    physical_address1 = fields.Char(string='Physical Address Line 1')
    physical_address2 = fields.Char(string='Physical Address Line 2')
    physical_address3 = fields.Char(string='Physical Address Line 3')
    physical_suburb_id = fields.Many2one('res.suburb',string='Physical Suburb')
    physical_city_id = fields.Many2one('res.city', string='Physical City')
    physical_municipality_id = fields.Many2one(
        'res.municipality', string='Physical Municipality')
    physical_province_id = fields.Many2one(
        'res.country.state', string='Physical Province', domain=[('code', '=', 'ZA')])

    postal_code = fields.Char(string='Postal Code')
    postal_address1 = fields.Char(string='Postal Address Line 1')
    postal_address2 = fields.Char(string='Postal Address Line 2')
    postal_address3 = fields.Char(string='Postal Address Line 3')
    postal_suburb_id = fields.Many2one('res.suburb',string='Postal Suburb')
    postal_city_id = fields.Many2one('res.city', string='Postal City',)
    postal_municipality_id = fields.Many2one('res.municipality', string='Postal Municipality')
     
    postal_urban_rural = fields.Selection([
            ('Urban', 'Urban'), 
            ('Rural', 'Rural'), 
            ('Unknown', 'Unknown')
        ], string='Postal Urban/Rural')

    end_date = fields.Date(string='Accreditation End Date')
    start_date = fields.Date(string='Accreditation Start Date')
    dhet_end_date = fields.Date(string='DHET End Date')
    dhet_start_date = fields.Date(string='DHET Start Date')
    accreditation_number = fields.Char(string='Accreditation number')
    current_business_years = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('10+', '10+'),
    ], string='Years in Business')

    provider_type_id =fields.Many2one('res.provider.type', string='Provider type') # FASSET, QAP
    provider_class_id =fields.Many2one('res.provider.class', string='Provider Class')
    provider_category_id =fields.Many2one('res.provider.category', string='Provider Category')
    provider_quality_assurance_id =fields.Many2one('inseta.quality.assurance', string='Quality Assurance Body id')
    quality_assurance_code = fields.Char(string='QA Saqa Code', related="provider_quality_assurance_id.code")
    reference = fields.Char(string='Reference')
    work_zip_code = fields.Char(string='Work Zip code')
    user_id = fields.Many2one('res.users', string="User ID", default=lambda self: self.env.user.id)
    tax_clearance_ids = fields.Many2many('ir.attachment', 'tax_attachment_rel', 'column1', string="Tax clearance")
    tax_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    all_complaint = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    qualification_certificate_copy_ids = fields.Many2many('ir.attachment', 'cert_copy_attachment_rel', 'column1',string="Certificate copies of Qualifications")
    director_cv_ids = fields.Many2many('ir.attachment', 'director_cv_attachment_rel', 'column1', string="Director CV")
    cipc_dsd_ids = fields.Many2many('ir.attachment', 'cipc_attachment_rel', 'column1',string="CIPC")
    company_profile = fields.Many2one('ir.attachment', string='Company profile')
    company_organogram = fields.Many2one('ir.attachment',string='Organogram')
    appointment_letter = fields.Many2one('ir.attachment', string='Appointment Letter')
    proof_of_ownership = fields.Many2one('ir.attachment', string='Proof of Ownership')
    workplace_agreement = fields.Many2one('ir.attachment', string='Workplace agreement')
    skills_registration_letter = fields.Many2one('ir.attachment', string='Skills Programme registration letter')
    learning_approval_report = fields.Many2one('ir.attachment', string='Learning Programme approval Report')
    referral_letter = fields.Many2one('ir.attachment', string='PRIMARY ETQA REFERRAL LETTER')
    primary_accreditation_letter = fields.Many2one('ir.attachment', string='Primary accreditation letter')

    business_lease_agreement = fields.Many2one('ir.attachment', string='Business lease agreement')
    lease_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    account_business_solvency_letter = fields.Many2one('ir.attachment', string='BUSINESS ACCOUNTANT SOLVENCY LETTER')
    acc_solvency_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], default="no", string='Compliant', store=False)
    
    bank_account_confirmation = fields.Many2one('ir.attachment', string='Bank account confirmation')
    bccount_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    bbbeee_affidavit = fields.Many2one('ir.attachment', string='')
    bbbeee_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    business_occupational_certificate_report = fields.Many2one('ir.attachment', string='Business Occupation certificate programme report')
    boc_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    it_servicing = fields.Many2one('ir.attachment', string='')
    it_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    programme_curriculum = fields.Many2one('ir.attachment', string='')
    pc_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    learner_details_achievement_spreadsheet = fields.Many2one('ir.attachment', string='') 
    ld_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)
    quality_management_system = fields.Many2one('ir.attachment', string='Quality management system')
    qms_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

    qcto_referral_letter = fields.Many2one('ir.attachment', string='Qcto referral letter')
    qcto_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

    accreditation_recommended = fields.Selection([('no', 'No'),('yes', 'Yes')], string="Accreditation recommended", store=True)
    provider_contact_person_ids = fields.One2many('inseta.provider.contact', 'provider_id', string="Contact Persons")

    contact_person_ids = fields.Many2many('inseta.provider.contact', 'provider_reg_contact_person_rel', 'column1', string="Contact Person", ondelete="cascade")
    delivery_center_ids = fields.Many2many('inseta.delivery.center', 'provider_reg_delivery_center_rel', 'column1', string="Delivery Center", ondelete="cascade")
    site_visit_ids = fields.Many2many('inseta.provider.site.visit', 'provider_reg_site_visit_rel', 'column1', string="Site visit", ondelete="cascade")
    campus_details = fields.Text(string='Campus Details')
    contact_person_id = fields.Many2one('inseta.provider.contact', string="Contact Person", ondelete="cascade")
    employer_sdl_no = fields.Char(string='SDL No')
    bee_status = fields.Many2one('res.bee.status', string="BBBEEE Status")
    campus_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Campus Urban/Rural') 
     
    gps_coordinates = fields.Char()
    saqa_provider_code = fields.Char(string='SAQA Provider code')
    saqa_id = fields.Char(string='SAQA ID', default="595")
    active = fields.Boolean(default=True)
    latitude_degree = fields.Char(string='Latitude Degree')
    latitude_minutes = fields.Char(string='Latitude Minutes', size=2, tracking=True)
    latitude_seconds = fields.Char(string='Latitude Seconds', size=6, tracking=True)
    
    longitude_degree = fields.Char(string='Longitude Degree')
    longitude_minutes = fields.Char(string='Longitude Minutes',size=2, tracking=True)
    longitude_seconds = fields.Char(string='Longitude Seconds', size=6, tracking=True)
    use_physical_for_postal_addr = fields.Boolean(string= "Use physical address for postal address?")
    
    postal_code = fields.Char(string='Postal Code')
    postal_address1 = fields.Char(string='Postal Address Line 1')
    postal_address2 = fields.Char(string='Postal Address Line 2')
    postal_address3 = fields.Char(string='Postal Address Line 3')
    postal_suburb_id = fields.Many2one('res.suburb',string='Postal Suburb')
    postal_city_id = fields.Many2one('res.city', string='Postal City',)
    postal_municipality_id = fields.Many2one('res.municipality', string='Postal Municipality')
    
    postal_urban_rural = fields.Selection([
            ('Urban', 'Urban'), 
            ('Rural', 'Rural'), 
            ('Unknown', 'Unknown')
        ], string='Postal Urban/Rural')
    postal_province_id = fields.Many2one(
        'res.country.state', 
        string='Postal Province', 
        domain=[('country_id.code', '=', 'ZA')]
    )

    provider_skill_accreditation_ids = fields.One2many("inseta.accreditation.skill.line", 'provider_accreditation_skill_id', string='Skill Accreditations')
    provider_learnership_accreditation_ids = fields.One2many("inseta.accreditation.learnership.line", 'provider_accreditation_learnership_id', string='Learnership Accreditations')
    provider_qualification_ids = fields.One2many(
        'inseta.accreditation.qualification.line',
        'provider_accreditation_qualification_id', 
        'Qualification reference', 
    )
    provider_unit_standard_ids = fields.One2many(
        'inseta.accreditation.unit_standard.line',
        'provider_accreditation_unit_standard_id', 
        'Unit standard reference')
    skill_programmes_ids = fields.Many2many("inseta.skill.programme", 'provider_skill_programme_rel', string='Skill Programmes')
    learner_programmes_ids = fields.Many2many("inseta.learner.programme",'provider_learner_programme_rel', string='Learnership Programmes')
    qualification_ids = fields.Many2many("inseta.qualification", 'inseta_provider_reg_qualification_rel', 'column1', string='Qualification')
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_provider_reg_unit_standard_rel', 'column1', string='Unit standard')
    assessor_ids = fields.Many2many("inseta.assessor", 'inseta_provider_reg_assessor_rel', 'column1', string='Assessors')
    facilitator_ids = fields.Many2many("inseta.assessor", 'inseta_assessor_facilitator_rel', 'inseta_provider_acreditation_id', 'inseta_assessor_facilitator_id', string='Facilitator')
    moderator_ids = fields.Many2many("inseta.moderator", 'inseta_provider_reg_moderator_rel', 'column1', string='Moderator')
    # provider_assessor_ids = fields.One2many("inseta.assessor", 'provider_id', string='Assessors')
    # provider_moderator_ids = fields.One2many("inseta.moderator", 'provider_id', string='Moderators')
    # provider_facilitator_ids = fields.One2many("inseta.assessor", 'inseta_assessor_facilitator_rel', 'inseta_provider_acreditation_id', 'inseta_assessor_facilitator_id', string='Facilitator')
    
    # discard
    # qualification_programmes_ids = fields.Many2many("inseta.qualification.programme",'provider_qualification_programme_rel', 'inseta_provider_accreditation_id', 'inseta_qualification_programme_id', string='Qualification Programmes')
    state = fields.Selection([
        ('draft', 'Address Information'),
        ('evaluation', 'Verification'),
        ('recommend', 'Recommendation'),
        ('manager', 'Manager'),
        ('queried', 'Queried'),
        ('approved', 'Approved'),
        ('denied', 'Rejected'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False)
    manipulated_state = fields.Selection([
        ('draft', 'Address Information'),
        ('evaluation', 'Verification'),
        ('recommend', 'Recommendation'),
        ('manager', 'Manager'),
        ('queried', 'Queried'),
        ('approved', 'Approved'),
        ('denied', 'Rejected'),
    ], string='Manipulated', index=True, readonly=False, default='draft', copy=False)
    accreditation_status = fields.Selection([
        ('Primary', 'Primary Provider'),
        ('secondary', 'Secondary Provider'),
    ], string='Accreditation Status', index=True, copy=False)
    refusal_comment = fields.Text('Refusal Comments')
    comments = fields.Text('Comments')
    notes = fields.Text('Notes')
    approval_date = fields.Date('Approval Date')
    denied_date = fields.Date('Denial Date')
    query_date = fields.Date('Query Date')
    total_credits = fields.Integer('Total Credits')
    expiry_reminder_sent = fields.Boolean('Expiry Reminder')
    etqa_manager_ids = fields.Many2many(
        'res.users',
        'etqa_provider_manager_rel',
        'etqa_provider_manager_id',
        'res_users_id',
        string='Evaluation Manager (s)',
        help="Technical Field to compute eval manager"
    )
    application_compliance = fields.Text('Application compliance Status')

    @api.onchange('end_date')
    def onchange_end_date(self):
        for rec in self:
            if rec.start_date:
                if rec.end_date < rec.start_date:
                    rec.end_date = False 
                    return {'warning': {'title': 'Warning', 'message': "Start date must be lesser than end date"}}

    @api.onchange('employer_sdl_no')
    def check_existing_employer(self):
        if self.employer_sdl_no:
            existing_provider = self.env['inseta.provider'].sudo().search([('employer_sdl_no', '=', self.employer_sdl_no)], limit=1)
             
            if not self.is_existing_reg:
                if existing_provider:
                    self.employer_sdl_no = ""
                    return {
                        'warning': {
                            'title': 'Duplicate Employer',
                            'message': "Provider with SDL/N Number already exist"
                        }
                    }
            else:
                if not existing_provider:
                    self.provider_name = ""
                    self.employer_sdl_no = ""
                    return {
                        'warning': {
                            'title': 'Warning',
                            'message': "Provider with SDL/N Number does not exist"
                        }}
                self.provider_name = existing_provider.name

    @api.onchange('physical_address1')
    def onchange_physical_address1(self):
        if self.physical_address1:
            addr = self.physical_address1.split(' ')
            res = False 
            for txt in addr:
                if txt.isalpha():
                    res = True
                    break
            if not res:
                self.physical_address1 = ''
                return {'warning': {'title':'Invalid input','message': "Physical Address Line 1 must be alpha number format e.g 23 chris maduka street"}}

    @api.onchange('physical_code')
    def _onchange_physical_code(self):
        if self.physical_code:
            if len(self.physical_code) != 4:
                self.clear_address()
                return {
                    'warning': {'title': 'Invalid', 'message': "Physical code must be up to 4 characters !!!"}
                }
            locals = self.env['res.suburb'].search(
                [('postal_code', '=', self.physical_code)], limit=1)
            if locals:
                self.physical_municipality_id = locals.municipality_id.id
                self.physical_suburb_id = locals.id
                self.physical_province_id = locals.province_id.id
                self.physical_city_id = locals.city_id.id
            else:
                self.clear_address()
                return {
                    'warning': {'title': 'Invalid', 'message': "Wrong Physical code provided!!!"}
                }
    
    def clear_address(self):
        self.physical_suburb_id = False
        self.physical_municipality_id = False
        self.physical_province_id = False
        self.physical_city_id = False

        self.postal_suburb_id = False
        self.postal_municipality_id = False
        self.postal_province_id = False
        self.postal_city_id = False
        self.postal_urban_rural = False

    @api.onchange('postal_code')
    def _onchange_postal_code(self):
        if self.postal_code:
            if len(self.postal_code) != 4:
                return {
                    'warning': {'title': 'Invalid', 'message': "Postal code must be up to 4 characters !!!"}
                }
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.postal_code)], limit=1)
            if sub:
                self.postal_suburb_id = sub.id
                self.postal_municipality_id = sub.municipality_id.id
                self.postal_province_id = sub.district_id.province_id.id
                self.postal_city_id = sub.city_id.id
                #self.nationality_id = sub.nationality_id.id
                self.postal_urban_rural = sub.municipality_id.urban_rural
            else:
                return {
                    'warning': {'title': 'Invalid', 'message': "Wrong Postal code provided!!!"}
                }

    @api.onchange('use_physical_for_postal_addr')
    def _onchange_use_physical_for_postal_addr(self):
        if self.use_physical_for_postal_addr:
            self.postal_municipality_id = self.physical_municipality_id.id
            self.postal_suburb_id = self.physical_suburb_id.id
            self.postal_province_id = self.physical_province_id.id
            self.postal_city_id = self.physical_city_id.id
            # self.postal_urban_rural = self.physical_urban_rural
            self.postal_address1 = self.physical_address1
            self.postal_address2 = self.physical_address2
            self.postal_address3 = self.physical_address3
            self.postal_code = self.physical_code
        else:
            self.postal_municipality_id = False
            self.postal_suburb_id = False
            self.postal_province_id = False
            self.postal_city_id = False
            self.postal_address1 = False
            self.postal_address2 = False
            self.postal_address3 = False
            self.postal_code = False

    def get_geolocation(self):
        # We need country names in English below
        for rec in self.with_context(lang='en_US'):
            result = self.env['res.partner']._geo_localize(
                rec.physical_address1,
                rec.physical_code,
                rec.physical_city_id.name,
                rec.physical_province_id.name,
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
                
    @api.depends('provider_qualification_ids')
    def _compute_total_credit(self):
        pass 
        # total_credit_point = 0
        # if self.provider_qualification_ids:
        # 	for unit_line in self.provider_qualification_ids:
        # 		if unit_line.qualification_id:
        # 			if unit_line.qualification_id.nqflevel_id:
        # 				total_credit_point += int(unit_line.qualification_id.credits)
        # self.total_credits = total_credit_point

    @api.onchange('campus_phone','fax')
    def onchange_validate_number(self):
        if self.campus_phone:
            if not self.campus_phone.strip().isdigit() or len(self.campus_phone) != 10:
                self.campus_phone = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Campus Phone number'}}
        if self.fax:
            if not self.fax.strip().isdigit() or len(self.fax) != 10:
                self.fax = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Fax number'}}
    
    @api.onchange('campus_email', 'email')
    def onchange_validate_email(self):
        if self.campus_email:
            if '@' not in self.campus_email:
                self.campus_email = ''
                return {'warning':{'title':'Invalid input','message':'Please enter a valid campus email address'}}

        if self.email:
            if '@' not in self.email:
                self.email = ''
                return {'warning':{'title':'Invalid input','message':'Please enter a valid email address'}}

    # --------------------------------------------
    # Business Logic
    # --------------------------------------------

    def _get_group_users(self):
        group_obj = self.env['res.groups']
        evaluation_committee_group_id = self.env.ref('inseta_etqa.group_etqa_accreditation_specialist').id
        eval_commmittee_users = group_obj.browse([evaluation_committee_group_id]).users

        group_system_id = self.env.ref('base.group_system').id
        system_users = group_obj.browse([group_system_id]).users
        return eval_commmittee_users or system_users

    def set_to_draft(self):
        self.state = 'draft'

    def _check_valid_fields(self):
        if self.state in ['evaluation']:
            if not (self.skill_programmes_ids or self.qualification_ids or self.learner_programmes_ids):
                raise ValidationError("Please provide programmes")
            if self.all_complaint != "yes":
                raise ValidationError('No evidence is recieved for this application. Scroll through the verification tab')

            if not self.site_visit_ids:
                raise ValidationError('Evidence must be compliant before adding site Visit.. Check site visit under support document tab.')

        if self.state in ['recommend']:
            if self.accreditation_recommended != 'yes':
                raise ValidationError('Please Recommend this accreditation before approving...')

    def _message_post(self, template):
        """Wrapper method for message_post_with_template
        Args:
            template (str): email template
        """
        if template:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('inseta_etqa', template)[1]         
            self.message_post_with_template(
                template_id, composition_mode='comment',
                model=f'{self._name}', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def action_submit_button(self):
        # self._check_valid_fields()
        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group]
        email_from = '"INSETA"registrations@inseta.org.za'
        contact_emails = [rec.contact_person_email for rec in self.delivery_center_ids]
        template = 'email_template_send_to_provider_contact'
        self.action_send_mail(template, contact_emails, email_from, None)
        self._message_post(template)

        # send to provider
        provider_template = "email_template_send_to_provider_after_submission"
        self.action_send_mail(provider_template, [self.email], None, None)
        self._message_post(provider_template)
        #  Sent to Evaluation committees 
        evaluator_template = "email_template_send_to_provider_evaluating_conmmittee"
        self.action_send_mail(evaluator_template, reciepients, None, None) 
        self._message_post(evaluator_template)
        self.write({'state': 'evaluation', 'refusal_comment': '', 'comments': '', 'manipulated_state': 'evaluation'})
    
    def action_evaluating_committee_approve_button(self):
        self._check_valid_fields()
        self.set_to_existing()
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        contact_email = [rec.contact_person_email for rec in self.delivery_center_ids]
        # contact_email = [self.contact_person_id.contact_person_email]
        verifiers = [rec.login for rec in self.verifier_ids]
        reciepients = eval_emails + contact_email + verifiers
        reciepients.append(self.email)
        template = 'email_template_provider_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'recommend', 'manipulated_state': 'recommend'})

    def action_verify_approve_button(self):
        self._check_valid_fields()
        group_obj = self.env['res.groups']
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        contact_email = [rec.contact_person_email for rec in self.delivery_center_ids]
        group_etqa_manager = self.env.ref('inseta_etqa.group_etqa_evaluating_manager').id
        etqa_mgr_users = group_obj.browse([group_etqa_manager]).users
        mgrs = [rec.login for rec in etqa_mgr_users]
        reciepients = eval_emails + contact_email + mgrs
        reciepients.append(self.email)
        template = 'email_template_provider_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'manager','manipulated_state': 'manager'})

    def action_approve_button(self):
        self._check_valid_fields()
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        # contact_email = [rec.contact_person_email for rec in self.contact_person_ids]
        contact_email = [rec.contact_person_email for rec in self.delivery_center_ids]
        verifiers = [rec.login for rec in self.verifier_ids]
        reciepients = eval_emails + contact_email + verifiers
        reciepients.append(self.email)
        template = 'email_template_provider_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        # self.get_geolocation()
        self.write({'state': 'approved', 'approval_date': fields.date.today(), 'manipulated_state': 'approved', 'accreditation_recommended': 'yes'})
        return self.action_manager_approve()

    def action_query(self):
        if self.env.user.has_group("inseta_etqa.group_etqa_evaluating_manager") and self.state not in ['manager']:
            raise ValidationError('You are not allowed to query at this stage')

        if self.env.user.has_group("inseta_etqa.group_etqa_accreditation_specialist") and self.state not in ['recommend']:
            raise ValidationError('You are not allowed to query at this stage')

        if self.env.user.has_group("inseta_etqa.group_etqa_accreditation_admin") and self.state not in ['evaluation']:
            raise ValidationError('You are not allowed to query at this stage')

            #gfffffffffff()
        return self.popup_notification(False, 'query') 

    def action_reject(self):
        if self.env.user.has_group("inseta_etqa.group_etqa_evaluating_manager") and self.state not in ['manager']:
            raise ValidationError('You are not allowed to query at this stage')

        if self.env.user.has_group("inseta_etqa.group_etqa_accreditation_specialist") and self.state not in ['recommend']:
            raise ValidationError('You are not allowed to query at this stage')

        if self.env.user.has_group("inseta_etqa.group_etqa_accreditation_admin") and self.state not in ['evaluation']:
            raise ValidationError('You are not allowed to query at this stage')
        return self.popup_notification(False, 'refuse') 

    def eval_committee_send_query_notification(self): # query notification
        self.update({'query_date': fields.date.today()})
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        # contact_email = [rec.contact_person_email for rec in self.contact_person_ids]
        contact_email = [rec.contact_person_email for rec in self.delivery_center_ids]
        reciepients = eval_emails + contact_email
        reciepients.append(self.email)
        query_submission_date = self.query_date + relativedelta(day=7)
        contexts = {'query_submission_date': query_submission_date}
        template = 'email_template_query_notification'
        self.action_send_mail(template, reciepients, None, contexts) 
        status = 'evaluation' if self.state in ['recommend'] else 'draft' if self.state in ['evaluation'] else 'queried'
        self.write({'state': status})

    def action_provider_submit_query(self): #
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        # contact_email = [rec.contact_person_email for rec in self.contact_person_ids]
        contact_email = [rec.contact_person_email for rec in self.delivery_center_ids]
        reciepients = eval_emails + contact_email
        reciepients.append(self.email)
        template = 'email_template_submit_query_notification'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'evaluation'})
     
    def action_reject_method(self):
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        # contact_email = [rec.contact_person_email for rec in self.contact_person_ids]
        contact_email = [rec.contact_person_email for rec in self.delivery_center_ids]
        reciepients = eval_emails + contact_email
        reciepients.append(self.email)
        template = 'email_template_notify_provider_rejection'	
        self.action_send_mail(template, reciepients, None, None) 
        status = 'evaluation' if self.state in ['recommend'] else 'draft' if self.state in ['evaluation'] else 'denied'
        self.write({
            'state': status, 'denied_date': fields.date.today(),
            'refusal_comment': '', 'comments': ''})

    def action_print_certficate(self):   
        return self.env.ref('inseta_etqa.provider_accreditation_certificate_report_2').report_action(self)

    def action_print_accreditation_summary_statement(self):   
        return self.env.ref('inseta_etqa.provider_accreditation_summary_report').report_action(self)

    def action_send_provider_accreditation_summary_report(self):
        self.ensure_one() 
        report_template = "inseta_etqa.provider_accreditation_summary_report"
        report_template_ref = self.env.ref(report_template)
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', 'etqa_generic_email_template')[1]
        template_rec = self.env['mail.template'].browse(template_id)
        template_rec.write({
            'report_template': report_template_ref.id,
            'report_name': "Accreditation Summary",
            'email_to': self.email,
            })
        template_rec.send_mail(self.id, True)

    def action_send_provider_certficate(self): # needs to refactor for the above to use same method
        self.ensure_one() 
        report_template = "inseta_etqa.provider_accreditation_certificate_report_2"
        report_template_ref = self.env.ref(report_template)
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', 'etqa_generic_email_template')[1]
        template_rec = self.env['mail.template'].browse(template_id)
        template_rec.write({
            'report_template': report_template_ref.id,
            'report_name': "Certificate",
            'email_to': self.email,
            })
        template_rec.send_mail(self.id, True)

    def action_send_mail(self, with_template_id, email_items, email_from=None, contexts=None):
        '''Email_to = [lists of emails], Contexts = {Dictionary} '''
        ids = self.id
        subject = contexts.get('subject', '') if contexts else False
        body = contexts.get('body_context', '') if contexts else False
        email_ctx = contexts.get('email_from', '') if contexts else False
        email_from = email_ctx if not email_from else email_ctx
        addressed_to = contexts.get('addressed_to', '') if contexts else False
        subject = subject if subject else 'Notification Message'
        email_items.append('provideraccreditation@inseta.org.za')
        email_to = (','.join([str(m) for m in email_items])) if email_items else False
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', with_template_id)[1]         
        if template_id:
            ctx = dict()
            ctx.update({
                'default_model': 'inseta.provider.accreditation',
                'default_res_id': ids,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
            })
            if email_from:
                ctx['email_from'] = email_from
            if body:
                ctx['body_context'] = body
            if addressed_to:
                ctx['addressed_to'] = addressed_to
            if subject:
                ctx['subject'] = subject
            template_rec = self.env['mail.template'].browse(template_id)
            template_rec.write({'email_to': email_to})
            template_rec.with_context(ctx).send_mail(ids, True)

    def popup_notification(self, subject, action):
        self.write({'comments': '', 'refusal_comment': ''})
        view = self.env.ref('inseta_etqa.inseta_etqa_wiz_main_view_form')
        view_id = view and view.id or False
        context = {
                    'default_subject': subject, 
                    'default_date': fields.Date.today(),
                    'default_reference': self.id,
                    'default_action': action,
                    'default_model_name': "inseta.provider.accreditation",
                    }
        return {
                'name':'Dialog',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'res_model':'inseta.etqa.wizard',
                'views':[(view.id, 'form')],
                'view_id':view.id,
                'target':'new',
                'context':context,
                } 
         
    def send_reminder_mail(self):
        email_from = '"INSETA"registrations@inseta.org.za'
        contact_email = [self.email]
        template = 'email_template_provider_notify_provider_for_expiry'
        self.action_send_mail(self, contact_email, email_from, template, None)
        self.write({'expiry_reminder_sent': True})

    def _cron_reminder_method(self):
        for rec in self:
            if self.start_date < self.end_date:
                """check if the difference between now and start date is in range of 30, """
                now = datetime.now()
                start_dt = datetime.strptime(rec.start_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                delta = now - start_dt
                days = int(delta.days)
                if days in range (0, 91):
                    rec.send_reminder_mail()

    def provider_vals_func(self):
        vals = {
            # 'partner_id': self.user_id.partner_id.id,
            'user_id': self.user_id.id,
            'name': self.provider_name,
            'trade_name': self.trade_name,
            'email': self.email, 
            'phone': self.phone, 
            'mobile': self.cell_phone,
            # 'fax_number': self.fax,
            'saqa_id': self.saqa_id,
            'provider_status': self.provider_status.id,
            'postal_province_id': self.postal_province_id.id,
            'state_id': self.physical_province_id.id, 
            'physical_code': self.physical_code,
            'zip': self.physical_code,
            'street': self.physical_address1, 
            'street2': self.physical_address2,
            'street3': self.physical_address3, 
            'physical_suburb_id': self.physical_suburb_id.id,
            'physical_city_id': self.physical_city_id.id, 
            'physical_province_id': self.physical_province_id.id, 
            'physical_municipality_id': self.physical_municipality_id.id, 
            'city': self.physical_city_id.name,
            'postal_code': self.postal_code,
            'postal_address1': self.postal_address1,
            'postal_address2': self.postal_address2,
            'postal_address3': self.postal_address3,
            'postal_suburb_id': self.postal_suburb_id.id,
            'postal_city_id': self.postal_city_id.id,
            'postal_municipality_id': self.postal_municipality_id.id,
            'postal_urban_rural': self.postal_urban_rural,
            'current_business_years': self.current_business_years, 
            # 'provider_qualification_ids': [(6, 0, [rec.id for rec in self.provider_qualification_ids])] if self.provider_qualification_ids else False,
            'campus_name': self.campus_name,
            'campus_street_number': self.campus_street_number,
            'campus_phone': self.campus_phone,
            'campus_mobile': self.mobile,
            'campus_fax': self.fax,
            'campus_email': self.campus_email,
            'campus_code': self.campus_code,
            'campus_address1': self.campus_address1,
            'campus_address2': self.campus_address2,
            'campus_urban_rural': self.campus_urban_rural,
            'number_staff_members': self.number_staff_members,
            'total_credits': self.total_credits,
            'tax_clearance_ids': self.tax_clearance_ids.ids,
            'qualification_certificate_copy_ids': self.qualification_certificate_copy_ids.ids,
            'director_cv_ids': self.director_cv_ids.ids,
            'cipc_dsd_ids': self.cipc_dsd_ids.ids,
            # 'skill_programmes_ids': self.skill_programmes_ids,
            # 'learner_programmes_ids': self.learner_programmes_ids,
            # 'qualification_ids': self.qualification_ids,
            # 'unit_standard_ids': self.unit_standard_ids,
            'company_profile': self.company_profile.id,
            'company_organogram': self.company_organogram.id,
            'appointment_letter': self.appointment_letter.id,
            'business_lease_agreement': self.business_lease_agreement.id,
            'account_business_solvency_letter': self.account_business_solvency_letter.id,
            'bbbeee_affidavit': self.bbbeee_affidavit.id,
            'bank_account_confirmation': self.bank_account_confirmation.id,
            'it_servicing': self.it_servicing.id,
            'programme_curriculum': self.programme_curriculum.id,
            'learner_details_achievement_spreadsheet': self.learner_details_achievement_spreadsheet.id,
            'quality_management_system': self.quality_management_system.id,
            'qcto_referral_letter': self.qcto_referral_letter.id,
            'campus_details': self.campus_details,
            'skills_registration_letter': self.primary_accreditation_letter.id,
            'primary_accreditation_letter': self.primary_accreditation_letter.id,
            'referral_letter': self.referral_letter.id,
            'learning_approval_report': self.learning_approval_report.id,
            'training_material_id': self.training_material_id.id,
            'registration_no': self.registration_no,
            'employer_sdl_no': self.employer_sdl_no,
            'reference': self.reference,
            'sic_code': self.sic_code.id,
            "approval_date": fields.Date.today(),
            'contact_type': 'provider',
            'active': True,
            'provider_type_id': self.provider_type_id.id, 
            'provider_class_id': self.provider_class_id.id,
            'provider_category_id': self.provider_category_id.id, 
            'provider_quality_assurance_id': self.provider_quality_assurance_id.id,
            'provider_accreditation_number': self.accreditation_number,
            'contact_person_id': self.contact_person_id.id, 
            "delivery_center_ids": self.delivery_center_ids, 
            'gps_coordinates': self.gps_coordinates,
            'latitude_degree': self.latitude_degree,
            'latitude_minutes': self.latitude_minutes,
            'latitude_seconds': self.latitude_seconds,
            'longitude_degree': self.longitude_degree,
            'longitude_minutes': self.longitude_minutes,
            'longitude_seconds': self.longitude_seconds,
            'saqa_provider_code': self.saqa_provider_code,
            'saqa_id': self.saqa_id,
            'provider_etqa_id': self.provider_etqa_id,
            'assessor_ids': self.assessor_ids,
            'facilitator_ids': self.facilitator_ids,
            'moderator_ids': self.moderator_ids,
            'accreditation_recommended': self.accreditation_recommended,
            'linked_user_ids': [(4, self.user_id.id)],
            'provider_skill_accreditation_ids': [(6, 0, [rec.id for rec in self.provider_skill_accreditation_ids])],
            'provider_learnership_accreditation_ids': [(6, 0, [rec.id for rec in self.provider_learnership_accreditation_ids])],
            'provider_qualification_ids': [(6, 0, [rec.id for rec in self.provider_qualification_ids])],
            'provider_unit_standard_ids': [(6, 0, [rec.id for rec in self.provider_unit_standard_ids])],
            'campus2_name': self.campus2_name,
            'campus2_phone': self.campus2_phone,
            'campus2_email': self.campus2_email,
            'campus2_building': self.campus2_building,
            'campus2_street_number': self.campus2_street_number,
            'campus2_code': self.campus2_code,
            'campus2_address1': self.campus2_address1,
            'campus2_address2': self.campus2_address2,
            'campus2_urban_rural': self.campus2_urban_rural,
            'accreditation_status': self.accreditation_status,
            'end_date': self.dhet_end_date,
            'start_date': self.dhet_end_date,
            'accreditation_end_date': self.end_date,
            'accreditation_start_date': self.start_date,
        }
        return vals

    def set_to_existing(self):
        existing_provider = self.env['inseta.provider'].sudo().search([('employer_sdl_no', '=', self.employer_sdl_no)], limit=1)
        provider_vals = self.provider_vals_func()
        if existing_provider:
            self.is_existing_reg = True
            return True 
        else:
            return False

    def action_manager_approve(self, update=False):
        """Manager approves an SDF registration record, the actual SDF record is created in inseta.sdf model
        we will use the already generated user_id.partner_id
        as this will ensure SDF delegation inheritance will not create a new partner record
        """
        provider_vals = self.provider_vals_func()
        existing_provider = self.env['inseta.provider'].sudo().search([('employer_sdl_no', '=', self.employer_sdl_no)], limit=1)
        if not self.provider_status:
            raise ValidationError("Please set the Provider status!!!")
        if existing_provider:
            provider_vals = self.provider_vals_func()
            self.is_existing_reg = True
            provider_vals['partner_id'] = existing_provider.partner_id.id
            existing_provider.sudo().write(provider_vals)
            existing_provider.sudo().write({
                'skill_programmes_ids': [(0, 0, {'skill_programme_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.skill_programmes_ids],
                'learner_programmes_ids': [(0, 0, {'learner_programme_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.learner_programmes_ids],
                'unit_standard_ids': [(0, 0, {'unit_standard_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.unit_standard_ids],
                'qualification_ids': [(0, 0, {'qualification_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.qualification_ids],
                'provider_assessor_ids': [(0, 0, 
                    {
                    'provider_id': existing_provider.id,
                    'assessor_id': ass.id, 
                    'active': True,
                    }) for ass in self.assessor_ids],

                'provider_moderator_ids': [(0, 0, 
                    {
                    'provider_id': existing_provider.id,
                    'moderator_id': mod.id, 
                    'active': True,
                    }) for mod in self.moderator_ids],
                
                'provider_contact_person_ids': [(0, 0, 
                    {
                    'provider_id_main': existing_provider.id,
                    'name': delivery.contact_person_name,
                    'contact_person_surname': delivery.contact_person_surname,
                    'contact_person_tel': delivery.contact_person_tel,
                    'contact_person_cell': delivery.contact_person_cell,
                    'contact_person_fax': delivery.contact_person_fax,
                    'contact_person_email': delivery.contact_person_email,
                    'active': True,
                    }) for delivery in self.delivery_center_ids],

                })
                # return {'warning': {'title': 'Validation', 'message': 'A provider with same  SDL/ N No. already exists, click the update details button'}}
            
        else:
            provider = self.env['inseta.provider'].sudo().create(provider_vals)
            provider.sudo().write({
                'skill_programmes_ids': [(0, 0, {'skill_programme_id': pr.id, 'provider_id': provider.id, 'accreditation_id':self.id}) for pr in self.skill_programmes_ids],
                'learner_programmes_ids': [(0, 0, {'learner_programme_id': pr.id, 'provider_id': provider.id, 'accreditation_id':self.id}) for pr in self.learner_programmes_ids],
                'unit_standard_ids': [(0, 0, {'unit_standard_id': pr.id, 'provider_id': provider.id, 'accreditation_id':self.id}) for pr in self.unit_standard_ids],
                'qualification_ids': [(0, 0, {'qualification_id': pr.id, 'provider_id': provider.id, 'accreditation_id':self.id}) for pr in self.qualification_ids],
                'provider_assessor_ids': [(0, 0, 
                    {
                    'provider_id': provider.id,
                    'assessor_id': ass.id,
                    'active': True,
                    }) for ass in self.assessor_ids],

                'provider_moderator_ids': [(0, 0, 
                    {
                    'provider_id': provider.id,
                    'moderator_id': mod.id,
                    'active': True,
                    }) for mod in self.moderator_ids],
                
                'provider_contact_person_ids': [(0, 0, 
                    {
                    'provider_id_main': provider.id,
                    'name': cnt.name,
                    'contact_person_surname': cnt.contact_person_surname,
                    'contact_person_tel': cnt.contact_person_tel,
                    'contact_person_cell': cnt.contact_person_cell,
                    'contact_person_fax': cnt.contact_person_fax,
                    'contact_person_email': cnt.contact_person_email,
                    'active': True,
                    }) for cnt in self.provider_contact_person_ids],
                })
            group_approved_provider = self.env.ref("inseta_etqa.group_approved_provider")
            if not self.env.user.has_group("inseta_etqa.group_approved_provider"):
                provider.user_id.sudo().write({'groups_id': [(4, group_approved_provider.id)]})

    def update_existing_provider(self):
        pass 
        # existing_provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.employer_sdl_no)], limit=1)
        # if existing_provider:
        # 	provider_vals = self.provider_vals_func()
        # 	self.is_existing_reg = True
        # 	provider_vals['partner_id'] = existing_provider.partner_id.id
        # 	provider = existing_provider.update(provider_vals)
        # 	existing_provider.write({'skill_programmes_ids': [(0, 0, {'skill_programme_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.skill_programmes_ids],
        # 	'learner_programmes_ids': [(0, 0, {'learner_programme_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.learner_programmes_ids],
        # 	'unit_standard_ids': [(0, 0, {'unit_standard_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.unit_standard_ids],
        # 	'qualification_ids': [(0, 0, {'qualification_id': pr.id, 'provider_id': existing_provider.id, 'accreditation_id':self.id}) for pr in self.qualification_ids],
        # 	})
        # else:
        # 	return {'warning': {'title': 'Validation', 'message': 'There is no provider with SDL/ N No. existing in the system'}}

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.provider.accreditation')
        accreditation_number = self.env['ir.sequence'].next_by_code('inseta.provider.accreditation_number')
        vals['reference'] = sequence or '/'
        vals['accreditation_number'] = accreditation_number
        return super(ProviderAccreditation, self).create(vals)
 
