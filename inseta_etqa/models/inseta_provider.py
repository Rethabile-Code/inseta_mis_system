from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.addons.inseta_tools.converters import  dd2dms
import logging

_logger = logging.getLogger(__name__)


class providerUsers(models.Model):
    _name = 'inseta.provider.users'
    _descripiton = "users Linked to Provider"
    _rec_name = "user_id"
    _order= "id desc"

    """users Linked to Provider"""

    user_id = fields.Many2one("res.users", "User ID")
    provider_id = fields.Many2one("inseta.provider", 'Provider')
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean('Active', default=True)


class providerQualification(models.Model):
    _name = 'inseta.provider.qualification'
    _descripiton = "Provider qualification line"
    _rec_name = "accreditation_id"
    _order= "id desc"

    """This holds the qualifications of a provider - to be related to inseta.provider"""

    accreditation_id = fields.Many2one("inseta.provider.accreditation", 'Accreditation ID')
    qualification_id = fields.Many2one("inseta.qualification", 'Qualification')
    provider_id = fields.Many2one("inseta.provider", 'Provider')
    training_end_date = fields.Date('Training End date')
    certificate_number = fields.Char('Certificate Number')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer('Legacy System ID')


class providerlearnership(models.Model):
    _name = 'inseta.provider.learnership'
    _descripiton = "Provider learership line"
    _rec_name = "accreditation_id"
    _order= "id desc"
    """This holds the qualifications of a provider - to be related to inseta.provider"""

    accreditation_id = fields.Many2one("inseta.provider.accreditation", 'Accreditation ID')
    learner_programme_id = fields.Many2one('inseta.learner.programme',string="Learnership id")
    provider_id = fields.Many2one("inseta.provider", 'Provider')
    training_end_date = fields.Date('Training End date')
    certificate_number = fields.Char('Certificate Number')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer('Legacy System ID')


class providerUnitStandard(models.Model):
    _name = 'inseta.provider.unit_standard'
    _descripiton = "Provider us line"
    _rec_name = "accreditation_id"
    _order= "id desc"

    """This holds the qualifications of a provider - to be related to inseta.provider"""

    accreditation_id = fields.Many2one("inseta.provider.accreditation", 'Accreditation ID')
    unit_standard_id = fields.Many2one('inseta.unit.standard',string="Unit standard id")
    provider_id = fields.Many2one("inseta.provider", 'Provider')
    training_end_date = fields.Date('Training End date')
    certificate_number = fields.Char('Certificate Number')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer('Legacy System ID')


class providerQualification(models.Model):
    _name = 'inseta.provider.skill'
    _descripiton = "Provider skill line"
    _rec_name = "accreditation_id"
    _order= "id desc"
    """This holds the qualifications of a provider - to be related to inseta.provider"""

    accreditation_id = fields.Many2one("inseta.provider.accreditation", 'Accreditation ID')
    skill_programme_id = fields.Many2one('inseta.skill.programme', string="Skills programme")
    provider_id = fields.Many2one("inseta.provider", 'Provider')
    training_end_date = fields.Date('Training End date')
    certificate_number = fields.Char('Certificate Number')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer('Legacy System ID')
 

