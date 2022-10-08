from odoo import models, fields, api


class InsetaDialogModel(models.TransientModel):
    _name="inseta.confirm.dialog"
    
    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False 

    name=fields.Text(string="Message",readonly=True,default=get_default)