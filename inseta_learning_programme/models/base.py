# -*- coding: utf-8 -*-
import base64
from xlwt import easyxf, Workbook
import logging
from io import BytesIO

from odoo.osv import expression
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)



class InsetaLearneringIntervention(models.Model):
	_name = 'inseta.employer.learner.intervention' # dbo.ikporamemployerlearnerintervention.csv
	_description = "Inseta Learner Intervention"

	name = fields.Char('Description')
	code = fields.Char('SAQA Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer('Legacy System ID')