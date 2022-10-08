
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
	_name = 'inseta.learner.batch.upload.wizard'
	_description  = "Import Wizard"

	file_type = fields.Selection(
		[('xlsx', 'XLSX File')], default='xlsx', string='File Type')
	file = fields.Binary(string="Upload File (.xlsx)")
	file_name = fields.Char("Filename")
	import_type = fields.Selection([
			('batch', 'Learner Batch Upload'),
		],
		string='Import Type', required=True, index=True,
		copy=True, default='batch',
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

	def validate_id_number(self, id_number):
		if type(id_number) in [int, float]:
			id_number = int(id_number)
		id_number = str(id_number).strip()
		return id_number

	def validate_phone_fax_number(self, number):
		if type(number) in [int, float]:
			number = int(number)
		if type(number) == str:
			number = number.split('.')[0]
		number = str(number).strip()
		return number

	def get_genders(self, gender_value):
		gender = ''
		if gender_value in ['M', 'm', 'Male', 'male']:
			gender_id = self.env['res.gender'].search([('name', 'like', 'male')], limit=1)
			gender = gender_id.id

		if gender_value in ['F', 'f', 'Female', 'female']:
			gender_id = self.env['res.gender'].search([('name', 'like', 'female')], limit=1)
			gender = gender_id.id
		return gender
	
	def validate_date(self, input_date): # '%d/%m/%Y'
		try:
			if type(input_date) in [str]:
				input_date = datetime.strptime(
					str(input_date), '%d/%m/%Y').date()
			elif type(input_date) in [int, float]:
				input_date = datetime(
					*xlrd.xldate_as_tuple(input_date, 0)).date()
				
			else:
				input_date = str(input_date)
		except:
			input_date = str(input_date)
		return input_date
	
	def get_value_id(self, model, value):
		name = "" if not value else value
		value_id = self.env[f'{model}'].search([('name', 'like', value)], limit=1)
		return value_id.id
 
	def action_import(self):
		file_data = self.read_file()
		for count, row in enumerate(file_data):
			error = []
			vals = dict(
				title = self.get_value_id('res.partner.title', row[1]),  # name
				first_name=row[2],
				middle_name=row[3],
				last_name=row[4],
				name = f"{row[2]} {row[3]} {row[4]}",
				initials = row[5],
				id_no = self.validate_id_number(row[6]),# int(row[6]) if isinstance(row[6], float) else row[6],
				alternateid_type_id = self.get_value_id('res.alternate.id.type', row[7]),
				birth_date = self.validate_date(row[8]), # row[8].split(" ")[0],
				gender_id =  self.get_value_id('res.gender', row[9]),
				equity_id = self.get_value_id('res.equity', row[10]),
				disability_id = self.get_value_id('res.disability', row[11]),
				home_language_id = self.get_value_id('res.lang', row[12]),
				nationality_id = self.get_value_id('res.nationality', row[13]),
				citizen_resident_status_id = self.get_value_id('res.citizen.status', row[14]),
				socio_economic_status_id = self.get_value_id('res.socio.economic.status', row[15]),
				phone = self.validate_phone_fax_number(row[16]),# int(row[16]) if isinstance(row[16], float) else row[16],
				mobile = self.validate_phone_fax_number(row[17]),#int(row[17]) if isinstance(row[17], float) else row[17],
				fax_number = self.validate_phone_fax_number(row[18]),#int(row[18]) if isinstance(row[18], float) else row[18],
				email = row[19],
				street = row[20],
				street2 = row[21],
				street3 = row[22],
				physical_code = row[23] if row[23] else "",
				physical_suburb_id = self.get_value_id('res.suburb', row[24]),
				physical_city_id = self.get_value_id('res.city', row[25]),
				physical_municipality_id = self.get_value_id('res.municipality', row[26]),
				physical_urban_rural = 'Urban' if row[27] == "Urban" else "Rural",
				physical_province_id = self.get_value_id('res.country.state', row[28]),
				use_physical_for_postal_addr = True if row[29] in ['True', 'TRUE'] else False,
				postal_address1 = row[19] if row[29] in ['True', 'TRUE'] else row[30],
				postal_address2 = row[20] if row[29] in ['True', 'TRUE'] else row[31],
				postal_address3 = row[22] if row[29] in ['True', 'TRUE'] else row[32],
				postal_code = row[23] if row[29] in ['True', 'TRUE'] else row[33],
				postal_suburb_id = self.get_value_id('res.suburb', row[24]) if row[29] in ['True', 'TRUE'] else self.get_value_id('res.suburb', row[34]),
				postal_city_id = self.get_value_id('res.city', row[25]) if row[29] in ['True', 'TRUE'] else self.get_value_id('res.city', row[35]),
				postal_municipality_id = self.get_value_id('res.municipality', row[26]) if row[29] in ['True', 'TRUE'] else self.get_value_id('res.municipality', row[36]),
				postal_urban_rural = 'Urban' if row[37] == "Urban" else "Rural",
				postal_province_id = self.get_value_id('res.country.state', row[28]) if row[29] in ['True', 'TRUE'] else self.get_value_id('res.country.state', row[38]),
				)
			if self.import_type == "batch":
				self.env['inseta.learner'].create(vals)

	# def _get_object_by_legacy_id(self, model, legacy_id):
	# 	if legacy_id: 
	# 		if isinstance(legacy_id, int) or isinstance(legacy_id, float):
	# 			_logger.info(f" Model: {model}, Legacy ID: {int(legacy_id)} ")
	# 			obj = self.env[model].search([('legacy_system_id', '=', int(legacy_id))], limit=1)
	# 			return obj and int(obj.id) or False
	# 	return False

 