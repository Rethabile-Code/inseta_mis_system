from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.inseta_tools.validators import validate_said


class InsetaAssessorRegister(models.Model):
    _name = "inseta.assessor.register"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Inseta Assessor and moderator registration"
    _rec_name="reference"
    _order= "id desc"

    assessor_status = fields.Many2one("inseta.assessor.reg.status", 'Assessor Status')
    image_512 = fields.Image("Image", max_width=512, max_height=512)
    reference = fields.Char(string='Reference')
    name =  fields.Char(store=True)
    title_id = fields.Many2one('res.partner.title', string='Title', )
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Surname')
    middle_name = fields.Char(string='Middle Name')
    initials = fields.Char(string='Initials')
    birth_date = fields.Date(string='Birth Date')
    # gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    gender_id = fields.Many2one('res.gender', 'Gender')
    all_complaint = fields.Selection([('no', 'No'),('yes', 'Yes')], default="no", store=True)
    cell_phone_number = fields.Char(string='Cell Phone Number')
    telephone_number = fields.Char(string='Telephone Number')
    fax_number = fields.Char(string='Fax Number')
    email = fields.Char(string='Email Address')
    function_id = fields.Many2one("res.sdf.function", "Function")
    user_id = fields.Many2one('res.users', string='Related User id')
    password = fields.Char(string='Password')
    physical_code = fields.Char(string='Physical Code')
    physical_address1 = fields.Char(string='Physical Address Line 1') 
    physical_address2 = fields.Char(string='Physical Address Line 2')
    physical_address3 = fields.Char(string='Physical Address Line 3')
    physical_suburb_id = fields.Many2one('res.suburb',string='Physical Suburb')
    physical_city_id = fields.Many2one('res.city', string='Physical City')
    moderator_id = fields.Many2one('inseta.moderator', string='Related moderator')
    physical_municipality_id = fields.Many2one(
        'res.municipality', string='Physical Municipality')
    physical_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Physical Urban/Rural') 
     
    physical_province_id = fields.Many2one(
        'res.country.state', string='Physical Province', domain=[('code', '=', 'ZA')])
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
    
    id_no = fields.Char(string="Identification No")
    sdl_no = fields.Char(string="Assessor SDL No")
    is_existing_reg = fields.Boolean(string='Existing Registration', default=False)
    equity_id = fields.Many2one('res.equity', 'Equity')
    home_language_id = fields.Many2one('res.lang', string='Home Language',)
    disability_id = fields.Many2one('res.disability', string="Disability Status")
    notes = fields.Text(string='Notes')
    nationality_id = fields.Many2one('res.nationality', string='Nationality')
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref("base.za").id)	
    passport_no = fields.Char(string='Passport No')
    comments = fields.Text(string='General Comments')
    refusal_comment = fields.Text(string='Refusal Comments')
    date_of_registration = fields.Date('Registration Date', default=lambda self: fields.Date.today(), readonly=True)
    is_confirmed = fields.Boolean('Form submission Confirmed?')
    legacy_system_id = fields.Integer(string='Legacy System ID')
    assessor_id = fields.Many2one('inseta.assessor', 'Assessor Registration Number', domain=lambda act: [('active', '=', True)])
    is_permanent_consultant = fields.Boolean(string='Permanent consultant?')
    work_zip_code = fields.Char(string='Work Zip code')
    organization_sdl_no = fields.Char(string='Organization SDL Number')
    compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], default="no", store=True)
    qualification_document_ids = fields.Many2many('ir.attachment', 'qualification_ids_rel', 'qualification_column_id', string="Qualification Documents")
    statement_of_result_ids = fields.Many2many('ir.attachment', 'statement_ids_rel', 'statement_column_id', string="Statement of results")
    additional_document_ids = fields.Many2many('ir.attachment', 'additional_ids_rel', 'additional_column_id',string="Additional Documents")
    cv_ids = fields.Many2many('ir.attachment', 'cv_ids_rel', 'cv_column_id', string="CVs")
    code_of_conduct = fields.Many2one('ir.attachment', string="Code of conduct")
    id_document_ids = fields.Many2many('ir.attachment', 'identity_ids_rel', 'identity_column_id', string="ID Docments")
    # qualification_ids = fields.Many2many("inseta.qualification", 'inseta_qualification_rel', 'column1',string="Qualifications")
    # unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_standard_rel', 'column1', string="Qualification Unit Standard")
    # skill_programmes_ids = fields.Many2many("inseta.skill.programme",'assessor_skill_programme_rel', string='Skills Programmes')
    # learner_programmes_ids = fields.Many2many("inseta.learner.programme",'assessor_learner_programme_rel', string='Learnership Programmes')
    qualification_ids = fields.Many2many("inseta.qualification", 'inseta_qualification_rel', 'column1', 'inseta_qualification_id', string="Qualifications")
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_standard_rel', 'column1', 'inseta_unit_standard_id', string="Qualification Unit Standard")
    skill_programmes_ids = fields.Many2many("inseta.skill.programme",'assessor_skill_programme_rel', 'inseta_assessor_register_id', 'inseta_skill_programme_id', string='Skills Programmes')
    learner_programmes_ids = fields.Many2many("inseta.learner.programme",'assessor_learner_programme_rel', 'inseta_assessor_register_id', 'inseta_learner_programme_id', string='Learnership Programmes')
    state = fields.Selection([
        ('draft', 'Address Information'),
        ('evaluation', 'Verification'),
        ('recommend', 'Recommendation'),
        ('queried', 'Queried'),
        ('approved', 'Approved'),
        ('denied', 'Not Recommended'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False)

    manipulated_state = fields.Selection([
        ('draft', 'Address Information'),
        ('evaluation', 'Verification'),
        ('recommend', 'Recommendation'),
        ('manager', 'Manager'),
        ('queried', 'Queried'),
        ('approved', 'Approved'),
        ('denied', 'Not Recommended'),
    ], string='Manipulated', index=True, readonly=False, default='draft', copy=False)
    approval_date = fields.Date('Approval Date')
    registration_start_date = fields.Date('Start Date', default=lambda x: datetime.strptime('30/06/2023 00:00:00', '%d/%m/%Y %H:%M:%S'))
    registration_end_date = fields.Date('End Date')
    denied_date = fields.Date('Denial Date')
    query_date = fields.Date('Query Date')
    active = fields.Boolean(string='Active', default=True)
    alternateid_type_id = fields.Many2one(
        'res.alternate.id.type', string='Alternate ID Type')
    id_copy = fields.Binary(string='Upload ID')
    # todo discard
    # qualification_programmes_ids = fields.Many2many("inseta.qualification.programme",'assessor_qualification_programme_rel', 'inseta_assessor_register_id', 'inseta_qualification_programme_id', string='Qualification Programmes')
    # new field 
    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    highest_edu_desc = fields.Text('Highest Education Description')
    popi_act_status_id = fields.Many2one(
        'res.popi.act.status', string='POPI Act Status')
    popi_act_status_date = fields.Date(string='POPI Act Status Date')
    statssa_area_code_id = fields.Many2one('res.statssa.area.code', string='Statssa Area code')
    school_emis_id = fields.Many2one('res.school.emis', string='School EMIS')
    last_school_year = fields.Many2one('res.last_school.year', string='Last school year')
    bank_name = fields.Char(string='Bank Name')
    branch_code = fields.Char(string='Branch Code')
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, domain=lambda act: [('active', '=', True)])
    provider_code = fields.Char(string='Provider Code', size=20)
    filler01 = fields.Char(string='Filler01', size=2)
    filler02 = fields.Char(string='Filler02', size=10)
    bank_account_number = fields.Char(string='Bank Account Number')
    job_title = fields.Char(string='Job Title')
    application_compliance = fields.Selection([('no', 'No'),('yes', 'Yes')], default="no", string="Application compliance", store=False)
    accreditation_recommended = fields.Selection([('no', 'No'),('yes', 'Yes')], default="no", string="Accreditation recommended", store=False)
    person_home_province_code = fields.Many2one('res.country.state', string='Province Code')
    person_postal_province_code = fields.Many2one('res.country.state', string='Province Code')
    organisation = fields.Many2one('res.partner', string='Organisation')
    country_home = fields.Many2one('res.country', string='Country')
    country_postal = fields.Many2one('res.country', string='Country')
    department = fields.Char(string='Department')
    coach_id = fields.Many2one('hr.employee', string='Coach')
    etdp_registration_number = fields.Char(string='ETPD SETA Reg Number')
    registration_number = fields.Char(string='Registration Number')
    test_purpose = fields.Boolean(default=False) # to be remove while on production 
    verifier_ids = fields.Many2many('res.users', 'assessor_reg_verifier_rel', 'column1', string="Verifiers")
    gps_coordinates = fields.Char()
    latitude_degree = fields.Char(string='Latitude Degree')
    longitude_degree = fields.Char(string='Longitude Degree')
    popi_act_status_id = fields.Many2one(
        'res.popi.act.status', string='POPI Act Status')
    popi_act_status_date = fields.Date(string='POPI Act Status Date')
    nsds_target_id = fields.Many2one(
        'res.nsds.target', string='NSDS Target')
    funding_type = fields.Many2one('res.fundingtype', string='SFunding Type', required=False)
    # dgapplication_id = fields.Many2one('inseta.dgapplication')
    statssa_area_code_id = fields.Many2one('res.statssa.area.code', string='Statssa area code')
    school_emis_id = fields.Many2one('res.school.emis', string='School EMIS')
    
    @api.onchange('registration_end_date')
    def _onchange_end_date(self):
        end_date = self.registration_end_date	 
        if self.registration_end_date and self.registration_start_date:
            if self.registration_end_date < self.registration_start_date:
                self.registration_end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
                    }
                }

    @api.onchange('middle_name', 'first_name', 'last_name')
    def onchange_names(self):
        if self.first_name:
            self.first_name = self.first_name.capitalize()
        if self.middle_name:
            self.middle_name = self.middle_name.capitalize()
        if self.last_name:
            self.last_name = self.last_name.capitalize()

        if self.middle_name and self.first_name:
            self.initials = f'{self.first_name[0].capitalize()}{self.middle_name[0].capitalize()}'

    @api.onchange('telephone_number','cell_phone_number','fax_number')
    def onchange_validate_number(self):
        
        if self.telephone_number:
            if not self.telephone_number.strip().isdigit() or len(self.telephone_number) != 10:
                self.telephone_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Phone number'}}
        if self.cell_phone_number:
            if not self.cell_phone_number.strip().isdigit() or len(self.cell_phone_number) != 10:
                self.cell_phone_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Cell phone number'}}
        if self.fax_number:
            if not self.fax_number.strip().isdigit() or len(self.fax_number) != 10:
                self.fax_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Fax number'}}
    
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
                rec.write({
                    'latitude_degree': result[0] if result else False,
                    'longitude_degree': result[1] if result else False,
                })
        return True

    def _get_group_users(self):
        group_obj = self.env['res.groups']
        group_accessor_moderator_reg = self.env.ref('inseta_etqa.group_accessor_moderator_reg').id
        manager_group_id = self.env.ref('inseta_etqa.group_etqa_evaluating_manager').id
        accessor_moderator_users = group_obj.browse([group_accessor_moderator_reg]).users
        manager_users = group_obj.browse([manager_group_id]).users
        return accessor_moderator_users, manager_users

    def set_to_draft(self):
        self.state = 'draft'

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
                'default_model': 'inseta.assessor.register',
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
            self._message_post(with_template_id)
    
    def _check_valid_fields(self):
        # if not (self.skill_programmes_ids or self.qualification_ids or self.learner_programmes_ids):
        # 	raise ValidationError("Please provide programmes")
        if self.all_complaint != "yes":
            raise ValidationError('No evidence is received for this application. Scroll through the verification tab')

        if self.state == "recommend":
            if not (self.registration_start_date and self.registration_end_date):
                raise ValidationError('Start and end date is required. Scroll to recommendation tab to add it')
            if not (self.application_compliance and self.accreditation_recommended):
                raise ValidationError('Accreditation Recomended  and application complaince field required. Scroll to recommendation tab to add it')
        
        # if not self.verifier_ids:
        # 	raise ValidationError("Please provide verifiers")

        if not self.qualification_ids and self.unit_standard_ids:
            raise ValidationError("Please provide Qualification or unit standard programmes")

    def action_submit_button(self):
        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group]
        reciepients.append('assessorregistration@inseta.org.za')
        # send to registrants
        template = "email_template_send_to_assessor_after_submission"
        self.action_send_mail(template, [self.email], None, None)
        #  Sent to Evaluation committees 
        evaluator_template = "email_template_send_to_assessor_evaluating_conmmittee"
        self.action_send_mail(evaluator_template, reciepients, None, None) 
        self.write({'state': 'evaluation', 'refusal_comment': '', 'comments': '', 'manipulated_state': 'evaluation',})

    def action_evaluating_committee_approve_button(self):
        self._check_valid_fields()
        eval_grp, manager_group_ids = self._get_group_users()
        reciepients = [rec.login for rec in manager_group_ids]
        reciepients.append('assessorregistration@inseta.org.za')
        template = 'email_template_assessor_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'recommend', 'approval_date': fields.date.today(), 'manipulated_state': 'recommend'})

    def action_verify_approve_button(self):
        self._check_valid_fields()
        eval_grp, manager_group_ids = self._get_group_users()
        reciepients = [rec.login for rec in manager_group_ids] + [self.email] +  [rec.login for rec in eval_grp]
        reciepients.append('assessorregistration@inseta.org.za')
        template = 'email_template_assessor_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'approved', 'approval_date': fields.date.today(), 'manipulated_state': 'approved', 'accreditation_recommended': 'yes'})
        return self.action_manager_approve()

    def action_query(self):
        return self.popup_notification(False, 'query') 

    def action_reject(self):
        return self.popup_notification(False, 'refuse') 

    def eval_committee_send_query_notification(self): # query notification
        self.update({'query_date': fields.date.today()})
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group]
        reciepients = eval_emails 
        reciepients.append(self.email)
        reciepients.append('assessorregistration@inseta.org.za')
        query_submission_date = self.query_date + relativedelta(day=5)
        contexts = {'query_submission_date': query_submission_date}
        template = 'email_template_assessor_query_notification'
        self.action_send_mail(template, reciepients, None, contexts) 
        self.write({'state': 'queried'})

    def action_submit_rework(self): # queried
        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group]
        reciepients.append(self.email)
        reciepients.append('assessorregistration@inseta.org.za')
        template = 'email_template_assessor_submit_query_notification'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'evaluation'})
     
    def action_reject_method(self):
        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group]
        reciepients.append(self.email)
        reciepients.append('assessorregistration@inseta.org.za')
        template = 'email_template_notify_assessor_rejection'	
        self.action_send_mail(template, reciepients, None, None) 
         
    def popup_notification(self, subject, action):
        self.write({'comments': '', 'refusal_comment': ''})
        view = self.env.ref('inseta_etqa.inseta_etqa_wiz_main_view_form')
        view_id = view and view.id or False
        context = {
                    'default_subject': subject, 
                    'default_date': fields.Date.today(),
                    'default_reference': self.id,
                    'default_action': action,
                    'default_model_name': "inseta.assessor.register",

                    }
        return {'name':'Dialog',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'res_model':'inseta.etqa.wizard',
                    'views':[(view.id, 'form')],
                    'view_id':view.id,
                    'target':'new',
                    'context':context,
                } 

    def action_print_appointment_letter(self):
        return self.env.ref('inseta_etqa.assessor_appointment_letter_report').report_action(self)
    
    def action_print_statement_result(self):
        return self.env.ref('inseta_etqa.assessor_result_statement_report').report_action(self)

    def action_print_reject_letter(self):
        return self.env.ref('inseta_etqa.assessor_rejection_letter_report').report_action(self)

    def action_view_rejection_letter(self):
        template_name = 'inseta_etqa.assessor_rejection_letter_report'
        report_template = self.env.ref('inseta_etqa.assessor_rejection_letter_report')
        report = self.env['ir.actions.report'].search([('report_name', '=', template_name)], limit=1)
        if report:
            report.write({'report_type': 'qweb-html'})
        return report_template.report_action(self)

    def action_print_certficate(self):   
        return self.env.ref('inseta_etqa.assessor_certificate_report_register').report_action(self)

    def action_manager_approve(self):
        """assessor approval creates them as a contact (res.partner) record. 
        """
        assessor = self.env['inseta.assessor'].sudo().create({
            # 'partner_id': self.user_id.partner_id.id,
            'user_id': self.user_id.id,
            'title': self.title_id.id, 
            'birth_date': self.birth_date, 
            'gender_id': self.gender_id.id , 
            'name': f"{self.first_name} {self.middle_name} {self.last_name}",
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "initials": self.initials,
            'equity_id': self.equity_id.id, 
            'disability_id': self.disability_id.id, 
            'email': self.email, 
            'id_no': self.id_no or self.passport_no,
            'phone': self.telephone_number, 
            'mobile': self.cell_phone_number,
            'fax_number': self.fax_number,
            'state_id': self.physical_province_id.id, 
            'home_language_id': self.home_language_id.id,
            'nationality_id': self.nationality_id.id,  
            # 'country_id': self.country_id.id,  
            'physical_code': self.physical_code,
            'street': self.physical_address1, 
            'street2': self.physical_address2,
            'street3': self.physical_address3, 
            'physical_suburb_id': self.physical_suburb_id.id,
            'physical_city_id': self.physical_city_id.id, 
            'physical_municipality_id': self.physical_municipality_id.id, 
            'postal_municipality_id': self.postal_municipality_id.id, 
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
            "is_permanent_consultant": self.is_permanent_consultant,
            "work_zip_code": self.work_zip_code,
            "organization_sdl_no": self.organization_sdl_no,
            "qualification_document_ids": self.qualification_document_ids,
            "statement_of_result_ids": self.statement_of_result_ids,
            "additional_document_ids": self.additional_document_ids,
            "cv_ids": self.cv_ids,
            "code_of_conduct": self.code_of_conduct.id,
            # 'skill_programmes_ids': self.skill_programmes_ids,
            "id_document_ids": self.id_document_ids,
            "qualification_ids": [(0, 0, {'qualification_id': rec.id}) for rec in self.qualification_ids],
            "unit_standard_ids":  [(0, 0, {'unit_standard_id': rec.id}) for rec in self.unit_standard_ids],
            'contact_type': 'assessor',
            'active': True,
            "latitude_degree": self.latitude_degree,
            "longitude_degree": self.longitude_degree,
            "popi_act_status_id": self.popi_act_status_id.id,
            "popi_act_status_date": self.popi_act_status_date,
            "nsds_target_id": self.nsds_target_id.id,
            "funding_type": self.funding_type.id,
            "statssa_area_code_id": self.statssa_area_code_id.id,
            "school_emis_id": self.school_emis_id.id,
            "provider_id": self.provider_id,
            "employer_sdl_no": self.sdl_no if self.sdl_no else self.reference,
            "etdp_registration_number": self.etdp_registration_number,
            'last_school_year': self.last_school_year.id,
            "assessor_status": self.assessor_status.id,
            'start_date': self.registration_start_date, 
            'end_date': self.registration_end_date,
        })
        self.sudo().write({"approval_date": fields.Date.today(), 'assessor_id': assessor.id})
        group_approved_assessor = self.env.ref("inseta_etqa.group_approved_assesor")
        if not self.env.user.has_group("inseta_etqa.group_approved_assesor"):
            assessor.user_id.sudo().write({'groups_id': [(4, group_approved_assessor.id)]})

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.assessor.register')
        vals['reference'] = sequence or '/'
        vals['registration_number'] = sequence or '/'
        # vals['etdp_registration_number'] = sequence or '/'
        name = '{} {} {}'.format(vals.get('first_name'), vals.get(
            'middle_name'), vals.get('last_name'))
        # vals['name'] = name
        return super(InsetaAssessorRegister, self).create(vals)


