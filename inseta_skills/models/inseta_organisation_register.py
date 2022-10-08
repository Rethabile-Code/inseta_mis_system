from datetime import datetime, timedelta
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class InsetaOrganisationRegister(models.Model):
	_name = 'inseta.organization.register'
	_description = "Organisation Register"
	_inherit =  ['mail.thread', 'mail.activity.mixin']
	

 