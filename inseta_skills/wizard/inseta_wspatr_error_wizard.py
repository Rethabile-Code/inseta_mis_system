# -*- coding: utf-8 -*-
from odoo import api, fields, models


class InsetaWspAtrErrorWizard(models.TransientModel):
    _name = 'inseta.wspatr.error.wizard'
    _description = 'WSPATR Error Wizard'
    
    message = fields.Text()
    error_file = fields.Html()