import base64
import calendar
from xlwt import easyxf, Workbook
import logging
from io import BytesIO
import json
import threading

from odoo.tools import date_utils
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class InsetaWspAtrError(models.Model):
    _inherit = 'inseta.wspatr'


    def action_generate_wsp_error(self):

        # --------------------------------------------
        # Current Employment Profile
        # --------------------------------------------
        current_employment_list = []
        self._cr.execute("select id, ofo_occupation_id, ofo_specialization_id, other_country,\
            african_male,african_female,indian_male,indian_female, colored_male,colored_female,white_male, \
            white_female, other_male,other_female,age1,age2,age3,age4 from inseta_wspatr_employment_profile where wspatr_id = %s",(self.id,))
        current_employment_profile_ids = self._cr.fetchall()
        _logger.info( f"Current Employment Profile => {current_employment_profile_ids}")
        # for total_employment_data in current_employment_profile_ids:
        #     # Validations for Employee ID
        #     if total_employment_data[3] in ['sa', 'dual']:
        #         id_number = total_employment_data[4]
        #         if id_number:
        #             if total_employment_data[3] in ['sa', 'dual'] and total_employment_data[5] == 'passport':
        #                 pass
        #             else:
        #                 if not id_number.isdigit():
        #                     msg += 'Employee ID should be numeric <b>' + \
        #                         str(id_number) + \
        #                         '</b> Total Employment Profile!='
        #                     current_employment_list.append(total_employment_data[0])
        #                 else:
        #                     year = id_number[:2]
        #                     id_number = id_number[2:]
        #                     month = id_number[:2]
        #                     id_number = id_number[2:]
        #                     day = id_number[:2]
        #                     if int(month) > 12 or int(month) < 1 or int(day) > 31 or int(day) < 1:
        #                         msg += 'Incorrect Identification Number <b>' + \
        #                             str(id_number) + \
        #                             '</b> in Total Employment Profile!='
        #                         current_employment_list.append(total_employment_data[0])
        #                     else:
        #                         # # Calculating last day of month.
        #                         x_year = int(year)
        #                         if x_year == 00:
        #                             x_year = 2000
        #                         last_day = calendar.monthrange(
        #                             int(x_year), int(month))[1]
        #                         if int(day) > last_day:
        #                             msg += 'Incorrect Identification Number <b>' + \
        #                                 str(id_number) + \
        #                                 '</b> in Total Employment Profile!='
        #                             current_employment_list.append(total_employment_data[0])
        #     # Validations on Name and Surname
        #     if total_employment_data[1] and total_employment_data[1].isdigit():
        #         msg += 'Name should not be numeric: <b>' + \
        #             str(total_employment_data[1]) + \
        #             '</b> in Total Employment Profile!='
        #         current_employment_list.append(total_employment_data[1])
        #     if total_employment_data[2] and total_employment_data[2].isdigit():
        #         msg += 'Surname should not be numeric: <b>' + \
        #             str(total_employment_data[2]) + \
        #             '</b> in Total Employment Profile!='
        #         current_employment_list.append(total_employment_data[2])
        #     # Validations on occupation and code
        #     if total_employment_data[6] and total_employment_data[7]:
        #         self._cr.execute('select id from ofo_code where occupation = %s',(total_employment_data[7],))
        #         ofo_occupation_id = self._cr.fetchone()
        #         if ofo_occupation_id:
        #             if total_employment_data[6] != ofo_occupation_id[0]:
        #                 msg += 'Wrong occupation for OFO code <b>' + str(self.env['ofo.code'].browse(
        #                     total_employment_data[6]).name or '') + '</b> in Total Employment Profile!='
        #                 current_employment_list.append(total_employment_data[0])

        wb = Workbook(encoding='utf8')
        worksheet1 = wb.add_sheet('Current Employment Profile')
        worksheet2 = wb.add_sheet('Highest Educational Profile')
        worksheet3 = wb.add_sheet('Pivotal Planned Beneficiaries')
        worksheet4 = wb.add_sheet('Planned Beneficiaries')
        worksheet5 = wb.add_sheet('Planned AET Training')
        worksheet6 = wb.add_sheet('Training Planned')

        headers1 = ["OFO Occupation","OFO Specialisation",]
        col_heading_style = easyxf('font: colour white, height 200; pattern: pattern solid, fore_color dark_blue;')
        date_style = easyxf(num_format_str='mm/dd/yyyy')

        colh = 0
        for head in headers1:
            worksheet1.write(0, colh, head, col_heading_style)
            worksheet1.col(colh).width = 8000
            colh += 1
        
        row = 1
        # if isinstance(val, date):
        #     style = date_style

        fp = BytesIO()
        wb.save(fp)
        filename = f"WSP_error_log_{self.sdl_no}.xlsx"
        file_binary = base64.encodebytes(fp.getvalue())
        fp.close()
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_binary,
            'type': 'binary',
            'res_id': self.id,
            'res_model': 'inseta.wspatr',
            'description': f"WSP Error log for employer [{self.sdl_no}] created on {fields.Datetime.now()}"
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}/{filename}?download=true",
            'target': 'new',
        }