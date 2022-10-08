from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
	_inherit = 'ir.attachment'
	'''To be use during migrating providers attachment'''
	provider_id = fields.Many2one('inseta.provider')
	legacy_system_id = fields.Integer('Legacy System ID')
	# active = fields.Boolean(string='Active', default=True)

 