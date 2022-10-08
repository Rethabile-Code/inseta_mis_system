from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

class InsetaProgrammesType(models.Model):
	_name = 'inseta.programme.type'
	_description = "Inseta Programme type"

	name = fields.Char('Name')
	active = fields.Boolean('Active', default=True)
	code = fields.Char('SAQA Code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	is_type = fields.Selection([ 
	('skills', 'Skills Programme'),
	('qualification', 'Qualification Programme'),
	('unit', 'Unit standard'),
	('learnership', 'Learnership Programme'),
	('internship', 'Internship Programme'),
	('bursary', 'Bursary Programme'),
	('wiltvet', 'WilTvet Programme'),
	('candidacy', 'Candidacy Programme'),
	('standalone', 'Standalone'),
	('others', 'Others')], string="Type")

  
class InsetaProgrammes(models.Model):
	_name = 'inseta.programme'
	_description = "Inseta Programme"  

	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type')

	active = fields.Boolean('Active', default=True)
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False) 
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	active = fields.Boolean(string='Active', default=True)


class InsetaSkillProgrammesType(models.Model):
	_name = 'inseta.skill.programme.type'
	_description = "Inseta Programme type"

	name = fields.Char('Name')
	active = fields.Boolean('Active', default=True)
	code = fields.Char('SAQA Code')
	legacy_system_id = fields.Integer(string='Legacy System ID')

class InsetaQualificationProgrammesType(models.Model):
	_name = 'inseta.qualification.programme.type'
	_description = "Inseta ualification Programme type"

	name = fields.Char('Name')
	active = fields.Boolean('Active', default=True)
	code = fields.Char('SAQA Code')
	legacy_system_id = fields.Integer(string='Legacy System ID')

class InsetaLearningProgrammesType(models.Model):
	_name = 'inseta.learning.programme.type'
	_description = "Inseta ualification Programme type"

	name = fields.Char('Name')
	active = fields.Boolean('Active', default=True)
	code = fields.Char('SAQA Code')
	legacy_system_id = fields.Integer(string='Legacy System ID')

