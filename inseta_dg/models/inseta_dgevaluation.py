# -*- coding: utf-8 -*-
import base64
from xlwt import easyxf, Workbook
import logging
from io import BytesIO

from odoo.addons.inseta_tools import date_tools
from odoo.addons.inseta_dg.models.inseta_dgapplication import DG_STATES


from odoo.tools import date_utils
from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# DG_STATES = [
#     ('draft', 'Draft'),
#     ('submit','Submitted'),
#     ('rework','Pending Outstanding Information'),
#     ('pending_approval', 'Pending Evaluation'),
#     ('rework_eval_committee', 'Pending Outstanding Information'),
#     ('pending_adjudication','Pending Adjudication'),
#     ('rework_adjud_committee', 'Pending Outstanding Information'),
#     ('pending_approval2', 'Pending Approval'),
#     ('approve','Approved'),
#     ('reject','Rejected'),
#     ('recommend','Recommended'),
#     ('sign1','Awaiting Manager Signature'),
#     ('sign2','Awaiting COO signature'),
#     ('signed','Signed'),
# ]
class InsetaDgEvaluationHeader(models.Model):
    """
     Migrate ALL DG Evaluation tables to this table
    """
    _name = 'inseta.dgevaluation.header'
    _description = "DG Evaluation Header"
    _order= "id desc"
    _rec_name = "dgapplication_id"


    # @api.model
    # def default_get(self, fields):
    #     res = super().default_get(fields)
    #     active_ids = self._context.get('active_ids', [])
    #     stage = self._context.get("default_stage")
    #     id = active_ids[0] if active_ids else False


    #     evaluation_count = self.env['inseta.dgevaluation.header'] \
    #         .sudo() \
    #         .search_count([
    #             ('dgapplication_id','=',id),
    #             ('stage','=','desktop_evaluation')
    #         ])
    #     if stage == "desktop_evaluation" and evaluation_count:
    #         raise ValidationError(_('A Desktop evaluation already exists for this DG application. Kindly select the existing one.'))

    #     recommend_count = self.env['inseta.dgevaluation.header'] \
    #         .sudo() \
    #         .search_count([
    #             ('dgapplication_id','=',id),
    #             ('stage','=','final_recommendation')
    #         ])
    #     if stage == "final_recommendation" and recommend_count:
    #         raise ValidationError(_('A recommendation already exists for this DG application. Kindly select the existing one.'))

    #     # dg = self.env['inseta.dgapplication'].search([('id','=', id)])
    
    #     # line_ids = self._prepare_default_vals(dg, stage)
    #     # _logger.info(f"DG LINE  {line_ids}")

    #     # res.update({
    #     #     'dgapplication_id': id,
    #     #     'evaluation_ids':line_ids,
    #     #     'dgtype_id': dg.dgtype_id.id,
    #     #     'dgtype_code': dg.dgtype_code,
    #     #     'stage': stage,
    #     # })

    #     return res

    # @api.model
    # def _prepare_default_vals(self, dg, stage):
    #     #dg = self.env['inseta.dgapplication'].search([('id','=', id)])
        
    #     _logger.info(f"DG application details {dg.learnershipdetails_ids}")

    #     line_ids = []
    #     if 'LRN' in dg.dgtype_code:
    #         applicationdetails = dg.learnershipdetails_ids
    #     elif dg.dgtype_code in ('IT-DEGREE','IT-MATRIC'):
    #         applicationdetails = dg.internshipdetails_ids
    #     elif dg.dgtype_code in ('BUR',):
    #         applicationdetails = dg.burlearnerdetails_ids
    #     else: #skills programme
    #         #dg.dgtype_code in ('SP',):
    #         applicationdetails = dg.splearnerdetails_ids

    #     _logger.info(f"Selected details {applicationdetails}")

    #     for dtl in applicationdetails:
    #         desktop_evals = dtl.evaluation_ids.filtered(lambda x: x.stage==stage).sorted(key=lambda z: z.id, reverse=True)
    #         desktop_eval = desktop_evals and desktop_evals[0] or False
    #         line_ids.append((0,0,{
    #             'dgapplication_id': dg.id,
    #             'organisation_id': dg.organisation_id.id,
    #             'financial_year_id': dg.financial_year_id.id,
    #             'dgtype_id': dg.dgtype_id.id,
    #             'state': dg.state,
    #             'dgapplicationdetails_id': dtl.id,
    #             'learnership_id': dtl.learnership_id and dtl.learnership_id.id or False,
    #             'programme_name': dtl.programme_name,
    #             'fullqualification_title': dtl.fullqualification_title, 
    #             'cost_per_student': dtl.cost_per_student,
    #             'actual_cost_per_student': dtl.actual_cost_per_student,
    #             'no_learners': dtl.no_learners,
    #             'disabled': dtl.disabled,
    #             'total_learners': dtl.total_learners,
    #             'amount_applied': dtl.amount_applied,
    #             'no_learners_recommended': desktop_eval and desktop_eval.no_learners_recommended or 0,
    #             'disabled_recommended': desktop_eval and desktop_eval.disabled_recommended or 0,
    #             'total_recommended': desktop_eval and desktop_eval.total_recommended or 0, 
    #             'amount_total_recommended': desktop_eval and desktop_eval.amount_total_recommended or 0,
    #             'no_learners_approved': 0,
    #             'amount_total_approved': 0,
    #             'option': desktop_eval and desktop_eval.option or False,
    #             'comment': desktop_eval and desktop_eval.comment or False,
    #             'stage':stage
    #         }))
    #     return line_ids


    stage = fields.Char(default="desktop_evaluation")
    state = fields.Selection(DG_STATES)
    dgapplication_id = fields.Many2one('inseta.dgapplication')
    dgtype_id = fields.Many2one('res.dgtype', related="dgapplication_id.dgtype_id", store=True)
    dgtype_code = fields.Char( related="dgapplication_id.dgtype_code", store=True)
    is_learnership = fields.Boolean(compute="_compute_is_learnership")

    option = fields.Selection([
        ('Verified', 'Verified'),
        ('Query', 'Query'),
    ])

    # evaluation_ids = fields.One2many('inseta.dgevaluation', 'header_id', string='Evaluations')



    @api.depends('dgtype_id','dgtype_code')
    def _compute_is_learnership(self):
        for rec in self:
            if rec.dgtype_code and 'LRN' in rec.dgtype_code:
                rec.is_learnership = True
            else:
                rec.is_learnership = False

    def unlink(self):
        # for rec in self:
        #     if rec.state not in ('draft', 'submit'):
        #         raise ValidationError(
        #             _('You can not delete record'))
        return super(InsetaDgEvaluationHeader, self).unlink()


    def dgapplication_evaluate(self):
        self.ensure_one()
        if self.state == "submit":
            #Desktop Evaluation is done for each line item in a DG application
            query_list = []
            for line in self.evaluation_ids:
                if line.option == "Query":
                    query_list.append(line.comment)

            if len(query_list) > 0:
                self.dgapplication_id.rework_application(", \n".join(query_list)) 
            else:
                for line in self.evaluation_ids:
                    if line.total_recommended < 1:
                        programme = line.learnership_id.name or line.programme_name or  line.fullqualification_title
                        raise ValidationError(_(
                            'Please recommend No of learners/Disabled for programme "{prg}"'
                        ).format(
                             prg= programme   
                        ))
                self.dgapplication_id.verify_application()
        return {'type': 'ir.actions.act_window_close'}


    def generate_letter(self):
        """ Generate approval or Rejection letter
        """
        for line in self.evaluation_ids:

            #we will ONLY VALIDATE no of learners if DG has been approved
            if line.state == "approve":
                programme = line.learnership_id.name or  line.programme_name  or line.fullqualification_title
                if line.total_recommended < 1:
                    raise ValidationError(_(
                        'Please recommend No of learners/Disabled for programme "{prg}"'
                    ).format(
                        prg= programme   
                    ))
                elif line.no_learners_approved < 1:
                    raise ValidationError(_(
                        'Please provide the No. of learners/Interns approved for programme "{prg}"'
                    ).format(
                        prg= programme   
                    ))

         
        self.dgapplication_id.with_context(allow_write=True).write({
            'state': 'recommend' if self.state == 'approve' else self.state,
        })
        # mail_template = False
        # if self.state == "reject":
        #     mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_rejection_employer_afterreview', raise_if_not_found=False)
        # elif self.state == "approve":
        #     mail_template = self.env.ref('inseta_dg.mail_template_notify_dgappl_approval_employer_afterreview', raise_if_not_found=False)
        # self.dgapplication_id.with_context(allow_write=True)._message_post(mail_template) 

