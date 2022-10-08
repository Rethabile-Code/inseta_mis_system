from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Insetasponsorship(models.Model):
	_name = 'inseta.res.sponsorship'
	_description = "Inseta sponsorship Id"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')


class InsetaLearnerLearnership(models.Model):
    _name = "inseta.learner.learnership"
    _description = "learner.learnership"
    _rec_name = "learner_programme_id"
    _order = "id desc"

    def action_print_all_certficate(self):
        achieved_programme_status = [
            self.env.ref('inseta_etqa.id_programme_status_16').id,
            self.env.ref('inseta_etqa.id_programme_status_13').id,
            self.env.ref('inseta_etqa.id_programme_status_07').id,
            self.env.ref('inseta_etqa.id_programme_status_02').id,
        ]
        if self.programme_status_id.id not in achieved_programme_status:
            raise ValidationError('You can only print certificates tht is not achieved!!!')
        self.write({'certificate_created_date': fields.Date.today()})
        return self.env.ref('inseta_etqa.programmes_learner_learnership_certificate_report').report_action(self)

    def action_print_result_statement(self):
        return self.env.ref('inseta_etqa.programmes_learnership_statement_result_report').report_action(self) 

    # def action_print_certficate(self): # TODO
    #     return self.env.ref('inseta_etqa.learner_appointment_letter_report').report_action(self)

    # def action_print_result_statement(self):# TODO
    #     return self.env.ref('inseta_etqa.assessment_result_statement_report').report_action(self)

    def _get_compulsory_document(self):
        self.document_ids = False 
        learnership_docs = ['Learnership Agreement', 'Certified ID copy', 'POPI act consent', 'Certified copy of matric/ Qualification']
        if self.dgtype_code in ['Learnership-Worker']:
            learnership_docs.append('Confirmation of Employment')
        else: 
            learnership_docs.append('Fixed term contract of employment')
        for rec in learnership_docs:
            vals = {
                'name': rec,
                'learner_learnship_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]
    
    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id 

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    learner_learnership_partial_assessment_ids = fields.One2many('learner.learnership.partial_assessment', 'learner_learnership_id', string='Learner Assessment Line')	
    edit_mode = fields.Boolean(default=True)
    lpro_id = fields.Integer()
    site_no = fields.Char(string='Site No', help="Required for setmis")
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_learnship_document_id", string="Documents")
    dgtype_code = fields.Char('DG Type Code')
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    learner_id = fields.Many2one('inseta.learner', string='Learner', store=True, required=False)
    provider_id = fields.Many2one('inseta.provider', string='Provider',default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])
    # , default = lambda self: self.get_provider_default_user())								
    # learning_programming_id = fields.Many2one('inseta.learner.programme', string='Learnership Programme', required=False)	
    learner_programme_id = fields.Many2one("inseta.learner.programme", string='Learnership Programme')
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    highest_edu_desc = fields.Text('Highest Education Description')
    document = fields.Binary(string="Document")
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
    
    # discard
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification', readonly=False, domain=lambda act: [('active', '=', True)])
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer', default=lambda s: s.get_employer_default_user())
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
    financial_year_id = fields.Many2one('res.financial.year', required=False)
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_learner_learnership_rel', 'ir_attachment_learner_learnership_id', 'ir_attachment_len_learnership_rel_id', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    achievement_date = fields.Date('Achievement Date')
    certificate_number = fields.Char('Certificate Number')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True)
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=True) 
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', compute="compute_socio_economic_status", store=True)
    student_number = fields.Char('Student Number')
    lga_number = fields.Char('LGA Number')
    effective_date = fields.Date('Status Effective Date')
    cummulative_spend = fields.Char('Cummulative spend')
    institution_name = fields.Char(string="Institution name")
    amount_due_institution = fields.Float(string="Amount due to institution")
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user())
    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('Programme code') # , related="learner_programme_id.programme_code")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )
    programme_status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','Achieved'),
            ('dropped','Dropped'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
        ],
        default="enrolled", string=""
    )
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'learnership_unit_standard_rel', 'column1', string="Learnership Unit Standard")
    learnership_unit_standard_ids = fields.One2many("inseta.learnership.unitstandard", 'learnership_id', string="Learnership Unit Standard")
    elective_learnership_unit_standard_line_ids = fields.Many2many(
        "inseta.learnership.unit.standard", 
        'elective_learnership_unit_standard_rel1', 
        'elective_learnership_unit_standard_id1', 
        string="Elective Learnership Unit Standard")
    state = fields.Char(string='State')
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")

    learnership_assessment_ids = fields.One2many("inseta.learner_learnership.assessment", 'learner_learnership_id', string="Learnership Assessment")
    
    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else: 
            self.is_employed = False 

    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    @api.constrains('learnership_unit_standard_ids','document_ids')
    def check_required_fields(self):
        if self.learner_programme_id.learnership_unit_standard_ids:
            if self.learner_programme_id.learnership_unit_standard_ids and not self.learnership_unit_standard_ids:
                raise ValidationError('learnership Unit standard ids must be filled')
            # if sum([rec.unit_standard_id.credits for rec in self.learnership_unit_standard_ids]) < self.learner_programme_id.minimum_credits:
            # 	raise ValidationError('Total unit standard credits must be greater than programme minimum credit(s)')

        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    @api.depends('dgtype_code')
    def compute_socio_economic_status(self):
        if self.dgtype_code in ['LRN-W','Learnership-Worker', 'Skill-W','SP', 'BUR']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                } 

    # @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

    # @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no


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

    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id
        learner_status = self.learner_id.mapped('learner_learnership_line').\
        filtered(lambda val: val.learner_programme_id.id == self.learner_programme_id.id and val.financial_year_id.id == self.financial_year_id.id)
        #  or \
        # self.env['inseta.learner.learnership'].search([('learner_id', '=',self.learner_id.id),('learner_programme_id', '=',self.learner_programme_id.id), 
        # ('financial_year_id', '=',self.financial_year_id.id)], limit=1)
        if learner_status:
            self.learner_programme_id = False
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme')
 
    def get_compulsory_unit_standard(self):
        self.learnership_unit_standard_ids = False
        programme_learnership_unit_standards = self.learner_programme_id.mapped('learnership_unit_standard_ids').\
        filtered(lambda se: se.unit_standard_type_id.name in ['Core', 'core', 'Fundamental', 'fundamental'])
        for rex in programme_learnership_unit_standards:
            self.learnership_unit_standard_ids = [(0, 0, {
                'learnership_id': self.id,
                'unit_standard_id': rex.unit_standard_id.id,
                'unit_standard_type': rex.unit_standard_type_id.id,
                }
            )]

    @api.onchange('elective_learnership_unit_standard_line_ids')
    def _onchange_elective_learnership_unit_standard_line_ids(self):
        existing_unit_ids = self.mapped('learnership_unit_standard_ids').filtered(lambda s: s.unit_standard_type.name in ['Elective', 'elective'])
        if self.elective_learnership_unit_standard_line_ids:
            if existing_unit_ids:
                self.learnership_unit_standard_ids = [(3, rex.id) for rex in existing_unit_ids]
            for elect in self.elective_learnership_unit_standard_line_ids:
                # existing_unit_ids = self.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_id.id == elect.unit_standard_id.id and s.unit_standard_type.id == elect.unit_standard_type_id.id)
                self.learnership_unit_standard_ids = [(0, 0, {
                    'learnership_id': self.id,
                    'unit_standard_id': elect.unit_standard_id.id,
                    'unit_standard_type': elect.unit_standard_type_id.id,
                    }
                )]
        else:
            if existing_unit_ids:
                self.learnership_unit_standard_ids = [(3, rex.id) for rex in existing_unit_ids]

    @api.onchange('learner_programme_id')
    def _onchange_programme_id(self):
        domain = {
            'elective_learnership_unit_standard_line_ids': [('id', '=', None)]
        }
        if self.learner_programme_id:
            self.check_learner_status()
            self._get_compulsory_document()
            self.get_compulsory_unit_standard()
            self.qualification_code = self.learner_programme_id.programme_code
            elective_unit_standards = self.learner_programme_id.mapped('learnership_unit_standard_ids').filtered(lambda x: x.unit_standard_type_id.name in ['Elective', 'elective'])
            domain_tuple = [('id', 'in', [r.id for r in elective_unit_standards])] if elective_unit_standards else [('id', '=', None)]
            domain = {
            'elective_learnership_unit_standard_line_ids': domain_tuple,
            }
        return {'domain': domain}

    @api.onchange('provider_id', 'provider_sdl')
    def _onchange_provider_id(self):
        if self.provider_sdl:
            self.onchange_provider_sdl()
        if self.provider_id:
            self.onchange_provider_id()
        provider_id = self.env['inseta.provider'].search(['|',('id', '=', self.provider_id.id),('employer_sdl_no', '=', self.provider_sdl)], limit=1)
        if provider_id:
            domain_val = None
            provider_prog = provider_id.mapped('learner_programmes_ids')
            programme_ids = [record.learner_programme_id.id for record in provider_prog]
            domain_val = [('id', '=', programme_ids)]
            # if not self.lpro_id:
            #     provider_prog = provider_id.mapped('learner_programmes_ids')
            #     programme_ids = [record.learner_programme_id.id for record in provider_prog]
            #     domain_val = [('id', '=', programme_ids)]
            # else:
            #     learnership_id = self.env['inseta.lpro'].browse([self.lpro_id]).dg_evaluation_id.learnership_id.id
            #     domain_val = [('id', 'in', [learnership_id])]
            domain = {'learner_programme_id': domain_val}
            return {'domain': domain}
        # else:
        # 	raise ValidationError('Provider does not have learnership linked')
 

