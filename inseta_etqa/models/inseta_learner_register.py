from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
import re
from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class LearnerRegister(models.Model):
    """This model holds the record of all SDF applications """

    _name = 'inseta.learner.register'
    _description = "Learner Registration"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    sataarea_code_id = fields.Char()
    employer_sdl = fields.Char(string='Employer SDL')
    employer_ids = fields.Many2many("inseta.organisation", 'inseta_learner_org_register_rel', 'inseta_learner_org_register_id', string='Employers IDs')
    moderator_id = fields.Many2one("inseta.moderator", 'Moderator ID')
    assessor_id = fields.Many2one("inseta.assessor", 'Assesssor ID')
    learner_id = fields.Many2one("inseta.learner", 'Learner ID')
    lpro_learner_wizard_id = fields.Many2one("inseta.lpro.register.learner.wizard", 'Learner Wizard ID')
    is_existing_reg = fields.Boolean('is Existing Provider?')
    compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], string="Evidence Compliance / Submitted", default="no", store=True)
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')

    provider_id = fields.Many2one("inseta.provider", 'Provider ID', default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])
    registration_no = fields.Char(string='Registration Number')
    image_512 = fields.Image("Image", max_width=512, max_height=512)
    reference = fields.Char(string='Reference')
    name = fields.Char(compute="_compute_name", store=True)
    user_id = fields.Many2one('res.users', string='Related User')
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    title = fields.Many2one('res.partner.title', string='Title', )
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Surname')
    middle_name = fields.Char(string='Middle Name')
    initials = fields.Char(string='Initials')
    birth_date = fields.Date(string='Birth Date')
    gender_id = fields.Many2one('res.gender', string='Gender')
    mobile = fields.Char(string='Cell Phone Number')
    phone = fields.Char(string='Telephone Number')
    fax_number = fields.Char(string='Fax Number')
    email = fields.Char(string='Email Address')
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref("base.za").id)	
    physical_code = fields.Char(string='Physical Code')
    physical_address1 = fields.Char(string='Physical Address Line 1')
    physical_address2 = fields.Char(string='Physical Address Line 2')
    physical_address3 = fields.Char(string='Physical Address Line 3')
    physical_suburb_id = fields.Many2one(
        'res.suburb', string='Physical Suburb')
    physical_city_id = fields.Many2one('res.city', string='Physical City')
    physical_municipality_id = fields.Many2one(
        'res.municipality', string='Physical Municipality')
    physical_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Physical Urban/Rural')
    physical_province_id = fields.Many2one(
        'res.country.state', string='Physical Province', domain=[('code', '=', 'ZA')])
    use_physical_for_postal_addr = fields.Boolean(
        string="Use physical address for postal address?")

    document_ids = fields.One2many("inseta.learner.document", "learner_document_id", string="Inseta Learner document")
    postal_code = fields.Char(string='Postal Code')
    postal_address1 = fields.Char(string='Postal Address Line 1')
    postal_address2 = fields.Char(string='Postal Address Line 2')
    postal_address3 = fields.Char(string='Postal Address Line 3')
    postal_suburb_id = fields.Many2one('res.suburb', string='Postal Suburb')
    postal_city_id = fields.Many2one('res.city', string='Postal City',)
    postal_municipality_id = fields.Many2one(
        'res.municipality', string='Postal Municipality')
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
    alternateid_type_id = fields.Many2one(
        'res.alternate.id.type', string='Alternate ID Type')
    
    id_no = fields.Char(string="Identification No")
    passport_no = fields.Char(string='Passport No')
    is_existing_reg = fields.Boolean(
        string='Existing Learner Registration', default=False)
    equity_id = fields.Many2one('res.equity', 'Equity')
    disability_id = fields.Many2one(
        'res.disability', string="Disability Status")
    home_language_id = fields.Many2one('res.lang', string='Home Language',)
    nationality_id = fields.Many2one('res.nationality', string='Nationality')
    citizen_resident_status_id = fields.Many2one(
        'res.citizen.status', string='Citizen Res. Status')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status')
    general_comments = fields.Text(string='General Comments')
    current_occupation = fields.Char(string='Current Occupation')
    occupation_years = fields.Integer(string='Years in Occupation')
    occupation_experience = fields.Char(string='Experience in Occupation')
    # comments = fields.Text(string='General Comments')
    # refusal_comment = fields.Text(string='Refusal Comments')
    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    highest_edu_desc = fields.Text('Highest Education Description')
    employed = fields.Boolean('Employed?')

    # workflow fields
    approval_date = fields.Date('Approval Date', readonly=True)
    rework_date = fields.Date('Rework Date', help="Date Requested the Rework")
    reworked_date = fields.Date('Reworked Date', help="Date Learner Sumbitted the Rework")
    rework_expiration_date = fields.Date('Rework Expiration Date', compute="_compute_rework_expiration", store=True)
    rework_comment = fields.Text()
    rejection_comment = fields.Text()
    rejection_date = fields.Date('Rejection Date', help="Date Admin Rejects Learner registraion")
    registration_date = fields.Datetime(
        'Registration Date', default=lambda self: fields.Datetime.now(), readonly=True)
    is_confirmed = fields.Boolean('Form submission Confirmed?')
    id_copy = fields.Binary(string='Upload ID')
    
    etqa_committee_ids = fields.Many2many(
        'res.users', 
        'etqa_committee_rel', 
        string='Evaluation Committee',
        help="Technical Field to compute eeval committees"
    )
    etqa_admin_ids = fields.Many2many(
        'res.users', 
        'etqa_admin_rel', 
        string='Evaluation Admin',
        help="Technical Field to compute eval admin"
    )
    # programmes_ids = fields.Many2many("inseta.programme", string='Programmes')
    skill_programmes_ids = fields.Many2many("inseta.skill.programme", string='Programmes')
    learner_programmes_ids = fields.Many2many("inseta.learner.programme",'learner_learner_programme_rel', string='Learnership Programmes')
    learner_unit_standard_assessment_ids = fields.One2many("inseta.learner.unit.standard.assessment", "learner_register_id", 'Unit Standard Assessments')
    
    learner_learnership_line = fields.Many2many("inseta.learner.learnership", 'inseta_learner_learnership_register', string='Learnership')
    skill_learnership_line = fields.Many2many("inseta.skill.learnership", 'inseta_skill_learnership_register', 'inseta_learner_register_id', 'inseta_skill_learnership_id', string='Skill Programme')
    qualification_learnership_line = fields.Many2many("inseta.qualification.learnership", 'inseta_qualification_learnership_register', 'inseta_learner_register_id', 'inseta_qualification_learnership_id', string='Qualification')
    internship_learnership_line = fields.Many2many("inseta.internship.learnership", 'inseta_internship_learnership_register', 'inseta_learner_register_id', 'inseta_internship_learnership_id', string='Internship')
    unit_standard_learnership_line = fields.Many2many("inseta.unit_standard.learnership", 'inseta_unit_standard_learnership_register', 'inseta_learner_register_id', 'inseta_unit_standard_learnership_id', string='Unit standards')
    bursary_learnership_line = fields.Many2many("inseta.bursary.learnership", 'inseta_bursary_learnership_register', 'inseta_learner_register_id', 'inseta_bursary_learnership_id', string='Bursary')
    wiltvet_learnership_line = fields.Many2many("inseta.wiltvet.learnership", 'inseta_wiltvet_learnership_register', 'inseta_learner_register_id', 'inseta_wiltvet_learnership_id', string='WIL(TVET)')
    candidacy_learnership_line = fields.Many2many("inseta.candidacy.learnership", 'inseta_candidacy_learnership_register', 'inseta_learner_register_id', 'inseta_candidacy_learnership_id', string='Candidacy')
    
    # new_field / might be out
    learner_programmes_line_ids = fields.One2many("inseta.learnership.assessment", 'inseta_learner_register', string='Learning programmes')
    skill_programmes_line_ids = fields.One2many("inseta.learnership.assessment", 'inseta_skill_register', string='Skill programmes')
    qualification_programmes_line_ids = fields.One2many("inseta.learnership.assessment", 'inseta_qualification_register', string='Qualification programmes')
    
    qualification_ids = fields.Many2many("inseta.qualification", 'inseta_learner_reg_qualification_rel', 'column1', string='Qualification')
    # discard 
    # qualification_programmes_ids = fields.Many2many("inseta.qualification.programme",'learner_qualification_programme_rel','inseta_learner_register_id', 'inseta_qualification_programme_id', string='Qualification Programmes')

    is_initial_update = fields.Boolean(
        help="Is set to True the first time the"
        "model is updated to trigger learner registration Mail automated action")
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('rework', 'Pending Additional Information'),
        ('rework_etqa_eval', 'Pending Additional Information'),
        ('evaluation', 'Validation'),
        ('queried', 'Queried/Rework'),
        ('pending_approval', 'Pending Approval'),
        ('awaiting_rejection', 'Request Rejection'), #if rework stays more than 10days, committe can request for rejection
        ('awaiting_rejection2', 'Awaiting Rejection'),
        ('done', 'Approved'),
        ('reject', 'Rejected')], default='draft', string="Status")

    popi_act_status_id = fields.Many2one(
        'res.popi.act.status', string='POPI Act Status')
    popi_act_status_date = fields.Date(string='POPI Act Status Date')
    nsds_target_id = fields.Many2one(
        'res.nsds.target', string='NSDS Target')
    funding_type = fields.Many2one('res.fundingtype', string='SFunding Type', required=False)
    # dgapplication_id = fields.Many2one('inseta.dgapplication')
    statssa_area_code_id = fields.Many2one('res.statssa.area.code', string='STATSSA code')
    school_emis_id = fields.Many2one('res.school.emis', string='School EMIS')
    last_school_year = fields.Many2one('res.last_school.year', string='Last school year')

    enrollment_status = fields.Selection([
        ('enrolled', 'Enrolled'), 
        ('unenrolled', 'Not-Enrolled'), 
        ], default='unenrolled', string="Status")

    gps_coordinates = fields.Char()
    active = fields.Boolean(default=True)
    latitude_degree = fields.Char(string='Latitude Degree')
    longitude_degree = fields.Char(string='Longitude Degree')
    scarcecritical_id  = fields.Many2one('res.dginternshipscarcecritical','Scarce & Critical Skills') #scarcecriticalskillsid
    organisation_id =  fields.Many2one('inseta.organisation', string='Organisation')
    test_purpose = fields.Boolean(default=False) # to be remove while on production 
    captured_from_lp = fields.Boolean(default=False) 

    
    # @api.constrains('learner_learnership_line', 'skill_learnership_line', 
    # 'qualification_learnership_line','internship_learnership_line', 'unit_standard_learnership_line',
    # 'bursary_learnership_line', 'wiltvet_learnership_line', 'candidacy_learnership_line')
    # def check_programme_lines(self):
    #     if not self.captured_from_lp:
    #         if self.learner_learnership_line or self.skill_learnership_line or self.qualification_learnership_line or \
    #         self.internship_learnership_line or self.unit_standard_learnership_line or self.bursary_learnership_line or \
    #         self.wiltvet_learnership_line or self.candidacy_learnership_line:
    #             pass
    #         else:
    #             raise ValidationError('Please register at least a programme for this learner') 

    @api.onchange('birth_date')
    def _onchange_birth_date(self):
        if self.birth_date:
            if self.birth_date > fields.Date.today():
                self.birth_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Birthday date cannot be greater than the today's date"
                    }
                }

                
    def drop_learner(self):
        pass 

    @api.onchange('alternateid_type_id')
    def onchange_alternateid_type_id(self):
        self.gender_id = False 
        self.id_no = False 
        self.birth_date = False

    @api.onchange('middle_name', 'first_name', 'last_name')
    def onchange_learner_name(self):
        if self.first_name:
            self.first_name = self.first_name.capitalize()
            self.initials = f'{self.first_name[0].capitalize()}{self.middle_name[0].capitalize() if self.middle_name else ""}'

        if self.middle_name:
            self.middle_name = self.middle_name.capitalize() 

        if self.first_name and self.last_name:
            self.last_name = self.last_name.capitalize()
            self.initials = f'{self.first_name[0].capitalize()}{self.middle_name[0].capitalize() if self.middle_name else ""}'

        if self.middle_name and self.first_name:
            m_initial = self.middle_name[0] 
            mname = self.middle_name.split(' ')
            if len(mname) > 1:
                m_initial += mname[1][0].capitalize()
            self.initials = f'{self.first_name[0].capitalize()}{m_initial.capitalize()}'

    @api.onchange('socio_economic_status_id')
    def onchange_socio_economic_status_id(self):
        if self.socio_economic_status_id:
            if self.socio_economic_status_id.name.startswith('E'):
                self.employed = True 
            else:
                self.employed = False

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
                return {'warning': {
                    'title':'Invalid input',
                    'message': "Physical Address Line 1 must be alpha number format  e.g 23 chris maduka street"
                    }}

    @api.onchange('first_name')
    def onchange_first_name(self):
        if self.first_name:
            if ' ' in self.first_name:
                self.first_name = False 
                return {'warning': {'title':'Invalid input','message': "First name must only contain a name"}}

    @api.onchange('phone','mobile','fax_number')
    def onchange_validate_number(self):
        if self.phone:
            if not self.phone.strip().isdigit() or len(self.phone) != 10:
                self.phone = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Phone number'}}
        if self.mobile:
            if not self.mobile.strip().isdigit() or len(self.mobile) != 10:
                self.mobile = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Cell phone number'}}
        if self.fax_number:
            if not self.fax_number.strip().isdigit() or len(self.fax_number) != 10:
                self.fax_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Fax number'}}
    
    @api.onchange('email')
    def onchange_validate_email(self):
        if self.email:
            # rematch_email = re.match("^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", self.email,re.IGNORECASE)
            # if rematch_email != None:
            if '@' not in self.email:
                self.email = ''
                return {'warning':{'title':'Invalid input','message':'Please enter a valid email address'}}
 
