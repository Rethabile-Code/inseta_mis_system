# -*- coding: utf-8 -*-
import logging
import base64
from datetime import datetime
import json
from xlrd import open_workbook, xldate_as_tuple

from odoo.addons.inseta_tools.validators import format_to_odoo_date
from odoo.addons.inseta_tools.date_tools import dd_mm_yyy_to_y_m_d

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

def cast_to_integer(val):
    """Convert float to integer
    Args:
        val (float): The item to convert
    Returns:
        int: the converted item
    """
    return int(val) if isinstance(val, float) else val

class InsetaWspAtrImportWizard(models.TransientModel):

    _name = "inseta.wspatr.import.wizard"
    _description = "Import WSP/ATR Data"

    @api.model
    def default_get(self, fields):
        res = super(InsetaWspAtrImportWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({
            'wspatr_id': active_ids[0] if active_ids else False,
        })
        return res

    template = fields.Selection([
            ('Current Employment Profile', 'WSP: Current Employment Profile'),
            ('Highest Educational Profile', 'WSP: Highest Educational Profile'),
            ('Pivotal_Planned_Beneficiaries_Large', 'WSP: Pivotal Planned Beneficiaries - Large'),
            ('Pivotal_Planned_Beneficiaries_Small', 'WSP: Pivotal Planned Beneficiaries - Small'), 
            ('Planned_Beneficiaries_Large', 'WSP: Planned Beneficiaries of Training - Large'),
            ('Planned_Beneficiaries_Small', 'WSP: Planned Beneficiaries of Training - Small'),
            ('Planned AET Training','WSP: Planned AET Training'),
            ('Training planned','WSP: Training Planned'),
            # ('Workplace Skill Plan', 'Planned Beneficiaries of Training'),
            ('Provincial Breakdown','Provincial Breakdown'),
            ('Implementation Report','ATR: Implementation Report'), #small firms
            ('Trained Beneficiaries Report', 'ATR 1: Trained Beneficiaries Report'),
            ('Learning Programmes', 'ATR 2: Learning Programmes'),
            ('Pivotal Trained Beneficiaries', 'ATR: Pivotal Trained Beneficiaries'),
            ('Hard To Fill Vacancies','ATR: Hard To Fill Vacancies'),
            ('Trained AET', 'ATR: Trained AET'),
            ('Skills Gap','ATR: Skills Gaps')
        ], 
        "WSP Template",
        default="Current Employment Profile"
    )

    submission_type = fields.Selection([('ATR', 'ATR'), ('WSP', 'WSP')], default="WSP")
    wspatr_id = fields.Many2one('inseta.wspatr')
    is_small_firm = fields.Boolean(related="wspatr_id.is_small_firm")
    form_type = fields.Selection(related="wspatr_id.form_type") #Small
    file = fields.Binary(string="Select File", required=True)
    file_name = fields.Char("File Name")


    @api.constrains('file')
    def _check_file(self):
        ext = str(self.file_name.split(".")[1])
        if ext and ext not in ('xls', 'xlsx'):
                raise ValidationError("You can only upload excel sheets")


    def read_file(self, index=0):
        if not self.file:
            raise ValidationError('Please select a file')

        file_datas = base64.decodebytes(self.file)
        workbook = open_workbook(file_contents=file_datas)
        sheet = workbook.sheet_by_index(index)
        file_data = [[sheet.cell_value(r, c) for c in range(
            sheet.ncols)] for r in range(2,sheet.nrows)] #skip the first 3 rows
        file_data.pop(0)
        return file_data

    def action_import(self):
        # file_data = self.read_file()
        if not self.file:
            raise ValidationError('Please select a file')

        file_datas = base64.decodebytes(self.file)
        workbook = open_workbook(file_contents=file_datas)
        sheet = workbook.sheet_by_index(0)
        file_data = [[sheet.cell_value(r, c) for c in range(
            sheet.ncols)] for r in range(2,sheet.nrows)] #skip the first 3 rows
        file_data.pop(0)

        template = self.template

        if template == "Trained Beneficiaries Report":
            _logger.info("Importing Trained Beneficiaries Report...")
            for count, row in enumerate(file_data):
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[6]
                    self._validate_other_country(other_country)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        municipality_id = self._get_municipality_id(row[2]),
                        programme_level =  row[3],
                        training_provider = row[4],
                        completion_status = row[5] or False,
                        other_country = row[6],
                        african_male = cast_to_integer(row[7]),
                        african_female = cast_to_integer(row[8]),
                        african_disabled = cast_to_integer(row[9]),
                        colored_male = cast_to_integer(row[10]),
                        colored_female = cast_to_integer(row[11]),
                        colored_disabled = cast_to_integer(row[12]),
                        indian_male = cast_to_integer(row[13]),
                        indian_female = cast_to_integer(row[14]),
                        indian_disabled = cast_to_integer(row[15]),
                        white_male = cast_to_integer(row[16]),
                        white_female = cast_to_integer(row[17]),
                        white_disabled = cast_to_integer(row[18]),
                        other_male = cast_to_integer(row[19]),
                        other_female = cast_to_integer(row[20]),
                        other_disabled = cast_to_integer(row[21]),
                        age1 = cast_to_integer(row[22]),
                        age2 = cast_to_integer(row[23]),
                        age3 = cast_to_integer(row[24]),
                        age4 = cast_to_integer(row[25]),
                    )
                    _logger.info(f"ATR DATA => {json.dumps(vals, indent=4)}")
                    Tbr = self.env['inseta.wspatr.trained.beneficiaries.report']
                    obj = Tbr.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else Tbr.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))
            #trigger change to compute variance report
            self.wspatr_id.confirm_variance = True
            self.wspatr_id._onchange_trained_beneficiaries_report()

        if template == "Current Employment Profile":
            _logger.info("Importing Current Employment Profile...")
            no_employees_curr_emp_profile = []

            for count, row in enumerate(file_data):
                error = []
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[2]
                    self._validate_other_country(other_country)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        other_country = row[2],
                        african_male = int(row[3]) if isinstance(row[3], float) else row[3],
                        african_female = int(row[4]) if isinstance(row[4], float) else row[4],
                        african_disabled = int(row[5]) if isinstance(row[5], float) else row[5],
                        colored_male = int(row[6]) if isinstance(row[6], float) else row[6],
                        colored_female = int(row[7]) if isinstance(row[7], float) else row[7],
                        colored_disabled = int(row[8]) if isinstance(row[8], float) else row[8],
                        indian_male = int(row[9]) if isinstance(row[9], float) else row[9],
                        indian_female = int(row[10]) if isinstance(row[10], float) else row[10],
                        indian_disabled = int(row[11]) if isinstance(row[11], float) else row[11],
                        white_male = int(row[12]) if isinstance(row[12], float) else row[12],
                        white_female = int(row[13]) if isinstance(row[13], float) else row[13],
                        white_disabled = int(row[14]) if isinstance(row[14], float) else row[14],
                        other_male = int(row[15]) if isinstance(row[15], float) else row[15],
                        other_female = int(row[16]) if isinstance(row[16], float) else row[16],
                        other_disabled = int(row[17]) if isinstance(row[17], float) else row[17],
                        age1 = int(row[18]) if isinstance(row[18], float) else row[18],
                        age2 = int(row[19]) if isinstance(row[19], float) else row[19],
                        age3 = int(row[20]) if isinstance(row[20], float) else row[20],
                        age4 = int(row[21]) if isinstance(row[21], float) else row[21],
                    )
                    no_employees_curr_emp_profile.append(
                        sum([
                            vals.get('african_male'), 
                            vals.get('african_female'),
                            vals.get('indian_male'),
                            vals.get('indian_female'),
                            vals.get('colored_male'),
                            vals.get('colored_female'),
                            vals.get('white_male'),
                            vals.get('white_female'),
                            vals.get('other_male'),
                            vals.get('other_female')
                        ])
                    )
                    # _logger.info(f"WSP DATA => {json.dumps(vals, indent=4)}")
                    Profile = self.env['inseta.wspatr.employment.profile']
                    profile = Profile.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = profile.write(vals) if profile else Profile.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                        # record.wspatr_id._compute_no_employees_emp_profile()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))

            #update current employment profile
            self.wspatr_id.organisation_id.with_context(allow_write=True).write({
                'no_employees': sum(no_employees_curr_emp_profile)
            })


        for count, row in enumerate(file_data):
            error = []
            #ATR
            if template == "Implementation Report":
                try:

                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[9]
                    other_country_obj = self._validate_other_country(other_country)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        formsp_id = self._get_formsp_id(row[2]),
                        intervention_id = self._get_intervention_id(row[3]),
                        formspl_id = self._get_formspl_id(row[4]),
                        formspl_notes = row[5],
                        inseta_funding = row[6],
                        other_funding = row[7],
                        company_funding = row[8],
                        other_country = row[9],
                        other_country_id = other_country_obj and other_country_obj.id or False,
                        african_male = cast_to_integer(row[10]),
                        african_female = cast_to_integer(row[11]),
                        african_disabled = cast_to_integer(row[12]),
                        colored_male = cast_to_integer(row[13]),
                        colored_female = cast_to_integer(row[14]),
                        colored_disabled = cast_to_integer(row[15]),
                        indian_male = cast_to_integer(row[16]),
                        indian_female = cast_to_integer(row[17]),
                        indian_disabled = cast_to_integer(row[18]),
                        white_male = cast_to_integer(row[19]),
                        white_female = cast_to_integer(row[20]),
                        white_disabled = cast_to_integer(row[21]),
                        other_male = cast_to_integer(row[22]),
                        other_female = cast_to_integer(row[23]),
                        other_disabled = cast_to_integer(row[24]),
                        age1 = cast_to_integer(row[25]),
                        age2 = cast_to_integer(row[26]),
                        age3 = cast_to_integer(row[27]),
                        age4 = cast_to_integer(row[28]),
                    )
                    _logger.info(f"ATR DATA => {json.dumps(vals, indent=4)}")
                    ImplReport = self.env['inseta.wspatr.implementation.report']
                    obj = ImplReport.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                        ('programme_level','=',vals.get('programme_level')),
                        ('training_provider','=', vals.get('training_provider')),
                        ('completion_status','=', vals.get('completion_status')),
                        ('formsp_id','=', vals.get('formsp_id')),
                        ('intervention_id','=',vals.get('intervention_id')),
                        ('formspl_id','=',vals.get('formspl_id.id'))
                    ])
                    record = obj.write(vals) if obj else ImplReport.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))


            if template == "Learning Programmes":
                try:
                    _logger.info('Importing Learning Programmes ...')
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        formoccupation_id = self._get_formoccupation_id(row[0]),
                        learning_programme = row[1],
                        formsp_id = self._get_formsp_id(row[2]),
                        inseta_funding = row[3],
                        other_funding = row[4],
                        company_funding = row[5],
                        training_provider = row[6],
                        form_cred_id = self._get_form_cred_id(row[7]),
                        nqf_level_id = self._get_nqflevel_id(row[8]),
                        no_of_employees = row[9]
                    )
                    # _logger.info(f"ATR DATA => {json.dumps(vals, indent=4)}")
                    LearningProgramme = self.env['inseta.wspatr.learning.programmes']
                    obj = LearningProgramme.search([
                        ('formoccupation_id', '=', vals.get('formoccupation_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    obj.write(vals) if obj else LearningProgramme.create(vals)
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))


            if template == "Trained AET":
                _logger.info("Importing Trained AET...")
            
                start_dt, end_dt = False, False
                try:
                    start_dt = datetime(*xldate_as_tuple(row[9], workbook.datemode))
                except Exception as ex:
                    raise ValidationError(f"Invalid start date. The start date must be a VALID EXCEL DATE format. " 
                    "Please check the format of the date column and also ensure you are uploading the correct template")
                
                try:
                    end_dt = datetime(*xldate_as_tuple(row[10], workbook.datemode))
                except Exception as ex:
                    raise ValidationError(f"Invalid end date. The end date must be a VALID EXCEL DATE format. " 
                    "Please check the format of the date column and also ensure you are uploading the correct template")

                try:

                    if row[15] not in ('Yes','No'):
                        raise ValidationError('Funded By INSETA must either be "Yes" or "No"')

                    _logger.info(f"START Date => {start_dt}  END date => {end_dt}")
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        first_name = row[2],
                        last_name = row[3],
                        id_no = row[4],
                        equity_id = self._get_equity_id(row[5]),
                        gender_id = self._get_gender_id(row[6]),
                        disability_id = self._get_disability_id(row[7]),
                        municipality_id = self._get_municipality_id(row[8]),
                        aet_start_date = fields.Date.to_string(start_dt),
                        aet_end_date = fields.Date.to_string(end_dt),
                        training_provider = row[11],
                        aet_level_id = self._get_aet_level_id(row[12]),
                        aet_subject_id = self._get_aet_subject_id(row[13]),
                        learner_programme_status  = row[14],
                        is_inseta_funded = row[15],
                    )

                    _logger.info(f"ATR DATA => {json.dumps(vals, indent=4)}")
                    TrainedAet = self.env['inseta.wspatr.trained.aet']
                    obj = TrainedAet.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else TrainedAet.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))

            if template == "Pivotal Trained Beneficiaries":
                _logger.info("Importing Pivotal Trained Beneficiaries...")

                start_dt, end_dt = False, False
                try:
                    start_dt = datetime(*xldate_as_tuple(row[5], workbook.datemode))
                except Exception as ex:
                    raise ValidationError(f"Invalid start date. The start date must be a VALID EXCEL DATE format. " 
                    "Please check the format of the date column and also ensure you are uploading the correct template")
                
                try:
                    end_dt = datetime(*xldate_as_tuple(row[6], workbook.datemode))
                except Exception as ex:
                    raise ValidationError(f"Invalid end date. The end date must be a VALID EXCEL DATE format. " 
                    "Please check the format of the date column and also ensure you are uploading the correct template")
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[12]
                    self._validate_other_country(other_country)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        programme_level =  row[2],
                        training_provider = row[3],
                        completion_status = row[4] or False,
                        start_date = start_dt,
                        end_date = end_dt,
                        nqf_level_id = self._get_nqflevel_id(row[7]),
                        municipality_id = self._get_municipality_id(row[8]),
                        socio_economic_status = row[9],
                        pivotal_programme_id = self._get_pivotal_programme_id(row[10]),
                        other_pivotal_programme = row[11],
                        other_country = row[12],
                        african_male = cast_to_integer(row[13]),
                        african_female = cast_to_integer(row[14]),
                        african_disabled = cast_to_integer(row[15]),
                        colored_male = cast_to_integer(row[16]),
                        colored_female = cast_to_integer(row[17]),
                        colored_disabled = cast_to_integer(row[18]),
                        indian_male = cast_to_integer(row[19]),
                        indian_female = cast_to_integer(row[20]),
                        indian_disabled = cast_to_integer(row[21]),
                        white_male = cast_to_integer(row[22]),
                        white_female = cast_to_integer(row[23]),
                        white_disabled = cast_to_integer(row[24]),
                        other_male = cast_to_integer(row[25]),
                        other_female = cast_to_integer(row[26]),
                        other_disabled = cast_to_integer(row[27]),
                        age1 = cast_to_integer(row[28]),
                        age2 = cast_to_integer(row[29]),
                        age3 = cast_to_integer(row[30]),
                        age4 = cast_to_integer(row[31]),
                    )
                    # _logger.info(f"ATR DATA => {json.dumps(vals, indent=4)}")
                    Ptb = self.env['inseta.wspatr.pivotal.trained.beneficiaries']
                    obj = Ptb.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                        ('programme_level','=',vals.get('programme_level')),
                        ('training_provider','=', vals.get('training_provider')),
                        ('completion_status','=', vals.get('completion_status')),
                        ('start_date','=',vals.get('start_date')),
                        ('end_date','=',vals.get('end_date')),
                        ('nqf_level_id','=',vals.get('nqf_level_id.id')),
                        ('municipality_id','=',vals.get('municipality_id.id')),
                        ('socio_economic_status','=',vals.get('socio_economic_status')),
                        ('pivotal_programme_id','=',vals.get('pivotal_programme_id.id'))
                    ])
                    record = obj.write(vals) if obj else Ptb.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))

            #WSP

            if template == "Highest Educational Profile":
                _logger.info("Importing highest educational profile...")

                try:
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        formspl_id  = self._get_formspl_id(row[0]),
                        african_male = int(row[1]) if isinstance(row[1], float) else row[1],
                        african_female = int(row[2]) if isinstance(row[2], float) else row[2],
                        african_disabled = int(row[3]) if isinstance(row[3], float) else row[3],
                        colored_male = int(row[4]) if isinstance(row[4], float) else row[4],
                        colored_female = int(row[5]) if isinstance(row[5], float) else row[5],
                        colored_disabled = int(row[6]) if isinstance(row[6], float) else row[6],
                        indian_male = int(row[7]) if isinstance(row[7], float) else row[7],
                        indian_female = int(row[8]) if isinstance(row[8], float) else row[8],
                        indian_disabled = int(row[9]) if isinstance(row[9], float) else row[9],
                        white_male = int(row[10]) if isinstance(row[10], float) else row[10],
                        white_female = int(row[11]) if isinstance(row[11], float) else row[11],
                        white_disabled = int(row[12]) if isinstance(row[12], float) else row[12],
                        other_male = int(row[13]) if isinstance(row[13], float) else row[13],
                        other_female = int(row[14]) if isinstance(row[14], float) else row[14],
                        other_disabled = int(row[15]) if isinstance(row[15], float) else row[15],
                        age1 = int(row[16]) if isinstance(row[16], float) else row[16],
                        age2 = int(row[17]) if isinstance(row[17], float) else row[17],
                        age3 = int(row[18]) if isinstance(row[18], float) else row[18],
                        age4 = int(row[19]) if isinstance(row[19], float) else row[19],
                    )
                    _logger.info(f"WSP HIGHEST EDU PROFILE DATA => {json.dumps(vals, indent=4)}")

                    Profile = self.env['inseta.wspatr.highest.educational.profile']
                    profile = Profile.search([
                        ('formspl_id', '=', vals.get('formspl_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    if profile:
                        profile.write(vals)
                    else:
                        high_edu_profile = Profile.create(vals)
                        #high_edu_profile.wspatr_id._compute_no_employees_highest_edu_profile()

                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))

            if self.template == "Provincial Breakdown":
                try:
                    sdlno = row[0]
                    org = self.env['inseta.organisation'].search([('sdl_no','=', sdlno)])
                    if not org:
                        raise ValidationError(_("Organisation with sdl no '{sdlno}' not found").format(sdlno=sdlno))
                    siccode_id = self._get_siccode_id(row[1])
                    if not siccode_id:
                        raise ValidationError(f"Sic Code '{row[1]}' not found in the database")

                    if row[11] not in ('Small','Medium','Large'):
                        raise ValidationError(f"Wrong value for Company Size column. Please choose one of 'Small, Medium OR Large' ")

                    if row[12] not in ('Levy Payer','Non-Levy Payer'):
                        raise ValidationError(f"Wrong value for Levy Paying column. Please choose one of 'Levy Payer OR Non-Levy Payer' ")
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        sdl_no = sdlno,
                        sic_code_id = siccode_id,
                        easterncape = cast_to_integer(row[2]),
                        freestate = cast_to_integer(row[3]),
                        gauteng = cast_to_integer(row[4]),
                        kwazulunatal = cast_to_integer(row[5]),
                        limpopo = cast_to_integer(row[6]),
                        northwest = cast_to_integer(row[7]),
                        northerncape = cast_to_integer(row[8]),
                        mpumalanga = cast_to_integer(row[9]),
                        westerncape = cast_to_integer(row[10]),
                        company_size = row[11],
                        levy_status = 'Levy Paying' if row[12] == 'Levy Payer' else 'Non-Levy Paying',
                        noemployees = cast_to_integer(row[13]),
                        reasons = row[14]
                    )
                    Pb = self.env['inseta.wspatr.provincialbreakdown']
                    obj = Pb.search([
                        ('sdl_no', '=', vals.get('sdl_no')),
                        ('sic_code_id', '=', vals.get('sic_code_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else Pb.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_total()

                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))

            if template == "Pivotal_Planned_Beneficiaries_Small":
                _logger.info("Importing Pivotal Planned Beneficiaries")
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[6]
                    other_country_obj = self._validate_other_country(other_country)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        municipality_id = self._get_municipality_id(row[2]),
                        socio_economic_status = row[3],
                        pivotal_programme_id = self._get_pivotal_programme_id(row[4]),
                        other_pivotal_programme = row[5],
                        other_country = row[6],
                        african_male = cast_to_integer(row[7]),
                        african_female = cast_to_integer(row[8]),
                        african_disabled = cast_to_integer(row[9]),
                        colored_male = cast_to_integer(row[10]),
                        colored_female = cast_to_integer(row[11]),
                        colored_disabled = cast_to_integer(row[12]),
                        indian_male = cast_to_integer(row[13]),
                        indian_female = cast_to_integer(row[14]),
                        indian_disabled = cast_to_integer(row[15]),
                        white_male = cast_to_integer(row[16]),
                        white_female = cast_to_integer(row[17]),
                        white_disabled = cast_to_integer(row[18]),
                        other_male = cast_to_integer(row[19]),
                        other_female = cast_to_integer(row[20]),
                        other_disabled = cast_to_integer(row[21]),
                        age1 = cast_to_integer(row[22]),
                        age2 = cast_to_integer(row[23]),
                        age3 = cast_to_integer(row[24]),
                        age4 = cast_to_integer(row[25]),
                    )

                    Pivotal = self.env['inseta.wspatr.pivotal.planned.beneficiaries']
                    obj = Pivotal.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else Pivotal.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))
            
            if template == "Pivotal_Planned_Beneficiaries_Large":
                _logger.info(f"Importing Pivotal Planned Beneficiaries => {row[4]} {row[5]} {row[6]} {row[7]} {row[8]}")
                start_dt, end_dt = False, False
                try:
                    start_dt = datetime(*xldate_as_tuple(row[4], workbook.datemode))
                except Exception as ex:
                    raise ValidationError(f"Invalid start date. The start date must be a VALID EXCEL DATE format. " 
                    "Please check the format of the date column and also ensure you are uploading the correct template")
                
                try:
                    end_dt = datetime(*xldate_as_tuple(row[5], workbook.datemode))
                except Exception as ex:
                    raise ValidationError(f"Invalid end date. The end date must be a VALID EXCEL DATE format. " 
                    "Please check the format of the date column and also ensure you are uploading the correct template")

                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[10]
                    self._validate_other_country(other_country)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        programme_level =  row[2],
                        training_provider = row[3],
                        start_date = start_dt,
                        end_date = end_dt,
                        municipality_id = self._get_municipality_id(row[6]),
                        socio_economic_status = row[7],
                        pivotal_programme_id = self._get_pivotal_programme_id(row[8]),
                        other_pivotal_programme = row[9],
                        other_country = row[10],
                        african_male = cast_to_integer(row[11]),
                        african_female = cast_to_integer(row[12]),
                        african_disabled = cast_to_integer(row[13]),
                        colored_male = cast_to_integer(row[14]),
                        colored_female = cast_to_integer(row[15]),
                        colored_disabled = cast_to_integer(row[16]),
                        indian_male = cast_to_integer(row[17]),
                        indian_female = cast_to_integer(row[18]),
                        indian_disabled = cast_to_integer(row[19]),
                        white_male = cast_to_integer(row[20]),
                        white_female = cast_to_integer(row[21]),
                        white_disabled = cast_to_integer(row[22]),
                        other_male = cast_to_integer(row[23]),
                        other_female = cast_to_integer(row[24]),
                        other_disabled = cast_to_integer(row[25]),
                        age1 = cast_to_integer(row[26]),
                        age2 = cast_to_integer(row[27]),
                        age3 = cast_to_integer(row[28]),
                        age4 = cast_to_integer(row[29]),
                    )
                    _logger.info(f'Vals =>  {json.dumps(str(vals), indent=4)}')

                    Pivotal = self.env['inseta.wspatr.pivotal.planned.beneficiaries']
                    obj = Pivotal.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else Pivotal.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nPlease ensure you are uploading the correct template').format(e=ex))

            if self.template == "Planned_Beneficiaries_Small":
                _logger.info("Importing Planned Beneficiaries/ Workplace Skills Plan (small firms)...")
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[6]
                    self._validate_other_country(other_country)
                    programme_level =  row[2] and row[2].strip() or ''
                    if programme_level not in ('Entry', 'Intermediate', 'Advanced'):
                        raise ValidationError(_(
                            'Wrong Value {level} for Programme Level. Allowed Programme Levels are:\n'
                            'Entry\nIntermediate\nAdvanced'
                            'Please note the casing.'
                        ).format(
                            level = programme_level
                        ))
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        programme_level =  row[2],
                        formsp_id = self._get_formsp_id(row[3]),
                        formspl_id = self._get_formspl_id(row[4]),
                        formspl_notes =  row[5],
                        other_country = row[6],
                        african_male = cast_to_integer(row[7]),
                        african_female = cast_to_integer(row[8]),
                        african_disabled = cast_to_integer(row[9]),
                        colored_male = cast_to_integer(row[10]),
                        colored_female = cast_to_integer(row[11]),
                        colored_disabled = cast_to_integer(row[12]),
                        indian_male = cast_to_integer(row[13]),
                        indian_female = cast_to_integer(row[14]),
                        indian_disabled = cast_to_integer(row[15]),
                        white_male = cast_to_integer(row[16]),
                        white_female = cast_to_integer(row[17]),
                        white_disabled = cast_to_integer(row[18]),
                        other_male = cast_to_integer(row[19]),
                        other_female = cast_to_integer(row[20]),
                        other_disabled = cast_to_integer(row[21]),
                        age1 = cast_to_integer(row[22]),
                        age2 = cast_to_integer(row[23]),
                        age3 = cast_to_integer(row[24]),
                        age4 = cast_to_integer(row[25]),
                    )
                    _logger.info(json.dumps(vals, indent=4))
                    WSP = self.env['inseta.wspatr.workplaceskillsplan']
                    obj = WSP.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                        ('programme_level','=',vals.get('programme_level')),
                        ('formsp_id','=',vals.get('formsp_id')),
                        ('formspl_id','=',vals.get('formspl_id'))
                    ])
                    record = obj.write(vals) if obj else WSP.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()

                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nPlesae ensure you are uploading the correct template').format(e=ex))

            if self.template == "Planned_Beneficiaries_Large":
                _logger.info("Importing Planned Beneficiaries...")
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[5]
                    self._validate_other_country(other_country)
                    programme_level =  row[2]
                    if programme_level not in ('Entry', 'Intermediate', 'Advanced'):
                        raise ValidationError(_(
                            'Wrong Value {val} for Programme Level. Allowed Programme Levels are:\n '
                            'Entry\nIntermediate\nAdvanced .\n'
                            'Please note the casing.'
                        ).format(
                            val = programme_level
                        ))
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        programme_level =  row[2],
                        municipality_id = self._get_municipality_id(row[3]),
                        formsp_id = self._get_formsp_id(row[4]),
                        other_country = row[5],
                        african_male = cast_to_integer(row[6]),
                        african_female = cast_to_integer(row[7]),
                        african_disabled = cast_to_integer(row[8]),
                        colored_male = cast_to_integer(row[9]),
                        colored_female = cast_to_integer(row[10]),
                        colored_disabled = cast_to_integer(row[11]),
                        indian_male = cast_to_integer(row[12]),
                        indian_female = cast_to_integer(row[13]),
                        indian_disabled = cast_to_integer(row[14]),
                        white_male = cast_to_integer(row[15]),
                        white_female = cast_to_integer(row[16]),
                        white_disabled = cast_to_integer(row[17]),
                        other_male = cast_to_integer(row[18]),
                        other_female = cast_to_integer(row[19]),
                        other_disabled = cast_to_integer(row[20]),
                        age1 = cast_to_integer(row[21]),
                        age2 = cast_to_integer(row[22]),
                        age3 = cast_to_integer(row[23]),
                        age4 = cast_to_integer(row[24]),
                    )
                    _logger.info(f'Vals =>  {json.dumps(vals)}')
                    PlannedBeneficiaries = self.env['inseta.wspatr.planned.beneficiaries']
                    obj = PlannedBeneficiaries.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                        ('programme_level','=',vals.get('programme_level')),
                        ('municipality_id','=',vals.get('municipality_id')),
                        ('formsp_id','=',vals.get('formsp_id'))
                    ])
                    record = obj.write(vals) if obj else PlannedBeneficiaries.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()

                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nPlease ensure you are uploading the correct template').format(e=ex))

            if self.template == "Skills Gap":
                _logger.info("Importing Skills Gap...")
                # ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                # province_name = row[1]
                # if 'Natal' in province_name:
                #     province_name = 'KwaZulu-Natal'
                # province_id = self._get_province_id(province_name)
                try:
                    pass
                    # vals = dict(
                    #     wspatr_id = self.wspatr_id.id,
                    #     ofo_occupation_id  = ofo_occupation_id,
                    #     province_id = province_id,
                    #     vacancyreason_ids = [(4, self._get_object_id_by_name('res.vacancyreason', row[2]))]
                    # )
                    # Hfv = self.env['inseta.wspatr.hardtofillvacancies']
                    # obj = Hfv.search([
                    #     ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                    #     ('province_id', '=', vals.get('province_id')),
                    #     # ('vacancyreason_id','=',vals.get('vacancyreason_id')),
                    #     ('wspatr_id', '=', vals.get('wspatr_id')),
                    # ])
                    # record = obj.write(vals) if obj else Hfv.create(vals)

                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error.\nThe Server encountered error while importing ' 
                        'Skills Gap. Please crosscheck and ensure you are uploading the correct template'))

            if self.template == "Hard To Fill Vacancies":
                _logger.info("Importing Hard To Fill Vacancies...")
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    province_name = row[1]
                    if 'Natal' in province_name:
                        province_name = 'KwaZulu-Natal'
                    province_id = self._get_province_id(province_name)
                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        province_id = province_id,
                        vacancyreason_ids = [(4, self._get_object_id_by_name('res.vacancyreason', row[2]))]
                    )
                    Hfv = self.env['inseta.wspatr.hardtofillvacancies']
                    obj = Hfv.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('province_id', '=', vals.get('province_id')),
                        # ('vacancyreason_id','=',vals.get('vacancyreason_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else Hfv.create(vals)

                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error.\nThe Server encountered error while importing ' 
                        'Hard To Fill Vacancies. Please crosscheck and ensure you are uploading the correct template'))

            if self.template == "Planned AET Training":
                _logger.info("Importing Planned AET Training...")
                try:
                    ofo_occupation_id  = self._get_ofo_occupation_id(row[0])
                    ofo_specialization_id = self._get_ofo_specialization_id(row[1])
                    self._validate_ofo_code(ofo_occupation_id, ofo_specialization_id)
                    other_country = row[2]
                    self._validate_other_country(other_country)

                    vals = dict(
                        wspatr_id = self.wspatr_id.id,
                        ofo_occupation_id  = ofo_occupation_id,
                        ofo_specialization_id = ofo_specialization_id,
                        other_country = other_country,
                        african_male = cast_to_integer(row[3]),
                        african_female = cast_to_integer(row[4]),
                        african_disabled = cast_to_integer(row[5]),
                        colored_male = cast_to_integer(row[6]),
                        colored_female = cast_to_integer(row[7]),
                        colored_disabled = cast_to_integer(row[8]),
                        indian_male = cast_to_integer(row[9]),
                        indian_female = cast_to_integer(row[10]),
                        indian_disabled = cast_to_integer(row[11]),
                        white_male = cast_to_integer(row[12]),
                        white_female = cast_to_integer(row[13]),
                        white_disabled = cast_to_integer(row[14]),
                        other_male = cast_to_integer(row[15]),
                        other_female = cast_to_integer(row[16]),
                        other_disabled = cast_to_integer(row[17]),
                        age1 = cast_to_integer(row[18]),
                        age2 = cast_to_integer(row[19]),
                        age3 = cast_to_integer(row[20]),
                        age4 = cast_to_integer(row[21]),
                    )
                    AetTraining = self.env['inseta.wspatr.planned.aet.training']
                    obj = AetTraining.search([
                        ('ofo_occupation_id', '=', vals.get('ofo_occupation_id')),
                        ('ofo_specialization_id', '=', vals.get('ofo_specialization_id')),
                        ('wspatr_id', '=', vals.get('wspatr_id')),
                    ])
                    record = obj.write(vals) if obj else AetTraining.create(vals)
                    if record and not isinstance(record, bool):
                        record._compute_ofo_specialization()
                except Exception as ex:
                    _logger.exception(ex)
                    raise ValidationError(_('Import Error\n{e}\nEnsure you are uploading the correct template').format(e=ex))


    def _validate_other_country(self, other_country):
        if not isinstance(other_country, str):
            return
        country_name = other_country.replace(" ","")
        if country_name and len(country_name) > 1:

            record = self.env['res.country'].search([('name','ilike',country_name)],limit=1)
            if not record:
                raise ValidationError(
                    _(
                        "Wrong value for Foreign Country '{country}'.\n"
                        "You can copy and paste this URL {base_url}/web#model=res.country&view_type=list on your browser to get the list of acceptable country names"
                    ).format(
                        country=country_name,
                        base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    )
                )
            return record

    def _validate_ofo_code(self, ofo_occupation_id, ofo_specialization_id):
        ofo_occ = self.env['res.ofo.occupation'].search([('id','=',ofo_occupation_id)])
        ofo_spec = self.env['res.ofo.specialization'].search([('id','=',ofo_specialization_id)])

        ofo_occ_code =  ofo_occ  and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            raise ValidationError(
                _(
                    "Wrong Ofo Specializtion Code '{spec_code}' for Occupation '{occ}' '{occ_code}'.\n"
                    "Please select OFO Specialisation that has the same code as the Ofo Occupation '{occ}'"
                ).format(
                    occ_code=ofo_occ.code,
                    occ=ofo_occ.name,
                    spec_code=ofo_spec.code,
                )
            )

    def _get_object_id_by_name(self, model, name):
        if name:
            obj = self.env[model].search([('name', '=',name)],limit=1)
            return obj and obj.id or False

    def _get_province_id(self, name):
        if name:
            obj = self.env['res.country.state'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Sic Code '{name}' not found in the database")
            return obj and obj.id or False

    def _get_siccode_id(self, name):
        if name:
            code = name.split(' ')[0]
            obj = self.env['res.sic.code'].search([('siccode', '=',code)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Sic Code '{name}' not found in the database")
            return obj and obj.id or False

    def _get_intervention_id(self, name):
        if name:
            obj = self.env['res.intervention'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Intervention '{name}' not found in the database")
            return obj and obj.id or False
        

    def _get_form_cred_id(self, name):
        if name:
            obj = self.env['res.formcred'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Credit Bearing '{name}' not found in the database")
            return obj and obj.id or False

    def _get_aet_level_id(self, name):
        if name:
            obj = self.env['res.aetlevel'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"AET Level '{name}' not found in the database")
            return obj and obj.id or False

    def _get_aet_subject_id(self, name):
        if name:
            obj = self.env['res.aetsubject'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"AET Subject '{name}' not found in the database")
            return obj and obj.id or False
        

    def _get_disability_id(self, name):
        if name:
            obj = self.env['res.disability'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Disability '{name}' not found in the database")
            return obj and obj.id or False

    def _get_gender_id(self, name):
        if name:
            obj = self.env['res.gender'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Gender '{name}' not found in the database")
            return obj and obj.id or False

    def _get_equity_id(self, name):
        if name:
            obj = self.env['res.equity'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Equity '{name}' not found in the database")
            return obj and obj.id or False

    def _get_nqflevel_id(self, name):
        if name:
            obj = self.env['res.nqflevel'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"NQF Level '{name}' not found in the database")
            return obj and obj.id or False

    def _get_pivotal_programme_id(self, name):
        if name:
            code = name.split(' ')[0]
            obj = self.env['res.pivotal.programme'].search([('saqacode', '=',code)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Pivotal Programme '{name}' not found")
            return obj and obj.id or False

    def _get_municipality_id(self, name):
        if name:
            obj = self.env['res.municipality'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Municipality '{name}' not found")
            return obj and obj.id or False

    def _get_formoccupation_id(self, name):
        if name:
            obj = self.env['res.formoccupation'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Occupation Description '{name}' not found")
            return obj and obj.id or False

    def _get_ofo_occupation_id(self, name):
        if name:
            code = name.split(' ')[0]
            occ = self.env['res.ofo.occupation'].search([('code', '=',code)],limit=1)
            return occ and occ.id or False

    def _get_ofo_specialization_id(self, name):
        if name:
            code = name.split(' ')[0]
            spec = self.env['res.ofo.specialization'].search([('code', '=',code)],limit=1)
            return spec and spec.id or False

    def _get_formsp_id(self, name):
        if name:
            obj = self.env['res.formsp'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Scarce and Critical Skills Priority '{name}' not found in the database")
            return obj and obj.id or False

    def _get_formspl_id(self, name):
        if name:
            obj = self.env['res.formspl'].search([('name', '=',name)],limit=1)
            # if not obj:
            #     raise ValidationError(f"Description '{name}' not found in the database")
            return obj and obj.id or False
