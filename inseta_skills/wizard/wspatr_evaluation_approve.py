from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class WspAtrEvaluationApprove(models.TransientModel):
    _name = 'wizard.evaluation.approve'
    _description = "WSPATR Bulk approval"

    text = fields.Text(default="Are you sure you want to approve the selected evaluations?")


    def action_approve(self):
        evaluations = self.env[self._context.get('active_model')].search([
            ('id','in',self._context.get('active_ids', [])),
            ('state','=','Recommended_For_Approval')
        ])
        evaluations.approve()