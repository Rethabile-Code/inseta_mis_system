from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class InsetaDgSigning(models.Model):
    _name = 'inseta.dgbulksigning' #dbo.dgapproval
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "DG Bulk Signing"
    _order= "id desc"

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaDgSigning, self).default_get(fields_list)

        if not self.env.user.has_group('inseta_dg.group_pmo_admin'):
            raise ValidationError(_('Only PMO Admin is allowed to Create Bulk Signing'))

        return res

    state = fields.Selection([
        ('draft','draft'),
        ('awaiting_sign1','Awaiting Mgr Signature'),
        ('awaiting_sign2','Awaiting COO Signature'),
        ('signed','Signed')
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
    # dgapplication_id = fields.Many2one('inseta.dgapplication')
    approval_date = fields.Date(default=lambda self: fields.Date.today())
    evaluation_ids = fields.One2many(
        'inseta.dgevaluation',
        'bulksigning_id',
        'DG Evaluations'
    )
    count = fields.Integer(compute="_compute_count", string="Count")
    # is_learnership = fields.Boolean(compute="_compute_is_learnership")


    # @api.depends('dgtype_id')
    # def _compute_is_learnership(self):
    #     for rec in self:
    #         if rec.dgtype_id and 'LRN' in rec.dgtype_id.saqacode:
    #             rec.is_learnership = True
    #         else:
    #             rec.is_learnership = False

    @api.depends('evaluation_ids')
    def _compute_count(self):
        for rec in self:
            rec.count = len(rec.evaluation_ids)


    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.dgapproval.code')
        vals['name'] = sequence or '/'
        return super(InsetaDgSigning, self).create(vals)

    
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft',):
                raise ValidationError(
                    _('You can not delete record'))
        return super(InsetaDgSigning, self).unlink()

    def action_draft(self):
        for rec in self:
            rec.with_context(allow_write=True).write({'state':'draft'})

    def action_pull(self):
        domain = [('state','in', ('approved','awaiting_sign1','awaiting_sign2','signed'))]
        if self.financial_year_id:
            domain.append(('financial_year_id','=', self.financial_year_id.id))

        if self.dgtype_id:
            domain.append(('dgtype_id','=', self.dgtype_id.id))

        evals = self.env['inseta.dgevaluation'].search(domain)
        self.evaluation_ids = False
        self.write({
            'evaluation_ids': evals
        })


    # def get_pmo_admin(self):
    #     if self.dgapplication_ids:
    #         if self.dgapplication_ids:
    #             return self.dgapplication_ids[0]._get_pmo_admin()
        
    # def get_pmo_admin_email(self):
    #     if self.dgapplication_ids:
    #         if self.dgapplication_ids:
    #             return self.dgapplication_ids[0].get_pmo_admin_email()

    def generate_letter(self):
        """ Generate approval or Rejection letter
        """
        for rec in self.evaluation_ids:
            seq = self.env['ir.sequence'].next_by_code('inseta.application.reference') or '/'

            if rec.state == "approved":
                #VALIDATE no of learners if DG has been approved
                if rec.dgapplication_id.is_ceo_approved:
                    programme = rec.learnership_id.name or rec.programme_name  or rec.fullqualification_title
                    if rec.total_recommended < 1:
                        raise ValidationError(_(
                            'Please recommend No of learners/Disabled for programme "{prg}"'
                        ).format(
                            prg= programme   
                        ))
                    elif rec.no_learners_approved < 1:
                        raise ValidationError(_(
                            'Please provide the No. of learners/Interns approved for programme "{prg}" for organisation "{org}"'
                        ).format(
                            prg=programme,
                            org=rec.organisation_id.name   
                        ))
                sequence = seq.replace('DG_Code',rec.dgapplication_id.name)
                rec.write({'state':'awaiting_sign1', 'name': sequence})
        self.write({"state":"awaiting_sign1"})
        self.activity_update()


    def action_sign1(self):
        user = self.env.user
        for rec in self.evaluation_ids:
            if rec.state == "approved":
                if rec.dgapplication_id.is_learnership and \
                    not user.has_group("inseta_learning_programme.group_learning_manager_id"):
                    raise ValidationError(_("Only Learnership Manager can sign a sign letter " 
                        "for a learnership programme. Please contact the System Admin.")
                    )

                # if the DG is approved, it will go through 2-step signing, 
                # but rejected DG's will be signed once by the manager
                state = "awaiting_sign2" if rec.is_ceo_approved else "signed"
                rec.write({
                    'state': state,
                    'signed_mgr_date': fields.Datetime.now(),
                    'signed_by_mgr': self.env.user.id
                })
        #force reload dg application to show new state
        self.write({"state":"awaiting_sign2"})
        self.activity_update()


    def action_sign2(self):
        if not self.env.user.has_group("inseta_dg.group_coo"):
            raise ValidationError(_("Only COO is allowed to Sign. Please contact the System Admin."))
        for rec in self.evaluation_ids:
            #once COO has signed, the state changes to signed
            rec.write({
                'state':"signed",
                'signed_coo_date': fields.Datetime.now(),
                'signed_by_coo': self.env.user.id
            })
        self.write({"state":"signed"})
        self.activity_update()

    def action_send_to_programme_mgr(self):
        """ Send recommendation/decline letter to the Programme/Intervention Manager for signature
        """
        self.with_context(allow_write=True).write({'state':'awaiting_sign1'})
        self.activity_update()


    def action_send_to_coo(self):
        """ Send recommendation/decline letter to the COO for signature
        """
        self.with_context(allow_write=True).write({'state':'awaiting_sign2'})
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
        if self.state in ("signed",):
            mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_pmoadmin_afterbulkapproval', raise_if_not_found=False)
        self.with_context(allow_write=True)._message_post(mail_template) #notify sdf
