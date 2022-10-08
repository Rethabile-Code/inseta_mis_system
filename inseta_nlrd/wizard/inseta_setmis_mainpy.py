from odoo.exceptions import UserError, ValidationError, RedirectWarning
import csv 
import io
import xlwt
import random
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.parser import parse
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta as rd
import base64
import sys
import re
import os
from collections import OrderedDict as OD

_logger = logging.getLogger(__name__)


class Insetasetmis(models.Model):
    _name = 'inseta.setmis'
    _description  = "setmis GENERATED"
    
    name = fields.Char('File')
    file_unique_identifier = fields.Char('File Unique Idenitifier')
    error_to_fix =


class InsetasetmisExport(models.TransientModel):
    _name = 'inseta.setmis.export'
    _description  = "setmis EXPORT Wizard"

    dat_file = fields.Binary('Download SETMIS file', filename='filename', readonly=True)
    filename = fields.Char('DAT File')
    file_type = fields.Selection([
        ('100', 'Providers (File 100)'),
        ('200', 'Employer (File 200)'),
        ('400', 'Person Information (File 400)'),
        ('401', 'Person Designation - Assessor Registration (File 401)'),
        ('500', 'Learnership Enrollment  / Achievement (File 500)'),
        ('501', 'Qualification Enrollment / Achievement (File 501)'),
        ('502', 'Non NQF Intervention Enrolments (502)'),
    ], required=True)
    filter_by = fields.Selection([
        ('all', 'All records'),
        ('date', 'Date'),
    ], required=True, default='date', string="Filter by", help="Start Date")

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    limit = fields.Integer('Limit', default=100)

    def nationality_to_code(self,nat):
        nat_map = {
            "COLOMBIA": "U",
            "MOZAMBIQUE":"MOZ",
            "South Africa": "SA",
            "sa (DO NOT USE!)": "SA",
            "SA (DO NOT USE!)": "SA",
            "S A (DO NOT USE!)": "SA",
            "SADC except SA": "SDC",
            "Angola": "ANG",
            "Botswana": "BOT",
            "LESOTHO": "LES",
            "MALAWI": "MAL",
            "Malawi": "MAL",
            "Mauritius": "MAU",
            "Mozambique": "MOZ",
            "NAMIBIA": "NAM",
            "Namibia": "NAM",
            "Seychelles": "SEY",
            "SWAZILAND": "SWA",
            "Swaziland": "SWA",
            "Tanzania": "TAN",
            "Zaire": "ZAI",
            "Zambia": "ZAM",
            "ZAMBIA": "ZAM",
            "ZIMBABWE": "ZIM",
            "Asian countries": "AIS",
            "Australia	Oceania	countries": "AUS",
            "European	countries": "EUR",
            "North	American	countries": "NOR",
            "South / Central American": "SOU",
            "Rest	of	Africa": "ROA",
            "NIGERIA": "ROA",
            "CONGO": "ROA",
            "UGANDA": "ROA",
            "Other & rest of Oceania": "OOC",
            'ANGOLA': "U",
            'GHANA': "U",
            'CAMEROON': "U",
            "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "U",
            "COTE D'IVOIRE": "U",
            'AFGHANISTAN': "U",
            False: "U",
            "Unspecified": "U",
            "N / A: Institution": "NOT",
            'South Africa': "ZA",
        }
        return nat_map[nat]

    def validate_date_filters(self):
        if self.end_date and self.end_date < self.start_date:
            self.end_date = False
            raise ValidationError("End date must be greater than Start date")

    def fix_dates(self, date):
        dt_return = '19890413'
        if type(date) == str and len(date) > 10:
            dt_return = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
            dt_return = re.sub('-', '', dt_return)

        elif type(date) == str and len(date) <= 10:
            dt_return = re.sub('-', '', date)
        elif type(date) == datetime:
            dt_return = datetime.strftime(date, '%Y-%m-%d %H:%M:%S') 
            dt_split = dt_return.split(' ')
            if dt_split:
                dt_return = re.sub('-', '', dt_split[0])
        elif type(date) == date:
            dt_return = datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
            dt_split = dt_return.split(' ')
            if dt_split:
                dt_return = re.sub('-', '', dt_split[0])
        # else:
        # 	dt_return = dt_return 
        return dt_return

    def compute_date_data(self, dateobj):
        result = "19890413"
        if dateobj:
            date_str = datetime.strftime(dateobj, "%Y-%m-%d")
            result = re.sub('-','',date_str)
        return result 

    def filth_date_gap(self,start, end):
        if end == '20200331':
            return '20150331'
        else:
            return start

    def make_up_date(self,date):
        if not date:
            return '20200331'
        else:
            return date

    def sanitize_addrs(self,addr):
        addr = re.sub(";", " ", str(addr))
        addr = re.sub('"', '', str(addr))
        addr = str.strip(str(addr))
        return addr

    def sanitize_email(self, email):
        if email:
            email = re.sub(' ', '', email)
        else:
            email = email # consider removing
        return email

    def lang_to_code(self, lang):
        langs = {'English': 'Eng',
                'isiZulu': 'Zul',
                'Ndebele': 'Nde',
                'Afrikaans': 'Afr',
                'Other': 'Oth',
                'South African Sign Language': 'SASL',
                'sePedi': 'Sep',
                'seSotho': 'Ses',
                'seTswana': 'Set',
                'siSwati': 'Swa',
                'tshivenda': 'Tsh',
                False: 'U',
                'Unknown': 'U',
                'isiXhosa': 'Xho',
                'xiTsonga': 'Xit',
                }
        return langs[lang]

    def generate_filename(self, file_code):
        # FORMAT [CODE]_0006_100_v001_YYYYMMDD
        code = 'INSE'
        unique_code = '0006' 
        file_code = file_code
        date = dt_str = datetime.strftime(datetime.today(), '%Y-%m-%d')
        filename_suffix = re.sub('-', '', dt_str) # 20210121 
        setmis_last_gen = self.env['inseta.setmis'].search([('name', '=', file_code)])
        filename = f"{code}_{unique_code}_{file_code}_v001_{filename_suffix}.dat" # e.g INSE_0006_100_v001_20120130

        # if setmis_last_gen:
        #     old_setmis_file = setmis_last_gen[-1].file_unique_identifier[14:17] # v001  => 1
        #     setmis_filename = setmis_last_gen[-1].file_unique_identifier[17:18] # v001  => 1
        #     # raise ValidationError(setmis_filename)
        #     cnvrt_setmis_filename_int = int(setmis_filename) + 1  #=> 1 + 1
        #     filename = f"{code}_{unique_code}_{file_code}_{old_setmis_file}{str(cnvrt_setmis_filename_int)}_{filename_suffix}.dat" # e.g INSE_0006_100_v001_20120130
        # else:
        #     filename = f"{code}_{unique_code}_{file_code}_v001_{filename_suffix}.dat"
        return filename

    def accredit_status_to_code(self,pas):
        provider_accredit_status_code_map = {
            "Active": "A",
            "Inactive": "I",
            "Legacy": "L",
            "Provisional": "V",
        }
        return provider_accredit_status_code_map[pas]

    def gender_to_code(self, gen):
        gender_map = {
            False: "F",
            "female": "F",
            "male": "M",
            "Male": "M",
            "Female": "F",
        }
        return gender_map[gen]

    def disability_status_code(self,ds):
        dsmap = {
            '1': "01",
            '2': "02",
            '3': '03',
            '4': '04',
            '5': '05',
            '6': '06',
            '7': '07',
            '8': '08',
            '9': '09',
            '10': '09',
            '11': 'N',
            '12': 'N',
            'none': 'N',
            'None': 'N',
            False: 'N',
            False: 'N',
        }
        try:
            return dsmap[ds]
        except:
            return "N"

    def equity_to_code(self, eq):
        equity_map = {
            "White": "Wh",
            "WHITE": "Wh",
            "white": "Wh",
            "black_coloured": "BC",
            "Black: Coloured": "BC",
            "block_col": "BC",
            "Black_af": "BA",
            "Black: African": "BA",
            "black_co": "BC",
            "Other": "Oth",
            False: "U",
            None: "U",
            "None": "U",
            "BA": "BA",
            "BC": "BC",
            "BI": "BI",
            "Wh": "Wh",
            "Oth": "Oth",
            "U": "U",
            "Unknown": "U",
        }
        return equity_map[eq]

    def socio_to_code(self, soc):
        socio_map = {'Unspecified': "U",
                    False: "U",
                    'unemployed': "02",
                    'Home-maker (not working)': '04',
                    'Pensioner/retired (not w.)': '07',
                    'Not working - disabled': '08',
                    'Not working - no wish to w': '09',
                    'Not working - N.E.C.': '10',
                    'N/A: Institution': '98',
                    'employed': '01',
                    'Employed': '01',
                    'Unemployed': '02',
                    'N/A: aged <15': '97',
                    'Scholar/student (not w.)': '06',
                    'Not working, not looking': '03'}
        return socio_map[soc]

    def action_generate_200(self):
        # header = [
        #         1, 11,21,24,34,
        #         54,124,194, 244, 294,
        #         344,348,398, 448,498,
        #         502, 522, 542, 592, 642, 
        #         662, 682, 692, 700, 708, 
        #         728,730, 734, 737, 739,
        #         745,747, 749, 755, 765,
        #         785, 789,]
        header = [
            10, 10, 3, 10, 20,
            70, 70, 50, 50, 50, 
            4, 50, 50, 50, 4, 
            20, 20, 50, 50, 20, 
            20, 10, 8, 8, 20, 
            2, 4, 3, 2, 6, 
            2, 2, 6, 10, 20, 
            4, 8
            ]    
        header_keys = [
            'SDL_No',
            'Site_No',
            'SETA_Id',  # maybe later
            'SIC_Code',
            'Employer_Registration_Number',
            'Employer_Company_Name',
            'Employer_Trading_Name',
            'Employer_Postal_Address_1',
            'Employer_Postal_Address_2',
            'Employer_Postal_Address_3',
            'Employer_Postal_Address_Code',
            'Employer_Physical_Address_1',
            'Employer_Physical_Address_2',
            'Employer_Physical_Address_3',
            'Employer_Physical_Address_Code',
            'Employer_Phone_Number',
            'Employer_Fax_Number', 
            'Employer_Contact_Name', 
            'Employer_Contact_Email_Address', 
            'Employer_Contact_Phone_Number', 
            'Employer_Contact_Cell_Number', 
            'Employer_Approval_Status_Id', 
            'Employer_Approval_Status_Start_Date', 
            'Employer_Approval_Status_End_Date',
            'Employer_Approval_Status_Num', 
            'Province_Code', 
            'Country_Code', 
            'Latitude_Degree', 
            'Latitude_Minutes', 
            'Latitude_Seconds', 
            'Longitude_Degree', 
            'Longitude_Minutes', 
            'Longitude_Seconds', 
            'Main_SDL_No', 
            'Filler01', 
            'Filler02', 
            'Date_Stamp', 
        ]
        val = {
            }
        domain = []
        if self.filter_by == "date": 
            domain = [
                ('date_of_registration', '>=', self.start_date), 
                ('date_of_registration', '<=', self.end_date)
                ]
        organisation_ids = self.env['inseta.organisation'].search(domain, limit=self.limit)
        if organisation_ids:
            val_items = []
            filename = self.generate_filename('200')
            error_msg = []
            for emp in organisation_ids:
                if emp.sdl_no:
                    vals = {
                        
                            'SDL_No': emp.sdl_no,
                            'Site_No': "",
                            'SETA_Id': emp.seta_id.saqacode,  # maybe later
                            'SIC_Code': emp.sic_code_id.siccode,
                            'Employer_Registration_Number': emp.registration_no,
                            'Employer_Company_Name': emp.legal_name or emp.name,
                            'Employer_Trading_Name': emp.trade_name,
                            'Employer_Postal_Address_1': emp.postal_address1,
                            'Employer_Postal_Address_2': emp.postal_address2,
                            'Employer_Postal_Address_3': emp.postal_address3,
                            'Employer_Postal_Address_Code': emp.postal_code,
                            'Employer_Physical_Address_1':emp.street,
                            'Employer_Physical_Address_2':emp.street2,
                            'Employer_Physical_Address_3':emp.street3,
                            'Employer_Physical_Address_Code': emp.physical_code,
                            'Employer_Phone_Number':emp.phone,
                            'Employer_Fax_Number':emp.fax_number, 
                            'Employer_Contact_Name': emp.child_ids[0].name if emp.child_ids else "", 
                            'Employer_Contact_Email_Address': emp.child_ids[0].email if emp.child_ids else "", 
                            'Employer_Contact_Phone_Number': emp.child_ids[0].phone if emp.child_ids else "", 
                            'Employer_Contact_Cell_Number': emp.child_ids[0].mobile if emp.child_ids else "", 
                            'Employer_Approval_Status_Id': 1 if emp.active else 2, 
                            'Employer_Approval_Status_Start_Date': self.fix_dates(emp.date_of_registration),
                            'Employer_Approval_Status_End_Date': '',
                            'Employer_Approval_Status_Num': '', 
                            'Province_Code': emp.physical_code, 
                            'Country_Code': emp.country_id.code, 
                            'Latitude_Degree': emp.latitude_degree, 
                            'Latitude_Minutes': emp.latitude_minutes, 
                            'Latitude_Seconds': emp.latitude_seconds, 
                            'Longitude_Degree': emp.longitude_degree, 
                            'Longitude_Minutes': emp.longitude_minutes, 
                            'Longitude_Seconds': emp.longitude_seconds, 
                            'Main_SDL_No':emp.sdl_no or emp.possible_sdl_no, 
                            'Filler01': '', 
                            'Filler02': '', 
                            'Date_Stamp': self.fix_dates(emp.write_date),
                    }
                    val_items.append(vals)
                else:
                    error_msg.append(emp.trade_name)
                # raise ValidationError(len(header)) # f'{len(vals.keys())}')
            setmis_obj = self.env['inseta.setmis'].create({
                'name': '200',
                'file_unique_identifier': filename,
            })
            # for values in val_items:
            #     _logger.info(values)
            #     self.generate_dat(values, header, header_keys, filename)
            self.generate_dat(val_items, header, header_keys, filename)
            filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
            byte_data = None
            with open(filepath, "rb") as xlfile:
                byte_data = xlfile.read()
                 
            attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.encodestring(byte_data),
                    'type': 'binary',
                    'res_id': self.id,
                    'res_model': 'inseta.setmis.export',
                    'mimetype': 'application/dat'
                    # 'description': f"inseta setmis export: [{filename}] created on {fields.Datetime.now()}"
                })
            return attachment, filename, error_msg
        else:
            raise ValidationError('No Provider record to generate setmis')

    def action_generate_400(self):
        """Generate Learner / person (inseta.learner) model record"""
         
        header = [
            15, 20, 3, 10, 3,
            10, 1, 10, 2, 45,
            26, 50, 10, 8, 50,
            50, 50, 50, 50, 50, 
            4, 4, 20, 20, 20,
            50, 2, 20, 10, 45,
            20, 3, 20, 10, 2,
            2, 2, 2, 2, 2, 
            20, 4, 20, 2, 8,
            8, 
            ]

        header_keys = [
                    'National_Id',
                       'Person_Alternate_Id',  
                       'Alternate_Id_Type',
                       'Equity_Code',  # y
                       'Nationality_Code', #5
                       'Home_Language_Code',
                       'Gender_Code',
                       'Citizen_Resident_Status_Code',
                       'Filler01',
                       'Filler02',
                       'Person_Last_Name',
                       'Person_First_Name', 
                       'Person_Middle_Name',
                       'Person_Title',
                       'Person_Birth_Date',
                       'Person_Home_Address_1',
                       'Person_Home_Address_2',
                       'Person_Home_Address_3',
                       'Person_Postal_Address_1',
                       'Person_Postal_Address_2', # 20
                       'Person_Postal_Address_3',
                       'Person_Home_Addr_Postal_Code',
                       'Person_Postal_Addr_Post_Code',
                       'Person_Phone_Number',
                       'Person_Cell_Phone_Number',
                       'Person_Fax_Number',
                       'Person_Email_Address',
                       'Province_Code',
                       'Provider_Code',  # c
                       'Provider_ETQE_Id',  # 30 c blanket 
                       'Person_Previous_Alternate_Id',
                       'Person_Previous_Alternate_Id_Type_Id',  # c
                       'Person_Previous_Provider_Code',
                       'Person_Previous_Provider_ETQE_Id',  # c
                       'Seeing_Rating_Id',
                       'Hearing_Rating_Id',
                       'Walking_Rating_Id',
                       'Remembering_Rating_Id',
                       'Communicating_Rating_Id',
                       'Self_Care_Rating_Id',
                       'Last_School_EMIS_No',
                       'Last_School_Year', # 40
                       'STATSSA_Area_Code', # 40
                       'POPI_Act_Status_ID', # 40
                       'POPI_Act_Status_Date', # 40
                       'Date_Stamp',  # y
                       ]
        # raise ValidationError(f'{len(header)} --- {len(header_keys)}')
        domain = [('id_no', '!=', False)]
        if self.filter_by == "date": 
            domain += [
                ('create_date', '>=', self.start_date), 
                ('create_date', '<=', self.end_date)
                ]
        person = self.env['inseta.learner'].search(domain, limit=self.limit)
        if person:
            val_items = []
            filename = self.generate_filename('400')
            for pers in person:
                vals = {
                    'National_Id': pers.id_no,
                    'Person_Alternate_Id': pers.id_no,  # c
                    'Alternate_Id_Type': pers.alternateid_type_id.saqacode,  # req
                    'Equity_Code': pers.equity_id.saqacode, # self.equity_to_code(pers.equity_id.name),  # y
                    'Nationality_Code': pers.nationality_id.saqacode, #self.nationality_to_code(pers.nationality_id.name),  # y
                    'Home_Language_Code': pers.home_language_id.code or self.lang_to_code(pers.home_language_id.name),  # y
                    'Gender_Code': self.gender_to_code(pers.gender_id.name),  # y
                    'Citizen_Resident_Status_Code': pers.citizen_resident_status_id.saqacode,
                    'Filler01': '',  # y
                    'Filler02': '',  # y
                    'Person_First_Name': pers.first_name,  # y
                    'Person_Last_Name': pers.last_name,  # y
                    'Person_Middle_Name': pers.middle_name,
                    'Person_Title': '',
                    'Person_Birth_Date': self.compute_date_data(pers.birth_date),
                    'Person_Home_Address_1': pers.street,
                    'Person_Home_Address_2': pers.street2,
                    'Person_Home_Address_3': pers.street3,
                    'Person_Postal_Address_1': pers.postal_address1,
                    'Person_Postal_Address_2': pers.postal_address2, # 20
                    'Person_Postal_Address_3': pers.postal_address3,
                    'Person_Home_Addr_Postal_Code': pers.physical_code,
                    'Person_Postal_Addr_Post_Code': pers.postal_code,
                    'Person_Phone_Number': pers.phone,
                    'Person_Cell_Phone_Number': pers.mobile,
                    'Person_Fax_Number': pers.fax_number,
                    'Person_Email_Address': pers.email,
                    'Province_Code': pers.physical_province_id.saqacode,  # y
                    'Provider_Code': pers.provider_id.saqa_provider_code,  # c
                    'Provider_ETQE_Id': '595',  # 30 c blanket
                    'Person_Previous_Alternate_Id': '',
                    'Person_Previous_Alternate_Id_Type_Id': '',  # c
                    'Person_Previous_Provider_Code': '',
                    'Person_Previous_Provider_ETQE_Id': '',  # c
                    'Seeing_Rating_Id': '',
                    'Hearing_Rating_Id': '',
                    'Walking_Rating_Id': '',
                    'Remembering_Rating_Id': '',
                    'Communicating_Rating_Id': '',
                    'Self_Care_Rating_Id': '',
                    'Last_School_EMIS_No': pers.school_emis_id.saqacode,
                    'Last_School_Year': pers.last_school_year.saqacode,
                    'STATSSA_Area_Code': pers.statssa_area_code_id.saqacode,
                    'POPI_Act_Status_ID': '' if pers.popi_act_status_id.saqacode == 2 else pers.popi_act_status_id.saqacode,
                    'POPI_Act_Status_Date': self.fix_dates(pers.popi_act_status_date),
                    'Date_Stamp': self.fix_dates(pers.write_date),  # y
                    }
                val_items.append(vals)
            setmis_obj = self.env['inseta.setmis'].create({
                'name': '400',
                'file_unique_identifier': filename,
            })
            # for values in val_items:
            #     _logger.info(values)
            #     self.generate_dat(values, header, header_keys, filename)
            self.generate_dat(val_items, header, header_keys, filename)
            filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
            byte_data = None
            with open(filepath, "rb") as xlfile:
                byte_data = xlfile.read()
            attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.encodestring(byte_data),
                    'type': 'binary',
                    'res_id': self.id,
                    'res_model': 'inseta.setmis.export',
                    'mimetype': 'application/dat'
                    # 'description': f"inseta setmis export: [{filename}] created on {fields.Datetime.now()}"
                })
            return attachment, filename
        else:
            raise ValidationError('No learner record to generate setmis')

    def action_generate_401(self):
        """Generate Assessor model record"""
        header = [
                15, 20,3,5,20,10,
                8, 8,10,20,20,10,
                10, 10, 10, 8
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternative_Id_Type',
            'Designation_Id',
            'Designation_Registration_Number',
            'Designation_ETQA_Id',
            'Designation_Start_Date',
            'Designation_End_Date',
            'Designation_Structure_Status_Id',
            'Etqa_Decision_Number',
            'Provider_Code',
            'Provider_ETQE_Id',
            'Filler01',
            'Filler01',
            'Filler03',
            'Date_Stamp', 
        ]

        val = {
            }
        domain = []
        if self.filter_by == "date": 
            domain = [
                ('start_date', '>=', self.registration_start_date), 
                ('start_date', '<=', self.registration_end_date)
                ]
        assessor_objs = self.env['inseta.assessor'].search(domain, limit=self.limit)
        if assessor_objs:
            val_items = []
            filename = self.generate_filename('401')
            attachment = False 
            for accrs in assessor_objs:      
                eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                vals = {

                    'National_Id': accrs.id_no,
                    'Person_Alternate_Id': accrs.id_no,
                    'Alternative_Id_Type': accrs.alternateid_type_id.saqacode or '533',
                    'Designation_Id':accrs.employer_sdl_no,
                    'Designation_Registration_Number': accrs.etdp_registration_number,
                    'Designation_ETQA_Id':'595',
                    'Designation_Start_Date': self.fix_dates(self.filth_date_gap(accrs.start_date,eddy)),
                    'Designation_End_Date': eddy,
                    'Designation_Structure_Status_Id': '501' if accrs.active else '503', # 501 means registered while 503 means deregistered
                    'Etqa_Decision_Number': ' ',
                    'Provider_Code': accrs.provider_id.saqa_provider_code,
                    'Provider_ETQE_Id': '595',
                    'Filler01': "",
                    'Filler01': "",
                    'Filler03': "",
                    'Date_Stamp':self.fix_dates(accrs.write_date),
                }
                val_items.append(vals)
            if val_items:
                setmis_obj = self.env['inseta.setmis'].create({
                    'name': '401',
                    'file_unique_identifier': filename,
                })
                # for values in val_items:
                #     _logger.info(values)
                #     self.generate_dat(values, header, header_keys, filename)
                self.generate_dat(val_items, header, header_keys, filename)
                filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                    
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.setmis.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
            return attachment, filename
        else:
            raise ValidationError('No Assessor record to generate SETMIS')

    def action_generate_500(self):
        """Generate learnership assessment model record"""

        header = [
                15, 20,3,10,3,20,
                8, 8,20,10,10, 10, 
                8, 30, 10, 10, 10, 15,
                10, 10, 10, 8,
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternate_Id_Type',
            'Learnership_Id',
            'Enrolment_Status_Id',
            'Assessor_Registration_Number',
            'Enrolment_Status_Date',
            'Enrolment_Date',
            'Provider_Code',
            'Provider_Etqa_Id',  # blanket
            'Assessor_Etqa_Id',  # blanket

            'Enrolment_Status_Reason_Id',
            'Most_Recent_Registration_Date',
            'Certificate_Number',
            'Economic_Status_Id',
            'Funding_Id',
            'Cumulative_Spend',
            'OFO_Code',
            'SDL_No',
            'Site_No',
            'Urban_Rural_ID',
            # 'Certification_Date',
            'Date_Stamp',
                       ]
        domain = []
        # domain = [('learner_learnership_id', '!=', False)]
        if self.filter_by == "date": 
            domain += [
                ('create_date', '>=', self.start_date), 
                ('create_date', '<=', self.end_date)
                ]
        # learnership_assessments = self.env['inseta.learner.assessment.detail'].search(domain, limit=self.limit)
        learnership_assessments = self.env['inseta.learner.learnership'].search(domain, limit=self.limit)
        if learnership_assessments: 
            val_items = []
            error_found = []
            filename = self.generate_filename('500')
            attachment = False
            for la in learnership_assessments:
                programme_status = la.programme_status_id 
                def validate_28():
                    error_txt = ""
                    if not la.learner_id.id_no:
                        error_txt += "Learner ID Number not found"
 
                    # codes = [2,3,4,5,7,10,14,15,27,28,29,31,32,49,50,69,70,89]

                    # if not programme_status or programme_status.code not in codes: 
                    #     error_txt += "Programme status with saqa code not found"

                    # if not la.enrollment_date:
                    #     error_txt += "Enrollment_date not found"

                    # if not la.provider_id.saqa_provider_code:
                    #     error_txt += "Provider saqa code not found"

                    if not la.learner_programme_id.programme_code:
                        error_txt += "learner programme code not found"

                    return error_txt
                error = validate_28()
                if error:
                    error_dict = {f'{la.id}': error}
                    error_found.append(error_dict)
                else:
                    vals = {
                        'National_Id': la.learner_id.id_no,
                        'Person_Alternate_Id': la.learner_id.id_no,
                        'Alternate_Id_Type': la.learner_id.alternateid_type_id.saqacode if la.learner_id.alternateid_type_id.saqacode else 533,
                        'Learnership_Id': la.learner_programme_id.programme_code,
                        'Enrolment_Status_Id': la.programme_status_id.code or la.enrollment_status_id.code,
                        'Assessor_Registration_Number': '', #la.assessor_id.id_no or la.assessor_id.employer_sdl_no,
                        'Enrolment_Status_Date': self.compute_date_data(la.achievement_date) if la.programme_status_id.code != 3 else None,  # todo:needs eval based on learner_achievement_type_id
                        'Enrolment_Date': self.compute_date_data(la.enrollment_date),
                        'Provider_Code': self.env['inseta.provider'].browse([la.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Enrolment_Status_Reason_Id': "",
                        'Most_Recent_Registration_Date': self.compute_date_data(la.most_recent_registration_date),
                        'Certificate_Number': la.certificate_number,
                        'Economic_Status_Id': la.socio_economic_status_id.saqacode,
                        'Funding_Id': la.funding_type.saqacode,
                        'Cumulative_Spend': la.cummulative_spend,
                        'OFO_Code': la.ofo_occupation_id.code,
                        'SDL_No': la.provider_id.employer_sdl_no or la.provider_sdl,
                        'Site_No': la.site_no,
                        'Urban_Rural_ID': la.learner_id.physical_urban_rural,
                        # 'Certification_Date': self.compute_date_data(la.certificate_created_date),
                        'Date_Stamp': self.fix_dates(la.write_date),
                    }
                    val_items.append(vals)
            if val_items:
                setmis_obj = self.env['inseta.setmis'].create({
                    'name': '500',
                    'file_unique_identifier': filename,
                })
                # for values in val_items:
                #     _logger.info(values)
                #     self.generate_dat(values, header, header_keys, filename)
                self.generate_dat(val_items, header, header_keys, filename)
                filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.setmis.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
            return attachment, filename
        else:
            raise ValidationError('No learner record to generate SETMIS')

    def action_generate_501(self):
        """Generate qualification assessment model record"""

        header = [
                15, 20,3,10,3,
                20, 3, 8, 8, 3,
                2, 10, 20,10,10,
                20, 10, 8, 30, 4, 
                10, 10, 10, 10, 10, 
                10, 10, 1, 10, 10,
                10, 20, 10, 10, 10, 
                15, 10, 10, 8,
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternate_Id_Type',
            'Qualification_Id',
            'Enrolment_Status_Id',
            'Assessor_Registration_Number',
            'Enrolment_Type_Id',
            'Enrolment_Status_Date',
            'Enrolment_Date',
            'Filler01',
            'Part_Of_Id',
            'Learnership_Id',
            'Provider_Code',
            'Provider_Etqa_Id',  # blanket
            'Assessor_Etqa_Id',  # blanket
            'Filler02',
            'Enrolment_Status_Reason_Id',
            'Most_Recent_Registration_Date',
            'Certificate_Number',
            'Filler03', # 20
            'Filler04',
            'Filler05',
            'Filler06',
            'Economic_Status_Id',
            'Filler07',
            'SDL_No',
            'Filler08',
            'Filler09',
            'Filler10',
            'Filler11', 
            'Site_No',
            'Practical_Provider_Code',
            'Practical_Provider_ETQE_Id',
            'Funding_Id',
            'Cumulative_Spend',
            'OFO_Code',
            'Urban_Rural_ID',
            'Learning_Programme_Type_Id',
            'Date_Stamp',
                       ]
        domain = []
        # domain = [('learner_learnership_id', '!=', False)]
        if self.filter_by == "date": 
            domain += [
                ('create_date', '>=', self.start_date), 
                ('create_date', '<=', self.end_date)
                ]
        # learnership_assessments = self.env['inseta.learner.assessment.detail'].search(domain, limit=self.limit)
        qualification_assessments = self.env['inseta.qualification.learnership'].search(domain, limit=self.limit)
        if qualification_assessments:
            val_items = []
            error_found = []
            filename = self.generate_filename('501')
            attachment = False
            for la in qualification_assessments:
                programme_status = la.programme_status_id 
                def validate_500():
                    error_txt = ""
                    if not la.learner_id.id_no:
                        error_txt += "Learner ID Number not found"
 
                    # codes = [2,3,4,5,7,10,14,15,27,28,29,31,32,49,50,69,70,89]

                    # if not programme_status or programme_status.code not in codes: 
                    #     error_txt += "Programme status with saqa code not found"

                    # if not la.enrollment_date:
                    #     error_txt += "Enrollment_date not found"

                    # if not la.provider_id.saqa_provider_code:
                    #     error_txt += "Provider saqa code not found"

                    if not la.qualification_id.saqa_id:
                        error_txt += "learner programme code not found"

                    return error_txt
                error = validate_500()
                if error:
                    error_dict = {f'{la.id}': error}
                    error_found.append(error_dict)
                else:
                    vals = {
                        'National_Id': la.learner_id.id_no,
                        'Person_Alternate_Id': la.learner_id.id_no,
                        'Alternate_Id_Type': la.learner_id.alternateid_type_id.saqacode if la.learner_id.alternateid_type_id.saqacode else 533,
                        'Qualification_Id': la.qualification_id.saqa_id,
                        'Enrolment_Status_Id': la.programme_status_id.code or la.enrollment_status_id.code,
                        'Assessor_Registration_Number': '', #la.assessor_id.id_no or la.assessor_id.employer_sdl_no,
                        'Enrolment_Type_Id': '',
                        'Enrolment_Status_Date': self.compute_date_data(la.achievement_date) if la.programme_status_id.code != 3 else None,  # todo:needs eval based on learner_achievement_type_id
                        'Enrolment_Date': self.compute_date_data(la.enrollment_date),
                        'Filler01': '',
                        'Part_Of_Id': 1 if not la.qualification_id.qualification_unit_standard_ids else 2,
                        'Learnership_Id': "",
                        'Provider_Code': self.env['inseta.provider'].browse([la.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Filler02': "",
                        'Enrolment_Status_Reason_Id': "",
                        'Most_Recent_Registration_Date': self.compute_date_data(la.most_recent_registration_date),
                        'Certificate_Number': la.certificate_number,
                        'Filler03': '',
                        'Filler04': '',
                        'Filler05': '',
                        'Filler06': '',
                        'Economic_Status_Id': la.socio_economic_status_id.saqacode,
                        'Filler07': "",
                        'SDL_No': la.provider_id.employer_sdl_no or la.provider_sdl,
                        'Filler08': "",
                        'Filler09': "",
                        'Filler10': "",
                        'Filler11': "",
                        'Site_No': la.site_no,
                        'Practical_Provider_Code': "",
                        'Practical_Provider_ETQE_Id': "",
                        'Funding_Id': la.funding_type.saqacode,
                        'Cumulative_Spend': la.cummulative_spend,
                        'OFO_Code': la.ofo_occupation_id.code,
                        'Urban_Rural_ID': la.learner_id.physical_urban_rural,
                        'Learning_Programme_Type_Id': la.qualification_id.qualification_programme_type_id.code,
                        # 'Certification_Date': self.compute_date_data(la.certificate_created_date),
                        'Date_Stamp': self.fix_dates(la.write_date),
                    }
                    val_items.append(vals)
            if val_items:
                setmis_obj = self.env['inseta.setmis'].create({
                    'name': filename,
                    'file_unique_identifier': filename,
                })
                # for values in val_items:
                #     _logger.info(values)
                #     self.generate_dat(values, header, header_keys, filename)
                self.generate_dat(val_items, header, header_keys, filename)
                filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.setmis.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
            return attachment, filename
        else:
            raise ValidationError('No learner record to generate SETMIS')


    def action_export_setmis_data(self):
        self.validate_date_filters()
        attachment = None
        filename = None
        if self.file_type == "100": # Generating providers record
            header = [
                    20, 10, 10, 70, 10, 
                    50,  50, 50, 4, 20, 
                    20, 20, 50, 50, 20,
                    20, 20, 8,8, 20, 10,
                    10, 2, 4, 3,2,
                    6, 2, 2, 6, 50, 50,
                    50, 4, 50, 10, 8
                    ] # 37

            header_keys = [
                    'Provider_Code','Provider_ETQE_Id', 
                    'SIC_Code', 'Provider_Name',
                    'Provider_Type_Id', 'Provider_Postal_Address_1',
                    'Provider_Postal_Address_2','Provider_Postal_Address_3',
                    'Provider_Postal_Address_Code','Provider_Phone_Number',
                    'Provider_Fax_Number', 'Provider_Sars_Number', 
                    'Provider_Contact_Name', 'Provider_Contact_Email_Address',
                    'Provider_Contact_Phone_Number', 'Provider_Contact_Cell_Number',
                    'Provider_Accreditation_Num', 'Provider_Start_Date', 
                    'Provider_End_Date',
                    'Etqa_Decision_Number', 'Provider_Class_Id',
                     'Provider_Status_Id', 'Province_Code',
                     'Country_Code', 'Latitude_Degree', 
                     'Latitude_Minutes', 'Latitude_Seconds',
                     'Longitude_Degree', 'Longitude_Minutes', 
                     'Longitude_Seconds', 'Provider_Physical_Address_1',
                     'Provider_Physical_Address_2', 'Provider_Physical_Address_3',
                      'Provider_Physical_Address_Code', 'Provider_Website_Address', 
                      'SDL_No', 'Date_Stamp',
                ] # 37
            domain = []
            if self.filter_by == "date": 
                domain = [
                    ('create_date', '>=', self.start_date), 
                    ('create_date', '<=', self.end_date)
                    ]
            providers = self.env['inseta.provider'].search(domain, limit=self.limit)
            if providers:
                filename = self.generate_filename('100')
                val_items, file100_errors = [], []
                for provider in providers:
                    eddy = self.fix_dates(self.make_up_date(provider.accreditation_end_date))
                    
                    # Validations
                    # if not provider.saqa_provider_code:
                    #     file100_errors.append("No provider code found")

                    # if not provider.name:
                    #     file100_errors.append("No provider name found")

                    # if file100_errors:
                    #     raise ValidationError(f"{provider.name} has issues listed here [{file100_errors}]")
                    vals = { 
                        'Provider_Code': provider.saqa_provider_code, # .lstrip(' '), # Y
                       'Provider_ETQE_Id': '595', # zz blanket # Y
                       'SIC_Code': provider.sic_code.name or "", 
                       'Provider_Name': provider.name, # Y
                       'Provider_Type_Id': provider.provider_type_id.code, # Y
                       'Provider_Postal_Address_1': provider.street,#.lstrip(' ') if  provider.street else "", # Y
                       'Provider_Postal_Address_2': provider.street2,#.lstrip(' ') if  provider.street2 else "",  # Y
                       'Provider_Postal_Address_3': provider.street3,#.lstrip(' ') if provider.street3 else "",
                       'Provider_Postal_Address_Code': provider.zip,#.lstrip(' ') if  provider.zip else "",
                       'Provider_Phone_Number': provider.phone,#.lstrip(' ') if  provider.phone else "",
                       'Provider_Fax_Number': provider.fax_number, #.lstrip(' ') if provider.fax_number else "",
                       'Provider_Sars_Number': '',
                       'Provider_Contact_Name': '',
                       'Provider_Contact_Email_Address': self.sanitize_email(provider.email),
                       'Provider_Contact_Phone_Number': '',
                       'Provider_Contact_Cell_Number': provider.mobile,
                       'Provider_Accreditation_Num': provider.provider_accreditation_number,
                       'Provider_Start_Date': self.fix_dates(self.filth_date_gap(provider.accreditation_start_date,eddy)),
                       'Provider_End_Date': eddy,
                       # untested make sure
                       'Etqa_Decision_Number': '',  # blank
                       'Provider_Class_Id': provider.provider_class_id.code or 1,  # blanket
                       'Provider_Status_Id': provider.provider_status.code,  # blanket
                       'Province_Code': provider.physical_province_id.saqacode,
                       # maybe change from db id to name or something better
                       'Country_Code': 'ZA',  # blanket ZZ
                       'Latitude_Degree': provider.latitude_degree,  # blank
                       'Latitude_Minutes': provider.latitude_degree,  # blank
                       'Latitude_Seconds': provider.latitude_degree,  # blank
                       'Longitude_Degree': provider.longitude_degree,  # blank
                       'Longitude_Minutes':provider.latitude_degree,  # blank
                       'Longitude_Seconds': provider.latitude_degree,  # blank
                       'Provider_Physical_Address_1': self.sanitize_addrs(provider.street) + ' a',  # zz
                       'Provider_Physical_Address_2': self.sanitize_addrs(provider.street2) + ' a',  # zz
                       'Provider_Physical_Address_3': self.sanitize_addrs(provider.street3),  # blank
                       'Provider_Physical_Address_Code': provider.zip,  # blank
                       'Provider_Website_Address': '',  # blank
                       'SDL_No': provider.employer_sdl_no, 
                       'Date_Stamp': self.fix_dates(provider.write_date),
                       }
                    val_items.append(vals)
                setmis_obj = self.env['inseta.setmis'].create({
                    'name': '100',
                    'file_unique_identifier': filename,
                })
                # for values in val_items:
                #     _logger.info(values)
                #     self.generate_dat(values, header, header_keys, filename)
                self.generate_dat(val_items, header, header_keys, filename)
                filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                 
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.encodestring(byte_data),
                    'type': 'binary',
                    'res_id': self.id,
                    'res_model': 'inseta.setmis.export',
                    'mimetype': 'application/dat'
                    # 'description': f"inseta setmis export: [{filename}] created on {fields.Datetime.now()}"
                })
             
            else:
                raise ValidationError('No Provider record to generate setmis')

        elif self.file_type == "200": # employer
            attachment, filename, error_msg = self.action_generate_200()
            # message_err = '\n'.join([m for m in list(filter(bool, error_msg))])
            # return {
            #     'warning': {
            #         'title': 'IMPORT ERROR',
            #         'message': f"The following record(s) was not successfully imported \n \
            #         {message_err}"
            #     }
            # }

        elif self.file_type == "400":
            attachment, filename = self.action_generate_400()

        elif self.file_type == "401":
            attachment, filename = self.action_generate_401()

        elif self.file_type == "500":
            attachment, filename = self.action_generate_500()

        elif self.file_type == "501":
            attachment, filename = self.action_generate_501()

     
        if attachment and filename:
            return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}/{filename}?download=true',
                    'target': 'new',
                    'nodestroy': False,
                    }
        else:
            raise ValidationError('No File to generate because of validations')

    def generate_dat(self, object_items, header_positions, headers, datfile_name):
        """ 
            object_items = [
            {'name':'Maduka', 'age': '45', 'phone': '09099'},
            {'name':'Solomon', 'age': '54','phone': '09099'}
            ]
            # headers = ['name', 'age', 'phone']
            # header_positions = [10, 30, 40]
        """
        txt = ""
        if len(headers) != len(header_positions):
            raise ValidationError(header_positions) # (f"Length of ({len(headers)}) field size not equal to the Header positions ({len(header_positions)})")
        for dicts in object_items:
            for hp in range(0, len(header_positions)): # header_positions = [10, 30, 40]
                hps = header_positions[hp] #  header_positions[3]   = 30                                                   
                if dicts[headers[hp]]: 
                    txt += f"{str(dicts[headers[hp]]).ljust(hps)[0:header_positions[hp]]}"
                else:
                    txt += f"{''.ljust(hps)[0:header_positions[hp]]}"
            txt += '\n'
        # raise ValidationError(txt)
        with open("var/log/odoo/"+datfile_name, 'w') as f:
            f.write(txt)

    # def generate_dat(self, vald, lens, fields_list, datfile_name):
    #     """
    #     This will take each dictionary and create a dat file.

    #     Usage will be:

    #     from setmis_dat import gendat

    #     gendat(the_dictionary_that_gets_passed_to_create, lengths_according_to_setmis, name_of_dat_file)

    #     One thing to note though, the list that gets generated by the list() function below
    #     may end up being in the wrong order unless we use OrderedDictionaries. Luckily, these
    #     are in the collections module in the standard library and Odoo should not have difficulty
    #     handling them as if they were normal dictionaries.
    #     """
    #     fmt = ""
    #     endtup = []
    #     vall = list(vald.values())

    #     for x in range(0, len(lens)): 
    #         fmt += "%-*s"
    #         endtup.append(lens[x]) 
    #         if len(lens) != len(vall):
    #             raise ValidationError('field length and length list are not same len ' + str(len(lens)) + str(len(vall)))
    #         try:
    #             if not vald[fields_list[x]]:
    #                 endtup.append(''[0:10])
    #                 # valu = vald[fields_list[x]]
 
    #             elif type(vald[fields_list[x]]) == int:
    #                 valu = vald[fields_list[x]]
    #                 endtup.append(str(valu)[0:len(str(valu))]) 
    #             else:
    #                 valu = vald[fields_list[x]]
    #                 # valu = valu.encode("ascii")
    #                 endtup.append(valu[0:len(valu)])

    #         except UnicodeEncodeError:
    #             if not vald[fields_list[x]]:
    #                 endtup.append(''[0:len(valu)])
    #             elif type(vald[fields_list[x]]) == int:
    #                 valu = vald[fields_list[x]]
    #                 endtup.append(str(valu)[0:len(valu)])
    #             else:
    #                 valu = "CHEESE"
    #                 endtup.append(valu[0:len(valu)])
                
    #     fmt += "\r\n"
    #     try:
    #         # with open("/var/log/odoo/"+datfile_name, 'a') as f:
    #         # for local testing create a directory to use
    #         with open("var/log/odoo/"+datfile_name, 'a') as f:
    #             f.write(fmt % tuple(endtup))
    #     except IOError:
    #         with open("var/log/odoo/"+datfile_name, 'w') as f:
    #             f.write(fmt % tuple(endtup))

