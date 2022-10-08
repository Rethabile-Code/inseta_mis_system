
from odoo import fields, models ,api, _
from tempfile import TemporaryFile
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import base64
import copy
import io
import re
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta as rd
import xlrd
from xlrd import open_workbook
import csv
import base64
import sys
_logger = logging.getLogger(__name__)


class ImportLearnerRegisters(models.TransientModel):
	_name = 'inseta.etqa.data.import.wizard'
	_description  = "Import Wizard"

	file_type = fields.Selection(
		[('xlsx', 'XLSX File')], default='xlsx', string='File Type')
	file = fields.Binary(string="Upload File (.xlsx)")
	file_name = fields.Char("Filename")
	import_type = fields.Selection([
			('provider', 'Provider Migration'),
			('moderator', 'Moderator Migration'),
			('assessor', 'Assessor Migration'),
			('learner', 'Learner Migration'),
			('qualification_assurance', 'Qualification Assurance Migration'),
			('unit_standard', 'Unit standard Migration'),
			('qualification', 'Qualification Migration'),
			('skill_programme', 'Skill Programme Migration'),
			('skills_learnership', 'Skills LearnerShip Migration'),
			('programme_type', 'Programme type Migration'),
			('programme', 'Programme Migration'),
			('programme_unit_standard', 'Programme Unit standard Migration'),
			('learner_programme', 'LearnerShip Migration'), # dbo.learnership.csv
			# ('qualification_programme', 'Qualification Learnership Programme Migration'),
			('learner_learnership', 'Learner LearnerShip Migration'),
			('learner_learnership_assessment', 'Learner LearnerShip Assessment Migration'),
			('skill_learnership_assessment', 'Skills LearnerShip Assessment Migration'),
			('qualification_learnership', 'Qualification LearnerShip Migration'),
			('qualification_learnership_assessment', 'Qualification LearnerShip Assessment Migration')
		],
		string='Import Type', required=True, index=True,
		copy=True,
	) 

	def read_file(self, index=0):
		if not self.file:
			raise ValidationError('Please select a file')

		file_datas = base64.decodestring(self.file)
		workbook = open_workbook(file_contents=file_datas)
		sheet = workbook.sheet_by_index(index)
		file_data = [[sheet.cell_value(r, c) for c in range(
			sheet.ncols)] for r in range(sheet.nrows)]
		file_data.pop(0)
		return file_data
		
	def format_date(self, date_str):
		if date_str and date_str in [str]:
			date_split = date_str.split(' ')
			if date_split and len(date_split) > 2:
				year, month, day = date_split[0], date_split[1], date_split[2]
				if len(year) == 4 or len(month) == 2 or len(day) == 2:
					return f'{year}-{month}-{day}'
				else:
					return fields.Date.today()
			else:
				return fields.Date.today()

		else:
			return fields.Date.today()

	def _get_object_by_legacy_id(self, model, legacy_id, auto_create_legacy_id=False):
		if legacy_id: 
			if isinstance(legacy_id, int) or isinstance(legacy_id, float):
				_logger.info(f" Model: {model}, Legacy ID: {int(legacy_id)} ")
				obj = self.env[model].search([('legacy_system_id', '=', int(legacy_id))], limit=1)
				if not obj:
					if auto_create_legacy_id:
						obj = self.env[model].create({'legacy_system_id': int(legacy_id)})
				else:
					obj = obj
				return obj and int(obj.id) or False
		return False

	def action_import(self):
		file_data = self.read_file()
		if self.import_type in ["learner", "assessor", "moderator"]: # dbo.learner.xlsx, dbo.moderator, dbo.assessor.csv
			count = 0
			for count, row in enumerate(file_data):
				# if count > 60:
				# 	break
				legacy_sys_id = int(row[0])
				personid = int(row[1])
				partner = self.env['res.partner'].search([('legacy_system_id','=', personid)],limit=1) # TODO Change model to inseta.organization, then get the partner id 
				if partner:
					vals = dict(
					legacy_system_id=legacy_sys_id,  # legacy system ID
					title = partner.title.id,  # name
					partner_id = partner.id, # always add this not to duplicate in contacts
					first_name= partner.first_name,
					middle_name=partner.middle_name,
					last_name=partner.last_name,
					name =partner.name,
					birth_date = partner.birth_date,
					gender_id =partner.gender_id.id,
					equity_id = partner.equity_id.id,
					id_no = partner.id_no,
					disability_id = partner.disability_id.id,
					home_language_id = partner.home_language_id.id,
					nationality_id = partner.nationality_id.id,
					citizen_resident_status_id = partner.citizen_resident_status_id.id,
					socio_economic_status_id = partner.socio_economic_status_id.id,
					phone = partner.phone,
					mobile = partner.mobile,
					fax_number = partner.fax_number,
					email = partner.email,
					street = partner.street,
					street2 = partner.street2,
					street3 = partner.street3,
					physical_code = partner.first_name,
					physical_suburb_id = partner.physical_suburb_id.id,
					physical_city_id = partner.physical_city_id.id,
					physical_municipality_id = partner.physical_municipality_id.id,
					physical_urban_rural = partner.physical_urban_rural,
					physical_province_id = partner.physical_province_id.id,  
					postal_address1 = partner.postal_address1,
					postal_address2 = partner.postal_address2,
					postal_address3 =partner.postal_address3,
					postal_code = partner.postal_code,
					postal_suburb_id = partner.postal_suburb_id.id,
					postal_city_id = partner.postal_city_id.id,
					postal_municipality_id = partner.postal_municipality_id.id,
					postal_urban_rural = partner.postal_urban_rural,
					postal_province_id =  partner.postal_province_id.id,
					popi_act_status_id = partner.popi_act_status_id.id,
					popi_act_status_date = partner.popi_act_status_date,
					statssa_area_code_id = partner.statssa_area_code_id.id,
					school_emis_id = partner.school_emis_id.id,
					school_year = partner.school_year,
					user_id = partner.user_id.id,


					)
					if self.import_type == 'learner': 
						search_existing_record = self.env['inseta.learner'].search([('legacy_system_id', '=', legacy_sys_id)], limit=1)
						if not search_existing_record:
							self.env['inseta.learner'].create(vals)
					elif self.import_type == 'assessor':
						vals['etdp_registration_number'] = row[2] 
						vals['person_type_id'] = self._get_object_by_legacy_id('res.person.type', row[3], True)
						vals['start_date'] = row[4].split(" ")[0] if row[4] else False
						vals['end_date'] = row[5].split(" ")[0] if row[5] else False
						vals['registration_number'] = row[7]
						vals['statement_number'] = row[9]
						vals['statement_date'] = row[11].split(" ")[0] if row[11] else False
						self.env['inseta.assessor'].create(vals) 
					elif self.import_type == 'moderator':
						vals['etdp_registration_number'] = row[2] 
						vals['person_type_id'] = self._get_object_by_legacy_id('res.person.type', row[3], True)
						vals['start_date'] = row[4].split(" ")[0] if row[4] else False
						vals['end_date'] = row[5].split(" ")[0] if row[5] else False
						vals['registration_number'] = row[7]
						vals['statement_number'] = row[9]
						vals['statement_date'] = row[11].split(" ")[0] if row[11] else False
						search_existing_record = self.env['inseta.moderator'].search([('legacy_system_id', '=', legacy_sys_id)], limit=1)
						if not search_existing_record:
							self.env['inseta.moderator'].create(vals)

					elif self.import_type == 'provider':
						vals['provider_type_id'] = self._get_object_by_legacy_id('res.provider.type', row[2], True)
						vals['provider_class_id'] = self._get_object_by_legacy_id('res.provider.class', row[3], True)
						vals['organisation_id'] =  self._get_object_by_legacy_id('inseta.organisation', row[1])
						vals['start_date'] = row[5].split(" ")[0] if row[5] else False
						vals['end_date'] = row[6].split(" ")[0] if row[6] else False
						vals['provider_accreditation_number'] = row[7]
						vals['certificate_number'] = row[16]
						vals['saqa_id'] = int(row[9]) if row[9] else False # self._get_object_by_legacy_id('inseta.saqa.qualification', row[9], True)
						vals['saqa_provider_code'] = row[10]
						vals['certificate_date'] = row[18].split(" ")[0] if row[18] else False
						vals['approval_date'] = row[18].split(" ")[0] if row[18] else False
						vals['is_rpl'] = row[24] if row[24] == 1 else False
						vals['islearning'] = row[25] if row[25] == 1 else False
						vals['ismixed_model_learning'] = row[26] if row[26] == 1 else False
						vals['is_learnerships'] = row[27] if row[27] == 1 else False
						vals['is_facilitated_distance'] = row[28] if row[28] == 1 else False
						vals['is_facilitated_contact_delivery'] = row[29] if row[29] == 1 else False
						search_existing_record = self.env['inseta.provider'].search([('legacy_system_id', '=', legacy_sys_id)], limit=1)
						if not search_existing_record:
							self.env['inseta.provider'].create(vals)
				# count += 1
		if self.import_type == "qualification_assurance": # 
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				obj = self._get_object_by_legacy_id('inseta.quality.assurance', legacy_sys_id, False)
				vals = dict(
					legacy_system_id=legacy_sys_id,  # legacy system ID
					name=row[1],
					code=row[2],
					)
				if not obj:
					self.env['inseta.quality.assurance'].create(vals)
				else:
					self.env['inseta.quality.assurance'].write(vals)

		if self.import_type == 'unit_standard':
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				is_replaced = True if row[9] == 1 else False 
				quality_id = self.env['inseta.quality.assurance'].search([('legacy_system_id','=', row[22])], limit=1)
				replace_unit_standard_id = False 
				if row[10]:
					replace_unit_standard_id = self.env['inseta.unit.standard'].search([('legacy_system_id', '=', row[10])], limit=1)

				vals = dict(
				legacy_system_id=legacy_sys_id,  # legacy system ID
				quality_assurance_id = quality_id.id if quality_id else False,
				name=row[2],
				saqa_id = row[1],
				credits=row[4],
				nqflevel_id = self._get_object_by_legacy_id('res.nqflevel', row[3], False),
				registration_start_date = row[5].split(" ")[0] if row[5] else False,
				registration_end_date = row[6].split(" ")[0] if row[6] else False,
				last_enroll_date = row[7].split(" ")[0] if row[7] else False,
				last_achievement_date = row[8].split(" ")[0] if row[8] else False,
				is_replaced = is_replaced,
				# replaced_unit_standard = replace_unit_standard_id.id if replace_unit_standard_id else False,
				is_registered = True if row[11] == 1 else False,
				new_registration_start_date = row[12].split(" ")[0] if row[12] else False,
				new_registration_end_date = row[13].split(" ")[0] if row[13] else False,
				new_last_enroll_date = row[14].split(" ")[0] if row[14] else False,
				new_last_achievement_date = row[15].split(" ")[0] if row[15] else False,
				)
				self.env['inseta.unit.standard'].create(vals)

		if self.import_type == "qualification": # dbo.qualication.csv
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				is_replaced = True if row[11] == 1 else False 

				saqa_qualification = self.env['inseta.saqa.qualification'].search([('name','=', row[1])], limit=1)
				if not saqa_qualification:
					saqa_qualification = self.env['inseta.saqa.qualification'].create({'name': row[1]})
				nqflevel_id = self.env['res.nqflevel'].search([('legacy_system_id','=', int(row[3]) or False)], limit=1)
				replaced_qualification = False 
				if row[12]:
					replaced_qualification = self.env['inseta.qualification'].search([('legacy_system_id', '=', int(row[12]))], limit=1)
				quality_assurance_id = self.env['inseta.quality.assurance'].search([('legacy_system_id','=', row[9])], limit=1)

				vals = dict(
				legacy_system_id=legacy_sys_id,  # legacy system ID
				# saqa_qualification_id = saqa_qualification.id,  # name
				saqa_id=row[1],
				name=row[2],
				nqflevel_id=nqflevel_id.id if nqflevel_id else False,
				credits=row[4],
				quality_assurance_id = quality_assurance_id.id,
				registration_start_date = row[5].split(" ")[0] if row[5] else False,
				registration_end_date = row[6].split(" ")[0] if row[6] else False,
				last_enroll_date = row[7].split(" ")[0] if row[7] else False,
				last_achievement_date = row[8].split(" ")[0] if row[8] else False,
				qualification_type_id = row[10] if row[10] else False,
				is_replaced = is_replaced, 
				replaced_qualification_id = replaced_qualification.id if replaced_qualification else False,
				is_registered = True if row[13] == 1 else False,
				new_registration_start_date = row[14].split(" ")[0] if row[14] else False,
				new_registration_end_date = row[15].split(" ")[0] if row[15] else False,
				new_last_enroll_date = row[16].split(" ")[0] if row[16] else False,
				new_last_achievement_date = row[17].split(" ")[0] if row[17] else False,
				core_credits = row[25],
				fundamental_credits = row[26],
				elective_credits = row[27]
				)
				search_existing_record = self.env['inseta.qualification'].search([('legacy_system_id', '=', legacy_sys_id)], limit=1)
				if not search_existing_record:
					self.env['inseta.qualification'].create(vals)

		if self.import_type == "programme_type": # dbo.lkplearningprogrammetype.csv
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				obj = self._get_object_by_legacy_id('inseta.programme.type', legacy_sys_id, False)
				if not obj:
					vals = dict(
					legacy_system_id=legacy_sys_id,  # legacy system ID
					name=row[1],
					# code=row[2],
					)
					self.env['inseta.programme.type'].create(vals)
				else:
					self.env['inseta.programme.type'].write(vals)

		if self.import_type == "programme": # dbo.skillsprogramme.csv
			for count, row in enumerate(file_data):
				legacy_system_id = int(row[0])
				nqflevel_id = self.env['res.nqflevel'].search([('legacy_system_id','=', int(row[3]) or False)], limit=1)
				quality_assurance_id = self.env['inseta.quality.assurance'].search([('legacy_system_id','=', int(row[7]) or False)], limit=1)
				programme_type_id = self.env['inseta.programme.type'].search([('legacy_system_id','=', row[8])], limit=1)
				qualification_id = self.env['inseta.qualification'].search([('legacy_system_id','=', int(row[9]) or False)], limit=1)
				vals = dict(
				legacy_system_id=legacy_system_id,  # legacy system ID
				programme_code = row[1],  # name
				name=row[2],
				nqflevel_id=nqflevel_id.id,
				credits=row[4],
				quality_assurance_id = quality_assurance_id.id,
				programme_type_id = programme_type_id.id,
				qualification_id = qualification_id.id,
				)
				search_existing_record = self.env['inseta.skill.programme'].search([('legacy_system_id', '=', legacy_system_id)], limit=1)
				if not search_existing_record:
					self.env['inseta.skill.programme'].create(vals)
 
		if self.import_type == "programme_unit_standard": # dbo.skillsprogrammeunitstandard.csv
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				programmes = self.env['inseta.skill.programme'].search([('legacy_system_id','=', row[1])], limit=1)
				unit_standard_id = self.env['inseta.unit.standard'].search([('legacy_system_id','=', int(row[2]) or False)], limit=1)
				programmes.write({'programme_unit_id': unit_standard_id.id})


		if self.import_type == 'learner_programme': # dbo.learnership.csv
			for count, row in enumerate(file_data):

				legacy_system_id = int(row[0])
				programme_code = row[1]
				name = row[2]
				programme_type_id = self.env['inseta.programme.type'].search([('legacy_system_id','=', int(row[3]))], limit=1)
				qualification_id = self.env['inseta.qualification'].search([('legacy_system_id','=', int(row[4]) or False)], limit=1)
				nqflevel_id = self.env['res.nqflevel'].search([('legacy_system_id','=', int(row[5]) or False)], limit=1)
				credits = row[6]
				quality_assurance_id = self.env['inseta.quality.assurance'].search([('legacy_system_id','=', row[7])], limit=1)
				ofo_occupation_id = self.env['res.ofo.occupation'].search([('legacy_system_id','=', int(row[8]))], limit=1)
				vals = dict(
				legacy_system_id=legacy_system_id,  # legacy system ID
				programme_code = programme_code,
				quality_assurance_id = quality_assurance_id.id or row[7],
				qualification_id = qualification_id.id,
				name=name,
				credits=credits,
				nqflevel_id = self._get_object_by_legacy_id('res.nqflevel', row[5], False),
				registration_start_date = row[9].split(" ")[0] if row[9] else False,
				registration_end_date = row[10].split(" ")[0] if row[10] else False,
				ofo_occupation_id= ofo_occupation_id.id
				)
				search_existing_record = self.env['inseta.learner.programme'].search([('legacy_system_id', '=', legacy_system_id)], limit=1)
				if not search_existing_record:
					learner_programme = self.env['inseta.learner.programme'].create(vals)

		if self.import_type == 'skill_programme': # dbo.skillprogramme.csv
			for count, row in enumerate(file_data):

				legacy_system_id = int(row[0]) if row[0] else False
				programme_code = row[1]
				name = row[2]
				nqflevel_id = self.env['res.nqflevel'].search([('legacy_system_id','=', row[3])], limit=1)
				credits = row[4]
				quality_assurance_id = self.env['inseta.quality.assurance'].search([('legacy_system_id','=', row[7])], limit=1)
				programme_type_id = self.env['inseta.programme.type'].search([('legacy_system_id','=', row[8])], limit=1)
				qualification_id = self.env['inseta.qualification'].search([('legacy_system_id','=', row[9])], limit=1)
				ofo_occupation_id = self.env['res.ofo.occupation'].search([('legacy_system_id','=', row[10])], limit=1)
				vals = dict(
				legacy_system_id=legacy_system_id,  # legacy system ID
				programme_code = programme_code,
				quality_assurance_id = quality_assurance_id.id if quality_assurance_id else False,
				qualification_id = qualification_id.id,
				name=name,
				credits=credits,
				nqflevel_id = self._get_object_by_legacy_id('res.nqflevel', row[5], False),
				registration_start_date = row[5].split(" ")[0] if row[5] else False,
				registration_end_date = row[6].split(" ")[0] if row[6] else False,
				ofo_occupation_id= ofo_occupation_id.id
				)
				search_existing_record = self.env['inseta.skill.programme'].search([('legacy_system_id', '=', legacy_system_id)], limit=1)
				if not search_existing_record:
					skill = self.env['inseta.skill.programme'].create(vals)

		if self.import_type == "learner_learnership": # dbo.learnerlearnership.csv
			for count, row in enumerate(file_data):
				# try:
				legacy_system_id = int(row[0])
				learner_id = self.env['inseta.learner'].search([('legacy_system_id','=', row[1])], limit=1)
				learning_programming_id = self.env['inseta.learner.programme'].search([('legacy_system_id','=', row[2])], limit=1)
				agreement_number = row[3]
				financial_year_id = self.env['res.financial.year'].search([('legacy_system_id','=', row[10])], limit=1)
				prj_id = int(row[9]) if row[9] else False
				# project_id = self.env['project.project'].search([('legacy_system_id','=', prj_id)], limit=1)
				# provider_id = self.env['inseta.provider'].search([('legacy_system_id','=', row[7])], limit=1) or learner_id.provider_id.id
				provider_id = learner_id.provider_id.id
				approved = True if row[11] == 1 else False
				commence_date = row[4]
				completion_date = row[5]
				approved_date = row[34]
				# commencement_date = commence_date.split(" ")[0] if commence_date else False,
				# approval_date = approved_date.split(" ")[0] if approved_date else False,
				# enddate = completion_date.split(" ")[0] if completion_date else False,
				commencement_date = self.format_date(commence_date)
				enddate = self.format_date(completion_date)
				approval_date = self.format_date(approved_date)
				
				vals = dict(
				legacy_system_id=legacy_system_id,  # legacy system ID
				is_successful = approved,
				verified = approved,
				commencement_date = commencement_date,
				completion_date = enddate,
				learner_id = learner_id.id if learner_id else False,
				provider_id = provider_id,
				certificate_number = row[14],
				financial_year_id = financial_year_id.id if financial_year_id else False,
				# project_id = project_id.id,
				lga_number = row[25],
				# approved_date = approval_date,
				learning_programming_id = learning_programming_id.id if learning_programming_id else False,
				agreement_number = agreement_number
				)
				search_existing_record = self.env['inseta.learner.learnership'].search([('legacy_system_id', '=', legacy_system_id)], limit=1)
				if not search_existing_record:
					self.env['inseta.learner.learnership'].create(vals)
				# except Exception as e:
				# 	raise ValidationError(f'Error at {row}: See {e}')

		if self.import_type == "skills_learnership": # dbo.learnerskillsprogramme.csv
			for count, row in enumerate(file_data):
				legacy_system_id = int(row[0])
				learner_id = self.env['inseta.learner'].search([('legacy_system_id','=', row[1])], limit=1)
				learning_programming_id = self.env['inseta.learner.programme'].search([('legacy_system_id','=', row[2])], limit=1)
				agreement_number = row[3]
				financial_year_id = self.env['res.financial.year'].search([('legacy_system_id','=', row[10])], limit=1)
				prj_id = int(row[9]) if row[9] else False
				# project_id = self.env['project.project'].search([('legacy_system_id','=', prj_id)], limit=1)
				# provider_id = self.env['inseta.provider'].search([('legacy_system_id','=', row[7])], limit=1) or learner_id.provider_id.id
				provider_id = learner_id.provider_id.id
				approved = True if row and int(row[11]) == 1 else False
				commence_date = row[4]
				completion_date = row[5]
				approved_date = row[34]
				commencement_date = self.format_date(commence_date) # commence_date.split(" ")[0] if commence_date else False,
				approval_date = self.format_date(completion_date) # approved_date.split(" ")[0] if approved_date else False,
				enddate = self.format_date(approved_date) # completion_date.split(" ")[0] if completion_date else False, 
				vals = dict(
				legacy_system_id=legacy_system_id,  # legacy system ID
				is_successful = approved,
				verified = approved,
				commencement_date = commencement_date,
				completion_date = enddate,
				approved_date = approval_date,

				learner_id = learner_id.id,
				provider_id = provider_id.id,
				certificate_number = row[14],
				financial_year_id = financial_year_id.id,
				# project_id = project_id.id,
				lga_number = row[25],
				learning_programming_id = learning_programming_id.id,
				agreement_number = agreement_number
				)
				search_existing_record = self.env['inseta.learner.learnership'].search([('legacy_system_id', '=', legacy_system_id)], limit=1)
				if not search_existing_record:
					self.env['inseta.learner.learnership'].create(vals)

		if self.import_type == "qualification_learnership": # dbo.learnerqualification.csv
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				learner_id = self.env['inseta.learner'].search([('legacy_system_id','=', row[1])], limit=1)
				qualification_id = self.env['inseta.qualification'].search([('legacy_system_id','=', row[2])], limit=1)
				financial_year_id = self.env['res.financial.year'].search([('legacy_system_id','=', row[20])], limit=1)
				project_id = self.env['project.project'].search([('legacy_system_id','=', row[21])], limit=1)
				provider_id = self.env['inseta.provider'].search([('legacy_system_id','=', row[7])], limit=1)
				approved = True if row and int(row[9]) == 1 else False
				commence_date = row[3]
				completion_date = row[4]
				commencement_date = datetime.strptime(
					commence_date, '%Y-%m-%d') if commence_date else False 

				enddate = datetime.strptime(
					completion_date, '%Y-%m-%d') if completion_date else False 
				vals = dict(
				legacy_system_id=legacy_sys_id,  # legacy system ID
				is_successful = approved,
				verified = approved,
				commencement_date = commencement_date,
				completion_date = enddate,
				learner_id = learner_id.id,
				qualification_id = qualification_id.id,
				provider_id = provider_id.id,
				certificate_number = row[12],
				financial_year_id = financial_year_id.id,
				project_id = project_id.id,
				lga_number = False,
				approved_date = False,
				)
				self.env['inseta.qualification.learnership'].create(vals)

		if self.import_type == "learner_qualification_assessment": # dbo.learnerqualificationassessment.csv
			for count, row in enumerate(file_data):
				legacy_sys_id = int(row[0])
				learner_qualification_id = self.env['inseta.learner.learnership'].search([('legacy_system_id','=', int(row[1]) or False)], limit=1)
				unit_standard_id = self.env['inseta.unit.standard'].search([('legacy_system_id','=', int(row[2]) or False)], limit=1)
				assessor_id = self.env['inseta.assessor'].search([('legacy_system_id','=', row[4])], limit=1)
				moderator_id = self.env['inseta.moderator'].search([('legacy_system_id','=', row[6])], limit=1)
				approved = True if row and int(row[8]) == 1 else False
				assessor_assessment_date = row[5]
				moderator_assessment_date = row[7]
				completion_date = row[4] 
				assessor_date = datetime.strptime(
					assessor_assessment_date, '%Y-%m-%d') if assessor_assessment_date else False 

				moderator_date = datetime.strptime(
					moderator_assessment_date, '%Y-%m-%d') if moderator_assessment_date else False 
				vals = dict(
				legacy_system_id=legacy_sys_id,  # legacy system ID
				learner_qualification_assessment_id = learner_qualification_id.id,
				moderator_id = moderator_id.id,
				assessor_id = assessor_id.id,
				unit_standard_id = unit_standard_id.id,
				assessment_date = assessor_date,
				moderator_date = moderator_date,
				active = True,
				)

				self.env['inseta.learnership.assessment'].create(vals)