class InsetaSkillLearnership(models.Model):
    _name = "inseta.skill.learnership"
    _description = "skill.learnership"
    _rec_name = "skill_programme_id"
    _order = "id desc"

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    learner_skill_partial_assessment_ids = fields.One2many('learner.skill.partial_assessment', 'learner_skill_learnership_id', string='Learner Skill Partial Assessment Line')	
    edit_mode = fields.Boolean(default=True)
    
    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    lpro_id = fields.Integer()
    state = fields.Char(string='State')
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_skill_document_id", string="Documents")
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])								
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user())
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer',)
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
 
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification',readonly=False, domain=lambda act: [('active', '=', True)])#  compute="_compute_skills_programming_id")
    skill_programme_id = fields.Many2one("inseta.skill.programme", string='Skill Programme', domain=lambda act: [('active', '=', True)])
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'OFO occupation')
    
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False, default= lambda s: s.env.ref('inseta_base.data_fundingtype1').id)

    financial_year_id = fields.Many2one('res.financial.year', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    achievement_date = fields.Date('Achievement Date')
    certificate_number = fields.Char('Certificate Number')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    lga_number = fields.Char('LGA Number')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_skill_learnership_rel', 'ir_attachment_skill_learnership_id', 'ir_attachment_ski_learnership_rel_id', required=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True)
    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    student_number = fields.Char('Student Number')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', compute="compute_dgtype_code", store=True)
    effective_date = fields.Date('Status Effective Date')

    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('Programme code') # , related="qualification_id.saqa_id")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=True)
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'skill_unit_standard_rel', 'column1', string="Skill Unit Standards")
    skills_unit_standard_ids = fields.One2many("inseta.skill.unitstandard", 'skill_learnership_id', string="Skills Unit Standard")
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    elective_skills_unit_standard_ids = fields.Many2many(
        "inseta.skill.unitstandard", 
        'elective_skills_unit_standard_rel', 
        'elective_skills_unit_standard_id', 
        string="Elective skills Unit Standard",)
    elective_skills_unit_standard_ids = fields.Many2many(
        "inseta.skill.unit.standard", 
        'elective_skills_unit_standard_rel1', 
        'elective_skills_unit_standard_id1', 
        string="Elective skills Unit Standard",)
    skills_assessment_ids = fields.One2many("inseta.skill_learnership.assessment", 'learner_skill_learnership_id', string="Skills Programme Assessment")

    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 

    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    @api.constrains('skills_unit_standard_ids','document_ids')
    def check_required_fields(self):
        if self.skill_programme_id.skill_unit_standard_ids:
            if self.skill_programme_id.skill_unit_standard_ids and not self.skills_unit_standard_ids:
                raise ValidationError('Skill Unit standard ids must be filled')
            # if sum([rec.unit_standard_id.credits for rec in self.skills_unit_standard_ids]) < self.skill_programme_id.credits:
            # 	raise ValidationError('Total unit standard credits must be greater than programme minimum credit(s)')
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')
     
    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    # skills 
    @api.depends('dgtype_code')
    def compute_dgtype_code(self):
        # if self.lpro_id:
        #     self.funding_type = self.env.ref('inseta_base.data_fundingtype1').id
        # else:
        #     self.funding_type = False 
        #     lpro = self.env['inseta.lpro'].browse([self.lpro_id])
        #     # if self.lpro_id and lpro.dgtype_id.name.startswith('Skills Programmes for Workers') or lpro.dgtype_code in ['SPW', 'Skill-W']:
        #     if self.dgtype_code in ['SPW', 'Skill-W']:
        #         self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        #         self.funding_type = self.env.ref('inseta_base.data_fundingtype1').id
        #     else:
        #         self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id
        #         self.funding_type = self.env.ref('inseta_base.data_fundingtype2').id
        if self.dgtype_code in ['SPW', 'Skill-W']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id

        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

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

    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
             
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }

    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    @api.onchange('provider_id', 'provider_sdl')
    def _onchange_provider_id(self):
        if self.provider_sdl or self.provider_id:
            provider_id = self.env['inseta.provider'].search(['|',('id', '=', self.provider_id.id),('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider_id:
                provider_prog = provider_id.mapped('skill_programmes_ids')
                programme_ids = [record.skill_programme_id.id for record in provider_prog]
                domain = {'skill_programme_id': [('id', '=', programme_ids)]}
                return {'domain': domain}

    # skills
    def _get_compulsory_document(self):
        self.document_ids = False 
        # docs = ['Proof of Registration', 'Proof of Employment', 'Certified ID copy', 'Worker Programme Agreement', 'Quotation']
        docs = ['Proof of Registration', 'Worker Programme Agreement', 'Certified ID copy', 'Quotation']
        lpro = self.env['inseta.lpro'].browse([self.lpro_id])
        # if self.lpro_id and lpro.dg_evaluation_id.name.startswith('SPW') or lpro.dgtype_code.startswith('SPW'):
        if self.dgtype_code in ['SPW', 'Skill-W']:
            docs += ['contract of employment']
        for rec in docs:
            vals = {
                'name': rec,
                'lpro_id': self.lpro_id,
                'learner_skill_document_id': self.id,
                'learner_document2_id': self.learner_id.id,

            }
            self.document_ids = [(0, 0, vals)]

    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id

        learner_status = self.learner_id.mapped('skill_learnership_line').\
        filtered(lambda val: val.skill_programme_id.id == self.skill_programme_id.id \
        and val.financial_year_id.id == self.financial_year_id.id) 
        # or self.env['inseta.skill.learnership'].search([('learner_id', '=',self.learner_id.id),('skill_programme_id', '=',self.skill_programme_id.id), 
        # ('financial_year_id', '=',self.financial_year_id.id)],limit=1)
        if learner_status:
            self.skill_programme_id = False 
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme')
 
    def get_compulsory_unit_standard(self):
        self.skills_unit_standard_ids = False
        programme_learnership_unit_standards = self.skill_programme_id.mapped('skill_unit_standard_ids').\
        filtered(lambda se: se.unit_standard_type_id.name in ['Core', 'core', 'Fundamental', 'fundamental'])
        for rex in programme_learnership_unit_standards:
            self.skills_unit_standard_ids = [(0, 0, {
                'skill_learnership_id': self.id,
                'unit_standard_id': rex.unit_standard_id.id,
                'unit_standard_type': rex.unit_standard_type_id.id,
                }
            )]

    @api.onchange('skill_programme_id')
    def _onchange_programme_id(self):
        domain = {
            'elective_learnership_unit_standard_line_ids': [('id', '=', None)]
        }
        if self.skill_programme_id:
            self.check_learner_status()
            self._get_compulsory_document()
            self.get_compulsory_unit_standard()
            self.qualification_code = self.skill_programme_id.programme_code
            unit_standards = [record.unit_standard_id.id for record in self.skill_programme_id.mapped('skill_unit_standard_ids')]
            if not unit_standards:
                self.is_unit_standard == False
            # domain = {'unit_standard_ids': [('id', '=', unit_standards)]}
            elective_unit_standards = self.skill_programme_id.mapped('skill_unit_standard_ids').filtered(lambda x: x.unit_standard_type_id.name in ['Elective', 'elective'])
            domain_tuple = [('id', 'in', [r.id for r in elective_unit_standards])] if elective_unit_standards else [('id', '=', None)]
            domain = {
            'elective_skills_unit_standard_ids': domain_tuple
            }
        return {'domain': domain}

    @api.onchange('elective_skills_unit_standard_ids')
    def _onchange_elective_skills_unit_standard_line(self):
        existing_unit_ids = self.mapped('skills_unit_standard_ids').filtered(lambda s: s.unit_standard_type.name in ['Elective', 'elective'])
        if self.elective_skills_unit_standard_ids:
            if existing_unit_ids:
                self.skills_unit_standard_ids = [(3, rex.id) for rex in existing_unit_ids]
            for elect in self.elective_skills_unit_standard_ids:
                # existing_unit_ids = self.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_id.id == elect.unit_standard_id.id and s.unit_standard_type.id == elect.unit_standard_type_id.id)
                self.skills_unit_standard_ids = [(0, 0, {
                    'skill_learnership_id': self.id,
                    'unit_standard_id': elect.unit_standard_id.id,
                    'unit_standard_type': elect.unit_standard_type_id.id,
                    }
                )]
        else:
            if existing_unit_ids:
                self.skills_unit_standard_ids = [(3, rex.id) for rex in existing_unit_ids]

    def action_print_all_certficate(self):
        achieved_programme_status = [
            self.env.ref('inseta_etqa.id_programme_status_16').id,
            self.env.ref('inseta_etqa.id_programme_status_13').id,
            self.env.ref('inseta_etqa.id_programme_status_07').id,
            self.env.ref('inseta_etqa.id_programme_status_02').id,
        ]
        if self.programme_status_id.id not in achieved_programme_status:
            raise ValidationError('You can only print certificates tht is not achieved!!!')
        self.write({'certificate_created_date': fields.Date.today()})
        return self.env.ref('inseta_etqa.programmes_skill_learnership_certificate_report').report_action(self)

    def action_print_result_statement(self): 
        return self.env.ref('inseta_etqa.programmes_skill_learnership_statement_result_report').report_action(self) 


    # def action_print_certficate(self): # TODO
    #     return self.env.ref('inseta_etqa.learner_appointment_letter_report').report_action(self)

    # def action_print_result_statement(self):# TODO
    #     return self.env.ref('inseta_etqa.learner_rejection_letter_report').report_action(self)

    
class InsetaqualificationLearnership(models.Model):
    _name = "inseta.qualification.learnership"
    _description = "qualification learnership"
    _rec_name = "qualification_id"
    _order = "id desc"

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 
        
    learner_qualification_partial_assessment_ids = fields.One2many('learner.qualification.partial_assessment', 'learner_qualification_id', string='Learner qualification Partial Assessment Line')	
    edit_mode = fields.Boolean(default=True)
    
    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    lpro_id = fields.Integer()
    site_no = fields.Char(string='Site No', help="Required for setmis")
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', string='Ofo occupation', help="Required for setmis")

    state = fields.Char(string='State')
    cummulative_spend = fields.Char('Cummulative spend')
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_qualification_document_id", string="Documents")
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    learner_id = fields.Many2one('inseta.learner', string='Learner', store=True, required=False)
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])								
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user())
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification', readonly=False, domain=lambda act: [('active', '=', True)])#
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer')
    effective_date = fields.Date('Status Effective Date')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', compute="compute_dgtype_code", store=True)
    qualification_programming_id = fields.Many2one('inseta.qualification.programme', string='Qualification', required=False)	 
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
    financial_year_id = fields.Many2one('res.financial.year', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    achievement_date = fields.Date('Achievement Date')
    certificate_number = fields.Char('Certificate Number')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    lga_number = fields.Char('LGA Number')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_qualification_learnership_rel', 'ir_attachment_qualification_learnership_id', 'ir_attachment_qual_learnership_rel_id', required=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True) 
    student_number = fields.Char('Student Number')
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('Qualification code') # , related="qualification_id.saqa_id")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','Achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )
    
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'qualification_unit_standard_rel', 'column1', string="Unit Standards")
    qualification_unit_standard_ids = fields.One2many("inseta.qualification.unitstandard", 'qualification_learnership_id', string="Qualification Unit Standard")
    # elective_qualification_unit_standard_line_ids = fields.Many2many("inseta.qualification.unit.standard", 'elective_qualification_unit_standard_rel', 'elective_qualification_unit_standard_id', string="Elective Qualification Unit Standard",
    # domain = lambda self: self._get_related_elective_unitstandards())

    elective_qualification_unit_standard_line_ids = fields.Many2many(
        "inseta.qualification.unit.standard", 
        'elective_qualification_unit_standard_rel1', 
        'elective_qualification_unit_standard_id1', 
        string="Elective Qualification Unit Standard",)
        # domain = lambda self: self._get_related_elective_unitstandards())
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=True)
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    qualification_assessment_ids = fields.One2many("inseta.learner_qualification.assessment", 'learner_qualification_id', string="Qualification Programme Assessment")

    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 

    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    @api.constrains('qualification_unit_standard_ids','document_ids')
    def check_required_fields(self):
        if self.qualification_id.qualification_unit_standard_ids:
            if self.qualification_id.qualification_unit_standard_ids and not self.qualification_unit_standard_ids:
                pass # raise ValidationError('Qualification Unit standard ids must be filled')
                 
            qualification_unit_standard_credits = sum([rec.unit_standard_id.credits for rec in self.qualification_unit_standard_ids])
            if self.qualification_id.minimum_credits > qualification_unit_standard_credits:
                raise ValidationError(f'Qualification minimum credit is {self.qualification_id.minimum_credits} - while the total captured unit standard is {qualification_unit_standard_credits}. \n \
                Qualification unit standards credits must be greater than the qualification minimum credits:')# ('Total unit standard credits must be greater than programme minimum credit(s)')
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id
    
    @api.depends('dgtype_code')
    def compute_socio_economic_status(self):
        if self.dgtype_code in ['LRN-W']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }
            
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

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    def _get_compulsory_document(self):
        self.document_ids = False 
        # docs = ['Learnership Agreement', 'Certified ID copy', 'Confirmation of Employment', 'POPI act consent']
        docs = ['Proof of Registration', 'POPI act consent']
        for rec in docs:
            vals = {
                'name': rec,
                'learner_qualification_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]

    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id
        # and val.status in ['enrolled','competent']) or \

        learner_status = self.learner_id.mapped('qualification_learnership_line').\
        filtered(lambda val: val.qualification_id.id == self.qualification_id.id and val.financial_year_id.id == self.financial_year_id.id)
        #  or \
        # self.env['inseta.qualification.learnership'].search([('learner_id', '=',self.learner_id.id),('qualification_id', '=',self.qualification_id.id), 
        # ('financial_year_id', '=',self.financial_year_id.id)], limit=1)
        if learner_status:
            self.qualification_id = False 
            # return {
            # 			'warning': {
            # 				'title': 'Validation',
            # 				'message': f'{self.learner_id.name} is already enrolled or has completed this programme')
            # 			}
            # 		}
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme for the selected financial year {self.financial_year_id.name}')

    def get_compulsory_unit_standard(self):
        self.qualification_unit_standard_ids = False
        programme_learnership_unit_standards = self.qualification_id.mapped('qualification_unit_standard_ids').\
        filtered(lambda se: se.unit_standard_type_id.name in ['Core', 'core', 'Fundamental', 'fundamental'])
        for rex in programme_learnership_unit_standards:
            self.qualification_unit_standard_ids = [(0, 0, {
                'qualification_learnership_id': self.id,
                'unit_standard_id': rex.unit_standard_id.id,
                'unit_standard_type': rex.unit_standard_type_id.id,
                }
            )]

    @api.onchange('qualification_id')
    def _onchange_programme_id(self):
        domain = {
            'elective_qualification_unit_standard_line_ids': [('id', '=', None)]
        }
        if self.qualification_id:
            self.check_learner_status()
            self._get_compulsory_document()
            self.get_compulsory_unit_standard()
            self.qualification_code = str(self.qualification_id.saqa_id)
            unit_standards = [record.unit_standard_id.id for record in self.qualification_id.mapped('qualification_unit_standard_ids')]
            if not unit_standards:
                self.is_unit_standard == False
            elective_unit_standards = self.qualification_id.mapped('qualification_unit_standard_ids').filtered(lambda x: x.unit_standard_type_id.name in ['Elective', 'elective'])
            domain_tuple = [('id', 'in', [r.id for r in elective_unit_standards])]
            domain = {
            # 'unit_standard_ids': [('id', '=', unit_standards)],
            'elective_qualification_unit_standard_line_ids': domain_tuple
            }
        return {'domain': domain}

    @api.onchange('elective_qualification_unit_standard_line_ids')
    def _onchange_elective_qualification_unit_standard_line(self):
        existing_unit_ids = self.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_type.name in ['Elective', 'elective'])
        if self.elective_qualification_unit_standard_line_ids:
            if existing_unit_ids:
                self.qualification_unit_standard_ids = [(3, rex.id) for rex in existing_unit_ids]
            for elect in self.elective_qualification_unit_standard_line_ids:
                # existing_unit_ids = self.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_id.id == elect.unit_standard_id.id and s.unit_standard_type.id == elect.unit_standard_type_id.id)
                self.qualification_unit_standard_ids = [(0, 0, {
                    'qualification_learnership_id': self.id,
                    'unit_standard_id': elect.unit_standard_id.id,
                    'unit_standard_type': elect.unit_standard_type_id.id,
                    }
                )]
        else:
            if existing_unit_ids:
                self.qualification_unit_standard_ids = [(3, rex.id) for rex in existing_unit_ids]

    @api.onchange('provider_id', 'provider_sdl')
    def _onchange_provider_id(self):
        if self.provider_sdl or self.provider_id:
            provider_id = self.env['inseta.provider'].search(['|',('id', '=', self.provider_id.id),('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider_id:
                # provider_prog = provider_id.mapped('provider_qualification_ids')
                provider_prog = provider_id.mapped('qualification_ids')
                programme_ids = [record.qualification_id.id for record in provider_prog]
                domain = {'qualification_id': [('id', '=', programme_ids)]}
                return {'domain': domain}
            # else:
            # 	raise ValidationError('There is no programmes linked for the provider: Check assessor and moderator linking tab')
    
    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id 

    # def action_print_certficate(self): # TODO
    #     return self.env.ref('inseta_etqa.learner_appointment_letter_report').report_action(self)

    # def action_print_result_statement(self):# TODO
    #     return self.env.ref('inseta_etqa.learner_rejection_letter_report').report_action(self)

    def action_print_all_certficate(self):
        achieved_programme_status = [
            self.env.ref('inseta_etqa.id_programme_status_16').id,
            self.env.ref('inseta_etqa.id_programme_status_13').id,
            self.env.ref('inseta_etqa.id_programme_status_07').id,
            self.env.ref('inseta_etqa.id_programme_status_02').id,
        ]
        if self.programme_status_id.id not in achieved_programme_status:
            raise ValidationError('You can only print certificates tht is not achieved!!!')
        self.write({'certificate_created_date': fields.Date.today()})
        return self.env.ref('inseta_etqa.programmes_qualification_learnership_certificate_report').report_action(self)

    def action_print_result_statement(self): 
        return self.env.ref('inseta_etqa.programmes_qualification_learnership_statement_result_report').report_action(self)


class InsetaUnitStandardLearnership(models.Model):
    _name = "inseta.unit_standard.learnership"
    _description = "unit_standard.learnership"
    _rec_name = "unit_standard_id"
    _order = "id desc"
    _inherit = ["inseta.qualification.learnership"]
    
    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    edit_mode = fields.Boolean(default=True)
    learner_unit_standard_partial_assessment_ids = fields.One2many('learner.unit_standard.partial_assessment', 'unit_standard_learnership_id', string='Learner unitstandard Partial Assessment Line')	
    lpro_id = fields.Integer()
    elective_qualification_unit_standard_line_ids = fields.Many2many(
        "inseta.qualification.unit.standard", 
        'elective_qualification_unit_standard_rel', 
        'elective_qualification_unit_standard_id', 
        string="Elective Qualification Unit Standard",
    )
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_unit_standard_document_id", string="Documents")
    unit_standard_id = fields.Many2one('inseta.unit.standard', 'Unit standard', readonly=False)#
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_unit_standard_learnership_rel', 'ir_attachment_unit_standard_learnership_id', 'ir_attachment_qual_learnership_rel_id', required=False)
    programme_status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Programme Status"
    )
    dgtype_code = fields.Char('DG Type Code')
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_unit_standard_rel', 'column1', string="Qualification Unit Standard")
    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])								
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user())
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', compute="compute_socio_economic_status", store=True)
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    document = fields.Binary(string="Document")
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    
    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 
            
    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    @api.depends('dgtype_code')
    def compute_socio_economic_status(self):
        if self.dgtype_code in ['LRN-W']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

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

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }

    @api.onchange('provider_id', 'provider_sdl')
    def _onchange_provider_id(self):
        if self.provider_sdl or self.provider_id:
            provider_id = self.env['inseta.provider'].search(['|',('id', '=', self.provider_id.id),('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider_id:
                provider_prog = provider_id.mapped('unit_standard_ids')
                programme_ids = [record.unit_standard_id.id for record in provider_prog]
                domain = {'unit_standard_id': [('id', '=', programme_ids)]}
                return {'domain': domain}

    def _get_compulsory_document(self):
        self.document_ids = False 
        docs = ['Proof of Registration', 'POPI act consent']
        # docs = ['Learnership Agreement', 'Certified ID copy', 'Confirmation of Employment', 'POPI act consent']
        for rec in docs:
            vals = {
                'name': rec,
                'learner_unit_standard_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]

    @api.onchange('unit_standard_id')
    def _onchange_unit_standard_id(self):
        if self.unit_standard_id:
            learner_status = self.check_learner_unit_status()
            if learner_status:
                self.unit_standard_id = False 
                return {
                        'warning': {
                            'title': 'Validation',
                            'message': f'{self.learner_id.name} has completed this programme for the selected financial year {self.financial_year_id.name}'
                        }
                    }
            # raise ValidationError(f'{self.learner_id.name} has completed this programme for the selected financial year {self.financial_year_id.name}')
            self._get_compulsory_document()

    @api.constrains('unit_standard_ids','document_ids')
    def check_required_fields(self):
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')

    def check_learner_unit_status(self):
        learner_status = self.learner_id.mapped('unit_standard_learnership_line').\
        filtered(lambda val: val.unit_standard_id.id == self.unit_standard_id.id) or \
        self.env['inseta.unit_standard.learnership'].search([('learner_id', '=',self.learner_id.id),('unit_standard_id', '=',self.unit_standard_id.id), 
        ('financial_year_id', '=',self.financial_year_id.id)], limit=1)
        if learner_status:
            return True


class InsetaInternshipLearnership(models.Model):
    _name = "inseta.internship.learnership"
    _description = "internship.learnership"
    _rec_name = "programme_id"
    _order = "id desc"

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id

    edit_mode = fields.Boolean(default=True)
    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    lpro_id = fields.Integer()
    state = fields.Char(string='State')
    site_no = fields.Char(string='Site No', help="Required for setmis")
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_internship_document_id", string="Documents")
    programme_id = fields.Many2one('inseta.internship.programme', 'Internship Type', readonly=False)#
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    lwga_number = fields.Date('LWGA Number')
    year_of_study = fields.Char('Year of study')
    sic_code = fields.Many2one('res.sic.code', string='SIC CODE') 
    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    core_business_desc = fields.Text('Core business')
    fet = fields.Many2one('inseta.fet', 'FET')
    het = fields.Many2one('inseta.het', 'HET')
    qualification_achievement_date = fields.Date('Qualification')
    cummulative_spend = fields.Char('Cummulative spend')
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    internship_type_id = fields.Many2one('res.internship.type', 'Internship type')
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=False, help="Determines if this programme type will be computed based on unit standard credits")
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False,default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user(), domain=lambda act: [('active', '=', True)])
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer')
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification',readonly=False, domain=lambda act: [('active', '=', True)])#  compute="_compute_skills_programming_id")
    # discard
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False, default= lambda s: s.env.ref('inseta_base.data_fundingtype1').id)

    financial_year_id = fields.Many2one('res.financial.year', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    achievement_date = fields.Date('Achievement Date')
    certificate_number = fields.Char('Certificate Number')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True)

    student_number = fields.Char('Student Number')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', default=lambda self: self.env.ref('inseta_base.data_sec_2').id, store=True)
    lga_number = fields.Char('IWGA Number')
    effective_date = fields.Date('Status Effective Date')

    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('SAQA code', related="qualification_id.saqa_id")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )
    programme_status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Programme Status"
    )
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'internship_unit_standard_rel', 'column1', string="Internship Unit Standard")

    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
    placement_type_id = fields.Many2one('res.placementtype', string='Placement type')
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    
    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 
            
    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    # internship
    # @api.depends('dgtype_code')
    # def compute_socio_economic_status(self):
    #     if self.dgtype_code in ['LRN-W']:
    #         self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
    #     else:
    #         self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }

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

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }
    
    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    @api.constrains('document_ids')
    def check_required_fields(self):
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')

    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id

        learner_status = self.learner_id.mapped('internship_learnership_line').\
        filtered(lambda val: val.qualification_id.id == self.qualification_id.id \
        and val.financial_year_id.id == self.financial_year_id.id)
        #  or \
        # self.env['inseta.internship.learnership'].search([('learner_id', '=',self.learner_id.id),('qualification_id', '=',self.qualification_id.id), 
        # ('financial_year_id', '=',self.financial_year_id.id)], limit=1)
        if learner_status:
            self.qualification_id = False 
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme')

    def _get_compulsory_document(self):
        self.document_ids = False 
        docs = ['Internship Agreement', 'Certified ID copy', 'Fixed term contract of employment', 'POPI act consent', 'Certified Copy of Qualification']
        for rec in docs:
            vals = {
                'name': rec,
                'lpro_id': self.lpro_id,
                'learner_internship_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]

    @api.onchange('provider_id', 'provider_sdl')
    def _onchange_provider_id(self):
        if self.provider_sdl or self.provider_id:
            provider_id = self.env['inseta.provider'].search(['|',('id', '=', self.provider_id.id),('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider_id:
                # provider_prog = provider_id.mapped('provider_qualification_ids')
                provider_prog = provider_id.mapped('qualification_ids')
                programme_ids = [record.qualification_id.id for record in provider_prog]
                domain = {'qualification_id': [('id', '=', programme_ids)]}
                return {'domain': domain}
            # else:
            # 	raise ValidationError('There is no programmes linked for the provider: Check assessor and moderator linking tab')
    

    @api.onchange('qualification_id')
    def _onchange_programme_id(self):
        if self.qualification_id:
            self.check_learner_status()
            self._get_compulsory_document()
            self.qualification_code = str(self.qualification_id.saqa_id)
            self.nqflevel_id = self.qualification_id.nqflevel_id.id
            unit_standards = [record.unit_standard_id.id for record in self.qualification_id.mapped('qualification_unit_standard_ids')]
            domain = {'unit_standard_ids': [('id', '=', unit_standards)]}
            return {'domain': domain}


class InsetaBusaryLearnership(models.Model):
    _name = "inseta.bursary.learnership" 
    _description = "bursary.learnership"
    _rec_name = "programme_id"
    _order = "id desc"

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    edit_mode = fields.Boolean(default=True)
    lpro_id = fields.Integer()
    state = fields.Char(string='State')
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_bursary_document_id", string="Documents")
    programme_id = fields.Many2one('inseta.bursary.programme', 'Programme', readonly=False)#
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_bursary_learnership_rel', 'ir_attachment_bursary_learnership_id', 'ir_attachment_qual_learnership_rel_id', required=False)
    contract_number = fields.Char('Contract number')
    cummulative_spend = fields.Char('Cummulative spend')
    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    institution_name = fields.Char(string="Institution name")
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
    amount_due_institution = fields.Float(string="Amount due to institution")
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	

    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user())
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer')
    # discard
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification',readonly=False, domain=lambda act: [('active', '=', True)])#  compute="_compute_skills_programming_id")
    skill_programme_id = fields.Many2one("inseta.skill.programme", string='Skill Programme')
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
    bursary_type_id = fields.Many2one('res.bursary.type', 'Bursary type')
    agreement_number = fields.Char('Bursary Funding Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False, default= lambda s: s.env.ref('inseta_base.data_fundingtype1').id)
    financial_year_id = fields.Many2one('res.financial.year', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    certificate_number = fields.Char('Certificate Number')
    achievement_date = fields.Date('Achievement Date')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    lga_number = fields.Char('LGA Number')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True)
    student_number = fields.Char('Student Number')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', compute="compute_dgtype_code", store=True)
    effective_date = fields.Date('Status Effective Date')
    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('Programme code') # , related="qualification_id.saqa_id")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )
    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=False, help="Determines if this programme type will be computed based on unit standard credits")

    programme_status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Programme Status"
    )
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')

    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'bursary_unit_standard_rel', 'column1', string="Bursary Unit Standard")
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    
    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 
            
    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    @api.depends('dgtype_code')
    def compute_dgtype_code(self):
        # if self.lpro_id:
        #     lpro = self.env['inseta.lpro'].browse([self.lpro_id])
        #     if self.lpro_id and lpro.dgtype_id.name.startswith('Bursaries for Workers'):
        #         self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        #         self.funding_type = self.env.ref('inseta_base.data_fundingtype1').id
        #     else:
        #         self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id
        #         self.funding_type = self.env.ref('inseta_base.data_fundingtype2').id
        
        if self.dgtype_code == 'Bursary-W':
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
            self.funding_type = self.env.ref('inseta_base.data_fundingtype1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id
            self.funding_type = self.env.ref('inseta_base.data_fundingtype2').id

    # Bursary
    def _get_compulsory_document(self):
        self.document_ids = False 
        docs = ['Proof of Registration', 'Proof of Employment', 'Certified ID copy', 'Worker Programme Agreement', 'Quotation']
        lpro = self.env['inseta.lpro'].browse([self.lpro_id])
        # if self.lpro_id and lpro.dgtype_id.name.startswith('Bursaries for Workers'):
        if self.dgtype_code == 'Bursary-W':
            docs += ['contract of employment']
        for rec in docs:
            vals = {
                'name': rec,
                'lpro_id': self.lpro_id,
                'learner_bursary_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]

    @api.onchange('programme_id')
    def onchange_programme(self):
        if self.programme_id:
            self._get_compulsory_document()
            self.unit_standard_ids = [(6, 0, [rec.id for rec in self.programme_id.mapped('unit_standard_ids').filtered(lambda se: se.unit_standard_type.name in ['Core', 'core', 'Fundamental', 'fundamental'])])]
    
    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

    @api.onchange('employer_sdl')
    def onchange_employer_sdl(self):
        if self.employer_sdl:
            employer = self.env['inseta.organisation'].search([('sdl_no', '=', self.employer_sdl)], limit=1)
            if employer:
                self.organisation_id = employer.id
            else:
                self.employer_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Employer with the SDL / N Number does not exist in the system"
                    }
                }
    
    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    @api.constrains('document_ids')
    def check_required_fields(self):
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')

    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id
        learner_status = self.learner_id.mapped('bursary_learnership_line').\
        filtered(lambda val: val.bursary_type_id.id == self.bursary_type_id.id and val.qualification_id.id == self.qualification_id.id \
        and val.financial_year_id.id == self.financial_year_id.id) \
        or self.env['inseta.bursary.learnership'].search([
            ('bursary_type_id', '=',self.bursary_type_id.id),
            # ('learner_id', '=',self.learner_id.id),
            ('qualification_id', '=',self.qualification_id.id),
            ('financial_year_id', '=',self.financial_year_id.id),
            # ('programme_status_id', 'in', [registered_status, completed_status,uncompleted_status])
            ], limit=1)
        if learner_status:
            self.bursary_type_id = False 
            # return {
            # 			'warning': {
            # 				'title': 'Validation',
            # 				'message': f'{self.learner_id.name} is already enrolled or has completed this programme')
            # 			}
            # 		}
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme')
        
    @api.onchange('qualification_id')
    def _onchange_programme_id(self):
        if self.qualification_id:
            self.check_learner_status()
            self._get_compulsory_document()
    

class InsetaWilTvetType(models.Model):
    _name = "inseta.wiltvet.type"
    _order= "id desc"
    _rec_name = "description"

    description = fields.Char('Name')
    saqacode = fields.Char('SAQA CODE')
    active = fields.Boolean('Active', default=True)
    legacy_system_id = fields.Integer('Legacy System ID')


class InsetaWilTvetLearnership(models.Model):
    _name = "inseta.wiltvet.learnership"
    _inherit = ["inseta.learner.learnership"]
    _order= "id desc"
    _rec_name = "programme_id"

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id 

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 
    
    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    edit_mode = fields.Boolean(default=True)
    lpro_id = fields.Integer()
    state = fields.Char(string='State')
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_wilvet_document_id", string="Documents")
    programme_id = fields.Many2one('inseta.wiltvet.type', 'Wiltvet type', readonly=False)#
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_wiltvet_learnership_rel', 'ir_attachment_wiltvet_learnership_id', 'ir_attachment_qual_learnership_rel_id', required=False)
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])								
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user(), domain=lambda act: [('active', '=', True)])
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer')
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=False, help="Determines if this programme type will be computed based on unit standard credits")

    # discard
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification',readonly=False, domain=lambda act: [('active', '=', True)])#  compute="_compute_skills_programming_id")
    skill_programme_id = fields.Many2one("inseta.skill.programme", string='Skill Programme', domain=lambda act: [('active', '=', True)])
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
    cummulative_spend = fields.Char('Cummulative spend')
    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
    learner_id = fields.Many2one('inseta.learner', string="Learner Name", store=True)
    financial_year_id = fields.Many2one('res.financial.year', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    certificate_number = fields.Char('Certificate Number')
    achievement_date = fields.Date('Achievement Date')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    reference = fields.Char('Reference')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True)
    student_number = fields.Char('Student Number')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status',default=lambda self: self.env.ref('inseta_base.data_sec_2').id, store=True)
    lga_number = fields.Char('LGA Number')
    effective_date = fields.Date('Status Effective Date')
    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('Programme code') # , related="qualification_id.saqa_id")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )

    programme_status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Programme Status"
    )
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'wiltvet_unit_standard_rel', 'column1', string="WILTVET Unit Standard")
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    elective_learnership_unit_standard_line_ids = fields.Many2many(
        "inseta.learnership.unit.standard", 
        'elective_learnership_unit_standard_rel2', 
        'elective_learnership_unit_standard_id2', 
        string="Elective wiltvet Unit Standard")

    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 
            
    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    @api.depends('dgtype_code')
    def compute_socio_economic_status(self):
        if self.dgtype_code in ['LRN-W']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    def _get_compulsory_document(self):
        self.document_ids = False 
        docs = [
                'Work Base Placement Learning Agreement (WBPLA)', 'POPIA consent form', 
                'Certified Learner ID copy', 'Leaner N4-N6 SOR or Certificate', 'Matric certificate',
                'MOA with the college'
                ]
        for rec in docs:
            vals = {
                'name': rec,
                'learner_wilvet_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]

    @api.onchange('programme_id')
    def onchange_programme(self):
        if self.programme_id:
            self._get_compulsory_document()
            # self.unit_standard_ids = [(6, 0, [rec.id for rec in self.programme_id.mapped('unit_standard_ids').filtered(lambda se: se.unit_standard_type.name in ['Core', 'core', 'Fundamental', 'fundamental'])])]
    
    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':"Provider with the SDL / N Number does not exist in the system"
                    }
                }

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

    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    @api.constrains('document_ids')
    def check_required_fields(self):
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')

    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id
        learner_status = self.learner_id.mapped('wiltvet_learnership_line').\
        filtered(lambda val: val.qualification_id.id == self.qualification_id.id \
        and val.financial_year_id.id == self.financial_year_id.id) 
        # \
        # or self.env['inseta.wiltvet.learnership'].search([('learner_id', '=',self.learner_id.id),('qualification_id', '=',self.qualification_id.id), 
        # ('financial_year_id', '=',self.financial_year_id.id)], limit=1)
        if learner_status:
            self.qualification_id = False
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme')

            # return {
            # 			'warning': {
            # 				'title': 'Validation',
            # 				'message': f'{self.learner_id.name} is already enrolled or has completed this programme')
            # 			}
            # 		}

    @api.onchange('qualification_id')
    def _onchange_programme_id(self):
        if self.qualification_id:
            self.check_learner_status()
            self._get_compulsory_document()
    

