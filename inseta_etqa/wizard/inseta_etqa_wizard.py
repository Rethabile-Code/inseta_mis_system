from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

class insetaETQAWizard(models.Model):
	_name = 'inseta.etqa.wizard'
	_description  = "ETQA Wizards"
	
	name = fields.Text('Message/Reason', required=True)
	date = fields.Datetime('Date') 
	user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user.id)
	reference = fields.Integer('Reference ID', default=False, readonly=True)
	model_name = fields.Char('Model Name:', readonly=True)
	action = fields.Selection([('refusal', 'Refusal'),('rework', 'Rework'),('query', 'Query'), ('mass', 'Mass Notification')], 
	string="Action", help="Action to perform. Set to refusal if you want to refuse a record")

	def post_action(self):
		model = str(self.model_name)
		ref_id = self.env['{}'.format(model)].browse([self.reference])
		if ref_id:
			if self.action == "refusal":
				ref_id.update({'comments': '', 'refusal_comment': self.name.capitalize() if self.name else '',
				'state': 'denied', 'denied_date': fields.date.today()})
				ref_id.action_reject_method()
			elif self.action in ["rework", "query"]:
				ref_id.update({'comments': self.name.capitalize() if self.name else '', 'refusal_comment': ''})
				ref_id.eval_committee_send_query_notification() 
		return{'type': 'ir.actions.act_window_close'}


class insetaPMFWizard(models.TransientModel):
	_name = 'inseta.amf.wizard'
	_description = "Wizard to add provider, moderator, facilitators"

	moderator_ids = fields.Many2many('inseta.moderator', 'amf_moderator_rel', string="Moderator") 
	assessor_ids = fields.Many2many('inseta.assessor','amf_assessor_rel', string="Assessor") 
	facilitator_ids = fields.Many2many('inseta.assessor', 'amf_facilitator_rel', string="Facilitator") 

	assessor_id = fields.Many2one('inseta.assessor', string="Assessor", domain=lambda act: [('active', '=', True)]) 
	moderator_id = fields.Many2one('inseta.moderator', string="Moderator", domain=lambda act: [('active', '=', True)]) 
	qualification_id = fields.Many2one('inseta.qualification', string="Qualification") 
	unit_standard_id = fields.Many2one('inseta.unit.standard', string="Unit standard") 
	skill_programme_id = fields.Many2one('inseta.skill.programme', string="Skills") 
	learner_programme_id = fields.Many2one('inseta.learner.programme', string="Learnership") 
	reference = fields.Integer('Reference ID', default=False, readonly=True)
	action = fields.Selection([('moderator', 'Moderator'),('assessor', 'Assessor'),('facilitator', 'Facilitator'),('linking', 'Programme Linking')], 
	string="Action", help="Action to perform")

	def action_link_to_programme(self):
		ref_id = self.env['inseta.provider'].search([('id', '=', self.reference)],limit=1)
		if self.qualification_id:
			ref_id.provider_qualification_ids = [(0, 0, {
				'moderators_id': self.moderator_id.id,
				'assessors_id': self.assessor_id.id,
				'qualification_id': self.qualification_id.id,
				'provider_id': self.reference,
			})]
			ref_id.qualification_ids = [(4, self.qualification_id.id)]

		if self.learner_programme_id:
			ref_id.provider_learnership_accreditation_ids =  [(0, 0, {
				'moderators_id': self.moderator_id.id,
				'assessors_id': self.assessor_id.id,
				'programme_id': self.learner_programme_id.id,
				'provider_id': self.reference,
			})] 
			ref_id.learner_programmes_ids = [(4, self.learner_programme_id.id)]

		if self.unit_standard_id:
			ref_id.provider_unit_standard_ids =  [(0, 0, {
				'moderators_id': self.moderator_id.id,
				'assessors_id': self.assessor_id.id,
				'programme_id': self.unit_standard_id.id,
				'provider_id': self.reference,
			})]
			ref_id.unit_standard_ids = [(4, self.unit_standard_id.id)]

		if self.skill_programme_id:
			ref_id.provider_skill_accreditation_ids =  [(0, 0, {
				'moderators_id': self.moderator_id.id,
				'assessors_id': self.assessor_id.id,
				'programme_id': self.skill_programme_id.id,
				'provider_id': self.reference,
			})]
			ref_id.skill_programmes_ids = [(4, self.skill_programme_id.id)]

	def post_action(self):
		if self.action != "linking":
			if not (self.moderator_ids or self.assessor_ids or self.facilitator_ids):
				raise ValidationError('Please select Moderator / Assessor / Facilitator')
			ref_id = self.env['inseta.provider'].search([('id', '=', self.reference)],limit=1)
			if ref_id:
				if self.action == "moderator":
					for res in self.moderator_ids:
						ref_id.update({'provider_moderator_ids': [(0, 0, 
							{
							'provider_id': ref_id.id,
							'moderator_id': res.id,
							'active': True,
							})]
						})
						ref_id.update({'moderator_ids': [(4, res.id)]})
				if self.action == "assessor":
					for res in self.assessor_ids:
						ref_id.update({'provider_assessor_ids': [(0, 0, 
							{
							'provider_id': ref_id.id,
							'assessor_id': res.id,
							'active': True,
							})]
						})
						ref_id.update({'assessor_ids': [(4, res.id)]})

				if self.action == "facilitator":
					for res in self.facilitator_ids:
						ref_id.update({'facilitator_ids': [(4, res.id)]})
			return{'type': 'ir.actions.act_window_close'}
		else:
			raise ValidationError('Select other action!!!')
