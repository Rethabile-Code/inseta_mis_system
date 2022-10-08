from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError, AccessError


class InsetaLearnerfinancialBudget(models.Model):
	_name = 'inseta.learner.financial.budget'
	_description = """This model holds the record of financial budget of all learners applications """
	
	learner_register_id = fields.Many2one('inseta.learner')
	financial_year_id = fields.Many2one('res.financial.year')
	approved_amount = fields.Float('Approved Amount')
	funding_type = fields.Many2one('res.fundingtype', string='Funding Type', required=False)
	# dgbursary_detail_id = fields.Many2one('inseta.dgbursplearnerdetails', string='DG Bursary Details', required=False)


class InsetaLearnerInherit(models.Model):
	_inherit = 'inseta.learner.register'

	lpro_learner_id = fields.Many2one('inseta.lpro', string='Learner Learning programmme')
	financial_budget_ids = fields.One2many('inseta.learner.financial.budget', 'learner_register_id', string='Financial budget lines')