class InsetaCandidacyLearnership(models.Model):
    _name = "inseta.candidacy.learnership"
    _inherit = ["inseta.learner.learnership"]
    _rec_name = "programme_id"
    _order= "id desc"

    def set_to_edit(self):
        self.edit_mode = True if self.edit_mode == False else False 

    def get_provider_default_user(self):
        user = self.env.user.id
        provider = self.env['inseta.provider'].search([('user_id', '=', user)], limit=1)
        return provider.id 

    enrollment_date = fields.Date('Enrollment Date', default=fields.Date.today())
    lpro_id = fields.Integer()
    edit_mode = fields.Boolean(default=True)
    # state = fields.Char(string='State')
    certificate_issued = fields.Boolean('Certificate Issued', default=False)
    document_ids = fields.One2many("inseta.learner.document", "learner_candidacy_document_id", string="Documents")
    programme_id = fields.Many2one('inseta.candidacy.programme', 'Candidacy Type', readonly=False)#
    attachment_ids = fields.Many2many('ir.attachment', 'inseta_candidacy_learnership_rel', 'ir_attachment_candidacy_learnership_id', 'ir_attachment_qual_learnership_rel_id', required=False)
    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    assessment_id = fields.Many2one('inseta.learnership.assessment', string='Assessment')	
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, default = lambda self: self.get_provider_default_user(), domain=lambda act: [('active', '=', True)])								
    organisation_id = fields.Many2one('inseta.organisation', string='Employer', default=lambda s: s.get_employer_default_user())
    secondary_provider_id = fields.Many2one('inseta.provider', string='Provider', domain=lambda act: [('active', '=', True)])								
    secondary_organisation_id = fields.Many2one('inseta.organisation', string='Secondary Employer')
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    enrollment_status_id = fields.Many2one('res.enrollment.status', string="enrollment status", required=False)
    institution_id = fields.Many2one('res.inseta.institution', string='Institution')
    # discard
    qualification_id = fields.Many2one('inseta.qualification', 'Qualification',readonly=False, domain=lambda act: [('active', '=', True)])#  compute="_compute_skills_programming_id")
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
    
    agreement_number = fields.Char('Agreement Number')
    commencement_date = fields.Date('Commencement Date')
    completion_date = fields.Date('Completion Date')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor', required=False)
    funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')

    financial_year_id = fields.Many2one('res.financial.year', required=False)
    project_id = fields.Many2one('project.project', required=False)
    approved_date = fields.Date('Approved Date')
    certificate_number = fields.Char('Certificate Number')
    achievement_date = fields.Date('Achievement Date')
    certificate_created_by = fields.Char('Certificate created by')
    certificate_created_date = fields.Date('Certificate Issue Date')
    lga_number = fields.Char('LGA Number')
    endorsed = fields.Boolean('Endorsed', default=False)
    verified = fields.Boolean('Verified', default=False)
    is_successful = fields.Boolean('Successful', default=False)
    legacy_system_id = fields.Integer(string='Legacy System')
    active = fields.Boolean(string='Active', default=True)

    student_number = fields.Char('Student Number')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status', default=lambda self: self.env.ref('inseta_base.data_sec_1').id, store=True)
    effective_date = fields.Date('Status Effective Date')

    most_recent_registration_date = fields.Date('Most recent registration date', compute="_compute_most_recent_registration_date")
    project_type_id = fields.Many2one('project.project', required=False)
    qualification_code = fields.Char('Programme code') # , related="qualification_id.saqa_id")
    status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Status"
    )
    programme_status = fields.Selection([ 
            ('enrolled','Enrolled'),
            ('achieved','achieved'),
            ('unachieved','Unachieved'),
            ('competent','Competent'),
            ('uncompetent','Not competent'),
            ('dropped','Dropped'),
        ],
        default="enrolled", string="Programme Status"
    )
    provider_sdl = fields.Char('Provider SDL / N No.')
    employer_sdl = fields.Char('Employer SDL / N No.')
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'candidacy_unit_standard_rel', 'column1', string="Candidacy Unit Standard")
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=False, help="Determines if this programme type will be computed based on unit standard credits")
    is_employed = fields.Boolean('Employed', default=False, compute="_compute_socio_economic_static")
    elective_learnership_unit_standard_line_ids = fields.Many2many(
        "inseta.learnership.unit.standard", 
        'elective_learnership_unit_standard_rel4', 
        'elective_learnership_unit_standard_id4', 
        string="Elective candidacy Unit Standard")

        
    @api.depends('socio_economic_status_id')
    def _compute_socio_economic_static(self):
        employed_socio_economic_status_id = self.env.ref('inseta_base.data_sec_1')
        if self.socio_economic_status_id and self.socio_economic_status_id.id == employed_socio_economic_status_id.id:
            self.is_employed = True 
        else:
            self.is_employed = False 
            
    @api.depends('commencement_date')
    def _compute_most_recent_registration_date(self):
        for rec in self:
            if rec.commencement_date:
                rec.most_recent_registration_date = rec.commencement_date 
            else:
                rec.most_recent_registration_date = False 

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    @api.depends('dgtype_code')
    def compute_socio_economic_status(self):
        if self.dgtype_code in ['LRN-W']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    def _get_compulsory_document(self):
        self.document_ids = False 
        docs = ['Highest qualification','Worker Programme Agreement', 'Certified ID copy', 'Proof of Registration', 'Quotation', 'Proof of Employment']
        for rec in docs:
            vals = {
                'name': rec,
                'learner_candidacy_document_id': self.id,
                'learner_document2_id': self.learner_id.id,
            }
            self.document_ids = [(0, 0, vals)]

    # @api.onchange('programme_id')
    # def onchange_programme(self):
    # 	if self.programme_id:
    # 		self._get_compulsory_document()
    # 		self.unit_standard_ids = [(6, 0, [rec.id for rec in self.programme_id.mapped('unit_standard_ids').filtered(lambda se: se.unit_standard_type.name in ['Core', 'core', 'Fundamental', 'fundamental'])])]
    
    def check_learner_status(self):
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id

        learner_status = self.learner_id.mapped('candidacy_learnership_line').\
        filtered(lambda val: val.qualification_id.id == self.qualification_id.id \
        and val.financial_year_id.id == self.financial_year_id.id) or \
        self.env['inseta.candidacy.learnership'].search([('learner_id', '=',self.learner_id.id),('qualification_id', '=',self.qualification_id.id), 
        ('financial_year_id', '=',self.financial_year_id.id)], limit=1)
        if learner_status:
            self.qualification_id = False 
            raise ValidationError(f'{self.learner_id.name} is already enrolled or has completed this programme')

            # return {
            # 			'warning': {
            # 				'title': 'Validation',
            # 				'message': f'{self.learner_id.name} is already enrolled or has completed this programme')
            # 			}
            # 		}

    @api.onchange('qualification_id')
    def _onchange_programme_id(self):
        if self.qualification_id:
            self.check_learner_status()
            self._get_compulsory_document()
            self.qualification_code = str(self.qualification_id.saqa_id)
            unit_standards = [record.id for record in self.qualification_id.mapped('unit_standard_ids')]
            
            domain = {'unit_standard_ids': [('id', '=', unit_standards)]}
            return {'domain': domain}

    @api.onchange('completion_date')
    def _onchange_end_date(self):
        end_date = self.completion_date	 
        if self.completion_date and self.commencement_date:
            if self.completion_date < self.commencement_date:
                self.completion_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.commencement_date}"
                    }
                }

    @api.onchange('commencement_date')
    def _onchange_commencement_date(self):
        if self.commencement_date and self.financial_year_id:
            if not (self.commencement_date >= self.financial_year_id.date_from and self.commencement_date <= self.financial_year_id.date_to):
                self.commencement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Commencement End date must be within the financial year period !!!"
                    }
                }

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

    @api.onchange('provider_sdl')
    def onchange_provider_sdl(self):
        if self.provider_sdl:
            provider = self.env['inseta.provider'].search([('employer_sdl_no', '=', self.provider_sdl)], limit=1)
            if provider:
                self.provider_id = provider.id
            else:
                self.provider_sdl = False
                self.provider_id = False 
                return {
                        'warning': {
                            'title': "Validation Error!",
                            'message':"Provider with the SDL / N Number does not exist in the system"
                        }
                    }
    
    @api.onchange('provider_id')
    def onchange_provider_id(self):
        if self.provider_id:
            self.provider_sdl = self.provider_id.employer_sdl_no

    @api.onchange('organisation_id')
    def onchange_organisation_id(self):
        if self.organisation_id:
            self.employer_sdl = self.organisation_id.sdl_no

    @api.constrains('document_ids')
    def check_required_fields(self):
        if self.mapped('document_ids').filtered(lambda s: s.datas == False):
            raise ValidationError('Compulsory documents must be filled')


