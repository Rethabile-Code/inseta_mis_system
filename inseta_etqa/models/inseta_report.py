import csv 
import io
import xlwt
from datetime import datetime, timedelta
import base64
import random
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.parser import parse


class InsetaProviderReport(models.TransientModel):
    _name = "inseta.excel.report"

    excel_file = fields.Binary('Download Excel file', filename='filename', readonly=True)
    filename = fields.Char('Excel File', size=64)
    filter_by = fields.Selection([
        ('all', 'All records'),
        ('date', 'Date'),
    ], required=True, default='date')

    type = fields.Selection([
        ('provider', 'Providers'),
        ('assessor', 'Assessors'),
        ('moderator', 'Moderators'),
        ('learner', 'Learners'),
    ], required=True,)


    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    provider_ids = fields.Many2many('inseta.provider', 'inseta_provider_report_rel', 'inseta_provider_report_id', 'inseta_provider_id', string="Provider")
    assessor_ids = fields.Many2many('inseta.assessor', 'inseta_assessor_report_rel', 'inseta_assessor_report_id', 'inseta_assessor_id', string="Assessor")

    def validate_date_filters(self):
        if self.end_date and self.end_date < self.start_date:
            self.end_date = False
            raise ValidationError("End date must be greater than Start date")

    def export_data(self):
        self.validate_date_filters()
        ProviderObj = self.env['inseta.provider']
        AssessorObj = self.env['inseta.assessor']
        domain = []
        if self.type == "provider":
            if self.filter_by == "date": 
                if self.provider_ids:
                    providers = self.mapped('provider_ids').filtered(lambda s: s.accreditation_start_date >= self.start_date and s.accreditation_start_date <= self.end_date)
                    domain = [('id', 'in', [rec.id for rec in providers])]
                else:
                    domain = [('accreditation_start_date', '>=', self.start_date),
                            ('accreditation_start_date', '<=', self.end_date)]
            
            else:
                if self.provider_ids:
                    providers = self.mapped('provider_ids') #.filtered(lambda s: s.accreditation_start_date >= self.start_date and s.accreditation_start_date <= self.end_date)
                    domain = [('id', 'in', [rec.id for rec in providers])]
                else:
                    domain = []

        elif self.type == "assessor":
            if self.filter_by == "date": 
                if self.assessor_ids:
                    assessors = self.mapped('assessor_ids').filtered(lambda s: s.create_date >= self.start_date and s.create_date <= self.end_date)
                    domain = [('id', 'in', [rec.id for rec in assessors])]
                else:
                    domain = [('create_date', '>=', self.start_date),
                            ('create_date', '<=', self.end_date)]
            
            else:
                if self.assessor_ids:
                    assessors = self.mapped('assessor_ids')
                    domain = [('id', 'in', [rec.id for rec in assessors])]
                else:
                    domain = []
              

        style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
            num_format_str='#,##0.00')
        style1 = xlwt.easyxf(num_format_str='DD-MMM-YYYY')
        wb = xlwt.Workbook()
        ws = wb.add_sheet('REPORT')
        colh = 0
        if self.type == "provider":
            headers = [
            'SDL Number #', 'Name', 'Accreditation Start Date', 'Accreditation End Date', 'Accreditation No',
            'Provider type', 'Provider class', 'SIC code', 
            'Phone', 'Email', 'Physical Code', 'Physical Address Line 1', 'Physical Address Line 2',  
            'Physical Address Line 3', 'Phyiscal Municipality', 'Physical City', 'Physical Suburb', 'Physical Province',
            'Postal Code', 'Postal Address Line 1', 'Postal Address Line 2',  'Postal Address Line 3',  
            'Postal Municipality', 'Postal City', 'Postal Suburb', 'Postal Province',
            'Learnership Scope', 'Qualification Scope', 'Skills Scope', 'Unit standards'
            ] 
            provider_objs = ProviderObj.search(domain)
            if provider_objs:
                ws.write(0, 6, 'PROVIDER RECORDS GENERATED FOR %s - %s' %(self.start_date if self.start_date else '', self.end_date if self.end_date else datetime.strftime(fields.Date.today(), '%Y-%m-%d')), style0)
                for head in headers:
                    ws.write(1, colh, head)
                    colh += 1
                row = 3 
                for records in provider_objs:
                    col = 0
                    employer_sdl_no = records.employer_sdl_no or ""
                    name = records.name or ""
                    accreditation_start_date =  records.accreditation_start_date.strftime("%Y-%m-%d, %H:%M:%S") if records.accreditation_start_date else ""
                    accreditation_end_date =  records.accreditation_end_date.strftime("%Y-%m-%d, %H:%M:%S") if records.accreditation_end_date else ""
                    provider_accreditation_number = records.provider_accreditation_number or ""
                    provider_type_id = records.provider_type_id.name or ""
                    provider_class_id = records.provider_class_id.name or ""
                    sic_code = records.sic_code.name or "" # provider primary focus
                    phone = records.phone or ""
                    email = records.email or ""
                    physical_code = records.zip or ""
                    physical_address_line_1 = records.street or ""
                    physical_address_line_2 = records.street2 or ""
                    physical_address_line_3 = records.street3 or ""
                    physical_municipality = records.physical_municipality_id.name or ""
                    physical_city = records.physical_city_id.name or ""
                    physical_suburb = records.physical_suburb_id.name or ""
                    physical_province = records.physical_province_id.name or ""
                    postal_code = records.postal_code or ""
                    postal_address_line_1 = records.postal_address1 or ""
                    postal_address_line_2 = records.postal_address2 or ""
                    postal_address_line_3 = records.postal_address3 or ""
                    postal_municipality = records.postal_municipality_id.name or ""
                    postal_city = records.postal_city_id.name or ""
                    postal_suburb = records.postal_suburb_id.name or ""
                    postal_province = records.postal_province_id.name or ""
                    learner_programmes_ids = self.env['inseta.provider.learnership'].search([('provider_id', '=', records.id)])
                    learnership_programmes = (',').join(learner_programmes_ids.mapped(lambda e: e.learner_programme_id.name))

                    skill_programmes_ids = self.env['inseta.provider.skill'].search([('provider_id', '=', records.id)])
                    skill_programmes = (',').join(skill_programmes_ids.mapped(lambda e: e.skill_programme_id.name))

                    qualification_programmes_ids = self.env['inseta.provider.qualification'].search([('provider_id', '=', records.id)])
                    qualification_programmes = (',').join(qualification_programmes_ids.mapped(lambda e: e.qualification_id.name))

                    unit_standard_programmes_ids = self.env['inseta.provider.unit_standard'].search([('provider_id', '=', records.id)])
                    unit_standard_programmes = (',').join(unit_standard_programmes_ids.mapped(lambda e: e.unit_standard_id.name))

                    ws.write(row, col, employer_sdl_no)
                    ws.write(row, col + 1, name, style1)
                    ws.write(row, col + 2, accreditation_start_date)
                    ws.write(row, col + 3, accreditation_end_date)
                    ws.write(row, col + 4, provider_accreditation_number)
                    ws.write(row, col + 5, provider_type_id)
                    ws.write(row, col + 6, provider_class_id)
                    ws.write(row, col + 7, sic_code)
                    ws.write(row, col + 8, phone)
                    ws.write(row, col + 9, email)
                    ws.write(row, col + 10, physical_code)
                    ws.write(row, col + 11, physical_address_line_1)
                    ws.write(row, col + 12, physical_address_line_2)
                    ws.write(row, col + 13, physical_address_line_3)
                    ws.write(row, col + 14, physical_municipality)
                    ws.write(row, col + 15, physical_city)
                    ws.write(row, col + 16, physical_suburb)
                    ws.write(row, col + 17, physical_province)
                    ws.write(row, col + 18, postal_code)
                    ws.write(row, col + 19, postal_address_line_1)
                    ws.write(row, col + 20, postal_address_line_2)
                    ws.write(row, col + 21, postal_address_line_3)
                    ws.write(row, col + 22, postal_municipality)
                    ws.write(row, col + 23, postal_city)
                    ws.write(row, col + 24, postal_suburb)
                    ws.write(row, col + 25, postal_province)
                    ws.write(row, col + 26, learnership_programmes)
                    ws.write(row, col + 27, skill_programmes)
                    ws.write(row, col + 28, qualification_programmes)
                    ws.write(row, col + 29, unit_standard_programmes)
                    row += 1

                fp = io.BytesIO()
                wb.save(fp)
                filename = "PROVIDER REPORT ON {}.xls".format(datetime.strftime(fields.Date.today(), '%Y-%m-%d'), style0)
                self.excel_file = base64.encodestring(fp.getvalue())
                self.filename = filename
                fp.close()
            else:
                raise ValidationError('No PROVIDER record found to Export')

        elif self.type == 'assessor':
            headers = [
            'ID Number #', 'Name', 'Birth date', 
            'Sex', 'Phone', 'Mobile', 'Email', 'Fax NUMBER', 
            'Physical Code', 'Physical Address Line 1', 'Physical Address Line 2', 'Physical Address Line 3',  
            'Phyiscal Municipality', 'Physical City', 'Physical Suburb', 'Physical Province',
            'Postal Code', 'Postal Address Line 1', 'Postal Address Line 2', 'Postal Address Line 3', 
            'Postal Municipality', 'Postal City', 'Postal Suburb', 'Postal Province', 'Provider',
            'Home Language', 'School Emis', 'POPI ACT Status', 'POPI ACT Status Date',
            'Learnership Scope', 'Qualification Scope', 'Skills Scope', 'Unit standards'
            ] 
            assessor_objs = AssessorObj.search(domain)
            if assessor_objs:
                ws.write(0, 6, 'ASSESSOR RECORDS GENERATED FOR %s - %s' %(self.start_date if self.start_date else '', self.end_date if self.end_date else datetime.strftime(fields.Date.today(), '%Y-%m-%d')), style0)
                for head in headers:
                    ws.write(1, colh, head)
                    colh += 1
                row = 3 
                for records in assessor_objs:
                    col = 0
                    Identification = records.id_no or ""
                    name = records.name or ""
                    birth_date =  records.birth_date.strftime("%Y-%m-%d, %H:%M:%S") if records.birth_date else ""
                    gender_id = records.gender_id.name or ""
                    phone = records.phone or ""
                    mobile = records.mobile or ""
                    email = records.email or ""
                    fax_number = records.fax_number or ""
                    physical_code = records.zip or ""
                    physical_address_line_1 = records.street or ""
                    physical_address_line_2 = records.street2 or ""
                    physical_address_line_3 = records.street3 or ""
                    physical_municipality = records.physical_municipality_id.name or ""
                    physical_city = records.physical_city_id.name or ""
                    physical_suburb = records.physical_suburb_id.name or ""
                    physical_province = records.physical_province_id.name or ""
                    postal_code = records.postal_code or ""
                    postal_address_line_1 = records.postal_address1 or ""
                    postal_address_line_2 = records.postal_address2 or ""
                    postal_address_line_3 = records.postal_address3 or ""
                    postal_municipality = records.postal_municipality_id.name or ""
                    postal_city = records.postal_city_id.name or ""
                    postal_suburb = records.postal_suburb_id.name or ""
                    postal_province = records.postal_province_id.name or ""
                    provider_id = records.provider_id.name or ""
                    home_language = records.home_language_id.name or ""
                    school_emis = records.school_emis_id.name or ""
                    popi_act_status = records.popi_act_status_id.name or ""
                    popi_act_status_date = records.popi_act_status_date.strftime("%Y-%m-%d, %H:%M:%S") if records.popi_act_status_date else "" 
                    learner_programmes_ids = self.env['inseta.assessor.learner.programme'].search([('assessor_id', '=', records.id)])
                    learnership_programmes = (',').join(learner_programmes_ids.mapped(lambda e: e.learner_programme_id.name))
                    skill_programmes_ids = self.env['inseta.assessor.skill.programme'].search([('assessor_id', '=', records.id)])
                    skill_programmes = (',').join(skill_programmes_ids.mapped(lambda e: e.skill_programme_id.name))
                    qualification_programmes_ids = self.env['inseta.assessor.qualification'].search([('assessor_id', '=', records.id)])
                    qualification_programmes = (',').join(qualification_programmes_ids.mapped(lambda e: e.qualification_id.name))
                    unit_standard_programmes_ids = self.env['inseta.assessor.unit.standard'].search([('assessor_id', '=', records.id)])
                    unit_standard_programmes = (',').join(unit_standard_programmes_ids.mapped(lambda e: e.unit_standard_id.name))

                    ws.write(row, col, Identification)
                    ws.write(row, col + 1, name, style1)
                    ws.write(row, col + 2, birth_date)
                    ws.write(row, col + 3, gender_id)
                    ws.write(row, col + 4, phone)
                    ws.write(row, col + 5, mobile)
                    ws.write(row, col + 6, email)
                    ws.write(row, col + 7, fax_number)
                    ws.write(row, col + 8, physical_code) 
                    ws.write(row, col + 9, physical_address_line_1)
                    ws.write(row, col + 10, physical_address_line_2)
                    ws.write(row, col + 11, physical_address_line_3)
                    ws.write(row, col + 12, physical_municipality)
                    ws.write(row, col + 13, physical_city)
                    ws.write(row, col + 14, physical_suburb)
                    ws.write(row, col + 15, physical_province)
                    ws.write(row, col + 16, postal_code)
                    ws.write(row, col + 17, postal_address_line_1)
                    ws.write(row, col + 18, postal_address_line_2)
                    ws.write(row, col + 19, postal_address_line_3)
                    ws.write(row, col + 20, postal_municipality)
                    ws.write(row, col + 21, postal_city)
                    ws.write(row, col + 22, postal_suburb)
                    ws.write(row, col + 23, postal_province)
                    ws.write(row, col + 24, provider_id)
                    ws.write(row, col + 25, home_language)
                    ws.write(row, col + 26, school_emis)
                    ws.write(row, col + 27, popi_act_status)
                    ws.write(row, col + 28, popi_act_status_date)
                    ws.write(row, col + 29, learnership_programmes)
                    ws.write(row, col + 30, qualification_programmes)
                    ws.write(row, col + 31, unit_standard_programmes)
                    row += 1

                fp = io.BytesIO()
                wb.save(fp)
                filename = "ASSESSOR REPORT ON {}.xls".format(datetime.strftime(fields.Date.today(), '%Y-%m-%d'), style0)
                self.excel_file = base64.encodestring(fp.getvalue())
                self.filename = filename
                fp.close()
            else:
                raise ValidationError('No ASSESSOR record found to Export')

    def button_export_records(self):
        self.export_data()
        self.end_date = False
        self.excel_file = False

    def button_export_and_download(self):
        self.export_data()
        return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model=inseta.excel.report&download=true&field=excel_file&id={}&filename={}'.format(self.id, self.filename),
                'target': 'new',
                'nodestroy': False,
        }