# --------------------------------------------
# compute Methods
# --------------------------------------------
    @api.depends(
        'first_name',
        'last_name',
        'middle_name')
    def _compute_name(self):
        for rec in self:
            middle_name = rec.middle_name if rec.middle_name else rec.initials
            rec.name = "{} {} {}".format(
                rec.first_name or '', middle_name or '', rec.last_name or '')

    @api.model
    def default_get(self, fields_list):
        res = super(LearnerRegister, self).default_get(fields_list)
        etqa_eval_committee, etqa_admin = self._get_group_users()
        res.update({
            'etqa_committee_ids': etqa_eval_committee,
            'etqa_admin_ids': etqa_admin,
        })
        return res
    
    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id

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
    # Onchange methods and overrides
    # --------------------------------------------
    @api.onchange("id_no")
    def _onchange_id_no(self):
        """Update gender and birth_date fields on validation of R.S.A id_no"""
        if self.id_no:
            id_number = self.id_no
            if not self.test_purpose:
                existing_learner = self.env['inseta.learner'].search([('id_no', '=', self.id_no)], limit=1)
                if existing_learner:
                    self.id_no = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"Learner with RSA No. {id_number} Already exists"
                        }
                    }
            if (not self.alternateid_type_id) or (self.alternateid_type_id.name.startswith('No')): # starts with None
                original_idno = self.id_no
                identity = validate_said(self.id_no)
                if not identity:
                    self.id_no = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"Invalid R.S.A Identification No. {original_idno}"
                        }
                    }
                # update date of birth with identity
                self.update({"birth_date": identity.get('dob'),
                            "gender_id": 1 if identity.get("gender") == 'male' else 2})			

    @api.onchange('physical_code')
    def _onchange_physical_code(self):
        if self.physical_code:
            if len(self.physical_code) != 4:
                self.clear_address()
                return {
                    'warning': {'title': 'Invalid', 'message': "Physical code must be up to 4 characters !!!"}
                }
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.physical_code)], limit=1)
            if sub:
                self.physical_suburb_id = sub.id
                self.physical_municipality_id = sub.municipality_id.id
                self.physical_province_id = sub.district_id.province_id.id
                self.physical_city_id = sub.city_id.id
                #self.nationality_id = sub.nationality_id.id
                self.physical_urban_rural = sub.municipality_id.urban_rural
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
        self.physical_urban_rural =False

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
            self.postal_urban_rural = self.physical_urban_rural
            self.postal_address1 = self.physical_address1
            self.postal_address2 = self.physical_address2
            self.postal_address3 = self.physical_address3
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

    def get_geolocation(self):
        # We need country names in English below
        for rec in self.with_context(lang='en_US'):
            result = self.env['res.partner']._geo_localize(
                rec.physical_address1,
                rec.physical_code,
                rec.physical_city_id.name,
                rec.physical_province_id.name,
                # rec.country_id.name
            )

            if result:
                rec.write({
                    'latitude_degree': result[0],
                    'longitude_degree': result[1],
                })
        return True

    def action_work_addr_map(self):
        street =  f"{self.physical_address1 or ''} {self.physical_address2 or ''} {self.physical_address3 or ''}"
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
        return {
            'type': 'ir.actions.act_url',
            'url':url,
            'target': 'new'
        }

    def action_validate_learner_document(self):
        view = self.env.ref('inseta_learning_programme.inseta_lpro_register_learner_wizard_form_view')
        view_id = view and view.id or False
        document_ids = []
        if self.learner_learnership_line:
            for line in self.learner_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]

        if self.skill_learnership_line:
            for line in self.skill_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]

        if self.bursary_learnership_line:
            for line in self.bursary_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]

        if self.candidacy_learnership_line:
            for line in self.candidacy_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]

        if self.wiltvet_learnership_line:
            for line in self.wiltvet_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]

        if self.internship_learnership_line:
            for line in self.internship_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]

        if self.unit_standard_learnership_line:
            for line in self.unit_standard_learnership_line:
                document_ids += [doc.id for doc in line.mapped('document_ids')]
        context = {
                    'default_action': 'doc_validity', 
                    'default_learner_register_id': self.id,
                    'default_document_validation': True,
                    'default_document_ids': [(6, 0, document_ids)],
                    }
        return {'name':'Dialog',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'res_model':'inseta.lpro.register.learner.wizard',
                    'views':[(view.id, 'form')],
                    'view_id':view.id,
                    'target':'new',
                    'context':context,
                }

    def unlink(self):
        for rec in self:
            if any([
                rec.learner_learnership_line, 
                rec.skill_learnership_line, 
                rec.qualification_learnership_line,
                rec.internship_learnership_line, 
                rec.unit_standard_learnership_line, 
                rec.bursary_learnership_line]):
                raise ValidationError('You can not delete record')
        return super(LearnerRegister, self).unlink()

