import logging

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class ResUsersExtension(models.Model):
    _inherit = "res.users"

    has_agreed_popiact = fields.Boolean("Agreed to POPI Act?", help="Indicates that a user has agreed to popi act.")
    has_agreed_yes_no = fields.Char('Yes/No', default="No")
    popiact_date = fields.Date(default=lambda self: fields.Date.today())
    user_email = fields.Char(compute="_compute_email")

    @api.onchange("login")
    def _compute_email(self):
        for rec in self:
            if rec.login and "@" in  rec.login:
                rec.user_email = rec.login
            elif rec.partner_id.email and "@" in  rec.partner_id.email:
                rec.user_email = rec.partner_id.email
            else:
                rec.user_email = False
