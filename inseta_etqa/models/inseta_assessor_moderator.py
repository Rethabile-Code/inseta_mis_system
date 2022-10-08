from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)

class InsetaFacilitator(models.Model):
    _inherit = 'inseta.sdf'

    provider_id = fields.Many2one('inseta.provider', domain=lambda act: [('active', '=', True)])


class AssessorRegistrationStatus(models.Model):
	_name = 'inseta.assessor.reg.status'
	_description = "Status"

	name = fields.Char('Name')
	code = fields.Char('Code')
	legacy_system_id = fields.Integer('Legacy System ID')
	active = fields.Boolean(string='Active', default=True)


class ModeratorRegistrationStatus(models.Model):
	_name = 'inseta.moderator.reg.status'
	_description = "training material"

	name = fields.Char('Name')
	code = fields.Char('Code')
	legacy_system_id = fields.Integer('Legacy System ID')
	active = fields.Boolean(string='Active', default=True)


class InsetaAssessorQualification(models.Model):
    _name = 'inseta.assessor.qualification'
    _description = "Inseta Assessor"

    assessor_id = fields.Many2one('inseta.assessor')
    assessment_date = fields.Date(string="Assessment date")
    qualification_id = fields.Many2one('inseta.qualification',string="Qualification")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")


class InsetaAssessorLearenr(models.Model):
    _name = 'inseta.assessor.learner.programme'
    _description = "Inseta Assessor"

    assessor_id = fields.Many2one('inseta.assessor')
    assessment_date = fields.Date(string="Assessment date")
    learner_programme_id = fields.Many2one('inseta.learner.programme',string="Learnership id")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")


class InsetaAssessoUnitStandard(models.Model):
    _name ="inseta.assessor.unit.standard"
    _description = "Inseta Assessor US"

    assessor_id = fields.Many2one('inseta.assessor')
    assessment_date = fields.Date(string="Assessment date")
    unit_standard_id = fields.Many2one('inseta.unit.standard',string="Unit standard id")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")


class InsetaAssessorSkill(models.Model):
    _name = 'inseta.assessor.skill.programme'
    _description = "Inseta Assessor"

    assessor_id = fields.Many2one('inseta.assessor')
    assessment_date = fields.Date(string="Assessment date")
    skill_programme_id = fields.Many2one('inseta.skill.programme', string="Skills programme")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")
 

class InsetamoderatorQualification(models.Model):
    _name = 'inseta.moderator.qualification'
    _description = "Inseta moderator"

    moderator_id = fields.Many2one('inseta.moderator', domain=lambda act: [('active', '=', True)])
    assessment_date = fields.Date(string="Assessment date")
    qualification_id = fields.Many2one('inseta.qualification',string="Qualification")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")

class InsetamoderatorrLearenr(models.Model):
    _name = 'inseta.moderator.learner.programme'
    _description = "Inseta moderator"

    moderator_id = fields.Many2one('inseta.moderator')
    assessment_date = fields.Date(string="Assessment date")
    learner_programme_id = fields.Many2one('inseta.learner.programme',string="Learnership id")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")


class InsetamoderatorUnitStandard(models.Model):
    _name ="inseta.moderator.unit.standard"
    _description = "Inseta moderator US"

    moderator_id = fields.Many2one('inseta.moderator')
    assessment_date = fields.Date(string="Assessment date")
    unit_standard_id = fields.Many2one('inseta.unit.standard',string="Unit standard id")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")


class InsetamoderatorSkill(models.Model):
    _name = 'inseta.moderator.skill.programme'
    _description = "Inseta moderator"

    moderator_id = fields.Many2one('inseta.moderator')
    assessment_date = fields.Date(string="Assessment date")
    skill_programme_id = fields.Many2one('inseta.skill.programme', string="Skills programme")
    active = fields.Boolean(string="active", default=True)
    legacy_system_id = fields.Integer(string="Legacy system id")
 

