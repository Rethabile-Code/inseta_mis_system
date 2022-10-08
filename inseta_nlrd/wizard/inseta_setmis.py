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
import shutil
import zipfile
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


class Insetasetmis(models.Model):
    _name = 'inseta.setmis'
    _description  = "setmis GENERATED"
    
    name = fields.Char('File')
    file_unique_identifier = fields.Char('File Unique Idenitifier')
    error_to_fix = fields.Text("Errors to Fix")
    model_id = fields.Char("Model / Table name")
    ref_id= fields.Integer("Record reference")

    def action_go_to_record(self):
        name = self.name
        if name == "100":
            form_view_ref = "inseta_etqa.view_provider_form"
            tree_view_ref = "inseta_etqa.view_provider_tree"
            return self.see_sale_order_reference("Provider", tree_view_ref, form_view_ref)
        elif name == "200":
            form_view_ref = "inseta_skills.view_organization_form"
            tree_view_ref = "inseta_skills.view_organization_tree"
            return self.see_sale_order_reference("Employer", tree_view_ref, form_view_ref)
        elif name == "400":
            form_view_ref = "inseta_etqa.view_learner_form"
            tree_view_ref = "inseta_etqa.view_learner_tree"
            return self.see_sale_order_reference("Learner", tree_view_ref, form_view_ref)
        elif name == "401":
            form_view_ref = "inseta_etqa.view_assessor_form"
            tree_view_ref = "inseta_etqa.view_assessor_tree"
            return self.see_sale_order_reference("Assessor", tree_view_ref, form_view_ref)
        elif name == "500":
            form_view_ref = "inseta_etqa.view_inseta_learner_learnership_form"
            tree_view_ref = "inseta_etqa.view_inseta_learner_learnership_tree"
            return self.see_sale_order_reference("Learnership", tree_view_ref, form_view_ref)
        elif name == "501":
            form_view_ref = "inseta_etqa.view_inseta_qualification_learnership_form"
            tree_view_ref = "inseta_etqa.view_inseta_qualification_learnership_tree"
            return self.see_sale_order_reference("Learner qualification", tree_view_ref, form_view_ref)

        elif name == "503":
            form_view_ref = "inseta_etqa.view_inseta_unit_standard_learnership_form"
            tree_view_ref = "inseta_etqa.view_inseta_unit_standard_learnership_tree"
            return self.see_sale_order_reference("Learner Unit standard", tree_view_ref, form_view_ref)

    def see_sale_order_reference(self, name, tree_view_id, form_view_id):
        if self.ref_id:
            # search_view_ref = self.env.ref(
            #     'sale.sale_order_view_search_inherit_sale', False)
            form_view_ref = self.env.ref(form_view_id, False)
            if form_view_ref:
                tree_view_ref = self.env.ref(tree_view_id, False)
                return {
                    'domain': [('id', '=', int(self.ref_id))],
                    'name': name,
                    'res_model': f'{self.model_id}',
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_ref.id, 'tree'),(form_view_ref.id, 'form')],
                    # 'search_view_id': search_view_ref and search_view_ref.id,
                }
            else:
                raise ValidationError("Form view not found or this record!!!")
        else:
            raise ValidationError("No record reference!!!")

