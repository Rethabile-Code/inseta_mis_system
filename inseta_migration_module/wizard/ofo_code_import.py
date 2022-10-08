import base64
# from dataclasses import field
import json
import logging
from operator import index
from os import name
import re
import timeit

from xlrd import open_workbook

from odoo import fields, models, _
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



class OfoCodeImportWizard(models.TransientModel):
    _name = 'ofocode.import.wizard'
    _description = "Import Ofo Codes"

    file_type = fields.Selection(
        [('xlsx', 'XLSX File')], default='xlsx', string='File Type')
    file = fields.Binary(string="Upload File (.xlsx)")
    model = fields.Selection([
        ('res.ofo.majorgroup', 'Major Group'),
        ('res.ofo.submajorgroup', 'Sub Major Group'),
        ('res.ofo.minorgroup', 'Minor Group'),
        ('res.ofo.unitgroup', 'Unit Group'),
        ('res.ofo.occupation', 'OFO Occupation'),
        ('res.ofo.specialization', 'OFO Specialization'),
        ('update_occ', 'Update Occupation'),
        ('update_spec', 'Update Specialization'),
    ])

    def _get_sheet_index(self):
        if self.model == 'res.ofo.majorgroup':
            index = 3
        elif self.model == 'res.ofo.submajorgroup':
            index = 4
        elif self.model == 'res.ofo.minorgroup':
            index = 5
        elif self.model == 'res.ofo.unitgroup':
            index = 6
        elif self.model == 'res.ofo.occupation':
            index = 7
        else:
            index = 8
        return index


    def _get_major_group(self,itemcode):
        if not itemcode:
            return
        major_code = itemcode[:6]
        _logger.info(f"Major code {major_code}")

        major_group = self.env['res.ofo.majorgroup'].search([('code','=',major_code)])
        _logger.info(f"{major_group}")
        return major_group

    def _get_submajor_group(self,itemcode):
        if not itemcode:
            return
        code = itemcode[:7]
        _logger.info(f"Sub Major code {code}")

        submajor_group = self.env['res.ofo.submajorgroup'].search([('code','=',code)])
        _logger.info(f"{submajor_group}")
        return submajor_group

    def _get_minor_group(self,itemcode):
        if not itemcode:
            return
        code = itemcode[:8]
        _logger.info(f" Minor grp code {code}")

        group = self.env['res.ofo.minorgroup'].search([('code','=',code)])
        _logger.info(f"{group}")
        return group

    def _get_unit_group(self,itemcode):
        if not itemcode:
            return
        code = itemcode[:9]
        group = self.env['res.ofo.unitgroup'].search([('code','=',code)])
        _logger.info(f"{group}")
        return group

    def _get_occupation(self,code):
        if not code:
            return
        occ = self.env['res.ofo.occupation'].search([('code','=',code)])
        _logger.info(f"{occ}")
        return occ


    def action_import(self):
        if not self.file:
            raise ValidationError('Please select a file')

        Model = False
        if self.model not in ['update_occ','update_spec']:
            Model = self.env[self.model]

        index = self._get_sheet_index()
        file_datas = base64.decodebytes(self.file)
        workbook = open_workbook(file_contents=file_datas)
        sheet = workbook.sheet_by_index(index)
        file_data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
        file_data.pop(0)

        _logger.info("Importing OFO Codes ...")
        loop = 0
        for count, row in enumerate(file_data):
# --------------------------------------------
            if self.model == "res.ofo.majorgroup":
                vals = dict(
                    code = int(row[0]) if isinstance(row[0], float) else row[0],
                    name = row[1],
                    ofoyear = int(row[2]) if isinstance(row[2], float) else row[2],
                    version_no = int(row[3]) if isinstance(row[3], float) else row[3],
                )
                _logger.info(vals)
                obj = Model.search([('code', '=', vals.get('code'))])
                if obj:
                    obj.write(vals)
                else:
                    Model.create(vals)
            if self.model == "res.ofo.submajorgroup":
                code = int(row[0]) if isinstance(row[0], float) else row[0]
                major_grp = self._get_major_group(code)
                vals = dict(
                    major_group_id = major_grp.id,
                    code = code,
                    name = row[1],
                    ofoyear = major_grp.ofoyear
                )
                obj = Model.search([('code', '=', vals.get('code'))])
                if obj:
                    obj.write(vals)
                else:
                    Model.create(vals)
            if self.model == "res.ofo.minorgroup":
                code = int(row[0]) if isinstance(row[0], float) else row[0]
                #major_grp = self._get_major_group(code)
                submajor_grp = self._get_submajor_group(code)
                vals = dict(
                    sub_major_group_id = submajor_grp.id,
                    code = code,
                    name = row[1],
                    ofoyear = submajor_grp.ofoyear
                )
                _logger.info(vals)
                obj = Model.search([('code', '=', vals.get('code'))])
                if obj:
                    obj.write(vals)
                else:
                    Model.create(vals)

            if self.model == "res.ofo.unitgroup":
                code = int(row[0]) if isinstance(row[0], float) else row[0]
                minor_grp = self._get_minor_group(code)
                #submajor_grp = self._get_submajor_group(code)

                vals = dict(
                    minor_group_id = minor_grp.id,
                    sub_major_group_id = minor_grp.sub_major_group_id.id,
                    code = code,
                    name = row[1],
                    ofoyear = minor_grp.ofoyear
                )
                _logger.info(vals)
                obj = Model.search([('code', '=', vals.get('code'))])
                if obj:
                    obj.write(vals)
                else:
                    Model.create(vals)
            if self.model == "res.ofo.occupation":
                code = int(row[0]) if isinstance(row[0], float) else row[0]
                unit_grp = self._get_unit_group(code)
                vals = dict(
                    unit_group_id = unit_grp.id,
                    code = code,
                    name = row[1],
                    trade = row[2],
                    green_occupation = row[3],
                    green_skill = row[4],
                    ofoyear = unit_grp.ofoyear
                )
                obj = Model.search([('code', '=', vals.get('code'))])
                if obj:
                    obj.write(vals)
                else:
                    Model.create(vals)
            if self.model == "res.ofo.specialization":
                code = int(row[0]) if isinstance(row[0], float) else row[0]
                occ = self._get_occupation(code)
                vals = dict(
                    occupation_id = occ.id,
                    code = code,
                    name = row[1],
                    ofoyear = occ.ofoyear
                )
                obj = Model.search([('code', '=', vals.get('code')),('name', '=', vals.get('name'))])
                if obj:
                    obj.write(vals)
                else:
                    Model.create(vals)
            
            if self.model == "update_occ":
                occs = self.env['res.ofo.occupation'].search([])
                for occ in occs:
                    _logger.info(f"updating ofo occ {occ.name}")

                    major_group  = occ.unit_group_id.sub_major_group_id.major_group_id
                    ofoyear = major_group and major_group.ofoyear or False
                    if ofoyear and not occ.ofoyear:
                        occ.write({'ofoyear': ofoyear})

            if self.model == "update_spec":
                specs = self.env['res.ofo.specialization'].search([])
                for spec in specs:
                    _logger.info(f"updating ofo spec {spec.name}")

                    major_group  = spec.occupation_id.unit_group_id.sub_major_group_id.major_group_id
                    ofoyear = major_group and major_group.ofoyear or False
                    if ofoyear and not spec.ofoyear:
                        occ.write({'ofoyear': ofoyear})