# --------------------------------------------
# ORM Methods override
# --------------------------------------------
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.learner.register')
        if not vals.get('is_imported'):
            vals['reference'] = sequence or '/'
            vals['registration_no'] = sequence or '/'

        name = '{} {} {}'.format(vals.get('first_name'), vals.get(
            'middle_name'), vals.get('last_name'))
        vals['name'] = name
        # document_ids = vals.get('document_ids')
        # if not vals.get('if res.captured_from_lp'):
        # 	if not vals.get('document_ids'):
        # 		raise ValidationError('Please add all compulsory documents... ')
        # 	else:
        # 		document_names = ['Learnership Agreement', 'Certified ID copy', 'Certified copy of matric/ Qualification'
        # 		'Confirmation of Employment', 'POPI act consent',]
        # 		if len(document_ids) < len(document_names):
        # 			raise ValidationError('Compulsory documents not met')
        
        res = super(LearnerRegister, self).create(vals)

        # res.check_document_ids() 
        if res.captured_from_lp:
            res.action_manager_approve()
        return res

    # def write(self, vals):
    # 	if not vals.get('if res.captured_from_lp'):
    # 		document_ids = vals.get('document_ids')
    # 		if not document_ids:
    # 			raise ValidationError('Compulsory documents not met')

    # 	return super(LearnerRegister, self).write(vals)

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.reference, rec.name.title())
            arr.append((rec.id, name))
        return arr