class InsetasetmisExport(models.TransientModel):
    _name = 'inseta.setmis.export'
    _description  = "setmis EXPORT Wizard"

    dat_file = fields.Binary('Download SETMIS file', filename='filename', readonly=True)
    filename = fields.Char('DAT File')
    file_type = fields.Selection([
        ('all', 'All'),
    ], required=True, default="all")
    filter_by = fields.Selection([
        ('all', 'All records'),
        ('date', 'Date'),
    ], required=True, default='all', string="Filter by", help="Start Date")

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    date_threshold = fields.Date('Threshold date', default= fields.date.today() + timedelta(days = -360),
     help = "To set threshold in which Qualification should be generated based on Enrollment or commencement date ")
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
        # FORMAT [CODE]_0006_100_v001_YYYYMMDD
        code = 'INSE' 
        file_code = name
        dt_str = datetime.strftime(datetime.today(), '%Y-%m-%d')
        filename_suffix = re.sub('-', '', dt_str) # 20210121 
        suffix_result = filename_suffix[2:] # 210121
        # YY,MM,DD = filename_suffix[2:4], filename_suffix[4:6], filename_suffix[6:]
        if name:
            filename = f"{code}_0006_{file_code}_v001_{filename_suffix}.dat" # e.g INSE_0006_100_v001_20120130
        else:
            filename = f"{filename_suffix}" #used to generate folder only dont remove
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

    def get_enrollment_date(self, program):
        enrollment_date = ""
        if program.certificate_created_date:
            if program.enrollment_date == False:
                enrollment_date = program.certificate_created_date + timedelta(days = -2)
            elif program.enrollment_date:
                if program.enrollment_date > program.certificate_created_date:
                    enrollment_date = program.certificate_created_date + timedelta(days = -2)
                else:
                    enrollment_date = program.enrollment_date
            else:
                enrollment_date = program.enrollment_date
        elif not program.certificate_created_date and not program.enrollment_date:
            enrollment_date = program.commencement_date or program.create_date
        else:
            enrollment_date = program.enrollment_date or program.commencement_date or ""
        return enrollment_date

    def _create_log(self, data):
        vals = {
            'name': data.get('file_type'),
            'file_unique_identifier': "",
            'error_to_fix': data.get('error_msg'),
            'model_id': data.get('model_id'),
            'ref_id': data.get('rec_id'),
        }
        self.env['inseta.setmis'].create(vals)

    def action_generate_100(self, _PROVIDERS):
        header = [
                    20, 10, 10, 70, 10, 
                    50,  50, 50, 4, 20, 
                    20, 20, 50, 50, 20,
                    20, 20, 8,8, 20, 10,
                    10, 2, 4, 3,2,
                    6, 2, 2, 6, 50, 50,
                    50, 4, 50, 10, 8
                    ]  

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
        domain = [('id', 'in', _PROVIDERS)] 
        providers = (self.env['inseta.provider'].search(domain))
        filename = self.generate_filename('100')
        attachment = False
        error_found = []
        val_items = []
        if providers:
            for provider in providers:
                eddy = self.fix_dates(self.make_up_date(provider.accreditation_end_date))
                def validate_100():
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
                error = validate_100()
                if error:
                    error_dict = {
                        'error_msg': error,
                        'file_type': "100",
                        'model_id': 'inseta.provider',
                        'rec_id': provider.id,
                    }
                    error_found.append(error_dict)
                    self._create_log(error_dict)
                else:
                    latitude_degree = ""
                    latitude_minutes = ""
                    latitude_seconds = ""
                    longitude_degree = ""
                    longitude_minutes = ""
                    longitude_seconds = ""
                    if provider.latitude_degree:
                        if not provider.latitude_degree.startswith('-'):
                            pass
                        if provider.latitude_degree[0:2].isdigit():
                            if int(provider.latitude_degree[0:2]) < -22:
                                latitude_degree = provider.latitude_degree
                        if not (provider.latitude_minutes and provider.latitude_seconds):
                            pass
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
        if val_items: 
            self.generate_dat(val_items, header, header_keys, filename)
            # folder_name = self.generate_filename(False)
            # filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
            # byte_data = None
            # with open(filepath, "rb") as xlfile:
            #     byte_data = xlfile.read()
            #     # attachment = self.env['ir.attachment'].create({
            #     #     'name': filename,
            #     #     'datas': base64.encodestring(byte_data),
            #     #     'type': 'binary',
            #     #     'res_id': self.id,
            #     #     'res_model': 'inseta.setmis.export',
            #     #     'mimetype': 'application/dat'
            #     #     # 'description': f"inseta setmis export: [{filename}] created on {fields.Datetime.now()}"
            #     # })
            #     # else:
            #     #     raise ValidationError('No Provider record to generate setmis')
    def action_generate_200(self):
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
        organisation_ids = self.env['inseta.organisation'].search(domain)
        val_items = []
        filename = self.generate_filename('200')
        error_msg = []
        error_found = []
        if organisation_ids:
            for emp in organisation_ids:
                def validate_21():
                    error_txt = ""
                    return error_txt 
                error = validate_21()
                if error:
                    error_dict = {
                        'error_msg': error,
                        'file_type': "200",
                        'model_id': 'inseta.organisation',
                        'rec_id': emp.id,
                    }
                    self._create_log(error_dict)
                else:
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
        if val_items:
            self.generate_dat(val_items, header, header_keys, filename)
            # folder_name = self.generate_filename(False)
            # filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
            # byte_data = None
            # with open(filepath, "rb") as xlfile:
            #     byte_data = xlfile.read()
                
    def action_generate_400(self, _LEARNERS):
        """Generate Learner / person (including assessors (inseta.learner) model record"""
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
                        'Provider_ETQE_Id',  # 30 c blanket  Provider_ETQE_Id
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
        domain = [('id', 'in', _LEARNERS)]
        person = (self.env['inseta.learner'].search(domain))
        error_found = []
        attachment = False
        filename = self.generate_filename('400')
        val_items = []
        if person:
            alternateid_type_ids = [
                '521', '527', '529',
                '531', '533', '535',
                '537', '538', '539', 
                '540', '541', '561', 
                '565'
                ]
            for pers in person:
                def validate_400():
                    error_txt = ""
                    if not pers.equity_id.saqacode:
                        error_txt += f"{pers.id} does not have Equity code"
                    # if pers.provider_id.saqa_provider_code:
                    #     if pers.provider_id.saqa_provider_code not in _PROVIDERS:
                    #         error_txt += f"{pers.id} does not have matching SAQA provider code"
                    if not pers.home_language_id.code:
                        error_txt += f"{pers.id} does not have home Language id code"
                    if not pers.gender_id:
                        error_txt += f"{pers.id} does not have gender code"
                    if not pers.id_no:
                        error_txt += f"{pers.id} does not have National ID"
                    if pers.id_no and len(pers.id_no) > 13:
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
                                '565']\n"""
                    # if not pers.equity_id.saqacode:
                    #     error_txt += "equity code not found\n"
                    # if not pers.citizen_resident_status_id.saqacode:
                    #     error_txt += "citizen_resident_status code not found\n"
                    if not pers.socio_economic_status_id.saqacode:
                        error_txt += "socio economic status code not found\n"
                    if not pers.disability_id.saqacode:
                        error_txt += "disability code not found\n"
                    if not self.validate_a_z_name_values(pers.first_name):
                        error_txt += f"{pers.id} does not have first name, \n"
                    if not self.validate_a_z_name_values(pers.last_name):
                        error_txt += f"{pers.id} does not have last name, \n"
                    if not pers.birth_date:
                        error_txt += f"{pers.id} does not have birth date, \n"
                    return error_txt
                error = validate_400()
                if error:
                    error_dict = {
                        'error_msg': error,
                        'file_type': "400",
                        'model_id': 'inseta.learner',
                        'rec_id': pers.id,
                    }
                    self._create_log(error_dict)
                else:
                    vals = {
                        'National_Id': self.validate_person_id(pers)[0],
                        'Person_Alternate_Id': self.validate_person_id(pers)[1],  # c
                        'Alternate_Id_Type': pers.alternateid_type_id.saqacode,  # req
                        'Equity_Code': pers.equity_id.saqacode if pers.equity_id.saqacode not in _NONE else "",  # y
                        'Nationality_Code': pers.nationality_id.saqacode if pers.nationality_id.saqacode not in _NONE else "",  # y
                        'Home_Language_Code': self.validate_home_language_code(pers.home_language_id.code), # pers.home_language_id.code or self.lang_to_code(pers.home_language_id.name) if pers.home_language_id.code not in _NONE else "",  # y
                        'Gender_Code': self.gender_to_code(pers.gender_id.name),  # y
                        'Citizen_Resident_Status_Code': pers.citizen_resident_status_id.saqacode if pers.citizen_resident_status_id.saqacode not in _NONE else "",
                        'Filler01': '',  # y
                        'Filler02': '',  # y
                        'Person_First_Name': pers.first_name if self.validate_a_z_name_values(pers.first_name) else "",  # y
                        'Person_Last_Name': pers.last_name if self.validate_a_z_name_values(pers.last_name) else "",  # y
                        'Person_Middle_Name': pers.middle_name if self.validate_a_z_name_values(pers.middle_name) else "",
                        'Person_Title': '',
                        'Person_Birth_Date': self.compute_date_data(pers.birth_date),
                        'Person_Home_Address_1': self.validate_address_text(pers.street),
                        'Person_Home_Address_2': self.validate_address_text(pers.street2), #pers.street2 or "",
                        'Person_Home_Address_3': self.validate_address_text(pers.street3), #pers.street3 or "",
                        'Person_Postal_Address_1': self.validate_address_text(pers.postal_address1), #pers.postal_address1 or "",
                        'Person_Postal_Address_2': self.validate_address_text(pers.postal_address2), # pers.postal_address2 or "", # 20
                        'Person_Postal_Address_3': self.validate_address_text(pers.postal_address3), # pers.postal_address3 or "",
                        'Person_Home_Addr_Postal_Code': pers.physical_code if self.validate_address_text(pers.physical_code) else "", # pers.physical_code or "",
                        'Person_Postal_Addr_Post_Code': pers.postal_code if self.validate_address_text(pers.postal_code) else "", # pers.postal_code or "",
                        'Person_Phone_Number': self.validate_address_text(pers.phone), #pers.phone or "",
                        'Person_Cell_Phone_Number': self.validate_address_text(pers.mobile), # pers.mobile or "",
                        'Person_Fax_Number': self.validate_address_text(pers.fax_number), #pers.fax_number or "",
                        'Person_Email_Address': self.validate_null_fields(pers.email), #pers.email or "",
                        'Province_Code': pers.physical_province_id.saqacode if not self.validate_province_code(pers.physical_province_id.saqacode) else "N", #pers.physical_province_id.saqacode or "",  # y
                        'Provider_Code': self.validate_non_alphabet_numeric_text(pers.provider_id.saqa_provider_code), #pers.provider_id.saqa_provider_code or "",  # c
                        'Provider_ETQE_Id': 595,
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
        if val_items:
            self.generate_dat(val_items, header, header_keys, filename)
            # # filepath = os.getcwd() + "/var/log/odoo/"+filename # get the filename absolute path
            # folder_name = self.generate_filename(False)
            # filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
            # # byte_data = None
            # # with open(filepath, "rb") as xlfile:
            # #     byte_data = xlfile.read()
             
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
        assessor_objs = (self.env['inseta.assessor'].search([]))
        error_found = []
        _PROVIDERS = []
        attachment = False 
        if assessor_objs:
            val_items = []
            filename = self.generate_filename('401')
            for accrs in assessor_objs:      
                eddy = self.fix_dates(self.make_up_date(accrs.end_date))
                # _ASSESSOR_NUM.append(assessor.registration_number)
                vals = {
                    'National_Id': accrs.id_no,
                    'Person_Alternate_Id': accrs.id_no,
                    'Alternative_Id_Type': int(accrs.alternateid_type_id.saqacode) if accrs.alternateid_type_id.saqacode not in _NONE else 533,
                    'Designation_Id':accrs.employer_sdl_no,
                    'Designation_Registration_Number': self.validate_null_fields(accrs.registration_number),  #assessor.employer_sdl_no,# assessor.etdp_registration_number,
                    'Designation_ETQA_Id':'595',
                    'Designation_Start_Date': self.fix_dates(self.filth_date_gap(accrs.start_date,eddy)),
                    'Designation_End_Date': eddy,
                    'Designation_Structure_Status_Id': '501' if accrs.active else '503', # 501 means registered while 503 means deregistered
                    'Etqa_Decision_Number': ' ',
                    'Provider_Code': accrs.provider_id.saqa_provider_code if accrs.provider_id.saqa_provider_code in _PROVIDERS else "",
                    'Provider_ETQE_Id': '595',
                    'Filler01': "",
                    'Filler01': "",
                    'Filler03': "",
                    'Date_Stamp':self.fix_dates(accrs.write_date),
                }
                val_items.append(vals)
                # _PROVIDERS.append(accrs.provider_id.id)
        if val_items:
            self.generate_dat(val_items, header, header_keys, filename)
            # folder_name = self.generate_filename(False)
            # filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
        # return _PROVIDERS
                # byte_data = None
                # with open(filepath, "rb") as xlfile:
                #     byte_data = xlfile.read()
                    
        #         attachment = self.env['ir.attachment'].create({
        #                 'name': filename,
        #                 'datas': base64.encodestring(byte_data),
        #                 'type': 'binary',
        #                 'res_id': self.id,
        #                 'res_model': 'inseta.setmis.export',
        #                 'mimetype': 'application/dat'
        #                 # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
        #             })
        #     return attachment, filename
        # else:
        #     raise ValidationError('No Assessor record to generate SETMIS')

    def action_generate_500(self):
        """Generate learnership model record"""
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
        _PROVIDERS, _LEARNERS = [], []
        val_items = []
        error_found = []
        filename = self.generate_filename('500')
        attachment = False
        learnership_assessments = self.env['inseta.learner.learnership'].search(domain)
        if learnership_assessments: 
            _PROGRAMME_STATUS_CODE = ['2','3','4','5','7','10','14','15','27','28','29','31','32','49','50','69','70','89']
            for la in learnership_assessments:
                programme_status = la.programme_status_id 
                def validate_500():
                    error_txt = ""
                    if not la.learner_id.id_no:
                        error_txt += f"{la.id}: Learner ID Number not found\n"
                    if programme_status.code not in _PROGRAMME_STATUS_CODE:
                        error_txt += f"{la.id}: Programme status with saqa code not found\n"
                    if not la.enrollment_date:
                        error_txt += f"{la.id}: Enrollment_date not found\n"
                    if la.certificate_created_date and la.enrollment_date:
                        if la.certificate_created_date < la.enrollment_date:
                            error_txt += f"{la.id}: certificate_created_date is less than enrollment date\n"
                    if not la.provider_id.saqa_provider_code:
                        error_txt += f"{la.id}: Provider saqa code not found\n"
                    if not any([la.learner_programme_id.learnership_saqa_id]):
                        error_txt += f"{la.id}: learner programme code not found\n"
                    return error_txt
                error = validate_500()
                if error:
                    error_dict = {
                        'error_msg': error,
                        'file_type': "500",
                        'model_id': 'inseta.learner.learnership',
                        'rec_id': la.id,
                    }
                    self._create_log(error_dict)
                else:
                    vals = {
                        'National_Id': la.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(la.learner_id)[0], # la.learner_id.id_no,
                        'Alternate_Id_Type':  self.validate_person_id(la.learner_id)[1], # la.learner_id.alternateid_type_id.saqacode if la.learner_id.id_no and la.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Learnership_Id': la.learner_programme_id.learnership_saqa_id,
                        'Enrolment_Status_Id': la.programme_status_id.code or la.enrollment_status_id.code,
                        'Assessor_Registration_Number': '', #la.assessor_id.id_no or la.assessor_id.employer_sdl_no,
                        'Enrolment_Status_Date': self.compute_date_data(la.achievement_date) if la.programme_status_id.code != '3' else None,  # todo:needs eval based on learner_achievement_type_id
                        'Enrolment_Date': self.compute_date_data(la.enrollment_date),
                        'Provider_Code': la.provider_id.saqa_provider_code, 
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
                        'Date_Stamp': self.fix_dates(la.write_date),
                    }
                    val_items.append(vals)
                    _PROVIDERS.append(la.provider_id.id)
                    _LEARNERS.append(la.learner_id.id)
        if val_items:
            self.generate_dat(val_items, header, header_keys, filename)
            # folder_name = self.generate_filename(False)
            # filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
        return _PROVIDERS, _LEARNERS
            
                # byte_data = None
                # with open(filepath, "rb") as xlfile:
                #     byte_data = xlfile.read()
        #         attachment = self.env['ir.attachment'].create({
        #                 'name': filename,
        #                 'datas': base64.encodestring(byte_data),
        #                 'type': 'binary',
        #                 'res_id': self.id,
        #                 'res_model': 'inseta.setmis.export',
        #                 'mimetype': 'application/dat'
        #                 # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
        #             })
        #     return attachment, filename
        # else:
        #     raise ValidationError('No learner record to generate SETMIS')

    def action_generate_501(self):
        """Generate qualification assessment model record"""
        _PROGRAMME_STATUS_CODE = ['2','3','4','5','7','10','14','15','27','28','29','31','32','49','50','69','70','89']
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
        _PROVIDERS, _LEARNERS = [], []
        val_items = []
        error_found = []
        filename = self.generate_filename('501')
        attachment = False
        qualification_assessments = self.env['inseta.qualification.learnership'].search(domain)
        if qualification_assessments:
            for la in qualification_assessments:
                programme_status = la.programme_status_id 
                def validate_501():
                    error_txt = ""
                    if not la.enrollment_date:
                        error_txt += f"{la.id} does not have enrollment date"
                    if la.certificate_created_date and la.enrollment_date:
                        if la.certificate_created_date < la.enrollment_date:
                            error_txt += f"{la.id} Achievement date is lesser than enrollment date"
                    if la.programme_status_id.code not in _PROGRAMME_STATUS_CODE:
                        error_txt += f"{la.programme_status_id.code} Qualification does not have programme status code"
                    return error_txt
                error = validate_501()
                if error:
                    error_dict = {
                        'error_msg': error,
                        'file_type': "501",
                        'model_id': 'inseta.qualification.learnership',
                        'rec_id': la.id,
                    }
                    self._create_log(error_dict)
                else:
                    vals = {
                        'National_Id': la.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(la.learner_id)[0], #qa.learner_id.id_no,
                        'Alternate_Id_Type':self.validate_person_id(la.learner_id)[1],# qa.learner_id.alternateid_type_id.saqacode if qa.learner_id.id_no and qa.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Qualification_Id': la.qualification_id.saqa_id,
                        'Enrolment_Status_Id': la.programme_status_id.code, # or la.enrollment_status_id.code,
                        'Assessor_Registration_Number': '', #la.assessor_id.id_no or la.assessor_id.employer_sdl_no,
                        'Enrolment_Type_Id': 5,
                        'Enrolment_Status_Date': self.compute_date_data(la.achievement_date) if la.programme_status_id.code != '3' else None,  # todo:needs eval based on learner_achievement_type_id
                        'Enrolment_Date': self.compute_date_data(la.enrollment_date),
                        'Filler01': '',
                        'Part_Of_Id': 1 if not la.qualification_id.qualification_unit_standard_ids else 2,
                        'Learnership_Id': "",
                        'Provider_Code': la.provider_id.saqa_provider_code, 
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
                        'Date_Stamp': self.fix_dates(la.write_date),
                    }
                    val_items.append(vals)
                    _PROVIDERS.append(la.provider_id.id)
                    _LEARNERS.append( la.learner_id.id)
        if val_items:
            self.generate_dat(val_items, header, header_keys, filename)
            # folder_name = self.generate_filename(False)
            # filepath = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+filename # get the filename absolute path
        return _PROVIDERS, _LEARNERS
                # byte_data = None
                # with open(filepath, "rb") as xlfile:
                #     byte_data = xlfile.read()
        #         attachment = self.env['ir.attachment'].create({
        #                 'name': filename,
        #                 'datas': base64.encodestring(byte_data),
        #                 'type': 'binary',
        #                 'res_id': self.id,
        #                 'res_model': 'inseta.setmis.export',
        #                 'mimetype': 'application/dat'
        #                 # 'description': f"inseta Nlrd export: [{filename}] created on {fields.Datetime.now()}"
        #             })
        #     return attachment, filename
        # else:
        #     raise ValidationError('No learner record to generate SETMIS')

    def action_generate_503(self):
        """Generate unit standard enrollments model record"""
        header = [
                    15, 20, 3, 10, 3, 20, 3, 8, 8, 3,
                    2, 10, 10, 20, 10, 10, 20, 20, 10,
                    8, 10, 10, 10, 10, 10, 1, 10, 10, 30, 
                    10, 15, 10, 10, 20, 10, 10, 8
                ]
        header_keys = [
            'National_Id',
            'Person_Alternate_Id',
            'Alternate_Id_Type',  
            'Unit_Standard_Id',
            'Enrolment_Status_Id',
            'Assessor_Registration_Number',
            'Enrolment_Type_Id',  # todo: find or pass flat value 6 is  other
            'Enrolment_Status_Date',  # todo:needs eval based on learner_achievement_type_id
            'Enrolment_Date',
            'Filler01',  # not req
            'Part_Of_Id',  # only allows 1 or 3/should only be 1 , blanket
            'Qualification_Id',  # not req
            'Learnership_Id',  # not req
            'Provider_Code',
            'Provider_Etqa_Id',  # blanket
            'Assessor_Etqa_Id',  # blanket
            'Filler02',  # blanket
            'Filler03',
            'Enrolment_Status_Reason_Id',
            'Most_Recent_Registration_Date',
            'Filler04',
            'Filler05',
            'Filler06',
            'Economic_Status_Id',
            'Filler07',
            'Filler08',
            'Filler09',
            'Cumulative_Spend',
            'Certificate_Number',
            'Funding_Id',
            'OFO_Code', 
            'SDL_No',
            'Site_No',
            'Non_NQF_Interv_Code',
            'Non_NQF_Interv_ETQE_Id',
            'Urban_Rural_ID',
            'Date_Stamp',
            # 'lrq_id': lrq.id,
            # 'learner_id': lrq.learner_id.id,
                       ]
        
        unit_standard_domain = []
        if self.date_threshold:
            # learnership_domain = [
            # '|', ('learnership_id.commencement_date', '>=', self.date_threshold), # '2021-04-01'
            # ('learnership_id.enrollment_date', '>=', self.date_threshold),
            # ]
            unit_standard_domain = [
            '|', ('commencement_date', '>=', self.date_threshold), # '2021-04-01'
            ('enrollment_date', '>=', self.date_threshold), # '2021-04-01'
            ]
        # qualification_unitstandards = (self.env['inseta.qualification.unit.standard'].search(qual_domain))
        # learnership_unitstandards = (self.env['inseta.learnership.unit.standard'].search(learnership_domain))
        learner_unitstandards = (self.env['inseta.unit_standard.learnership'].search(unit_standard_domain))
        _QUALIFICATIONS = []
        _LEARNERSHIPS = []
        _PROVIDERS = []
        _LEARNERS = []
        _UNIT_STANDARD_IDS = []
        error_found = []
        val_items = [] 
        attachment = False 
        filename = self.generate_filename('503')
        if learner_unitstandards:
            for qa in learner_unitstandards: 
                def validate_503():
                    error_txt = ""
                    if not qa.unit_standard_id.code:
                        error_txt += f"{qa.id} does not have unit standard saqa ID\n"
                    enrollment = self.get_enrollment_date(qa)
                    if not enrollment:
                        error_txt += f"{qa.id} enrollment date not found\n"
                    return error_txt
                error = validate_503()
                if error:
                    error_dict = {
                        'error_msg': error,
                        'file_type': "503",
                        'model_id': 'inseta.unit_standard.learnership',
                        'rec_id': la.id,
                    }
                    self._create_log(error_dict)
                else:
                    vals = {
                        'National_Id': qa.learner_id.id_no,
                        'Person_Alternate_Id': self.validate_person_id(qa.learner_id)[0],#qa.learnership_id.learner_id.id_no if qa.learnership_id.learner_id.id_no not in _NONE else "",
                        'Alternate_Id_Type':self.validate_person_id(qa.learner_id)[1],# qa.learnership_id.learner_id.alternateid_type_id.saqacode if qa.learnership_id.learner_id.id_no and qa.learnership_id.learner_id.alternateid_type_id.saqacode not in _NONE else 533,
                        'Unit_Standard_Id': qa.unit_standard_id.code,
                        'Enrolment_Status_Id': qa.programme_status_id.code,
                        'Assessor_Registration_Number': "", 
                        'Enrolment_Type_Id': "5", # 5 work place learning by default for now
                        'Enrolment_Status_Date': self.compute_date_data(qa.certificate_created_date) if qa.programme_status_id.code != '3' else "",  # todo:needs eval based on learner_achievement_type_id
                        'Enrolment_Date': self.compute_date_data(qa.enrollment_date),
                        'Filler01': "",
                        'Part_Of_Id': 1,
                        'Qualification_Id': "",
                        'Learnership_Id': "",# qa.learner_programme_id.learnership_saqa_id,  # not req
                        'Provider_Code': self.env['inseta.provider'].browse([qa.provider_id.id]).saqa_provider_code, 
                        'Provider_Etqa_Id': 595,  # blanket
                        'Assessor_Etqa_Id': 595,  # blanket
                        'Filler02': "",
                        'Filler03': "",
                        'Enrolment_Status_Reason_Id': "",
                        'Most_Recent_Registration_Date': self.compute_date_data(qa.most_recent_registration_date),
                        'Filler04': "",
                        'Filler05': "",
                        'Filler06': "",
                        'Economic_Status_Id': "",
                        'Filler07': "",
                        'Filler08': "",
                        'Filler09': "",
                        'Cumulative_Spend': qa.cummulative_spend,
                        'Certificate_Number': "",
                        'Funding_Id': qa.funding_type.saqacode,
                        'OFO_Code': qa.ofo_occupation_id.code,
                        'SDL_No': "",
                        'Site_No': "",
                        'Non_NQF_Interv_Code': "",
                        'Non_NQF_Interv_ETQE_Id': "",
                        'Urban_Rural_ID': qa.learner_id.physical_urban_rural,
                        'Date_Stamp': self.fix_dates(qa.write_date),
                    }
                    val_items.append(vals)
                    _PROVIDERS.append(qa.provider_id.id)
                    _LEARNERS.append(qa.learner_id.id)
                    # _UNIT_STANDARD_IDS.append(qa.unit_standard_id.code)
        if val_items:
            self.generate_dat(val_items, header, header_keys, filename)
        return _PROVIDERS, _LEARNERS
         
    def export_all(self):
        # try:
        self.env['inseta.setmis'].search([]).unlink()
        _PROVIDERS, _LEARNERS, = [], []
        
        file_503 = self.action_generate_503()
        _PROVIDERS += file_503[0]
        _LEARNERS += file_503[1]

        file_501 = self.action_generate_501()
        _PROVIDERS += file_501[0]
        _LEARNERS += file_501[1]

        file_500 = self.action_generate_500()
        _PROVIDERS += file_500[0]
        _LEARNERS += file_500[1]

        file_401 = self.action_generate_401()
        # _LEARNERS += file_401[1]

        self.action_generate_400(_LEARNERS)
        self.action_generate_200()
        self.action_generate_100(_PROVIDERS)
        # except Exception as e:
        #     raise ValidationError(e)

    def action_export_setmis_data(self):
        attachment = None
        filename = None
        error_found = []
        filedata = []
        file_name_list = []
        folder_dir = f"/var/log/odoo/{_FOLDER_NAME}"
        if os.path.isdir(os.getcwd() + folder_dir):
            shutil.rmtree(os.getcwd() + folder_dir, ignore_errors=True)
        else:
            os.mkdir(os.getcwd() + folder_dir)
        if self.file_type == "all":
            self.export_all()
            # # zip_folder_name = self.generate_filename(False) # generate a filename 20220301
            working_directory = os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME+'/'+_FOLDER_NAME+'.zip' # generate a zip file with the name 20220301
            path = os.getcwd() + folder_dir # os.getcwd() + "/var/log/odoo/"+_FOLDER_NAME
            with zipfile.ZipFile(working_directory, mode="w") as archive:
                for root, dirs, files in os.walk(path):
                    for fil in files:
                        if fil.startswith('INSE'):
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
        folder_dir = os.getcwd() + f"/var/log/odoo/{_FOLDER_NAME}/"
        with open(folder_dir + datfile_name, 'w') as f:
            f.write(txt)
            f.close()

    # def generate_dat(self, object_items, header_positions, headers, datfile_name):
    #     """ 
    #         object_items = [
    #         {'name':'Maduka', 'age': '45', 'phone': '09099'},
    #         {'name':'Solomon', 'age': '54','phone': '09099'}
    #         ]
    #         # headers = ['name', 'age', 'phone']
    #         # header_positions = [10, 30, 40]
    #     """
    #     txt = ""
    #     if len(headers) != len(header_positions):
    #         raise ValidationError(f"{datfile_name} header and header positions not matching") # (f"Length of ({len(headers)}) field size not equal to the Header positions ({len(header_positions)})")
    #     for dicts in object_items:
    #         for hp in range(0, len(header_positions)): # header_positions = [10, 30, 40]
    #             hps = header_positions[hp] #  header_positions[3]   = 30                                                   
    #             if dicts[headers[hp]]: 
    #                 txt += f"{str(dicts[headers[hp]]).ljust(hps)[0:header_positions[hp]]}"
    #             else:
    #                 txt += f"{''.ljust(hps)[0:header_positions[hp]]}"
    #         txt += '\n'
    #     # raise ValidationError(txt)
    #     with open("var/log/odoo/"+datfile_name, 'w') as f:
    #         f.write(txt)

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

