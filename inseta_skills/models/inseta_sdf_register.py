from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo.addons.inseta_tools.validators import validate_said
from odoo.addons.inseta_tools.converters import  dd2dms

_logger = logging.getLogger(__name__)

class SdfRegisterEmployerRel(models.Model):
    """
    This model would be used to hold the SDF Employer details during registration.
    Information stored in this model would be copied to inseta.sdf.organisation on approval
    of SDF registration
    """
    _name = 'inseta.sdf.register.employer.rel'
    _description = "SDF Register Employer Rel"
    _order = "id desc" 

    sdf_register_id = fields.Many2one('inseta.sdf.register', required=True)
    org_id = fields.Many2one('inseta.organisation', required=True, help="Organisation")


class SDFRegister(models.Model):
    """This model holds the record of all SDF applications """

    _name = 'inseta.sdf.register'
    _description = "SDF Registration"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"


    @api.model
    def default_get(self, fields_list):
        res = super(SDFRegister, self).default_get(fields_list)
        skill_specs , skill_mgrs , skill_admin = self._get_group_users()
        res.update({
            'skill_specialist_ids': skill_specs,
            'skill_manager_ids': skill_mgrs,
            'skill_admin_ids': skill_admin,
        })
        return res

    sdf_role = fields.Selection([
        ('primary', 'Primary'), 
        ('secondary', 'Secondary'),
        ('contract', 'Contract')], 
        index=True,
        string="SDF Role")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('rework', 'Pending Additional Information'),
        ('rework_skill_spec', 'Pending Additional Information'), #skill manager asks specilist to rework
        ('pending_verification', 'Pending Verification'),
        ('queried', 'Queried/Rework'),
        ('pending_approval', 'Pending Approval'),
        ('awaiting_rejection', 'Request Rejection'), #if rework stays more than 10days, skill spec can request for rejection
        ('awaiting_rejection2', 'Awaiting Rejection'),
        ('approve', 'Approved'),
        ('reject', 'Rejected')], default='draft', string="Status")

    image_512 = fields.Image("Image", max_width=512, max_height=512)

    reference = fields.Char(string='Reference')
    name = fields.Char(compute="_compute_name", store=True)
    user_id = fields.Many2one('res.users', string='Related User')
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    title = fields.Many2one('res.partner.title', string='Title', )
    first_name = fields.Char(string='First Name', tracking=True)
    last_name = fields.Char(string='Last Name', tracking=True)
    middle_name = fields.Char(string='Middle Name')
    initials = fields.Char(string='Initials', tracking=True)
    birth_date = fields.Date(string='Birth Date', tracking=True)
    gender_id = fields.Many2one('res.gender', 'Gender')
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
        'res.country.state', 
        string='Physical Province', 
        domain=[('country_id.code', '=', 'ZA')]
    )
    use_physical_for_postal_addr = fields.Boolean(
        string="Use physical address for postal address?")

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

    gps_coordinates = fields.Char()
    latitude_degree = fields.Char(string='Latitude Degree', size=3, tracking=True)
    latitude_minutes = fields.Char(string='Latitude Minutes', size=2, tracking=True)
    latitude_seconds = fields.Char(string='Latitude Seconds', size=6, tracking=True)
    
    longitude_degree = fields.Char(string='Longitude Degree', size=3, tracking=True)
    longitude_minutes = fields.Char(string='Longitude Minutes',size=2, tracking=True)
    longitude_seconds = fields.Char(string='Longitude Seconds', size=6, tracking=True)

    alternateid_type_id = fields.Many2one(
        'res.alternate.id.type', string='Alternate ID Type')
    id_no = fields.Char(string="S.A Identification No")
    passport_no = fields.Char(string='Passport No')
    is_existing_reg = fields.Boolean(
        string='Existing SDF Registration', default=False)
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
    occupation_experience = fields.Text(string='Experience')
    # comments = fields.Text(string='General Comments')
    # refusal_comment = fields.Text(string='Refusal Comments')
    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    highest_edu_desc = fields.Text('Highest Education Description')
    has_requested_sdftraining = fields.Boolean(
        string="I want to attend INSETA funded Training?",
        help='''I do not have an SDF certificate and
				I would like to attend an INSETA  funded SDF training?'''
    )
    has_completed_sdftraining = fields.Boolean(
        string='Have you completed an SDF training?',
        help='''Have you completed an SDF Training Programme provided by an accredited training provider?'''
    )
    # FIXME make required and visible when has_completed_sdf_training is true
    accredited_trainingprovider_name = fields.Char(string='Accredited Training Provider')

    sdf_certificate = fields.Binary(string="SDF Certificate")
    file_name = fields.Char()
    code_of_conduct = fields.Binary(string="Code of Conduct")
    file_name2 = fields.Char()

    # workflow fields
    approval_date = fields.Date('Approval Date', readonly=True)
    rework_date = fields.Date('Rework Date', help="Date Skills Specialist Requested the Rework")
    reworked_date = fields.Date('Reworked Date', help="Date SDF Sumbitted the Rework")
    rework_expiration_date = fields.Date('Rework Expiration Date', compute="_compute_rework_expiration", store=True)
    rework_comment = fields.Text()
    rejection_comment = fields.Text()
    rejection_date = fields.Date('Rejection Date', help="Date Skills Manger Rejects SDF registraion")

    registration_date = fields.Datetime('Registration Date', default=lambda self: fields.Datetime.now(), readonly=True)
    is_confirmed = fields.Boolean('Form submission Confirmed?')

    employer_ids = fields.One2many(
        'inseta.sdf.register.employer.rel', 'sdf_register_id', string="Employers")
    skill_specialist_ids = fields.One2many(
        'res.users', 
        'sdf_register_id', 
        'Skills Specialists',
        help="Technical Field to compute skills specialist"
    )
    skill_manager_ids = fields.One2many(
        'res.users', 
        'sdf_register_id', 
        'Skills Managers',
        help="Technical Field to compute skills managers"
    )

    skill_admin_ids = fields.One2many(
        'res.users', 
        'sdf_register_id', 
        'Skills Admin',
        help="Technical Field to compute skills admin"
    )
    is_initial_update = fields.Boolean(
        help="Is set to True the first time the"
        "model is updated to trigger SDF registration Mail automated action")