class InsetaSkillProgrammes(models.Model):
	_name = 'inseta.skill.programme'
	_description = "Inseta Skill Programme"

	def name_get(self):
		arr = []
		for rec in self:
			programme_name = rec.name.title() if rec.name else rec.name 
			name = "[{}] {}".format(rec.programme_code, programme_name)
			arr.append((rec.id, name))
		return arr

	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	skill_unit_standard_ids = fields.One2many("inseta.skill.unit.standard", 'skill_programme_id', string='Skills Unit standards')
	# skill_unit_standard_ids = fields.Many2many("inseta.skill.unit.standard", 'inseta_skill_unit_standards_rel', 'inseta_skill_unit_standards_id', string='Skills Unit standards')
	skill_programme_type_id = fields.Many2one('inseta.skill.programme.type', string='Skills Programme type')
	# , default=lambda self: self.env.ref('inseta_etqa.inseta_skill_programme_type_01').id)
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'skills')], limit=1))
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False, compute="compute_total_credits") 
	minimum_credits = fields.Integer('Minimum Credits', default=False) 
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	active = fields.Boolean(string='Active', default=True)

	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_skill_programme_unit_standard_rel', 'inseta_skill_programme_unit_standard_id', 
	string='Unit standards')

	qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
	is_unit_base = fields.Char(default=False, compute="_compute_unit_base")
	is_south_african_programme = fields.Boolean('South Africa Programme')
	elective_credits = fields.Integer('Elective Credits', compute="compute_credits")
	core_credits = fields.Integer('Core Credits', default=False, compute="compute_credits")
	fundamental_credits = fields.Integer('Fundamental Credits', default=False, compute="compute_credits")

	@api.onchange('minimum_credits')
	def _onchange_mminimum_credits(self):
		for rec in self:
			if self.minimum_credits > 0 and self.minimum_credits > self.credits:
				raise ValidationError("Minimum credit should not be greater than total credits")

	@api.depends('qualification_type_id')
	def _compute_unit_base(self):
		for rec in self:
			if rec.qualification_type_id:
				if rec.qualification_type_id.name.startswith('Unit'):
					rec.is_unit_base = 'Yes'
					# rec.update({'is_unit_base': True})
				else:
					rec.is_unit_base = 'No'
			else:
				rec.is_unit_base = False

	# @api.onchange('qualification_id')
	# def get_qualification_unit_standards(self):
	# 	if self.qualification_id:
	# 		unit_standards = self.qualification_id.mapped('unit_standard_ids')
	# 		return {
	# 			'domain': {
	# 				'unit_standard_ids': [('id', 'in', [rec.id for rec in unit_standards])]
	# 				}
	# 		}
			
	@api.constrains('skill_unit_standard_ids')
	def _check_unit_standard(self):
		if self.programme_code != 0:
			programme_duplicate = self.env['inseta.skill.programme'].search([('programme_code', '=', self.programme_code)])
			if len(programme_duplicate) > 1:
				raise ValidationError('Please no duplicate programme code is allowed')
		if self.qualification_type_id:
			if self.qualification_type_id.name.startswith('Unit') and not self.skill_unit_standard_ids:
				raise ValidationError('Please ensure you provide unit standards for unit based qualifications')

		if self.programme_type_id.is_type in ['standalone', 'qualification', 'unit'] and not self.skill_unit_standard_ids:
			raise ValidationError('Please ensure you provide Skills unit standards for unit based qualifications')

	@api.onchange('registration_end_date')
	def _onchange_end_date(self):
		end_date = self.registration_end_date
		if self.registration_end_date:
			if self.registration_start_date:
				if self.registration_end_date < self.registration_start_date:
					self.registration_end_date = False
					return {
						'warning': {
							'title': "Validation Error!",
							'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
						}
					}
			else:
				self.registration_end_date = False
				return {
						'warning': {
							'title': "Validation Error!",
							'message': f"Start date  must be selected first"
						}
					}

			if self.registration_end_date >= fields.Date.today():
				self.active = True
			else:
				self.active = False

	@api.depends('core_credits', 'elective_credits', 'fundamental_credits')
	def compute_total_credits(self):
		for rec in self:
			if rec.core_credits and rec.elective_credits and rec.fundamental_credits:
				rec.credits = rec.core_credits + rec.elective_credits + rec.fundamental_credits
			else:
				rec.credits = False

	@api.depends('skill_unit_standard_ids')
	def compute_credits(self):
		for rec in self:
			if rec.skill_unit_standard_ids:
				core = rec.mapped('skill_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['core', 'Core'])
				elective = rec.mapped('skill_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['elective', 'Elective'])
				fundamental = rec.mapped('skill_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['fundamental', 'Fundamental'])
				rec.core_credits = sum([core.unit_standard_id.credits for core in core])
				rec.elective_credits = sum([elective.unit_standard_id.credits for elective in elective])
				rec.fundamental_credits = sum([fundamental.unit_standard_id.credits for fundamental in fundamental])
			else:
				rec.core_credits = False
				rec.elective_credits = False
				rec.fundamental_credits = False

				
class InsetaLearnerProgrammes(models.Model): # learnership.csv
	_name = 'inseta.learner.programme' 
	_description = "Inseta learnership programme"

	def name_get(self):
		arr = []
		for rec in self:
			programme_name = rec.name.title() if rec.name else rec.name 
			name = "[{}] {}".format(rec.programme_code, programme_name)
			arr.append((rec.id, name))
		return arr

	name = fields.Char('Name')
	learnership_unit_standard_ids = fields.One2many("inseta.learnership.unit.standard", 'learner_programme_id', string='Learnership Unit standards')
	# learnership_unit_standard_ids = fields.Many2many("inseta.learnership.unit.standard", 'inseta_learnership_unit_standards_rel', 'inseta_learnership_unit_standards_id', string='Learnership Unit standards')
	programme_code = fields.Char('Programme code')
	learnership_saqa_id = fields.Char('learnership saqa id')
	learner_programme_type_id = fields.Many2one('inseta.learning.programme.type', string='learning Programme type')
	# , default=lambda self: self.env.ref('inseta_etqa.inseta_learning_programme_type_A').id)
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'learnership')], limit=1))
	active = fields.Boolean('Active', default=True)
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False, compute="compute_credits") 
	minimum_credits = fields.Integer('Minimum Credits', default=False) 
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_learner_programme_unit_standard_rel', 'inseta_learner_programme_unit_standard_id', 
	string='Unit standards') # , domain=lambda self: self.get_qualification_unit_standards())
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	active = fields.Boolean(string='Active', default=True)
	qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
	is_unit_base = fields.Char(default=False, compute="_compute_unit_base")
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	is_south_african_programme = fields.Boolean('South Africa Programme')
	elective_credits = fields.Integer('Elective Credits', compute="compute_credits")
	core_credits = fields.Integer('Core Credits', default=False, compute="compute_credits")
	fundamental_credits = fields.Integer('Fundamental Credits', default=False, compute="compute_credits")

	@api.onchange('minimum_credits')
	def _onchange_minimum_credits(self):
		for rec in self:
			if self.minimum_credits > 0 and self.minimum_credits > self.credits:
				raise ValidationError("Minimum credit should not be greater than total credits")

	@api.depends('qualification_type_id')
	def _compute_unit_base(self):
		for rec in self:
			if rec.qualification_type_id:
				if rec.qualification_type_id.name.startswith('Unit'):
					rec.is_unit_base = 'Yes'
					# rec.update({'is_unit_base': True})
				else:
					rec.is_unit_base = 'No'
			else:
				rec.is_unit_base = False

	@api.depends('core_credits', 'elective_credits', 'fundamental_credits')
	def compute_total_credits(self):
		for rec in self:
			if rec.core_credits and rec.elective_credits and rec.fundamental_credits:
				rec.credits = rec.core_credits + rec.elective_credits + rec.fundamental_credits
			else:
				rec.credits = False

	@api.constrains('programme_code', 'learnership_unit_standard_ids')
	def _check_unit_standard(self):
		if self.programme_code != 0:
			programme_duplicate = self.env['inseta.learner.programme'].search([('programme_code', '=', self.programme_code)])
			if len(programme_duplicate) > 1:
				raise ValidationError('Please no duplicate programme code is allowed')
		if self.qualification_type_id:
			if self.qualification_type_id.name.startswith('Unit') and not self.learnership_unit_standard_ids:
				raise ValidationError('Please ensure you provide learnership unit standards for unit based qualifications')

	@api.onchange('registration_end_date')
	def _onchange_end_date(self):
		end_date = self.registration_end_date
		if self.registration_end_date:
			if self.registration_start_date:
				if self.registration_end_date < self.registration_start_date:
					self.registration_end_date = False
					return {
						'warning': {
							'title': "Validation Error!",
							'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
						}
					}
			else:
				self.registration_end_date = False
				return {
						'warning': {
							'title': "Validation Error!",
							'message': f"Start date  must be selected first"
						}
					}

			if self.registration_end_date >= fields.Date.today():
				self.active = True
			else:
				self.active = False

	@api.depends('learnership_unit_standard_ids')
	def compute_credits(self):
		for rec in self:
			if rec.learnership_unit_standard_ids:
				core = rec.mapped('learnership_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['core', 'Core'])
				elective = rec.mapped('learnership_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['elective', 'Elective'])
				fundamental = rec.mapped('learnership_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['fundamental', 'Fundamental'])
				rec.core_credits = sum([core.unit_standard_id.credits for core in core])
				rec.elective_credits = sum([elective.unit_standard_id.credits for elective in elective])
				rec.fundamental_credits = sum([fundamental.unit_standard_id.credits for fundamental in fundamental])
				rec.credits = sum([core.unit_standard_id.credits for core in core]) + sum([elective.unit_standard_id.credits for elective in elective]) + \
				 sum([fundamental.unit_standard_id.credits for fundamental in fundamental])

			else:
				rec.core_credits = False
				rec.elective_credits = False
				rec.fundamental_credits = False
				rec.credits = False
				

class InternshipProgramme(models.Model):
	_name = "inseta.internship.programme"
	_description = "internship Programme"

	def name_get(self):
		arr = []
		for rec in self:
			programme_name = rec.name.title() if rec.name else rec.name 
			name = "[{}] {}".format(rec.programme_code, programme_name)
			arr.append((rec.id, name))
		return arr

	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'internship')], limit=1))
	active = fields.Boolean('Active', default=True)
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False) #, compute="compute_total_credits") 
	minimum_credits = fields.Integer('Minimum Credits', default=False) 
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	active = fields.Boolean(string='Active', default=True)
	qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
	is_unit_base = fields.Char(default=False, compute="_compute_unit_base")
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	highest_edu_level_id = fields.Many2one(
		'res.education.level', string='Highest Level Of Education')
	highest_edu_desc = fields.Text('Highest Education Description')
	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_internship_programme_unit_standard_rel', 'inseta_internship_programme_unit_standard_id', string='Unit standards')
	is_south_african_programme = fields.Boolean('South Africa Programme')

	@api.depends('qualification_type_id')
	def _compute_unit_base(self):
		for rec in self:
			if rec.qualification_type_id:
				if rec.qualification_type_id.name.startswith('Unit'):
					rec.is_unit_base = 'Yes'
					# rec.update({'is_unit_base': True})
				else:
					rec.is_unit_base = 'No'
			else:
				rec.is_unit_base = False

	@api.onchange('registration_end_date')
	def _onchange_end_date(self):
		end_date = self.registration_end_date
		if self.registration_end_date:
			if self.registration_start_date:
				if self.registration_end_date < self.registration_start_date:
					self.registration_end_date = False
					return {
						'warning': {
							'title': "Validation Error!",
							'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
						}
					}
			else:
				self.registration_end_date = False
				return {
						'warning': {
							'title': "Validation Error!",
							'message': f"Start date  must be selected first"
						}
					}

			if self.registration_end_date >= fields.Date.today():
				self.active = True
			else:
				self.active = False

	# @api.onchange('unit_standard_ids')
	# def compute_total_credits(self):
	# 	for rec in self:
	# 		rec.credits = sum([rec.credits for rec in self.unit_standard_ids])


