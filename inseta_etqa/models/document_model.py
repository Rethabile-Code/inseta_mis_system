


from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class LearnerDocumentModel(models.Model):
	_name = 'inseta.learner.document'
	_description = 'Learner Document' 

	lpro_id = fields.Integer()
	attachment_id = fields.Many2one('ir.attachment', string="Document", store=True)
	learner_document_id = fields.Many2one('inseta.learner.register', string="Learner Register Id")
	learner_document2_id = fields.Many2one('inseta.learner', string="Learner Name")
	programme_register_document_id = fields.Many2one('inseta.programme.register', string="Programme register id", store=True)
	data_name = fields.Char(string='File Name')
	state = fields.Char(string='State', compute="_get_parent_state")
	original_file_name = fields.Char(string='Original File name')
	file_path = fields.Char(string='File path')
	save_file_name = fields.Char(string='Save File name')
	datas = fields.Binary(string='File Content (base64)')
	financial_year_id = fields.Many2one('res.financial.year', required=False, store=True)

	compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], string="Evidence Compliance / Submitted", default="no", store=True)
	name = fields.Selection([('Learnership Agreement', 'Learnership Agreement'),('Certified ID copy', 'Certified ID copy'),
	('Confirmation of Employment', 'Confirmation of Employment'),('Certified copy of matric/ Qualification', 'Certified copy of matric/ Qualification'),
	# Confirmation of Employment
	('contract of employment', 'Contract of Employment'),
	# Fixed term confirmation of employment
	('Fixed term contract of employment', 'Fixed Term Contract of Employment'),
	('POPI act consent', 'POPI act consent'),('Proof of Disability', 'Proof of Disability'),
	('Student Fee Account', 'Student Fee Account'),('Highest qualification', 'Highest qualification'),
	('Worker Programme Agreement', 'Worker Programme Agreement and  POPI Act Consent'),('Quotation', 'Quotation'),('Certified Copy of Qualification', 'Certified Copy of Qualification'),
	('Bursary for youth Agreement', 'Bursary for youth Agreement'),('Proof of Registration', 'Proof of Registration'),
	('Previous Academic year result', 'Previous Academic year result'),('Proof of Employment', 'Proof of Employment'),
	('Work Base Placement Learning Agreement (WBPLA)', 'Work Base Placement Learning Agreement (WBPLA)'),
	('POPIA consent form', 'POPIA consent form'),
	('Certified Learner ID copy', 'Certified Learner ID copy'),('Leaner N4-N6 SOR or Certificate', 'Leaner N4-N6 SOR or Certificate'),
	('Matric certificate', 'Matric certificate'),('MOA with the college', 'MOA with the college'),
	('Internship Agreement', 'Internship Agreement'),('Confirmation of Employment letter', 'Confirmation of Employment letter'),
	], store=True)
 
	qualification_id = fields.Many2one("inseta.qualification",string="Qualification ID", domain=lambda act: [('active', '=', True)])
	unit_standard_id = fields.Many2one("inseta.unit.standard", string="Unit Standard ID", domain=lambda act: [('active', '=', True)])
	skill_programme_id = fields.Many2one("inseta.skill.programme", string='Skills Programme ID', domain=lambda act: [('active', '=', True)])
	learner_programme_id = fields.Many2one("inseta.learner.programme", string='Learnership ID', domain=lambda act: [('active', '=', True)])
	code = fields.Char('SAQA Code')
	title = fields.Char('Title')

	learner_learnship_document_id = fields.Many2one("inseta.learner.learnership",string="Learnership document")
	learner_skill_document_id = fields.Many2one("inseta.skill.learnership",string="Skill document")
	learner_qualification_document_id = fields.Many2one("inseta.qualification.learnership",string="qualification document")
	learner_unit_standard_document_id = fields.Many2one("inseta.unit_standard.learnership",string="Unit standard document")
	learner_internship_document_id = fields.Many2one("inseta.internship.learnership",string="internship document")
	learner_wilvet_document_id = fields.Many2one("inseta.wiltvet.learnership",string="Wiltvet document")
	learner_candidacy_document_id = fields.Many2one("inseta.candidacy.learnership",string="Candidacy document")
	learner_bursary_document_id = fields.Many2one("inseta.bursary.learnership",string="Bursary document")

	@api.depends('lpro_id')
	def _get_parent_state(self):
		for rec in self:
			if rec.lpro_id:
				rec.state = self.env['inseta.lpro'].browse([rec.lpro_id]).state
			else:
				rec.state = False 

	@api.onchange('code')
	def add_programme_by_code(self):
		if self.code:
			qualification = self.env["inseta.qualification"].search([('saqa_id', '=', self.code)], limit=1)
			skill = self.env["inseta.skill.programme"].search([('programme_code', '=', self.code)], limit=1)
			unit_standard = self.env["inseta.unit.standard"].search([('code', '=', self.code)], limit=1)
			learner_id = self.env["inseta.learner.programme"].search([('programme_code', '=', self.code)], limit=1)
			
			if qualification:
				self.qualification_id = qualification.id
				self.title = qualification.name
			elif unit_standard:
				self.unit_standard_id = unit_standard.id
				self.title = unit_standard.name
			elif skill:
				self.skill_programme_id = skill.id
				self.title = skill.name
			elif learner_id:
				self.learner_programme_id = learner_id.id
				self.title = learner_id.name

			else:
				return {
					'warning': {
						'title': "Validation Error!",
						'message': f"Programme with SAQA Code does not exists"
					}
				}
				

class AssessmentDocumentModel(models.Model):
	_name = 'inseta.assessment.document'
	_description = 'Learner ETQA Assessment Document' 

	name = fields.Char(string="Name")
	data_file = fields.Binary(string="Upload File", required=False)
	filename = fields.Char("Filename")
	compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], string="Evidence Compliance / Submitted", default="no", store=True)