# --------------------------------------------
# compute Methods
# --------------------------------------------

    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            rec.rework_expiration_date = False
            if rec.rework_date:
                rec.rework_expiration_date = date_utils.add(rec.rework_date, days=10)

    @api.depends(
        'first_name',
        'last_name',
        'middle_name')
    def _compute_name(self):
        for rec in self:
            rec.name = "{} {} {}".format(
                rec.first_name or '', rec.middle_name or '', rec.last_name or '')

# --------------------------------------------
# Onchange methods and overrides
# --------------------------------------------

    @api.onchange("id_no")
    def _onchange_id_no(self):
        """Update gender and birth_date fields on validation of R.S.A id_no"""
        if self.id_no:
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
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.physical_code)], limit=1)
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

# --------------------------------------------
# ORM Methods override
# --------------------------------------------
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.sdf.register')
        if not vals.get('is_imported'):
            vals['reference'] = sequence or '/'
        name = '{} {} {}'.format(vals.get('first_name'), vals.get(
            'middle_name'), vals.get('last_name'))
        vals['name'] = name
        return super(SDFRegister, self).create(vals)

    # def write(self, vals):
    #     return super(SDFRegister, self).write(vals)

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.reference, rec.name.title())
            arr.append((rec.id, name))
        return arr

    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You can not delete an approved or rejected SDF Register'))
        return super(SDFRegister, self).unlink()