class InsetaModeratorRegister(models.Model):
    _name = "inseta.moderator.register"
    _inherit = "inseta.assessor.register"
    _description = "Inseta moderator"
    _rec_name = "reference"
    _order= "id desc"

    moderator_status = fields.Many2one("inseta.assessor.reg.status", 'Moderator Status')
    legacy_system_id = fields.Integer(string='Legacy System ID')
    moderator_id = fields.Many2one('inseta.moderator', 'Moderator ID')
    assessor_id = fields.Many2one('inseta.assessor', 'Assessor ID', domain=lambda act: [('active', '=', True)])
    qualification_document_ids = fields.Many2many('ir.attachment', 'moderator_qualification_ids_rel', 'qualification_column_id', string="Qualification Documents")
    statement_of_result_ids = fields.Many2many('ir.attachment', 'moderator_statement_ids_rel', 'statement_column_id', string="Statement of results")
    additional_document_ids = fields.Many2many('ir.attachment', 'moderator_additional_ids_rel', 'additional_column_id',string="Additional Documents")
    cv_ids = fields.Many2many('ir.attachment', 'moderator_cv_ids_rel', 'cv_column_id', string="CVs")
    code_of_conduct = fields.Many2one('ir.attachment', string="Code of conduct")
    id_document_ids = fields.Many2many('ir.attachment', 'moderator_identity_ids_rel', 'identity_column_id', string="ID Docments")
    qualification_ids = fields.Many2many("inseta.qualification", 'moderator_inseta_qualification_rel', 'column1', 'inseta_qualification_id', string="Qualifications", domain=lambda act: [('active', '=', True)])
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'moderator_unit_standard_rel', 'column1', 'inseta_unit_standard_id', string="Qualification Unit Standard", domain=lambda act: [('active', '=', True)])
    skill_programmes_ids = fields.Many2many(
        "inseta.skill.programme",
        'moderator_skill_programme_rel', 
        'inseta_moderator_register_id',
        'inseta_skill_programme_id',
        string='Skill Programmes',
        domain=[('active', '=', True)]
    )
    learner_programmes_ids = fields.Many2many(
        "inseta.learner.programme",
        'moderator_learner_programme_rel',
        'inseta_moderator_register_id',
        'inseta_learner_programme_id',
        string='Learnership Programmes'
    )
    verifier_ids = fields.Many2many('res.users', 'moderator_reg_verifier_rel', 'column1', string="Verifiers")
    gender_id = fields.Many2one('res.gender', 'Gender')

    @api.onchange('registration_end_date')
    def _onchange_end_date(self):
        end_date = self.registration_end_date	 
        if self.registration_end_date and self.registration_start_date:
            if self.registration_end_date < self.registration_start_date:
                self.registration_end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
                    }
                }

    @api.onchange('middle_name', 'first_name', 'last_name')
    def onchange_names(self):
        if self.first_name:
            self.first_name = self.first_name.capitalize()
        if self.middle_name:
            self.middle_name = self.middle_name.capitalize()
        if self.last_name:
            self.last_name = self.last_name.capitalize()

        if self.middle_name and self.first_name:
            self.initials = f'{self.first_name[0].capitalize()}{self.middle_name[0].capitalize()}'
 
    @api.onchange('telephone_number','cell_phone_number','fax_number')
    def onchange_validate_number(self):
        
        if self.telephone_number:
            if not self.telephone_number.strip().isdigit() or len(self.telephone_number) != 10:
                self.telephone_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Phone number'}}
        if self.cell_phone_number:
            if not self.cell_phone_number.strip().isdigit() or len(self.cell_phone_number) != 10:
                self.cell_phone_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Cell phone number'}}
        if self.fax_number:
            if not self.fax_number.strip().isdigit() or len(self.fax_number) != 10:
                self.fax_number = ''
                return {'warning':{'title':'Invalid input','message':'Please enter 10 digits Fax number'}}
    
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
            if not self.test_purpose:
                existing_record = self.env['inseta.assessor'].search([('id_no', '=', self.id_no)], limit=1)
                if existing_record:
                    self.id_no = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"Moderator with RSA No. {self.id_no} already exists"
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
                            'message': f"Invalid R.S.A Identification No. {original_idno}"
                        }
                    }
                # update date of birth with identity
                self.update({"birth_date": identity.get('dob'),
                            "gender_id": 1 if identity.get("gender") == 'male' else 2})

    @api.onchange('physical_code')
    def _onchange_physical_code(self):
        if self.physical_code:
            locals = self.env['res.suburb'].search(
                [('postal_code', '=', self.physical_code)], limit=1)
            if locals:
                self.physical_municipality_id = locals.municipality_id.id
                self.physical_suburb_id = locals.id
                self.physical_province_id = locals.province_id.id
                self.physical_city_id = locals.city_id.id
                

    @api.onchange('use_physical_for_postal_addr')
    def _onchange_use_physical_for_postal_addr(self):
        locals = self
        if self.use_physical_for_postal_addr:
            self.postal_municipality_id = locals.physical_municipality_id.id
            self.postal_suburb_id = locals.physical_suburb_id.id
            self.postal_province_id = locals.physical_province_id.id
            self.postal_city_id = locals.physical_city_id.id
            self.postal_urban_rural = locals.physical_urban_rural
            self.postal_address1 = locals.physical_address1
            self.postal_address2 = locals.physical_address2
            self.postal_address3 = locals.physical_address3
            self.postal_code = locals.physical_code
        else:
            self.postal_municipality_id = False
            self.postal_suburb_id = False
            self.postal_province_id = False
            self.postal_city_id = False
            self.postal_urban_rural = False
            self.postal_address1 = False
            self.postal_address2 = False
            self.postal_address3 = False

    def _check_valid_fields(self):
        # if not (self.skill_programmes_ids or self.qualification_ids or self.learner_programmes_ids):
        # 	raise ValidationError("Please provide programmes")
        if self.all_complaint != "yes":
            raise ValidationError('No evidence is received for this application. Scroll through the verification tab')
        if self.state == "recommend":
            if not (self.registration_start_date and self.registration_end_date):
                raise ValidationError('Start and end date is required. Scroll to recommendation tab to add it')
            if not (self.application_compliance and self.accreditation_recommended):
                raise ValidationError('Accreditation Recomended  and application complaince field required. Scroll to recommendation tab to add it')
        
        # if not self.verifier_ids:
        # 	raise ValidationError("Please provide verifiers")

        if not self.qualification_ids and self.unit_standard_ids:
            raise ValidationError("Please provide Qualification or unit standard programmes")

    def action_submit_button(self):
        related_assessor = self.env['inseta.assessor'].search([('id_no', '=', self.id_no)], limit=1)

        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group]
        reciepients.append('moderatorregistration@inseta.org.za')
        # send to registrants
        template = "email_template_send_to_moderator_after_submission"
        self.action_send_mail(template, [self.email], None, None)
        #  Sent to Evaluation committees 
        evaluator_template = "email_template_send_to_moderator_evaluating_conmmittee"
        self.action_send_mail(evaluator_template, reciepients, None, None) 
        self.write({'state': 'evaluation', 'refusal_comment': '', 'comments': '', 'manipulated_state': 'evaluation',})
        # 'unit_standard_ids': [(4, rec.id) for rec in related_assessor.unit_standard_ids], 'qualification_ids': [(4, rec.id) for rec in related_assessor.qualification_ids]})

    def action_evaluating_committee_approve_button(self):
        self._check_valid_fields()
        reciepients = [self.email, 'moderatorregistration@inseta.org.za']
        template = 'email_template_moderator_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'recommend', 'approval_date': fields.date.today(), 'manipulated_state': 'recommend'})

    def action_verify_approve_button(self):
        self._check_valid_fields()
        eval_grp, manager_group_ids = self._get_group_users()
        reciepients = [rec.login for rec in manager_group_ids] + [self.email] +  [rec.login for rec in eval_grp] + ['moderatorregistration@inseta.org.za']
        template = 'email_template_moderator_notify_all_after_approval'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'approved', 'approval_date': fields.date.today(), 'manipulated_state': 'approved', 'accreditation_recommended': 'yes'})
        return self.action_manager_approve()

    def action_query(self):
        return self.popup_notification(False, 'query')

    def action_reject(self):
        return self.popup_notification(False, 'refuse') 

    def eval_committee_send_query_notification(self): # query notification
        eval_group = self._get_group_users()[0]
        eval_emails = [rec.login for rec in eval_group] + ['moderatorregistration@inseta.org.za'] + self.email
        reciepients = eval_emails 
        self.update({'query_date': fields.date.today()})
        query_submission_date = self.query_date + relativedelta(day=5)
        contexts = {'query_submission_date': query_submission_date}
        template = 'email_template_moderator_query_notification'
        self.action_send_mail(template, reciepients, None, contexts) 
        self.write({'state': 'queried', 'query_date': fields.date.today()})

    def action_submit_rework(self): # queried
        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group]
        reciepients.append(self.email)
        reciepients.append('moderatorregistration@inseta.org.za')
        template = 'email_template_moderator_submit_query_notification'
        self.action_send_mail(template, reciepients, None, None) 
        self.write({'state': 'evaluation'})
     
    def action_reject_method(self):
        eval_group = self._get_group_users()[0]
        reciepients = [rec.login for rec in eval_group] + ['moderatorregistration@inseta.org.za']
        reciepients.append(self.email)
        template = 'email_template_notify_moderator_rejection'	
        self.action_send_mail(template, reciepients, None, None) 

    def popup_notification(self, subject, action):
        self.write({'comments': '', 'refusal_comment': ''})
        view = self.env.ref('inseta_etqa.inseta_etqa_wiz_main_view_form')
        view_id = view and view.id or False
        context = {
                    'default_subject': subject, 
                    'default_date': fields.Date.today(),
                    'default_reference': self.id,
                    'default_action': action,
                    'default_model_name': "inseta.moderator.register",
                }
        return {'name':'Dialog',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'res_model':'inseta.etqa.wizard',
                    'views':[(view.id, 'form')],
                    'view_id':view.id,
                    'target':'new',
                    'context':context,
                } 

    def action_print_certficate(self):   
        return self.env.ref('inseta_etqa.moderator_certificate_report_2').report_action(self)

    def action_print_appointment_letter(self):
        return self.env.ref('inseta_etqa.moderator_appointment_letter_report').report_action(self)

    def action_print_statement_result(self):
        return self.env.ref('inseta_etqa.moderator_result_statement_report').report_action(self)

    def action_print_reject_letter(self):
        return self.env.ref('inseta_etqa.moderator_rejection_letter_report').report_action(self)

    def action_view_rejection_letter(self):
        template_name = 'inseta_etqa.assessor_rejection_letter_report'
        report_template = self.env.ref('inseta_etqa.assessor_rejection_letter_report')
        report = self.env['ir.actions.report'].search([('report_name', '=', template_name)], limit=1)
        if report:
            report.write({'report_type': 'qweb-pdf'})
        return report_template.report_action(self)

    def action_manager_approve(self):
        """moderator approval creates a them as a contact (res.partner) record. 
        """
        related_assessor = self.env['inseta.moderator'].sudo().search([('id_no', '=', self.id_no)], limit=1)
        moderator = self.env['inseta.moderator'].sudo().create({
            'partner_id': related_assessor.user_id.partner_id.id,
            'user_id': related_assessor.user_id.id,
            'title': self.title_id.id, 
            'birth_date': self.birth_date, 
            'gender_id': self.gender_id.id , 
            'name': f"{self.first_name} {self.middle_name} {self.last_name}",
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "initials": self.initials,
            'equity_id': self.equity_id.id, 
            'disability_id': self.disability_id.id, 
            'email': self.email, 
            'phone': self.telephone_number, 
            'mobile': self.cell_phone_number,
            'fax_number': self.fax_number,
            'state_id': self.physical_province_id.id, 
            'home_language_id': self.home_language_id.id,
            # 'country_id': self.country_id.id,  
            'nationality_id': self.nationality_id.id,  
            'physical_code': self.physical_code,
            'street': self.physical_address1, 
            'street2': self.physical_address2,
            'street3': self.physical_address3, 
            'physical_suburb_id': self.physical_suburb_id.id,
            'physical_city_id': self.physical_city_id.id, 
            'physical_municipality_id': self.physical_municipality_id.id, 
            # 'physical_province_id': self.physical_province_id.id,
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
            'postal_municipality_id': self.postal_municipality_id.id, 
            'postal_urban_rural': self.postal_urban_rural, 
            "is_permanent_consultant": self.is_permanent_consultant,
            "work_zip_code": self.work_zip_code,
            "organization_sdl_no": self.organization_sdl_no,
            "qualification_document_ids": self.qualification_document_ids,
            "statement_of_result_ids": self.statement_of_result_ids,
            "additional_document_ids": self.additional_document_ids,
            "cv_ids": self.cv_ids,
            "code_of_conduct": self.code_of_conduct.id,
            "moderator_status": self.moderator_status.id,
            "id_document_ids": self.id_document_ids,
            # "qualification_ids": self.qualification_ids,
            # "unit_standard_ids": self.unit_standard_ids,
            "qualification_ids": [(0, 0, {'qualification_id': rec.id}) for rec in self.qualification_ids],
            "unit_standard_ids":  [(0, 0, {'unit_standard_id': rec.id}) for rec in self.unit_standard_ids],
            
            'contact_type': 'moderator',
            # 'skill_programmes_ids': self.skill_programmes_ids,
            'active': True,
            "latitude_degree": self.latitude_degree,
            "longitude_degree": self.longitude_degree,
            "popi_act_status_id": self.popi_act_status_id.id,
            "popi_act_status_date": self.popi_act_status_date,
            "nsds_target_id": self.nsds_target_id.id,
            "funding_type": self.funding_type.id,
            "statssa_area_code_id": self.statssa_area_code_id.id,
            "school_emis_id": self.school_emis_id.id,
            "etdp_registration_number": self.etdp_registration_number,
            "provider_id": self.provider_id,
            "employer_sdl_no": self.sdl_no if self.sdl_no else self.reference,
            'id_no': self.id_no or self.passport_no,
            'last_school_year': self.last_school_year.id,
            'start_date': self.registration_start_date, 
            'end_date': self.registration_end_date,
        })
        self.write({"approval_date": fields.Date.today(), 'moderator_id': moderator.id})
        group_approved_moderator = self.env.ref("inseta_etqa.group_approved_moderator")
        if not self.env.user.has_group("inseta_etqa.group_approved_moderator"):
            moderator.user_id.sudo().write({'groups_id': [(4, group_approved_moderator.id)]})

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.moderator.register')
        vals['reference'] = sequence or '/'
        vals['registration_number'] = sequence or '/'
        # vals['etdp_registration_number'] = sequence or '/'
        name = '{} {} {}'.format(vals.get('first_name'), vals.get(
            'middle_name'), vals.get('last_name'))
        vals['name'] = name
        return super(InsetaModeratorRegister, self).create(vals)
