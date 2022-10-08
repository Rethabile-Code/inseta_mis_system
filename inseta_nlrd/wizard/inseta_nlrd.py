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
import os, zipfile
import shutil
from collections import OrderedDict as OD

_logger = logging.getLogger(__name__)

dt_str = datetime.strftime(datetime.today(), '%Y-%m-%d')
filename_suffix = re.sub('-', '', dt_str) # 20210121

_FOLDER_NAME = filename_suffix
_PROVIDER_CODE = []
_LEARNER_CODE = []
_ASSESSOR_NUM = []
_QUALIFICATION_CODE = []
_LEARNERSHIP_CODE = []
_PROGRAMME_STATUS_CODE = ['2','3','4','5','7','10','14','15','27','28','29','31','32','49','50','69','70','89']
_DISABILITY_STATUS_CODE = [
'01',
'02',
'03',
'04',
'05',
'06',
'07',
'09',
'N',
'N - was 01',
'N - was 02',
'N - was 03',
'N - was 04',
'N - was 05',
'N - was 06',
'N - was 07',
'N - was 09',
]
_HOME_LANGUAGE_CODE = [
'Afr',
'Eng',
'Nde',
'Oth',
'SASL',
'Sep',
'Ses',
'Set',
'Swa',
'Tsh',
'U',
'Xho',
'Xit',
'Zul',
]
_NONE = ["N/A", None, False, 'false', 'none', 'n/a', ""]

class InsetaNLRD(models.Model):
    _name = 'inseta.nlrd'
    _description  = "NLRD GENERATED"
    
    name = fields.Char('File')
    file_unique_identifier = fields.Char('File Unique Idenitifier')


