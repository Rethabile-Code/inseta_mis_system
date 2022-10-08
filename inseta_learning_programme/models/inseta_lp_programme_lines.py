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


class InsetaLPProgrammeLines(models.Model):
    _name = "inseta.lp.programe.lines"
    _description = "learner_id"

    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    has_enrolled = fields.Boolean(string="Has enrolled", store=True, default=False)
    lpro_id = fields.Many2one('inseta.lpro', required=False, store=True)

    