from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class InsetaDgRecommendation(models.Model):
    """DG Bulk recommendation
    """
    _name = 'inseta.dgrecommendation' 
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "DG DGEC/DGAC Recommendation"
    _order= "id desc"

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaDgRecommendation, self).default_get(fields_list)

        if not (self.env.user.has_group('inseta_dg.group_evaluation_committee') or \
            self.env.user.has_group('inseta_dg.group_adjudication_committee')):
            raise ValidationError(_('Only DGEC and DGAC members are allowed to create DGEC/DGAC Recommendation'))

        return res

    state = fields.Selection([
        ('pending_approval', 'DGEC'),
        ('pending_adjudication','DGAC'), #recommended by DGEC -> DGAC
        ('pending_approval2', 'Pending CEO Approval'), #recommended by DGAC -> CEO
    ], default="pending_approval")

    name = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year')
    dgec_recommendation_sheet = fields.Binary(
        "DGEC Recommendation Sheet",
        help="DGEC Recommendation excel sheet"

    )
    dgac_recommendation_sheet = fields.Binary(
        "DGAC Recommendation Sheet",
        help="DGAC Recommendation excel sheet"
    )

    file_name = fields.Char()
    file_name2 = fields.Char()

    organisation_id = fields.Many2one(
        'inseta.organisation', 
        domain="[('state','=','approve')]",
    )
    dgtype_id = fields.Many2one('res.dgtype', 'Programme type')
    dgec_recommendation_date = fields.Date(default=lambda self: fields.Date.today())
    dgac_recommendation_date = fields.Date()

    dgapplication_ids = fields.One2many(
        'inseta.dgapplication',
        'dgrecommend_id',
        'DG Applications'
    )
    count_dgapplications = fields.Integer(compute="_compute_count_dgapplications", string="Count")


    @api.depends('dgapplication_ids')
    def _compute_count_dgapplications(self):
        for rec in self:
            rec.count_dgapplications = len(rec.dgapplication_ids)


    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.dgapproval.code')
        vals['name'] = sequence or '/'
        return super(InsetaDgRecommendation, self).create(vals)

    
    def unlink(self):
        for rec in self:
            if rec.state in ('pending_adjudication', 'pending_approval2'):
                raise ValidationError(
                    _('You can not delete record that has been evaluated by DGEC'))
        return super(InsetaDgRecommendation, self).unlink()

    def action_draft(self):
        self.with_context(allow_write=True).write({'state': 'pending_approval'})

    def action_pull(self):

        domain = [('state','=', self.state)] 
        if self.financial_year_id:
            domain.append(('financial_year_id','=', self.financial_year_id.id))

        if self.dgtype_id:
            domain.append(('dgtype_id','=', self.dgtype_id.id))

        dgs = self.env['inseta.dgapplication'].search(domain)
        self.dgapplication_ids = False
        self.write({
            'dgapplication_ids': dgs
        })

    def get_ceo(self):
        if self.dgapplication_ids:
            return self.dgapplication_ids[0]._get_ceo()

    def get_ceo_email(self):
        if self.dgapplication_ids:
            ceo_email = self.dgapplication_ids[0].get_ceo_email()
            _logger.info(f"CEO Email => {ceo_email }" )
            return ceo_email

        
    def get_adjudication_committee_email(self):
        if self.dgapplication_ids:
            dgac_emails = self.dgapplication_ids[0].get_adjudication_committee_email()
            _logger.info(f"DGAC Email => {dgac_emails }" )
            return dgac_emails


    def recommend_application(self, comment):
        """DGEC/DGAC recommend or not recommend the application.
        When the application is verified change the state
        to " Pending Approval".
        This method is called from the dgbulkrecommendation wizard

        Args:
            comment (str): comment
        """
        if not self.dgapplication_ids:
            raise ValidationError("Click on the 'Search Records' button to filter the applications you want to recommend")
        _logger.info('Bulk recommending DG application...')

        mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)
        if self.state == "pending_adjudication":
            if not self.env.user.has_group('inseta_dg.group_adjudication_committee'):
                raise ValidationError(_('Only DGAC members are allowed to recommend for CEO approval\n Please select the appropriate Committee'))

            records = self.dgapplication_ids.filtered(lambda x: x.state == "pending_adjudication")
            for record in records:
                if record.is_dgac_recommended:
                    record.write({
                        'state': 'pending_approval2', 
                        'dgac_recommendation':'Recommended',
                        'dgac_comment': comment}) 
                else:
                    record.write({'state': 'pending_approval2', 'dgac_recommendation':'Not Recommended'}) 

            self.write({'state': 'pending_approval2'})

        elif self.state == "pending_approval":
            if not self.env.user.has_group('inseta_dg.group_evaluation_committee'):
                raise ValidationError(_('Only DGEC members are allowed to recommend for Adjudication (DGAC)\n. Please select the appropriate Committee'))

            records = self.dgapplication_ids.filtered(lambda x: x.state == "pending_approval")
            for record in records:
                if record.is_dgac_recommended:
                    record.write({
                        'state': 'pending_adjudication', 
                        'dgec_recommendation':'Recommended',
                        'dgec_comment': comment
                    }) 
                else:
                    record.write({'state': 'pending_adjudication', 'dgec_recommendation':'Not Recommended'}) 

            self.write({'state': 'pending_adjudication'})

            #notify employer of the dg status
            records.with_context(allow_write=True)._message_post(mail_template)
        self.activity_update()

    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            for rec in self:
                rec.message_post_with_template(
                    template.id, composition_mode='comment',
                    model='inseta.dgrecommendation', res_id=rec.id,
                    email_layout_xmlid='mail.mail_notification_light',
                )
    
    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template = False
        if self.state == "pending_adjudication":
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_adjudcomm_bulk', raise_if_not_found=False)
        if self.state == "pending_approval2":
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_ceo_bulk', raise_if_not_found=False)
        self.with_context(allow_write=True)._message_post(mail_template) #notify sdf
