from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError, AccessError
from odoo.addons.inseta_tools.validators import validate_said


class InsetaLearner(models.Model):
    _name = "inseta.learner"
    _description = "Learners table Related to res.partner"
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _order= "id desc"

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.id_no, rec.name.title() if rec.name else "NO NAME")
            arr.append((rec.id, name))
        return arr

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    edit_mode = fields.Boolean(default=True)

    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
    moderator_id = fields.Many2one("inseta.moderator", 'Moderator ID')
    assessor_id = fields.Many2one("inseta.assessor", 'Assesssor ID')
    provider_id = fields.Many2one("inseta.provider", 'Provider ID')
    employer_ids = fields.Many2many("inseta.organisation", 'inseta_learner_org_rel', 'inseta_learner_org_id', string='Employers IDs')
    learner_register_id = fields.Many2one('inseta.learner.register')
    id_copy = fields.Binary(string='Upload ID')
    registration_no = fields.Char(string='Registration Number')
    document_ids = fields.One2many("inseta.learner.document", "learner_document2_id", string="Inseta Learner document")
    

    # image_512 = fields.Image("Image", max_width=512, max_height=512)
    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, index=True, ondelete='cascade', help='Partner-related data of the learner')
    user_id = fields.Many2one('res.users', string='Related User')
    state = fields.Selection([('done','Approved'),('drop','Dropped'), ('reject','Rejected')], string="state")
    highest_edu_level_id = fields.Many2one('res.education.level', string='Highest Level Of Education') 
    highest_edu_desc =  fields.Text()
    occupational_group_id  = fields.Char() #TODO: Change to Many2one field. dbo.lkpofomajorgroup
    current_occupation = fields.Char(string='Current Occupation')
    occupation_years = fields.Char(string='Years in Occupation')
    occupation_experience = fields.Char(string='Experience in Occupation')

    has_completed_learnertraining = fields.Boolean('Has completed learner training?')
    has_requested_learnertraining  = fields.Boolean('Has Requested learner training?')
    accredited_trainingprovider_name = fields.Char('Accredited Training Provider')
    is_interested_in_communication = fields.Boolean('Is Interested in Communication?')
    employed = fields.Boolean('Employed?')
    related_to = fields.Many2one('res.users', string='Related User')
    general_comments = fields.Text()
    # learner_learnership_line = fields.Many2many("inseta.learner.learnership", 'inseta_learner_learnership_rel_id', string='Learnership')
    # skill_learnership_line = fields.Many2many("inseta.skill.learnership", 'inseta_skill_learnership_rel_id', string='Skill Programme')
    # qualification_learnership_line = fields.Many2many("inseta.qualification.learnership", 'inseta_qualification_learnership_rrel_id', string='Qualification')
    # internship_learnership_line = fields.Many2many("inseta.internship.learnership", 'inseta_internship_learnership_rel_id', string='Internship')
    # unit_standard_learnership_line = fields.Many2many("inseta.unit_standard.learnership", 'inseta_unit_standard_learnership_rel_id', string='Unit standards')
    # bursary_learnership_line = fields.Many2many("inseta.bursary.learnership", 'inseta_bursary_learnership_rel_id', string='Bursary')
    # wiltvet_learnership_line = fields.Many2many("inseta.wiltvet.learnership", 'inseta_wiltvet_learnership_rel_id', string='WIL(TVET)')
    # candidacy_learnership_line = fields.Many2many("inseta.candidacy.learnership", 'inseta_candidacy_learnership_rel_id', string='Candidacy')
    

    learner_learnership_line = fields.One2many("inseta.learner.learnership", 'learner_id', string='Learnership')
    skill_learnership_line = fields.One2many("inseta.skill.learnership", 'learner_id', string='Skill Programme')
    qualification_learnership_line = fields.One2many("inseta.qualification.learnership", 'learner_id', string='Qualification')
    internship_learnership_line = fields.One2many("inseta.internship.learnership", 'learner_id', string='Internship')
    unit_standard_learnership_line = fields.One2many("inseta.unit_standard.learnership", 'learner_id', string='Unit standards')
    bursary_learnership_line = fields.One2many("inseta.bursary.learnership", 'learner_id', string='Bursary')
    wiltvet_learnership_line = fields.One2many("inseta.wiltvet.learnership", 'learner_id', string='WIL(TVET)')
    candidacy_learnership_line = fields.One2many("inseta.candidacy.learnership", 'learner_id', string='Candidacy')

    skill_programmes_ids = fields.Many2many("inseta.skill.programme", string='Skills Programmes')
    # qualification_programmes_ids = fields.Many2many("inseta.qualification.programme",'learner_rec_qualification_programme_rel', string='Qualification Programmes')
    learner_programmes_ids = fields.Many2many("inseta.learner.programme",'learner_rec_learner_programme_rel', string='Learnership Programmes')
    
    reregistration_state = fields.Selection([('approve', 'Approved'),('decline','Declined')], 'Reregistration State')
    reregistration_date = fields.Datetime()
    registration_date = fields.Datetime()
    approval_date = fields.Date()
    current_occupation = fields.Char(string='Current Occupation')
    occupation_experience = fields.Char(string='Experience in Occupation')
    learner_certificate = fields.Binary(string="Upload learner Certificate")
    code_of_conduct = fields.Binary(string="Code of Conduct")

    # learner organisation
    organisation_id =  fields.Many2one('inseta.organisation', string='Organisation')

    # Added new fields 
    legacy_system_id = fields.Integer(string='Legacy System ID')
    is_imported = fields.Boolean(string="Is Imported") # used to avoid auto generating reference sequence 

    popi_act_status_id = fields.Many2one(
        'res.popi.act.status', string='POPI Act Status')

    popi_act_status_date = fields.Date(string='POPI Act Status Date')

    nsds_target_id = fields.Many2one(
        'res.nsds.target', string='NSDS Target')
    statssa_area_code_id = fields.Many2one('res.statssa.area.code', string='SataArea code')
    school_emis_id = fields.Many2one('res.school.emis', string='School EMIS')
    enrollment_status = fields.Selection([
        ('enrolled', 'Enrolled'), 
        ('unenrolled', 'Not-Enrolled'), 
        ], default='unenrolled', string="Status")
    last_school_year = fields.Many2one('res.last_school.year', string='Last school year')
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
    scarcecritical_id  = fields.Many2one('res.dginternshipscarcecritical','Scarce & Critical Skills') #scarcecriticalskillsid
    
    # learner_learnership_line = fields.Many2many("inseta.learner.learnership", 'learner_id0', string='Learner Learnership IDs')
    # skill_learnership_line = fields.Many2many("inseta.skill.learnership", 'learner_id1', string='Skill IDs')
    # qualification_learnership_line = fields.Many2many("inseta.qualification.learnership", 'learner_id2', string='Qualification IDs')
    
    # consider removing
    learner_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learner_assessement_learn_rel', 'inseta_learner_assessement_learn_id', string='Learnership Assessment')
    skill_programmes_line_ids = fields.Many2many("inseta.learnership.assessment",'inseta_learner_assessement_skill_rel', 'inseta_learner_assessement_skill_id', string='Skill Assessment')
    qualification_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learner_assessement_qual_rel', 'inseta_learner_assessement_qual_id', string='Qualification Assessment')
 
    # assessment 
    # learner_assessment_lines = fields.Many2many("inseta.learnership.assessment", 'inseta_learner_assessement_line_rel', 'inseta_learner_assessement_line_id', string='Learner Assessment')
    
    learner_assessment_lines = fields.One2many("inseta.learnership.assessment", 'learner_id', string='Learner Assessment(s)')
    learner_unit_standard_assessment_ids = fields.One2many("inseta.learner.unit.standard.assessment", "learner_id", 'Unit Standard Assessments')

    learnership_assessment_line = fields.One2many('inseta.learner_learnership.assessment', 'learner_id', string='Learnership Assessment Line')	
    qualification_assessment_line = fields.One2many('inseta.learner_qualification.assessment', 'learner_id', string='Qualification Assessment Line')	
    skill_assessment_line = fields.One2many('inseta.skill_learnership.assessment', 'learner_id', string='Skills Assessment Line')	
    unit_standard_assessment_line = fields.One2many('inseta.unit_standard.assessment', 'learner_id', string='Unit Standard Assessment Line')	
    learner_assessment_line_ids = fields.One2many('inseta.learner.assessment.detail', 'learner', string='Learner Assessment Line')	

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
                rec.write({
                    'latitude_degree': result[0],
                    'longitude_degree': result[1],
                })
        return True

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

    @api.onchange('street')
    def onchange_physical_address1(self):
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

    # @api.onchange('alternateid_type_id')
    # def onchange_alternateid_type_id(self):
    #     self.gender_id = False 
    #     # self.id_no = False
    #     self.birth_date = False 

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
    @api.onchange(
        'first_name',
        'last_name',
        'middle_name')
    def _compute_name(self):
        for rec in self:
            middle_name = rec.middle_name if rec.middle_name else rec.initials
            rec.name = "{} {} {}".format(
                rec.first_name or '', middle_name or '', rec.last_name or '')

    # --------------------------------------------
    # Onchange methods and overrides
    # --------------------------------------------
    # @api.onchange("id_no")
    # def _onchange_id_no(self):
    #     """Update gender and birth_date fields on validation of R.S.A id_no"""
    #     if self.id_no:
    #         existing_learner = self.env['inseta.learner'].search([('id_no', '=', self.id_no)], limit=1)
    #         identity = validate_said(self.id_no)
    #         if existing_learner:
    #             self.id_no = False
    #             return {
    #                 'warning': {
    #                     'title': "Validation Error!",
    #                     'message': "Learner with RSA No. Already exists"
    #                 }
    #             }
    #         if (not self.alternateid_type_id) or (self.alternateid_type_id.name.startswith('Non')): # starts with None
    #             original_idno = self.id_no
    #             if not identity:
    #                 self.id_no = False
    #                 self.gender_id = False
    #                 self.birth_date = False
    #                 return {
    #                     'warning': {
    #                         'title': "Validation Error!",
    #                         'message': "Invalid R.S.A Identification No."
    #                     }
    #                 }
    #             # update date of birth with identity
    #             self.update({"birth_date": identity.get('dob'),
    #                         "gender_id": 1 if identity.get("gender") == 'male' else 2})

    #         elif identity and self.alternateid_type_id:
    #             self.alternateid_type_id = False 
    #             self.update({"birth_date": identity.get('dob'),
    #                         "gender_id": 1 if identity.get("gender") == 'male' else 2})

    @api.onchange("id_no")
    def _onchange_id_no(self):
        """Update gender and birth_date fields on validation of R.S.A id_no"""
        if self.id_no:
            existing_learner = self.env['inseta.learner'].search([('id_no', '=', self.id_no)], limit=1)
            identity = validate_said(self.id_no)
            id_number = self.id_no
            if existing_learner:
                self.id_no = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Learner with RSA {id_number}. Already exists"
                    }
                }
            if not identity:
                if self.alternateid_type_id:
                    # if self.alternateid_type_id.name.startswith('Non'):
                    self.gender_id, self.birth_date, self.id_copy = False,  False, False
                elif (not self.alternateid_type_id) or (self.alternateid_type_id.name.startswith('Non')): # starts with None
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': "Invalid R.S.A Identification No."
                        }
                    }

            else:
                self.alternateid_type_id = False
                self.id_copy = False
                self.update({
                        "birth_date": identity.get('dob'), 
                        "gender_id": 1 if identity.get("gender") == 'male' else 2
                        })


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

    def drop_learner(self):
        self.active = False
        

    # def _message_get_suggested_recipients(self):
    # 	recipients = super(InsetaLearner, self)._message_get_suggested_recipients()
    # 	try:
    # 		for rec in self:
    # 			if rec.partner_id:
    # 				rec._message_add_suggested_recipient(recipients, partner=rec.partner_id, reason=_('Learner'))
    # 	except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
    # 		pass
    # 	return recipients