class InsetaLearnershipAssessment(models.Model): # main assessment form
    _name = "inseta.learnership.assessment"
    _description = "Holds the assessment unit standards and credits"
    _rec_name = "reference"
    _order= "id desc"

    lpro_id = fields.Integer()
    reference = fields.Char('Reference')
    parent_id = fields.Integer('Parent ID')
    learner_register_id = fields.Many2one("inseta.learner.register", 'Learner ID')
    learner_id = fields.Many2one("inseta.learner", 'Learner ID') #, compute="compute_learner_id", store=True)
    learner_parent_id = fields.Integer('Parent Learner ID')

    provider_parent_id = fields.Integer('Parent Provider ID')  
    learner_assessment_detail_id = fields.Many2one("inseta.learner.assessment.detail", 'Learner')
    credits = fields.Integer(string="Learner's Credits", compute="compute_learner_achievement_lines", store=True)
    minimum_credits = fields.Integer(string='Minimum Credits', store=True)
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status') #, default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    temp_programme_status_id = fields.Many2one("inseta.program.status", string='Proposed Status') #, default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)

    previously_achieved = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="", string='Previously Achieved')
    is_competent = fields.Selection([('Competent', 'Competent'), ('Not Competent', 'Not Competent')], default="", string='Competent')
    assessor_id = fields.Many2one("inseta.assessor", 'Assesssor', domain=lambda act: [('active', '=', True)])
    assessment_date = fields.Date('Assessment Date')
    moderator_id = fields.Many2one("inseta.moderator", 'Moderator', domain=lambda act: [('active', '=', True)])
    moderator_date = fields.Date('Moderation Date')
    achievement_date = fields.Date('Achievement Date')
    enrollment_date = fields.Date('Enrollment Date')

    document_upload_id = fields.Binary('Upload Document')
    document = fields.Binary(string="Document")
    dgtype_code = fields.Char('DG Type Code')
    provider_id = fields.Many2one('inseta.provider', string='Provider', required=False, domain=lambda act: [('active', '=', True)])
    provider_sdl = fields.Char('Provider SDL / N No.')
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),], string="Status", default="draft")
    
    status = fields.Selection([ 
            ('achieved','Achieved'),
            ('unachieved','Unachieved'),
            ('dropped','Dropped'),
        ],
        default="", string="Status",
    )
    # new fields
    is_programme = fields.Selection([
        ('skill', 'Skills'), 
        ('learner', 'Learnership'),
        ('qual', 'Qualification'),
        ('candidacy', 'Candidacy'),
        ('intern', 'Internship'),
        ('bursary', 'Bursary'),
        ('all', 'All'),
        ], string="Programmes ?")

    # discard
    unit_standard_type = fields.Many2one("inseta.unit.standard.type", string='Unit standard Type')
    programme_id = fields.Many2one('inseta.programme', string='Programme', required=False)
    # nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    skill_programmes_id = fields.Many2one("inseta.skill.programme", string='Skill Programme', domain=lambda act: [('active', '=', True)])
    learner_programmes_id = fields.Many2one("inseta.learner.programme", string='Learnership Programme', domain=lambda act: [('active', '=', True)])#, default=lambda self: self._get_default_programme())
    qualification_id = fields.Many2one("inseta.qualification", string='Qualification', domain=lambda act: [('active', '=', True)])
    unit_standard_id = fields.Many2one("inseta.unit.standard", string='Unit standard', domain=lambda act: [('active', '=', True)])
    bursary_id = fields.Many2one("inseta.bursary.programme", string='Bursary')
    bursary_type_id = fields.Many2one('res.bursary.type', 'Bursary type')

    candidacy_id = fields.Many2one("inseta.candidacy.programme", string='Candidacy')
    wiltvet_id = fields.Many2one("inseta.wiltvet.programme", string='Wiltvet')
    internship_id = fields.Many2one("inseta.internship.programme", string='Internship')
    financial_year_id = fields.Many2one('res.financial.year', required=False,tracking=True)

    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_learnership_assessment_unit_standard_rel', 'inseta_learnership_assessment_unit_standard_id', string='Unit standards')
    inseta_learner_register = fields.Many2one('inseta.learner.register', string='Learner Register', required=False)
    inseta_skill_register = fields.Many2one('inseta.learner.register', string='Skill Register', required=False)
    inseta_qualification_register = fields.Many2one('inseta.learner.register', string='Qualification Register', required=False)
    learner_achievement_lines = fields.Many2many("inseta.learnership.achievement", 'learner_achievement_line_rel', string="Achievements")
 
    elective_credits = fields.Integer('Elective Credits', default=False,store=True, compute="compute_learner_achievement_lines")
    core_credits = fields.Integer('Core Credits', default=False, store=True, compute="compute_learner_achievement_lines")
    fundamental_credits = fields.Integer('Fundamental Credits', default=False, store=True, compute="compute_learner_achievement_lines")
    is_unit_standard = fields.Boolean('Unit standard Applicable?', default=True) 

    # # changes 
    # qualification_learnership_line = fields.Many2many("inseta.learner_qualification.assessment", 'inseta_learner_qualification_ver_rel', 'inseta_qual_ver_id', 'inseta_assessment_ver_id', string='Qualification Learnership Assessment')
    # learnership_learnership_line = fields.Many2many("inseta.learner_learnership.assessment", 'inseta_learnership_ver_rel', 'inseta_learnership_ver_id', 'inseta_assessment_ver_id', string='Learnership Assessment')
    # skills_learnership_line = fields.Many2many("inseta.skill_learnership.assessment", 'inseta_skill_learnership_ver_rel', 'inseta_skill_learnership_ver_id', 'inseta_assessment_ver_id', string='Learnership Assessment')

    @api.depends('dgtype_code')
    def compute_socio_economic_status(self):
        if self.dgtype_code in ['LRN-W']:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_1').id
        else:
            self.socio_economic_status_id = self.env.ref('inseta_base.data_sec_2').id

    def add_learner_to_assessment(self):
        if self.learner_parent_id:
            learner = self.env['inseta.learner'].browse([self.learner_parent_id])
            learner.learner_assessment_lines = [(4, self.id)]
        else:
            raise ValidationError('Error !!! No learner found for the assessment')

    def compute_competency(self,learnerObj, programme, learnership_line):
        """This determines the achievement of the learner by check if the learner's unit standard credits
        is above the programme minimum credits;
        unit standard, bursary, candidacy, internship selects the programme status manually, a temporal field
        as created to store the selection, once the approve button is click, it updates the status of the main
        programme status
        """
        rec = self
        registered_status = self.env.ref('inseta_etqa.id_programme_status_01').id
        enrolled_status = self.env.ref('inseta_etqa.id_programme_status_06').id
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        uncompleted_status = self.env.ref('inseta_etqa.id_programme_status_03').id
        withdraw_status = self.env.ref('inseta_etqa.id_programme_status_04').id

        core_result_check = programme.core_credits 
        fundamental_result_check = programme.fundamental_credits 
        elective_result_check = programme.elective_credits
        if rec.programme_status_id.id in [registered_status, enrolled_status, False] and not rec.temp_programme_status_id:
            # raise ValidationError("EW")
            # determines if the programme status is still registered,
            # it means the status was selected manually for internship, bursary , candidacy and wiltvet
            """
            if fundamental is less than programme fundamental or .... core is less than programme core or elective is less than programme 
            it should remain umcompleted 
            """
            if rec.fundamental_credits < fundamental_result_check or rec.core_credits < core_result_check or rec.elective_credits < elective_result_check:
                for ln in learnership_line:
                    ln.status = "uncompetent"
                    ln.programme_status_id = uncompleted_status
                    ln.achievement_date = fields.Date.today()
                rec.status = "unachieved"
                rec.programme_status_id = uncompleted_status
                
            else:
                for ln in learnership_line:
                    ln.status = "competent"
                    ln.programme_status_id = completed_status
                    ln.achievement_date = fields.Date.today()
                rec.status = "achieved"
                rec.programme_status_id = completed_status
         
        elif rec.programme_status_id.id == completed_status:
            for ln in learnership_line:
                ln.status = "competent"
                ln.programme_status_id = completed_status
                ln.achievement_date = fields.Date.today()
            rec.status = "achieved"
            rec.programme_status_id = completed_status

        elif self.programme_status_id.id == uncompleted_status:
            for ln in learnership_line:
                ln.status = "uncompetent"
                ln.programme_status_id = uncompleted_status
                ln.achievement_date = fields.Date.today()
            rec.status = "unachieved"
            rec.programme_status_id = uncompleted_status

        elif rec.programme_status_id.id == withdraw_status:
            for ln in learnership_line:
                ln.status = "uncompetent"
                ln.programme_status_id = withdraw_status
                ln.achievement_date = fields.Date.today()
            rec.status = "unachieved"
            rec.programme_status_id = withdraw_status

        elif not rec.programme_status_id and rec.temp_programme_status_id:
            # e.g unit standard, bursary, candidacy, internship
            for ln in learnership_line:
                # ln.status = "competent"
                ln.programme_status_id = rec.temp_programme_status_id.id
                ln.achievement_date = fields.Date.today()
            # rec.status = "achieved"
            rec.programme_status_id = rec.temp_programme_status_id.id
        rec.achievement_date = fields.Date.today()

    def action_validate_result(self, learnerObj, non_qualification = False):
        for rec in self: 
            core_result_check = 0
            fundamental_result_check = 0 
            elective_result_check = 0
            if rec.skill_programmes_id:
                learnership_line = learnerObj.mapped('skill_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.skill_programme_id.id == rec.skill_programmes_id.id)
                rec.compute_competency(learnerObj, rec.skill_programmes_id, learnership_line)

            if rec.learner_programmes_id:
                learnership_line = learnerObj.mapped('learner_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.learner_programme_id.id == rec.learner_programmes_id.id)
                rec.compute_competency(learnerObj,rec.learner_programmes_id, learnership_line)
 
            if rec.qualification_id: # and not rec.bursary_type_id:
                if not non_qualification:
                    learnership_line = learnerObj.mapped('qualification_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.qualification_id.id == rec.qualification_id.id)
                    rec.compute_competency(learnerObj,rec.qualification_id, learnership_line)

                else:
                    # internship
                    learnership_line = learnerObj.mapped('internship_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.qualification_id.id == rec.qualification_id.id)
                    rec.compute_competency(learnerObj,rec.qualification_id, learnership_line)

                    # wiltvet
                     
                    learnership_line = learnerObj.mapped('wiltvet_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.qualification_id.id == rec.qualification_id.id)
                    rec.compute_competency(learnerObj,rec.qualification_id, learnership_line)

                    # candidacy
                    learnership_line = learnerObj.mapped('candidacy_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.qualification_id.id == rec.qualification_id.id)
                    rec.compute_competency(learnerObj,rec.qualification_id, learnership_line)
            
            if rec.unit_standard_id:
                # candidacy
                learnership_line = learnerObj.mapped('unit_standard_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id and val.unit_standard_id.id == rec.unit_standard_id.id)
                rec.compute_competency(learnerObj,rec.unit_standard_id, learnership_line)


            if rec.bursary_type_id:
                learnership_line = learnerObj.mapped('bursary_learnership_line').filtered(lambda val: val.financial_year_id.id == rec.financial_year_id.id) # and val.qualification_id.id == rec.qualification_id.id and val.bursary_type_id.id == rec.bursary_type_id.id)
                rec.compute_competency(learnerObj,rec.qualification_id, learnership_line)
                
            rec.add_learner_to_assessment()  

    @api.depends('learner_achievement_lines')
    def compute_learner_achievement_lines(self):
        self.method_learner_achievement_lines()

    def method_learner_achievement_lines(self):
        for rec in self:
            if rec.learner_achievement_lines:
                total_core = sum([cr.credits for cr in rec.mapped('learner_achievement_lines').filtered(lambda s: s.status == "competent" and s.unit_standard_type.name in ['core', 'Core'] and s.select_option == True)])
                rec.core_credits = total_core if total_core else 0
                
                total_elective_credits = sum([cr.credits for cr in rec.mapped('learner_achievement_lines').filtered(lambda s:s.status == "competent" and s.unit_standard_type.name in ['elective', 'Elective'] and s.select_option == True)])
                rec.elective_credits = total_elective_credits if total_elective_credits else 0

                total_fundamental_credits = sum([cr.credits for cr in rec.mapped('learner_achievement_lines').filtered(lambda s: s.status == "competent" and s.unit_standard_type.name in ['fundamental', 'Fundamental'] and s.select_option == True)])
                rec.fundamental_credits = total_fundamental_credits if total_fundamental_credits else 0
                
                rec.credits = total_fundamental_credits + total_elective_credits + total_core
                
            else:
                rec.credits = 0
                rec.core_credits = 0
                rec.elective_credits = 0
                rec.fundamental_credits = 0

    @api.depends('learner_parent_id')
    def compute_learner_id(self):
        pass 

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

    @api.onchange('learner_register_id', 'learner_parent_id', 'provider_parent_id')
    def learner_programme_domain(self):
        if self.provider_parent_id or self.learner_parent_id:
            provider_id = self.env['inseta.provider'].search([('id', '=', self.provider_parent_id)], limit=1)
            learner = self.env['inseta.learner'].search([('id', '=', self.learner_parent_id)], limit=1)
            assessment_id = self.env['inseta.assessment'].search([('id', '=', self.parent_id)], limit=1)
            if learner:
                skills_programme = learner.mapped('skill_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id) # skill_programme_id 
                learner_programme = learner.mapped('learner_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id)
                qual_programme = learner.mapped('qualification_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id)
                unit_programme = learner.mapped('unit_standard_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id) 
                intern_programme = learner.mapped('internship_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id) 
                bursary_programme = learner.mapped('bursary_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id) 
                wiltvet_programme = learner.mapped('wiltvet_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id)  
                candidacy_programme = learner.mapped('candidacy_learnership_line').filtered(lambda s: s.provider_id.id in [self.provider_id.id, self.provider_parent_id] and s.financial_year_id.id == self.financial_year_id.id)  
                # raise ValidationError([rec.qualification_id.id for rec in wiltvet_programme])
                qualifications = [rec.qualification_id.id for rec in qual_programme] + [rec.qualification_id.id for rec in bursary_programme] + [rec.qualification_id.id for rec in wiltvet_programme]
                return {'domain': {
                    'skill_programmes_id': [('id', 'in', [rec.skill_programme_id.id for rec in skills_programme])],
                    'learner_programmes_id': [('id', 'in', [rec.learner_programme_id.id for rec in learner_programme])],
                    'qualification_id': [('id', 'in', qualifications)],
                    'unit_standard_id': [('id', 'in', [rec.unit_standard_id.id for rec in unit_programme])],
                    'bursary_type_id': [('id', 'in', [rec.bursary_type_id.id for rec in bursary_programme])],
                }}

    @api.onchange('qualification_id', 'learner_programmes_id', 'skill_programmes_id', 'bursary_type_id')
    def _onchange_programme_id(self):
        if self.learner_programmes_id or self.skill_programmes_id or self.qualification_id:
            self.minimum_credits = self.learner_programmes_id.credits or self.skill_programmes_id.credits or self.qualification_id.credits
            self.credits = self.learner_programmes_id.credits or self.skill_programmes_id.credits or self.qualification_id.credits
            
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        provider_id = self.env['inseta.provider'].search([('id', '=', self.provider_parent_id)], limit=1)

        # unit_standards = [record.id for record in self.skill_programmes_id.mapped('unit_standard_ids')]
        error_msg = 'Learner has already achieved this programme for the selected financial year !!!'
         
        if self.bursary_type_id:
            # self.generate_achievement_lines(self.learner_programmes_id)
            learner_has_achieved_programme = self.learner_id.mapped('bursary_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.bursary_type_id.id == self.bursary_type_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.id == completed_status)
            if learner_has_achieved_programme: 
                raise ValidationError(error_msg)
            programme_line_id = self.learner_id.mapped('bursary_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.bursary_type_id.id and val.qualification_id.id == self.qualification_id.id)
            if programme_line_id:
                self.enrollment_date = programme_line_id[0].enrollment_date

        elif self.learner_programmes_id:
            learner_has_achieved_programme = self.learner_id.mapped('learner_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.learner_programme_id.id == self.learner_programmes_id.id and val.programme_status_id.id == completed_status)
            if learner_has_achieved_programme: 
                raise ValidationError(error_msg)
            
            # raise ValidationError(f"{self.learner_programmes_id.name} was not enrolled for this {learnerObj.name} with the selected financial year")
            programme_line_id = self.learner_id.mapped('learner_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.learner_programme_id.id)
            if programme_line_id:
                self.enrollment_date = programme_line_id[0].enrollment_date
            self.generate_achievement_lines(self.learner_programmes_id.learnership_unit_standard_ids)
            unit_standards = [record.unit_standard_id.id for record in self.learner_programmes_id.mapped('learnership_unit_standard_ids')]
            if unit_standards:
                domain = {
                    'unit_standard_ids': [('id', '=', unit_standards)]
                    }
                return {'domain': domain}
            else:
                pass
                 
        elif self.skill_programmes_id:
            # check to see if learner has the programme in his learner assessment line and if it is achieved
            learner_has_achieved_programme = self.learner_id.mapped('skill_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.skill_programme_id.id == self.skill_programmes_id.id and val.programme_status_id.name == "Completed")
            if learner_has_achieved_programme: 
                raise ValidationError(error_msg)
            programme_line_id = self.learner_id.mapped('skill_learnership_line').filtered(
                lambda val: val.financial_year_id.id == self.financial_year_id.id and val.skill_programme_id.id == self.skill_programmes_id.id)
            if programme_line_id:
                self.enrollment_date = programme_line_id[0].enrollment_date
            self.generate_achievement_lines(self.skill_programmes_id.skill_unit_standard_ids)
            assessment_id = self.env['inseta.assessment'].search([('id', '=', self.parent_id)], limit=1)

        elif self.qualification_id:
            # check to see if learner has the programme in his learner assessment line and if it is achieved
            learner_has_achieved_programme = self.learner_id.mapped('qualification_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.id == completed_status)
            if learner_has_achieved_programme: 
                raise ValidationError(error_msg) 

            programme_line_id = self.learner_id.mapped('qualification_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.qualification_id.id == self.qualification_id.id)
            if programme_line_id:
                self.enrollment_date = programme_line_id[0].enrollment_date
            self.generate_achievement_lines(self.qualification_id.qualification_unit_standard_ids)
        else:
            pass 

        assessor_provider_domain = {}
        if provider_id:
            assessor_provider_domain = {
                'assessor_id': [('id', 'in', provider_id.provider_assessor_ids.ids if provider_id.provider_assessor_ids else None)],
                'moderator_id': [('id', 'in', provider_id.provider_moderator_ids.ids if provider_id.provider_moderator_ids else None)],
                }
        return {'domain': assessor_provider_domain}
        
    def check_all_options(self):
        if self.learner_achievement_lines:
            for lac in self.learner_achievement_lines:
                lac.select_option = True
             
    def uncheck_all_options(self):
        if self.learner_achievement_lines:
            for lac in self.learner_achievement_lines:
                lac.select_option = False
             
    def action_set_competent(self):
        for rec in self.learner_achievement_lines:
            if rec.select_option:
                rec.status = "competent"
        self.method_learner_achievement_lines()

    def action_set_uncompetent(self):
        for rec in self.learner_achievement_lines:
            if rec.select_option:
                rec.status = "uncompetent"
        self.method_learner_achievement_lines()

    def generate_achievement_lines(self, programme_unit_standard_lines):
        # builds unit standard lines based on programme
        if not programme_unit_standard_lines:
            self.is_unit_standard = False
        for unit in programme_unit_standard_lines:
            vals = {
                    'learner_id': self.learner_parent_id,
                    'credits': unit.unit_standard_id.credits,
                    'unit_standard_id': unit.unit_standard_id.id,
                    'learner_achievement_id': self.id,
                    'status': 'uncompetent',
                    'unit_standard_type': unit.unit_standard_type_id.id,
            }
            achievement_id = self.env['inseta.learnership.achievement'].create(vals)
            self.learner_achievement_lines = [(4, achievement_id.id)]

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.learnership.assessment')
        vals['reference'] = sequence or '/'
        res = super(InsetaLearnershipAssessment, self).create(vals)
        return res 
    