# --------------------------------------------
# Business Logic
# -------------------------------------------- 
    def action_send_mail(self, with_template_id, email_items= None, email_from=None):
        '''Email_to = [lists of emails], Contexts = {Dictionary} '''
        email_to = (','.join([m for m in email_items])) if email_items else False
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', with_template_id)[1]         
        if template_id:
            ctx = dict()
            ctx.update({
                'default_model': 'inseta.learner.register',
                'default_res_id': self.id,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
            })
            template_rec = self.env['mail.template'].browse(template_id)
            if email_to:
                template_rec.write({'email_to': email_to})
            template_rec.with_context(ctx).send_mail(self.id, True)

    def check_document_ids(self):
        if self.state == "draft":
            error_item = []
            if not self.document_ids:
                raise ValidationError('Please add all compulsory documents')
            else:
                document_names = ['Learnership Agreement', 'Certified ID copy', 'Certified copy of matric/ Qualification'
                'Confirmation of Employment', 'POPI act consent']
                # required_docs = self.mapped('document_ids').filtered(lambda s: s.name not in document_names)
                if len([rec.id for rec in self.mapped('document_ids')]) < len(document_names):
                    raise ValidationError('Compulsory documents not met')
                
        if self.state == "evaluation":
            if not self.document_ids:
                raise ValidationError('Please add all compulsory documents')
            else:
                attachment_not_compliant = self.mapped('document_ids').filtered(lambda s: s.compliant != "yes")
                if attachment_not_compliant:
                    raise ValidationError('Attached document not compliant')

    def action_set_to_draft(self):
        self.state = 'draft'

    def check_programme_lines(self):
        if not self.captured_from_lp:
            if self.learner_learnership_line or self.skill_learnership_line or self.qualification_learnership_line or \
            self.internship_learnership_line or self.unit_standard_learnership_line or self.bursary_learnership_line or \
            self.wiltvet_learnership_line or self.candidacy_learnership_line:
                pass
            else:
                raise ValidationError('Please register at least a programme for this learner')

    def action_submit(self):
        # self.check_document_ids()
        self.check_programme_lines()
        self.activity_update()
        self.write({'state': 'evaluation'})

    def action_verify(self):
        """Evaluation Committee Verifies learners registration
        """     
        # self.check_document_ids()
        if self.compliant == "no":
            raise ValidationError('Please validate the compulsory document before verification')
        self.activity_update()
        self.write({'state': 'pending_approval'})

    def rework_registration(self, comment):
        """Evaluation Committee Verifies query Registration and ask learner to rework.
        This method is called from the rework wizard
        Args:
            comment (str): Reason for rework
        """
        if self.env.user.id in self.etqa_committee_ids.ids and self.state == "evaluation":
            self.write({
                'state': 'rework_etqa_eval', 
                'rework_comment': comment, 
            })
        elif self.env.user.id in self.etqa_admin_ids.ids and self.state == "pending_approval":
            self.write({
                'state': 'rework',
                'rework_comment': comment,
                'rework_date': fields.Date.today(),
            })

        else:
            raise ValidationError('Please ensure to belong to the group ETQA Evaluation committee and ETQA Admin')
        self.activity_update()

    def reject_registration(self, comment):
        """Admin rejects Learner registration.
        This method is called from the reject wizard

        Args:
            comment (str): Reason for rejection
        """
        self.write({
            'state': 'reject', 
            'rejection_comment': comment, 
            'rejection_date': fields.Date.today()
        })
        self.activity_update()

    def action_rework(self):
        return self.popup_notification(False, 'query') 

    def action_reject(self):
        return self.popup_notification(False, 'refusal') 

    def action_reject2(self):
        return self.popup_notification(False, 'refusal')

    def popup_notification(self, subject, action):
        self.write({'general_comments': ''})
        view = self.env.ref('inseta_etqa.inseta_etqa_reject_wizard_form_view')
        view_id = view and view.id or False
        context = {
                    'default_subject': subject, 
                    'default_date': fields.Date.today(),
                    'default_reference': self.id,
                    'default_action': action,
                    'default_model_name': self._name,
                    }
        return {'name':'Dialog',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'res_model':'inseta.etqa.main.wizard',
                    'views':[(view.id, 'form')],
                    'view_id':view.id,
                    'target':'new',
                    'context':context,
                } 

    def action_request_admin_rejection(self):
        """Submits to etqa admin for rejection
        if learner does not rework after 10 days
        """
        self.write({'state': 'awaiting_rejection2'})

    def action_learner_submit_rework(self):  # rework
        self.write({
            'state': 'evaluation', 
            'reworked_date': fields.date.today()}
        )
        self.activity_update()

    
    def learner_vals(self):
        vals = {
            # 'partner_id': self.user_id.partner_id.id,
            'user_id': self.user_id.id,
            'title': self.title.id, 
            'birth_date': self.birth_date, 
            'gender_id': self.gender_id.id, 
            'name': self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "initials": self.initials,
            'equity_id': self.equity_id.id, 
            'disability_id': self.disability_id.id, 
            'email': self.email, 
            'phone': self.phone, 
            'mobile': self.mobile,
            'fax_number': self.fax_number,
            'state_id': self.physical_province_id.id, 
            'home_language_id': self.home_language_id.id,
            'nationality_id': self.nationality_id.id, 
            'citizen_resident_status_id': self.citizen_resident_status_id.id, 
            'socio_economic_status_id': self.socio_economic_status_id.id,
            'physical_code': self.physical_code,
            'street': self.physical_address1, 
            'street2': self.physical_address2,
            'street3': self.physical_address3, 
            'physical_suburb_id': self.physical_suburb_id.id,
            'physical_city_id': self.physical_city_id.id, 
            'physical_municipality_id': self.physical_municipality_id.id, 
            'physical_urban_rural': self.physical_urban_rural,
            'city': self.physical_city_id.name,
            'postal_province_id': self.postal_province_id.id,
            "use_physical_for_postal_addr": self.use_physical_for_postal_addr,
            'postal_code': self.postal_code,
            'postal_address1': self.postal_address1, 
            'postal_address2': self.postal_address2,
            'postal_address3': self.postal_address3, 
            'postal_suburb_id': self.postal_suburb_id.id, 
            'postal_city_id': self.postal_city_id.id,
            'postal_urban_rural': self.postal_urban_rural, 
            'occupation_experience': self.occupation_experience, 
            'occupation_years': self.occupation_years, 
            'current_occupation': self.current_occupation, 
            'highest_edu_level_id': self.highest_edu_level_id.id,
            'scarcecritical_id': self.scarcecritical_id.id,
            "highest_edu_desc": self.highest_edu_desc,
            "general_comments": self.general_comments,
            'alternateid_type_id': self.alternateid_type_id.id, 
            'passport_no': self.passport_no,
            'id_no': self.id_no,
            'contact_type': 'learner', 
            'moderator_id': self.moderator_id.id,
            'provider_id': self.provider_id.id,
            'organisation_id': self.organisation_id.id,
            'employer_ids': self.employer_ids,
            'related_to': self.provider_id.user_id.id,
            'assessor_id': self.assessor_id.id,
            'id_copy': self.id_copy, 
            "approval_date": fields.Date.today(),
            "registration_date": self.registration_date,
            'skill_programmes_ids': self.skill_programmes_ids,
            'learner_programmes_line_ids': [(4, rec.id) for rec in self.learner_programmes_line_ids],
            'qualification_programmes_line_ids': [(4, rec.id) for rec in self.qualification_programmes_line_ids],
            'skill_programmes_line_ids': [(4, rec.id) for rec in self.skill_programmes_line_ids],
            'learner_learnership_line': [(4, rec.id) for rec in self.learner_learnership_line],
            'skill_learnership_line': [(4, rec.id) for rec in self.skill_learnership_line],
            'qualification_learnership_line': [(4, rec.id) for rec in self.qualification_learnership_line],
            'internship_learnership_line': [(4, rec.id) for rec in self.internship_learnership_line],
            'unit_standard_learnership_line': [(4, rec.id) for rec in self.unit_standard_learnership_line],
            'bursary_learnership_line': [(4, rec.id) for rec in self.bursary_learnership_line],
            'wiltvet_learnership_line': [(4, rec.id) for rec in self.wiltvet_learnership_line],
            'candidacy_learnership_line': [(4, rec.id) for rec in self.candidacy_learnership_line],
            'enrollment_status': 'enrolled',
            'popi_act_status_id': self.popi_act_status_id.id,
            'nsds_target_id': self.nsds_target_id.id,
            'statssa_area_code_id': self.statssa_area_code_id.id,
            'school_emis_id': self.school_emis_id.id,
            'last_school_year': self.last_school_year.id,
            'popi_act_status_date': self.popi_act_status_date,
            'state': 'done',
            'document_ids': self.document_ids,
        
        }
        return vals

    def action_manager_approve(self):
        """Manager approves an Learner registration record, the actual Learner record is created in inseta.learner model
        we will use the already generated user_id.partner_id
        as this will ensure Learner delegation inheritance will not create a new partner record
        """
        existing_record = self.env['inseta.learner'].sudo().search([('id_no', '=', self.id_no)], limit=1)
        if existing_record:
            self.is_existing_reg = True
            return ValidationError('Learner with ID No. Already existing in the system. Click the update button to update details')
        else:
            vals = self.learner_vals()
            learner = self.env['inseta.learner'].sudo().create(vals)
            provider_learner_obj = self.env['inseta.provider.learner']
            provider_learner_obj.create({
                'provider_id': self.provider_id.id,
                'learner_id': learner.id,
                'active': True,
            })
            self.sudo().write({'state': 'done', "approval_date": fields.Date.today(), 'learner_id': learner.id})
            self.activity_update()

    def update_existing_record(self, update=False):
        existing_record = self.env['inseta.learner'].sudo().search([('id_no', '=', self.id_no)], limit=1)
        if existing_record:
            vals = self.learner_vals()
            self.is_existing_reg = True
            self.state = 'done'
            vals['partner_id'] = existing_record.partner_id.id
            learner = existing_record.update(vals)
        else:
            return {'warning': {'title': 'Validation', 'message': 'There is no learner with ID No. existing in the system'}}

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(LearnerRegister, self)._message_auto_subscribe_followers(
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
        Args: template (str): email template
        """
        if template:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('inseta_etqa', template)[1]
            self.message_post_with_template(
                template_id, composition_mode='comment',
                model='inseta.learner.register', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )
            # raise ValidationError(template.name)

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        eval_committee_group, eval_admin_group = self._get_group_users()
        committe_user_login = [rec.login for rec in eval_committee_group]
        admin_user_login = [rec.login for rec in eval_admin_group]
        reciepient1 = [self.email,self.assessor_id.partner_id.email or '',self.moderator_id.partner_id.email or '']
        # send to registrants
        MAIL_TEMPLATE, MAIL_TEMPLATE2 = False, False
        if self.state == 'draft':
            MAIL_TEMPLATE = 'mail_template_notify_learner_moderator_and_assessor_after_reg'
            MAIL_TEMPLATE2 = 'mail_template_notify_committee_after_registration'
            self.action_send_mail(MAIL_TEMPLATE, reciepient1, None) 
            self.action_send_mail(MAIL_TEMPLATE2, committe_user_login, None) 

        if self.state == 'evaluation':
            MAIL_TEMPLATE = 'mail_template_notify_learner_moderator_and_assessor_after_evaluation'
            MAIL_TEMPLATE2 = 'mail_template_notify_etqa_admin_after_evaluation'
            self.action_send_mail(MAIL_TEMPLATE, reciepient1, None) 
            self.action_send_mail(MAIL_TEMPLATE2, admin_user_login, None) 

        if self.state == 'pending_approval':
            MAIL_TEMPLATE = 'mail_template_notify_learner_moderator_and_assessor_after_approval'
            self.action_send_mail(MAIL_TEMPLATE, reciepient1, None) 

        if self.state in ['rework', 'rework_etqa_eval']:
            #schedule an activity for rework expiration for user
            self.activity_schedule(
                'inseta_etqa.mail_act_learner_rework',
                user_id=self.user_id.id or self.env.user.id,
                date_deadline=self.rework_expiration_date)
            MAIL_TEMPLATE = 'mail_template_notify_learners_rework'
            MAIL_TEMPLATE2 = 'mail_template_notify_moderator_and_assessor_for_rework'
            self.action_send_mail(MAIL_TEMPLATE, reciepient1, None) 
            self.action_send_mail(MAIL_TEMPLATE2, None, None) 
         
        if self.state == 'reject':
            MAIL_TEMPLATE = 'mail_template_notify_learner_rejection'
            MAIL_TEMPLATE2 = 'mail_template_notify_moderators_and_assessors_after_rejection_sdf'
            self.action_send_mail(MAIL_TEMPLATE, reciepient1, None) 
            self.action_send_mail(MAIL_TEMPLATE2, None, None) 

        #unlink learner rework activity if rework is resubmitted
        self.filtered(lambda s: s.state in ('rework','evaluation', 'rework_etqa_eval')).activity_unlink(['inseta_etqa.mail_act_learner_rework'])
        self._message_post(MAIL_TEMPLATE) #notify sdf

        # self._message_post(MAIL_TEMPLATE2) #notify etqa admin and committees

    def action_print_appointment_letter(self):
        return self.env.ref('inseta_etqa.learner_appointment_letter_report').report_action(self)

    def action_print_reject_letter(self):
        return self.env.ref('inseta_etqa.learner_rejection_letter_report').report_action(self)

    def _get_group_users(self):
        group_obj = self.env['res.groups']
        etqa_users_group_id = self.env.ref('inseta_etqa.group_etqa_user').id
        etqa_eval_committee_group_id = self.env.ref('inseta_etqa.group_etqa_evaluating_committee').id
        etqa_admin_group_id = self.env.ref('inseta_etqa.group_etqa_evaluating_admin').id
        etqa_user = group_obj.browse([etqa_users_group_id])
        etqa_committee = group_obj.browse([etqa_eval_committee_group_id])
        etqa_admin = group_obj.browse([etqa_admin_group_id])

        etqa_committee_users, etqa_admin_users= False, False
        if etqa_committee:
            etqa_committee_users = etqa_committee.mapped('users')
        if etqa_admin:
            etqa_admin_users = etqa_admin.mapped('users') 
        return etqa_committee_users, etqa_admin_users


class ResLastSchoolYear(models.Model):
    _name = "res.last_school.year"
    _description = "Last School year"

    legacy_system_id = fields.Integer(string='Legacy System ID')
    name = fields.Char(string="Name")
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)