class InsetaAssessor(models.Model):
    _name = 'inseta.assessor'
    _description = "Inseta Assessor"
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _order= "id desc"
    _rec_name = "name"

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.id_no, rec.name.title() if rec.name else "NO NAME")
            arr.append((rec.id, name))
        return arr

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False

    edit_mode = fields.Boolean(default=False)
    assessor_status = fields.Many2one("inseta.assessor.reg.status", 'Assessor Status')
    provider_assessor_ids = fields.One2many('inseta.provider.assessor', 'assessor_id', string="Provider Assessors IDS", store=True, ondelete='cascade')

    code_of_conduct = fields.Many2one('ir.attachment', string="Code of conduct")
    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, index=True, ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    provider_facilitator_id = fields.Many2one('inseta.provider')
    is_approved = fields.Boolean('Approved', default=False)
    registration_number = fields.Char('Registration Number')
    legacy_system_id = fields.Integer(string='Legacy System ID')
    assessment_date = fields.Date('Assessment Date')
    approval_date = fields.Date('Approval Date')
    denied_date = fields.Date('Denial Date')
    query_date = fields.Date('Query Date')
    assessor_id = fields.Many2one('inseta.assessor', 'Assessor ID')
    etdp_registration_number = fields.Char(string='ETPD SETA Reg Number')
    statement_number = fields.Char(string='Statemement Number')
    person_type_id =fields.Many2one('res.person.type', string='Assessor type') # FASSET, QAP
    end_date = fields.Date(string='ETPD Registration End Date')
    start_date = fields.Date(string='ETPD Registration Start Date')
    statement_date = fields.Date(string='Statement Date')
    # The expiry reminder field is to indicate that a reminder have been set
    expiry_reminder_sent = fields.Boolean('Expiry Reminder Sent', default=False)
    is_permanent_consultant = fields.Boolean(string='Permanent consultant?')
    work_zip_code = fields.Char(string='Work Zip code')
    organization_sdl_no = fields.Char(string='Organization SDL Number')
    assessor_sla_document = fields.Many2one('ir.attachment', string="Assessor SLA Document")
    qualification_document_ids = fields.Many2many('ir.attachment', 'qualification_ids_rel2', 'qualification_column_id', string="Qualification Documents")
    statement_of_result_ids = fields.Many2many('ir.attachment', 'statement_ids_rel2', 'statement_column_id', string="Statement of results")
    additional_document_ids = fields.Many2many('ir.attachment', 'additional_ids_rel2', 'additional_column_id',string="Additional Documents")
    cv_ids = fields.Many2many('ir.attachment', 'cv_ids_rel2', 'cv_column_id', string="CVs")
    id_document_ids = fields.Many2many('ir.attachment', 'identity_ids_rel2', 'identity_column_id', string="ID Docments")
    qualification_ids = fields.One2many("inseta.assessor.qualification", 'assessor_id',string="Qualifications")
    unit_standard_ids = fields.One2many("inseta.assessor.unit.standard", 'assessor_id', string="Qualification Unit Standard")
    skill_programmes_ids = fields.One2many("inseta.assessor.skill.programme",'assessor_id', string='Programmes')
    learner_programmes_ids = fields.One2many("inseta.assessor.learner.programme",'assessor_id', string='Learnership Programmes')

    # new fields
    bank_name = fields.Char(string='Bank Name')
    branch_code = fields.Char(string='Branch Code')
    provider_code = fields.Char(string='Provider Code', size=20)
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, domain=lambda act: [('active', '=', True)])
    filler01 = fields.Char(string='Filler01', size=2)
    filler02 = fields.Char(string='Filler02', size=10)
    bank_account_number = fields.Char(string='Bank Account Number')
    job_title = fields.Char(string='Job Title')

    person_home_province_code = fields.Many2one('res.country.state', string='Province Code')
    person_postal_province_code = fields.Many2one('res.country.state', string='Province Province Code')
    organisation = fields.Many2one('res.partner', string='Organisation')
    country_home = fields.Many2one('res.country', string='Country')
    country_postal = fields.Many2one('res.country', string='Country')
    
    department = fields.Char(string='Department')
    coach_id = fields.Many2one('hr.employee', string='Coach')
    popi_act_status_id = fields.Many2one(
        'res.popi.act.status', string='POPI Act Status')
    popi_act_status_date = fields.Date(string='POPI Act Status Date')
    last_school_year = fields.Many2one('res.last_school.year', string='Last school year')

    nsds_target_id = fields.Many2one(
        'res.nsds.target', string='NSDS Target')
    funding_type = fields.Many2one('res.fundingtype', string='SFunding Type', required=False)
    # dgapplication_id = fields.Many2one('inseta.dgapplication')
    statssa_area_code_id = fields.Many2one('res.statssa.area.code', string='STATSSA code')
    school_emis_id = fields.Many2one('res.school.emis', string='School EMIS')
    
    @api.onchange('end_date')
    def onchange_accreditation_end_date(self):
        if self.end_date:
            if self.end_date >= fields.Date.today():
                self.active = True
            else:
                self.active = False
        else:
            self.active = False

    def action_work_addr_map(self):
        street =  f"{self.street or ''} {self.street2 or ''} {self.street3 or ''}"
        city = self.physical_city_id
        state = self.state_id
        country = self.country_id
        zip = self.zip
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
                rec.zip,
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

    @api.onchange('phone','mobile','fax_number')
    def onchange_validate_number(self):
        
        if self.phone:
            if not self.phone.strip().isdigit() or len(self.phone) != 10:
                self.phone = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Phone number'}}
        if self.mobile:
            if not self.mobile.strip().isdigit() or len(self.mobile) != 10:
                self.cell_phone_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Cell phone number'}}
        if self.fax_number:
            if not self.fax_number.strip().isdigit() or len(self.fax_number) != 10:
                self.fax_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Fax number'}}
    
    @api.onchange('end_date')
    def _onchange_end_date(self):
        end_date = self.end_date	 
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                self.end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.start_date}"
                    }
                }

    @api.onchange('email')
    def onchange_validate_email(self):
        if self.email: 
            if '@' not in self.email:
                self.email = ''
                return {'warning':{'title':'Invalid input','message':'Please enter a valid email address'}}

    @api.onchange("id_no")
    def _onchange_id_no(self):
        """Update gender and birth_date fields on validation of R.S.A id_no"""
        if self.id_no:
            existing_record = self.env['inseta.assessor'].search([('id_no', '=', self.id_no)], limit=1)
            if existing_record:
                self.id_no = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Assessor with RSA No. {self.id_no} already exists"
                    }
                }
            if not self.alternateid_type_id:
                original_idno = self.id_no
                identity = validate_said(self.id_no)
                if not identity:
                    self.id_no = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"Invalid Identification No. {original_idno}"
                        }
                    }
                # update date of birth with identity
                self.update({"birth_date": identity.get('dob'),
                            "gender_id": 1 if identity.get("gender") == 'male' else 2})

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.zip)], limit=1)
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
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.postal_code)], limit=1)
            if sub:
                self.postal_suburb_id = sub.id
                self.postal_municipality_id = sub.municipality_id.id
                self.postal_province_id = sub.district_id.province_id.id
                self.postal_city_id = sub.city_id.id
                #self.nationality_id = sub.nationality_id.id
                self.postal_urban_rural = sub.municipality_id.urban_rural

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
                return {'warning': {'title':'Invalid input','message': "Physical Address Line 1 must be alpha number format e.g 23 Abres street"}}

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
            self.postal_code = self.zip
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

    def action_send_mail(self, with_template_id, email_items, email_from=None, contexts=None):
        '''Email_to = [lists of emails], Contexts = {Dictionary} '''
        ids = self.id
        subject = contexts.get('subject', '') if contexts else False
        body = contexts.get('body_context', '') if contexts else False
        email_ctx = contexts.get('email_from', '') if contexts else False
        email_from = email_ctx if not email_from else email_ctx
        addressed_to = contexts.get('addressed_to', '') if contexts else False
        subject = subject if subject else 'Notification Message'
        email_to = (','.join([m for m in email_items]))
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', with_template_id)[1]         
        if template_id:
            ctx = dict()
            ctx.update({
                'default_model': 'inseta.assessor',
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

    def send_reminder_mail(self):
        email_from = '"INSETA"registrations@inseta.org.za'
        contact_email = [self.email]
        template = 'email_template_notify_assessor_for_expiry' # TODO
        self.action_send_mail(self, contact_email, email_from, template, None)

    def send_reminder_mail(self, warning_mail=True):
        email_from = '"INSETA"registrations@inseta.org.za'
        contact_email = [self.email]
        warning_template = 'email_template_notify_assessor_for_expiry' 
        expiry_template = 'email_template_notify_assessor_moderator_for_expiry'
        template = warning_template if warning_mail else expiry_template
        self.action_send_mail(self, contact_email, email_from, template, None)
        self.write({'expiry_reminder_sent': True})

    def _cron_expiry_reminder_method(self):
        for rec in self:
            if self.approval_date < self.end_date:
                """check if the difference between now and approval date is up to 3 years, """ 
                now = datetime.now()
                start_dt = datetime.strptime(rec.approval_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                diff = now - start_dt
                days = int(diff.days)
                if days in range (1000, 1095): # Three months before the 3 years
                    rec.send_reminder_mail(True)
                elif days > 1095:
                    rec.send_reminder_mail(False)

    def action_print_certficate(self):   
        return self.env.ref('inseta_etqa.assessor_certificate_report_2').report_action(self)


class InsetaModerator(models.Model):
    _name = 'inseta.moderator'
    _description = "Inseta moderator"
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _rec_name = "name"
    _order= "id desc"
    
    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.id_no, rec.name.title())
            arr.append((rec.id, name))
        return arr
    
    # def write(self, val):
    # 	res = super(InsetaAssessor, self).write(vals)
    # 	self.edit_mode = False
    # 	return res 

    edit_mode = fields.Boolean(default=False)
    provider_moderator_ids = fields.One2many('inseta.provider.moderator', 'moderator_id', string="Provider Moderator IDS", store=True, ondelete='cascade')

    moderator_status = fields.Many2one("inseta.moderator.reg.status", 'Moderator Status')
    code_of_conduct = fields.Many2one('ir.attachment', string="Code of conduct")
    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, index=True, ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    is_approved = fields.Boolean('Approved', default=False)
    registration_number = fields.Char('Registration Number')
    legacy_system_id = fields.Integer(string='Legacy System ID')
    assessment_date = fields.Date('Assessment Date')
    approval_date = fields.Date('Approval Date')
    denied_date = fields.Date('Denial Date')
    query_date = fields.Date('Query Date')
    etdp_registration_number = fields.Char(string='ETPD SETA Reg Number')
    statement_number = fields.Char(string='Statemement Number')
    person_type_id =fields.Many2one('res.person.type', string='Moderator type') # FASSET, QAP
    end_date = fields.Date(string='ETPD Registration End Date')
    start_date = fields.Date(string='ETPD Registration Start Date')
    statement_date = fields.Date(string='Statement Date')
    expiry_reminder_sent = fields.Boolean('Expiry Reminder Sent', default=False)
    is_permanent_consultant = fields.Boolean(string='Permanent consultant?')
    work_zip_code = fields.Char(string='Work Zip code')
    organization_sdl_no = fields.Char(string='Organization SDL Number')
    moderator_sla_document = fields.Many2one('ir.attachment', string="Moderator SLA Document")
    qualification_document_ids = fields.Many2many('ir.attachment', 'moderator_qualification_ids_rel2', 'qualification_column_id', string="Qualification Documents")
    statement_of_result_ids = fields.Many2many('ir.attachment', 'moderator_statement_ids_rel2', 'statement_column_id', string="Statement of results")
    additional_document_ids = fields.Many2many('ir.attachment', 'moderator_additional_ids_rel2', 'additional_column_id',string="Additional Documents")
    cv_ids = fields.Many2many('ir.attachment', 'moderator_cv_ids_rel2', 'cv_column_id', string="CVs")
    id_document_ids = fields.Many2many('ir.attachment', 'moderator_identity_ids_rel2', 'identity_column_id', string="ID Docments")
    moderator_id = fields.Many2one('inseta.moderator', 'Moderator ID')
    qualification_ids = fields.One2many("inseta.moderator.qualification", 'moderator_id',string="Qualifications")
    unit_standard_ids = fields.One2many("inseta.moderator.unit.standard", 'moderator_id', string="Unit Standard")
    skill_programmes_ids = fields.One2many("inseta.moderator.skill.programme",'moderator_id', string='Programmes')
    learner_programmes_ids = fields.One2many("inseta.moderator.learner.programme",'moderator_id', string='Learnership Programmes')
     
    bank_name = fields.Char(string='Bank Name')
    branch_code = fields.Char(string='Branch Code')
    provider_code = fields.Char(string='Provider Code', size=20)
    filler01 = fields.Char(string='Filler01', size=2)
    filler02 = fields.Char(string='Filler02', size=10)
    bank_account_number = fields.Char(string='Bank Account Number')
    job_title = fields.Char(string='Job Title')
    provider_id = fields.Many2one('inseta.provider', domain=lambda act: [('active', '=', True)])

    person_home_province_code = fields.Many2one('res.country.state', string='Home Province Code')
    person_postal_province_code = fields.Many2one('res.country.state', string='Province Code')
    organisation = fields.Many2one('res.partner', string='Organisation')
    country_home = fields.Many2one('res.country', string='Home Country')
    country_postal = fields.Many2one('res.country', string='Postal Country')
    
    department = fields.Char(string='Department')
    coach_id = fields.Many2one('hr.employee', string='Coach')
    popi_act_status_id = fields.Many2one(
        'res.popi.act.status', string='POPI Act Status')
    popi_act_status_date = fields.Date(string='POPI Act Status Date')

    nsds_target_id = fields.Many2one(
        'res.nsds.target', string='NSDS Target')
    funding_type = fields.Many2one('res.fundingtype', string='SFunding Type', required=False)
    # dgapplication_id = fields.Many2one('inseta.dgapplication')
    statssa_area_code_id = fields.Many2one('res.statssa.area.code', string='SataArea code')
    school_emis_id = fields.Many2one('res.school.emis', string='School EMIS')
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, domain=lambda act: [('active', '=', True)])
    last_school_year = fields.Many2one('res.last_school.year', string='Last school year')
    
    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 
    
    @api.onchange('end_date')
    def onchange_accreditation_end_date(self):
        if self.end_date:
            if self.end_date >= fields.Date.today():
                self.active = True
            else:
                self.active = False
        else:
            self.active = False

    def action_work_addr_map(self):
        street =  f"{self.street or ''} {self.street2 or ''} {self.street3 or ''}"
        city = self.physical_city_id
        state = self.state_id
        country = self.country_id
        zip = self.zip
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
                rec.zip,
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
    
    def action_send_mail(self, with_template_id, email_items, email_from=None, contexts=None):
        '''Email_to = [lists of emails], Contexts = {Dictionary} '''
        ids = self.id
        subject = contexts.get('subject', '') if contexts else False
        body = contexts.get('body_context', '') if contexts else False
        email_ctx = contexts.get('email_from', '') if contexts else False
        email_from = email_ctx if not email_from else email_ctx
        addressed_to = contexts.get('addressed_to', '') if contexts else False
        subject = subject if subject else 'Notification Message'
        email_to = (','.join([m for m in email_items]))
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', with_template_id)[1]         
        if template_id:
            ctx = dict()
            ctx.update({
                'default_model': 'inseta.moderator',
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

    def send_reminder_mail(self, warning_mail):
        email_from = '"INSETA"registrations@inseta.org.za'
        contact_email = [self.email]
        warning_template = 'email_template_notify_moderator_for_expiry' 
        expiry_template = 'email_template_notify_assessor_moderator_for_expiry'
        template = warning_template if warning_mail else expiry_template
        self.action_send_mail(self, contact_email, email_from, template, None)
        self.write({'expiry_reminder_sent': True})

    def _cron_expiry_reminder_method(self):
        for rec in self:
            if self.approval_date < self.end_date:
                """check if the difference between now and approval date is up to 3 years, """ 
                now = datetime.now()
                start_dt = datetime.strptime(rec.approval_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                diff = now - start_dt
                days = int(diff.days)
                if days in range (1000, 1095): # Three months before the 3 years
                    rec.send_reminder_mail(True)
                elif days > 1095:
                    rec.send_reminder_mail(False)

    def action_print_certficate(self):   
        return self.env.ref('inseta_etqa.moderator_certificate_report_2').report_action(self)

