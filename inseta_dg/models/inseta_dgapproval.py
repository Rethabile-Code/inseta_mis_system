from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class InsetaDgApproval(models.Model):
    _name = 'inseta.dgapproval' #dbo.dgapproval
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "DG Bulk Approval"
    _order= "id desc"

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaDgApproval, self).default_get(fields_list)

        if not self.env.user.has_group('inseta_dg.group_ceo'):
            raise ValidationError(_('Only CEO is allowed to Create Bulk Approval'))

        return res

    state = fields.Selection([
        ('draft','Pending Approval'),
        ('approve','Approved'),
        ('reject','Reject'),
    ], default="draft")
    name = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year')
    approval_sheet = fields.Binary(string="Approval Sheet")
    file_name =fields.Char()

    organisation_id = fields.Many2one(
        'inseta.organisation', 
        domain="[('state','=','approve')]",
    )
    dgtype_id = fields.Many2one('res.dgtype', 'Programme type')
    approval_date = fields.Date(default=lambda self: fields.Date.today())
    dgapplication_ids = fields.One2many(
        'inseta.dgapplication',
        'dgapproval_id',
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
        return super(InsetaDgApproval, self).create(vals)

    
    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You can not delete record'))
        return super( InsetaDgApproval, self).unlink()

    def action_draft(self):
        for rec in self:
            rec.with_context(allow_write=True).write({'state':'draft'})

    def action_pull(self):
        domain = [('state','=', 'pending_approval2')]
        if self.financial_year_id:
            domain.append(('financial_year_id','=', self.financial_year_id.id))

        if self.dgtype_id:
            domain.append(('dgtype_id','=', self.dgtype_id.id))

        dgs = self.env['inseta.dgapplication'].search(domain)
        self.dgapplication_ids = False
        self.write({
            'dgapplication_ids': dgs
        })


    def get_pmo_admin(self):
        if self.dgapplication_ids:
            if self.dgapplication_ids:
                return self.dgapplication_ids[0]._get_pmo_admin()
        
    def get_pmo_admin_email(self):
        if self.dgapplication_ids:
            if self.dgapplication_ids:
                return self.dgapplication_ids[0].get_pmo_admin_email()

    def reject_application(self, comment):
        """CEO rejects DG. change status to "rejected".
        This method is called from the dgapplication approve wizard

        Args:
            comment (str): Reason for rejection
        """
        _logger.info('bulk Rejecting dg application...')
        self.write({'state': 'reject'})
        mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)
        for rec in self.dgapplication_ids:
            rec.with_context(allow_write=True).write({
                'state': 'reject',
                'rejected_date': fields.Date.today(),
                'rejected_by': self.env.user.id,
            })
            #notify employer of the dg status
            rec.with_context(allow_write=True)._message_post(mail_template)
        self.activity_update()


    def approve_application(self, comment):
        """CEO approves DG. change status to "approved".
        This method is called from the dgapplication approve wizard

        Args:
            comment (str): Reason for approval
        """
        _logger.info('Bulk Approving DG application...')
        mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_employer_progress1', raise_if_not_found=False)
        #Rejected DG's could be in the line, so we will filter n approve only DG in pending_approval2 state
        if not self.dgapplication_ids:
            raise ValidationError("Click on the 'Search Records' button to filter the applications you want to approve")
        records = self.dgapplication_ids.filtered(lambda x: x.state == "pending_approval2")
        for rec in records:
            if rec.is_ceo_approved:
                rec.with_context(allow_write=True).write({
                    'state': 'approve',
                    'approved_date': self.approval_date,
                    'approved_by': self.env.user.id,
                })
            else:
                rec.with_context(allow_write=True).write({
                    'state': 'reject',
                    'rejected_date': self.approval_date,
                    'rejected_by': self.env.user.id,
                })
            #notify employer of the dg status
            rec.with_context(allow_write=True)._message_post(mail_template)

        self.write({'state': 'approve'})
        self.activity_update()



    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            self.message_post_with_template(
                template.id, composition_mode='comment',
                model='inseta.dgapproval', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )
    
    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template = False
        if self.state in ("approve","reject"):
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_pmoadmin_afterbulkapproval', raise_if_not_found=False)
        self.with_context(allow_write=True)._message_post(mail_template) #notify sdf