class IVETProgramme(models.Model):
	_name = "inseta.wiltvet.programme"
	_description = "Wiltvet Programme"

	def name_get(self):
		arr = []
		for rec in self:
			programme_name = rec.name.title() if rec.name else rec.name 
			name = "[{}] {}".format(rec.programme_code, programme_name)
			arr.append((rec.id, name))
		return arr

	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'wiltvet')], limit=1))
	active = fields.Boolean('Active', default=True)
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False) #, compute="compute_total_credits") 
	minimum_credits = fields.Integer('Minimum Credits', default=False) 
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	active = fields.Boolean(string='Active', default=True)
	qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
	is_unit_base = fields.Char(default=False, compute="_compute_unit_base")
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_wiltvet_programme_unit_standard_rel', 'inseta_wiltvet_programme_unit_standard_id', string='Unit standards')
	is_south_african_programme = fields.Boolean('South Africa Programme')
	
	@api.depends('qualification_type_id')
	def _compute_unit_base(self):
		for rec in self:
			if rec.qualification_type_id:
				if rec.qualification_type_id.name.startswith('Unit'):
					rec.is_unit_base = 'Yes'
					# rec.update({'is_unit_base': True})
				else:
					rec.is_unit_base = 'No'
			else:
				rec.is_unit_base = False

	@api.onchange('registration_end_date')
	def _onchange_end_date(self):
		end_date = self.registration_end_date
		if self.registration_end_date:
			if self.registration_start_date:
				if self.registration_end_date < self.registration_start_date:
					self.registration_end_date = False
					return {
						'warning': {
							'title': "Validation Error!",
							'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
						}
					}
			else:
				self.registration_end_date = False
				return {
						'warning': {
							'title': "Validation Error!",
							'message': f"Start date  must be selected first"
						}
					}

			if self.registration_end_date >= fields.Date.today():
				self.active = True
			else:
				self.active = False

	# @api.onchange('unit_standard_ids')
	# def compute_total_credits(self):
	# 	for rec in self:
	# 		rec.credits = sum([rec.credits for rec in self.unit_standard_ids])


