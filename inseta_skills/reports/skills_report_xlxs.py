
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, _


class ReportOrganisationsXlxs(models.AbstractModel):
    _name = 'report.inseta_skills.report_organisation_xlxs'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Organisations Report Excel'

    def generate_xlsx_report(self, workbook, data, wizard):
        num_format = wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        report = wizard.report_id

        def _header_sheet(sheet):
            sheet.write(0, 4, report.name, report_format)
            sheet.write(2, 0, _('Company:'), bold)
            sheet.write(3, 0, wizard.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % report.print_time)

            sheet.write(2, 2, _('Start Date : %s ') % wizard.date_from if wizard.date_from else '')
            sheet.write(3, 2, _('End Date : %s ') % wizard.date_to if wizard.date_to else '')

            # sheet.write(2, 4, _('Target Moves:'), bold)
            # sheet.write(3, 4, _('All Entries') if wizard.target_move == 'all' else _('All Posted Entries'))


  
