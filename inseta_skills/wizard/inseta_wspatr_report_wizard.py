import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InsetaWspAtrReportWizard(models.TransientModel):

    _name = "inseta.wspatr.report.wizard"
    _description = "WSP/ATR Report Wizard"

    financial_year_id = fields.Many2one('res.financial.year', required=True)
    organisation_id = fields.Many2one('inseta.organisation', required=True)
    organisation_ids = fields.Many2many(
        'inseta.organisation',
        compute="_compute_organisations", 
        string='Organisations', 
        store=True,
        help="Used for applying domain for organisations that have submitted WSP"
    )


    @api.onchange('financial_year_id')
    def _compute_organisations(self):
        wsps = self.env['inseta.wspatr'].search([('financial_year_id', '=', self.financial_year_id.id)])
        for rec in self:
            rec.organisation_ids = False
            if rec.financial_year_id:
                rec.organisation_ids = [(6,0, [wsp.organisation_id.id for wsp in wsps])]


    def action_print(self):
        doc = self.env['inseta.wspatr'].search([
            ('organisation_id','=',self.organisation_id.id), 
            ('financial_year_id','=',self.financial_year_id.id)
        ])
        datas = {
            'docids': [doc.id],
            'ids': [doc.id],
            'form': self.read()[0],
            'docs': doc,
        }

        return self.env.ref('inseta_skills.action_wspatr_submission_report').report_action(doc)
                
         