class InsetaDgEvaluation(models.Model):
    """
     Migrate ALL DG Evaluation tables to this table
    """
    _name = 'inseta.dgevaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "DG Evaluation"
    _order= "id desc"
    
    name = fields.Char()
    option = fields.Selection([
        ('Verified', 'Verified'),
        ('Query', 'Query'),
    ])
    # header_id = fields.Many2one('inseta.dgevaluation.header')
    lganumber = fields.Char() #legacy system
    # stage = fields.Char()
    dgapplication_id = fields.Many2one('inseta.dgapplication')
    bulksigning_id = fields.Many2one('inseta.dgbulksigning')
    state = fields.Selection(
        DG_STATES,
        compute="_compute_state",
        inverse="_inverse_state",
        store=True, 
        index=True
    )
    dgapplicationdetails_id = fields.Many2one('inseta.dgapplicationdetails')
    # this is added to enable computation of employed or non employed learners
    total_employed = fields.Integer(compute="_compute_socio_economic_status", store=True) 
    total_unemployed = fields.Integer(compute="_compute_socio_economic_status", store=True) 

    learnership_id = fields.Many2one(
        'inseta.learner.programme', 
        'Learnership', 
        related="dgapplicationdetails_id.learnership_id",
        store=True
    )
    programme_name = fields.Char(related="dgapplicationdetails_id.programme_name",)
    fullqualification_title = fields.Char(related="dgapplicationdetails_id.fullqualification_title")
    qualification_ids = fields.Many2many( #WIL
        'inseta.qualification',
        'dg_evaluation_qualification_rel',
        'dgevaluation_id',
        'qualification_id',
        string="Qualification Title/Name",
    ) 
    dgtype_id = fields.Many2one(
        'res.dgtype', 
        related="dgapplication_id.dgtype_id", 
        store=True
    )
    dgtype_code = fields.Char(related="dgapplication_id.dgtype_code")
    is_learnership = fields.Boolean(compute="_compute_is_learnership")
    is_ceo_approved = fields.Boolean(
        compute="_compute_is_ceo_approved",
        help="Technical field to indicate if a DG is approved by the ceo"
        "We will use this field to hide/display print recommendation/decline letter on the view"
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    organisation_id = fields.Many2one(
        'inseta.organisation', 
        related="dgapplication_id.organisation_id", 
        store=True
    )
    financial_year_id = fields.Many2one(
        'res.financial.year', 
        related="dgapplication_id.financial_year_id", 
        store=True
    )
    #in_review = fields.Boolean() #TODO remove
    cost_per_student = fields.Monetary()
    actual_cost_per_student = fields.Monetary()
    cost_per_disabled = fields.Monetary()

    #Application
    no_learners = fields.Integer()
    disabled = fields.Integer()
    total_learners = fields.Integer()
    amount_applied = fields.Monetary()

    #desktop evaluation
    no_learners_recommended = fields.Integer() #learbership evaluation => dbo.dgevaluationlsdetails.csv
    disabled_recommended = fields.Integer() 
    total_recommended = fields.Integer(compute="_compute_total_recommended", store=True)
    amount_learners_recommended = fields.Monetary(compute="_compute_amount_recommended",inverse="_inverse_amount_recommended", store=True)
    amount_disabled_recommended = fields.Monetary(compute="_compute_amount_recommended", store=True)
    amount_total_recommended = fields.Monetary(compute="_compute_amount_recommended", store=True)
    amount_recommended_perlearner = fields.Monetary()

    #CEO approval
    no_learners_approved = fields.Integer('No. Learners Approved')
    disabled_approved = fields.Integer() 
    total_learners_approved = fields.Integer(
        'Total Learners Approved',
        compute="_compute_total_learners_approved", 
        inverse="_inverse_amount_approved",
        store=True
    )

    amount_total_approved = fields.Monetary(
        'Amount Total Approved',
        compute="_compute_amount_approved",
        store=True
    )
    amount_disabled_approved = fields.Monetary(
        'Amount Disabled Approved',
        compute="_compute_amount_approved",
        store=True
    )
    amount_learners_approved = fields.Monetary(
        'Amount Learners Approved',
        compute="_compute_amount_approved",
        inverse="_inverse_amount_approved",
        store=True
    )


    start_date = fields.Date('Evaluation Start Date')
    end_date = fields.Date('Evaluation End Date')
    comment = fields.Text()
    decline_reasons = fields.Text()
    mandatory_documents = fields.Text()
    notice = fields.Text()

    signed_mgr_date = fields.Datetime()
    signed_by_mgr = fields.Many2one('res.users')
    signed_coo_date = fields.Datetime()
    signed_by_coo = fields.Many2one('res.users')

    legacy_system_id_lrn = fields.Integer(string='Legacy System ID')
    legacy_system_id_bursp = fields.Integer(string='Legacy System ID Bursp')

    # this is added to enable computation of employed or non employed learners
    total_employed = fields.Integer(compute="_compute_socio_economic_status", store=True) 
    total_unemployed = fields.Integer(compute="_compute_socio_economic_status", store=True)

    @api.depends('dgapplication_id')
    def _compute_socio_economic_status(self):
        for rec in self:
            if rec.dgapplication_id:
                emp = self.env.ref('inseta_base.data_sec_1').id
                learnershipdetails_ids = rec.dgapplication_id.mapped('learnershipdetails_ids')
                rec.total_employed = sum([lrn.id for lrn in learnershipdetails_ids.filtered(lambda x: x.socio_economic_status_id.id == emp)])
                rec.total_unemployed = sum([lrn.id for lrn in learnershipdetails_ids.filtered(lambda x: x.socio_economic_status_id.id != emp)])

            else:
                rec.total_employed = False
                rec.total_unemployed = False

    @api.depends('dgapplication_id.is_ceo_approved')
    def _compute_is_ceo_approved(self):
        for rec in self:
            if rec.dgapplication_id.is_ceo_approved:
                rec.is_ceo_approved = True
            else:
                rec.is_ceo_approved = False


    @api.depends('dgapplication_id.state')
    def _compute_state(self):
        for rec in self:
            rec.state = rec.dgapplication_id.state

    def _inverse_state(self):
        for rec in self:
            return True

    @api.depends('dgtype_id','dgtype_code')
    def _compute_is_learnership(self):
        for rec in self:
            if rec.dgtype_code and 'LRN' in rec.dgtype_code:
                rec.is_learnership = True
            else:
                rec.is_learnership = False

    #DESKTOP
    @api.depends(
        'disabled_recommended', 
        'no_learners_recommended')
    def _compute_total_recommended(self):
        for rec in self:
            rec.total_recommended = sum([rec.no_learners_recommended, rec.disabled_recommended])

    @api.depends(
        'total_recommended', 
        'actual_cost_per_student',
        'cost_per_disabled')
    def _compute_amount_recommended(self):
        for rec in self:
            rec.amount_learners_recommended = rec.no_learners_recommended * rec.actual_cost_per_student
            rec.amount_disabled_recommended = rec.disabled_recommended * rec.cost_per_disabled
            rec.amount_total_recommended = sum([rec.amount_learners_recommended, rec.amount_disabled_recommended])

    @api.depends(
        'total_recommended', 
        'actual_cost_per_student')
    def _inverse_amount_recommended(self):
        for rec in self:
            return True


    #approval
    @api.depends(
    'no_learners_approved',
    'disabled_approved')
    def _compute_total_learners_approved(self):
        for rec in self:
            rec.total_learners_approved = sum([
                rec.no_learners_approved, 
                rec.disabled_approved
            ])

    @api.depends(
        'total_learners_approved',
        'disabled_approved',
        'no_learners_approved',
        'actual_cost_per_student',
        'cost_per_disabled'
    )
    def _compute_amount_approved(self):
        for rec in self:
            rec.amount_disabled_approved = rec.disabled_approved * rec.cost_per_disabled
            rec.amount_learners_approved = rec.no_learners_approved * rec.actual_cost_per_student
            rec.amount_total_approved = sum([rec.amount_disabled_approved, rec.amount_learners_approved])


    @api.depends(
        'total_learners_approved',
        'disabled_approved',
        'no_learners_approved',
        'actual_cost_per_student'
    )
    def _inverse_amount_approved(self):
        for rec in self:
            return True


    def action_reset(self):
        for rec in self:
            if rec.dgapplication_id.is_ceo_approved:
                rec.state = "approve"
            else:
                rec.state = "reject"
            
    def generate_letter(self):
        """ Generate approval or Rejection letter
        """
        for rec in self:

            #VALIDATE no of learners if DG has been approved
            if rec.is_ceo_approved:
                programme = rec.learnership_id.name or rec.programme_name  or rec.fullqualification_title
                if rec.total_recommended < 1:
                    raise ValidationError(_(
                        'Please recommend No of learners/Disabled for programme "{prg}"'
                    ).format(
                        prg= programme   
                    ))
                elif rec.no_learners_approved < 1:
                    raise ValidationError(_(
                        'Please provide the No. of learners/Interns approved for programme "{prg}"'
                    ).format(
                        prg= programme   
                    ))
            #iNT IWGA21279
            #LNR LGA210017Y LGA210010W 
            #BUR BFA2021-0001 SPW2021-0001
            seq = self.env['ir.sequence'].next_by_code('inseta.application.reference') or '/'
            prefix, suffix = "",""
            if self.dgtype_code in ('LRN-Y','LRN-R'):
                prefix = 'LGA'
                suffix = "Y"
            elif self.dgtype_code in ('LRN-W',):
                prefix = 'LGA'
                suffix = "W"
            elif self.dgtype_code in ('IT-DEGREE','IT-MATRIC'):
                prefix = "IWGA"
            elif self.dgtype_code in ('BUR',):
                prefix = "BFA"
            elif self.dgtype_code in ('SP',): #skills programme
                prefix = "SPW"

            sequence = seq.replace('PREFIX',prefix)
            sequence = f"{sequence}{suffix}"
            rec.write({'state':'awaiting_sign1', 'name': sequence})
        return self.activity_update()


    def action_sign1(self):
        user = self.env.user
        for rec in self:
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
        return self.activity_update()


    def action_sign2(self):
        if not self.env.user.has_group("inseta_dg.group_coo"):
            raise ValidationError(_("Only COO is allowed to Sign. Please contact the System Admin."))
        for rec in self:
            #once COO has signed, the state changes to signed
            rec.write({
                'state':"signed",
                'signed_coo_date': fields.Datetime.now(),
                'signed_by_coo': self.env.user.id
            })
        return self.activity_update()

    def action_print_recommendation_letter(self):
        return self.env.ref('inseta_dg.action_dgapplication_recommendation_letter_report').report_action(self)

    def action_print_rejection_letter(self):
        return self.env.ref('inseta_dg.action_dgapplication_decline_letter_report').report_action(self)


    def action_send_letter_employer(self):
        for rec in self:
            if rec.dgapplication_id.is_ceo_approved:
                template = self.env.ref('inseta_dg.mail_template_notify_dgappl_approval_employer_afterreview', raise_if_not_found=False) 
            else:
                template = self.env.ref('inseta_dg.mail_template_notify_dgappl_rejection_employer_afterreview', raise_if_not_found=False) 
            rec._message_post(template)


    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            self.message_post_with_template(
                template.id, composition_mode='comment',
                model='inseta.dgevaluation', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )


    def activity_update(self):
        reload = False
        if all([rec.state == "awaiting_sign1" for rec in self.search([('dgapplication_id','=',self.dgapplication_id.id)])]):
            if self.dgapplication_id.with_context(allow_write=True).write({'state':'awaiting_sign1'}):
                reload = True
                self.dgapplication_id.activity_update()
        elif all([rec.state == "awaiting_sign2" for rec in self.search([('dgapplication_id','=',self.dgapplication_id.id)])]):
            if self.dgapplication_id.with_context(allow_write=True).write({'state':'awaiting_sign2'}):
                reload = True
                self.dgapplication_id.activity_update()
        elif all([rec.state == "signed" for rec in self.search([('dgapplication_id','=',self.dgapplication_id.id)])]):
            self.dgapplication_id.with_context(allow_write=True).write({'state':'signed'})
            reload = True
            #update dg mail activity
            self.dgapplication_id.activity_update()
        #force reload dg application to show new state
        if reload:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
