from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class InsetaLearnershipAchievement(models.Model):
	_name = 'inseta.learnership.achievement'
	_description = "learnership achievement"

	learner_id = fields.Many2one('inseta.learner')
	learner_achievement_id = fields.Many2one('inseta.learnership.assessment')
	programme_status_id = fields.Many2one("inseta.program.status", string='Programme Status', default= lambda s: s.env.ref('inseta_etqa.id_programme_status_01').id)
	unit_standard_id = fields.Many2one("inseta.unit.standard", string='Unit Standard')
	select_option = fields.Boolean(string="Select")
	code = fields.Char('Code', related="unit_standard_id.code")
	unit_standard_type = fields.Many2one('inseta.unit.standard.type', store=True, string="Unit standard type")
	status = fields.Selection([ 
			('competent','Competent'),
			('uncompetent','Not competent'),
		],
		default="", string="Status"
	)
	credits = fields.Integer(string='Credits', store=True)


class LearnerUnitStandardAssessment(models.Model):
	"""This model holds the record of all Unit standard Assessment applications """

	_name = 'inseta.learner.unit.standard.assessment'

	unit_standard_id = fields.Many2one("inseta.unit.standard", 'Unit Standard')
	assessor_id = fields.Many2one("inseta.assessor", 'Assesssor', domain=lambda act: [('active', '=', True)])
	assessment_date = fields.Date('Assessment Date')
	moderator_id = fields.Many2one("inseta.moderator", 'Moderator', domain=lambda act: [('active', '=', True)])
	moderator_date = fields.Date('Moderation Date')
	learner_register_id = fields.Many2one('inseta.learner.register')
	learner_id = fields.Many2one('inseta.learner')
	credits = fields.Integer(string='Credits', store=True)

	status = fields.Selection([ 
			('enrolled','Enrolled'),
			('achieved','Achieved'),
			('unachieved','Unachieved'),
			('dropped','Dropped'),
			('competent','Competent'),
			('uncompetent','Not competent'),
		],
		default="", string="Status"
	)

#     learner_assessment_id = fields.Many2one('inseta.learner')

# 	learnership_programme_id = fields.Many2one('inseta.learner.programme', 'Learnership programme', readonly=False)#
# 	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_standard_learnership_rel', 'column1', string="learnership Unit Standards")


# class InsetaqualificationAchievement(models.Model):
# 	_name = 'inseta.qualification.achievement'
#     _description = "Qualification achievement"

#     learner_assessment_id = fields.Many2one('inseta.learner')
# 	qualification_id = fields.Many2one('inseta.qualification', 'Qualification', readonly=False)#
# 	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_standard_qualification_rel', 'column1', string="Qualification Unit Standards")

# 	learner_assessment_lines = fields.Many2many("inseta.learnership.assessment", 'inseta_learner_assessement_line_rel', 'inseta_learner_assessement_line_id', string='Learner Assessment')



# class InsetaSkillAchievement(models.Model):
# 	_name = 'inseta.skill.achievement'
#     _description = "Skill achievement"

#     learner_assessment_id = fields.Many2one('inseta.learner')
# 	skill_programme_id = fields.Many2one('inseta.skill.programme', 'Skills Programe', readonly=False)#
# 	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_standard_skill_rel', 'column1', string="Skill Unit Standards")
# inseta_inseta_learnership_achievement,access_name_inseta_learnership_achievement,model_inseta_learnership_achievement,,1,1,1,1
# inseta_inseta_qualification_achievement,access_name_inseta_qualification_achievement,model_inseta_qualification_achievement,,1,1,1,1
# inseta_inseta_skill_achievement,access_name_inseta_skill_achievement,model_inseta_skill_achievement,,1,1,1,1