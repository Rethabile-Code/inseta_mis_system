from odoo import _, api, models, fields


class ResUser(models.Model):
    _inherit = "res.users"

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(ResUser, self).default_get(fields_list)

        partner_model = self.env["res.partner"]
        inverted = partner_model._get_inverse_name(
            partner_model._get_whitespace_cleaned_name(result.get("name", "")),
            result.get("is_company", False),
        )

        for field in list(inverted.keys()):
            if field in fields_list:
                result[field] = inverted.get(field)

        return result

    user_email = fields.Char() #INSETA legacy system fields
    user_phone = fields.Char() #INSETA legacy system fields
    user_mobile = fields.Char()
    user_faxnumber = fields.Char()

    province_ids = fields.Many2many('res.country.state', string="Province")
    is_external_user =fields.Boolean(string="Is External user")
    is_pmo_mgr = fields.Boolean("Is PMO manager?", help="Specifically Identify PMO mgr.")
    is_ceo = fields.Boolean(string="Is CEO",  
        help="We will use this field to specifically identify CEO."
        "We can only have one CEO at a time" 
        "Sometimes, admin or other users can assume role of CEO. we dont want this to affect emails sent to the CEO"
        "or the CEO signature on docs.")

    is_coo = fields.Boolean(string="Is COO",  
        help="We will use this field to specifically identify COO."
        "We can only have one COO at a time" 
        "Sometimes, admin or other users can assume role of COO. we dont want this to affect emails sent to the CEO"
        "or the COO signature on docs.")
    is_learning_mgr_youth = fields.Boolean('Learning Mgr - Youth?')
    legacy_system_id = fields.Integer()
    id_no = fields.Char('SA Identification No')

    @api.onchange("first_name", "last_name")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        for rec in self:
            rec.name = rec.partner_id._get_computed_name(rec.last_name, rec.first_name)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if ("name" not in default) and ("partner_id" not in default):
            default["name"] = _("%s (copy)") % self.name
        if "login" not in default:
            default["login"] = _("%s (copy)") % self.login
        if (
            ("first_name" not in default)
            and ("last_name" not in default)
            and ("name" in default)
        ):
            default.update(
                self.env["res.partner"]._get_inverse_name(default["name"], False)
            )
        return super(ResUser, self).copy(default)

class ResGroups(models.Model):
	_inherit = "res.groups"
	legacy_system_id = fields.Integer()
    # legacy_system_id = fields.Integer()