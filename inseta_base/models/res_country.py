from odoo import fields, api, models, _



class ResCountryState(models.Model):
	_inherit = "res.country.state"

	saqacode = fields.Char('Saqa Code')
	legacy_system_id = fields.Integer('Legacy System ID')
	active = fields.Boolean(default=True)
