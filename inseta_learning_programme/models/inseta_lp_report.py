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


class InsetaEmployerLPReport(models.TransientModel):
    _name = "inseta.employer_lp.report"

    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    excel_file = fields.Binary('Download Excel file', filename='filename', readonly=True)
    filename = fields.Char('Excel File', size=64)

    organisation_id = fields.Many2one(
        'inseta.organisation', 
        required=False, 
        tracking=True, default=lambda s: s.get_employer_default_user())

    organisation_sdl = fields.Char(string='Employer SDL / N')
    financial_year_id = fields.Many2one('res.financial.year', required=False,tracking=True)
    dg_application_id = fields.Many2one('inseta.dgapplication')
    employer_report_type = fields.Boolean('Employer report')
    lp_division_report_type = fields.Boolean('LP Division')

    # @api.onchange('organisation_id')
    # def _get_organisation_id(self):
    #     if self.organisation_id:
    #         self.organisation_sdl = self.organisation_id.employer_sdl_no

    @api.onchange('organisation_sdl')
    def _get_related_dg(self):
        if self.organisation_sdl:
            self.financial_year_id = False
            self.dg_application_id = False
            organisation_id = self.env['inseta.organisation'].search([('employer_sdl_no', '=', self.organisation_sdl)], limit=1)
            if not organisation_id:	
                return {
                    'warning': {
                        'title': "Validation !!!",
                        'message':"No Employer record found for the SDL"
                    },
                    'domain': {
                        'financial_year_id': [('id', '=', None)]
                    }
                }
            self.organisation_id = organisation_id.id
            dg = self.env['inseta.dgapplication'].search([('sdl_no', '=', self.organisation_sdl), ('state', 'in', ['approve', 'signed'])])
            if dg:
                return {
                    'domain': {
                        'financial_year_id': [('id', 'in', [rec.financial_year_id.id for rec in dg])] if dg else [('id', 'in', None)]
                    }
                }
            else:
                return {
                    'warning': {
                        'title': "Validation !!!",
                        'message':"No DG found for this Employer"
                    },
                    'domain': {
                        'financial_year_id': [('id', '=', None)]
                    }
                }	 

    @api.onchange('financial_year_id')
    def _onchange_financial_year(self):
        if self.organisation_sdl:
            self.dg_application_id = False
            dg = self.env['inseta.dgapplication'].search([
                ('financial_year_id', '=', self.financial_year_id.id),
                ('organisation_id', '=', self.organisation_id.id), 
                ('state', 'in', ['approve', 'signed'])
                ])
            
            return {
                    'domain': {
                        'dg_application_id': [('id', 'in', [rec.id for rec in dg])] if dg else [('id', 'in', None)]
                    }
                }

    @api.onchange('employer_report_type')
    def _onchange_employer_report_type(self):
        if self.employer_report_type and self.lp_division_report_type:
            return {
                    'warning': {
                        'title': "Validation !!!",
                        'message':"Please uncheck one of the box to continue"
                    }}

    @api.onchange('lp_division_report_type')
    def _onchange_lp_division_report_type(self):
        if self.lp_division_report_type and self.employer_report_type:
            return {
                    'warning': {
                        'title': "Validation !!!",
                        'message':"Please uncheck one of the box to continue"
                    }}

    def export_data(self):
        domain = []
        style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
            num_format_str='#,##0')
        style1 = xlwt.easyxf(num_format_str='DD-MMM-YYYY')
        wb = xlwt.Workbook()
        ws = wb.add_sheet('REPORT')
        colh = 0
        if self.employer_report_type == True:
            headers = [
                'Project Name', 'Application- Total Beneficiaries', 'Applications - Total Value',
                'Recommended(Total Beneficiaries)', 'Recommended(Total Value)', 'Project reference',
                'Final Allocation Number(Total Beneficiaries)', 'Final Allocation(Total Value)'
                ]
    
            dg_evaluation_dgs = self.dg_application_id.mapped('evaluation_ids')
            if dg_evaluation_dgs:
                ws.write(0, 3, 'LEARNING PROGRAMMING EMPLOYER RECORDS GENERATED')
                for head in headers:
                    ws.write(1, colh, head)
                    colh += 1
                row = 3 
                for records in dg_evaluation_dgs:
                    col = 0
                    name = self.dg_application_id.dgtype_id.name or ""
                    no_applied_learners =records.total_learners or 0
                    no_amount_applied =records.amount_applied or 0
                    no_learners_recommended = records.no_learners_recommended or 0
                    amount_total_recommended = records.amount_total_recommended or 0
                    project_reference = records.name or 0
                    no_learners_approved = records.no_learners_approved or 0
                    amount_total_approved = records.amount_total_approved or 0 

                    ws.write(row, col, name)
                    ws.write(row, col + 1, no_applied_learners, style1)
                    ws.write(row, col + 2, no_amount_applied)
                    ws.write(row, col + 3, no_learners_recommended)
                    ws.write(row, col + 4, amount_total_recommended)
                    ws.write(row, col + 5, project_reference)
                    ws.write(row, col + 6, no_learners_approved)
                    ws.write(row, col + 7, amount_total_approved) 
                    row += 1
                fp = io.BytesIO()
                wb.save(fp)
                filename = "EMPLOYER DG REPORT ON {}.xls".format(datetime.strftime(fields.Date.today(), '%Y-%m-%d'), style0)
                self.excel_file = base64.encodestring(fp.getvalue())
                self.filename = filename
                fp.close()
            else:
                raise ValidationError('No DG Evaluation(s) found for the selected Application')
        elif self.lp_division_report_type == True:
            headers = [
                'Employer Name', 'SDL Number', 'Company Size',
                'Province', 'Application (Total Beneficiaries)', 'Programme Name',
                'Applications(Total Value)', 'Recommended(Total Beneficiaries)', 'Recommended(Total value)',
                 'Project reference',  'Final Allocation(Total Beneficiaries)',  'Final Allocation(Total Value)',  
                ]
             
            domain = []
            if self.financial_year_id:
                domain += [('financial_year_id', '=', self.financial_year_id.id)]

            lp_objs = self.env['inseta.lpro'].search(domain)
            if lp_objs:
                ws.write(0, 3, 'LEARNING PROGRAMMING REPORTS')
                for head in headers:
                    ws.write(1, colh, head)
                    colh += 1
                row = 3 
                for records in lp_objs:
                    col = 0
                    organisation_name = records.organisation_id.name or ""
                    organisation_sdl = records.organisation_sdl or ""
                    organisation_size = records.organisation_id.organisation_size_id.name or ""
                    province = records.organisation_id.physical_province_id.name or ""
                    applied_learners = records.dg_application_id.no_learners or 0
                    programme_name = records.dg_application_id.dgtype_id.name or ""
                    apllied_total_amount = records.dg_application_id.amount_total_applied or 0
                    recommended_learners = sum([rec.no_learners_recommended for rec in records.dg_application_id.mapped('evaluation_ids')]) or 0
                    recommend_amount = sum([rec.amount_total_recommended for rec in records.dg_application_id.mapped('evaluation_ids')]) or 0
                    project_reference = records.dg_application_id.name or ""
                    approved_learners = records.dg_application_id.no_learners_approved or 0
                    approved_amount = records.dg_application_id.amount_total_approved

                    ws.write(row, col, organisation_name)
                    ws.write(row, col + 1, organisation_sdl, style1)
                    ws.write(row, col + 2, organisation_size)
                    ws.write(row, col + 3, province)
                    ws.write(row, col + 4, applied_learners)
                    ws.write(row, col + 5, programme_name)
                    ws.write(row, col + 6, apllied_total_amount)
                    ws.write(row, col + 7, recommended_learners) 
                    ws.write(row, col + 8, recommend_amount) 
                    ws.write(row, col + 9, project_reference) 
                    ws.write(row, col + 10, approved_learners) 
                    ws.write(row, col + 11, approved_amount)

                    row += 1
                fp = io.BytesIO()
                wb.save(fp)
                filename = "LP REPORT ON {}.xls".format(datetime.strftime(fields.Date.today(), '%Y-%m-%d'), style0)
                self.excel_file = base64.encodestring(fp.getvalue())
                self.filename = filename
                fp.close()
            else:
                raise ValidationError('No LP found to be generated')

    def button_export_records(self):
        self.export_data()
        self.financial_year_id = False
        self.dg_application_id = False
        self.excel_file = False

    def button_export_and_download(self):
        self.export_data()
        return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model=inseta.employer_lp.report&download=true&field=excel_file&id={}&filename={}'.format(self.id, self.filename),
                'target': 'new',
                'nodestroy': False,
        }

