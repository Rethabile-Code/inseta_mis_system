from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError


class insetaETQAMainWizard(models.Model):
	_name = 'inseta.etqa.main.wizard'
	_description  = "ETQA Main Wizards"

	
	name = fields.Text('Reason', required=True)
	date = fields.Datetime('Date') 
	user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user.id)
	reference = fields.Integer('Reference ID', default=False, readonly=True)
	model_name = fields.Char('Model Name:', readonly=True)
	action = fields.Selection([('refusal', 'Refusal'),('rework', 'Rework'),('query', 'Query'), ('mass', 'Mass Notification')], 
	string="Action", help="Action to perform. Set to refusal if you want to refuse a record")

	def post_action(self):
		model = str(self.model_name)
		ref_id = self.env['{}'.format(model)].browse([self.reference])
		if ref_id:
			if self.action == "refusal":
				ref_id.reject_registration(self.name)
			elif self.action in ["rework", "query"]:
				ref_id.rework_registration(self.name) 
		return{'type': 'ir.actions.act_window_close'}
