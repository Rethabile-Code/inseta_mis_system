from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)

class InsetaLearnerSkillPartialAssessment(models.Model): # main assessment form
    _name = "learner.skill.partial_assessment"
    _description = "Holds the learnership partial assessment"
    _order= "id desc"

    inseta_assessment_detail_id = fields.Many2one("inseta.learner.assessment.detail", string='Assessment Detail ID')
    learner_skill_learnership_id = fields.Many2one("inseta.skill.learnership", string='Learner learnership ID')
    learner_skill_assessment_id = fields.Many2one("inseta.skill_learnership.assessment", string='Learner Skills Assessment ID')

    unit_standard_id = fields.Many2one("inseta.unit.standard", 'Unit standard', compute="compute_learner_skill_assessment_id")
    unit_standard_type_id = fields.Many2one("inseta.unit.standard.type", string='Unit standard type',  compute="compute_learner_skill_assessment_id")
    code = fields.Char(string='Code', related="unit_standard_id.code")
    learner_id = fields.Many2one("inseta.learner", 'Learner ID', compute="compute_learner_skill_assessment_id") #, compute="compute_learner_id", store=True)

    @api.depends('learner_skill_assessment_id')
    def compute_learner_skill_assessment_id(self):
        for rec in self:
            if rec.learner_skill_assessment_id:
                rec.unit_standard_id = rec.learner_skill_assessment_id.unit_standard_id.id
                rec.unit_standard_type_id = rec.learner_skill_assessment_id.unit_standard_type_id.id
                rec.learner_id = rec.learner_skill_assessment_id.learner_id.id
            else:
                rec.unit_standard_id =False
                rec.unit_standard_type_id = False
                rec.learner_id = False

class InsetaLearnerSkillLearnershipAssessment(models.Model): # main assessment form
    _name = "inseta.skill_learnership.assessment"
    _description = "Holds the learnership assessment"
    _order= "id desc"
    _rec_name = "learner_skill_learnership_id"

    learner_id = fields.Many2one("inseta.learner", 'Learner ID') #, compute="compute_learner_id", store=True)
    learner_skill_learnership_id = fields.Many2one("inseta.skill.learnership", string='Learner learnership ID')
    inseta_assessment_detail_id = fields.Many2one("inseta.learner.assessment.detail", string='Assessment Detail ID')
    assessor_id = fields.Many2one("inseta.assessor", 'Assesssor', domain=lambda act: [('active', '=', True)])
    assessment_date = fields.Date('Assessment Date')
    moderator_id = fields.Many2one("inseta.moderator", 'Moderator', domain=lambda act: [('active', '=', True)])
    moderator_date = fields.Date('Moderation Date')
    achievement_date = fields.Date('Achievement Date')
    enrollment_date = fields.Date('Enrollment Date')
    created_date = fields.Date('Created Date')
    created_by = fields.Integer('Created by')
    verification_date = fields.Date('Verification Date')
    programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status') #, default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    assessment_status_id = fields.Many2one("inseta.assessment.status.model", string='Assessment Status') #, default= lambda s: s.env.ref('inseta_etqa.id_programme_status_06').id)
    unit_standard_id = fields.Many2one("inseta.unit.standard", 'Unit standard')
    unit_standard_type_id = fields.Many2one("inseta.unit.standard.type", string='Unit standard type')
    select = fields.Boolean("Select")
    credits = fields.Integer(string='Credits')
    code = fields.Char(string='Code', related="unit_standard_id.code")
    completed = fields.Boolean("Completed", default=False,)# compute="_get_assessment_status")

    # @api.depends('assessment_status_id')
    # def _get_assessment_status(self):
    #     competent_status_id = self.env.ref('inseta_etqa.id_assessment_status_competent')
    #     if self.assessment_status_id and self.assessment_status_id.id == competent_status_id.id:
    #         self.completed = True 
    #     else:
    #         self.completed = False

    @api.onchange('learner_skill_learnership_id')
    def onchange_learner_skill_learnership_id(self):
        if self.learner_skill_learnership_id:
            items = self.learner_skill_learnership_id.unit_standard_ids.ids if self.learner_skill_learnership_id.unit_standard_ids else None 
            return {
                'domain': {
                    'unit_standard_id': [('id', 'in', items)]
                }
            }

    @api.onchange('learner_id')
    def onchange_learner_id(self):
        if self.learner_id:
            completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
            skill_learnership_line = self.learner_id.mapped('skill_learnership_line').filtered(lambda lrn: lrn.programme_status_id.id != completed_status)
            return {
                'domain': {
                    'learner_skill_learnership_id': [('id', 'in', [rec.id for rec in skill_learnership_line])]
                }
            }

