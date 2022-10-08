from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class InsetaVerificationRequest(models.Model):
    _name = "inseta.batch.verification.request"
    _order= "id desc"
    _description = "Inseta ETQA verification.request"

    provider_id = fields.Many2one("inseta.provider", 'Provider')
    provider_sdl = fields.Char('Provider SDL / N No.')
    programme_id = fields.Char('Programe Saqa Code')
    programme_description = fields.Char('Programme description')
    number_of_batch_learner = fields.Char('Number of learner')
    physical_address_1 = fields.Char('physical address 1')
    physical_address_2 = fields.Char('physical address 2')
    physical_address_3 = fields.Char('physical address 3')
    verification_number = fields.Integer('Verification Number')

    qualification_id = fields.Many2one("inseta.qualification", string='qualification ID')
    learnership_id = fields.Many2one("inseta.learner.programme", string='learnership ID')
    learnership_id = fields.Many2one("inseta.skill.programme", string='Skill ID')
    unit_standard_id = fields.Many2one("inseta.unit.standard", string='Standard Unit')
    assessment_date = fields.Date('Assessment Date')
    approved_date = fields.Date('Approval Date')


class InsetaVerificationRequest(models.Model):
    _name = "inseta.verification.request"
    _order= "id desc"
    _description = "Inseta ETQA verification.request"

    provider_id = fields.Many2one("inseta.provider", 'Provider', store=True, default = lambda self: self.get_provider_default_user())
    provider_sdl = fields.Char('Provider SDL / N No.')
    email = fields.Char(string='Email', compute="compute_provider_details")
    phone = fields.Char(string='Phone', compute="compute_provider_details")
    cell_phone = fields.Char(string='Cell Phone', compute="compute_provider_details")
    physical_address_1 = fields.Char('physical address 1',compute="compute_provider_details")
    physical_address_2 = fields.Char('physical address 2',compute="compute_provider_details")
    physical_address_3 = fields.Char('physical address 3',compute="compute_provider_details")

    name = fields.Integer('Reference Number')
    verification_number = fields.Integer('Verification Number')

    learner_id_no = fields.Char('Identification', related="learner_id.id_no")
    learner_id = fields.Many2one('inseta.learner', string="Learner")
    verification_status = fields.Many2one("inseta.verification.status", string='Verification status')
    batch_verification_status = fields.Many2one("inseta.batch.verification.request", string='Batch Verification ID')
    credits = fields.Integer('Core', default=0)
    active = fields.Boolean(string='Active', default=True)
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    assessment_date = fields.Date('Assessment Date')
    approved_date = fields.Date('Approval Date')
    learner_skill_learnership_id = fields.Many2one("inseta.skill.learnership", string='Learner learnership ID')
    unit_standard_learnership_id = fields.Many2one("inseta.unit_standard.learnership", string='Learner unit standard learnership ID')
    learner_learnership_id = fields.Many2one("inseta.learner.learnership", string='Learner learnership ID')
    learner_qualification_id = fields.Many2one("inseta.qualification.learnership", string='Learner Qualification ID')
    etqa_verifier_ids = fields.Many2many(
        'res.users', 
        'etqa_verification_rel',
        'inseta_verification_request_assessment_id',
        'res_users_id',
        string='Verifiers', domain=lambda self: self.domain_evaluating_verifier_users(), help="ETQA admin adds verifiers for the assessment request")

    etqa_admin_ids = fields.Many2many(
        'res.users',
        'etqa_verification_admin_rel', 
        'inseta_verification_request_assessment_id',
        'res_users_id',
        string='Evaluation Admin',
        help="Technical Field to compute evaluation admin"
    )

    etqa_manager_ids = fields.Many2many(
        'res.users',
        'etqa_verification_manager_rel',
        'inseta_verification_request_assessment_id',
        'res_users_id',
        string='Evaluation Manager (s)',
        help="Technical Field to compute eval manager"
    )
    etqa_committee_ids = fields.Many2many(
        'res.users', 
        'etqa_verification_comm_rel',
        'inseta_verification_request_assessment_id',
        'res_users_id',
        string='Verifiers', domain=lambda self: self.domain_evaluating_committee_user_groups(),)

    state = fields.Selection([
        ('draft', 'New verification'), 
        ('rework', 'Pending Additional Information'),
        ('pending_allocation', 'ETQA Admin'),
        ('queried', 'Queried/Rework'),
        ('pending_verification', 'Verification report'),
        ('manager_verify', 'Manager to Verify'),
        ('verified', 'Programme Assessment'),  
        ('awaiting_rejection', 'Request Rejection'), # if rework stays more than 10days, committe can request for rejection
        ('awaiting_rejection2', 'Awaiting Rejection'),
        ('manager', 'ETQA Admin to Approve'),
        ('done', 'Approved'),
        ('reject', 'Rejected')], default='draft', string="Status")
    refusal_comment = fields.Text(string='Refusal Comments')
    accreditation_number = fields.Char(string='Accreditation number', compute="compute_provider_details")
    end_date = fields.Date(string='DHET Registration End Date', compute="compute_provider_details")

    def domain_evaluating_verifier_users(self):
        etqa_eval_committee, etqa_admin, etqa_manager, etqa_verfier = self._get_group_users()
        return [('id','in', [res.id for res in etqa_verfier])]

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.assessment')
        vals['name'] = sequence or '/'
        return super(InsetaAssessment, self).create(vals)

    @api.onchange('commencement_date')
    def _onchange_end_date(self):
        end_date = self.completion_date
        if self.commencement_date:
            if self.commencement_date < fields.Date.today():
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement date cannot be less than the today's date"
                    }
                }

    @api.onchange('completion_date')
    def _onchange_completion_date(self):
        if self.completion_date:
            if not self.commencement_date:
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement date is required to be selected before completion date"
                    }
                }
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Completion date cannot be less than the Commencement date"
                    }
                }

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].sudo().search([('employer_sdl_no', '=', self.provider_sdl), ('active', '=', True)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }
    
    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id

    # def action_verification_signoff(self):
    # 	committee, etqa_admin, manager, verifier = self._get_group_users()
    # 	etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
    # 	recipients = etqa_manager_admin_login
    # 	self.env['inseta.assessment'].action_send_mail('send_to_manager_assessment_mail_template', recipients, None) 
    # 	self.write({'state': 'manager', 'assessment_date':fields.Date.today()})
        
    def _get_group_users(self):
        group_obj = self.env['res.groups']
        etqa_users_group_id = self.env.ref('inseta_etqa.group_etqa_user').id
        etqa_eval_committee_group_id = self.env.ref('inseta_etqa.group_etqa_evaluating_committee').id
        etqa_admin_group_id = self.env.ref('inseta_etqa.group_etqa_evaluating_admin').id
        etqa_manager_group_id = self.env.ref('inseta_etqa.group_etqa_evaluating_manager').id
        etqa_verifiers_group_id = self.env.ref('inseta_etqa.group_etqa_verifiers').id
        
        etqa_user = group_obj.browse([etqa_users_group_id])
        etqa_committee = group_obj.browse([etqa_eval_committee_group_id])
        etqa_admin = group_obj.browse([etqa_admin_group_id])
        etqa_manager = group_obj.browse([etqa_manager_group_id])
        etqa_verifier = group_obj.browse([etqa_verifiers_group_id])
        etqa_committee_users, etqa_admin_users, etqa_manager_users, etqa_verifier_user = False, False, False, False 
        if etqa_committee:
            etqa_committee_users = etqa_committee.mapped('users')
        if etqa_admin:
            etqa_admin_users = etqa_admin.mapped('users')

        if etqa_admin:
            etqa_manager_users = etqa_manager.mapped('users') 
        if etqa_verifier:
            etqa_verifier_user = etqa_verifier.mapped('users') 
        return etqa_committee_users, etqa_admin_users, etqa_manager_users, etqa_verifier_user

    @api.depends('provider_id')
    def compute_provider_details(self):
        for rec in self:
            provider = rec.provider_id
            if rec.provider_id:
                rec.physical_code = provider.zip
                rec.physical_address1 = provider.street
                rec.physical_address2 = provider.street1
                rec.physical_address3 = provider.street2
                rec.accreditation_number = provider.provider_accreditation_number
                rec.phone = provider.phone
                rec.email = provider.email
                rec.cell_phone = provider.phone
                rec.end_date = provider.end_date
                # rec.accreditation_status = provider.accreditation_status
            else:
                rec.physical_code = False
                rec.physical_address1 = False
                rec.email = False
                rec.phone = False
                rec.cell_phone = False
                rec.end_date = False
                rec.accreditation_number = False
                # rec.accreditation_status = False

    def action_set_to_draft(self):
        self.state = 'draft' 

    def action_reject_assesment_submit(self):
        emails = []
        
        if not self.refusal_comment:
            raise ValidationError("Please provide a reason in the refusal comment section")

        if self.state == "pending_allocation":
            self.state = "draft"

        elif self.state == "pending_verification":
            if not self.env.user.has_group('inseta_etqa.group_etqa_verifiers'):
                raise ValidationError("You are not allowed to reject this record... Only users with Verification access can do that!!!")
            emails = [mail.login for mail in self.etqa_admin_ids]
            self.state = "pending_allocation"

        elif self.state == "manager_verify":
            emails = [mail.login for mail in self.etqa_verifier_ids]
            self.state = "pending_verification"

        elif self.state == "manager":
            self.state = "verified"

        emails.append(self.provider_id.email)
        self.action_send_mail('reject_assessment_mail_template', emails, None) 

    def action_submit(self):
        self.check_updated_learners()
        recipients = [mail.login for mail in self.etqa_admin_ids]
        self.action_send_mail('submission_assessment_mail_template', recipients, None) 
        self.write({'state': 'pending_allocation'})

    def action_allocation_verifier(self):
        """ETQA Admin allocate Verifiers 
        """     
        if not self.etqa_verifier_ids:
            raise ValidationError('Please ensure to select at least one Reviewer / verifier!!!')
        if not self.learner_assessment_document_ids:
            raise ValidationError('Please ensure all documents are provider!!!')
        verifier_mails = [mail.login for mail in self.etqa_verifier_ids]
        if not verifier_mails: 
            raise ValidationError("No email found for selected verifiers")
        self.action_send_mail('request_verification_assessment_mail_template', verifier_mails, None) 
        self.write({'state': 'pending_verification'})

    def action_verify(self):
        """ETQA Verifiers Approves learners Assesssment
        """ 
        if not self.etqa_verifier_ids:
            raise ValidationError('Please ensure to select at least one Reviewer / verifier!!!')

        if not self.learner_assessment_verification_report_ids:
            raise ValidationError('Please ensure all reports documents are provided!!!')

        recipients = [mail.login for mail in self.etqa_manager_ids]
        self.action_send_mail('verification_assessment_mail_template', recipients, None) 
        self.write({'state': 'manager_verify'})
    
    def action_manager_approve_verification(self):
        """ETQA Manager Approves learners Verification
        """ 
        recipients = [mail.login for mail in self.etqa_verifier_ids]
        self.action_send_mail('manager_verification_assessment_mail_template', recipients, None) 
        ver_date = self.verification_date.strftime('%d/%m/%Y')# 09/01/2021
        self.verification_number = f'{self.provider_id.employer_sdl_no[0:3]}-{ver_date}' # N00-09/01/2021
        self.write({'state': 'verified', 'verified': True, 'endorsed': True})

    def action_verification_signoff(self):
        if not self.learner_assessment_details:
            raise ValidationError('Please add learner(s) under assessment line')
        verifiers_login = [mail.login for mail in self.etqa_verifier_ids]
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = verifiers_login + etqa_manager_admin_login
        self.action_send_mail('send_to_manager_assessment_mail_template', recipients, None) 
        self.write({'state': 'manager', 'assessment_date':fields.Date.today(), 'endorsed': True})

    def action_done(self):
        verifiers_login = [mail.login for mail in self.etqa_verifier_ids]
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = verifiers_login + etqa_manager_admin_login

        provider_email = [self.provider_id.email]
        self.action_send_mail('endorse_notification_to_provider_assessment_mail_template', provider_email, None) 
        self.action_send_mail('endorse_signoff_assessment_mail_template', recipients, None) 

        self.write({'state': 'done', 'assessment_date':fields.Date.today(), 'endorsed': True})

    def action_print_all_certficate(self):
        if self.qualification_assessment_type or self.learnership_assessment_type:   
            return self.env.ref('inseta_etqa.assessment_certificate_report').report_action(self)
        else:
            raise ValidationError('Sorry !!! You can only print certificate for qualification / learnership programmes')

    def action_print_result_statement(self):# TODO
        return self.env.ref('inseta_etqa.assessment_result_statement_report').report_action(self)


    def action_print_appointment_letter(self):
        return self.env.ref('inseta_etqa.learner_appointment_letter_report').report_action(self)

    def action_print_reject_letter(self):
        return self.env.ref('inseta_etqa.learner_rejection_letter_report').report_action(self)

    def action_send_mail(self, with_template_id, email_items= None, email_from=None):
        '''args: email_items = [lists of emails]'''
        # email_items = list(filter(bool, email_items))
        email_to = (','.join([m for m in list(filter(bool, email_items))])) if email_items else False
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('inseta_etqa', with_template_id)[1]         
        if template_id:
            ctx = dict()
            ctx.update({
                'default_model': f'{self._name}',
                'default_res_id': self.id,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'default_email': email_to,
            })
            template_rec = self.env['mail.template'].browse(template_id)
            if email_to:
                template_rec.write({'email_to': email_to})
            template_rec.with_context(ctx).send_mail(self.id, True)

    def _send_mail(self, record_id, template_name, emails):
        try:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('inseta_etqa', template_name)[1]
            ctx = dict()
            ctx.update({
                'default_model': 'inseta.assessment',
                'default_res_id': record_id,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'email_to': emails,
            })
            mail_rec = self.env['mail.template'].browse(template_id).with_context(ctx).send_mail(record_id, True)

        except ValueError as e:
            _logger.info(f'Error while sending reminder: {e}')

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaAssessment, self).default_get(fields_list)
        etqa_eval_committee, etqa_admin, etqa_manager, etqa_verfier = self._get_group_users()
        res.update({
            'etqa_admin_ids': etqa_admin,
            'etqa_manager_ids': etqa_manager,
        })
        return res
    
    def domain_evaluating_committee_user_groups(self):
        etqa_eval_committee, etqa_admin, etqa_manager, etqa_verfier = self._get_group_users()
        return [('id','in', [res.id for res in etqa_eval_committee])]
    
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.verification.request')
        vals['name'] = sequence or '/'
        return super(InsetaVerificationRequest, self).create(vals)