class InsetaBusaryProgramme(models.Model):
	_name = "inseta.bursary.programme"
	_description = "bursary Programme"

	def name_get(self):
		arr = []
		for rec in self:
			programme_name = rec.name.title() if rec.name else rec.name 
			name = "[{}] {}".format(rec.programme_code, programme_name)
			arr.append((rec.id, name))
		return arr

	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'bursary')], limit=1))
	active = fields.Boolean('Active', default=True)
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False) #, compute="compute_total_credits")
	minimum_credits = fields.Integer('Minimum Credits', default=False)  
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	active = fields.Boolean(string='Active', default=True)
	qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
	is_unit_base = fields.Char(default=False, compute="_compute_unit_base")
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	highest_edu_level_id = fields.Many2one(
		'res.education.level', string='Highest Level Of Education')
	highest_edu_desc = fields.Text('Highest Education Description')
	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_bursary_programme_unit_standard_rel', 'inseta_bursary_programme_unit_standard_id', string='Unit standards')
	is_south_african_programme = fields.Boolean('South Africa Programme')

	@api.depends('qualification_type_id')
	def _compute_unit_base(self):
		for rec in self:
			if rec.qualification_type_id:
				if rec.qualification_type_id.name.startswith('Unit'):
					rec.is_unit_base = 'Yes'
					# rec.update({'is_unit_base': True})
				else:
					rec.is_unit_base = 'No'
			else:
				rec.is_unit_base = False

	# @api.onchange('unit_standard_ids')
	# def compute_total_credits(self):
	# 	for rec in self:
	# 		rec.credits = sum([rec.credits for rec in self.unit_standard_ids])

	# @api.onchange('registration_start_date')
	# def _onchange_start_date(self):
	#     today = fields.Date.today()
	#     start_dt = self.start_date
	#     if self.start_date and self.start_date < today:
	#         self.start_date = False
	#         return {
	#             'warning': {
	#                 'title': "Validation Error!",
	#                 'message': f" The selected Start Date {start_dt} cannot be less than today"
	#             }
	#         }

	@api.onchange('registration_end_date')
	def _onchange_end_date(self):
		end_date = self.registration_end_date
		if self.registration_end_date:
			if self.registration_start_date:
				if self.registration_end_date < self.registration_start_date:
					self.registration_end_date = False
					return {
						'warning': {
							'title': "Validation Error!",
							'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
						}
					}
			else:
				self.registration_end_date = False
				return {
						'warning': {
							'title': "Validation Error!",
							'message': f"Start date  must be selected first"
						}
					}

			if self.registration_end_date >= fields.Date.today():
				self.active = True
			else:
				self.active = False

