from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError


class insetalLproRegisterLearnerWizard(models.Model):
	_name = 'inseta.lpro.register.learner.wizard'
	_description = "LPRO Register Learner"
	
	learner_ids = fields.One2many('inseta.learner.register', 'lpro_learner_wizard_id', string='Learners', required=False)
	inseta_learner_ids = fields.Many2many('inseta.learner', 'lpro_register_learner_wizard_rel', string="Learners", store=True)
	learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
	learner_register_id = fields.Many2one('inseta.learner.register', string='Register ID', required=False)
	document_ids = fields.Many2many("inseta.learner.document", "lpro_register_learner_document_wizard_rel", string="Inseta Learner document")
	reference = fields.Integer('Reference ID', default=False, readonly=True)
	action = fields.Selection([('register', 'New Register'),
	# ('upload', 'Add existing Learner'), # used to add existing learner but no to be used because inseta dont want it
	('upload_id', 'Use Identification No to Capture'),
	('doc_validity', 'Validation')], 
	string="Action", help="Action to perform")
	document_validation = fields.Boolean('Document Validity', store=False)
	compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], string="Evidence Compliance / Submitted", default="no", store=True)
	id_no = fields.Char('Learner ID No.', store=False)
	organisation_sdl = fields.Char(string='Employer SDL / N')
	state = fields.Char('State')
	dgtype_code = fields.Char('DG Type Code')
	dgtype_id = fields.Many2one('res.dgtype', 'DG Type', store=True)

	@api.onchange('compliant')
	def onchange_compliant(self):
		if self.compliant == "yes":
			for rec in self.document_ids:
				rec.compliant = "yes"
		else:
			for rec in self.document_ids:
				rec.compliant = "no"

	@api.onchange('reference')
	def display_learner(self):
		if self.reference:
			reference = self.env['inseta.lpro'].search([('id', '=', self.reference)], limit=1)
			loaded_learner = reference.mapped('inseta_learner_ids')
			ids = [rec.id for rec in loaded_learner] if loaded_learner else None
			domain = {
				'learner_id': [('id', '=', ids)]
			}
			return {'domain': domain }

	@api.onchange("id_no", "learner_id")
	def action_add_learner(self):
		reference = self.env['inseta.lpro'].search([('id', '=', self.reference)], limit=1)
		if not self.learner_register_id:
			if self.id_no:
				if self.document_validation:
					"""
						If document validation, check to see if the learner exists in the assessment learner line
					"""
					learner_ref = reference.mapped('inseta_learner_ids').filtered(lambda s: s.id_no == self.id_no)
					if not learner_ref:
						self.id_no = False 
						return {
								'warning': {
									'title': "Validation Error!",
									'message': f"Learner with ID No. does not exists on this LP application"
								}
							}
					else:
						self.learner_id = learner_ref.id

				elif not self.document_validation:
					learner_ref = self.env['inseta.learner'].search([('id_no', '=', self.id_no)], limit=1)
					if not learner_ref:
						self.id_no = False 
						return {
							'warning': {
								'title': "Validation Error!",
								'message': f"Learner with ID No. does not exists"
							}
						}
					else:
						self.id_no = False
						self.learner_id = learner_ref.id
						self.update({'inseta_learner_ids': [(4, learner_ref.id)]})
				else:
					self.get_programme_document_ids(learner_ref, reference)
					 
			if self.learner_id:
				learner_ref = self.env['inseta.learner'].search([('id', '=', self.learner_id.id)], limit=1)
				if not learner_ref:
					self.learner_id = False 
					return {
							'warning': {
								'title': "Validation Error!",
								'message': f"Learner with ID No. does not exists on this LP application"
							}
						}
				self.get_programme_document_ids(learner_ref, reference)
				# loaded_learner = reference.mapped('inseta_learner_ids').filtered(lambda s: s.id == self.learner_id.id) 
				# if loaded_learner:
				# 	self.document_ids = [(6, 0, [docs.id for docs in loaded_learner[0].mapped('document_ids').filtered(lambda s: s.financial_year_id.id == reference.financial_year_id.id)])]

		else:
			pass 
	
	def get_programme_document_ids(self, learner, reference):
		self.document_ids = False 
		if learner.learner_learnership_line:
			learner_lines = learner.mapped('learner_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]

		if learner.skill_learnership_line:
			learner_lines = learner.mapped('skill_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]

		if learner.qualification_learnership_line:
			learner_lines = learner.mapped('qualification_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]

		if learner.internship_learnership_line:
			learner_lines = learner.mapped('internship_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]
 
		if learner.bursary_learnership_line:
			learner_lines = learner.mapped('bursary_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]

		if learner.candidacy_learnership_line:
			learner_lines = learner.mapped('candidacy_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]

		if learner.wiltvet_learnership_line:
			learner_lines = learner.mapped('wiltvet_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]
		
		if learner.unit_standard_learnership_line:
			learner_lines = learner.mapped('unit_standard_learnership_line').filtered(lambda l: l.financial_year_id.id == reference.financial_year_id.id)
			for line in learner_lines:
				self.document_ids = [(4, doc.id) for doc in line.mapped('document_ids').filtered(lambda lpro: lpro.lpro_id == reference.id)]
		# Updates the state of the LP application to determine when to hide compliant fields
		for re_doc in self.document_ids:
			re_doc.state = reference.state
	
	def action_add_programme(self):
		view = self.env.ref('inseta_etqa.inseta_programme_register_learner_wizard_form_view')
		view_id = view and view.id or False
		context = {
					'default_learner_id': self.learner_id.id, 
					'default_learner_id_no': self.learner_id.id_no,
					'default_dgtype_code': self.dgtype_code,
					}
		return {'name':'Register Programme',
					'type':'ir.actions.act_window',
					'view_type':'form',
					'res_model':'inseta.programme.register',
					'views':[(view.id, 'form')],
					'view_id':view.id,
					'target':'new',
					'context':context,
				}

	def post_action(self):
		if not self.learner_register_id:
			reference = self.env['inseta.lpro'].search([('id', '=', self.reference)], limit=1)
			if not self.document_validation:
				for rex in self.learner_ids:
					self.inseta_learner_ids = [(4, rex.learner_id.id)]

				if reference:
					for lrn in self.inseta_learner_ids:
						reference.write({
							'inseta_learner_ids': [(4, lrn.id)]
						})
			else:
				 
				check_non_complaint = self.mapped('document_ids').filtered(lambda s:s.compliant == 'no')
				if check_non_complaint:
					pass # they want it to pass even without selecting yes
					# raise ValidationError('Please Set the compliant field to yes if all document is compliant.')
				else:
					self.compliant == 'yes'
					reference.compliant = 'yes'
		else:
			lreg = self.env['inseta.learner.register'].search([('id', '=', self.learner_register_id.id)], limit=1)
			lreg.compliant = "yes"
		return{'type': 'ir.actions.act_window_close'}


	
