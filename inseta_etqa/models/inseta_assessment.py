from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class InsetaLearnerAssessmentStatus(models.Model):
    _name = 'inseta.assessment.status.model'
    _description = "Inseta Assessment Status"

    name = fields.Char('Description', required=False)
    code = fields.Char('Saqa Code')
    active = fields.Boolean('Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
 

class InsetaLearnerAssessmentBulkApproval(models.TransientModel):
    _name = "inseta.assessment.bulk.order"
    _description = "Bulk Approval"

    def confirm_bulk_approval(self):
        for record in self._context.get('active_ids'):
            assessment = self.env[self._context.get('active_model')].browse(record)
            assessment.action_bulk_method()


class InsetaLearnerAssessmentDetails(models.Model):
    _name = "inseta.learner.assessment.detail"
    _description = "Holds the learner assessment details record"
    _order= "id desc"
    _rec_name= "learner"

    learner_id_no = fields.Char('Identification')
    learner = fields.Many2one("inseta.learner", 'Learner ID')
    provider_id = fields.Many2one("inseta.provider", 'Provider',store=True, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])
    provider_sdl = fields.Char('Provider SDL / N No.')
    verification_date = fields.Date('Verification Date')
    is_partial_assessment = fields.Boolean('Is Partial assessment?')
    
    provider_reference = fields.Integer('Provider ID')
    assessment_reference = fields.Integer('Assessment Ref')
    # left here because of conflicted column
    learner_id = fields.Many2one("inseta.learner.register", 'Learner ID')
    learner_register_id = fields.Many2one("inseta.learner.register", 'Learner ID')
    assessment_id = fields.Many2one("inseta.assessment", 'Assessment ID')
    verification_status = fields.Many2one("inseta.verification.status", string='Verification status')
    core_credits = fields.Integer('Core', default=0, compute="_compute_credits")
    fundamental_credits = fields.Integer('Fundamental', default=0, compute="_compute_credits")
    elective_credits = fields.Integer('Elective', default=0, compute="_compute_credits")
    total_credits = fields.Integer('Total Credits', compute="compute_total_credits")
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status') #, default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    enrollment_date = fields.Date('Enrollment Date')

    programme_core_credits = fields.Integer('Core', default=0)
    programme_fundamental_credits = fields.Integer('Fundamental', default=0,)
    programme_elective_credits = fields.Integer('Elective', default=0,)
    programme_total_credits = fields.Integer('Total Credits',)
    
    active = fields.Boolean(string='Active', default=True)
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')

    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
    financial_year_id = fields.Many2one('res.financial.year', required=False)
    approved_date = fields.Date('Approved Date')
    certificate_number = fields.Char('Certificate Number')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    lga_number = fields.Char('LGA Number')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    legacy_system_id = fields.Integer(string='Legacy System ID')
    student_number = fields.Char('Verification Number')
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','Achieved'),
            ('unachieved','Unachieved'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Programme Status"
    )
    assessment_type = fields.Selection([
        ('unit', 'Unit standard'), 
        ('skill', 'Skills'), 
        ('learner', 'Learnership'),
        ('qual', 'Qualification'),
        ('candidacy', 'Candidacy'),
        ('intern', 'Internship'),
        ('bursary', 'Bursary'),
        ('wiltvet', 'Wiltvet'),
        # ('all', 'All'),
        ], string="Assessment type ?")
    unit_assessment_type = fields.Boolean('Unit standard type')
    qualification_assessment_type = fields.Boolean('Qualification type')
    learnership_assessment_type = fields.Boolean('Learnership type')
    skill_assessment_type = fields.Boolean('Skills type')
    candidacy_assessment_type = fields.Boolean('Candidacy type')
    wiltvet_assessment_type = fields.Boolean('Wiltvet type')
    bursary_assessment_type = fields.Boolean('Bursary type')
    internship_assessment_type = fields.Boolean('Internship type')
    # new fields 
    learner_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_assessment_learner_detail_rel', 'inseta_learnership_assessment_learner_detail_id', string='Learnership')
    skill_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_skill_assessment_detail_rel', 'inseta_learnership_assessment_skkill_detail_id', string='Skill programmes')
    qualification_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_qual_assessment_detail_rel','inseta_learnership_skill_assessment_detail_id', string='Qualification programmes')
    unit_standard_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_unit_standard_assessment_detail_rel','inseta_unit_standard_assessment_detail_id', string='Unit Standard')
    candidacy_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_candidacy_assessment_detail_rel','inseta_candidacy_assessment_detail_id', string='Candidacy')
    bursary_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_bursary_assessment_detail_rel','inseta_bursary_assessment_detail_id', string='Bursary')
    internship_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_internship_assessment_detail_rel','inseta_internship_assessment_detail_id', string='Internship')
    wiltvet_programmes_line_ids = fields.Many2many("inseta.learnership.assessment", 'inseta_learnership_wiltvet_assessment_detail_rel','inseta_wiltvet_assessment_detail_id', string='WILTVET')
    lenght_of_line = fields.Integer('Line length', store=True, 
    help='''Use to determine the original number of lines - if lines are delete, 
    a contrain will check and compare if the total assessment lines is equal to the lenght of line value''')

    endorsed = fields.Boolean('Endorsed', default=False)
    state = fields.Selection([
        ('draft', 'New'), 
        ('rework', 'Pending Additional Information'),
        ('pending_allocation', 'ETQA Admin'),
        ('queried', 'Queried/Rework'),
        ('pending_verification', 'Verification report'),
        ('manager_verify', 'Manager to Verify'),
        ('verified', 'Programme Assessment'), 
        ('awaiting_rejection', 'Request Rejection'), 
        ('awaiting_rejection2', 'Awaiting Rejection'),
        ('manager', 'ETQA Admin to Approve'),
        ('done', 'Approved'),
        ('partial', 'Partial Achievement'),
        ('reject', 'Rejected')], default='draft', string="Status")
    assessment_date = fields.Date('Assessment Date')
    approved_date = fields.Date('Approval Date')
    refusal_comment = fields.Text(string='Refusal Comments')

    #discard
    learner_assessment_line = fields.One2many('inseta.learnership.assessment', 'learner_assessment_detail_id', string='Learner Assessment Line')	
    
    # changes 

    assessor_id = fields.Many2one("inseta.assessor", 'Assesssor', domain=lambda act: [('active', '=', True)])
    assessment_date = fields.Date('Assessment Date')
    moderator_id = fields.Many2one("inseta.moderator", 'Moderator', domain=lambda act: [('active', '=', True)])
    moderator_date = fields.Date('Moderation Date')

    learner_qualification_id = fields.Many2one("inseta.qualification.learnership", string='Qualification')
    learner_learnership_id = fields.Many2one("inseta.learner.learnership", string='Learner learnership')
    unit_standard_learnership_id = fields.Many2one("inseta.unit_standard.learnership", string='Unit Standard learnership')
    learner_skill_learnership_id = fields.Many2one("inseta.skill.learnership", string='Skills learnership')

    qualification_learnership_line = fields.Many2many("inseta.learner_qualification.assessment", 'inseta_learner_qualification_ass_rel', 'inseta_qual_ass_id', 'inseta_assessment_detail_id', string='Qualification Learnership Assessment')
    learnership_learnership_line = fields.Many2many("inseta.learner_learnership.assessment", 'inseta_learnership_ass_rel', 'inseta_learnership_ass_id', 'inseta_assessment_detail_id', string='Learnership Assessment')
    skills_learnership_line = fields.Many2many("inseta.skill_learnership.assessment", 'inseta_skill_learnership_ass_rel', 'inseta_skill_learnership_ass_id', 'inseta_assessment_detail_id', string='Learnership Assessment')
    unit_standard_learnership_line = fields.Many2many("inseta.unit_standard.assessment", 'inseta_unitstandard_ass_rel', 'inseta_unitstandard_learnership_ass_id', 'inseta_assessment_detail_id', string='Unitstandard Learnership Assessment')
    
    # qualification_learnership_line = fields.One2many("inseta.learner_qualification.assessment", 'learner_qualification_id', string='Qualification Assessment')
    # learnership_learnership_line = fields.One2many("inseta.learner_learnership.assessment", 'learner_learnership_id', string='Learnership Assessment')
    # skills_learnership_line = fields.One2many("inseta.skill_learnership.assessment", 'learner_skill_learnership_id', string='Skill Assessment')
    # unit_standard_learnership_line = fields.One2many("inseta.unit_standard.assessment", 'unit_standard_learnership_id', string='Unitstandard Learnership Assessment')
    
    qualification_partial_assessment_line = fields.Many2many("learner.qualification.partial_assessment", 'inseta_learner_qual_partial_ass_rel', 'inseta_qual_ass_id', 'inseta_assessment_detail_id', string='Qualification Learnership Partial Assessment')
    learnership_partial_assessment_line = fields.Many2many("learner.learnership.partial_assessment", 'inseta_learnership_partial_ass_rel', 'inseta_learnership_ass_id', 'inseta_assessment_detail_id', string='Learnership Partial Assessment')
    skills_partial_assessment_line = fields.Many2many("learner_skills.partial_assessment", 'inseta_skills_partial_ass_rel', 'inseta_skill_learnership_ass_id', 'inseta_assessment_detail_id', string='Learnership Partial Assessment')
    unit_standard_partial_assessment_line = fields.Many2many("unit_standard.partial_assessment", 'unitstandard_partial_ass_rel', 'inseta_unitstandard_learnership_ass_id', 'inseta_assessment_detail_id', string='Unitstandard Partial Assessment')
    
    # changes stop
    
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
                if self.financial_year_id:
                    return self._learner_programme()
            else:
                self.provider_id = False
                self.provider_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

    @api.onchange('learner_id_no')
    def _onchange_learner_id_no(self):
        if self.learner_id_no:
            learner = self.env['inseta.learner'].search([('id_no', '=', self.learner_id_no)], limit=1)
            if learner:
                self.learner = learner.id
            else:
                self.learner_id_no = False
                self.learner = False
                return {'warning':{'title':'Invalid Message','message':'The learner with ID is not a valid learner'}}

    @api.onchange('learner')
    def _onchange_learner(self):
        if self.learner:
            self.learner_id_no = self.learner.id_no

    @api.onchange('financial_year_id')
    def _onchange_financial_year_id(self):
        if self.learner and self.financial_year_id:
            return self._learner_programme()
 
    @api.depends('fundamental_credits', 'core_credits', 'elective_credits')
    def compute_total_credits(self):
        for rec in self:
            if rec.fundamental_credits or rec.core_credits or rec.elective_credits:
                rec.total_credits = rec.core_credits + rec.fundamental_credits + rec.elective_credits
            else:
                rec.total_credits = 0

    @api.onchange('moderator_date')
    def _onchange_date(self):
        if self.assessment_date and self.moderator_date:
            if self.moderator_date < self.assessment_date:
                self.moderator_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Moderator date cannot be less than the Assessment date"
                    }
                }

    @api.onchange('learner_qualification_id', 'learner_learnership_id', 'learner_skill_learnership_id')
    def _compute_programme_credits(self):
        if self.learner_qualification_id:
            programmeid = self.learner_qualification_id
            core = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('qualification_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name == 'Core')])
            fundamental = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('qualification_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name == 'Fundamental')])
            elective = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('qualification_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name in ['Elective', 'Compulsory Elective'])])
            self.programme_core_credits = core
            self.programme_fundamental_credits = fundamental
            self.programme_elective_credits = elective
            self.programme_total_credits = sum([core, fundamental, elective])

        elif self.learner_learnership_id:
            programmeid = self.learner_learnership_id
            core = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('learnership_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name == 'Core')])
            fundamental = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('learnership_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name == 'Fundamental')])
            elective = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('learnership_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name in ['Elective', 'Compulsory Elective'])])
            self.programme_core_credits = core
            self.programme_fundamental_credits = fundamental
            self.programme_elective_credits = elective
            self.programme_total_credits = sum([core, fundamental, elective])

        elif self.learner_skill_learnership_id:
            programmeid = self.learner_skill_learnership_id
            core = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('skills_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name == 'Core')])
            fundamental = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('skills_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name == 'Fundamental')])
            elective = sum([rec.unit_standard_id.credits for rec in programmeid.mapped('skills_unit_standard_ids').filtered(lambda cr: cr.unit_standard_type.name in ['Elective', 'Compulsory Elective'])])
            self.programme_core_credits = core
            self.programme_fundamental_credits = fundamental
            self.programme_elective_credits = elective
            self.programme_total_credits = sum([core, fundamental, elective])

    @api.onchange('learner_qualification_id')
    def _onchange_learner_qualification_id(self):
        self.qualification_learnership_line = False
        if self.learner_qualification_id and not self.is_partial_assessment:
            line_length = 0
            learner_qualification_ids = self.learner_qualification_id.mapped('qualification_unit_standard_ids')
            learner_qualification_assessment_ids = self.env['inseta.learner_qualification.assessment'].search([('learner_qualification_id.id', '=', self.learner_qualification_id.id)])
            if learner_qualification_assessment_ids:
                for record in learner_qualification_assessment_ids:
                    self.qualification_learnership_line = [(4, record.id)]
                    line_length += 1
            else: 
                if learner_qualification_ids:
                    for rec in learner_qualification_ids:
                        vals = {
                            'unit_standard_id': rec.unit_standard_id.id,
                            'learner_id': self.learner.id,
                            'credits': rec.unit_standard_id.credits,
                            'unit_standard_type_id': rec.unit_standard_type.id,
                            'learner_qualification_id': self.learner_qualification_id.id,
                            'inseta_assessment_detail_id': self.id,
                        }
                        record = self.env['inseta.learner_qualification.assessment'].create(vals)
                        self.qualification_learnership_line = [(4, record.id)]
                        line_length += 1
            self.lenght_of_line += line_length

        elif self.learner_qualification_id and self.is_partial_assessment:
            self.qualification_learnership_line = False
            competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
            records = self.env['inseta.learner_qualification.assessment'].search([
                ('learner_qualification_id', '=', self.learner_qualification_id.id),
                ('assessment_status_id', '=', competent_id.id),
                ])
            record_lists = []
            if records:
                record_lists += [rec.id for rec in records]
                # self.qualification_learnership_line = [(6, 0, [rec.id for rec in records])]
                # [(5, _, record.id)]
            partial_assessment_ids = self.learner_qualification_id.learner_qualification_partial_assessment_ids
            if partial_assessment_ids:
                record_lists += [rec.learner_qualification_assessment_id.id for rec in partial_assessment_ids]
            self.lenght_of_line += len(record_lists)
            self.qualification_learnership_line = [(6, 0, record_lists)]    

    
    @api.onchange('learner_learnership_id')
    def _onchange_learner_learnership_id(self):
        # self.check_if_assessment_exists()
        self.learnership_learnership_line = False
        if self.learner_learnership_id and not self.is_partial_assessment:
            line_length = 0
            learner_learnership_ids = self.learner_learnership_id.mapped('learnership_unit_standard_ids')
            learner_learnership_assessment_ids = self.learner_learnership_id.mapped('learnership_assessment_ids') or \
            self.env['inseta.learner_learnership.assessment'].search([('learner_learnership_id.id', '=', self.learner_learnership_id.id)])
            if learner_learnership_assessment_ids:
                for record in learner_learnership_assessment_ids:
                    self.learnership_learnership_line = [(4, record.id)]
                    line_length += 1
            elif learner_learnership_ids: 
                for rec in learner_learnership_ids:
                    vals = {
                        'unit_standard_id': rec.unit_standard_id.id,
                        'learner_id': self.learner.id,
                        'credits': rec.unit_standard_id.credits,
                        'learner_learnership_id': self.learner_learnership_id.id,
                        'unit_standard_type_id': rec.unit_standard_type.id,
                        'inseta_assessment_detail_id': self.id,
                    }
                    record = self.env['inseta.learner_learnership.assessment'].create(vals)
                    self.learnership_learnership_line = [(4, record.id)]
                    line_length += 1
            else:
                raise ValidationError("No unit standard or assessments found")
            self.lenght_of_line += line_length
        elif self.learner_learnership_id and self.is_partial_assessment:
            self.learnership_learnership_line = False
            competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
            records = self.env['inseta.learner_learnership.assessment'].search([
                ('learner_learnership_id', '=', self.learner_learnership_id.id),
                ('assessment_status_id', '=', competent_id.id),
                ])
            record_lists = []
            if records:
                # raise ValidationError(record_lists)
                record_lists += [rec.id for rec in records]
            partial_assessment_ids = self.learner_learnership_id.learner_learnership_partial_assessment_ids
            if partial_assessment_ids:
                record_lists += [rec.learner_learnership_assessment_id.id for rec in partial_assessment_ids]
            self.lenght_of_line += len(record_lists)
            self.learnership_learnership_line = [(6, 0, record_lists)]
        # else:
        #     record = self.env['inseta.learner_learnership.assessment'].search([('inseta_assessment_detail_id', '=', self.id)])
        #     if record:
        #         self.learnership_learnership_line = [(5, _, record.id)]

    @api.onchange('learner_skill_learnership_id')
    def _onchange_learner_skill_learnership_id(self):
        if self.learner_skill_learnership_id and not self.is_partial_assessment:
            self.skills_learnership_line = False
            line_length = 0
            skills_unit_standard_ids = self.learner_skill_learnership_id.mapped('skills_unit_standard_ids')
            skills_unit_standard_assessment_ids = self.env['inseta.skill_learnership.assessment'].search([('learner_skill_learnership_id.id', '=', self.learner_skill_learnership_id.id)])
            if skills_unit_standard_assessment_ids:
                for record in skills_unit_standard_assessment_ids:
                    self.skills_learnership_line = [(4, record.id)]
                    line_length += 1
            else:
                if skills_unit_standard_ids:      
                    for rec in skills_unit_standard_ids:
                        vals = {
                            'unit_standard_id': rec.unit_standard_id.id,
                            'learner_id': self.learner.id,
                            'credits': rec.unit_standard_id.credits,
                            'learner_skill_learnership_id': self.learner_skill_learnership_id.id,
                            'inseta_assessment_detail_id': self.id,
                            'unit_standard_type_id': rec.unit_standard_type.id,
                        }
                        record = self.env['inseta.skill_learnership.assessment'].create(vals)
                        self.skills_learnership_line = [(4, record.id)]
                        line_length += 1
            self.lenght_of_line += line_length
        elif self.learner_skill_learnership_id and self.is_partial_assessment:
            self.skills_learnership_line = False
            competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
            records = self.env['inseta.skill_learnership.assessment'].search([
                ('learner_skill_learnership_id', '=', self.learner_skill_learnership_id.id),
                ('assessment_status_id', '=', competent_id.id),
                ])
            record_lists = []
            if records:
                record_lists += [rec.id for rec in records]
            partial_assessment_ids = self.learner_skill_learnership_id.learner_skill_partial_assessment_ids
            if partial_assessment_ids:
                record_lists += [rec.learner_skill_assessment_id.id for rec in partial_assessment_ids]
            self.lenght_of_line += len(record_lists)
            self.skills_learnership_line = [(6, 0, record_lists)]
        # else:
        #     record = self.env['inseta.skill_learnership.assessment'].search([('inseta_assessment_detail_id', '=', self.id)])
        #     if record:
        #         self.skills_learnership_line = [(5, _, record.id)]

    def check_if_assessment_exists(self):
        """Check if there is an already existing assesment that is not in draft 
        if true, raise validation to let user location and continue with the record
        if state is done"""
        pass 
        # if self.learner_learnership_id and not self.is_partial_assessment:
        #     domain = [
        #         ('learner_id', '=', self.learner.id),
        #         ('learner_learnership_id', '=', self.learner_learnership_id.id)
        #         ]
        #     existing_assessment = self.env['inseta.learner_learnership.assessment'].search(domain)
        #     if existing_assessment:
        #         if existing_assessment.inseta_assessment_detail_id.state in ['pending_allocation', 'manager_verify', 'manager']:
        #             raise ValidationError('Sorry... You have pending assessment that is currently in process !!!')

        #         elif existing_assessment.inseta_assessment_detail_id.state in ['done']:
        #             raise ValidationError("""Sorry... You have completed an assessment for this learner.\
        #              Kindly use the 'is partial assessment' checkbox to proceed with partial assessment !!!""")


    @api.depends('qualification_learnership_line.assessment_status_id', 'learnership_learnership_line.assessment_status_id', 'skills_learnership_line.assessment_status_id')
    def _compute_credits(self):
        for record in self:
            qual_ids = record.mapped('qualification_learnership_line')
            learner_ids = record.mapped('learnership_learnership_line')
            skill_ids = record.mapped('skills_learnership_line')

            core_credits, fundamental_credits, elective_credits = 0, 0, 0
            competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
            core_type = self.env.ref('inseta_etqa.data_unit_standard_type_1').id
            fundamental_type = self.env.ref('inseta_etqa.data_unit_standard_type_2').id
            elective_type = self.env.ref('inseta_etqa.data_unit_standard_type_3').id
            compulsory_elective_type = self.env.ref('inseta_etqa.data_unit_standard_type_4').id
            if record.qualification_learnership_line:
                core_credits += sum([rec.credits for rec in qual_ids.filtered(lambda cr: cr.unit_standard_type_id.id == core_type and cr.assessment_status_id.id == competent_id.id)])
                fundamental_credits += sum([rec.credits for rec in qual_ids.filtered(lambda cr: cr.unit_standard_type_id.id == fundamental_type and cr.assessment_status_id.id == competent_id.id)])
                elective_credits += sum([rec.credits for rec in qual_ids.filtered(lambda cr: cr.unit_standard_type_id.id in [elective_type, compulsory_elective_type] and cr.assessment_status_id.id == competent_id.id)])
            
            elif record.learnership_learnership_line:
                core_credits += sum([rec.credits for rec in learner_ids.filtered(lambda cr: cr.unit_standard_type_id.id == core_type and cr.assessment_status_id.id == competent_id.id)])
                fundamental_credits += sum([rec.credits for rec in learner_ids.filtered(lambda cr: cr.unit_standard_type_id.id == fundamental_type and cr.assessment_status_id.id == competent_id.id)])
                elective_credits += sum([rec.credits for rec in learner_ids.filtered(lambda cr: cr.unit_standard_type_id.id in [elective_type, compulsory_elective_type] and cr.assessment_status_id.id == competent_id.id)])
                
            elif record.skills_learnership_line:
                core_credits += sum([rec.credits for rec in skill_ids.filtered(lambda cr: cr.unit_standard_type_id.id == core_type and cr.assessment_status_id.id == competent_id.id)])
                fundamental_credits += sum([rec.credits for rec in skill_ids.filtered(lambda cr: cr.unit_standard_type_id.id == fundamental_type and cr.assessment_status_id.id == competent_id.id)])
                elective_credits += sum([rec.credits for rec in skill_ids.filtered(lambda cr: cr.unit_standard_type_id.id in [elective_type, compulsory_elective_type] and cr.assessment_status_id.id == competent_id.id)])
                
            else:
                record.core_credits = 0
                record.fundamental_credits = 0
                record.elective_credits = 0 

            record.core_credits = core_credits
            record.fundamental_credits = fundamental_credits
            record.elective_credits = elective_credits

    def compute_programme_credits(self, programmeid):
        self.programme_core_credits = core
        self.programme_fundamental_credits = fundamental
        self.programme_elective_credits = elective
        self.programme_total_credits = sum([core, fundamental, elective])

    def get_partial_lines(self, assessment_line):
        """assessment_line: e.g str=> 'learnership_learnership_line'
        vals: vals = {
                'inseta_assessment_detail_id':  self.id, 
                'learner_qualification_id':  self.id, 
                'learner_qualification_assessment_id':  self.id, 
            }
        """
        assessmentline = self.mapped(f'{assessment_line}')
        competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
        uncompetent_assessments = assessmentline.filtered(lambda s: s.completed != True)
        return uncompetent_assessments

    def create_partial_assessment(self):
        if not self.is_partial_assessment:
            if self.learner_learnership_id:
                uncompetent_assessments = self.get_partial_lines('learnership_learnership_line')
                for ass in uncompetent_assessments: 
                    vals = {
                        'inseta_assessment_detail_id':  self.id, 
                        'learner_learnership_id':  self.learner_learnership_id.id, 
                        'learner_learnership_assessment_id': ass.id, 
                    }
                    self.env['learner.learnership.partial_assessment'].create(vals)
                    
            if self.learner_skill_learnership_id:
                uncompetent_assessments = self.get_partial_lines('skills_learnership_line')
                for ass in uncompetent_assessments: 
                    vals = {
                        'inseta_assessment_detail_id':  self.id or ass.inseta_assessment_detail_id.id, 
                        'learner_skill_learnership_id':  self.learner_skill_learnership_id.id, 
                        'learner_skill_assessment_id':  ass.id, 
                    }
                    self.env['learner.skill.partial_assessment'].create(vals)

            if self.learner_qualification_id:
                uncompetent_assessments = self.get_partial_lines('qualification_learnership_line')
                for ass in uncompetent_assessments:
                    vals = {
                        'inseta_assessment_detail_id':  self.id, 
                        'learner_qualification_id':  self.learner_qualification_id.id, 
                        'learner_qualification_assessment_id':  ass.id, 
                    }
                    self.env['learner.qualification.partial_assessment'].create(vals)

    def update_assessment_line(self, rec):
        rec.assessor_id = self.assessor_id.id 
        rec.moderator_id = self.moderator_id.id 
        rec.assessment_date = self.assessment_date 
        rec.moderator_date = self.moderator_date

    def update_assessment_status(self, result_id):
        competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
        qualification_assessment = self.mapped('qualification_learnership_line').filtered(lambda s: s.select == True and s.completed != True)
        for rec in qualification_assessment:
            rec.assessment_status_id = result_id

        for rec in self.mapped('learnership_learnership_line').filtered(lambda s: s.select == True and s.completed != True):
            rec.assessment_status_id = result_id

        for rec in self.mapped('skills_learnership_line').filtered(lambda s: s.select == True and s.completed != True):
            rec.assessment_status_id = result_id

    def action_mark_all_competent(self):
        competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
        self.update_assessment_status(competent_id.id)

    def action_mark_all_not_competent(self):
        incompetent_id = self.env.ref('inseta_etqa.id_assessment_status_incompetent')
        self.update_assessment_status(incompetent_id.id)

    def update_select_option(self, status):
        for rec in self.mapped('qualification_learnership_line'):
            rec.select = status 
        for rec in self.mapped('learnership_learnership_line'):
            rec.select = status
        for rec in self.mapped('skills_learnership_line'):
            rec.select = status

    def action_select_all(self):
        self.update_select_option(True)

    def action_deselect_all(self):
        self.update_select_option(False)

    def action_bulk_method(self):
        for rec in self:
            if rec.state == 'manager':
                rec.state = 'done'

    def action_update_assessors(self):
        competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
        if self.assessor_id and self.assessment_date:
            qualification_assessment = self.mapped('qualification_learnership_line').filtered(lambda s: s.select == True and s.completed != True)
            for rec in qualification_assessment:
                self.update_assessment_line(rec)
                # self.update_achieved_credits(rec)

            for rec in self.mapped('learnership_learnership_line').filtered(lambda s: s.select == True and s.completed != True):
                self.update_assessment_line(rec)

            for rec in self.mapped('skills_learnership_line').filtered(lambda s: s.select == True and s.completed != True):
                self.update_assessment_line(rec)
        else:
            raise ValidationError("Please select Assessor and assessment date !!!") 

    def _learner_programme(self):
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        qualification_line = self.learner.mapped('qualification_learnership_line').filtered(lambda lrn: lrn.programme_status_id.id != completed_status and lrn.commencement_date >= self.financial_year_id.date_from and lrn.commencement_date <= self.financial_year_id.date_to and lrn.provider_id.id == self.provider_id.id)
        learnership_line = self.learner.mapped('learner_learnership_line').filtered(lambda lrn: lrn.commencement_date >= self.financial_year_id.date_from and lrn.commencement_date <= self.financial_year_id.date_to and lrn.programme_status_id.id != completed_status)# and lrn.provider_id == self.provider_id.id)
        # skill_learnership_line = self.learner.mapped('skill_learnership_line').filtered(lambda lrn: lrn.provider_id.id == self.provider_id.id and lrn.commencement_date >= self.financial_year_id.date_from and lrn.commencement_date <= self.financial_year_id.date_to and lrn.programme_status_id.id != completed_status)
        skill_learnership_line = self.learner.mapped('skill_learnership_line').filtered(lambda lrn: lrn.commencement_date >= self.financial_year_id.date_from and lrn.commencement_date <= self.financial_year_id.date_to and lrn.programme_status_id.id != completed_status)
        unit_standard_learnership_line = self.learner.mapped('unit_standard_learnership_line').filtered(lambda lrn: lrn.commencement_date >= self.financial_year_id.date_from and lrn.commencement_date <= self.financial_year_id.date_to and lrn.programme_status_id.id != completed_status and lrn.provider_id.id == self.provider_id.id)
        assessor_ids = self.provider_id.mapped('provider_assessor_ids').filtered(lambda pr: pr.active == True)
        moderator_ids = self.provider_id.mapped('provider_moderator_ids').filtered(lambda pr: pr.active == True)
        return {
            'domain': {
                'learner_qualification_id': [('id', 'in', [rec.id for rec in qualification_line])],
                'learner_learnership_id': [('id', 'in', [rec.id for rec in learnership_line])],
                'learner_skill_learnership_id': [('id', 'in', [rec.id for rec in skill_learnership_line])],
                'unit_standard_learnership_id': [('id', 'in', [rec.id for rec in unit_standard_learnership_line])],
                'assessor_id': [('id', 'in', [rec.assessor_id.id for rec in assessor_ids])],
                'moderator_id': [('id', 'in', [rec.moderator_id.id for rec in moderator_ids])],
                'unit_standard_learnership_id': [('id', 'in', [rec.id for rec in unit_standard_learnership_line])],
            }
        } 

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].sudo().search([('user_id', '=', user)], limit=1)
        return provider.id

    def action_verification_signoff(self): 
        enrollment_date = self.learner_learnership_id.enrollment_date or self.learner_qualification_id.enrollment_date or self.learner_skill_learnership_id.enrollment_date
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = etqa_manager_admin_login
        self.action_send_mail('send_to_manager_assessment_detail_mail_template', recipients, None) 
        self.write({'state': 'manager', 'assessment_date':fields.Date.today(), 'enrollment_date': enrollment_date})
        
    def action_send_mail(self, with_template_id, email_items= None, email_from=None):
        '''args: email_items = [lists of emails]'''
        # email_items = list(filter(bool, email_items))
        email_items.append('verifications@inseta.org.za')
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
            etqa_committee_users = etqa_committee.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        if etqa_admin:
            etqa_admin_users = etqa_admin.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        if etqa_manager:
            etqa_manager_users = etqa_manager.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        if etqa_verifier:
            etqa_verifier_user = etqa_verifier.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        return etqa_committee_users, etqa_admin_users, etqa_manager_users, etqa_verifier_user

    def compute_result(self, result_status):
        competent_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
        if self.learner_qualification_id:
            for comp in self.mapped('qualification_learnership_line').filtered(lambda s: s.assessment_status_id.id == competent_id.id):
                comp.completed = True
            self.learner_qualification_id.programme_status_id = result_status
        
        elif self.learner_learnership_id:
            for comp in self.mapped('learnership_learnership_line').filtered(lambda s: s.assessment_status_id.id == competent_id.id):
                comp.completed = True
            self.learner_learnership_id.programme_status_id = result_status

        elif self.learner_skill_learnership_id:
            for comp in self.mapped('skills_learnership_line').filtered(lambda s: s.assessment_status_id.id == competent_id.id):
                comp.completed = True
            self.learner_skill_learnership_id.programme_status_id = result_status

    def action_done(self):
        achieved_status = self.env.ref('inseta_etqa.id_programme_status_02')
        incompleted_status = self.env.ref('inseta_etqa.id_programme_status_03')
        if self.total_credits >= self.programme_total_credits:
            self.compute_result(achieved_status.id)
            self.programme_status_id = achieved_status.id
        else:
            self.compute_result(incompleted_status.id)
            self.programme_status_id = incompleted_status.id
            self.create_partial_assessment()
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = etqa_manager_admin_login
        provider_email = [self.provider_id.email]
        self.action_send_mail('endorse_notification_to_provider_assessment_detail_mail_template', provider_email, None) 
        self.action_send_mail('endorse_signoff_assessment_detail_mail_template', recipients, None) 
        self.write({'state': 'done', 'approved_date':fields.Date.today(), 'endorsed': True})

    def action_done_old(self):
        for details in self:
            learnerObj = details.learner
            if details.qualification_programmes_line_ids:
                for line in details.qualification_programmes_line_ids:
                    line.action_validate_result(learnerObj, False)

            if details.learner_programmes_line_ids:
                for line in details.learner_programmes_line_ids:
                    line.action_validate_result(learnerObj)

            if details.skill_programmes_line_ids:
                for line in details.skill_programmes_line_ids:
                    line.action_validate_result(learnerObj)

            if details.bursary_programmes_line_ids:
                for line in details.bursary_programmes_line_ids:
                    line.action_validate_result(learnerObj)

            if details.internship_programmes_line_ids:
                for line in details.internship_programmes_line_ids:
                    line.action_validate_result(learnerObj, True)

            if details.candidacy_programmes_line_ids:
                for line in details.candidacy_programmes_line_ids:
                    line.action_validate_result(learnerObj, True)

            if details.wiltvet_programmes_line_ids:
                for line in details.wiltvet_programmes_line_ids:
                    line.action_validate_result(learnerObj, True)

            if details.unit_standard_line_ids:
                for line in details.unit_standard_line_ids:
                    line.action_validate_result(learnerObj, True)

        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = etqa_manager_admin_login
        provider_email = [self.provider_id.email]
        self.env['inseta.assessment'].action_send_mail('endorse_notification_to_provider_assessment_mail_template', provider_email, None) 
        self.env['inseta.assessment'].action_send_mail('endorse_signoff_assessment_mail_template', recipients, None) 
        self.write({'state': 'done', 'approved_date':fields.Date.today(), 'endorsed': True})

    def action_reject_assesment_submit(self):
        emails = []
        if not self.refusal_comment:
            raise ValidationError("Please provide a reason in the refusal comment section")
        if self.state == "pending_allocation":
            self.state = "draft"

        elif self.state in ["pending_allocation", "pending_verification"]:
            self.state = "draft"

        elif self.state == "manager_verify":
            self.state = "pending_verification"

        elif self.state == "verified":
            raise ValidationError("You cannot reject this application at this stage.")
        
        elif self.state == "manager":
            self.state = "verified"

        else:
            self.state = "draft"
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = etqa_manager_admin_login
        recipients.append(self.provider_id.email)
        self.env['inseta.assessment'].action_send_mail('reject_assessment_mail_template', recipients, None)

    def action_print_all_certficate(self):
        if self.qualification_assessment_type or self.learnership_assessment_type: 
            if self.programme_total_credits > self.total_credits:
                raise ValidationError('You can only print certificates when total achieved credits are greater than the total minimum credits...')
            self.sudo().write({'certificate_created_date': fields.Date.today()})
            return self.env.ref('inseta_etqa.main_assessment_certificate_report').sudo().report_action(self)
        else:
            raise ValidationError('Sorry !!! You can only print certificate for qualification / learnership programmes')

    def action_print_result_statement(self): 
        return self.env.ref('inseta_etqa.main_assessment_result_statement_report').report_action(self) 

    @api.constrains('qualification_learnership_line')
    def constraint_assessment_line(self):
        self.check_assessment_line()

    @api.onchange('qualification_learnership_line')
    def onchange_qualification_learnership_line(self):
        self.check_assessment_line()

    @api.onchange('learnership_learnership_line')
    def onchange_learnership_learnership_line(self):
        self.check_assessment_line()

    @api.onchange('skills_learnership_line')
    def onchange_skills_learnership_line(self):
        self.check_assessment_line()

    def check_assessment_line(self):
        # computes the total lenght of lines, onchange, it reduce the final length on delete
        #  
        line_length = 0
        if self.qualification_learnership_line:
            line_length += len([rec.id for rec in self.qualification_learnership_line])

        if self.learnership_learnership_line:
            line_length += len([rec.id for rec in self.learnership_learnership_line])

        if self.skills_learnership_line:
            line_length += len([rec.id for rec in self.skills_learnership_line])
        
        if line_length != self.lenght_of_line:
            raise ValidationError("Sorry!!! You are not allow to remove assessment lines, kindly check the partial assessment option or discard.")

    def unlink(self):
        for delete in self.filtered(lambda delete: delete.state not in ['draft','reject', 'rework']):
            raise ValidationError(_('You cannot delete an assessent which is in %s state.') % (delete.state,))
        return super(InsetaLearnerAssessmentDetails, self).unlink()

class InsetaAssessment(models.Model):
    _name = "inseta.assessment"
    _order= "id desc"
    _description = "Inseta ETQA assessment for learners"

    name = fields.Char('Description')
    reference = fields.Char('Reference')
    verification_number = fields.Char('Verification number')
    active = fields.Boolean(string='Active', default=True)
    assessment_date = fields.Date('Assessment Date')
    verification_date = fields.Date('Verification Date')
    financial_year_id = fields.Many2one('res.financial.year', required=False)
    request_date = fields.Date('Date of Request')
    no_learners = fields.Integer('No of learners', default=1)
    assessment_type = fields.Selection([
        ('unit', 'Unit standard type'), 
        ('skill', 'Skills'), 
        ('learner', 'Learnership'),
        ('qual', 'Qualification'),
        ('candidacy', 'Candidacy'),
        ('intern', 'Internship'),
        ('bursary', 'Bursary'),
        ('wiltvet', 'Wiltvet'),
        # ('all', 'All'),
        ], string="Assessment type ?")
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    qualification_assessment_type = fields.Boolean('Qualification')
    learnership_assessment_type = fields.Boolean('Learnership')
    skill_assessment_type = fields.Boolean('Skills')
    unit_assessment_type = fields.Boolean('Unit type')
    candidacy_assessment_type = fields.Boolean('Candidacy')
    wiltvet_assessment_type = fields.Boolean('Wiltvet')
    bursary_assessment_type = fields.Boolean('Bursary')
    internship_assessment_type = fields.Boolean('Internship')
    legacy_system_id = fields.Integer('Legacy System ID')
    learner_assessment_details = fields.One2many('inseta.learner.assessment.detail', 'assessment_id', string='Learnership Assessment Details')	
    etqa_committee_ids = fields.Many2many(
        'res.users', 
        'etqa_assessment_rel',
        'inseta_learner_assessment_id',
        'res_users_id',
        string='Verifiers', domain=lambda self: self.domain_evaluating_committee_user_groups(),)
    etqa_verifier_ids = fields.Many2many(
        'res.users', 
        'etqa_assessment_rel',
        'inseta_learner_assessment_id',
        'res_users_id',
        string='Verifiers', domain=lambda self: self.domain_evaluating_verifier_users(), help="ETQA admin adds verifiers for the assessment request")

    etqa_admin_ids = fields.Many2many(
        'res.users',
        'etqa_assessment_admin_rel', 
        'inseta_learner_assessment_id',
        'res_users_id',
        string='Evaluation Admin',
        help="Technical Field to compute evaluation admin"
    )

    etqa_manager_ids = fields.Many2many(
        'res.users',
        'etqa_assessment_manager_rel',
        'inseta_learner_assessment_id',
        'res_users_id',
        string='Evaluation Manager (s)',
        help="Technical Field to compute eval manager"
    )
    
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
    
    provider_id = fields.Many2one("inseta.provider", 'Provider', store=True, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])
    physical_code = fields.Char(string='Physical Code', compute="compute_provider_details")
    physical_address1 = fields.Char(string='Physical Address Line 1', compute="compute_provider_details")
    accreditation_number = fields.Char(string='Accreditation number', compute="compute_provider_details")
    end_date = fields.Date(string='DHET Registration End Date', compute="compute_provider_details")
    accreditation_status = fields.Selection([
        ('Primary', 'Primary Provider'),
        ('secondary', 'Secondary Provider'),
    ], string='Accreditation Class', index=True, copy=False, compute="compute_provider_details")
    email = fields.Char(string='Email', compute="compute_provider_details")
    phone = fields.Char(string='Phone', compute="compute_provider_details")
    cell_phone = fields.Char(string='Cell Phone', compute="compute_provider_details")

    organisation_id =  fields.Many2one('inseta.organisation', string='Employer', store=True,  default = lambda self: self.get_organisation_default_user())
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    learner_assessment_document_ids =fields.Many2many("inseta.assessment.document", "learner_assessment_document_rel", string="Learner Assessment document",
    default=lambda v: v.build_provider_document())
    learner_assessment_verification_report_ids = fields.Many2many("inseta.assessment.document", "learner_assessment_verification_document_rel", string="Verification document")
    refusal_comment = fields.Text(string='Refusal Comments')

    @api.depends('provider_id')
    def compute_provider_details(self):
        for rec in self:
            provider = rec.provider_id
            if rec.provider_id:
                rec.physical_code = provider.zip
                rec.physical_address1 = provider.street
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

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].sudo().search([('employer_sdl_no', '=', self.provider_sdl), ('active', '=', True)], limit=1)
            if provider:
                self.provider_id = provider.id
                # self.build_provider_document()
            else:
                self.provider_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

    def build_provider_document(self):
        provider_assessment_document_ids = []
        items = [
            'Verification request form', 
            'Signed Moderator / Assessor report', 
            'Learner list downloaded from the system',
            'Signed NLRD'
            ]
        for doc in items:
            vals = {
                'name': doc,
            }
            document_obj = self.env['inseta.assessment.document']
            provider_assessment_document_id = document_obj.create(vals)
            provider_assessment_document_ids.append(provider_assessment_document_id.id)
        return provider_assessment_document_ids
        # self.learner_assessment_document_ids = [(6, 0, provider_assessment_document_ids)]

    @api.onchange('qualification_assessment_type', 'learnership_assessment_type', 'skill_assessment_type', 'unit_assessment_type')
    def onchange_programme_type(self):
        if self.qualification_assessment_type: 
            self.assessment_type = 'qual'
        if self.learnership_assessment_type:
            self.assessment_type = 'learner'
        if self.skill_assessment_type:
            self.assessment_type = 'skill'
        if self.unit_assessment_type:
            self.assessment_type = 'unit'

    @api.onchange('employer_sdl')
    def onchange_employer_sdl(self):
        if self.employer_sdl:
            employer = self.env['inseta.organisation'].search([('sdl_no', '=', self.employer_sdl)], limit=1)
            if employer:
                self.organisation_id = employer.id
            else:
                self.employer_sdl = False
                return {
                        'warning': {
                            'title': "Validation Error!",
                            'message':"Employer with the SDL / N Number does not exist in the system"
                        }
                    }

    def get_organisation_default_user(self):
        user = self.env.user.id
        organisation = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return organisation.id 

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id 
    # --------------------------------------------
    # DOMAIN Methods
    # --------------------------------------------
    def domain_evaluating_committee_user_groups(self):
        etqa_eval_committee, etqa_admin, etqa_manager, etqa_verfier = self._get_group_users()
        return [('id','in', [res.id for res in etqa_eval_committee])]

    def domain_evaluating_verifier_users(self):
        etqa_eval_committee, etqa_admin, etqa_manager, etqa_verfier = self._get_group_users()
        return [('id','in', [res.id for res in etqa_verfier])]

    # --------------------------------------------
    # ORM Methods override
    # --------------------------------------------
    @api.model
    def default_get(self, fields_list):
        res = super(InsetaAssessment, self).default_get(fields_list)
        etqa_eval_committee, etqa_admin, etqa_manager, etqa_verfier = self._get_group_users()
        res.update({
            'etqa_admin_ids': etqa_admin,
            'etqa_manager_ids': etqa_manager,
        })
        return res

    def check_document(self):
        for rec in self.learner_assessment_document_ids:
            if not rec.data_file:
                raise ValidationError(f"Please ensure you add {rec.name}")

    @api.constrains('qualification_assessment_type', 'learnership_assessment_type',
    'skill_assessment_type', 'candidacy_assessment_type', 'wiltvet_assessment_type',
    'bursary_assessment_type', 'internship_assessment_type', 'unit_assessment_type',
    'learner_assessment_document_ids')
    def validate_assessment_type(self):
        if self.qualification_assessment_type or self.learnership_assessment_type or self.skill_assessment_type \
         or self.candidacy_assessment_type or self.wiltvet_assessment_type or self.bursary_assessment_type or self.internship_assessment_type \
         or self.unit_assessment_type:
            pass 
        else:
            raise ValidationError('Please select Programme assessment type')
        self.check_document()

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.assessment')
        vals['name'] = sequence or '/'
        return super(InsetaAssessment, self).create(vals)

    # --------------------------------------------
    # Business Logic
    # --------------------------------------------

    def action_set_to_draft(self):
        self.state = 'draft' 

    # def action_reject_assesment_submit(self):
    #     emails = []
        
    #     if not self.refusal_comment:
    #         raise ValidationError("Please provide a reason in the refusal comment section")

    #     if self.state == "pending_allocation":
    #         self.state = "draft"

    #     elif self.state == "pending_verification":
    #         if not self.env.user.has_group('inseta_etqa.group_etqa_verifiers'):
    #             raise ValidationError("You are not allowed to reject this record... Only users with Verification access can do that!!!")
    #         emails = [mail.login for mail in self.etqa_admin_ids]
    #         self.state = "pending_allocation"

    #     elif self.state == "manager_verify":
    #         emails = [mail.login for mail in self.etqa_verifier_ids]
    #         self.state = "pending_verification"

    #     elif self.state == "manager":
    #         self.state = "verified"

    #     emails.append(self.provider_id.email)
    #     self.action_send_mail('reject_assessment_mail_template', emails, None)

    def action_reject_assesment_submit(self):
        emails = []
        if not self.refusal_comment:
            raise ValidationError("Please provide a reason in the refusal comment section")
        if self.state == "pending_allocation":
            self.state = "draft"

        elif self.state in ["pending_allocation", "pending_verification"]:
            self.state = "draft"

        elif self.state == "manager_verify":
            self.state = "pending_verification"

        elif self.state == "verified":
            raise ValidationError("You cannot reject this application at this stage.")
        
        elif self.state == "manager":
            self.state = "verified"

        else:
            self.state = "draft"
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager] + ['verifications@inseta.org.za']
        recipients = etqa_manager_admin_login
        recipients.append(self.provider_id.email)
        self.env['inseta.assessment'].action_send_mail('reject_assessment_mail_template', recipients, None)

    def check_updated_learners(self):
        for rec in self:
            # if not rec.learner_assessment_details:
            # 	raise ValidationError("Learner's must be captured before submitting")
            if not rec.learner_assessment_document_ids:
                raise ValidationError("Please upload compulsory documents!!!")

    def action_submit(self):
        self.check_updated_learners()
        recipients = [mail.login for mail in self.etqa_admin_ids] + ['verifications@inseta.org.za']
        self.action_send_mail('submission_assessment_mail_template', recipients, None) 
        self.write({'state': 'pending_allocation'})

    def action_allocation_verifier(self):
        """ETQA Admin allocate Verifiers 
        """     
        if not self.etqa_verifier_ids:
            raise ValidationError('Please ensure to select at least one Reviewer / verifier!!!')
        if not self.learner_assessment_document_ids:
            raise ValidationError('Please ensure all documents are provider!!!')
        verifier_mails = [mail.login for mail in self.etqa_verifier_ids] + ['verifications@inseta.org.za']
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

        recipients = [mail.login for mail in self.etqa_manager_ids] + ['verifications@inseta.org.za']
        self.action_send_mail('verification_assessment_mail_template', recipients, None) 
        self.write({'state': 'manager_verify'})
    
    def action_manager_approve_verification(self):
        """ETQA Manager Approves learners Verification
        """ 
        recipients = [mail.login for mail in self.etqa_verifier_ids] + ['verifications@inseta.org.za']
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
        recipients = verifiers_login + etqa_manager_admin_login + ['verifications@inseta.org.za']
        self.action_send_mail('send_to_manager_assessment_mail_template', recipients, None) 
        self.write({'state': 'manager', 'assessment_date':fields.Date.today(), 'endorsed': True})

    def action_done(self):
        for rec in self.learner_assessment_details:
            achieved_status = self.env.ref('inseta_etqa.id_programme_status_02')
            incompleted_status = self.env.ref('inseta_etqa.id_programme_status_03')
            if rec.total_credits >= rec.programme_total_credits:
                rec.compute_result(achieved_status.id)
            else:
                rec.compute_result(incompleted_status.id)

        verifiers_login = [mail.login for mail in self.etqa_verifier_ids]
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = verifiers_login + etqa_manager_admin_login 

        provider_email = [self.provider_id.email]
        self.action_send_mail('endorse_notification_to_provider_assessment_mail_template', provider_email, None) 
        self.action_send_mail('endorse_signoff_assessment_mail_template', recipients, None) 
        self.write({'state': 'done', 'assessment_date':fields.Date.today(), 'endorsed': True})

    def action_done_old(self):
        if not self.learner_assessment_details:
            raise ValidationError('Please ensure that learner(s) are added on the assessment line tab')
            
        for details in self.learner_assessment_details:
            learnerObj = details.learner
            if details.qualification_programmes_line_ids:
                for line in details.qualification_programmes_line_ids:
                    line.action_validate_result(learnerObj, False)

            if details.learner_programmes_line_ids:
                for line in details.learner_programmes_line_ids:
                    line.action_validate_result(learnerObj)

            if details.skill_programmes_line_ids:
                for line in details.skill_programmes_line_ids:
                    line.action_validate_result(learnerObj)

            if details.bursary_programmes_line_ids:
                for line in details.bursary_programmes_line_ids:
                    line.action_validate_result(learnerObj)

            if details.internship_programmes_line_ids:
                for line in details.internship_programmes_line_ids:
                    line.action_validate_result(learnerObj, True)

            if details.candidacy_programmes_line_ids:
                for line in details.candidacy_programmes_line_ids:
                    line.action_validate_result(learnerObj, True)

            if details.wiltvet_programmes_line_ids:
                for line in details.wiltvet_programmes_line_ids:
                    line.action_validate_result(learnerObj, True)

        verifiers_login = [mail.login for mail in self.etqa_verifier_ids]
        committee, etqa_admin, manager, verifier = self._get_group_users()
        etqa_manager_admin_login = [mail.login for mail in etqa_admin] + [mail.login for mail in manager]
        recipients = verifiers_login + etqa_manager_admin_login

        provider_email = [self.provider_id.email]
        self.action_send_mail('endorse_notification_to_provider_assessment_mail_template', provider_email, None) 
        self.action_send_mail('endorse_signoff_assessment_mail_template', recipients, None)
        self.sudo().write({'state': 'done', 'assessment_date':fields.Date.today(), 'endorsed': True})
        for rec in self.learner_assessment_details:
            rec.sudo().write({'state': 'done'})

    def action_print_all_certficate(self):
        if self.qualification_assessment_type or self.learnership_assessment_type: 
            # if self.programme_total_credits > self.total_credits:
            #     raise ValidationError('You can only print certificates when total achieved credits are greater than the total minimum credits...')
            for rec in self.learner_assessment_details:
                if rec.programme_total_credits < rec.total_credits:
                    rec.sudo().write({'certificate_created_date': fields.Date.today()})  
            return self.env.ref('inseta_etqa.assessment_certificate_report').sudo().report_action(self)
        else:
            raise ValidationError('Sorry !!! You can only print certificate for qualification / learnership programmes')

    
    def action_print_result_statement(self):# TODO
        return self.env.ref('inseta_etqa.assessment_result_statement_report').sudo().report_action(self)

    def action_print_appointment_letter(self):
        return self.env.ref('inseta_etqa.learner_appointment_letter_report').report_action(self)

    def action_print_reject_letter(self):
        return self.env.ref('inseta_etqa.learner_rejection_letter_report').report_action(self)

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
            etqa_committee_users = etqa_committee.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        if etqa_admin:
            etqa_admin_users = etqa_admin.mapped('users')[0:5] # for performance issue, we set the list to 4 users

        if etqa_admin:
            etqa_manager_users = etqa_manager.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        if etqa_verifier:
            etqa_verifier_user = etqa_verifier.mapped('users')[0:5] # for performance issue, we set the list to 4 users
        return etqa_committee_users, etqa_admin_users, etqa_manager_users, etqa_verifier_user

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

    def action_open_assessements(self): 
        form_view_ref = self.env.ref('inseta_etqa.view_inseta_learner_assessment_detail_form', False)
        tree_view_ref = self.env.ref('inseta_etqa.view_inseta_learner_assessment_detail_tree', False) 
        if self.learner_assessment_details:
            return {
                'domain': [('id', 'in', [detail.id for detail in self.learner_assessment_details])],
                'name': 'Learner Assessment Details',
                'res_model': 'inseta.learner.assessment.detail',
                'type': 'ir.actions.act_window',
                'views': [(tree_view_ref.id, 'tree'),(form_view_ref.id, 'form')], 
            }
        else:
            raise ValidationError('No asessment found for this record!') 

    def unlink(self):
        for delete in self.filtered(lambda delete: delete.state not in ['draft','reject', 'rework']):
            raise ValidationError(_('You cannot delete an assessent which is in %s state.') % (delete.state,))
        return super(InsetaLearnerAssessmentDetails, self).unlink()

     