class InsetaCandidacyProgramme(models.Model):
	_name = "inseta.candidacy.programme"
	_description = "candidacy Programme"


	def name_get(self):
		arr = []
		for rec in self:
			programme_name = rec.name.title() if rec.name else rec.name 
			name = "[{}] {}".format(rec.programme_code, programme_name)
			arr.append((rec.id, name))
		return arr

	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type',  default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'candidacy')], limit=1))
	active = fields.Boolean('Active', default=True)
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False) #, compute="compute_total_credits")
	minimum_credits = fields.Integer('Minimum Credits', default=False)
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	active = fields.Boolean(string='Active', default=True)
	qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
	is_unit_base = fields.Char(default=False, compute="_compute_unit_base")
	highest_edu_level_id = fields.Many2one(
		'res.education.level', string='Highest Level Of Education')
	highest_edu_desc = fields.Text('Highest Education Description')
	unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_candidacy_programme_unit_standard_rel', 'inseta_candidacy_programme_unit_standard_id', string='Unit standards')
	is_south_african_programme = fields.Boolean('South Africa Programme')

	@api.depends('qualification_type_id')
	def _compute_unit_base(self):
		for rec in self:
			if rec.qualification_type_id:
				if rec.qualification_type_id.name.startswith('Unit'):
					rec.is_unit_base = 'Yes'
					# rec.update({'is_unit_base': True})
				else:
					rec.is_unit_base = 'No'
			else:
				rec.is_unit_base = False
				
	# @api.onchange('unit_standard_ids')
	# def compute_total_credits(self):
	# 	for rec in self:
	# 		rec.credits = sum([rec.credits for rec in self.unit_standard_ids])

	@api.onchange('registration_end_date')
	def _onchange_end_date(self):
		end_date = self.registration_end_date
		if self.registration_end_date:
			if self.registration_start_date:
				if self.registration_end_date < self.registration_start_date:
					self.registration_end_date = False
					return {
						'warning': {
							'title': "Validation Error!",
							'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
						}
					}
			else:
				self.registration_end_date = False
				return {
						'warning': {
							'title': "Validation Error!",
							'message': f"Start date  must be selected first"
						}
					}

			if self.registration_end_date >= fields.Date.today():
				self.active = True
			else:
				self.active = False

