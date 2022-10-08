# -*- coding: utf-8 -*-
import logging

from odoo.addons.inseta_tools import date_tools
from odoo.tools import date_utils

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

DG_STATES = [
    ('draft', 'Draft'),
    ('submit','Submitted'),
    ('rework','Pending Outstanding Information'),
    ('pending_approval', 'Pending Evaluation'),
    ('rework_eval_committee', 'Pending Outstanding Information'),
    ('pending_adjudication','Pending Adjudication'),
    ('rework_adjud_committee', 'Pending Outstanding Information'),
    ('pending_approval2', 'Pending Approval'),
    ('approve','Approved'),
    ('reject','Rejected'),
]


class InsetaDgApplicationDetails(models.Model):
    _name = 'inseta.dgapplicationdetails'  #all dg application learnership, internship, skills programme, bursary, TVET will be saved here
    _description = 'DG Application Details'
    _order= "id desc"

    name = fields.Char()
    state = fields.Selection(related="dgapplication_id.state")
    dgapplication_id = fields.Many2one('inseta.dgapplication')
    dgtype_id = fields.Many2one(
        'res.dgtype', 
        string='DG type', 
        compute="_compute_dgtype_code",
        store=True,
        help="Helps to differentiate different types of learnership."
    )
    dgtype_code = fields.Char(compute="_compute_dgtype_code", store=True)
    is_hei = fields.Boolean(related="dgapplication_id.is_hei", store=True)
    organisation_id = fields.Many2one('inseta.organisation',related="dgapplication_id.organisation_id")
    financial_year_id = fields.Many2one('res.financial.year',related="dgapplication_id.financial_year_id")
    fundingtype_id = fields.Many2one('res.fundingtype','Funding Type')
    learnership_id = fields.Many2one('inseta.learner.programme', 'Learnership')
    learnership_other = fields.Char()
    display_learnership_other = fields.Boolean(
        compute="_compute_display_learnership_other"
    )
    learnership_code = fields.Char(
        compute="_compute_learnership_code", 
        inverse="_inverse_learnership_code",
        store=True
    )
    socio_economic_status_id = fields.Many2one(
        'res.socio.economic.status', 
        'Socio Economic Status',
    )
    province_id = fields.Many2one(
        'res.country.state', 
        string='Physical Province', 
        domain=[('country_id.code', '=', 'ZA')]
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    cost_per_student = fields.Monetary(compute="_compute_cost_per_student")
    cost_per_month  = fields.Monetary()
    cost_per_disabled = fields.Monetary(compute="_compute_cost_per_student")
    funding_amount_required = fields.Monetary(
        help="Incase of bursary or SP, user can" 
        "provide amount less than the max"
    )
    actual_cost_per_student = fields.Monetary(
        compute="_compute_amount_applied", 
        store=True,
        help="For SP/BUR user can specify funding amount per learner." 
        "We save the actaul amount here so that we will not have to "
        "check for dgtype each time we want to reference cost_per_learner"
    )
    #applied
    no_learners = fields.Integer('No. Learners Applied', store=True)
    disabled = fields.Integer('No. Disabled Applied', store=True)
    total_learners = fields.Integer(
        "Total Learners Applied", 
        compute="_compute_total_learners", 
        store=True
    )
    amount_disabled_applied = fields.Monetary(compute="_compute_amount_applied",store=True)
    amount_learners_applied = fields.Monetary(compute="_compute_amount_applied",store=True)
    amount_applied = fields.Monetary('Total Amount Applied', compute="_compute_amount_applied",store=True)
    #desktop evaluation
    no_learners_recommended = fields.Integer(compute="_compute_total_recommended", store=True) 
    disabled_recommended = fields.Integer(compute="_compute_total_recommended", store=True) 
    total_recommended = fields.Integer(compute="_compute_total_recommended", store=True)
    amount_learners_recommended = fields.Monetary(compute="_compute_amount_recommended", store=True)
    amount_disabled_recommended = fields.Monetary(compute="_compute_amount_recommended", store=True)
    amount_total_recommended = fields.Monetary(compute="_compute_amount_recommended", store=True)
    #approval
    no_learners_approved = fields.Integer("No Learners Approved",store=True)
    disabled_approved = fields.Integer('No. Disabled Approved',store=True)
    total_learners_approved = fields.Integer(
        'Total Learners Approved',
        compute="_compute_total_learners_approved", 
        store=True
    )

    amount_disabled_approved = fields.Monetary(store=True)
    amount_learners_approved = fields.Monetary(store=True)
    amount_total_approved = fields.Monetary(
        'Total Amount Approved', 
        compute="_compute_amount_total_approved",
        store=True
    )

    start_date = fields.Date()
    end_date = fields.Date()
    active = fields.Boolean(default=True)
    #TODO contact should pull from Organisation Contact + CEO + CFO + 
    org_contacts_ids = fields.Many2many(
        'res.partner', 
        compute="_compute_org_contact_ids", 
        string='Organistaion Contacts', 
        help="Technical field used to list org. contacts"
    )
    contact_person_id = fields.Many2one(
        'res.partner',
        domain="[('id','in',org_contacts_ids)]",
        help="Employer Contact person for this application"
    )
    contact_person_name = fields.Char()
    contact_person_surname = fields.Char()
    contact_person_email = fields.Char()
    contact_person_phone = fields.Char() #for migration of dborganisation contact
    contact_person_mobile = fields.Char() #for migration of dborganisation contact
    contact_person_idno = fields.Char() #for migration of dborganisation contact

    #legacy fields
    # provider_id = fields.Many2one("inseta.provider", "Provider")
    # provider_other = fields.Char()
    # provider_scope_expirydate = fields.Date()

##### Bursary & sp fields
    # no_learnersappliedfor = fields.Integer('No Applied For') #numberoflearnersappliedfor
    # cost_per_student = fields.Monetary() #cost per student
    # funding_amount_required = fields.Monetary() #funding amount
    publicprovider_id = fields.Many2one('res.dgpublicprovider','Institution')
    publicprovider_name = fields.Char('Full Name of Provider', compute="_compute_publicprovider_name", store=True)
    publicproviderother = fields.Char('Full Name Other Institution')
    privateprovider = fields.Char('Private Provider') #legacy system field privateprovider
    privateproviderqualification = fields.Char()
    provider_id = fields.Many2one('inseta.provider','Provider', ondelete="cascade") 
    provideretqeid = fields.Char()#provideretqeid legacy system field
    provider_name = fields.Char() #skillsdevelopmentprovider
    provider_other = fields.Char('Other Provider') #skillsdevelopmentprovider
    providercode = fields.Char() #legacy sysyem
    provider_scope_expirydate = fields.Date()

    fullqualification_title = fields.Char('Qualification Title')
    # skillsprogramme_title = fields.Char('Programme Title')
    programme_name = fields.Char('Programme Title')
    skillsprogramme_category = fields.Selection([
        ('Programme 1','Programme 1'),
        ('Programme 2','Programme 2')
    ],string='Skills Programme Category')
    skillsprogramme_id = fields.Many2one('inseta.skill.programme', 'Skills Programme Name') #SP-Y
    qualification_ids = fields.Many2many( #WIL
        'inseta.qualification',
        'dg_applicationdetails_qualification_rel',
        'dgapplicationdetails_id',
        'qualification_id',
        string="Qualification Title/Name",
    ) 
    no_learners_per_programme = fields.Char('Number of learners per skills programme')

    tvet_accreditation = fields.Selection([
        ('Yes','Yes'),
        ('No','No')
    ])

    year_of_study = fields.Selection([
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
    ], string="Year of Study")

    qualification_saqaid = fields.Char(
        'Qualification SAQA ID', 
        compute="_compute_qualification_saqaid", 
        inverse='_inverse_qualification_saqaid',
        store=True
    ) #qualificationid
    scarcecritical_id  = fields.Many2one('res.dginternshipscarcecritical','Scarce & Critical Skills') #scarcecriticalskillsid
    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    # start_date = fields.Date('Start Date')
    # end_date = fields.Date('End Date')
    fullname_education = fields.Char('Full Name of Education') #skills Programme
    duration = fields.Integer('Duration')

#internship specific fields
    # programme_name = fields.Char()
    internship_type = fields.Selection([
        ('Matric','Matric Certificate'),
        ('Degree','Degree')
    ],
    compute="_compute_internship_type", store=True)
    # scarcecritical_id  = fields.Many2one('res.dginternshipscarcecritical','Critical Scarce Skills')
    # no_of_interns = fields.Integer('Total Number of Interns') #no_learners
    # duration = fields.Char()
    # start_date = fields.Date()
    # end_date = fields.Date()
    firsttime_applicant = fields.Selection([('Yes','Yes'),('No','No')], string="First Time Applicant?")
    # active = fields.Boolean(default=True)
    #for legacy system migration
    # contact_person = fields.Char("Contact Person Legacy", help="Legacy system Employer Contact person for this application")
    # contact_details = fields.Char(help="Legacy Contact person details for this application")

    legacy_system_id_lrn = fields.Integer() #legacy system ID for dbo.dglearnershipdetails
    legacy_system_id_int = fields.Integer() #legacy system ID for dbo.dglearnershipdetails
    legacy_system_id_bursp = fields.Integer() #legacy system ID bursary & sp

    evaluation_ids = fields.One2many(
        'inseta.dgevaluation', 
        'dgapplicationdetails_id', 
        'DG Evaluation'
    )
# --------------------------------------------
# Compute methods
# --------------------------------------------

    #DESKTOP

    @api.depends('no_learners','disabled')
    def _compute_total_learners(self):
        for rec in self:
            rec.total_learners = sum([rec.no_learners, rec.disabled])

            
    @api.depends('dgtype_id')
    def _compute_cost_per_student(self):
        for rec in self:
            if rec.dgtype_id:
                rec.cost_per_student = rec.dgtype_id.cost_per_learner
                rec.cost_per_disabled = rec.dgtype_id.cost_per_disabled or 0.00
            else:
                rec.cost_per_student = 0.00
                rec.cost_per_disabled = 0.00


    @api.depends(
        'evaluation_ids.disabled_recommended', 
        'evaluation_ids.no_learners_recommended')
    def _compute_total_recommended(self):
        for rec in self:
            desktop = rec.evaluation_ids.sorted(key=lambda z: z.id, reverse=True)[:1]
            rec.no_learners_recommended = desktop  and desktop.no_learners_recommended or 0
            rec.disabled_recommended =  desktop and desktop.disabled_recommended or 0
            rec.total_recommended = sum([desktop  and desktop.no_learners_recommended or 0, desktop and desktop.disabled_recommended or 0])


    @api.depends(
        'total_recommended', 
        'actual_cost_per_student',
        'cost_per_disabled')
    def _compute_amount_recommended(self):
        for rec in self:
            rec.amount_learners_recommended = rec.no_learners_recommended * rec.actual_cost_per_student
            rec.amount_disabled_recommended = rec.disabled_recommended * rec.cost_per_disabled
            rec.amount_total_recommended = sum([rec.amount_learners_recommended, rec.amount_disabled_recommended])

    # ceo approval
    @api.depends(
        'evaluation_ids.no_learners_approved', 
        'evaluation_ids.disabled_approved', 
        'evaluation_ids.total_learners_approved')
    def _compute_total_learners_approved(self):
        for rec in self:
            approval = rec.evaluation_ids.sorted(key=lambda z: z.id, reverse=True)[:1]
            rec.no_learners_approved = approval and sum(approval.mapped('no_learners_approved')) or 0
            rec.disabled_approved = approval and sum(approval.mapped('disabled_approved')) or 0
            rec.total_learners_approved = approval and sum(approval.mapped('total_learners_approved')) or 0


    @api.depends(
        'evaluation_ids.amount_total_approved', 
        'evaluation_ids.amount_disabled_approved', 
        'evaluation_ids.amount_learners_approved')
    def _compute_amount_total_approved(self):
        for rec in self:
            approval = rec.evaluation_ids.filtered(lambda x: x.state=="approve").sorted(key=lambda z: z.id, reverse=True)[:1]
            rec.amount_total_approved = approval and sum(approval.mapped('amount_total_approved')) or 0
            rec.amount_disabled_approved = approval and sum(approval.mapped('amount_disabled_approved')) or 0
            rec.amount_learners_approved = approval and sum(approval.mapped('amount_learners_approved')) or 0


    #applied
    @api.depends(
        'total_learners', 
        'no_learners',
        'disabled',
        'cost_per_student',
        'duration',
        'funding_amount_required')
    def _compute_amount_applied(self):
        for rec in self:
            # if rec.dgapplication_id.dgtype_code == 'IT-DEGREE':
            #     rec.internship_type = "Degree"
            #     _logger.info(f" DEGREE {rec.internship_type}")
            # elif rec.dgapplication_id.dgtype_code == 'IT-MATRIC':
            cost_per_month = 0.00
            if rec.dgtype_code in ('IT-DEGREE','IT-MATRIC'):
                cost_per_month = rec.cost_per_student / 12
                actual_cost_per_student = round(cost_per_month * rec.duration, 2)

            elif rec.dgtype_code in ('BUR','SP'):
                actual_cost_per_student = rec.funding_amount_required
            else:
                actual_cost_per_student = rec.cost_per_student

            # rec.actual_cost_per_student = rec.funding_amount_required if rec.dgtype_code in ('BUR','SP') else rec.cost_per_student
            rec.actual_cost_per_student = actual_cost_per_student
            rec.cost_per_month = cost_per_month
            rec.amount_learners_applied = rec.no_learners * rec.actual_cost_per_student
            rec.amount_disabled_applied = rec.disabled * rec.cost_per_disabled
            rec.amount_applied = sum([rec.amount_learners_applied, rec.amount_disabled_applied])


    #bursary specific compute fields
    @api.depends('qualification_ids')
    def _compute_qualification_saqaid(self):
        for rec in self:
            if rec.qualification_ids:
                _logger.info(f"SAQA ID =>  {rec.qualification_ids.mapped('saqa_id')}")
                rec.qualification_saqaid = ','.join(rec.qualification_ids.mapped('saqa_id'))
            else:
                rec.qualification_saqaid = False

    @api.depends('qualification_ids')
    def _inverse_qualification_saqaid(self):
        for rec in self:
            return True

    @api.depends('is_hei')
    def _compute_publicprovider_name(self):
        for rec in self:
            if rec.is_hei:
                rec.publicprovider_name = rec.organisation_id.legal_name
            else:
                rec.publicprovider_name = False

    @api.depends('provider_id')
    def _compute_provider_name(self):
        for rec in self:
            if rec.provider_id:
                rec.provider_name = rec.provider_id.name
            else:
                rec.provider_name = False

    #end bursary specific compute fields

    @api.depends('organisation_id')
    def _compute_org_contact_ids(self):
        for rec in self:
            if rec.organisation_id:
                contact_ids = rec.organisation_id.child_ids.ids
                ceo_ids = rec.organisation_id.ceo_ids.ids
                cfo_ids = rec.organisation_id.cfo_ids.ids
                _logger.info(f" CONTACTS => {contact_ids} {ceo_ids} {cfo_ids}")
                rec.org_contacts_ids = [(6,0, contact_ids + ceo_ids + cfo_ids)]
            else:
                rec.org_contacts_ids = False


    @api.depends('dgapplication_id.dgtype_id')
    def _compute_dgtype_code(self):
        for rec in self:
            if rec.dgapplication_id and rec.dgapplication_id.dgtype_id:
                rec.dgtype_id =  rec.dgapplication_id.dgtype_id.id
                rec.dgtype_code =  rec.dgapplication_id.dgtype_id.saqacode
            else:
                rec.dgtype_id =  False
                rec.dgtype_code = False

    @api.depends('dgapplication_id.dgtype_id')
    def _compute_internship_type(self):
        for rec in self:
            if rec.dgapplication_id.dgtype_id:
                if rec.dgapplication_id.dgtype_code == 'IT-DEGREE':
                    rec.internship_type = "Degree"
                    _logger.info(f" DEGREE {rec.internship_type}")
                elif rec.dgapplication_id.dgtype_code == 'IT-MATRIC':
                    rec.internship_type = "Matric"
                    _logger.info(f" MATRIC {rec.internship_type}")

                else:
                    rec.internship_type = False
                    _logger.info(f" FALSE {rec.internship_type}")

            else:
                rec.internship_type = False
                _logger.info(f" FALSE 2 {rec.internship_type}")



    @api.depends('learnership_id')
    def _compute_display_learnership_other(self):
        for rec in self:
            if rec.learnership_id and rec.learnership_id.name == "Other":
                rec.display_learnership_other = True
            else:
                rec.display_learnership_other = False


    @api.depends('learnership_id')
    def _compute_learnership_code(self):
        for rec in self:
            if rec.learnership_id:
                rec.learnership_code = rec.learnership_id.programme_code
            else:
                rec.learnership_code = False

    @api.depends('learnership_id')
    def _inverse_learnership_code(self):
        for rec in self:
            return True

# --------------------------------------------
# Onchange methods
# --------------------------------------------

    @api.onchange('cost_per_student')
    def _onchange_cost_per_student(self):
        if self.cost_per_student and self.dgapplication_id.dgtype_code in ("BUR","SP"):
            self.funding_amount_required = self.cost_per_student


    @api.onchange("contact_person_id")
    def _onchange_contact_person_id(self):
        if self.contact_person_id:
            self.contact_person_name = f"{self.contact_person_id.first_name} {self.contact_person_id.last_name}"
            self.contact_person_email = self.contact_person_id.email


    @api.onchange("dgtype_code")
    def _onchange_dgtype_code(self):
        if self.dgtype_code:
            if self.dgtype_code in ('LRN-Y','LRN-D','LRN-R'):
                self.socio_economic_status_id = self.env.ref("inseta_base.data_sec_2").id
            elif self.dgtype_code in ('LRN-W',): 
                self.socio_economic_status_id = self.env.ref("inseta_base.data_sec_1").id
            else:
                self.socio_economic_status_id = False


    @api.onchange("funding_amount_required")
    def _onchange_funding_amount_required(self):
        """For SP and BUR user can specify funding amount required. 
            But the total cost should not exceed the max cost allowed"""

        if self.funding_amount_required and self.dgapplication_id.dgtype_code in ("BUR","SP"):
            max_cost = self.cost_per_student
            if self.funding_amount_required > max_cost:
                self.funding_amount_required = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':_(
                            "Total Funding amount required should not exceed {cost}"
                        ).format(
                            cost = max_cost
                        )
                    }
                }


    @api.onchange("disabled","no_learners")
    def _onchange_disabled(self):
        if self.disabled and self.no_learners:
            if self.disabled > self.no_learners:
                self.disabled = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message':_("No of disabled cannot be greater than the total no of learners")
                    }
                }

    @api.onchange('province_id','learnership_code')
    def _onchange_province_id(self):
        """
            The system must not allow the Employer to apply for the same programme unless
            the programmes are in different provinces.
        """ 
        pass    
        if self.province_id and self.learnership_code and self.organisation_id:
            record = self.search([
                ('learnership_code','=', self.learnership_code),
                ('province_id','=',self.province_id.id),
                ('organisation_id', '=', self.organisation_id.id),
                ('financial_year_id', '=', self.financial_year_id.id),
            ])
            _logger.info(f"LEARNERSHIP {record}")
            province  = self.province_id

            if record:
                self.province_id = False
                return {
                    'warning': {
                        'title': "Duplicate Application!",
                        'message':
                        _(
                            "You cannot apply for the same programme '{code}-{name}' "
                            "in the same province '{pr}'"
                            "in the same financial year '{fy}' "
                        ).format(
                            code = self.learnership_code,
                            name = self.learnership_id.name,
                            pr = province.name,
                            fy=self.financial_year_id.name,
                        )
                    }
                }


    @api.onchange('start_date')
    def _onchange_start_date(self):
        today = fields.Date.today()
        start_dt = self.start_date
        if self.start_date:
            if self.start_date < today:
                self.start_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f" The selected Start Date {start_dt} cannot be less than today"
                    }
                }
            if self.dgtype_code in ('LRN-Y','LRN-D','LRN-R','LRN-W'):
                start_date = date_utils.subtract(self.start_date, days=1)
                self.end_date = date_utils.add(start_date, years=1) 


    @api.onchange('end_date')
    def _onchange_end_date(self):
        end_date = self.end_date
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                self.end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.start_date}"
                    }
                }
                
            #ensure duration is not less than 7 months
            duration = date_tools.months_between(self.start_date, self.end_date)
            self.duration = duration
            _logger.info(f"DURATION => {duration}")

            if self.dgapplication_id.dgtype_code == "BUR" and duration < 7:
                self.end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"The duration of bursary should not be less than 7 months"
                    }
                }

            if self.dgapplication_id.dgtype_code == "SP" and duration > 6:
                #Duration must be 6 months or less 
                self.end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"The duration of skills Programme should not be greater than 6 months"
                    }
                }



# --------------------------------------------
# ORM Methods Override
# --------------------------------------------
    # @api.model #TODO: Generate reference when generating approval letter
    # def create(self, vals):
    #     res = super(InsetaDgApplicationDetails, self).create(vals)
    #     seq = self.env['ir.sequence'].next_by_code('inseta.application.reference') or '/'
    #     dg = self.env['inseta.dgapplication'].browse([vals.get('dgapplication_id')])
    #     sequence = seq.replace('DG_Code',dg.name)
    #     res.write({'name': sequence})
    #     return res

    def unlink(self):
        if self.state not in ('draft',):
            raise ValidationError(_('You cannot delete a submitted DG Application details'))
        return super(InsetaDgApplicationDetails, self).unlink()

# class InsetaDgBurspLearnerDetails(models.Model):
#     _name = 'inseta.dgbursplearnerdetails'  # Bursary and Skills Programme records are stored in dbo.dglearnerdetails.csv
#     _description = 'DG Bursary Skills Programme Learner Details'
#     _order= "id desc"

# class Internshipdetails(models.Model):
#     _name = "inseta.dginternshipprogrammedetails"
#     _description = "DG internship"

