import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..services import  sage


_logger = logging.getLogger(__name__)

class InsetaWspAtrPayment(models.Model):
    _name = 'inseta.wspatr.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "WSP/ATR Payment Batch"
    _order= "id desc"

    state = fields.Selection([ 
            ('draft','Draft'),
            ('submit','Submitted'),
            ('approve','Approved'),
            ('in_queue','In Queue'),
            ('processing', 'Processing'), 
            ('done', 'Done')
        ],
        default="draft"
    )
    name = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year', required=True)
    wspatr_period_id = fields.Many2one('inseta.wspatr.period','WSP Period')
    submitted_date = fields.Datetime()
    submitted_by = fields.Many2one('res.users')
    approved_date = fields.Datetime()
    approved_by = fields.Many2one('res.users')
    schedule_date = fields.Datetime(string='Scheduled for')
    line_ids = fields.One2many('inseta.wspatr.payment.line','payment_id')
    count_lines = fields.Integer(compute="_compute_count_lines", string="Count")


    @api.depends('line_ids')
    def _compute_count_lines(self):
        for rec in self:
            rec.count_lines = len(rec.line_ids)

    @api.constrains('schedule_date')
    def _check_schedule_date(self):
        for scheduler in self:
            if scheduler.schedule_date and (scheduler.schedule_date < fields.Datetime.now()):
                raise ValidationError(_('Please select a date equal/or greater than the current date.'))


    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.wspatr.payment.reference')
        vals['name'] = sequence or '/'
        return super(InsetaWspAtrPayment, self).create(vals)

    def unlink(self):
        if self.state not in ('draft',):
            raise ValidationError(_('You can delete approved WSP Payment Batch')
            )
        return super(InsetaWspAtrPayment, self).unlink()

    def action_draft(self):
        self.with_context(allow_write=True).write({'state': 'draft'})

    def action_submit(self):
        if not self.line_ids:
            raise ValidationError('Please pull the WSP Approval list before you submit')
        self.with_context(allow_write=True).write({'state': 'submit'})

    def action_approve(self):
        """Generate Draft payment in the SAGE ERP
        """
        if not self.line_ids:
            raise ValidationError('No WSP approval list to approve.')

        
        res = sage._create_mandatory_grant_batch(self._prepare_sage_payment_vals())
        if res.get('value'):
            pass

        self.with_context(allow_write=True).write({'state': 'approve'})

    def action_schedule_payment(self):
        pass

    def set_schedule_date(self):
        self.write({'schedule_date': self.schedule_date, 'state': 'in_queue'})
        
    @api.model
    def _process_payment_queue(self):
        wsp_payment = self.search([('state', 'in', ('in_queue', 'sending')), '|', ('schedule_date', '<', fields.Datetime.now()), ('schedule_date', '=', False)])
        if wsp_payment:
            for line in wsp_payment.line_ids:
                user = line.write_uid or self.env.user
                line = line.with_context(**user.with_user(user).context_get())
                #create payment
                #update status of each line as payment is processed
                if len(line._get_remaining_recipients()) > 0:
                    line.state = 'sending'
                    line.action_send_mail()
                else:
                    line.write({
                        'state': 'done',
                        'sent_date': fields.Datetime.now(),
                    })


    def _prepare_sage_payment_vals(self):
        approval_list = []
        for line in self.line_ids:
            pass
        return approval_list


    def action_pull(self):

        # domain = [('state','=', self.state)] 
        domain = [] 
        if self.financial_year_id:
            domain.append(('financial_year_id','=', self.financial_year_id.id))

        if self.wspatr_period_id:
            domain.append(('wspatr_period_id','=', self.wspatr_period_id.id))

        wsps = self.env['inseta.wspatr'].search(domain)
        self.line_ids = False

        lines = [
            (
                0,
                0,
                dict(
                    organisation_id = wsp.organisation_id.id,
                    organisation_size_id = wsp.organisation_id.organisation_size_id.id,
                    parent_sdl_no = '',
                    parent_dhet_sdl_no = '',
                    wsp_status = wsp.state,
                    wsp_due_date = wsp.due_date,
                    wsp_form_type = wsp.form_type,
                    wsp_create_date = wsp.create_date,
                    wsp_submitted_date = wsp.submitted_date,
                    wsp_submitted_by = wsp.submitted_by.id,
                    wsp_approved_date = wsp.approved_date,
                    wsp_approved_by = wsp.approved_by.id,
                    wsp_rejected_date = wsp.rejected_date,
                    wsp_rejected_by = wsp.rejected_by.id,
                    sdf_id = wsp.sdf_id.id,
                    sdf_idno = wsp.sdf_id.id_no,
                    sdf_mobile = wsp.sdf_id.mobile,
                    sdf_phone = wsp.sdf_id.phone,
                    sdf_email = wsp.sdf_id.email,
                    no_employees_current_fy = wsp.organisation_id.current_fy_numberof_employees,
                    no_employees_previous_wsp = wsp._get_previous_wsp_no_employees(),
                    payment_amount = 0.00
                )
            ) for wsp in wsps
        ]

        self.write({'line_ids': lines})


class InsetaWspAtrPaymentLine(models.Model):
    _name = 'inseta.wspatr.payment.line'
    _description = "WSP/ATR Payment Batch Line"
    _order= "id desc"



    payment_id = fields.Many2one('inseta.wspatr.payment', 'WSP payment Batch')
    financial_year_id = fields.Many2one('res.financial.year', related="payment_id.financial_year_id", store=True)

    organisation_id = fields.Many2one('inseta.organisation')
    sdl_no = fields.Char('SDL No', related="organisation_id.sdl_no")
    dhet_sdl_no =fields.Char('SDL No', related="organisation_id.dhet_sdl_no")
    no_employees = fields.Integer(related="organisation_id.no_employees")

    organisation_size_id = fields.Many2one('res.organisation.size', string='Size')
    organisation_size_desc = fields.Char(
        related="organisation_id.organisation_size_desc", 
        string="Size Desc."
    )
    province_id = fields.Many2one(
        'res.country.state', 
        'Province', 
        domain=[('code', '=', 'ZA')],
        related="organisation_id.physical_province_id"
    )
    parent_sdl_no =fields.Char('Parent SDL No')
    parent_dhet_sdl_no =fields.Char('Parent DHET SDL No')
    wsp_status = fields.Char('WSP Status')
    wsp_form_type = fields.Char('Type')
    wsp_due_date = fields.Date('Due Date')
    wsp_create_date = fields.Datetime('Created Date')
    wsp_submitted_date = fields.Datetime('Submitted Date')
    wsp_submitted_by = fields.Many2one('res.users', 'Submitted By')
    wsp_approved_date = fields.Datetime('Approved Date')
    wsp_approved_by = fields.Many2one('res.users','Approved By')
    wsp_rejected_date = fields.Datetime('Rejected Date')
    wsp_rejected_by = fields.Many2one('res.users','Rejected By')
    sdf_id = fields.Many2one('inseta.sdf', 'SDF')
    sdf_idno = fields.Char('SDF ID Number')
    sdf_mobile = fields.Char('SDF CellPhone Number')
    sdf_phone = fields.Char('SDF Telephone Number')
    sdf_email = fields.Char('SDF EMail')
    no_employees_current_fy = fields.Integer('Number of Employees (Current FY)') 
    no_employees_previous_wsp = fields.Integer('Number of Employees (previous WSP submitted)') 

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    payment_amount = fields.Monetary()

