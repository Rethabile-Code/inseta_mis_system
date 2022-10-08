
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


class ImportSkillsRecords(models.TransientModel):
	_name = 'import_skill_record.wizard'
	_description = "Skill Import"

	select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], default='csv', string='Select')
	data_file = fields.Binary(string="Upload File (.xls)")
	filename = fields.Char("Filename")

	import_type = fields.Selection([
			('sdf', 'Import Facilitator'),
			('employer', 'Organisation / DHET Employer'),
			('inter-seta', 'Inter-seta'),
			('wsp', 'WSP'),
			('atr', 'ATR'),
		],string='Import Type', required=True, index=True, copy=True,
	)

	def excel_reader(self, index=0):
		if self.data_file:
			if self.select_file == 'csv' :
				# import CSV file import v10
				fileobj = TemporaryFile('w+')
				fileobj.write(base64.decodestring(self.data_file))
				fileobj.seek(0)
				reader = csv.reader(fileobj, delimiter=',', quotechar="'")
				next(reader)
				file_data = reader
				return file_data

			elif self.select_file == 'xls':  
				file_datas = base64.decodestring(self.data_file)
				workbook = xlrd.open_workbook(file_contents=file_datas)
				sheet = workbook.sheet_by_index(index)
				data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
				data.pop(0)
				file_data = data
				return file_data
		else:
			raise ValidationError('Please select file and type of file')

	def import_button(self):
		if self.import_type == "sdf":
			self.import_sdf_data()
		elif self.import_type == "inter-seta":
			self.update_inter_seta()


	def date_format(self, date_str):
		date_return = False
		if date_str:
			date_split = date_str[10].split(' ') # 2010-10-11 12:11:21.0+1
			if date_split:
				date_content = date_split[1] # 2010-10-11
				date_split2 = date_content.split('-')
				if len(date_split2) > 2:
					date_return = '{}-{}-{}'.format(date_split2[0], date_split2[1], date_split2[2])
		return date_return

	def import_sdf_data(self):
		index=1 # ensure that the sheet is in index 1 (2nd sheet after employer)
		file_data = self.excel_reader(index)
		err_list = ['The following error occurred']
		for row in file_data:
			try:
				inseta_sdf = self.env['inseta.sdf']
				inseta_sdf_reg = self.env['inseta.sdf.register']
				nationality = self.env['res.nationality'].search([('name', '=', row[18])], limit=1)
				city = self.env['res.city'].search([('name', '=', row[24])], limit=1)
				municipality = self.env['res.municipality'].search([('name', '=', row[25])], limit=1)
				province = self.env['res.country.state'].search([('name', '=', row[26])], limit=1)
				suburb = self.env['res.suburb'].search([('name', '=', row[27])], limit=1)
				city = self.env['res.city'].search([('name', '=', row[24])], limit=1)
				employers = row[38] # '12334 ', '4342 ',
				employer_list = []
				if employers:
					employer_item = employers.split(',') # ['12334 ', '4342 ',]
					for rec in employer_item:
						employer_id = self.env['inseta.organisation'].search([('employer_sdl_no', '=', rec.strip())], limit=1)
						if employer_id:
							employer_list.append(employer_id.id)
				value_data = {
					# 'legacy_system_id': row[0],
					'reference': row[1], 'first_name': row[2], 'middle_name': row[3], 'last_name': row[4],
					'name': '{} {} {}'.format(row[2], row[3],row[4]),
					'birth_date': self.birth_date, 'gender': 'male' if row[5] == 'M' else 'female', 
					'cell_phone_number': row[6], 'telephone_number': row[7], 'fax_number': row[8], 'email_address': row[9],
					'date_of_registration': self.date_format(row[10]), 'sdf_approval_date': self.date_format(row[11]), 
					'sdf_denied_date': self.date_format(row[12]),
					'state': 'deactive' if row[13] == 'Deactivated' else 'done' if row[13] == 'Approved' else 'refuse' if row[13] == 'Rejected' else 'rework',
					'has_completed_sdf_training': True if row[14] == 'TRUE' else False,
					'highest_level_of_education_desc': row[15], 'nationality_id': nationality.id if nationality else self.env['res.nationality'].create({'name': row[18]}).id,
					'physical_code': row[20], 'physical_address1': row[21], 'physical_address2': row[22], 'physical_address3': row[23], 
					'physical_city_id': city if city else self.env['res.city'].create({'name': row[24]}).id,
					'physical_municipality_id': municipality.id if municipality else self.env['res.municipality'].create({'name': row[25]}).id, 
					'physical_province_id': province.id if province else self.env['res.country.state'].create({'name': row[26]}).id, 
					'physical_suburb_id': suburb.id if suburb else self.env['res.suburb'].create({'name': row[27]}).id, 
					'physical_code': row[28], 'postal_address1': row[29], 'postal_address2': row[30], 'postal_address3': row[31], 
					'postal_city_id': self.env['res.city'].search([('name', '=', row[32])], limit=1).id if self.env['res.city'].search([('name', '=', row[32])], limit=1)\
							else self.env['res.city'].create({'name': row[32]}), 
					'postal_municipality_id': self.env['res.municipality'].search([('name', '=', row[33])], limit=1).id if self.env['res.municipality'].search([('name', '=', row[32])], limit=1)\
							else self.env['res.municipality'].create({'name': row[33]}), 
					'postal_province_id': self.env['res.country.state'].search([('name', '=', row[34])], limit=1).id if self.env['res.country.state'].search([('name', '=', row[34])], limit=1) else False,
					'postal_suburb_id': self.env['res.suburb'].search([('name', '=', row[35])], limit=1).id if self.env['res.suburb'].search([('name', '=', row[35])], limit=1)\
							else self.env['res.suburb'].create({'name': row[35]}),
					'socio_economic_status_id': 'employed' if row[36] == 'Employed' else 'unemployed',
					'years_in_occupation': row[37], 'employer_ids': [(6, 0, employer_list)]
				}
				inseta_sdf_reg.create(value_data) # creating sdf registration record
				inseta_sdf.create(value_data) # creating sdf record
			except Exception as e:
				err_list.append('Reference with reference {} error: {}'.format(row[1], e))
		if len(err_list) > 1:
			msg = ', \n'.join(err_list)
			return self.confirm_notification(msg)

	def update_inter_seta(self):
		index=0 # ensure that the sheet is in index 1 (2nd sheet after employer)
		file_data = self.excel_reader(index)
		err_list = ['The following error occurred']
		for row in file_data:
			municipality = self.env['res.municipality'].search([('name', '=', row[19])], limit=1)
			register_no_type_id = self.env['inseta.registration.no.type'].search([('name', '=', row[21])], limit=1)
			employer_no = row[0]
			inseta_org = self.env['inseta.organisation'].search([('employer_sdl_no', '=', employer_no)], limit=1)
			if inseta_org:
				inseta_org.update({
					'employer_sdl_no': employer_no, 'org_business_desc': row[1], 
					'registration_no': row[2], 'registration_no_type_id' : register_no_type_id.id or None,
					'status_type': row[4], 'email': row[5], 'phone': row[6],
					'fax_number': row[7], 'employees_count': row[8], 'postal_address1': row[9], 'postal_address2': row[10], 
					'postal_address3': row[11], 'postal_code': row[12], 'physical_address1': row[13], 'physical_address2': row[14],
					'physical_address3': row[15], 'physical_code': row[16], 'physical_urban_rural': row[17] if row[17].startswith('Urb') else 'Rural', 
					'is_unionized': row[18], 'physical_municipality_id': municipality.id if municipality else inseta_org.physical_municipality_id.id,
					'trading_name': row[20], 
				})

	def confirm_notification(self,popup_message):
		view = self.env.ref('migration_module.migration_confirm_dialog_view')
		view_id = view and view.id or False
		context = dict(self._context or {})
		context['message'] = popup_message
		return {
				'name':'Message!',
				'type':'ir.actions.act_window',
				'view_type':'form',
				'res_model':'migration.confirm.dialog',
				'views':[(view.id, 'form')],
				'view_id':view.id,
				'target':'new',
				'context':context,
				}

 