# from dataclasses import field
from odoo import _, api,fields, models
from odoo import SUPERUSER_ID
from odoo.osv import expression

class InsetaMajorUnitGroup(models.Model):
	_name = 'res.ofo.majorgroup'
	_description = "Inseta Ofo major group"

	name = fields.Char('Name')
	code = fields.Char('Code')
	ofoyear = fields.Char()
	version_no = fields.Char()
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')

class InsetaInstitution(models.Model):
	_name = 'res.inseta.institution'
	_description = "Inseta Institution"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')


class InsetaHet(models.Model):
	_name = 'inseta.het'
	_description = "Inseta Highest education training"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')

class InsetaHet(models.Model):
	_name = 'inseta.het'
	_description = "Inseta Highest education training"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')

class InsetaFet(models.Model):
	_name = 'inseta.fet'
	_description = "Inseta Further education training"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')

class InsetaBursaryType(models.Model):
	_name = 'res.bursary.type'
	_description = "Inseta bursary type"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')

class InsetaInternshipType(models.Model):
	_name = 'res.internship.type'
	_description = "Inseta bursary type"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')


class InsetaEnrollmentStatusReason(models.Model):
	_name = 'res.enrollment.status'
	_description = "Enrollment status"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')
 

class Insetaplacementtype(models.Model):
	_name = 'res.placementtype'
	_description = "Placement type"

	name = fields.Char('Name')
	code = fields.Char('Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')


class InsetaSubMajorUnitGroup(models.Model):
	_name = 'res.ofo.submajorgroup'
	_description = "Inseta Ofo sub major group"
	_order = "id desc"

	name = fields.Char('Name')
	code = fields.Char('Code')
	major_group_id = fields.Many2one('res.ofo.majorgroup', 'Major group')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')
	ofoyear = fields.Char('OFO Year')


class InsetaOfoMinorGroup(models.Model):
	_name = 'res.ofo.minorgroup'
	_description = "Inseta OfO Minor group"
	_order = "id desc"

	name = fields.Char('Name')
	code = fields.Char('Code')
	sub_major_group_id = fields.Many2one('res.ofo.submajorgroup', 'Sub Major group')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')
	ofoyear = fields.Char('OFO Year')

class InsetaOfoOccupationUnitGroup(models.Model):
	_name = 'res.ofo.unitgroup'
	_description = "Inseta Ofo unitgroup"
	_order = "id desc"

	name = fields.Char('Name')
	code = fields.Char('Code')
	minor_group_id = fields.Many2one('res.ofo.minorgroup', 'Minor group')
	sub_major_group_id = fields.Many2one('res.ofo.submajorgroup', 'Sub Major group')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')
	ofoyear = fields.Char('OFO Year')


class InsetaOfoOccupation(models.Model):
	_name = 'res.ofo.occupation'
	_description = "Inseta Ofo occupation"
	_order = "id desc"

	name = fields.Char('Name')
	code = fields.Char('Code')
	unit_group_id = fields.Many2one('res.ofo.unitgroup', 'Unit Group')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')
	ofoyear = fields.Char('OFO Year')
	trade = fields.Char()
	green_occupation = fields.Char()
	green_skill = fields.Char()

	
	def name_get(self):
		arr = []
		for rec in self:
			#major_group  = rec.unit_group_id.sub_major_group_id.major_group_id
			# ofoyear = major_group and major_group.ofoyear or False
			# if ofoyear:
			# 	name = f"{ofoyear}-{rec.code} - {rec.name}"
			# else:
			name = f"{rec.code} - {rec.name}"
			arr.append((rec.id, name))
		return arr
		
	@api.model
	def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
		args = list(args or [])
		# optimize out the default criterion of ``ilike ''`` that matches everything
		if not (name == '' and operator == 'ilike'):
			args += ['|', (self._rec_name, operator, name), ('code', operator, name)]
		return self._search(args, limit=limit, access_rights_uid=name_get_uid)

class ResOfoSpecialization(models.Model):
	_name = 'res.ofo.specialization'
	_description = "Inseta Ofo Specialization"
	_order = "id desc"

	name = fields.Char('Name')
	code = fields.Char('Code')
	occupation_id = fields.Many2one('res.ofo.occupation', 'Occupation')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')
	ofoyear = fields.Char('OFO Year')

	def name_get(self):
		arr = []
		for rec in self:
			major_group  = rec.occupation_id.unit_group_id.sub_major_group_id.major_group_id
			ofoyear = major_group and major_group.ofoyear or False
			name = f"{rec.code} - {rec.name}"
			arr.append((rec.id, name))
		return arr

	@api.model
	def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
		args = list(args or [])
		# optimize out the default criterion of ``ilike ''`` that matches everything
		if not (name == '' and operator == 'ilike'):
			args += ['|', (self._rec_name, operator, name), ('code', operator, name)]
		return self._search(args, limit=limit, access_rights_uid=name_get_uid)

class InsetaNqflevel(models.Model):
	_name = 'res.nqflevel'
	_description = "Inseta NQFLEVEL"

	name = fields.Char('Name')
	saqacode = fields.Char('SAQA Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')


class InsetaSaqaQualification(models.Model):
	_name = 'inseta.saqa.qualification'
	_description = "Inseta SAQA"

	name = fields.Char('Name')
	code = fields.Char('SAQA CODE')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')

class ResPersonType(models.Model):
	_name = "res.person.type"
	_description = "Person Type"
	'''To be used to accomodate assessors, moderators, learners type'''

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResProviderType(models.Model):
	_name = "res.provider.type"
	_description = "-"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResProviderDocument(models.Model):
	_name = "inseta.provider.document"
	_description = "-"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResProviderCategory(models.Model):
	_name = "res.provider.category"
	_description = "-"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResProviderClass(models.Model):
	_name = "res.provider.class"
	_description = "-"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResSataAreaCode(models.Model):
	_name = "res.sataarea.code"
	_description = "-"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResNsdsTarget(models.Model):
	_name = "res.nsds.target"
	_description = "-"

	name = fields.Char('Description', required=False)
	code = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResDginternshipscarcecritical(models.Model):
    _name = "res.dginternshipscarcecritical"
    _description ="DG internship scarcecritical"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')


 