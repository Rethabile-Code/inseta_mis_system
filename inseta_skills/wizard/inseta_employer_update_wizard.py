# -*- coding: utf-8 -*-
import base64
import csv
import json
import logging
from io import StringIO
import timeit

from odoo.tools import date_utils
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class InsetaEmployerUpdateWizard(models.TransientModel):
    """This wizard is used for INTER SETA transfer fow now
       MAP = {
            0: "employer_sdl_no",
            1: "field1",
            2: "field2",
            3: "company_name_1",
            4: "txtRegName",
            5: "company_rep_initial",
            6: "company_rep_surname",
            7: "ext_date_of_birth",
            8: "ext_identity_number",
            9: "employer_registration_number",
            10: "company_status",
            11: "ext_date_business_commenced",
            12: "ext_date_person_became_liable",
            13: "ext_partner_initial",
            14: "ext_partner_surname",
            15: "ext_capacity_rep_employer",
            16: "ext_physical_address_1",
            17: "ext_physical_address_2",
            18: "ext_physical_address_3",
            19: "ext_physical_code",
            20: "emp_postal_code",
            21: "ext_dial_code_rep_emp",
            22: "ext_telephone_number_rep_emp",
            23: "ext_fax_dial_code_rep_emp",
            24: "ext_fax_number_rep_emp",
            25: "ext_bus_cell_number",
            26: "employer_trading_name",
            27: "street",
            28: "street2",
            29: "street3",
            30: "suburb",
            31: "zip",
            32: "org_phone_code_1",
            33: "org_phone_number_1",
            34: "org_phone_code_2",
            35: "org_phone_number_2",
            36: "org_cell_number",
            37: "ext_postal_address_1",
            38: "ext_postal_address_2",
            39: "ext_postal_address_3",
            40: "org_postal_4",
            41: "ext_postal_code",
            42: "code_1",
            43: "code_2",
            44: "code_3",
            45: "ext_empl_sic_code_id",
            46: "code_5",
            47: "code_6",
            48: "code_7",
            49: "reserved_1",
            50: "reserved_2",
            51: "reserved_3",
            52: "reserved_4",
            53: "code_8",
            54: "code_9",
            55: "reserved_5",
            56: "reserved_6",
            57: "reserved_7",
            58: "code_10",
            59: "reserved_8",
            60: "sars_number",
            61: "code_11",
            62: "code_12",
        }
        
    """


    _name = "inseta.employer.update.wizard"
    _description = "Employer Update Wizard"

    file = fields.Binary(string="Select File", required=True)
    file_name = fields.Char("File Name")
    date_imported = fields.Date(default=fields.Date.today())

    @api.constrains('file')
    def _check_file(self):
        ext = str(self.file_name.split(".")[1])
        if ext and ext not in ('SDL', 'sdl'):
                raise ValidationError(_("You can only upload files with .SDL extension"))

    def action_import(self):
        _logger.info("Importing DHET Employer Update File ...")

        if not self.file:
            raise ValidationError('Please select a file')


        csv_data = base64.b64decode(self.file)
        data_file = StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.reader(data_file, delimiter='|')
        file_reader.extend(csv_reader)
        org_list = []
        count_org = len(file_reader)
        _logger.info(f"Importing {count_org} Organisations from DHET Employer Update File ...")
        # _logger.info(f"file data {json.dumps(file_reader,indent=4)}")
        _logger.info(f"file data {json.dumps(self._context.get('model'),indent=4)}")

        starttime = timeit.default_timer()
        _logger.info(f"The start time RAW SQL is : {starttime}")
        self.env.cr.execute("""SELECT sdl_no FROM inseta_organisation""")
        items =  self.env.cr.fetchall()
        sdlno_list = [sdlno and sdlno[0] for sdlno in items]

        OrganisationUpdate = self.env['inseta.levypayer.organisation.update']
        #Check if employer file have been imported to prevent creating duplicate import records
        employer_update = OrganisationUpdate.search([('file_name','=',self.file_name)])
        if not employer_update:
            employer_update = OrganisationUpdate.create({
                "file_name": self.file_name,
                "file": self.file
            })

        loop = 0
        for row in file_reader:
            #import only if the employer does not exists
            if row[0] not in sdlno_list and row[43] == '13':
                _logger.info(f"SDL NO => {row[0]}")
                dob1 = row[7]
                dob2 = row[11]
                dob3 = row[12]
                val = dict(
                    levy_status = "Levy Paying",
                    company_type = "company",
                    sdl_no = row[0],
                    dhet_sdl_no = row[0],
                    name = row[26], #row[3],
                    legal_name = row[4],
                    dhet_legal_name = row[4],
                    #ceo details moved to new dict
                    registration_no= row[9],
                    company_status = row[10],
                    # organisation_status = 'Active' if row[10] == 'A' else 'Inactive',
                    date_business_commenced = f"{dob2[:4]}-{dob2[4:6]}-{dob2[6:8]}" if len(dob2) == 8 else False,
                    date_person_became_liable = f"{dob3[:4]}-{dob3[4:6]}-{dob3[6:8]}" if len(dob3) == 8 else False,
                    #contact records moved to seperate dict
                    trade_name = row[26],
                    dhet_trade_name = row[26],
                    street = row[27],
                    street2 = row[28],
                    street3 = row[29],
                    physical_suburb_id = self._get_suburb_by_name(row[30],row[31]),
                    physical_code = row[31],
                    phone = f"{row[32]}{row[33]}",
                    fax_number = f"{row[34]}{row[35]}",
                    mobile = row[36],
                    postal_address1 = row[37],
                    postal_address2 = row[38],
                    postal_address3 = row[39],
                    city = row[40],
                    postal_code = row[41],
                    seta_id = self._get_seta(row[43]),
                    sic_code_id = self._get_sic_code(row[45]),
                    sars_number = row[60],
                    employer_update_id = employer_update.id, #link between this import and employer update record
                    state = "pending_approval",
                )
                Organisation = self.env['inseta.organisation']
                obj = Organisation.create(val)

                Partner = self.env['res.partner']
                #create or update CEO
                ceo_val = {
                    "type": "CEO",
                    "initials": row[5],
                    "last_name": row[6],
                    "birth_date": f"{dob1[:4]}-{dob1[4:6]}-{dob1[6:8]}" if dob1 and len(dob1) == 8 else False,
                    "id_no": row[8],
                    "parent_id": obj.partner_id.id
                } if row[6] else False
                if ceo_val:
                    ceo = Partner.search([
                        ('id_no', '=', row[8]),
                        ('parent_id', '=',obj.partner_id.id)
                    ])
                    #IMPORTANT do not perform write().. will slow down the import, only create ceo if not exists
                    if not ceo:
                        Partner.create(ceo_val)

                #create/update contact
                contact_val = {
                    "type": "contact",
                    "initials": row[13],
                    "name": row[14],
                    "function": row[15],
                    "street": row[16],
                    "street2": row[17],
                    "street3": row[18],
                    "physical_code": row[19],
                    "postal_code": row[20],
                    "phone": f"{row[21]}{row[22]}",
                    "fax_number":f"{row[23]}{row[24]}",
                    "mobile": row[25],
                    "parent_id": obj.partner_id.id
                }
                contact = Partner.search([
                    ('mobile', '=', contact_val.get('mobile')),
                    ('name', '=', contact_val.get('name'))
                ])
                #IMPORTANT do not perform write().. will slow down the import, only create contact if not exists
                if not contact:
                   Partner.create(contact_val)
                _logger.info(f"ORG ID {obj.id}")

                #Create Inter seta record if Date person become liable to pay levy is same month
                # date_become_liable_month = dob3[4:6]
                # if fields.Date.today().month == int(date_become_liable_month):
                #     OrganisationIst = self.env['inseta.organisation.ist']
                #     ist = OrganisationIst.search([('organisation_id', '=', obj.id)])
                #     if not ist:
                #         OrganisationIst.create({
                #             "organisation_id": obj.id,
                #             "transfer_type": "transfer_in",
                #             "current_seta_id": Organisation._get_default_seta(), #INSETA seta_id
                #             "new_seta_id": self._get_seta(row[43]),
                #             "new_sic_code_id": self._get_sic_code(row[45]),
                #         })

                if loop == 100:
                    _logger.info('100 Organisations records created/Updated')
                    self.env.cr.commit()
                    loop = 0
                loop += 1

        _logger.info(f"Total Time Taken To Import DHET File is : {timeit.default_timer() - starttime}") 

        return {'type': 'ir.actions.client','tag': 'reload'}


    def _get_seta(self, setaid):
        id = int(setaid) if (isinstance(setaid, float) or isinstance(setaid, str)) else setaid
        obj = self.env['res.seta'].search(
            [('seta_id', '=', id)], limit=1)
        return obj and obj.id or False

    def _get_sic_code(self,code):

        obj = self.env['res.sic.code'].search([
            ('siccode', '=', code),
        ], limit=1)
        return obj and int(obj.id) or False

    def _get_suburb_by_name(self, name, postal_code):

        obj = self.env['res.suburb'].search([
            ('name', '=', name),
            ('postal_code', '=', postal_code)
        ], limit=1)
        return obj and int(obj.id) or False