# --------------------------------------------
# Business Logic
# --------------------------------------------
    def action_set_to_draft(self):
        self.state = 'draft'

    def rework_registration(self, comment):
        """Skill specialist query Registration and ask SDF to rework.
        This method is called from the rework wizard

        Args:
            comment (str): Reason for rework
        """
        #if Skills Manager, reworks a registration, worklow to sdf specialist
        if self.env.user.has_group("inseta_skills.group_skills_manager") and self.state == "pending_approval":
            self.write({
                'state': 'rework_skill_spec', 
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
        """Skill manger rejects SDF registration.
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

    def action_request_manager_rejection(self):
        """Skill specialist submits to Skill manager for rejection
        if SDF does not rework after 10 days
        """
        self.write({'state': 'awaiting_rejection2'})

    def action_sdf_submit_rework(self):  # rework
    
        self.write({
            'state': 'pending_verification', 
            'reworked_date': fields.date.today()}
        )
        self.activity_update()


    def action_verify(self):
        """Skill specialist Verifies SDF registration
        """     
        self.write({'state': 'pending_approval'})
        self.activity_update()

    def action_manager_approve(self):
        """Manager approves an SDF registration record, the actual SDF record is created in inseta.sdf model
        we will use the already generated user_id.partner_id
        as this will ensure SDF delegation inheritance will not create a new partner record
        """
        sdf = self.env['inseta.sdf'].create({
            'partner_id': self.user_id.partner_id.id,
            'user_id': self.user_id.id,
            'password': self.password,
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
            'physical_province_id': self.physical_province_id.id, 
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
            "state_id": self.physical_province_id.id,
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
            "highest_edu_desc": self.highest_edu_desc,
            "has_requested_sdftraining": self.has_requested_sdftraining,
            "has_completed_sdftraining": self.has_completed_sdftraining,
            "accredited_trainingprovider_name": self.accredited_trainingprovider_name,
            "general_comments": self.general_comments,
            'alternateid_type_id': self.alternateid_type_id.id, 
            'passport_no': self.passport_no,
            'id_no': self.id_no,
            'contact_type': 'sdf', 
            'sdf_certificate': self.sdf_certificate,
            "code_of_conduct": self.code_of_conduct,
            "approval_date": fields.Date.today(),
            "registration_date": self.registration_date,
            "latitude_degree": self.latitude_degree,
            "latitude_minutes": self.latitude_minutes,
            "latitude_seconds": self.latitude_seconds,
            "longitude_degree": self.longitude_degree,
            "longitude_minutes": self.longitude_minutes,
            "longitude_seconds": self.longitude_seconds,
        })
        
        self.write({'state': 'approve', "approval_date": fields.Date.today()})

        #Update SDF organisation_ids after approval
        sdf.write({
            "state": self.state,
            "organisation_ids": [(0,0, 
            {
                'sdf_id': sdf.id,
                'organisation_id': emp.org_id.id,
                'appointment_letter_id': emp.appointment_letter_id.id,
                'sdf_role': emp.sdf_role,
                'date_approved': self.approval_date,
                'approved_by': self.env.user.id,
                'state': self.state
            }) for emp in self.employer_ids]
        })
        #add the organisation to user allowed organisations
        self.user_id.allowed_organisation_ids = [(6,0, [emp.org_id.id for emp in self.employer_ids] if self.employer_ids else [])]
        #TODO: Add  organisation to employer user allowed organisations

        #update mail activity
        self.activity_update()

    def action_submit(self):
        self.write({'state': 'pending_verification'})

    def get_employer_contact_email(self):
        emails = []
        if self.employer_ids:
            for emp in self.employer_ids:
                #retrieve contact emails
                if emp.org_id:
                    contact_emails = [str(contact.email) for contact in emp.org_id.child_ids] 
                    employer_emails = [str(c.org_id.email) for c in self.employer_ids]
                    emails = contact_emails or employer_emails

        return ",".join(emails) if emails else ''


    def get_skill_managers_email(self):
        emails =  [str(mgr.partner_id.email) for mgr in self.skill_manager_ids] if self.skill_manager_ids else []
        return ",".join(emails) if emails else ''

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(SDFRegister, self)._message_auto_subscribe_followers(
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
                model='inseta.sdf.register', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        MAIL_TEMPLATE, MAIL_TEMPLATE_EMPLOYER = False, False
        #Specilist request rework, state chnages to rework, notify SDF and SDF Employer
        if self.state == 'rework':
            #schedule an activity for rework expiration for  SDF user
            self.activity_schedule(
                'inseta_skills.mail_act_sdf_rework',
                user_id=self.user_id.id or self.env.user.id,
                date_deadline=self.rework_expiration_date)
            MAIL_TEMPLATE = self.env.ref('inseta_skills.mail_template_notify_sdf_rework', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref('inseta_skills.mail_template_notify_organisation_rework', raise_if_not_found=False)
        #SDF reworks and resubmits, state chnanges to pending_verification. Notify skill specialist
        if self.state == 'pending_verification':
            MAIL_TEMPLATE =  self.env.ref('inseta_skills.mail_template_notify_skills_spec_after_rework', raise_if_not_found=False)
        #Skill Specilist verifies registration, state changes to pending_approval. notify skill mgr and SDF Employer
        if self.state == 'pending_approval':
            MAIL_TEMPLATE =  self.env.ref('inseta_skills.mail_template_notify_manager_after_verify_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref('inseta_skills.mail_template_notify_organisation_after_verify_sdf', raise_if_not_found=False)
        #Skill Manager queries registration, and asks SKill specialist to rework. state changes to rework_skill_spec 
        if self.state == 'rework_skill_spec':
            MAIL_TEMPLATE = self.env.ref('inseta_skills.mail_template_notify_skills_spec_after_mgr_rework_sdf', raise_if_not_found=False)
        #Skill Manager Rejects registration, state changes to reject. notify SDF and SDF Employer
        if self.state == 'reject':
            MAIL_TEMPLATE =  self.env.ref('inseta_skills.mail_template_notify_rejection_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref('inseta_skills.mail_template_notify_organisation_after_rejection_sdf', raise_if_not_found=False)
        #Skill Manager Approves registration, state changes to approve. notify SDF and SDF Employer
        if self.state == 'approve':
            MAIL_TEMPLATE =  self.env.ref('inseta_skills.mail_template_notify_approval_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref('inseta_skills.mail_template_notify_organisation_approval_sdf', raise_if_not_found=False)

        #unlink sdf rework activity if rework is resubmitted
        self.filtered(lambda s: s.state in ('pending_verification','pending_approval')).activity_unlink(['inseta_skills.mail_act_sdf_rework'])

        self.with_context(allow_write=True)._message_post(MAIL_TEMPLATE) #notify sdf
        self.with_context(allow_write=True)._message_post(MAIL_TEMPLATE_EMPLOYER) #notify employers

    def action_print_appointment_letter(self):
        return self.env.ref('inseta_skills.sdf_appointment_letter_report').report_action(self)

    def action_print_reject_letter(self):
        return self.env.ref('inseta_skills.sdf_rejection_letter_report').report_action(self)

    def _get_group_users(self):
        group_obj = self.env['res.groups']
        skill_specialist_group_id = self.env.ref('inseta_skills.group_skills_specialist').id
        skill_manager_group_id = self.env.ref('inseta_skills.group_skills_manager').id
        skill_admin_group_id = self.env.ref('inseta_skills.group_skills_admin').id
        specialists = group_obj.browse([skill_specialist_group_id]).users
        skill_managers = group_obj.browse([skill_manager_group_id]).users
        skill_admin = group_obj.browse([skill_admin_group_id]).users
        return specialists, skill_managers, skill_admin

    

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

            