class InsetaNLRDExport(models.TransientModel):
    _name = 'inseta.nlrd.export'
    _description  = "NLRD EXPORT Wizard"

    dat_file = fields.Binary('Download DAT file', filename='filename', readonly=True)
    filename = fields.Char('DAT File')
    file_type = fields.Selection([
        # ('21', 'Providers (File 21)'),
        # ('24', 'Providers Accreditation (File 24)'),
        # ('25', 'Person Information (File 25)'),
        # ('26', 'Person Designation (File 26)'),
        # ('27', 'NQF Designation Registration- Assessor Registration (File 27)'),
        # ('28', 'Learnership Enrollment  / Achievement (File 28)'),
        # ('29', 'Qualification Enrollment / Achievement (File 29)'),
        # ('30', 'Unit Standard Enrollment / Achievement (File 30)'),
        ('all', 'All'),

    ], required=True, default="all")
    filter_by = fields.Selection([
        ('all', 'All records'),
        ('date', 'Date'),
    ], required=True, default='all', string="Filter by", help="Start Date")

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

    def validate_a_z_name_values(self, string):
        """Ensures only text wwith match a-z, A-Z is inputed"""
        pattern = re.compile("[A-Za-z]+")
        if type(string) == str:
            if pattern.fullmatch(string) is not None:
                return True
            else:
                return False
        else:
            return False

    def validate_null_fields(self, string):
        """Ensures values such as N/A , None, False is not captured"""
        if string in _NONE:
            return ""
        else:
            return string

    def validate_non_alphabet_numeric_text(self, string):
        """Ensures only text with match a-z, A-Z, 0-9 is inputed"""
        pattern = re.compile("[A-Za-z0-9]+")
        if type(string) == str:
            if pattern.fullmatch(string) is not None:
                return string
            else:
                return ""
        else:
            return ""

    def validate_address_text(self, string):
        """Ensures only text with match a-z, A-Z, 0-9 is inputed"""
        pattern = re.compile("[A-Za-z0-9]+")
        if string and type(string) == str:
            if pattern.fullmatch(string) is not None:
                return string
            else:
                return ""
        else:
            return ""

    def validate_postal_code(self, string):
        """Ensures only text with match 0-9 is inputed"""
        pattern = re.compile("[0-9]+")
        if type(string) == str:
            if pattern.fullmatch(string) is not None:
                return string
            else:
                return False
        else:
            return False 
    
    def validate_home_language_code(self, string):
        if string and string in _HOME_LANGUAGE_CODE:
            return string
        else:
            return "Oth"

    def validate_province_code(self, string):
        """Ensures only text with match a-z, A-Z, 0-9 is inputed"""
        pattern = re.compile("[A-Za-z0-9]+")
        if type(string) == str:
            if pattern.fullmatch(string) is not None:
                return True
            else:
                return False
        else:
            return False

    def fix_dates(self, date):
        dt_return = '19900413'
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

    def generate_filename(self, name=True):
        filename = f'INSU{name}220101' 
        dt_str = datetime.strftime(datetime.today(), '%Y-%m-%d')
        filename_suffix = re.sub('-', '', dt_str) # 20210121 
        suffix_result = filename_suffix[2:] # 210121
        # YY,MM,DD = filename_suffix[2:4], filename_suffix[4:6], filename_suffix[6:]
        if name:
            nlrd_last_gen = self.env['inseta.nlrd'].search([('name', '=', name)])
            if nlrd_last_gen:
                nlrd_filename = nlrd_last_gen[-1].file_unique_identifier[4:6] # INSE121111 => 12
                cnvrt_nlrd_filename_int = int(nlrd_filename) + 1 # 12 + 1 => 13
                filename = f"INSU{name}{suffix_result}.dat"
        else:
            filename = f"{filename_suffix}"
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
        
    def action_generate_21(self): # PROVIDER
        header = [
                    20, 10,10,128, 10,50, 50, 50, 4,20,20, 20, 50,50,20,
                    20, 20, 8, 8,20,10, 10, 2, 4, 3, 2, 6, 2,2,6, 50, 50,
                    50, 4,50,8,
                    ] 
        header_keys = [
                'Provider_Code', 'Etqa_Id', 'Std_Industry_Class_Code', 'Provider_Name',
                'Provider_Type_Id', 'Provider_Address_1','Provider_Address_2','Provider_Address_3',
                'Provider_Postal_Code', 'Provider_Phone_Number','Provider_Fax_Number','Provider_Sars_Number',
                'Provider_Contact_Name', 'Provider_Contact_Email_Address','Provider_Contact_Phone_Number',
                'Provider_Contact_Cell_Number','Provider_Accreditation_Num', 'Provider_Accredit_Start_Date',
                'Provider_Accredit_End_Date', 'Etqa_Decision_Number','Provider_Class_Id',
                'Structure_Status_Id', 'Province_Code','Country_Code',
                'Latitude_Degree', 'Latitude_Minutes', 'Latitude_Seconds',
                'Longitude_Degree', 'Longitude_Minutes', 'Longitude_Seconds',
                'Provider_Physical_Address_1','Provider_Physical_Address_2', 'Provider_Physical_Address_Town', 
                'Provider_Phys_Address_Postcode','Provider_Web_Address', 'Date_Stamp',
            ] # 36
        domain = []
        if self.filter_by == "date": 
            domain = [
                ('create_date', '>=', self.start_date), 
                ('create_date', '<=', self.end_date)
                ]
        providers = (self.env['inseta.provider'].search(domain, limit=self.limit))
        filename = self.generate_filename('21')
        attachment = False
        error_found = []
        if providers:
            val_items = []
            for provider in providers:
                eddy = self.fix_dates(self.make_up_date(provider.accreditation_end_date))
                def validate_21():
                    error_txt = ""
                    if not provider.saqa_provider_code:
                        error_txt += f"{provider.id} does not have SaQa provider code, "

                    if provider.saqa_provider_code in _NONE:
                        error_txt += f"{provider.id} does not have correct SaQa provider code, "

                    if not provider.trade_name:
                        error_txt += f"{provider.id} does not have provider name, "

                    if not provider.provider_type_id:
                        error_txt += f"{provider.id or provider.name} does not have provider type id, "

                    if not provider.street:
                        error_txt += f"{provider.trade_name or provider.name} does not have address 1 code, "

                    if not provider.street2:
                        error_txt += f"{provider.trade_name or provider.name} does not have address 2 code, "

                    if not provider.provider_status.code:
                        error_txt += f"{provider.trade_name or provider.name} does not have status code, "


                    if not provider.physical_province_id.saqacode:
                        error_txt += f"{provider.trade_name or provider.name} does not have province code, "

                    if not provider.provider_type_id.code in ['2','3','4','5','500']:
                        error_txt += f"{provider.trade_name} provider_type_id code must be within in ['2','3','4','5','500'], "

                    if not self.validate_postal_code(provider.zip):
                        error_txt += f"{provider.trade_name} provider zip must be within four characters  0-9"

                    return error_txt
                 
                error = validate_21()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    latitude_degree = ""
                    latitude_minutes = ""
                    latitude_seconds = ""
                    longitude_degree = ""
                    longitude_minutes = ""
                    longitude_seconds = ""
                    _PROVIDER_CODE.append(provider.saqa_provider_code)
                    if provider.latitude_degree:
                        if not provider.latitude_degree.startswith('-'):
                            pass
                            # error_txt += f"{provider.trade_name} has invalid latitude degree which much must start with (-), "
                        
                        if provider.latitude_degree[0:2].isdigit():
                            if int(provider.latitude_degree[0:2]) < -22:
                                latitude_degree = provider.latitude_degree

                        if not (provider.latitude_minutes and provider.latitude_seconds):
                            pass
                            # error_txt += f"{provider.trade_name} Does not have latitude minutes and latitude seconds, "
                        
                        if provider.latitude_minutes:
                            if provider.latitude_minutes not in range(16, 34):
                                pass
                                # error_txt += f"{provider.trade_name} latitude minutes must be in range of 16 - 33, "

                    if provider.longitude_degree:
                        if not provider.longitude_degree.startswith('-'):
                            pass
                            # error_txt += f"{provider.trade_name} has invalid longitude degree which much must start with (-), "
                        
                        if provider.longitude_degree:
                            if provider.longitude_degree[0:2].isdigit():
                                if int(provider.longitude_degree[0:2]) < -22:
                                    longitude_degree = provider.longitude_degree 

                        if not (provider.longitude_minutes and provider.longitude_seconds):
                            pass
                            # error_txt += f"{provider.trade_name} Does not have longitude degree and longitude seconds, "

                        if provider.longitude_minutes:
                            if provider.longitude_minutes.isdigit():
                                if provider.longitude_minutes not in range(16, 34):
                                    pass 
                                    # error_txt += f"{provider.trade_name} longitude minutes must be in range of 16 - 33, "

                    # _provider code stores the code so that file 24 and 26 
                    #  must be generated if the provider code exist in _PROVIDER CODE
                    vals = {
                        'Provider_Code': provider.saqa_provider_code if provider.saqa_provider_code not in _NONE else "", # Y
                        'Etqa_Id': 595, # zz blanket # Y
                        'Std_Industry_Class_Code': provider.sic_code.siccode or provider.sic_code.saqacode, 
                        'Provider_Name': provider.trade_name if provider.trade_name not in _NONE else "", # Y
                        'Provider_Type_Id': provider.provider_type_id.code if provider.provider_type_id.code not in _NONE else "", # Y
                        'Provider_Address_1': provider.street if provider.street not in _NONE else '123 Blom street', # Y
                        'Provider_Address_2': provider.street2 if provider.street2 not in _NONE else 'Pretoria',  # Y
                        'Provider_Address_3': provider.street3 if provider.street3 not in _NONE else "",
                        'Provider_Postal_Code': provider.zip if provider.zip not in _NONE else "",
                        'Provider_Phone_Number': provider.phone if provider.phone not in _NONE else "",
                        'Provider_Fax_Number': provider.fax_number if provider.fax_number not in _NONE else "",
                        'Provider_Sars_Number': '',
                        'Provider_Contact_Name': '',
                        'Provider_Contact_Email_Address': self.sanitize_email(provider.email) if provider.email not in _NONE else "",
                        'Provider_Contact_Phone_Number': '',
                        'Provider_Contact_Cell_Number': provider.mobile if provider.mobile not in ["N/A"] else "",
                        'Provider_Accreditation_Num': provider.provider_accreditation_number if provider.provider_accreditation_number not in _NONE else "",
                        'Provider_Accredit_Start_Date': self.fix_dates(self.filth_date_gap(provider.accreditation_start_date,eddy)) if provider.accreditation_start_date not in _NONE else "",
                        'Provider_Accredit_End_Date': eddy,
                        # untested make sure
                        'Etqa_Decision_Number': '',  # blank
                        'Provider_Class_Id': provider.provider_class_id.code if provider.provider_class_id.code not in _NONE else 1,  # blanket
                        'Structure_Status_Id': int(provider.provider_status.code) if provider.provider_status.code not in _NONE else 503,  # blanket
                        'Province_Code': provider.physical_province_id.saqacode if not self.validate_province_code(provider.physical_province_id.saqacode) else "N", #pers.physical_province_id.saqacode or "",  # y
                        # maybe change from db id to name or something better
                        'Country_Code': 'ZA',  # blanket ZZ
                        'Latitude_Degree': "", #latitude_degree,  # blank
                        'Latitude_Minutes': "", #provider.latitude_minutes ,  # blank
                        'Latitude_Seconds':"", # provider.latitude_seconds,  # blank
                        'Longitude_Degree':"", # longitude_degree,
                        'Longitude_Minutes':"", #provider.longitude_minutes,  # blank
                        'Longitude_Seconds': "", #provider.longitude_seconds,  # blank
                        'Provider_Physical_Address_1': self.sanitize_addrs(provider.street) + ' a' if provider.street not in _NONE else "",  # zz
                        'Provider_Physical_Address_2': self.sanitize_addrs(provider.street2) + ' a' if provider.street2 not in _NONE else "",  # zz
                        'Provider_Physical_Address_Town': '',  # blank
                        'Provider_Phys_Address_Postcode': '',  # blank
                        'Provider_Web_Address': '',  # blank
                        'Date_Stamp': self.fix_dates(provider.write_date),
                    }
                    val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '21',
                    'file_unique_identifier': filename,
                })
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                 
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.encodestring(byte_data),
                    'type': 'binary',
                    'res_id': self.id,
                    'res_model': 'inseta.nlrd.export',
                    'mimetype': 'application/dat'
                    # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                })
        return attachment, filename, error_found
        # else:
        #     raise ValidationError('No Provider record to generate NLRD')

    def action_generate_24(self): # PROVIDER ACCREDITATION
        header = [
                10, 10,10,20,10,20,
                1, 8,8,20,10,8,
                ]
        header_keys = [
            'Learnership_Id',
            'Qualification_Id',
            'Unit_Standard_Id',  # maybe later
            'Provider_Code',
            'Provider_Etqa_Id',
            'Provider_Accreditation_Num',
            'Provider_Accredit_Assessor_Ind',
            'Provider_Accred_Start_Date',
            'Provider_Accred_End_Date',
            'Etqa_Decision_Number',
            'Provider_Accred_Status_Code',
            'Date_Stamp', 
        ] 
        domain = [('saqa_provider_code', 'in', _PROVIDER_CODE),]
        # if self.filter_by == "date": 
        #     domain = [
        #         ('start_date', '>=', self.start_date), 
        #         ('start_date', '<=', self.end_date),
        #         ('saqa_provider_code', 'in', _PROVIDER_CODE)
        #         ]
        filename = self.generate_filename('24')
        attachment = False
        error_found = []
        provider_accreditation = (self.env['inseta.provider.accreditation'].search(domain, limit=self.limit))
        if provider_accreditation:
            val_items = []
            rec = []
            for accrs in provider_accreditation:
                # Unit standard Accreditation
                def validate_24():
                    error_txt = ""
                    if not accrs.start_date:
                        error_txt += f"{accrs.provider_name} does not have start date"
                    if not any([accrs.unit_standard_ids, accrs.qualification_ids, accrs.learner_programmes_ids]):
                        error_txt += f"{accrs.provider_name} does not have qualification_ids or unit_standard_ids or learner_programmes_ids"
                    return error_txt
                error = validate_24()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    for unit in accrs.unit_standard_ids:
                        eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                        vals = {
                            'Learnership_Id': '',
                            'Qualification_Id': '',
                            'Unit_Standard_Id': unit.code if unit.code not in _NONE else "",  # maybe later
                            'Provider_Code': accrs.saqa_provider_code if accrs.saqa_provider_code not in _NONE else "",
                            'Provider_Etqa_Id': 595,
                            'Provider_Accreditation_Num': accrs.accreditation_number if accrs.accreditation_number not in _NONE else "",
                            'Provider_Accredit_Assessor_Ind': '',
                            'Provider_Accred_Start_Date': self.fix_dates(self.filth_date_gap(accrs.start_date,eddy)),
                            'Provider_Accred_End_Date': eddy,
                            'Etqa_Decision_Number': '',
                            'Provider_Accred_Status_Code': self.accredit_status_to_code('Active') if accrs.active else self.accredit_status_to_code('Inactive'),
                            'Date_Stamp': self.fix_dates(accrs.write_date),
                        }
                        val_items.append(vals)
                    # Learnership Accreditation
                    for lrn in accrs.learner_programmes_ids:
                        eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                        vals = {
                            'Learnership_Id': lrn.learnership_saqa_id,
                            'Qualification_Id': '',
                            'Unit_Standard_Id': '',  # maybe later
                            'Provider_Code': accrs.saqa_provider_code if accrs.saqa_provider_code not in _NONE else "",
                            'Provider_Etqa_Id': 595,
                            'Provider_Accreditation_Num': accrs.accreditation_number or "",
                            'Provider_Accredit_Assessor_Ind': '',
                            'Provider_Accred_Start_Date': self.fix_dates(self.filth_date_gap(accrs.start_date,eddy)),
                            'Provider_Accred_End_Date': eddy,
                            'Etqa_Decision_Number': '',
                            'Provider_Accred_Status_Code': self.accredit_status_to_code('Active') if accrs.active else self.accredit_status_to_code('Inactive'),
                            'Date_Stamp':  self.fix_dates(accrs.write_date),
                        }
                        val_items.append(vals)

                    # Qualification Accreditation
                    for qa in accrs.qualification_ids:
                        eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                        vals = {
                            'Learnership_Id': "",
                            'Qualification_Id': qa.saqa_id if qa.saqa_id not in _NONE else "",
                            'Unit_Standard_Id': '',  # maybe later
                            'Provider_Code': accrs.saqa_provider_code if accrs.saqa_provider_code not in _NONE else "",
                            'Provider_Etqa_Id': 595,
                            'Provider_Accreditation_Num': accrs.accreditation_number if accrs.accreditation_number not in _NONE else "",
                            'Provider_Accredit_Assessor_Ind': '', # 'Y',
                            'Provider_Accred_Start_Date': self.fix_dates(self.filth_date_gap(accrs.start_date,eddy)),
                            'Provider_Accred_End_Date': eddy,
                            'Etqa_Decision_Number': '',
                            'Provider_Accred_Status_Code': self.accredit_status_to_code('Active') if accrs.active else self.accredit_status_to_code('Inactive'),
                            'Date_Stamp': self.fix_dates(accrs.write_date),
                        }
                        val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '24',
                    'file_unique_identifier': filename,
                })
                self.generate_dat(val_items, header, header_keys, filename)
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                    
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
        return attachment, filename, error_found

    def validate_person_id(self, pers):
        alternate_type = 533
        Person_Id = ""
        if pers:
            if pers.alternateid_type_id.saqacode in _NONE:
                alternate_type = 533
            else:
                alternate_type = pers.alternateid_type_id.saqacode
                Person_Id = pers.id_no
            if alternate_type == 533:
                Person_Id = ""
            else:
                Person_Id = pers.id_no
        return Person_Id, alternate_type

    def action_generate_25(self):
        """Generate Learner / person (res.partner) model record"""
        header = [
                15, 20,3,10,3,
                10, 1,10,2,10,
                45,26,50,10,8,
                50,50,50,50,50,
                50,4,4,20,20,
                20,50,2,20,10,
                45,20,3,20,10,
                2,2,2,2,2,2,8
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
                        'Socioeconomic_Status_Code',  # y
                        'Disability_Status_Code', # 10
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
                        'Provider_Etqa_Id',  # 30 c blanket 
                        'Person_Previous_Lastname',
                        'Person_Previous_Alternate_Id',
                        'Person_Previous_Alternative_Id_Type',  # c
                        'Person_Previous_Provider_Code',
                        'Person_Previous_Provider_Etqe_Id',  # c
                        'Seeing_Rating_Id',
                        'Hearing_Rating_Id',
                        'Communicating_Rating_Id',
                        'Walking_Rating_Id',
                        'Remembering_Rating_Id',
                        'Self_Care_Rating_Id', # 40
                        'Date_Stamp',  # y
                       ]
        # ('contact_type', 'in', ['employer', 'moderator', 'assessor', 'sdf', 'others', 'learner'])
        # if self.filter_by == "date": 
        #     domain += [
        #         ('create_date', '>=', self.start_date), 
        #         ('create_date', '<=', self.end_date)
        #         ]
        domain = [('id_no', '!=', False)]
        person = (self.env['inseta.learner'].search(domain, limit=self.limit))
        error_found = []
        attachment = False
        filename = self.generate_filename('25')
        if person:
            val_items = [] 
            alternateid_type_ids = [
                '521', '527', '529',
                '531', '533', '535',
                '537', '538', '539', 
                '540', '541', '561', 
                '565'
                ]
            for pers in person:
                def validate_25():
                    error_txt = ""
                    if not pers.equity_id.saqacode:
                        error_txt += f"{pers.id} does not have Equity code"
                    
                    if pers.provider_id.saqa_provider_code:
                        if pers.provider_id.saqa_provider_code not in _PROVIDER_CODE:
                            error_txt += f"{pers.id} does not have matching SAQA provider code"

                    if not pers.home_language_id.code:
                        error_txt += f"{pers.id} does not have home Language id code"

                    if not pers.gender_id:
                        error_txt += f"{pers.id} does not have gender code"
                     
                    if not pers.id_no:
                        error_txt += f"{pers.id} does not have National ID"

                    if not len(pers.id_no) != 15:
                        error_txt += f"{pers.id} National ID has incorrect number of character. Must be 15"

                    if pers.alternateid_type_id.saqacode and not pers.id_no:
                        error_txt += f"{pers.id} has alternatie id but Person national id does not exist"
                    
                    if pers.alternateid_type_id.saqacode in ['537'] and not pers.provider_id.saqa_provider_code:
                        error_txt += f"{pers.id} alternate id with 537 (student number) must have a provider code"

                    if pers.alternateid_type_id.saqacode:
                        if pers.alternateid_type_id.saqacode not in alternateid_type_ids:
                            error_txt += """alternateid type id code must be in [
                                '521', '527', '529',
                                '531', '533', '535',
                                '537', '538', '539', 
                                '540', '541', '561', 
                                '565']"""

                    # if not pers.equity_id.saqacode:
                    #     error_txt += "equity code not found"
                    # if not pers.citizen_resident_status_id.saqacode:
                    #     error_txt += "citizen_resident_status code not found"
                     
                    if not pers.socio_economic_status_id.saqacode:
                        error_txt += "socio economic status code not found"

                    if not pers.disability_id.saqacode:
                        error_txt += "disability code not found"

                    if not self.validate_a_z_name_values(pers.first_name):
                        error_txt += f"{pers.id} does not have first name, "

                    if not self.validate_a_z_name_values(pers.last_name):
                        error_txt += f"{pers.id} does not have last name, "

                    if not pers.birth_date:
                        error_txt += f"{pers.id} does not have birth date, "

                    # if not pers.provider_id.saqa_provider_code:
                    #     error_txt += "provider saqa Code not found"

                    return error_txt
                error = validate_25()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    _LEARNER_CODE.append(pers.id_no)
                    # eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                    
                    vals = {
                        'National_Id': pers.id_no,
                        'Person_Alternate_Id': self.validate_person_id(pers)[0], #pers.id_no,  # c
                        'Alternate_Id_Type': self.validate_person_id(pers)[1], #pers.alternateid_type_id.saqacode if pers.id_no and pers.alternateid_type_id.saqacode not in _NONE else 533,  # req
                        'Equity_Code': pers.equity_id.saqacode if pers.equity_id.saqacode not in _NONE else "",  # y
                        'Nationality_Code': pers.nationality_id.saqacode if pers.nationality_id.saqacode not in _NONE else "",  # y
                        'Home_Language_Code': self.validate_home_language_code(pers.home_language_id.code), # pers.home_language_id.code or self.lang_to_code(pers.home_language_id.name) if pers.home_language_id.code not in _NONE else "",  # y
                        'Gender_Code': self.gender_to_code(pers.gender_id.name),  # y
                        'Citizen_Resident_Status_Code': pers.citizen_resident_status_id.saqacode if pers.citizen_resident_status_id.saqacode not in _NONE else "",
                        'Socioeconomic_Status_Code': pers.socio_economic_status_id.saqacode or "" if pers.socio_economic_status_id.saqacode not in _NONE else "",  # y
                        'Disability_Status_Code': pers.disability_id.saqacode or "" if pers.disability_id.saqacode not in _DISABILITY_STATUS_CODE else 'N',  # y probably needs dict def
                        'Person_First_Name': pers.first_name if self.validate_a_z_name_values(pers.first_name) else "",  # y
                        'Person_Last_Name': pers.last_name if self.validate_a_z_name_values(pers.last_name) else "",  # y
                        'Person_Middle_Name': pers.middle_name if self.validate_a_z_name_values(pers.middle_name) else "",
                        'Person_Title': '',
                        'Person_Birth_Date': self.compute_date_data(pers.birth_date),
                        'Person_Home_Address_1': self.validate_address_text(pers.street),
                        'Person_Home_Address_2': self.validate_address_text(pers.street2), #pers.street2 or "",
                        'Person_Home_Address_3':  self.validate_address_text(pers.street3), #pers.street3 or "",
                        'Person_Postal_Address_1':  self.validate_address_text(pers.postal_address1), #pers.postal_address1 or "",
                        'Person_Postal_Address_2':  self.validate_address_text(pers.postal_address2), # pers.postal_address2 or "", # 20
                        'Person_Postal_Address_3': self.validate_address_text(pers.postal_address3), # pers.postal_address3 or "",
                        'Person_Home_Addr_Postal_Code': pers.physical_code if self.validate_address_text(pers.physical_code) else "", # pers.physical_code or "",
                        'Person_Postal_Addr_Post_Code': pers.postal_code if self.validate_address_text(pers.postal_code) else "", # pers.postal_code or "",
                        'Person_Phone_Number': self.validate_address_text(pers.phone), #pers.phone or "",
                        'Person_Cell_Phone_Number': self.validate_address_text(pers.mobile), # pers.mobile or "",
                        'Person_Fax_Number': self.validate_address_text(pers.fax_number), #pers.fax_number or "",
                        'Person_Email_Address': self.validate_null_fields(pers.email), #pers.email or "",
                        'Province_Code': pers.physical_province_id.saqacode if not self.validate_province_code(pers.physical_province_id.saqacode) else "N", #pers.physical_province_id.saqacode or "",  # y
                        'Provider_Code': self.validate_non_alphabet_numeric_text(pers.provider_id.saqa_provider_code), #pers.provider_id.saqa_provider_code or "",  # c
                        'Provider_Etqa_Id': 595,  # 30 c blanket
                        'Person_Previous_Lastname': "",
                        'Person_Previous_Alternate_Id': '',
                        'Person_Previous_Alternative_Id_Type': '',  # c
                        'Person_Previous_Provider_Code': '',
                        'Person_Previous_Provider_Etqe_Id': '',  # c
                        'Seeing_Rating_Id': '',
                        'Hearing_Rating_Id': '',
                        'Communicating_Rating_Id': '',
                        'Walking_Rating_Id': '',
                        'Remembering_Rating_Id': '',
                        'Self_Care_Rating_Id': '',
                        'Date_Stamp': self.fix_dates(pers.write_date),  # y
                        }
                    val_items.append(vals)
            assessor_objs = self.env['inseta.assessor'].search([])
            for assessor in assessor_objs:
                def validate_25():
                    error_txt = ""
                     
                    if not assessor.equity_id.saqacode:
                        error_txt += f"{assessor.id} does not have Equity code"

                    if not assessor.home_language_id.code:
                        error_txt += f"{assessor.id} does not have home Language id code"

                    if not assessor.gender_id:
                        error_txt += f"{assessor.id} does not have gender code"
                        
                    if not assessor.id_no:
                        error_txt += f"{assessor.id} does not have National ID"

                    if assessor.alternateid_type_id.saqacode:
                        if assessor.alternateid_type_id.saqacode not in alternateid_type_ids:
                            error_txt += """alternateid type id code must be in [
                                '521', '527', '529',
                                '531', '533', '535',
                                '537', '538', '539', 
                                '540', '541', '561', 
                                '565']"""
 
                    if not assessor.socio_economic_status_id.saqacode:
                        error_txt += "socio economic status code not found"

                    if not assessor.disability_id.saqacode:
                        error_txt += "disability code not found"

                    if not assessor.first_name:
                        error_txt += f"{assessor.id} does not have first name, "

                    if not assessor.last_name:
                        error_txt += f"{assessor.id} does not have last nam, "

                    if not assessor.birth_date:
                        error_txt += f"{assessor.id} does not have birth date, "
 
                    return error_txt
                error = validate_25()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    _LEARNER_CODE.append(assessor.id_no)
                    # eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                    vals = {
                        'National_Id': assessor.id_no,
                        'Person_Alternate_Id': self.validate_person_id(assessor)[0], #assessor.id_no, #assessor.id_no,  # c
                        'Alternate_Id_Type': self.validate_person_id(assessor)[1], #assessor.alternateid_type_id.saqacode if assessor.id_no and assessor.alternateid_type_id.saqacode not in _NONE else 533,
                        # assessor.alternateid_type_id.saqacode if assessor.alternateid_type_id.saqacode not in _NONE else 533,  # req
                        'Equity_Code': self.validate_null_fields(assessor.equity_id.saqacode),  # y
                        'Nationality_Code':self.validate_null_fields(assessor.nationality_id.saqacode),   # y
                        'Home_Language_Code': self.validate_home_language_code(assessor.home_language_id.code), #assessor.home_language_id.code or self.lang_to_code(assessor.home_language_id.name) if assessor.alternateid_type_id.saqacode not in _NONE else "",  # y
                        'Gender_Code': self.gender_to_code(assessor.gender_id.name),  # y
                        'Citizen_Resident_Status_Code': self.validate_null_fields(assessor.citizen_resident_status_id.saqacode),  #assessor.citizen_resident_status_id.saqacode or "",
                        'Socioeconomic_Status_Code': self.validate_null_fields(assessor.socio_economic_status_id.saqacode),  #assessor.socio_economic_status_id.saqacode or "",  # y
                        'Disability_Status_Code': assessor.disability_id.saqacode or "" if assessor.disability_id.saqacode not in _DISABILITY_STATUS_CODE else 'N',#  self.validate_null_fields(assessor.disability_id.saqacode),  #assessor.disability_id.saqacode or "",  # y probably needs dict def
                        'Person_First_Name': self.validate_null_fields(assessor.first_name),  #assessor.first_name or "",  # y
                        'Person_Last_Name': self.validate_null_fields(assessor.last_name),  # assessor.last_name or "",  # y
                        'Person_Middle_Name': self.validate_null_fields(assessor.middle_name),  # assessor.middle_name or "",
                        'Person_Title': '',
                        'Person_Birth_Date': self.compute_date_data(assessor.birth_date),
                        'Person_Home_Address_1': self.validate_address_text(assessor.street),  #assessor.street or "",
                        'Person_Home_Address_2': self.validate_address_text(assessor.street2),  #assessor.street2 or "",
                        'Person_Home_Address_3': self.validate_address_text(assessor.street3),  #assessor.street3 or "",
                        'Person_Postal_Address_1': self.validate_address_text(assessor.postal_address1),  #assessor.postal_address1 or "",
                        'Person_Postal_Address_2': self.validate_address_text(assessor.postal_address2),  #assessor.postal_address2 or "", # 20
                        'Person_Postal_Address_3': self.validate_address_text(assessor.postal_address3),  #assessor.postal_address3 or "",
                        'Person_Home_Addr_Postal_Code': assessor.physical_code if self.validate_postal_code(assessor.physical_code) else "", #  self.validate_null_fields(assessor.physical_code),  #assessor.physical_code or "",
                        'Person_Postal_Addr_Post_Code': assessor.postal_code if self.validate_postal_code(assessor.postal_code) else "", #self.validate_null_fields(assessor.postal_code),  #assessor.postal_code or "",
                        'Person_Phone_Number': self.validate_address_text(assessor.phone),  #assessor.phone or "",
                        'Person_Cell_Phone_Number': self.validate_address_text(assessor.mobile),  #assessor.mobile or "",
                        'Person_Fax_Number': self.validate_address_text(assessor.fax_number),  # assessor.fax_number or "",
                        'Person_Email_Address': self.validate_null_fields(assessor.email),  #assessor.email or "",
                        'Province_Code': assessor.physical_province_id.saqacode if not self.validate_province_code(assessor.physical_province_id.saqacode) else "N", #pers.physical_province_id.saqacode or "",  # y
                        # self.validate_null_fields(assessor.physical_province_id.saqacode),  #assessor.physical_province_id.saqacode or "",  # y
                        'Provider_Code': '', #assessor.provider_id.saqa_provider_code or "",  # c
                        'Provider_Etqa_Id': 595,  # 30 c blanket
                        'Person_Previous_Lastname': "",
                        'Person_Previous_Alternate_Id': '',
                        'Person_Previous_Alternative_Id_Type': '',  # c
                        'Person_Previous_Provider_Code': '',
                        'Person_Previous_Provider_Etqe_Id': '',  # c
                        'Seeing_Rating_Id': '',
                        'Hearing_Rating_Id': '',
                        'Communicating_Rating_Id': '',
                        'Walking_Rating_Id': '',
                        'Remembering_Rating_Id': '',
                        'Self_Care_Rating_Id': '',
                        'Date_Stamp': self.fix_dates(assessor.write_date),  # y
                        }
                    val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '25',
                    'file_unique_identifier': filename,
                })
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
        return attachment, filename, error_found
            # else:
            #     if len(error_found) > 1:
            #         message = error_found #'\n'.join(messages)
            #         return self.confirm_notification(message)
        # else:
        #     raise ValidationError('No learner record to generate NLRD')

    def action_generate_26(self):
        """Generate Assessor model record"""
        header = [
                15, 20,3,5,20,10,
                8, 8,10,20,20,10,
                8,
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
            'Structure_Status_Id',
            'Etqa_Decision_Number',
            'Provider_Code',
            'Provider_ETQA_ID',
            'Date_Stamp', 
        ]
        val = {
            }
        domain = [
            ('id_no', 'in', _LEARNER_CODE)
            ]
        if self.filter_by == "date": 
            domain = [
                ('start_date', '>=', self.registration_start_date), 
                ('start_date', '<=', self.registration_end_date),
                ('id_no', 'in', _LEARNER_CODE), 
                # ('provider_id.saqa_provider_code', 'in', _PROVIDER_CODE)
                ]
        assessor_objs = (self.env['inseta.assessor'].search(domain, limit=self.limit))
        error_found = []
        filename = self.generate_filename('26')
        attachment = False 
        if assessor_objs:
            val_items = []
            for assessor in assessor_objs:      
                eddy = self.fix_dates(self.make_up_date(assessor.end_date))
                _ASSESSOR_NUM.append(assessor.registration_number)
                vals = {
                    'National_Id': assessor.id_no,
                    'Person_Alternate_Id': assessor.id_no,
                    'Alternative_Id_Type': int(assessor.alternateid_type_id.saqacode) if assessor.alternateid_type_id.saqacode not in _NONE else 533,
                    'Designation_Id': 1,
                    'Designation_Registration_Number': self.validate_null_fields(assessor.registration_number),  #assessor.employer_sdl_no,# assessor.etdp_registration_number,
                    'Designation_ETQA_Id':595,
                    'Designation_Start_Date': self.fix_dates(self.filth_date_gap(assessor.start_date,eddy)),
                    'Designation_End_Date': eddy,
                    'Structure_Status_Id': 501 if assessor.active else 503, # 501 means registered while 503 means deregistered
                    'Etqa_Decision_Number': ' ',
                    'Provider_Code': assessor.provider_id.saqa_provider_code if assessor.provider_id.saqa_provider_code in _PROVIDER_CODE else "",
                    'Provider_ETQA_ID': 595,
                    'Date_Stamp':self.fix_dates(assessor.write_date),
                }
                val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '26',
                    'file_unique_identifier': filename,
                })
                # for values in val_items:
                #     _logger.info(values)
                #     self.generate_dat(values, header, header_keys, filename)
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
        return attachment, filename, error_found
        # else:
        #     raise ValidationError('No Assessor record to generate NLRD')

    def action_generate_27(self):
        """Generate Assessor registration model record"""
        header = [
                10, 10,10,5,20,10,
                8, 8,20,10,8,
                ]
        header_keys = [
            'Learnership_Id',
            'Qualification_Id',
            'Unit_Standard_Id',  # maybe later
            'Designation_Id',
            'Designation_Registration_Number',
            'Designation_ETQA_Id',
            'NQF_Designation_Start_Date',
            'NQF_Designation_End_Date',
            'Etqa_Decision_Number',
            'NQF_Desig_Status_Code',
            'Date_Stamp', 
        ]
        val = {
            }
        domain = [('registration_number','in',_ASSESSOR_NUM)]
        if self.filter_by == "date": 
            domain = [
                ('start_date', '>=', self.registration_start_date), 
                ('start_date', '<=', self.registration_end_date),
                ('registration_number','in',_ASSESSOR_NUM)
                ]
        error_found = []
        filename = self.generate_filename('27')
        attachment = []
        assessor_registers = (self.env['inseta.assessor.register'].search(domain, limit=self.limit))
        if assessor_registers:
            val_items = []
            for accrs in assessor_registers: 
                # Unit standard Accreditation
                def validate_27():
                    error_txt = ""
                    if not accrs.sdl_no:
                        error_txt += f"{accrs.id} Designate ID not found"

                    if accrs.registration_number not in _ASSESSOR_NUM:
                        error_txt += "Designation or assessor number not in file 26"
                        
                    # if not accrs.registration_start_date:
                    #     error_txt += "registration_start_date not found"

                    # if not accrs.registration_end_date:
                    #     error_txt += "end_date not found"

                    if not any([accrs.qualification_ids, accrs.unit_standard_ids]):
                        error_txt += f"{accrs.id}: qualification_ids or  unit_standard_ids not found"
                
                    return error_txt
                error = validate_27()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    eddy = self.fix_dates(self.make_up_date(accrs.registration_end_date))
                    for unit in accrs.unit_standard_ids: 
                        vals = {
                            'Learnership_Id': '',
                            'Qualification_Id': '',
                            'Unit_Standard_Id': unit.code,  # maybe later
                            'Designation_Id': 1,
                            'Designation_Registration_Number': self.validate_null_fields(accrs.sdl_no),  #accrs.sdl_no, # accrs.etdp_registration_number,
                            'Designation_ETQA_Id': 595,
                            'NQF_Designation_Start_Date': self.fix_dates(self.filth_date_gap(accrs.registration_start_date,eddy)),
                            'NQF_Designation_End_Date': eddy,
                            'Etqa_Decision_Number': '',
                            'NQF_Desig_Status_Code': self.accredit_status_to_code('Active') if accrs.active else self.accredit_status_to_code('Inactive'),
                            'Date_Stamp': self.fix_dates(accrs.write_date),
                        }
                        val_items.append(vals)
                    for qa in accrs.qualification_ids:
                        vals = {
                            'Learnership_Id': '',
                            'Qualification_Id': qa.saqa_id,
                            'Unit_Standard_Id': '',  # maybe later
                            'Designation_Id': 1,
                            'Designation_Registration_Number':self.validate_null_fields(accrs.sdl_no), # accrs.etdp_registration_number,
                            'Designation_ETQA_Id': 595,
                            'NQF_Designation_Start_Date': self.fix_dates(self.filth_date_gap(accrs.registration_start_date,eddy)),
                            'NQF_Designation_End_Date': eddy,
                            'Etqa_Decision_Number': '',
                            'NQF_Desig_Status_Code': self.accredit_status_to_code('Active') if accrs.active else self.accredit_status_to_code('Inactive'),
                            'Date_Stamp': self.fix_dates(accrs.write_date),
                        }
                        val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '27',
                    'file_unique_identifier': filename,
                }) 
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
        return attachment, filename,error_found

    def action_generate_28(self):
        """Generate learnership assessment model record"""
        header = [
                15, 20,3,10,3,20,
                8, 8,20,10,10,8,
                8,
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternate_Id_Type',
            'Learnership_Id',
            'Learner_Achievement_Status_Id',
            'Assessor_Registration_Number',
            'Learner_Achievement_Date',
            'Learner_Enrolled_Date',
            'Provider_Code',
            'Provider_Etqa_Id',  # blanket
            'Assessor_Etqa_Id',  # blanket
            'Certification_Date',
            'Date_Stamp',
                       ]
        domain = [
            ('learner_id.id_no', 'in', _LEARNER_CODE),
            # ('provider_id.saqa_provider_code', 'in', _PROVIDER_CODE)
        ]
        # domain = [('learner_learnership_id', '!=', False)]
        if self.filter_by == "date": 
            domain += [
                ('create_date', '>=', self.start_date), 
                ('create_date', '<=', self.end_date),
                ('learner_id.id_no', 'in', _LEARNER_CODE),
            ('provider_id.saqa_provider_code', 'in', _PROVIDER_CODE)
                ]
        learnership_assessments = (self.env['inseta.learner.learnership'].search(domain))
        error_found = []
        filename = self.generate_filename('28')
        attachment = False
        if learnership_assessments: 
            val_items = [] 
            for la in learnership_assessments:
                programme_status = la.programme_status_id 
                _LEARNERSHIP_CODE.append(la.learner_programme_id.learnership_saqa_id)
                def validate_28():
                    error_txt = ""
                    if not la.learner_id.id_no:
                        error_txt += f"{la.id}: Learner ID Number not found"
                        
                    if programme_status.code not in _PROGRAMME_STATUS_CODE:
                        #  and int(programme_status.code) not in codes:
                        # raise ValidationError(programme_status.code)
                        error_txt += f"{la.id}: Programme status with saqa code not found"
                    # if la.certificate_created_date and programme_status.code in ['3']:
                    #     #  and int(programme_status.code) not in codes:
                    #     # raise ValidationError(programme_status.code)
                    #     error_txt += f"{la.id}: Programme status with saqa code not found"

                    if not la.enrollment_date:
                        error_txt += f"{la.id}: Enrollment_date not found"
                    if la.certificate_created_date and la.enrollment_date:
                        if la.certificate_created_date < la.enrollment_date:
                            error_txt += f"{la.id}: certificate_created_date is less than enrollment date"
                    if not la.provider_id.saqa_provider_code:
                        error_txt += f"{la.id}: Provider saqa code not found"
                    if not any([la.learner_programme_id.learnership_saqa_id]):
                        error_txt += f"{la.id}: learner programme code not found"
                    return error_txt
                error = validate_28()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    vals = {
                        'National_Id': la.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(la.learner_id)[0], # la.learner_id.id_no,
                        'Alternate_Id_Type':  self.validate_person_id(la.learner_id)[1], # la.learner_id.alternateid_type_id.saqacode if la.learner_id.id_no and la.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Learnership_Id': la.learner_programme_id.learnership_saqa_id,
                        'Learner_Achievement_Status_Id': int(la.programme_status_id.code),
                        'Assessor_Registration_Number': '', #la.assessor_id.id_no or la.assessor_id.employer_sdl_no,
                        'Learner_Achievement_Date': self.compute_date_data(la.achievement_date) if la.programme_status_id.code != '3' else "",  # todo:needs eval based on learner_achievement_type_id
                        'Learner_Enrolled_Date': self.compute_date_data(la.enrollment_date),
                        'Provider_Code': self.env['inseta.provider'].browse([la.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Certification_Date': self.compute_date_data(la.certificate_created_date) if la.programme_status_id.code != '3' else "",
                        'Date_Stamp': self.fix_dates(la.write_date),
                    }
                    val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '28',
                    'file_unique_identifier': filename,
                })
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                        # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
                    })
        return attachment, filename, error_found

    def action_generate_29(self):
        """Generate qualification learnership model record"""
        header = [
                15, 20,3,10,3,20,
                3, 8,8,3,2,10,
                20, 10, 10, 8, 8,
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternate_Id_Type',  
            'Qualification_Id',
            'Learner_Achievement_Status_Id',
            'Assessor_Registration_Number',
            'Learner_Achievement_Type_Id',  # todo: find or pass flat value 6 is  other
            'Learner_Achievement_Date',  # todo:needs eval based on learner_achievement_type_id
            'Learner_Enrolled_Date',
            'Honours_Classification',  # not req
            'Part_Of',  # only allows 1 or 3/should only be 1 , blanket
            'Learnership_Id',  # not req
            'Provider_Code',
            'Provider_Etqa_Id',  # blanket
            'Assessor_Etqa_Id',  # blanket
            'Certification_Date',
            'Date_Stamp',
            # 'lrq_id': lrq.id,
            # 'learner_id': lrq.learner_id.id,
                       ]
        domain = [('learner_id.id_no', 'in', _LEARNER_CODE),
            ('provider_id.saqa_provider_code', 'in', _PROVIDER_CODE),]
        # domain = [('learner_qualification_id', '!=', False)]
        if self.filter_by == "date": 
            domain += [
                ('create_date', '>=', self.start_date), 
                ('create_date', '<=', self.end_date),
                ('learner_id.id_no', 'in', _LEARNER_CODE),
            ('provider_id.saqa_provider_code', 'in', _PROVIDER_CODE)
                ]
        qualification_assessments = (self.env['inseta.qualification.learnership'].search(domain))
        error_found = []
        attachment = False
        filename = self.generate_filename('29')
        if qualification_assessments: 
            val_items = []
            for qa in qualification_assessments:
                def validate_29():
                    error_txt = ""
                    # if not pers.alternateid_type_id.saqacode:
                    #     error_txt += f"{pers.id} does not have Alternate Id Type"
                    if not qa.qualification_id.saqa_id:
                        error_txt += f"{qa.id} does not have qualification ID"

                    if qa.certificate_created_date and qa.enrollment_date:
                        if qa.certificate_created_date < qa.enrollment_date:
                            error_txt += f"{qa.id} Achievement date is lesser than enrollment date"
 
                    if qa.programme_status_id.code not in _PROGRAMME_STATUS_CODE:
                        error_txt += f"{qa.programme_status_id.code} Qualification does not have programme status code"


                    if not qa.enrollment_date:
                        error_txt += f"{pers.id} does not have enrollment date"
                    return error_txt
                error = validate_29()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    _QUALIFICATION_CODE.append(qa.qualification_id.saqa_id)
                    # eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                    vals = {
                        'National_Id': qa.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(qa.learner_id)[0], #qa.learner_id.id_no,
                        'Alternate_Id_Type':self.validate_person_id(qa.learner_id)[1],# qa.learner_id.alternateid_type_id.saqacode if qa.learner_id.id_no and qa.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Qualification_Id': qa.qualification_id.saqa_id,
                        'Learner_Achievement_Status_Id': qa.programme_status_id.code,
                        'Assessor_Registration_Number': '', 
                        'Learner_Achievement_Type_Id': 5,
                        'Learner_Achievement_Date': self.compute_date_data(qa.certificate_created_date) if qa.programme_status_id.code != '3' else "",# and qa.certificate_created_date < qa.enrollment_date else "",  # todo:needs eval based on learner_achievement_type_id
                        'Learner_Enrolled_Date': self.compute_date_data(qa.enrollment_date),
                        'Honours_Classification': "",
                        'Part_Of': 1, # if not qa.qualification_id.qualification_unit_standard_ids else 2,
                        'Learnership_Id': "",
                        'Provider_Code': self.env['inseta.provider'].browse([qa.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Certification_Date': self.compute_date_data(qa.certificate_created_date) if qa.programme_status_id.code != '3' else "",
                        'Date_Stamp': self.fix_dates(qa.write_date),
                    }
                    val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '29',
                    'file_unique_identifier': filename,
                })
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                    })
        return attachment, filename, error_found

    def action_generate_30(self):
        """Generate unit standard assessment model record"""
        header = [
                15, 20,3,10,3,20,
                3, 8,8,3,2,10,
                10, 20,10,10,8,8,
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternate_Id_Type',  
            'Unit_Standard_Id',
            'Learner_Achievement_Status_Id',
            'Assessor_Registration_Number',
            'Learner_Achievement_Type_Id',  # todo: find or pass flat value 6 is  other
            'Learner_Achievement_Date',  # todo:needs eval based on learner_achievement_type_id
            'Learner_Enrolled_Date',
            'Honours_Classification',  # not req
            'Part_Of',  # only allows 1 or 3/should only be 1 , blanket
            'Qualification_Id',  # not req
            'Learnership_Id',  # not req
            'Provider_Code',
            'Provider_Etqa_Id',  # blanket
            'Assessor_Etqa_Id',  # blanket
            'Certification_Date',
            'Date_Stamp',
            # 'lrq_id': lrq.id,
            # 'learner_id': lrq.learner_id.id,
                       ]
        qual_domain = [
            ('qualification_learnership_id.learner_id.id_no', 'in', _LEARNER_CODE),
            ('qualification_learnership_id.provider_id.saqa_provider_code', 'in', _PROVIDER_CODE),
            ]
        learnership_domain = [
            ('learnership_id.learner_id.id_no', 'in', _LEARNER_CODE),
            ('learnership_id.provider_id.saqa_provider_code', 'in', _PROVIDER_CODE),
        ]
        # domain = [('unit_standard_learnership_id', '!=', False)]
        # if self.filter_by == "date": 
        #     domain += [
        #         ('create_date', '>=', self.start_date), 
        #         ('create_date', '<=', self.end_date),
        #         ('learner_id.id_no', 'in', _LEARNER_CODE),
        #     ('provider_id.saqa_provider_code', 'in', _PROVIDER_CODE)
        #         ]
        qualification_unitstandards = (self.env['inseta.qualification.unitstandard'].search(qual_domain))
        learnership_unitstandards = (self.env['inseta.learnership.unitstandard'].search(learnership_domain))
        error_found = []
        val_items = [] 
        attachment = False
        filename = self.generate_filename('30')
        if learnership_unitstandards: 
            for qa in learnership_unitstandards:
                def validate_30():
                    error_txt = ""
                    if not qa.learnership_id.learner_programme_id.learnership_saqa_id:
                        error_txt += f"{qa.id} does not have learnership saqa ID"
                    if qa.learnership_id.learner_programme_id.learnership_saqa_id not in _LEARNERSHIP_CODE:
                        error_txt += f"{qa.id} does not have matching learnership saqa ID"
                    if qa.learnership_id.provider_id.saqa_provider_code not in _PROVIDER_CODE:
                        error_txt += f"{qa.id} does not have matching provider saqa code"

                    if qa.learnership_id.certificate_created_date:
                        if qa.learnership_id.certificate_created_date < qa.learnership_id.enrollment_date:
                            error_txt += f"{qa.id} Achievement date is lesser than enrollment date"
                    if qa.learnership_id.certificate_created_date:
                        if qa.learnership_id.certificate_created_date < qa.learnership_id.enrollment_date:
                            error_txt += f"{qa.id}: certificate_created_date is less than enrollment date"
                    if qa.learnership_id.programme_status_id.code not in _PROGRAMME_STATUS_CODE:
                        error_txt += f"{qa.learnership_id.programme_status_id.code} Qualification does not have programme status code"
                    return error_txt
                error = validate_30()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    vals = {
                        'National_Id': qa.learnership_id.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(qa.learnership_id.learner_id)[0],#qa.learnership_id.learner_id.id_no if qa.learnership_id.learner_id.id_no not in _NONE else "",
                        'Alternate_Id_Type':self.validate_person_id(qa.learnership_id.learner_id)[1],# qa.learnership_id.learner_id.alternateid_type_id.saqacode if qa.learnership_id.learner_id.id_no and qa.learnership_id.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Unit_Standard_Id': qa.unit_standard_id.code,
                        'Learner_Achievement_Status_Id': qa.learnership_id.programme_status_id.code,
                        'Assessor_Registration_Number': "", 
                        'Learner_Achievement_Type_Id': 5, # 5 work place learning by default for now
                        'Learner_Achievement_Date': self.compute_date_data(qa.learnership_id.certificate_created_date) if qa.learnership_id.programme_status_id.code != '3' and qa.learnership_id.certificate_created_date < qa.learnership_id.enrollment_date else "",  # todo:needs eval based on learner_achievement_type_id
                        'Learner_Enrolled_Date': self.compute_date_data(qa.learnership_id.enrollment_date),
                        'Honours_Classification': "",
                        'Part_Of': 1,
                        'Qualification_Id': "",
                        'Learnership_Id': qa.learnership_id.learner_programme_id.learnership_saqa_id,  # not req
                        'Provider_Code': self.env['inseta.provider'].browse([qa.learnership_id.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Certification_Date': self.compute_date_data(qa.learnership_id.certificate_created_date) if qa.learnership_id.programme_status_id.code != '3' else "",
                        'Date_Stamp': self.fix_dates(qa.write_date),
                    }
                    val_items.append(vals)
        if qualification_unitstandards: 
            for qa in qualification_unitstandards:
                # eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                def validate_30():
                    error_txt = ""
                    if qa.qualification_learnership_id.provider_id.saqa_provider_code not in _PROVIDER_CODE:
                        error_txt += f"{qa.id} does not have matching provider saqa codd"
                    if qa.qualification_learnership_id.qualification_id.saqa_id not in _LEARNERSHIP_CODE:
                        error_txt += f"{qa.id} does not have matching qualification saqa ID"
                    if qa.qualification_learnership_id.certificate_created_date:
                        if qa.qualification_learnership_id.certificate_created_date < qa.qualification_learnership_id.enrollment_date:
                            error_txt += f"{qa.id} Achievement date is lesser than enrollment date"
 
                    if qa.qualification_learnership_id.programme_status_id.code not in _PROGRAMME_STATUS_CODE:
                        error_txt += f"{qa.qualification_learnership_id.programme_status_id.code} Qualification does not have programme status code"

                    return error_txt
                error = validate_30()
                if error:
                    error_dict = {'error_msg': error}
                    error_found.append(error_dict)
                else:
                    vals = {
                        'National_Id': qa.qualification_learnership_id.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(qa.qualification_learnership_id.learner_id)[0],# qa.qualification_learnership_id.learner_id.id_no,
                        'Alternate_Id_Type': self.validate_person_id(qa.qualification_learnership_id.learner_id)[1], # qa.qualification_learnership_id.learner_id.alternateid_type_id.saqacode if qa.qualification_learnership_id.learner_id.id_no and qa.qualification_learnership_id.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Unit_Standard_Id': qa.unit_standard_id.code,
                        'Learner_Achievement_Status_Id': qa.qualification_learnership_id.programme_status_id.code,
                        'Assessor_Registration_Number': "", # qa.qualification_learnership_id.assessor_id.registration_number,
                        'Learner_Achievement_Type_Id': 5, # 5 work place learning by default for now
                        'Learner_Achievement_Date': self.compute_date_data(qa.qualification_learnership_id.certificate_created_date) if qa.qualification_learnership_id.programme_status_id.code != '3' else "",  # todo:needs eval based on learner_achievement_type_id
                        'Learner_Enrolled_Date': self.compute_date_data(qa.qualification_learnership_id.enrollment_date),
                        'Honours_Classification': "",
                        'Part_Of': 1,
                        'Qualification_Id': qa.qualification_learnership_id.qualification_id.saqa_id,
                        'Learnership_Id': "",  # not req
                        'Provider_Code': self.env['inseta.provider'].browse([qa.qualification_learnership_id.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Certification_Date': self.compute_date_data(qa.qualification_learnership_id.certificate_created_date) if qa.qualification_learnership_id.programme_status_id.code != '3' else "",
                        'Date_Stamp': self.fix_dates(qa.write_date),
                    }
                    val_items.append(vals)
            if val_items:
                nlrd_obj = self.env['inseta.nlrd'].create({
                    'name': '30',
                    'file_unique_identifier': filename,
                })
                self.generate_dat(val_items, header, header_keys, filename)
                # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
                folder_name = self.generate_filename(False)
                filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
                byte_data = None
                with open(filepath, "rb") as xlfile:
                    byte_data = xlfile.read()
                attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': base64.encodestring(byte_data),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': 'inseta.nlrd.export',
                        'mimetype': 'application/dat'
                    })
        return attachment, filename, error_found

    # def validate_achieve_enrollment_date(self, qa):
    #     Learner_Achievement_Date = self.compute_date_data(qa.qualification_learnership_id.certificate_created_date)
    #     #  if qa.qualification_learnership_id.programme_status_id.code != '3' else "",
    #       # todo:needs eval based on learner_achievement_type_id
    #     Learner_Enrolled_Date = self.compute_date_data(qa.qualification_learnership_id.enrollment_date),
                        
    def confirm_notification(self, popup_message):
        view = self.env.ref('inseta_nlrd.view_confirmation_dialog')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = popup_message
        return {
            'name': 'Message!',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'inseta.nlrd.dialog',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    def action_export_nlrd_data(self):
        self.validate_date_filters()
        attachment = None
        filename = None
        error_found = []
        filedata = []
        file_name_list = []
        folder_dir = f"/var/log/odoo/{_FOLDER_NAME}"
        if os.path.isdir(os.getcwd() + folder_dir):
            shutil.rmtree(os.getcwd() + folder_dir, ignore_errors=True)
            os.mkdir(os.getcwd() + folder_dir)
        else:
            os.mkdir(os.getcwd() + folder_dir)
            
        # if self.file_type == "21": # Generating providers record
        #     attachment, filename, error_found, file_data = self.action_generate_21()

        # elif self.file_type == "24":
        #     attachment, filename, error_found = self.action_generate_24()

        # elif self.file_type == "25":
        #     attachment, filename, error_found = self.action_generate_25()

        # elif self.file_type == "26":
        #     attachment, filename, error_found = self.action_generate_26()

        # elif self.file_type == "27":
        #     attachment, filename, error_found = self.action_generate_27()

        # elif self.file_type == "28":
        #     attachment, filename, error_found = self.action_generate_28()

        # elif self.file_type == "29":
        #     attachment, filename, error_found = self.action_generate_29()

        # elif self.file_type == "30":
        #     attachment, filename, error_found = self.action_generate_30()

        if self.file_type == "all":
            attachment_ids = []
            attachment, filename, error_found = self.action_generate_21()
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_24()
            # filedata.append({'attachment': attachment.id, 'filename': filename, 'error_found': error_found })
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_25()
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_26()
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_27()
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_28()
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_29()
            file_name_list.append(filename)

            attachment, filename, error_found = self.action_generate_30()
            file_name_list.append(filename)

            # # zip_folder_name = self.generate_filename(False) # generate a filename 20220301
            working_directory = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+_FOLDER_NAME+'.zip' # generate a zip file with the name 20220301
            path = os.getcwd() + folder_dir # os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME
            with zipfile.ZipFile(working_directory, mode="w") as archive:
                for root, dirs, files in os.walk(path):
                    for fil in files:
                        if fil.startswith('INSU'):
                            # archive.write(path+'/'+fil)
                            archive.write(path+'/'+fil, os.path.relpath(fil, root))
                # archive.close()
            byte_data = None
            with open(working_directory, "rb") as xlfile:
                byte_data = xlfile.read()
            zip_filename = _FOLDER_NAME+'.zip'
            attachment = self.env['ir.attachment'].create({
                    'name': zip_filename,
                    'datas': base64.encodestring(byte_data),
                    'type': 'binary',
                    'res_id': self.id,
                    'res_model': 'inseta.nlrd.export',
                    'mimetype': 'application/x-zip-compressed'
                })

            return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}/{zip_filename}?download=true',
                    'target': 'new',
                    'nodestroy': False,
                    }
 
            
        if self.file_type != 'all':
            if attachment and filename:
                return {
                        'type': 'ir.actions.act_url',
                        'url': f'/web/content/{attachment.id}/{filename}?download=true',
                        'target': 'new',
                        'nodestroy': False,
                        }
            else:
                message_err = ""
                for dics in error_found:
                    message_err += dics.get('error_msg', '')
                raise ValidationError(f'No File to generate because of the following validations \n {message_err}')
        else:
            if filedata:
                for rc in filedata:
                    raise ValidationError(rc.get('attachment'))
                    return {
                        'type': 'ir.actions.act_url',
                        'url': '/web/content/{}/{}?download=true'.format(rc.get('attachment'), rc.get('filename')),
                        'target': 'new',
                        'nodestroy': True,
                        }

    def generate_dat(self, object_items, header_positions, headers, datfile_name):
        """ 
            object_items = [
            {'provider_code':'909992929292929292999', 'age': '45', 'phone': '09099'},
            {'name':'Solomon', 'age': '54','phone': '09099'}
            ]
            # headers = ['name', 'age', 'phone']
            # header_positions = [10, 30, 40, 50, 70, 128]
        """
        txt = ""
        LINUX_EOF, WINDOWS_EOF = '\r\n', '\n'
        NEW_LINE = WINDOWS_EOF if os.name == "nt" else LINUX_EOF # posix
        if len(headers) != len(header_positions):
            raise ValidationError(header_positions) # (f"Length of ({len(headers)}) field size not equal to the Header positions ({len(header_positions)})")
        for dicts in object_items:
            for hp in range(0, len(header_positions)):
                # {'provider_code':'909992929292929292999', 'age': '45', 'phone': '09099'},
                hps = header_positions[hp] # 128
                if dicts[headers[hp]]:
                    txt += f"{str(dicts[headers[hp]]).ljust(hps)[0:header_positions[hp]]}"
                else:
                    txt += f"{''.ljust(hps)[0:header_positions[hp]]}"
            # txt += '\r\n'
            txt += NEW_LINE
        folder_dir = f"var/log/odoo/{_FOLDER_NAME}"
        with open(folder_dir+'/'+datfile_name, 'w') as f:
            f.write(txt)
            f.close()

    # def generate_dat_main(self, vald, lens, fields_list, datfile_name):

    #     """
    #     This will take each dictionary and create a dat file.

    #     Usage will be:

    #     from nlrd_dat import gendat

    #     gendat(the_dictionary_that_gets_passed_to_create, lengths_according_to_nlrd, name_of_dat_file)

    #     One thing to note though, the list that gets generated by the list() function below
    #     may end up being in the wrong order unless we use OrderedDictionaries. Luckily, these
    #     are in the collections module in the standard library and Odoo should not have difficulty
    #     handling them as if they were normal dictionaries.
        
    #     vald = list of value items or objects
    #     lens = headers items
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
    #             # vald[fields_list[x] = object[header_keys[index]]
    #             # eg. obj = {'name': 'maduka'}, obj['name'][1]
    #             # if nothing, add an empty
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
    #     raise ValidationError(tuple(endtup))

    #     try:
    #         # with open("/var/log/odoo/"+datfile_name, 'a') as f:
    #         # for local testing create a directory to use
    #         with open("var/log/odoo/"+datfile_name, 'a') as f:
    #             f.write(fmt % tuple(endtup))
    #     except IOError:
    #         with open("var/log/odoo/"+datfile_name, 'w') as f:
    #             f.write(fmt % tuple(endtup))
    #     # raise ValidationError(os.getcwd()+ ) # path.abspath("/var/log/odoo/"+datfile_name))

    #     # filename = os.path.abspath(datfile_name)
    #     # Path = os.path.expanduser(datfile_name)
    #     # # raise ValidationError(filename)
    #     # fileout = open(Path, "r")
    #     # # output = fileout.read()
    #     # self.dat_file = base64.encodestring(fileout)

    # def generate_dat_file(self, val_items, header, header_keys, filename):
    #     result = [] 
    #     txt = """"""
    #     length_header = len(header_keys) 
    #     for val in val_items:
    #         endtup = []
    #         for x in range(0, length_header):
    #             # raise ValidationError(val)
    #             txt = "{0} {1:150}".format(txt, str(val[header_keys[x]]))
    #         txt += "\n"
         
    #     with open(filename, 'a') as fl:
    #         fl.write(txt)
        
    #     fileout = open(filename, "rb")
    #     output = fileout.read()

    #     # output.close()
    #     self.dat_file = base64.b64encode(output)


class INSETANLRDDialog(models.TransientModel):
    _name = "inseta.nlrd.dialog"
    
    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False
    
    name = fields.Text(string="Message", readonly=True, default=get_default)


    # def gendat_method(self, vald, lens, fields_list, datfile_name):
    # 	"""
    # 	This will take each dictionary and create a dat file.

    # 	Usage will be:

    # 	from nlrd_dat import gendat

    # 	gendat(the_dictionary_that_gets_passed_to_create, lengths_according_to_nlrd, name_of_dat_file)

    # 	One thing to note though, the list that gets generated by the list() function below
    # 	may end up being in the wrong order unless we use OrderedDictionaries. Luckily, these
    # 	are in the collections module in the standard library and Odoo should not have difficulty
    # 	handling them as if they were normal dictionaries.
    # 	"""

    # 	fmt = ""
    # 	endtup = []
    # 	vall = list(vald.values())

    # 	for x in range(0, len(lens)):

    # 		fmt += "%-*s"
    # 		endtup.append(lens[x])

    # 		# if len(lens) != len(vall):
    # 		# 	raise AssertionError('field length and length list are not same len ' + str(len(lens)) + str(len(vall)))
    # 		try:
    # 			if not vald[fields_list[x]]:
    # 				endtup.append(''[0:lens[x]])
    # 			elif type(vald[fields_list[x]]) == int:
    # 				valu = vald[fields_list[x]]
    # 				print(valu)
    # 				#valu = valu.encode("ascii")
    # 				print(lens[x])
    # 				endtup.append(str(valu)[0:lens[x]])
    # 			# if lambda a, d: any(k in a for k in d):
    # 			else:
    # 				valu = vald[fields_list[x]]
    # 				#valu = valu.encode("ascii")
    # 				print('ELSE')
    # 				endtup.append(valu[0:lens[x]])
                
    # 		except UnicodeEncodeError:
    # 			if not vald[fields_list[x]]:
    # 				endtup.append(''[0:lens[x]])
    # 			elif type(vald[fields_list[x]]) == int:
    # 				valu = vald[fields_list[x]]
    # 				endtup.append(str(valu)[0:lens[x]])
    # 			# if lambda a, d: any(k in a for k in d):
    # 			else:
    # 				valu = "CHEESE"
    # 				endtup.append(valu[0:lens[x]])
                

    # 	# dbg(endtup)
    # 	fmt += "\r\n"
    # 	try:
    # 		# Pictures Pictures
    # 		with open(datfile_name, 'a') as f:
    # 			f.write(fmt % tuple(endtup))
    # 			self.filename = datfile_name
    # 	except IOError:
    # 		with open(datfile_name, 'w') as f:
    # 			f.write(fmt % tuple(endtup))
    # 			self.filename = datfile_name