class InsetaProvider(models.Model):
    _name = 'inseta.provider'
    _description = "Inseta Provider"
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _rec_name = "name"
    _order= "id desc"
    
    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.employer_sdl_no, rec.name.title() if rec.name else "NO NAME")
            arr.append((rec.id, name))
        return arr
    
    def write(self, vals):
        res = super(InsetaProvider, self).write(vals)
        vals['edit_mode'] = False
        return res

    edit_mode = fields.Boolean(default=False)
    learner_ids = fields.Many2many('inseta.learner', 'inseta_provider_learner_rel', 'inseta_provider_id', 'inseta_learner_id', string="Learners")
    provider_learner_ids = fields.One2many('inseta.provider.learner', 'provider_id', string="Provider Learners")
    provider_status = fields.Many2one("inseta.provider.registration.status", 'Provider Status')
    provider_etqa_id = fields.Char(string='ETQA ID', default="595")
    is_existing_reg = fields.Boolean('is Existing Provider?')
    is_already_seta_member = fields.Boolean('Already Accredited by other SETA?')
    password = fields.Char(string='Password')
    vat_number = fields.Char(string='VAT Number')
    cell_phone = fields.Char(string='Cell Phone')
    bee_status = fields.Many2one('res.bee.status', string="BBBEEE")
    accreditation_ids = fields.Many2many('inseta.provider.accreditation', string="Accreditations")
    accreditation_history_ids = fields.One2many('inseta.provider.accredit_history', 'provider_id', string="Provider Accreditation History")

    # Might be existing before 
    campus_name = fields.Char(string='Campus Name')
    campus_phone = fields.Char(string='Campus phone')
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
    
    # provider_skill_accreditation_ids = fields.Many2many("inseta.accreditation.skill.line", 'provider_accreditation_skill_id', string='Skill Accreditations')
    # provider_learnership_accreditation_ids = fields.Many2many("inseta.accreditation.learnership.line", 'provider_accreditation_learnership_id', string='Learnership Accreditations')
    # provider_qualification_ids = fields.Many2many(
    #   'inseta.accreditation.qualification.line',
    #   'provider_accreditation_qualification_id', 
    #   'Qualification Accreditations', 
    # )

    accreditation_status = fields.Selection([
        ('Primary', 'Primary Provider'),
        ('secondary', 'Secondary Provider'),
    ], string='Accreditation Status', index=True, copy=False)

    assessor_ids = fields.Many2many("inseta.assessor", 'inseta_provider_assessor_id_rel', 'provider_id', 'column1', string='Assessors')
    facilitator_ids = fields.Many2many("inseta.assessor", 'inseta_provider_facilitator_ids_rel', 'provider_id','column1', string='Facilitators')
    moderator_ids = fields.Many2many("inseta.moderator", 'inseta_provider_moderator_ids_rel', 'provider_id', 'column1', string='Moderators')
    provider_assessor_ids = fields.One2many("inseta.provider.assessor", 'provider_id', string='Assessors')
    provider_moderator_ids = fields.One2many("inseta.provider.moderator", 'provider_id', string='Moderators')

    # assessor_ids = fields.One2many("inseta.assessor", 'provider_id', string='Assessors')
    # facilitator_ids = fields.One2many("inseta.assessor", 'provider_facilitator_id', string='Facilitator')
    # moderator_ids = fields.One2many("inseta.moderator", 'provider_id', string='Moderator')
     
    qualification_ids = fields.One2many("inseta.provider.qualification", 'provider_id',string="Qualifications")
    unit_standard_ids = fields.One2many("inseta.provider.unit_standard", 'provider_id', string="Qualification Unit Standard")
    skill_programmes_ids = fields.One2many("inseta.provider.skill",'provider_id', string='Programmes')
    learner_programmes_ids = fields.One2many("inseta.provider.learnership",'provider_id', string='Learnership Programmes')


    # skill_programmes_ids = fields.Many2many("inseta.skill.programme", string='Programmes')
    # learner_programmes_ids = fields.Many2many("inseta.learner.programme",'provider_rec_learner_programme_rel', string='Learnership Programmes')
    # qualification_ids = fields.Many2many("inseta.qualification", 'inseta_provider_qualification_rel', 'column1', string='Qualifications')
    # unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_provider_unit_standard_rel', 'column1', string='Unit standards')

    delivery_center_ids = fields.Many2many('inseta.delivery.center', 'provider_delivery_center_rel', 'column1', string="Delivery Center", ondelete="cascade")
    campus_details = fields.Text(string='Campus Details')
    business_lease_agreement = fields.Many2one('ir.attachment', string='Business lease agreement')
    accreditation_recommended = fields.Selection([('no', 'No'),('yes', 'Yes')], default="no", string="Accreditation recommended", store=False)
    site_visit_ids = fields.Many2many('inseta.provider.site.visit', 'provider_site_visit_rel', 'column1', string="Site visit", ondelete="cascade")
    account_business_solvency_letter = fields.Many2one('ir.attachment', string='BUSINESS ACCOUNTANT SOLVENCY LETTER')
    bank_account_confirmation = fields.Many2one('ir.attachment', string='')
    bbbeee_affidavit = fields.Many2one('ir.attachment', string='')
    business_occupational_certificate_report = fields.Many2one('ir.attachment', string='')
    it_servicing = fields.Many2one('ir.attachment', string='')
    programme_curriculum = fields.Many2one('ir.attachment', string='')
    learner_details_achievement_spreadsheet = fields.Many2one('ir.attachment', string='')
    linked_user_ids = fields.Many2many('res.users', 'link_users_rel', 'linked_user_id', 'user_id', string="Related User IDS", ondelete="cascade")
    provider_user_ids = fields.Many2many('inseta.provider.users', 'provider_users_rel', 'provider_user_id', 'provider_users_id', string="Provider User IDS", store=True)
    
    # @api.depends('provider_user_ids')
    # def compute_linked_users(self):
    #     for rec in self:
    #         users = []
    #         if rec.provider_user_ids:
    #             for prv_user in rec.provider_user_ids:
    #                 users.append(prv_user.user_id.id)
    #             rec.linked_user_ids = [(6, 0, users)]
    #         else:
    #             rec.linked_user_ids = False

    # Already exists in partner
    # gps_coordinates = fields.Char()
    # latitude_degree = fields.Char(string='Latitude Degree')
    # longitude_degree = fields.Char(string='Longitude Degree')

    # discard
    # qualification_programmes_idsx = fields.Many2many("inseta.qualification.programme",'provider_rec_qualification_programme_rel', 'inseta_provider_id', 'inseta_qualification_programme_id', string='Qualification Programmes')
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string='Related Partner', index=True, ondelete='cascade')
    # provider_document_ids = fields.Many2many('ir.attachment', string='Attachment IDs', required=True, index=True, ondelete='cascade')
    # provider_qualification_ids = fields.One2many("inseta.provider.qualification", 'provider_id', 'Provider Qualification IDs')
    trade_name = fields.Char(string='Trading As Name')
    legacy_system_id = fields.Integer('Legacy System ID')
    reference = fields.Char(string='Accreditation Reference') 
    organisation_sdf_id = fields.Many2one('inseta.sdf.organisation', string='Organisation SDF ID') 
    organisation_id = fields.Many2one('inseta.organisation', string='Organisation ID') 
    campus_mobile = fields.Char(string='Campus Cell Number')
    campus_fax = fields.Char(string='Campus Fax')
    number_staff_members = fields.Char(string='Number of full time staff members')
    certificate_number = fields.Char(string='Cert Number')
    certificate_date = fields.Date('Cert Date')
    saqa_id = fields.Char(string='Saqa ID')
    saqa_provider_code = fields.Char(string='SAQA Provider code')
    provider_type_id =fields.Many2one('res.provider.type', string='Provider type') # FASSET, QAP
    provider_class_id =fields.Many2one('res.provider.class', string='Provider Class')
    provider_category_id =fields.Many2one('res.provider.category', string='Provider Category')
    provider_accreditation_number = fields.Char(string='Accreditation number')
    sic_code = fields.Many2one('res.sic.code', string='Primary Focus') # MUST EXIST IN THE SYSTEM
    provider_approval_date = fields.Date(string='Provider Approval Date')
    provider_register_date = fields.Date(string='Provider Accreditation Date')
    provider_expiry_date = fields.Date(string='Provider Accreditation Date')
    
    provider_quality_assurance_id =fields.Many2one('inseta.quality.assurance', string='Quality Assurance Body id')
    end_date = fields.Date(string='DHET Registration End Date')
    start_date = fields.Date(string='DHET Registration Start Date')
    accreditation_end_date = fields.Date(string='Accreditation End Date')
    accreditation_start_date = fields.Date(string='Accreditation Start Date')
    #     General Business Information part1
    contact_person_ids = fields.Many2many('inseta.provider.contact', 'provider_contact_person_rel', 'column1', string="Contact Person")
    provider_contact_person_ids = fields.One2many('inseta.provider.contact', 'provider_id_main', string="Contact Person")
    contact_person_id = fields.Many2one('inseta.provider.contact', string="Contact Person")
    total_credits = fields.Integer('Total Credits')
    approval_date = fields.Date('Approval Date')
    
    is_rpl = fields.Boolean('Is RPL')
    islearning = fields.Boolean('is learning')
    ismixed_model_learning = fields.Boolean('Is Mixed model learning')
    is_learnerships = fields.Boolean('is learnerships')
    is_facilitated_distance = fields.Boolean('Is Facilitated Distance')
    is_facilitated_contact_delivery = fields.Boolean('Is Facilitated Contact delivery')

    tax_clearance_ids = fields.Many2many('ir.attachment', 'provider_tax_attachment_rel', 'column1', string="Tax clearance")
    qualification_certificate_copy_ids = fields.Many2many('ir.attachment', 'provider_cert_copy_attachment_rel', 'column1',string="Certificate copies of Qualifications")
    director_cv_ids = fields.Many2many('ir.attachment', 'provider_director_cv_attachment_rel', 'column1', string="Director CV")
    cipc_dsd_ids = fields.Many2many('ir.attachment', 'provider_cipc_attachment_rel', 'column1',string="CIPC /DSD")
    company_profile = fields.Many2one('ir.attachment', string='Company profile')
    company_organogram = fields.Many2one('ir.attachment',string='Organogram')
    appointment_letter = fields.Many2one('ir.attachment', string='Appointment Letter')
    proof_of_ownership = fields.Many2one('ir.attachment', string='Proof of Ownership')
    workplace_agreement = fields.Many2one('ir.attachment', string='Workplace agreement')
    skills_registration_letter = fields.Many2one('ir.attachment', string='skills Programme registration letter')
    learning_approval_report = fields.Many2one('ir.attachment', string='Learning Programme approval Report')
    referral_letter = fields.Many2one('ir.attachment', string='PRIMARY ETQA REFERRAL LETTER')
    quality_management_system = fields.Many2one('ir.attachment', string='Quality management system')
    qcto_referral_letter = fields.Many2one('ir.attachment', string='Qcto referral letter')
    primary_accreditation_letter = fields.Many2one('ir.attachment', string='Primary accreditation letter')
    registration_no = fields.Char(string='Registration Number')
    
    # provider_qualification_ids = fields.Many2many("inseta.accreditation.qualification.line", 'provider_accreditation_qualification_rel', 'provider_accreditation_qualification_id', string='Provider Qualification IDs')
    # provider_skill_accreditation_ids = fields.Many2many("inseta.accreditation.skill.line",'provider_accreditation_skill_rel', 'provider_accreditation_skill_id', string='Provider Skill IDs')
    # provider_learnership_accreditation_ids = fields.Many2many("inseta.accreditation.learnership.line",'provider_accreditation_learnership_rel', 'provider_accreditation_learnership_id', string='Provider Learnership IDs')
    # provider_unit_standard_ids = fields.Many2many("inseta.accreditation.unit_standard.line",'provider_accreditation_unit_standard_rel', 'provider_accreditation_unit_standards_id', string='Provider Unit standard IDs')
    # provider_qualification_ids = fields.One2many("inseta.accreditation.qualification.line", 'provider_accreditation_qualification_id', 'Provider Qualification IDs', compute="_compute_accreditation_qualification")
    
    provider_qualification_ids = fields.One2many("inseta.accreditation.qualification.line", 'provider_id', string='Provider Qualification IDs')
    provider_skill_accreditation_ids = fields.One2many("inseta.accreditation.skill.line",'provider_id', string='Provider Skill IDs')
    provider_learnership_accreditation_ids = fields.One2many("inseta.accreditation.learnership.line",'provider_id', string='Provider Learnership IDs')
    provider_unit_standard_ids = fields.One2many("inseta.accreditation.unit_standard.line",'provider_id', string='Provider Unit standard IDs')
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
    training_material_id = fields.Many2one('inseta.training.material', string='Training material') # MUST EXIST IN THE SYSTEM

    def action_add_amf_or_link_programme(self):
        view = self.env.ref('inseta_etqa.inseta_amf_wiz_main_view_form')
        view_id = view and view.id or False
        context = {
                    'default_reference': self.id,
                    }
        return {'name':'Add Moderator /Assessor/ Facilitator',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'res_model':'inseta.amf.wizard',
                    'views':[(view.id, 'form')],
                    'view_id':view.id,
                    'target':'new',
                    'context':context,
                }

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False

    @api.onchange('accreditation_end_date', 'provider_status')
    def onchange_accreditation_end_date(self):
        de_accreditated_status = self.env.ref('inseta_etqa.data_inseta_provider_regis_status5').id
        withdrawn_status = self.env.ref('inseta_etqa.data_inseta_provider_regis_status7').id
        accreditated_unsuccessful_status = self.env.ref('inseta_etqa.data_inseta_provider_regis_status8').id
        de_registered_status = self.env.ref('inseta_etqa.data_inseta_provider_regis_status10').id
        accreditated_provider_status = [
            de_accreditated_status,
            accreditated_unsuccessful_status,
            withdrawn_status,
            de_registered_status]
        if self.accreditation_end_date and self.provider_status:
            if self.provider_status.id not in accreditated_provider_status:#  and self.accreditation_end_date >= fields.Date.today():
                self.active = True
            else:
                self.active = False
        else:
            self.active = False
            
    def get_geolocation(self):
        # We need country names in English below
        for rec in self.with_context(lang='en_US'):
            result = self.env['res.partner']._geo_localize(
                rec.street,
                rec.street2,
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
 
    def action_print_certficate(self):   
        return self.env.ref('inseta_etqa.provider_certificate_report_2').report_action(self)

    def action_provider_history(self):
        accreditation_history = self.env['inseta.provider.accreditation'].sudo().search(['|', ('provider_id', '=', self.id), ('employer_sdl_no', '=', self.employer_sdl_no)])
        if accreditation_history:
            self.accreditation_ids = accreditation_history.ids
        else:
            raise ValidationError("No Accreditation found for the provider")

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

    @api.onchange('street')
    def onchange_street(self):
        if self.street:
            addr = self.street.split(' ')
            res = False 
            for txt in addr:
                if txt.isalpha():
                    res = True
                    break
            if not res:
                self.street = ''
                return {'warning': {'title':'Invalid input','message': "Physical Address Line 1 must be alpha number format e.g 23 chris maduka street"}}

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            if len(self.zip) != 4:
                self.clear_address()
                return {
                    'warning': {'title': 'Invalid', 'message': "Physical code must be up to 4 characters !!!"}
                }
            locals = self.env['res.suburb'].search(
                [('postal_code', '=', self.zip)], limit=1)
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
            self.postal_address1 = self.street
            self.postal_address2 = self.street2
            self.postal_address3 = self.street3
            self.postal_code = self.zip
        else:
            self.postal_municipality_id = False
            self.postal_suburb_id = False
            self.postal_province_id = False
            self.postal_city_id = False
            self.postal_address1 = False
            self.postal_address2 = False
            self.postal_address3 = False
            self.postal_code = False

    # def get_geolocation(self):
    #   # We need country names in English below
    #   for rec in self.with_context(lang='en_US'):
    #       result = self.env['res.partner']._geo_localize(
    #           rec.street,
    #           rec.zip,
    #           rec.physical_city_id.name,
    #           rec.physical_province_id.name,
    #           rec.country_id.name
    #       )

    #       if result:
    #           rec.write({
    #               'latitude_degree': result[0],
    #               'longitude_degree': result[1],
    #           })
    #   return True
         

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

    def see_related_learner(self):
        form_view_ref = self.env.ref("inseta_etqa.view_learner_form", False)
        tree_view_ref = self.env.ref("inseta_etqa.view_learner_tree", False)
        provider_learners = self.mapped('provider_learner_ids').filtered(lambda learner: learner.learner_id.id != False)
        related_provider_learners = self.mapped('provider_user_ids')
        related_learners = [] 
        for pro in related_provider_learners:
            providers = pro.provider_id.mapped('provider_learner_ids')
            related_learners = [rec.learner_id.id for rec in providers]
        learner_list = [rec.learner_id.id for rec in provider_learners] + related_learners
        if provider_learners:
            return {
                'domain': [('id', 'in', learner_list)],
                'name': "Provider Learners",
                'res_model': 'inseta.learner',
                'type': 'ir.actions.act_window',
                'views': [(tree_view_ref.id, 'tree'),(form_view_ref.id, 'form')],
            }
        else:
            raise ValidationError("No learners is related to this provider !!!")

class InsetaProviderSiteVisit(models.Model):
    _name = 'inseta.provider.site.visit'
    _description = "Provider site visit" 
    _order= "id desc"
    # _inherits = {'res.partner': 'partner_id'}
    
    name = fields.Char('Evaluator Name')
    visit_date = fields.Datetime('Site visit date')
    reasons = fields.Text(string='Reason')
    outcome = fields.Text(string='Outcomes')
    upload_document = fields.Binary(string='Upload report')
    data_name = fields.Char(string='File Name') 
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean(string='Active', default=True)
    complaint_non_complaint = fields.Selection([('compliant', 'Compliant'),('non_compliant', 'Non compliant')], default="", store=False)



class InsetaDeliveryCenter(models.Model):
    _name = 'inseta.delivery.center'
    _description = "Provider contacts"
    _rec_name = "provider_id"
    _order= "id desc"
    # _inherits = {'res.partner': 'partner_id'}
    
    provider_id = fields.Many2one('inseta.provider.accreditation')
    provider_id_main = fields.Many2one('inseta.provider')
    name = fields.Char(string='Campus Name')
    contact_person_name = fields.Char(string='First name')
    contact_person_surname = fields.Char(string='Surname')
    contact_person_tel = fields.Char(string='Telephone')
    contact_person_cell = fields.Char(string='Cell Phone')
    contact_person_fax = fields.Char(string='Fax')
    contact_person_email = fields.Char('Email Address')
    campus_email = fields.Char('Campus Email Address')
    campus_address = fields.Char('Campus Address')
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean(string='Active', default=True)


class InsetaProviderContact(models.Model):
    _name = 'inseta.provider.contact'
    _description = "Provider contacts"
    _rec_name = "provider_id"
    _order= "id desc"
    # _inherits = {'res.partner': 'partner_id'}
    
    provider_id = fields.Many2one('inseta.provider.accreditation')
    provider_id_main = fields.Many2one('inseta.provider')
    # partner_id = fields.Many2one('res.partner', string='Related Partner', required=False, index=True, ondelete='cascade')
    name = fields.Char(string='Contact Firstname', required=True)
    contact_person_surname = fields.Char(string='Surname')
    contact_person_designation = fields.Many2one('res.partner.title', string='Contact Person Designation / title')
    contact_person_tel = fields.Char(string='Telephone')
    contact_person_cell = fields.Char(string='Cell Phone')
    contact_person_fax = fields.Char(string='Fax')
    contact_person_email = fields.Char('Email Address', required=True)
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean(string='Active', default=True)