class InsetaQualificationProgrammes(models.Model):
	_name = 'inseta.qualification.programme'
	_description = "Inseta qualification programme"


	name = fields.Char('Name')
	programme_code = fields.Char('Programme code')
	programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type')
	qualification_id = fields.Many2one('inseta.qualification', 'Qualification ID', domain=lambda act: [('active', '=', True)])
	nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
	credits = fields.Integer('Credits', default=False)
	minimum_credits = fields.Integer('Minimum Credits', default=False)
	legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
	quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
	programme_unit_id = fields.Many2one('inseta.unit.standard', 'Unit standard')
	registration_start_date = fields.Date('Registration start date')
	registration_end_date = fields.Date('Registration end date')
	ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')
	active = fields.Boolean(string='Active', default=True)

	# @api.model 
	# def create(self, vals):
	# 	values = dict(
	# 		name = vals.get('name'),
	# 		programme_code = vals.get('programme_code'),
	# 		programme_type_id = vals.get('programme_type_id', False),
	# 		qualification_id = vals.get('qualification_id', False),
	# 		nqflevel_id = vals.get('nqflevel_id', False),
	# 		credits = vals.get('credits'),
	# 		legacy_system_id = vals.get('legacy_system_id'),
	# 		quality_assurance_id = vals.get('quality_assurance_id', False),
	# 		programme_unit_id = vals.get('programme_unit_id', False),
	# 		registration_start_date = vals.get('registration_start_date'),
	# 		registration_end_date = vals.get('registration_end_date'),
	# 		ofo_occupation_id = vals.get('ofo_occupation_id', False),
	# 		active = True
	# 	)
	# 	programme = self.env['inseta.programme']
		 
		# programme.create(vals)
		# res = super(InsetaQualificationProgrammes, self).create(vals)
		# return res


class InsetaProgrammeStatus(models.Model):
	_name = 'inseta.program.status'
	_description = "Inseta programme Status"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class InsetaVerificationStatus(models.Model):
	_name = 'inseta.verification.status'
	_description = "Inseta Verification Status"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')