from audioop import add
import base64
from xlwt import easyxf, Workbook
import logging
from io import BytesIO
import json
from datetime import date, timedelta

from odoo.tools import date_utils
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class InsetaWspAtrPeriod(models.Model):
    _name = 'inseta.wspatr.period'
    _description = "WSP/ATR Period"
    _order = "id desc"

    @api.model
    def default_get(self, fields_list):
        res = super(InsetaWspAtrPeriod, self).default_get(fields_list)
        # 2021-08-01 yyyy-mm-dd
        year = fields.Date.today().year
        str_start_date = f"{year}-01-01"
        # According to spec, WSP period ends every 30th April
        str_end_date = f"{year}-04-30"
        res.update({
            'start_date': str_start_date,
            'end_date': str_end_date,
        })
        return res

    state = fields.Selection([  # TODO: Implement automated action to close period
        ('Open', 'Open'),
        ('Close', 'Closed')
    ],
    )
    name = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year', required=True)
    start_date = fields.Date()
    end_date = fields.Date()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    #extension_date = fields.Date()

    @api.constrains("start_date", "end_date", "company_id")
    def _check_dates(self):
        """Check intersection with existing wsp years."""
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.start_date
            date_to = fy.end_date
            if date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting date.")
                )

            domain = fy._get_overlapping_domain()
            overlapping_fy = self.search(domain, limit=1)
            if overlapping_fy:
                raise ValidationError(
                    _(
                        "This WSP period '{fy}' "
                        "overlaps with '{overlapping_fy}'.\n"
                        "Please correct the start and/or end dates "
                        "of the WSP period."
                    ).format(
                        fy=fy.display_name,
                        overlapping_fy=overlapping_fy.display_name,
                    )
                )

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code(
            'inseta.wspatr.period.reference')
        vals['name'] = sequence or '/'
        return super(InsetaWspAtrPeriod, self).create(vals)

    def unlink(self):
        if self.state not in ('open',):
            raise ValidationError(_('You can delete a closed WSP Period')
                                  )
        return super(InsetaWspAtrPeriod, self).unlink()

    def _get_overlapping_domain(self):
        """Get domain for finding fiscal years overlapping with self.

        The domain will search only among fiscal years of this company.
        """
        self.ensure_one()
        # Compare with other fiscal years defined for this company
        company_domain = [
            ("id", "!=", self.id),
            ("company_id", "=", self.company_id.id),
        ]

        start_date = self.start_date
        end_date = self.end_date

        intersection_domain_from = [
            "&",
            ("start_date", "<=", start_date),
            ("end_date", ">=", end_date),
        ]
        # This fiscal year's `to` is contained in another fiscal year
        # other.from <= fy.to <= other.to
        intersection_domain_to = [
            "&",
            ("start_date", "<=", start_date),
            ("end_date", ">=", end_date),
        ]
        # This fiscal year completely contains another fiscal year
        # fy.from <= other.from (or other.to) <= fy.to
        intersection_domain_contain = [
            "&",
            ("start_date", ">=", start_date),
            ("end_date", "<=", end_date),
        ]
        intersection_domain = expression.OR(
            [
                intersection_domain_from,
                intersection_domain_to,
                intersection_domain_contain,
            ]
        )

        return expression.AND(
            [
                company_domain,
                intersection_domain,
            ]
        )

# ATR


class InsetaWspAtrTrainedBeneficiariesReport(models.Model):
    _name = 'inseta.wspatr.trained.beneficiaries.report'
    _description = "ATR Trained Beneficiaries Report"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    is_pivotal = fields.Boolean('Is Pivotal?', default=False)
    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2021')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id),('ofoyear','=','2021')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )

    municipality_id = fields.Many2one('res.municipality')
    programme_level = fields.Selection([
        ('Entry', 'Entry'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    training_provider = fields.Char()  # hide in small company
    completion_status = fields.Selection([
        ('Completed', 'Completed'),
        ('Not Completed', 'Not Completed'),
    ])

    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(
        compute="_compute_totals", store=True, readonly=False)
    grand_total_agegroup = fields.Integer(
        compute="_compute_totals", store=True, readonly=False)

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id',
        'programme_level',
        'training_provider',
        'completion_status')
    def _check_duplicate(self):
        '''
            Duplicates records are not accepted on the system - 
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, 
            OFO specialisation, 
            Programme Level, 
            training provider, 
            completion status, 
            scarce and critical skills, 
            intervention and NQF level. 
            if one of the above mentioned field is different then the system must all the record.
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
                ('programme_level', '=', rec.programme_level),
                ('training_provider', '=', rec.training_provider),
                ('completion_status', '=', rec.completion_status)
            ])
            if len(records) > 1:
                raise ValidationError(f"Duplicate record found for record: Occupation - {rec.ofo_occupation_id.name}\n \
                Specialization {rec.ofo_specialization_id.name}\n \
                Programme Level - {rec.programme_level}\n  \
                Training Provider - {rec.training_provider}\n \
                Completion Status {rec.completion_status}")

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(f"The Sum of Race & Gender MUST equal the sum of Age breakdown for record - \
                Specialization {rec.ofo_specialization_id.name}\n \
                Programme Level - {rec.programme_level}\n  \
                Training Provider - {rec.training_provider}\n \
                Completion Status {rec.completion_status}")

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }

    @api.onchange('ofo_specialization_id')
    def _onchange_ofo_specialization_id(self):
        ofo_occ = self.ofo_occupation_id
        ofo_spec = self.ofo_specialization_id

        ofo_occ_code = ofo_occ and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            self.ofo_specialization_id = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': _(
                        "Mixing of Ofo Code is not Allowed\n"
                        "Wrong specilization code '{spec_code}' for Ofo Occupation '{occ}' with code '{occ_code}' "
                        "Please select a specialization that has the same code as the ofo occupation"
                    ).format(
                        occ_code=ofo_occ.code,
                        occ=ofo_occ.name,
                        spec_code=ofo_spec.code,
                        # spec=ofo_spec.name
                    )
                }
            }


class InsetaWspAtrImplementationReport(models.Model):
    _name = 'inseta.wspatr.implementation.report'
    _description = "ATR Implementation Report"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    is_pivotal = fields.Boolean()

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation',
        'OFO Occupation',
        domain="[('ofoyear','=','2021')]"
    )
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id),('ofoyear','=','2021')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    programme_level = fields.Selection([
        ('Entry', 'Entry'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    training_provider = fields.Char()
    completion_status = fields.Selection([
        ('Completed', 'Completed'),
        ('Not Completed', 'Not Completed'),
    ])
    formsp_id = fields.Many2one(
        'res.formsp', 'Scarce and Critical Skills Priority')
    intervention_id = fields.Many2one('res.intervention', 'Intervention')
    formspl_id = fields.Many2one('res.formspl', 'NQF Level of Skill Priority')
    require_other_nqf_level = fields.Boolean(
        compute="_compute_require_other_nqf_level")
    formspl_notes = fields.Char('Other NQF Level of Skill Priority')
    inseta_funding = fields.Float()
    other_funding = fields.Float()
    company_funding = fields.Float()
    other_country = fields.Char('Foreign Country')
    other_country_id = fields.Many2one('res.country')

    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends("formspl_id")
    def _compute_require_other_nqf_level(self):
        for rec in self:
            other = self.env.ref(
                "inseta_base.data_formspl12")  # Other (Specify)
            if rec.formspl_id.id == other.id:
                rec.require_other_nqf_level = True
            else:
                rec.require_other_nqf_level = False

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id',
        'programme_level',
        'training_provider',
        'completion_status',
        'formsp_id',
        'intervention_id',
        'formspl_id')
    def _check_duplicate(self):
        '''
            Duplicates records are not accepted on the system - 
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, 
            OFO specialisation, 
            Programme Level, 
            training provider, 
            completion status, 
            scarce and critical skills, 
            intervention and 
            NQF level
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
                ('programme_level', '=', rec.programme_level),
                ('training_provider', '=', rec.training_provider),
                ('completion_status', '=', rec.completion_status),
                ('formsp_id', '=', rec.formsp_id.id),
                ('intervention_id', '=', rec.intervention_id.id),
                ('formspl_id', '=', rec.formspl_id.id)
            ])
            if len(records) > 1:
                raise ValidationError(f"Duplicate record found for record: Occupation - {rec.ofo_occupation_id.name}\n \
                    Specialization {rec.ofo_specialization_id.name}\n \
                    Programme Level - {rec.programme_level}\n  \
                    Training Provider - {rec.training_provider}\n \
                    Completion Status - {rec.completion_status}\n \
                    Scarce and Critical Skills Priority - {rec.formsp_id.name}\n \
                    intervention - {rec.intervention_id.name}\n \
                    NQF level - {rec.formspl_id.name}\n ")

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(f"The Sum of Race & Gender MUST equal the sum of Age breakdown for record - \
                Specialization {rec.ofo_specialization_id.name}\n \
                Programme Level - {rec.programme_level}\n  \
                Training Provider - {rec.training_provider}\n \
                Completion Status - {rec.completion_status}\n \
                Scarce and Critical Skills Priority - {rec.formsp_id.name}\n \
                intervention - {rec.intervention_id.name}\n \
                NQF level - {rec.formspl_id.name}\n ")

    @api.onchange(
        'african_male',
        'african_female',
        'african_disabled',
        'indian_male',
        'indian_female',
        'indian_disabled',
        'colored_male',
        'colored_female',
        'colored_disabled',
        'white_male',
        'white_female',
        'white_disabled',
    )
    def _onchange_gender_breakdown(self):
        if self.other_country:
            if self.african_male > 0 or \
                    self.african_female > 0 or \
                    self.african_disabled > 0 or \
                    self.indian_male > 0 or \
                    self.indian_female > 0 or \
                    self.indian_disabled > 0 or \
                    self.colored_male > 0 or \
                    self.colored_female > 0 or \
                    self.colored_disabled > 0 or \
                    self.white_male > 0 or \
                    self.white_female > 0 or \
                    self.white_disabled > 0:
                raise ValidationError(_(
                    "You can ONLY record gender breakdown under"
                    "Foreign Nationals section when Foreign Country is selected"
                ))

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }

    @api.onchange('ofo_specialization_id')
    def _onchange_ofo_specialization_id(self):
        ofo_occ = self.ofo_occupation_id
        ofo_spec = self.ofo_specialization_id

        ofo_occ_code = ofo_occ and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            self.ofo_specialization_id = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': _(
                        "Mixing of Ofo Code is not Allowed\n"
                        "Ofo Occupation Code '{occ_code}' for Occupation '{occ}'."
                        "must be the same as ofo specilization code '{spec_code}' for specialization '{spec}' "
                    ).format(
                        occ_code=ofo_occ.code,
                        occ=ofo_occ.name,
                        spec_code=ofo_spec.code,
                        spec=ofo_spec.name
                    )
                }
            }

    def write(self, vals):
        if self.wspatr_id.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot modify  Implementation Report for an Approved or Rejected WSP'))
        return super(InsetaWspAtrImplementationReport, self).write(vals)

    def unlink(self):
        if self.wspatr_id.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot delete Implementation Report for approved or Rejected WSP'))
        return super(InsetaWspAtrImplementationReport, self).unlink()


class InsetaWspAtrLearningProgrammes(models.Model):
    _name = 'inseta.wspatr.learning.programmes'
    _description = "ATR Learning Programmes"
    _order = "id desc"
    _rec_name = "formoccupation_id"

    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    formoccupation_id = fields.Many2one(
        'res.formoccupation', 'Occupational Group')
    learning_programme = fields.Char()
    formsp_id = fields.Many2one(
        'res.formsp', 'Which scarce and critical occupation is the training linked to?')
    inseta_funding = fields.Float()
    other_funding = fields.Float()
    company_funding = fields.Float()
    training_provider = fields.Char()
    form_cred_id = fields.Many2one('res.formcred', 'Credit Bearing')
    nqf_level_id = fields.Many2one('res.nqflevel', 'NQF Level')
    no_of_employees = fields.Integer()

    total_funding = fields.Integer(compute="_compute_totals")
    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'inseta_funding',
        'other_funding',
        'company_funding',
    )
    def _compute_totals(self):
        for rec in self:
            rec.total_funding = sum(
                [rec.inseta_funding, rec.other_funding, rec.company_funding])

    @api.constrains(
        'formoccupation_id',
        'learning_programme',
        'formsp_id',
        'training_provider',
        'nqf_level_id')
    def _check_duplicate(self):
        '''
            a record is considered a duplicate when the following fields are the same: 
            Occupational group, 
            Learning programme, 
            scarce and critical skills, 
            Training provider, 
            credit bearing and NQF level. 
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('formoccupation_id', '=', rec.formoccupation_id.id),
                ('learning_programme', '=', rec.learning_programme),
                ('formsp_id', '=', rec.formsp_id.id),
                ('training_provider', '=', rec.training_provider),
                ('nqf_level_id', '=', rec.nqf_level_id.id)
            ])
            if len(records) > 1:
                raise ValidationError(
                    f"Duplicate record found for {rec.formoccupation_id.name} {rec.learning_programme} {rec.formsp_id.name} {rec.training_provider} {rec.nqf_level_id.name}")


class InsetaWspAtrVarianceReport(models.Model):
    _name = 'inseta.wspatr.variancereport'  # dbo.wspatrvariancereport.csv
    _description = "ATR 3 Variance Report"
    _order = "id desc"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        string='Major Occupation',
    )
    totalplanned = fields.Integer()
    totaltrained = fields.Integer()
    variance_perc = fields.Integer('Variance')
    variancereason_id = fields.Many2one('res.variancereason')
    variancereason_other = fields.Char()
    is_pivotal = fields.Boolean(default=False)
    requires_reason = fields.Boolean(compute="_compute_requires_reason")
    legacy_system_id = fields.Integer()

    @api.depends('totalplanned', 'totaltrained')
    def _compute_requires_reason(self):
        """The system must require reasons only if the trained beneficiaries are less than the planned beneficiries
        """
        for rec in self:
            if rec.totaltrained < rec.totalplanned:
                rec.requires_reason = False
            else:
                rec.requires_reason = False


class InsetaWspAtrTrainedAet(models.Model):
    _name = 'inseta.wspatr.trained.aet'
    _description = "ATR Trained Adult Education And Training"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2021')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id),('ofoyear','=','2021')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    first_name = fields.Char()
    last_name = fields.Char('Surname')
    id_no = fields.Char()
    equity_id = fields.Many2one('res.equity', 'Population Group')
    gender_id = fields.Many2one('res.gender', 'Gender')
    disability_id = fields.Many2one(
        'res.disability', string="Disability Status")
    municipality_id = fields.Many2one(
        'res.municipality', string='Municipality')
    aet_start_date = fields.Date()
    aet_end_date = fields.Date()
    training_provider = fields.Char()
    aet_level_id = fields.Many2one('res.aetlevel')
    aet_subject_id = fields.Many2one('res.aetsubject', 'AET Subject')
    learner_programme_status = fields.Selection(
        [('Registered', 'Registered'), ('Completed', 'Completed')])
    is_inseta_funded = fields.Selection(
        [('Yes', 'Yes'), ('No', 'No')], 'Is INSETA Funded?')
    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False
    # --------------------------------------------
    # Onchange methods and overrides
    # --------------------------------------------

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id')
    def _check_duplicate(self):
        '''
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, OFO specialisation
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
            ])
            if len(records) > 1:
                raise ValidationError(
                    f"Duplicate record found for record: Occupation - {rec.ofo_occupation_id.name}, Specialization - {rec.ofo_specialization_id.name} ")

    @api.onchange('ofo_specialization_id')
    def _onchange_ofo_specialization_id(self):
        ofo_occ = self.ofo_occupation_id
        ofo_spec = self.ofo_specialization_id

        ofo_occ_code = ofo_occ and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            self.ofo_specialization_id = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': _(
                        "Mixing of Ofo Code is not Allowed\n"
                        "Wrong specilization code '{spec_code}' for Ofo Occupation '{occ}' with code '{occ_code}' "
                        "Please select a specialization that has the same code as the ofo occupation"
                    ).format(
                        occ_code=ofo_occ.code,
                        occ=ofo_occ.name,
                        spec_code=ofo_spec.code,
                        # spec=ofo_spec.name
                    )
                }
            }

    @api.onchange("id_no")
    def _onchange_id_no(self):
        """Update gender and birth_date fields on validation of R.S.A id_no"""
        if self.id_no:
            original_idno = self.id_no
            identity = validate_said(self.id_no)
            if not identity:
                self.id_no = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Invalid R.S.A Identification No. {original_idno}"
                    }
                }


class InsetaWspAtrHardtofillVacancies(models.Model):  # small firms
    _name = 'inseta.wspatr.hardtofillvacancies'
    _description = "ATR 3 Hard to fill vacancies"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2021')]")
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    province_id = fields.Many2one(
        'res.country.state',
        string='Province',
        domain=[('country_id.code', '=', 'ZA')]
    )
    # TODO: Delete . replaced by vacancyreason_ids
    vacancyreason_id = fields.Many2one('res.vacancyreason')
    vacancyreason_ids = fields.Many2many(
        'res.vacancyreason',
        'wspatr_hardtofillvacancies_reasons_rel',
        'hardtofillvacancy_id',
        'vacancyreason_id',
        string="Vacancy Reasons",
        help="We could have multiple reasons"
    )

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False

    def write(self, vals):
        if self.wspatr_id.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot modify record for an Approved or Rejected WSP'))
        return super(InsetaWspAtrHardtofillVacancies, self).write(vals)

    def unlink(self):
        if self.wspatr_id.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot delete record for approved or Rejected WSP'))
        return super(InsetaWspAtrHardtofillVacancies, self).unlink()


class InsetaWspAtrSkillsGap(models.Model):
    _name = 'inseta.wspatr.vacanciesskillsgap'  # dbo.wspatrvacanciesskillsgap
    _description = "ATR form 4: Skills Gaps"
    _order = "id desc"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    managersgap1 = fields.Many2one('res.formskillsgap')
    managersgap2 = fields.Many2one('res.formskillsgap')
    managersgap3 = fields.Many2one('res.formskillsgap')
    managersreasons1 = fields.Many2one('res.formskillsgapreasons')
    managersreasons2 = fields.Many2one('res.formskillsgapreasons')
    managersreasons3 = fields.Many2one('res.formskillsgapreasons')

    professionalsgap1 = fields.Many2one('res.formskillsgap')
    professionalsgap2 = fields.Many2one('res.formskillsgap')
    professionalsgap3 = fields.Many2one('res.formskillsgap')
    professionalsreasons1 = fields.Many2one('res.formskillsgapreasons')
    professionalsreasons2 = fields.Many2one('res.formskillsgapreasons')
    professionalsreasons3 = fields.Many2one('res.formskillsgapreasons')

    techniciansgap1 = fields.Many2one(
        'res.formskillsgap', 'Technicians and Associate Professionals 1')
    techniciansgap2 = fields.Many2one(
        'res.formskillsgap', 'Technicians and Associate Professionals 2')
    techniciansgap3 = fields.Many2one(
        'res.formskillsgap', 'Technicians and Associate Professionals 3')
    techniciansreasons1 = fields.Many2one('res.formskillsgapreasons')
    techniciansreasons2 = fields.Many2one('res.formskillsgapreasons')
    techniciansreasons3 = fields.Many2one('res.formskillsgapreasons')

    clericalsupportworkergap1 = fields.Many2one('res.formskillsgap')
    clericalsupportworkergap2 = fields.Many2one('res.formskillsgap')
    clericalsupportworkergap3 = fields.Many2one('res.formskillsgap')
    clericalsupportworkerreasons1 = fields.Many2one('res.formskillsgapreasons')
    clericalsupportworkerreasons2 = fields.Many2one('res.formskillsgapreasons')
    clericalsupportworkerreasons3 = fields.Many2one('res.formskillsgapreasons')

    servicesalesworkersgap1 = fields.Many2one('res.formskillsgap')
    servicesalesworkersgap2 = fields.Many2one('res.formskillsgap')
    servicesalesworkersgap3 = fields.Many2one('res.formskillsgap')
    servicesalesworkersreasons1 = fields.Many2one('res.formskillsgapreasons')
    servicesalesworkersreasons2 = fields.Many2one('res.formskillsgapreasons')
    servicesalesworkersreasons3 = fields.Many2one('res.formskillsgapreasons')

    skilledtradesworkersgap1 = fields.Many2one('res.formskillsgap')
    skilledtradesworkersgap2 = fields.Many2one('res.formskillsgap')
    skilledtradesworkersgap3 = fields.Many2one('res.formskillsgap')
    skilledtradesworkersreasons1 = fields.Many2one('res.formskillsgapreasons')
    skilledtradesworkersreasons2 = fields.Many2one('res.formskillsgapreasons')
    skilledtradesworkersreasons3 = fields.Many2one('res.formskillsgapreasons')

    plantmachineoperatorsgap1 = fields.Many2one('res.formskillsgap')
    plantmachineoperatorsgap2 = fields.Many2one('res.formskillsgap')
    plantmachineoperatorsgap3 = fields.Many2one('res.formskillsgap')
    plantmachineoperatorsreasons1 = fields.Many2one('res.formskillsgapreasons')
    plantmachineoperatorsreasons2 = fields.Many2one('res.formskillsgapreasons')
    plantmachineoperatorsreasons3 = fields.Many2one('res.formskillsgapreasons')

    elementaryoccupationsgap1 = fields.Many2one('res.formskillsgap')
    elementaryoccupationsgap2 = fields.Many2one('res.formskillsgap')
    elementaryoccupationsgap3 = fields.Many2one('res.formskillsgap')
    elementaryoccupationsreasons1 = fields.Many2one('res.formskillsgapreasons')
    elementaryoccupationsreasons2 = fields.Many2one('res.formskillsgapreasons')
    elementaryoccupationsreasons3 = fields.Many2one('res.formskillsgapreasons')
    confirm = fields.Boolean()

    @api.constrains('wspatr_id')
    def _check_duplicate(self):
        '''
            Only one Skills Gaps can be addded for a WSP submission 
        '''
        for rec in self:
            records = self.search([('wspatr_id', '=', rec.wspatr_id.id)])
            if len(records) > 1:
                raise ValidationError(
                    "You can only add one Skills Gaps record per WSP/ATR submission")

    def write(self, vals):
        if self.wspatr_id.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot modify record for an Approved or Rejected WSP'))
        return super(InsetaWspAtrSkillsGap, self).write(vals)

    def unlink(self):
        if self.wspatr_id.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot delete record for approved or Rejected WSP'))
        return super(InsetaWspAtrSkillsGap, self).unlink()


class InsetaWspAtrPivotalTrainedBeneficiaries(models.Model):
    _name = 'inseta.wspatr.pivotal.trained.beneficiaries'
    _description = "ATR Pivotal Trained Beneficiaries"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2021')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('ofoyear','=','2021')]"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    programme_level = fields.Selection([
        ('Entry', 'Entry'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    training_provider = fields.Char()  # hide in small company
    completion_status = fields.Selection([
        ('Completed', 'Completed'),
        ('Not Completed', 'Not Completed'),
    ], 'Completion Status')
    start_date = fields.Date()
    end_date = fields.Date()
    nqf_level_id = fields.Many2one('res.nqflevel', 'NQF Level')
    municipality_id = fields.Many2one('res.municipality')
    socio_economic_status = fields.Selection([
        ('UnEmployed', 'UnEmployed'),
        ('Employed', 'Employed')
    ])
    pivotal_programme_id = fields.Many2one('res.pivotal.programme')
    other_pivotal_programme = fields.Char()
    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id',
        'programme_level',
        'training_provider',
        'completion_status',
        'start_date',
        'end_date',
        'nqf_level_id',
        'municipality_id',
        'socio_economic_status',
        'pivotal_programme_id')
    def _check_duplicate(self):
        '''
            Duplicates records are not accepted on the system - 
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, OFO specialisation, Programme Level, training provider, 
            completion status, Start and end dates, NQF level, municpality, 
            socio economic status and PIVOTAL programme
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
                ('programme_level', '=', rec.programme_level),
                ('training_provider', '=', rec.training_provider),
                ('completion_status', '=', rec.completion_status),
                ('start_date', '=', rec.start_date),
                ('end_date', '=', rec.end_date),
                ('nqf_level_id', '=', rec.nqf_level_id.id),
                ('municipality_id', '=', rec.municipality_id.id),
                ('socio_economic_status', '=', rec.socio_economic_status),
                ('pivotal_programme_id', '=', rec.pivotal_programme_id.id)
            ])
            if len(records) > 1:
                raise ValidationError(f"Duplicate record found for Occupation - {rec.ofo_occupation_id.name}\n \
                    Specialization - {rec.ofo_specialization_id.name}\n \
                    Programme Level - {rec.programme_level}\n \
                    Training Provider - {rec.training_provider}\n \
                    Completetion Status - {rec.completion_status}\n \
                    start date - {rec.start_date}\n \
                    end date - {rec.end_date}\n \
                    NQF Level {rec.nqf_level_id.name}\n \
                    Municipality - {rec.municipality_id.name}\n \
                    Socio Economic Status - {rec.socio_economic_status}\n \
                    Pivotal programme - {rec.pivotal_programme_id.name}"
                                      )

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(
                    f"The Sum of Race & Gender MUST equal the sum of Age breakdown for record - Occupation '{rec.ofo_occupation_id.code} {rec.ofo_occupation_id.name}' and Specialization '{rec.ofo_specialization_id.code} {rec.ofo_specialization_id.name}'")

    @api.onchange('ofo_specialization_id')
    def _onchange_ofo_specialization_id(self):
        ofo_occ = self.ofo_occupation_id
        ofo_spec = self.ofo_specialization_id

        ofo_occ_code = ofo_occ and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            self.ofo_specialization_id = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': _(
                        "Mixing of Ofo Code is not Allowed\n"
                        "Wrong specilization code '{spec_code}' for Ofo Occupation '{occ}' with code '{occ_code}' "
                        "Please select a specialization that has the same code as the ofo occupation"
                    ).format(
                        occ_code=ofo_occ.code,
                        occ=ofo_occ.name,
                        spec_code=ofo_spec.code,
                        # spec=ofo_spec.name
                    )
                }
            }


class InsetaWspAtrkillsdevconsultplanning(models.Model):
    # dbo.wspatrskillsdevelopmentconsultationplanning
    _name = 'inseta.wspatr.skillsdevconsultplanning'
    _description = "WSP form 1: Skills Development Consultation and Planning."
    _order = "id desc"

    YES_NO = [('Yes', 'Yes'), ('No', 'No')]

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    state = fields.Selection(related="wspatr_id.state")
    workplacespid = fields.Many2one(
        'res.workplacesp', '1.1. What process was used to develop the Workplace Skills Plan?')
    require_1_1_1 = fields.Boolean(compute="_compute_require_1_1_1")
    comment1 = fields.Text(
        '1.1.1. Please add additional comments if applicable')
    comment2 = fields.Text(
        '1.2. Provide a brief summary of the impact of the legislation on the organization i.e. FAIS regulatory exams')
    # 1.3. Note: Question must be posed and completed by people in the following occupational areas and not completed by SDF: How much has your job changed in the last 12 months and in the last 3 years?
    underwriter = fields.Text('1.3.1. Underwriter')
    insurancebroker = fields.Text('1.3.2. Insurance Broker')
    itoccupations = fields.Text(
        '1.3.3. Software Developer / Programmer / IT related occupations')
    claims = fields.Text('1.3.4. Claims Clerks / Manager / Assessor')
    salesmanager = fields.Text('1.3.5. Sales Managers')
    accountant = fields.Text('1.3.6. Accountant')
    actuary = fields.Text('1.3.7. Actuary')
    merged = fields.Selection(
        YES_NO, string='1.4. Has your Organisation gone through any restructuringin the past 12 months due to merger/acquisition?')  # mergeid
    # 1.5. Number of people retrenched/dismissed/resigned for the period 1 January 2019 to 31 December 2019
    retrenched = fields.Integer('1.5.1. Retrenched')
    dismissedmisconduct = fields.Integer('1.5.2. Dismissed - Misconduct')
    resigned = fields.Integer('1.5.3. Resigned')
    deceased = fields.Integer('1.5.4. Deceased')
    retired = fields.Integer('1.5.5. Retired')
    nonrenewal = fields.Integer('1.5.6. Non- Renewal of Contract')
    dismissedincapacity = fields.Integer('1.5.7. Dismissed - Incapacity')
    dismissednoncompliance = fields.Integer(
        '1.5.8. Dismissed – Non-compliance ( RE )')
    # 1.6. In order to measure the impact of training in your Organisation kindly state:
    productivity = fields.Selection([
        ('Increased', 'Increased'),
        ('Decreased', 'Decreased')
    ], string='1.6.1. Has productivity increased or decreased in the Organisation?')  # formprodid
    comment4 = fields.Text('1.6.2. What are your findings based on?')
    # 1.7. Class of Business for the Organisation
    productprovider = fields.Selection(
        YES_NO, string='1.7.1. Are you a product provider?')
    providercorebusiness_id = fields.Many2one(
        'res.formclass', string='1.7.1.1. What is your Core business?')  # providercoreid
    comments5 = fields.Text('1.7.1.2. Comment')
    providersecondary_id = fields.Many2one(
        'res.formclass', string='1.7.1.3. What is your Secondary business?')
    comments6 = fields.Text('1.7.1.4. Comment')
    broker = fields.Selection(YES_NO, string='1.7.2. Are you a Broker?')
    brokercorebusiness_id = fields.Many2one(
        'res.formclass', string='1.7.2.1. What is your Core business?')
    comments7 = fields.Text('1.7.2.2. Comment')
    brokersecondary_id = fields.Many2one(
        'res.formclass', string='1.7.2.3. What is your Secondary business?')
    comments8 = fields.Text('1.7.2.4. Comment')
    payroll = fields.Integer(
        '1.8. What is the percentage of payroll spent on training?')

    @api.depends('workplacespid')
    def _compute_require_1_1_1(self):
        for rec in self:
            other_methods = self.env.ref(
                "inseta_skills.data_workplacesp4", raise_if_not_found=False)
            if (rec.workplacespid and other_methods) and (rec.workplacespid.id == other_methods.id):
                rec.require_1_1_1 = True
            else:
                rec.require_1_1_1 = False

    @api.constrains('productprovider', 'broker')
    def _check_productprovider_and_broker(self):
        """ The system must not allow the SDF to select option No on both 1.7.1 and 1.7.2.
        """
        for rec in self:
            if rec.broker == "No" and rec.productprovider == "No":
                raise ValidationError(
                    _("Both 1.7.1 and 1.7.2 cannot be 'No'.\nYou must answer yes for either of the questions."))

    @api.constrains('wspatr_id')
    def _check_duplicate(self):
        '''
            Only one skill dev and consult can be addded for a WSP submission 
        '''
        for rec in self:
            records = self.search([('wspatr_id', '=', rec.wspatr_id.id)])
            if len(records) > 1:
                raise ValidationError(
                    "You can only add one Skills Dev. & Consult record per WSP/ATR submission")


class InsetaWspAtrEmploymentProfile(models.Model):
    _name = 'inseta.wspatr.employment.profile'
    _description = "WSP Employment Profile"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    is_small_firm = fields.Boolean(related="wspatr_id.is_small_firm")
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2022')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id), ('ofoyear','=','2022')]"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view",
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(
                    f"The Sum of Race & Gender MUST equal the sum of Age breakdown for the record - Occupation '{rec.ofo_occupation_id.code} {rec.ofo_occupation_id.name}' and Specialization '{rec.ofo_specialization_id.code} {rec.ofo_specialization_id.name}'")

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id')
    def _check_duplicate(self):
        '''
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, OFO specialisation
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
            ])
            if len(records) > 1:
                raise ValidationError(
                    f"Duplicate record found for record: Occupation - {rec.ofo_occupation_id.name}, Specialization - {rec.ofo_specialization_id.name} ")

    @api.onchange('ofo_specialization_id')
    def _onchange_ofo_specialization_id(self):
        ofo_occ = self.ofo_occupation_id
        ofo_spec = self.ofo_specialization_id

        ofo_occ_code = ofo_occ and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            self.ofo_specialization_id = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': _(
                        "Mixing of Ofo Code is not Allowed\n"
                        "Wrong specilization code '{spec_code}' for Ofo Occupation '{occ} - {occ_code}' "
                        "Please select a specialization that has the same code as the ofo occupation"
                    ).format(
                        occ_code=ofo_occ.code,
                        occ=ofo_occ.name,
                        spec_code=ofo_spec.code,
                        # spec=ofo_spec.name
                    )
                }
            }

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }


class InsetaWspAtrHighestEduProfile(models.Model):
    _name = 'inseta.wspatr.highest.educational.profile'
    _description = "WSP Highest Educational Profile"
    _order = "id desc"
    _rec_name = "formspl_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    state = fields.Selection(related="wspatr_id.state")

    is_small_firm = fields.Boolean(related="wspatr_id.is_small_firm")

    formspl_id = fields.Many2one('res.formspl', 'NQF Level Of Skill Priority')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")
    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(
                    f"The Sum of Race & Gender MUST equal the sum of Age breakdown for the record - '{rec.formspl_id.name}' ")

    @api.constrains(
        'wspatr_id',
        'formspl_id')
    def _check_duplicate(self):
        '''
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, OFO specialisation
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('formspl_id', '=', rec.formspl_id.id),
            ])
            if len(records) > 1:
                raise ValidationError(
                    f"Duplicate record found for record: - '{rec.formspl_id.name}' ")


class InsetaWspAtrProvincialBreakdown(models.Model):
    _name = 'inseta.wspatr.provincialbreakdown'
    _description = "WSP 4 Provincial breakdown"
    _order = "id desc"
    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    state = fields.Selection(related="wspatr_id.state")
    parent_sdl_no = fields.Char(compute="_compute_parent_sdl_no")
    sdl_no = fields.Char('SDL No')
    sic_code_id = fields.Many2one(
        'res.sic.code',
        'SIC Code',
    )
    easterncape = fields.Integer('Eastern Cape')
    freestate = fields.Integer('Free State')
    gauteng = fields.Integer('Gauteng')
    kwazulunatal = fields.Integer('KwaZulu Natal')
    limpopo = fields.Integer('Limpopo')
    northwest = fields.Integer('North West')
    northerncape = fields.Integer('Northern Cape')
    mpumalanga = fields.Integer('Mpumalanga')
    westerncape = fields.Integer('Western Cape')
    total = fields.Integer(compute="_compute_total", store=True)
    company_size = fields.Selection(
        [('Small', 'Small'), ('Medium', 'Medium'), ('Large', 'Large')], string="Company Size")
    levy_status = fields.Selection(
        [('Levy Paying', 'Levy Paying'), ('Non-Levy Paying', 'Non-Levy Paying')])
    noemployees = fields.Integer()
    reasons = fields.Text()
    


    @api.depends('wspatr_id')
    def _compute_parent_sdl_no(self):
        for rec in self:
            if rec.wspatr_id:
                rec.parent_sdl_no = rec.wspatr_id.organisation_id.sdl_no
            else:
                rec.parent_sdl_no = False

    @api.depends(
        'easterncape',
        'freestate',
        'gauteng',
        'kwazulunatal',
        'limpopo',
        'northwest',
        'northerncape',
        'mpumalanga',
        'westerncape'
    )
    def _compute_total(self):
        for rec in self:
            rec.total = sum([
                rec.easterncape, rec.freestate,
                rec.gauteng, rec.kwazulunatal,
                rec.limpopo, rec.northwest,
                rec.northerncape, rec.mpumalanga,
                rec.westerncape
            ])

    @api.onchange('noemployees','total')
    def _onchange_no_employees(self):
        if self.noemployees <= 49:
            self.company_size = 'Small'

        elif self.noemployees > 49 and self.noemployees <= 149:
            self.company_size  = "Medium"
        else:
            self.company_size = "Large"

    @api.constrains(
        'wspatr_id',
        'sdl_no')
    def _check_sdl_no(self):
        '''
            Ensure single record is added for each sdl no
        '''
        wsp_org_sdl_no = self.wspatr_id.organisation_id.sdl_no
        linked_orgs = self.wspatr_id.organisation_id.linkage_ids
        linked_org_sdl_nos = linked_orgs and linked_orgs.childorganisation_id.mapped(
            'sdl_no') or []
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('sdl_no', '=', rec.sdl_no),
            ])
            if len(records) > 1:
                raise ValidationError(
                    f"Duplicate record found for record: - '{rec.sdl_no}' ")

            # validate SDL no for imported records
            sdl_no = rec.sdl_no.replace(" ", "")
            if sdl_no:
                record = self.env['inseta.organisation'].search(
                    [('sdl_no', '=', sdl_no)])
                if not record:
                    raise ValidationError(
                        _("Organisation with SDL no '{sdl_no}' not found!").format(sdl_no=sdl_no,))

            # check if provided SDL belongs to the company
            if not sdl_no == wsp_org_sdl_no:
                # check if it belongs to employer child organisations
                if sdl_no not in linked_org_sdl_nos:
                    raise ValidationError(
                        _("SDL No '{sdl_no}' does not belong to this employer OR employers child organisations!. Please provide correct SDL No and try again.").format(sdl_no=sdl_no,))

    @api.onchange('sdl_no')
    def _onchange_sdl_no(self):
        if self.sdl_no:
            wsp_org_sdl_no = self.wspatr_id.organisation_id.sdl_no
            linked_orgs = self.wspatr_id.organisation_id.linkage_ids
            linked_org_sdl_nos = linked_orgs and linked_orgs.childorganisation_id.mapped(
                'sdl_no') or []
            sdl_no = self.sdl_no.replace(" ", "")
            if sdl_no:
                record = self.env['inseta.organisation'].search(
                    [('sdl_no', '=', sdl_no)])
                if not record:
                    self.sdl_no = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Organisation with SDL no '{sdl_no}' not found!"
                            ).format(
                                sdl_no=sdl_no,
                            )

                        }
                    }
            # check if provided SDL belongs to the company
            if not sdl_no == wsp_org_sdl_no:
                # check if it belongs to employer child organisations
                if sdl_no not in linked_org_sdl_nos:
                    self.sdl_no = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "SDL No '{sdl_no}' does not belong to this employer OR employers child organisations!. Please provide correct SDL No and try again."
                            ).format(
                                sdl_no=sdl_no,
                            )

                        }
                    }


class InsetaWspAtrPlannedAetTraining(models.Model):
    _name = 'inseta.wspatr.planned.aet.training'
    _description = "WSP Planned AET Training"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2022')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id),('ofoyear','=','2022')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(
                    f"The Sum of Race & Gender MUST equal the sum of Age breakdown for the record - Occupation '{rec.ofo_occupation_id.code} {rec.ofo_occupation_id.name}' and Specialization '{rec.ofo_specialization_id.code} {rec.ofo_specialization_id.name}'")

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id')
    def _check_duplicate(self):
        '''
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, OFO specialisation
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
            ])
            if len(records) > 1:
                raise ValidationError(
                    f"Duplicate record found for record: Occupation - {rec.ofo_occupation_id.name}, Specialization - {rec.ofo_specialization_id.name} ")

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }


class InsetaWspAtrPlannedBeneficiaries(models.Model):
    """ Does not apply to small firms. This is equivalent to Workplace skills plan in small forms"""
    _name = 'inseta.wspatr.planned.beneficiaries'  # dbo.wspatrplannedbeneficiaries.csv
    _description = "WSP Planned Beneficiaries"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    is_pivotal = fields.Boolean()
    state = fields.Selection(related='wspatr_id.state')
    financial_year_id = fields.Many2one(
        'res.financial.year', related="wspatr_id.financial_year_id")
    is_small_firm = fields.Boolean(related="wspatr_id.is_small_firm")
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2022')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id), ('ofoyear','=','2022')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    programme_level = fields.Selection([
        ('Entry', 'Entry'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    socio_economic_status = fields.Selection([
        ('UnEmployed', 'UnEmployed'),
        ('Employed', 'Employed')
    ])
    municipality_id = fields.Many2one('res.municipality')
    formsp_id = fields.Many2one(
        'res.formsp', 'Scarce and Critical Skills Priority')

    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id',
        'programme_level',
        'municipality_id',
        'formsp_id')
    def _check_duplicate(self):
        '''
            A record is considered a duplicate when the following fields are the same: 
            OFO code occupation, 
            OFO code specilisation, 
            Programme level, 
            scarce and critical skills, 
            and NQF level.
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
                ('programme_level', '=', rec.programme_level),
                ('municipality_id', '=', rec.municipality_id.id),
                ('formsp_id', '=', rec.formsp_id.id)
            ])
            if len(records) > 1:
                raise ValidationError(f"Duplicate record found for Occupation - {rec.ofo_occupation_id.name}\n \
                    Specialization - {rec.ofo_specialization_id.name}\n \
                    Programme Level - {rec.programme_level}\n \
                    Municipality - {rec.municipality_id.name}\n \
                    Scarce & Critical Skills Priority- {rec.formsp_id.name}"
                                      )

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(f"The Sum of Race & Gender MUST equal the sum of Age breakdown for record - \n \
                    Occupation '{rec.ofo_occupation_id.code} {rec.ofo_occupation_id.name}' - \n \
                    Specialization '{rec.ofo_specialization_id.code} {rec.ofo_specialization_id.name}' - \n \
                    Programme Level '{rec.programme_level}' - \n \
                    Municipality '{rec.municipality_id.name}' - \n \
                    Scarce & Critical Skills Priority '{rec.formsp_id.name}'"
                                      )

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }


class InsetaWspAtrWorkplaceskillsplan(models.Model):
    """same as WSP Planned Beneficiaries for Large forms.
     This was created for backward compatiblity with the legacy system
    """
    _name = 'inseta.wspatr.workplaceskillsplan'  # dbo.wspatrworkplaceskillsplan.csv => 2020_WSP_Training_Planned_V1 for small organisations
    _description = "WSP Workplace Skills Plan"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    is_pivotal = fields.Boolean()
    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2022')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id),('ofoyear','=','2022')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )
    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    programme_level = fields.Selection([
        ('Entry', 'Entry'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    # small firms fields
    formsp_id = fields.Many2one(
        'res.formsp', 'Scarce and Critical Skills Priority')
    formspl_id = fields.Many2one('res.formspl', 'NQF Level of Skill Priority')
    require_other_nqf_level = fields.Boolean(
        compute="_compute_require_other_nqf_level")
    formspl_notes = fields.Char('Other NQF Level of Skill Priority')

    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends("formspl_id")
    def _compute_require_other_nqf_level(self):
        for rec in self:
            other = self.env.ref(
                "inseta_base.data_formspl12")  # Other (Specify)
            if rec.formspl_id.id == other.id:
                rec.require_other_nqf_level = True
            else:
                rec.require_other_nqf_level = False

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id',
        'programme_level',
        'formsp_id',
        'formspl_id')
    def _check_duplicate(self):
        '''
            A record is considered a duplicate when the following fields are the same: 
            OFO code occupation, 
            OFO code specilisation, 
            Programme level, 
            scarce and critical skills, 
            and NQF level.
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
                ('programme_level', '=', rec.programme_level),
                ('formsp_id', '=', rec.formsp_id.id),
                ('formspl_id', '=', rec.formspl_id.id)
            ])
            if len(records) > 1:
                raise ValidationError(f"Duplicate record found for Occupation - {rec.ofo_occupation_id.name}\n \
                    Specialization - {rec.ofo_specialization_id.name}\n \
                    Programme Level - {rec.programme_level}\n \
                    NQF Level of Skill Priority '{rec.formspl_id.name}' - \n \
                    Scarce & Critical Skills Priority- {rec.formsp_id.name}"
                                      )

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(f"The Sum of Race & Gender MUST equal the sum of Age breakdown for record - \n \
                    Occupation '{rec.ofo_occupation_id.code} {rec.ofo_occupation_id.name}' - \n \
                    Specialization '{rec.ofo_specialization_id.code} {rec.ofo_specialization_id.name}' - \n \
                    Programme Level '{rec.programme_level}' - \n \
                    NQF Level of Skill Priority '{rec.formspl_id.name}' - \n \
                    Scarce & Critical Skills Priority '{rec.formsp_id.name}'"
                                      )

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }


class InsetaWspAtrPivotalPlannedBeneficiaries(models.Model):
    _name = 'inseta.wspatr.pivotal.planned.beneficiaries'
    _description = "WSP Pivotal Planned Beneficiaries"
    _order = "id desc"
    _rec_name = "ofo_occupation_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    is_small_firm = fields.Boolean(
        related="wspatr_id.is_small_firm", store=True)
    ofo_occupation_id = fields.Many2one(
        'res.ofo.occupation', 'OFO Occupation', domain="[('ofoyear','=','2022')]")
    ofo_specialization_id = fields.Many2one(
        'res.ofo.specialization',
        domain="[('occupation_id','=',ofo_occupation_id), ('ofoyear','=','2022')]",
        string="OFO Specialisation"
    )
    require_ofo_specialization = fields.Boolean(
        compute="_compute_ofo_specialization",
        help="indicates if specialization should be required in the view"
    )

    ofo_majorgroup_id = fields.Many2one(
        'res.ofo.majorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Major Group"
    )
    ofo_submajorgroup_id = fields.Many2one(
        'res.ofo.submajorgroup',
        compute='_compute_ofo_specialization',
        store=True,
        string="OFO Sub Major Group"
    )
    programme_level = fields.Selection([  # hide in small company
        ('Entry', 'Entry'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    training_provider = fields.Char()  # hide in small company
    start_date = fields.Date()  # hide in small company
    end_date = fields.Date()  # hide in small company
    municipality_id = fields.Many2one('res.municipality')
    socio_economic_status = fields.Selection([
        ('UnEmployed', 'UnEmployed'),
        ('Employed', 'Employed')
    ])
    pivotal_programme_id = fields.Many2one('res.pivotal.programme')
    other_pivotal_programme = fields.Char()
    other_country = fields.Char('Foreign Country')
    african_male = fields.Integer()
    african_female = fields.Integer()
    african_disabled = fields.Integer()
    colored_male = fields.Integer('Coloured Male')
    colored_female = fields.Integer('Coloured Female')
    colored_disabled = fields.Integer('Coloured Disabled')
    indian_male = fields.Integer('Indian/Asian Male')
    indian_female = fields.Integer('Indian/Asian Female')
    indian_disabled = fields.Integer('Indian/Asian Disabled')
    white_male = fields.Integer()
    white_female = fields.Integer()
    white_disabled = fields.Integer()
    other_male = fields.Integer("Foreign National Male")
    other_female = fields.Integer("Foreign National Female")
    other_disabled = fields.Integer("Foreign National Disabled")
    age1 = fields.Integer("Age <35", help="Age Group - Less than 35")
    age2 = fields.Integer("Age 35-54", help="Age Group - 35 to 54")
    age3 = fields.Integer("Age 55-64", help="Age Group - 55 to 64")
    age4 = fields.Integer("Age > 64", help="Age Group - Greater than 64")

    total_male = fields.Integer(compute="_compute_totals")
    total_female = fields.Integer(compute="_compute_totals")
    total_disabled = fields.Integer(compute="_compute_totals")
    grand_total_gender = fields.Integer(compute="_compute_totals")
    grand_total_agegroup = fields.Integer(compute="_compute_totals")

    legacy_system_id = fields.Integer(string='Legacy System ID')

    @api.depends('ofo_occupation_id')
    def _compute_ofo_specialization(self):
        for rec in self:
            sub_major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id
            major_group = rec.ofo_occupation_id.unit_group_id.sub_major_group_id.major_group_id
            _logger.info(
                f"SUB MAJOR => {sub_major_group} MAJOR => {major_group}")

            rec.ofo_submajorgroup_id = sub_major_group and sub_major_group.id or False
            rec.ofo_majorgroup_id = major_group and major_group.id or False
            rec.require_ofo_specialization = True if self.env['res.ofo.specialization'].search(
                [('occupation_id', '=', rec.ofo_occupation_id.id)]) else False

    @api.depends(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _compute_totals(self):
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            total_disabled = sum([rec.african_disabled, rec.indian_disabled,
                                 rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            rec.total_male = total_male
            rec.total_female = total_female
            rec.total_disabled = total_disabled
            rec.grand_total_gender = sum([total_male, total_female])
            rec.grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

    @api.constrains(
        'ofo_occupation_id',
        'ofo_specialization_id',
        'programme_level',
        'training_provider',
        'start_date',
        'end_date',
        'municipality_id',
        'socio_economic_status',
        'pivotal_programme_id')
    def _check_duplicate(self):
        '''
            Duplicates records are not accepted on the system - 
            a record is considered a duplicate when the following fields are the same: 
            OFO occupation, 
            OFO specialisation, 
            Programme Level, 
            training provider, 
            Start and end dates, 
            NQF level, 
            municpality, 
            socio economic status 
            and PIVOTAL programme
            if one of the above mentioned field is different then the system must all the record.
        '''
        for rec in self:
            records = self.search([
                ('wspatr_id', '=', self.wspatr_id.id),
                ('ofo_occupation_id', '=', rec.ofo_occupation_id.id),
                ('ofo_specialization_id', '=', rec.ofo_specialization_id.id),
                ('programme_level', '=', rec.programme_level),
                ('training_provider', '=', rec.training_provider),
                ('start_date', '=', rec.start_date),
                ('end_date', '=', rec.end_date),
                ('municipality_id', '=', rec.municipality_id.id),
                ('socio_economic_status', '=', rec.socio_economic_status),
                ('pivotal_programme_id', '=', rec.pivotal_programme_id.id),

            ])
            if len(records) > 1:
                raise ValidationError(f"Duplicate record found for record: Occupation - {rec.ofo_occupation_id.name}\n \
                    Specialization {rec.ofo_specialization_id.name}\n \
                    Programme Level - {rec.programme_level}\n  \
                    Training Provider - {rec.training_provider}\n \
                    Start Date {rec.start_date}\n \
                    End date {rec.end_date} \n \
                    Municipality {rec.municipality_id.name}\n \
                    Socio Economic Status {rec.socio_economic_status}\n \
                    pivotal programme {rec.pivotal_programme_id.name}")

    @api.constrains(
        'african_male',
        'african_female',
        'indian_male',
        'indian_female',
        'colored_male',
        'colored_female',
        'white_male',
        'white_female',
        'other_male',
        'other_female',
        'age1',
        'age2',
        'age3',
        'age4'
    )
    def _check_totals(self):
        '''
        Race, Gender and Age breakdown must balance and the sytem must not count the disability section when balancing. 
        The system must be able to indicate and specify that these fields are not balancing.
        '''
        for rec in self:
            total_male = sum([rec.african_male, rec.indian_male,
                             rec.colored_male, rec.white_male, rec.other_male])
            total_female = sum([rec.african_female, rec.indian_female,
                               rec.colored_female, rec.white_female, rec.other_female])
            #total_disabled = sum([rec.african_disabled, rec.indian_disabled, rec.colored_disabled, rec.white_disabled, rec.other_disabled])
            grand_total_gender = sum([total_male, total_female])
            grand_total_agegroup = sum(
                [rec.age1, rec.age2, rec.age3, rec.age4])

            if grand_total_gender != grand_total_agegroup:
                raise ValidationError(f"The Sum of Race & Gender MUST equal the sum of Age breakdown for record - \
                    Specialization {rec.ofo_specialization_id.name}\n \
                    Programme Level - {rec.programme_level}\n  \
                    Training Provider - {rec.training_provider}\n \
                    Start Date {rec.start_date}\n \
                    End date {rec.end_date} \n \
                    Municipality {rec.municipality_id.name}\n \
                    Socio Economic Status {rec.socio_economic_status}\n \
                    pivotal programme {rec.pivotal_programme_id.name}")

    @api.onchange('other_country')
    def _onchange_other_country(self):
        if self.other_country:
            country_name = self.other_country.replace(" ", "")
            if country_name and len(country_name) > 1:
                record = self.env['res.country'].search(
                    [('name', 'ilike', country_name)])
                if not record:
                    self.other_country = False

                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': _(
                                "Wrong value for Foreign Country '{country}'.\n"
                                "You can copy and paste this URL {base_url}/web#action=&model=res.country&view_type=list&cids=&menu_id= on your browser to get the list of acceptable country names"
                            ).format(
                                country=country_name,
                                base_url=self.env['ir.config_parameter'].sudo(
                                ).get_param('web.base.url')
                            )
                        }
                    }


class InsetaWspAtr(models.Model):
    _name = 'inseta.wspatr'
    _description = "WSP/ATR"

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    @api.model
    def default_get(self, fields_list):
        """Compute list of organisations where the SDF is the primary SDF.
            According to the SPEC only primary SDFs can fill WSP/ATR forms
        """
        res = super(InsetaWspAtr, self).default_get(fields_list)

        user = self.env.user
        # internal users should be able to create WSP for sdf
        if user.id not in self._get_internal_users_ids():
            sdf = self.env['inseta.sdf'].sudo().search(
                [('partner_id', '=', user.partner_id.id)], order="id desc", limit=1)
            # filter organisations where the SDF is the primary SDF
            # sdf_organisations = sdf and sdf.organisation_ids.filtered(lambda r: r.sdf_role in ("primary", "secondary")  and r.state == "approve") or []
            #_logger.info(f"User Roles {user_groups}")
            # user_allowed_organisations = user.allowed_organisation_ids
            # sdf_org_ids =  [o.organisation_id.id for o in sdf_organisations]
            # user_org_ids = [o.id for o in user_allowed_organisations]
            # linked_orgs = [o.childorganisation_id.id for o in user.allowed_organisation_ids.mapped('linkage_ids').filtered(lambda x: x.state=='active')]
            # use set to retrieve unique organisation ids
            # allowed_org_ids = list(set(sdf_org_ids + user_org_ids))
        else:
            #allowed_org_ids = self.env['inseta.organisation'].search([("state","=","approve")])
            sdf = False

        res.update({
            'sdf_id': sdf and sdf.id or False,
            # 'sdf_allowed_organisation_ids': allowed_org_ids
        })
        return res

    # confirm fields
    confirm_variance = fields.Boolean('Confirm Variance report')
    confirm_trained_beneficiaries = fields.Boolean(
        'Confirm Trained Beneficiaries')
    confirm_impl_report = fields.Boolean(
        'Confirm Implementation Report')  # small firms

    confirm_learning_programmes = fields.Boolean('Confirm Learning Programmes')
    confirm_trained_aet = fields.Boolean('Confirm Trained AET')
    confirm_hardtofillvacancies = fields.Boolean(
        'Confirm Hard to fill vacancies')
    confirm_skillsgap = fields.Boolean('Confirm Skills Gaps')
    confirm_pivotaltrained = fields.Boolean(
        'Confirm Pivotal Trained Beneficiaries')
    confirm_skillsdevconsult = fields.Boolean(
        'Confirm Skills Development and Consultation')
    confirm_currentemploymentprofile = fields.Boolean(
        'Confirm current employment profile')
    confirm_highesteduprofile = fields.Boolean(
        'Confirm Highest Educational Profile')
    confirm_provincialbreakdown = fields.Boolean(
        'Confirm Provincial Breakdown')
    confirm_plannedaet = fields.Boolean('Confirm Planned AET')
    confirm_planned_beneficiaries = fields.Boolean(
        'Confirm Planned Beneficiaries')
    confirm_pivotal_planned_beneficiaries = fields.Boolean(
        'Confirm Pivotal Planned Beneficiaries')
    confirm_wpskillplan = fields.Boolean('Confirm Workplace Skills Plan')

    not_hosted_hardtofillvacancies = fields.Boolean(
        'We did not host any Hard to fill vacancies')
    not_hosted_pivotalprogrammes = fields.Boolean(
        'We did not host any PIVOTAL programmes')
    not_hosted_plannedpivotalprogrammes = fields.Boolean(
        'We did not host any PIVOTAL programme')

    # totals
    # total_african_male_trained = fields.Integer()
    # total_colored_male_trained = fields.Integer()
    # total_indian_male_trained = fields.Integer()
    # total_white_male = fields.Integer()
    # total_other_male = fields.Integer()
    # total_african_female = fields.Integer()
    # total_colored_female = fields.Integer('Coloured Female')
    # total_indian_female = fields.Integer()
    # total_white_female = fields.Integer()
    # total_other_female = fields.Integer()
    # total_african_disabled = fields.Integer()
    # total_colored_disabled = fields.Integer('Coloured Disabled')
    # total_indian_disabled = fields.Integer()
    # total_white_disabled = fields.Integer()
    # total_other_disabled = fields.Integer()

    state = fields.Selection([
        ('draft', 'Draft'),  # legacy equiv => Created  - 8
        # legacy equiv =>  Pending 1
        ('pending_validation', 'Pending Validation'),
        ('rework', 'Pending Additional Information'),  # legacy equiv =>  Query 5
        # skill specs asks skill admin to rework
        ('rework_skill_admin', 'Pending Additional Information'),
        # skill mgr asks skill spec to rework
        ('rework_skill_spec', 'Pending Additional Information'),
        ('pending_assessment', 'Pending Assessment'),  # Evaluation In Progress 18
        # Recommended for Approval 17
        ('pending_evaluation', 'Pending Evaluation'),
        ('approve', 'Approved'),  # Accepted = 6
        ('reject', 'Rejected')  # Rejected = 4
    ], default='draft', index=True)

    wpsstatus_id = fields.Many2one(
        'res.wspstatus', 'WSP Status', help="Legacy WSP Status")

    # template = fields.Selection([
    #     ('Current Employment Profile', 'WSP: Current Employment Profile'),
    #     ('Highest Educational Profile', 'WSP: Highest Educational Profile'),
    #     ('Pivotal Planned Beneficiaries', 'WSP: Pivotal Planned Beneficiaries'),
    #     ('Planned Beneficiaries', 'WSP: Planned Beneficiaries'),
    #     ('Planned AET Training', 'WSP: Planned AET Training'),
    #     ('Training planned', 'WSP: Training Planned'),
    # ],
    #     "WSP Template",
    # )
    # template2 = fields.Selection([
    #     ('Trained Beneficiaries Report', 'ATR: Trained Beneficiaries Report'),
    #     ('Pivotal Trained Beneficiaries', 'ATR: Pivotal Trained Beneficiaries'),
    #     ('Trained AET', 'ATR: Trained AET'),
    #     ('Learning Programmes', 'ATR: Learning Programmes'),
    #     ('Implementation Report', 'ATR: Implementation Report'),  # small firms
    # ],
    #     "ATR Template",
    # )

    def get_organisation_domain(self):
        user = self.env.user
        # internal users should be able to create WSP for sdf
        if user.id not in self._get_internal_users_ids():
            sdf = self.env['inseta.sdf'].sudo().search(
                [('partner_id', '=', user.partner_id.id)], order="id desc", limit=1)
            # filter organisations where the SDF is the primary SDF
            sdf_organisations = sdf and sdf.organisation_ids.filtered(
                lambda r: r.sdf_role in ("primary", "secondary") and r.state == "approve") or []
            #_logger.info(f"User Roles {user_groups}")
            user_allowed_organisations = user.allowed_organisation_ids
            sdf_org_ids = [o.organisation_id.id for o in sdf_organisations]
            user_org_ids = [o.id for o in user_allowed_organisations]
            linked_org_ids = [o.childorganisation_id.id for o in user.allowed_organisation_ids.mapped(
                'linkage_ids').filtered(lambda x: x.state == 'active')]

            # use set to retrieve unique organisation ids
            allowed_org_ids = list(
                set(sdf_org_ids + user_org_ids + linked_org_ids))
            return [('id', 'in', allowed_org_ids)]

        return [(1, '=', 1)]

    name = fields.Char(string='Reference Number')
    active = fields.Boolean(default=True)
    report_title = fields.Char(
        compute="_compute_report_title", help="WSP/ATR Report display title")
    wsp_period = fields.Char(
        compute="_compute_report_title", help="eg. 1 January 2021 – 31 December 2021")
    atr_period = fields.Char(compute="_compute_report_title",
                             help="eg. 1 January 2020 to 31 December 2020. ATR is usually for the previous year")
    atr_year = fields.Char(store=False)
    wsp_next_year = fields.Char(compute="_compute_report_title",
                                help="used to indicate  Disbursement year in authorization report")
    wsp_year = fields.Char(compute="_compute_report_title",
                           help="used to indicate wsp year in wsp report", store=True)
    sdf_id = fields.Many2one('inseta.sdf', 'SDF')
    # user_group_id = fields.Many2one('res.groups', 'User Role')
    # user_group_ids = fields.Many2many(
    #     'res.groups',
    #     'inseta_wspatr_usergroups_rel',
    #     'wspatr_id',
    #     'group_id',
    #     string='User Roles',
    #     help="Technical fields uses as domain for filtering user groups"
    # )
    organisation_id = fields.Many2one('inseta.organisation', domain=lambda self: self.get_organisation_domain(
    ), required=True, index=True, tracking=True)
    sic_code_id = fields.Many2one(
        'res.sic.code',
        'SIC Code',
        compute="_compute_sic_code_desc",
        store=True
    )
    sic_code_desc = fields.Char(
        'SIC Code Description',
        compute="_compute_sic_code_desc",
        store=True
    )
    sdf_allowed_organisation_ids = fields.Many2many(
        'inseta.organisation',
        'inseta_wspatr_organisation_rel',
        'wspatr_id',
        'organisation_id',
        string="Primary SDF Organisations",
        help="Technical List of Primary SDF Organisation"
        "used as domain in the organisation_id field"
    )
    sdl_no = fields.Char('SDL No', related="organisation_id.sdl_no")
    no_employees = fields.Integer(related="organisation_id.no_employees")
    organisation_size_id = fields.Many2one(
        'res.organisation.size', string='Size')
    organisation_size_desc = fields.Char(
        related="organisation_id.organisation_size_desc",
        string="Size Desc."
    )
    is_small_firm = fields.Boolean(
        default=False, compute="_compute_is_small_firm", store=True)
    financial_year_id = fields.Many2one(
        'res.financial.year', required=True, tracking=True, index=True)
    wspatr_period_id = fields.Many2one(
        'inseta.wspatr.period', 'WSP Period', tracking=True, index=True)
    start_date = fields.Date()
    due_date = fields.Date()
    form_type = fields.Selection([
        ('Small', 'Small Firms'),
        ('Large', 'Large/Medium')
    ], string="Form Type", index=True)
    submission_type = fields.Selection(
        [('ATR', 'ATR'), ('WSP', 'WSP')], default="WSP")
    submitted_date = fields.Datetime()
    submitted_by = fields.Many2one('res.users')
    # rework_comment = fields.Text()
    rework_date = fields.Date(
        'Rework Date', help="Date Skills Admin Requested the Rework")
    reworked_date = fields.Date('Query submission date', help="Date SDF Reworked the submission")
    reworked_by = fields.Many2one('res.users')

    rework_expiration_date = fields.Date(
        'Rework Expiration Date',
        compute="_compute_rework_expiration",
        store=True
    )


    approved_date = fields.Datetime()
    approved_by = fields.Many2one('res.users')
    rejected_date = fields.Datetime()
    rejected_by = fields.Many2one('res.users')
    # technical fields
    is_wsp_open = fields.Boolean(
        "Is WSP Open?",
        compute="_compute_is_wsp_open",
        store=True,
        help="Indicates if a WSP period is open"
    )
    is_payment_synced = fields.Boolean(
        help="indicated if the WSP Payment for mandatory grant")

    # WSP Evaluation
    evaluation_ids = fields.One2many(
        'inseta.wspatr.evaluation',
        'wspatr_id',
        'Evaluation Status'
    )

    evaluation_count = fields.Integer(compute="_compute_evaluation_count")

    # WSP Uploads
    upload_ids = fields.One2many(
        'inseta.wspatr.documentupload',
        'wspatr_id',
        'Document Uploads'
    )

    is_able_to_modify = fields.Boolean(
        compute="_compute_is_able_to_modify",
        help="Technical Field used to determine "
        "if a field should be required for logged in user"
    )
    is_imported = fields.Boolean()
    legacy_system_id = fields.Integer(string='Legacy System ID')
    # WSP Report fields
    no_employees_emp_profile = fields.Integer(
        'Number of Employees (Employment Profile)',
        compute="_compute_no_employees_emp_profile",
        help="No of employees as computed from the current employment profile"
    )
    no_employees_highest_edu_profile = fields.Integer(
        'Number of Employees (Highest Edu. Profile)',
        compute="_compute_no_employees_highest_edu_profile",
        help="No of employees as computed from the Highest Edu profile"
    )
    # wsp submission fields
    variance_ids = fields.One2many(
        'inseta.wspatr.variancereport',
        'wspatr_id',
        'Variance Report',
    )
    variance_pivotal_ids = fields.One2many(
        'inseta.wspatr.variancereport',
        'wspatr_id',
        'Variance Report For Pivotal Beneficaries',
        domain="[('is_pivotal','=',True)]",

    )
    skillsdevconsultplanning_ids = fields.One2many(
        'inseta.wspatr.skillsdevconsultplanning',
        'wspatr_id',
        'Skills Development & Consultation'
    )

    employement_profile_ids = fields.One2many(
        'inseta.wspatr.employment.profile',
        'wspatr_id',
        'Current Employment Profile',
        tracking=True
    )
    highest_educational_profile_ids = fields.One2many(
        'inseta.wspatr.highest.educational.profile',
        'wspatr_id',
        'Highest Educational Profile',
        tracking=True
    )
    provincialbreakdown_ids = fields.One2many(
        'inseta.wspatr.provincialbreakdown',
        'wspatr_id',
        'Provincial Breakdown',
        tracking=True
    )
    planned_aet_training_ids = fields.One2many(
        'inseta.wspatr.planned.aet.training',
        'wspatr_id',
        'Planned AET Training',
        tracking=True
    )

    pivotal_planned_beneficiaries_ids = fields.One2many(
        'inseta.wspatr.pivotal.planned.beneficiaries',
        'wspatr_id',
        'Pivotal Planned Beneficiaries',
        tracking=True
    )

    planned_beneficiaries_ids = fields.One2many(
        'inseta.wspatr.planned.beneficiaries',
        'wspatr_id',
        'Planned Beneficiaries',
        tracking=True
    )

    workplaceskillsplan_ids = fields.One2many(
        'inseta.wspatr.workplaceskillsplan',
        'wspatr_id',
        'Workplace Skills Plan',
        tracking=True
    )
    # ATR
    trained_beneficiaries_report_ids = fields.One2many(
        'inseta.wspatr.trained.beneficiaries.report',
        'wspatr_id',
        'Trained Beneficiaries Report',
        tracking=True
    )
    trained_aet_ids = fields.One2many(
        'inseta.wspatr.trained.aet',
        'wspatr_id',
        'Trained AET',
        tracking=True
    )
    learning_programmes_ids = fields.One2many(
        'inseta.wspatr.learning.programmes',
        'wspatr_id',
        'Learning Programmes',
        tracking=True
    )
    hardtofillvacancies_ids = fields.One2many(
        'inseta.wspatr.hardtofillvacancies',
        'wspatr_id',
        'Hard To Fill Vacancies',
        tracking=True
    )
    vacanciesskillsgap_ids = fields.One2many(
        'inseta.wspatr.vacanciesskillsgap',
        'wspatr_id',
        'Skill Gap',
    )
    pivotal_trained_beneficiaries_ids = fields.One2many(  # small & large
        'inseta.wspatr.pivotal.trained.beneficiaries',
        'wspatr_id',
        'Pivotal Trained Beneficiaries',
        tracking=True
    )
    # small firms
    implementation_report_ids = fields.One2many(
        'inseta.wspatr.implementation.report',
        'wspatr_id',
        'Implementation Report',
        tracking=True
    )

# --------------------------------------------
# compute Methods
# --------------------------------------------
    @api.depends('evaluation_ids', 'state')
    def _compute_evaluation_count(self):
        for rec in self:
            rec.evaluation_count = len(rec.evaluation_ids)

    @api.depends('financial_year_id')
    def _compute_report_title(self):
        for rec in self:
            rec.report_title = False
            if rec.financial_year_id:
                # ATR YEAR 2020 AND WSP YEAR 2021 TEMPLATES
                start_yr = rec.financial_year_id.date_from.year
                end_yr = rec.financial_year_id.date_to.year
                prev_fy_start_date = date_utils.subtract(
                    rec.financial_year_id.date_from, years=1)
                rec.atr_period = f"1 January {prev_fy_start_date.year} to 31 December {prev_fy_start_date.year}"
                rec.atr_year = prev_fy_start_date.year
                rec.wsp_period = f"1 January {start_yr} – 31 December {start_yr}"
                rec.wsp_year = start_yr
                rec.wsp_next_year = end_yr
                rec.report_title = f"ATR YEAR {start_yr} AND WSP YEAR {end_yr} TEMPLATES"
            else:
                rec.atr_period = False
                rec.atr_year = False
                rec.wsp_period = False
                rec.wsp_year = False
                rec.wsp_next_year = False
                rec.report_title = False

    @api.depends(
        'employement_profile_ids.african_male',
        'employement_profile_ids.african_female',
        'employement_profile_ids.indian_male',
        'employement_profile_ids.indian_female',
        'employement_profile_ids.colored_male',
        'employement_profile_ids.colored_female',
        'employement_profile_ids.white_male',
        'employement_profile_ids.white_female',
        'employement_profile_ids.other_male',
        'employement_profile_ids.other_female',
    )
    def _compute_no_employees_emp_profile(self):
        for rec in self:
            african_male = sum(
                rec.employement_profile_ids.mapped('african_male'))
            african_female = sum(
                rec.employement_profile_ids.mapped('african_female'))
            indian_male = sum(
                rec.employement_profile_ids.mapped('indian_male'))
            indian_female = sum(
                rec.employement_profile_ids.mapped('indian_female'))
            colored_male = sum(
                rec.employement_profile_ids.mapped('colored_male'))
            colored_female = sum(
                rec.employement_profile_ids.mapped('colored_female'))
            white_male = sum(rec.employement_profile_ids.mapped('white_male'))
            white_female = sum(
                rec.employement_profile_ids.mapped('white_female'))
            other_male = sum(rec.employement_profile_ids.mapped('other_male'))
            other_female = sum(
                rec.employement_profile_ids.mapped('other_female'))
            rec.no_employees_emp_profile = sum([
                african_male,
                african_female,
                indian_male,
                indian_female,
                colored_male,
                colored_female,
                white_male,
                white_female,
                other_male,
                other_female
            ])
            _logger.info(
                f"WSP Current emp profile => {rec.no_employees_emp_profile}")

    @api.depends(
        'highest_educational_profile_ids.african_male',
        'highest_educational_profile_ids.african_female',
        'highest_educational_profile_ids.indian_male',
        'highest_educational_profile_ids.indian_female',
        'highest_educational_profile_ids.colored_male',
        'highest_educational_profile_ids.colored_female',
        'highest_educational_profile_ids.white_male',
        'highest_educational_profile_ids.white_female',
        'highest_educational_profile_ids.other_male',
        'highest_educational_profile_ids.other_female',
    )
    def _compute_no_employees_highest_edu_profile(self):
        for rec in self:
            african_male = sum(
                rec.highest_educational_profile_ids.mapped('african_male'))
            african_female = sum(
                rec.highest_educational_profile_ids.mapped('african_female'))
            indian_male = sum(
                rec.highest_educational_profile_ids.mapped('indian_male'))
            indian_female = sum(
                rec.highest_educational_profile_ids.mapped('indian_female'))
            colored_male = sum(
                rec.highest_educational_profile_ids.mapped('colored_male'))
            colored_female = sum(
                rec.highest_educational_profile_ids.mapped('colored_female'))
            white_male = sum(
                rec.highest_educational_profile_ids.mapped('white_male'))
            white_female = sum(
                rec.highest_educational_profile_ids.mapped('white_female'))
            other_male = sum(
                rec.highest_educational_profile_ids.mapped('other_male'))
            other_female = sum(
                rec.highest_educational_profile_ids.mapped('other_female'))
            rec.no_employees_highest_edu_profile = sum([
                african_male,
                african_female,
                indian_male,
                indian_female,
                colored_male,
                colored_female,
                white_male,
                white_female,
                other_male,
                other_female
            ])

    @api.depends('state')
    def _compute_is_able_to_modify(self):
        """
        Compute a field indicating whether the current user
        shouldn't be able to edit some fields.
        SDF should not be able to modify some fields once  WSP its submitted
        """
        grp_primary_sdf = self.env.ref('inseta_skills.group_sdf_user')
        grp_secondary_sdf = self.env.ref('inseta_skills.group_sdf_secondary')

        primary_sdf_users = [user.id for user in grp_primary_sdf.users]
        secondary_sdf_users = [user.id for user in grp_secondary_sdf.users]
        allowed_user_ids = primary_sdf_users + secondary_sdf_users
        for rec in self:
            rec.is_able_to_modify = True if not (
                self._uid in allowed_user_ids and rec.state == 'submit') else False

    @api.depends('organisation_id')
    def _compute_sic_code_desc(self):
        for rec in self:

            if rec.organisation_id and rec.organisation_id.sic_code_id:
                rec.sic_code_id = rec.organisation_id.sic_code_id.id
                rec.sic_code_desc = rec.organisation_id.sic_code_id.name
            else:
                rec.sic_code_desc = False
                rec.sic_code_id = False


    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            if rec.rework_date:
                rec.rework_expiration_date = rec._get_rework_expiration_date()
            else:
                rec.rework_expiration_date = False
                    

    def _get_rework_expiration_date(self):
            
        rework_expiration_date = False
        if self.rework_date:
            no_working_days = 0
            add_days = 10
            while no_working_days < 10:
                if no_working_days > 0:
                    add_days = add_days + (10 - no_working_days)
                rework_expiration_date = self._get_expiry_date(add_days)
                no_working_days = self._get_no_business_days(self.rework_date, rework_expiration_date)
                
        _logger.info(f"business days ====>>> {no_working_days} days to add ==>> {add_days} expiry ==> {rework_expiration_date}")
        return rework_expiration_date
            

    def _get_expiry_date(self, days=10):
        return date_utils.add(self.rework_date, days=days)

    def _get_no_business_days(self, start, end):
            # get list of all days
            all_days = []
            all_days = (start + timedelta(x + 1) for x in range((end - start).days))

            # filter business days
            # weekday from 0 to 4. 0 is monday adn 4 is friday
            # increase counter in each iteration if it is a weekday
            return sum(1 for day in all_days if day.weekday() < 5)

    @api.depends('organisation_id')
    def _compute_is_small_firm(self):
        for rec in self:
            rec.is_small_firm = False
            if rec.organisation_id and rec.organisation_size_desc == "Small":
                rec.is_small_firm = True

    @api.depends('financial_year_id')
    def _compute_is_wsp_open(self):
        for rec in self:
            period = self.env['inseta.wspatr.period'].search(
                [('id', '=', rec.financial_year_id.id)])
            rec.is_wsp_open = False
            today = fields.Date.today()
            if period and today <= period.end_date:
                rec.is_wsp_open = True

# --------------------------------------------
# Onchange and constraints
# --------------------------------------------

    @api.constrains("financial_year_id", "organisation_id")
    def _check_wsp_current_financial_year(self):
        """ 
        Check if organisation has submitted has created a WSP for same financial year.
        Neli (INSETA BA) says organisation should only be able to create a single wsp for a financial year
        """
        for rec in self:
            # Starting date must be prior to the ending date
            domain = [('organisation_id', '=', rec.organisation_id.id),
                      ('financial_year_id', '=', rec.financial_year_id.id)]
            existing_wsp_fy = self.search(domain)
            if len(existing_wsp_fy) > 1:
                raise ValidationError(
                    _(
                        "Organisation '{org}' "
                        "has already created a WSP/ATR for financial year '{fy}'.\n"
                        "To continue, please go back and select the previously created WSP/ATR for the financial year"
                    ).format(
                        fy=rec.financial_year_id.display_name,
                        org=rec.organisation_id.trade_name
                    )
                )

    @api.onchange("no_employees_emp_profile")
    def _onchange_no_employees_emp_profile(self):
        # Number of employees (Employment Profile) must be greyed out and
        # auto populate from the number of employees captured under Current Employment Profile
        # -- Malinga London
        if self.no_employees_emp_profile:
            self.organisation_id.with_context(allow_write=True).write({
                'no_employees': self.no_employees_emp_profile
            })

    @api.onchange('trained_beneficiaries_report_ids')
    def _onchange_trained_beneficiaries_report(self):
        # reset variance
        # get previous year major groups
        # get current year major
        prev_wsp = self._get_previous_year_wsp()
        _logger.info(
            f"Variance Previous Year WSP => {prev_wsp and prev_wsp.name or ''}")

        majorgrps = list(set(prev_wsp.planned_beneficiaries_ids.ofo_majorgroup_id.mapped(
            'name'))) if prev_wsp else []
        _majorgrps = [name.lower() for name in majorgrps] if majorgrps else []
        _logger.info(f"Variance Major Groups  => {_majorgrps}")
        planned_dict = self._prepare_previous_year_planned_beneficiaries_vals()
        trainned_dict = self._prepare_current_year_trainned_beneficiaries_vals()
        _logger.info(
            f"Planned beneficiaries => {planned_dict} Trained Beneficiaries => {trainned_dict }")
        self.variance_ids = False
        # variance_data = [(5,0,0)]
        variance_data = []
        for name in _majorgrps:
            try:
                prev_majorgrp = prev_wsp.planned_beneficiaries_ids.ofo_majorgroup_id.filtered(
                    lambda x: x.name == name.upper())
                majorgrp_id = prev_majorgrp and prev_majorgrp[0].id or False
                # We could have a keyError if major occupation group selected for this year,
                # was not included in the planned beneficiaries for the previous year
                totalplanned = planned_dict[name].get('no_of_learner', 0)
                totaltrained = trainned_dict[name].get('no_of_learner', 0)
                _logger.info(
                    f"actual: {totaltrained} - planned: {totalplanned}")

                #perc = (float(totaltrained) / float(totalplanned)) * 100
                variance = totaltrained - totalplanned
                variance_data.append((
                    0, 0,
                    {
                        'wspatr_id': self._origin.id,
                        'ofo_majorgroup_id': majorgrp_id,
                        'totalplanned': totalplanned,
                        'totaltrained': totaltrained,
                        'variance_perc': variance,
                        # 'variance_perc': var_pec if var_pec <= 100 else 0,
                    }
                ))
            except KeyError as ex:
                _logger.info(f"Variance Computation Error=> {ex}")
                pass

        _logger.info(f"VARIANCE DATA {variance_data}")
        self.write({'variance_ids': variance_data})

    @api.onchange("organisation_id")
    def _onchange_organisation_id(self):
        """Update organisation size"""
        if self.organisation_id:
            # check if user is a primary SDF for the organisation and can submit WSP/ATR
            #organisation_sdf_ids = self.organisation_id.sdf_ids.filtered(lambda x: x.sdf_role == "primary" and x.state == "approve").mapped("sdf_id.id")

            #_logger.info(f"allowed sdf ids for wsp submission {organisation_sdf_ids}")
            # user = self.env.user
            # sdf = self.env['inseta.sdf'].sudo().search([('partner_id','=', user.partner_id.id)], order="id desc", limit=1)
            # if sdf and sdf.id not in organisation_sdf_ids:
            #     #This error can only occur if an organisation is linked to a user from the user profile.
            #     #or the SDF has not been approved
            #     raise ValidationError(_(f'Only Approved Primary SDFs can submit WSP/ATR for an organisation.\n'
            #     'Kindly confirm that the organisation "{self.organisation_id.name}" has an approved primary SDF.'))

            if self.organisation_id.is_childorganisation:
                _logger.info("IS CHILD ORGANISATION")
                raise ValidationError(
                    f"You cannot create WSP for company because it is linked as a child company to {self.organisation_id.parent_company.name}")

            organisation_sdfs = self.organisation_id.sdf_ids.filtered(
                lambda x: x.sdf_role == "primary" and x.state == "approve").mapped("sdf_id")
            if not organisation_sdfs:
                raise ValidationError(
                    "The Selected organisation does not have a primary SDF. Please link a primary SDF and try again.")

            sdf = organisation_sdfs[0]

            org = self.organisation_id
            if not org.state == 'approve':
                self.organisation_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"{org.trade_name} has not been approved"
                    }
                }

            # find linked organisations and auto populate provincial breakdown
            LEVY_STATUS = ('Non-Levy Paying', 'Levy Paying')
            small_levy = self.env.ref('inseta_base.data_orgsize_small_levy')
            small_non_levy = self.env.ref(
                'inseta_base.data_orgsize_small_non_levy')
            medium = self.env.ref('inseta_base.data_orgsize_medium')
            size = False
            if self.organisation_size_id.id == small_levy.id or self.organisation_size_id.id == small_non_levy.id:
                size = "Small"
            elif self.organisation_size_id.id == medium.id:
                size = "Medium"
            else:
                size = "Large"

            breakdown = [
                (0, 0, {
                    'wspatr_id': self._origin.id,
                    'sdl_no': self.organisation_id.sdl_no,
                    'sic_code_id': self.organisation_id.sic_code_id.id,
                    'levy_status': self.organisation_id.levy_status if self.organisation_id.levy_status in LEVY_STATUS else False,
                    'company_size': size,
                    'noemployees': self.organisation_id.no_employees
                })
            ]

            if self.organisation_id.linkage_ids:
                for linked in self.organisation_id.linkage_ids.filtered(lambda x: x.state == 'active'):
                    child_organisation = linked.childorganisation_id
                    if child_organisation.no_employees <= 49:
                        size = "Small"
                    elif child_organisation.no_employees > 49 and child_organisation.no_employees <= 149:
                        size = "Medium"
                    else:
                        size = "Large"

                    breakdown.append((0, 0, {
                        'wspatr_id': self._origin.id,
                        'sdl_no': linked.sdl_no,
                        'sic_code_id': linked.childorganisation_id.sic_code_id.id,
                        'levy_status': linked.childorganisation_id.levy_status if linked.childorganisation_id.levy_status in LEVY_STATUS else False,
                        'company_size': size,
                        'noemployees': linked.childorganisation_id.no_employees
                    }))

            _logger.info(f"Provicial Breakdown => {json.dumps(breakdown)}")

            self.provincialbreakdown_ids = [(5, 0, 0)]
            self.update({
                'organisation_size_id': org.organisation_size_id.id,
                'provincialbreakdown_ids': breakdown,
                "sdf_id": sdf.id
            })

    @api.onchange("organisation_size_id")
    def _onchange_organisation_size_id(self):
        small_levy = self.env.ref('inseta_base.data_orgsize_small_levy')
        small_non_levy = self.env.ref(
            'inseta_base.data_orgsize_small_non_levy')
        if self.organisation_size_id:
            if self.organisation_size_id.id == small_levy.id or self.organisation_size_id.id == small_non_levy.id:
                self.form_type = "Small"
            else:
                self.form_type = "Large"

    @api.onchange('financial_year_id')
    def _onchange_financial_year(self):
        if self.financial_year_id:
            period = self.env['inseta.wspatr.period'].search(
                [('financial_year_id', '=', self.financial_year_id.id)], order="id desc", limit=1)
            fy = self.financial_year_id
            # TODO. Refactor the IF condition when you are done with development
            # if not period and not self.env.user.has_group("base.group_system"):
            if not period:
                self.financial_year_id = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _("The WSP/ATR Period has not been opened "
                                     "for the selected Financial Year '{fy}'. "
                                     "Kindly contact the system administrator"
                                     ).format(
                            fy=fy.name
                        )
                    }
                }
            self.wspatr_period_id = period.id
            self.start_date = period.start_date
            self.due_date = period.end_date

    @api.constrains("wspatr_period_id")
    def _check_wsp_period(self):
        """Check if wsp period has elapsed
        """
        for rec in self:
            # Starting date must be prior to the ending date
            if rec.wspatr_period_id and fields.Date.today() > rec.wspatr_period_id.end_date:
                raise ValidationError(
                    _("The WSP Period has elapsed")
                )
# --------------------------------------------
# ORM Methods Override
# --------------------------------------------

    @api.model
    def create(self, vals):
        res = super(InsetaWspAtr, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code(
            'inseta.wspatr.reference') or '/'
        if 'is_imported' in vals and vals.get('is_imported'):
            yr = fields.Date.from_string(vals.get('create_date')).year
        else:
            yr = fields.Date.today().year
        sequence = seq.replace('YR', str(yr))
        res.write({'name': sequence})
        return res

    def write(self, vals):

        if "variance_ids" in vals and self.form_type == "Large":
            if not (self.confirm_variance or vals.get("confirm_variance")):
                raise ValidationError(
                    _('Please confirm the information provided for Variance Report'))

        if "trained_beneficiaries_report_ids" in vals and self.form_type == "Large":
            if not (self.confirm_trained_beneficiaries or vals.get("confirm_trained_beneficiaries")):
                raise ValidationError(
                    _('Please confirm the information provided for Trained Beneficiaries Report'))

        if "implementation_report_ids" in vals and self.form_type == "Small":
            if not (self.confirm_impl_report or vals.get('confirm_impl_report')):
                raise ValidationError(
                    _('Please confirm the information provided for Implementation Report'))

        if 'learning_programmes_ids' in vals:
            if not (self.confirm_learning_programmes or vals.get('confirm_learning_programmes')):
                raise ValidationError(
                    _('Please confirm the information provided for Learning Programmes'))

        if 'trained_aet_ids' in vals:
            if not (self.confirm_trained_aet or vals.get('confirm_trained_aet')):
                raise ValidationError(
                    _('Please confirm the information provided for Trained AET'))

        if 'hardtofillvacancies_ids' in vals:
            if not (self.confirm_hardtofillvacancies or vals.get('confirm_hardtofillvacancies')):
                raise ValidationError(
                    _('Please confirm the information provided for Hard To Fill Vacancies'))

        if 'vacanciesskillsgap_ids' in vals:
            if not (self.confirm_skillsgap or vals.get('confirm_skillsgap')):
                raise ValidationError(
                    _('Please confirm the information provided for Skills Gaps'))

        if 'pivotal_trained_beneficiaries_ids' in vals:
            if not (self.confirm_pivotaltrained or vals.get('confirm_pivotaltrained')):
                raise ValidationError(
                    _('Please confirm the information provided for PIVOTAL Trained Beneficiaries'))

        # WSP
        if 'skillsdevconsultplanning_ids' in vals:
            if not (self.confirm_skillsdevconsult or vals.get('confirm_skillsdevconsult')):
                raise ValidationError(
                    _('Please Confirm the information provided for Skills Development & Consultation'))

        if 'employement_profile_ids' in vals:
            if not (self.confirm_currentemploymentprofile or vals.get('confirm_currentemploymentprofile')):
                raise ValidationError(
                    _('Please confirm that the information provided for Current Employment Profile'))

        if 'highest_educational_profile_ids' in vals:
            if not (self.confirm_highesteduprofile or vals.get('confirm_highesteduprofile')):
                raise ValidationError(
                    _('Please confirm the information provided for Highest Educational Profile'))

        if 'provincialbreakdown_ids' in vals:
            if not (self.confirm_provincialbreakdown or vals.get('confirm_provincialbreakdown')):
                raise ValidationError(
                    _('Please confirm  the information provided for provincial Breakdown Report'))

        if 'planned_aet_training_ids' in vals:
            if not (self.confirm_plannedaet or vals.get('confirm_plannedaet')):
                raise ValidationError(
                    _('Please confirm the information provided for Planned AET'))

        if 'planned_beneficiaries_ids' in vals:
            if not (self.confirm_planned_beneficiaries or vals.get('confirm_planned_beneficiaries')):
                raise ValidationError(
                    _('Please confirm the information provided for Planned Beneficiaries of Training'))

        if 'workplaceskillsplan_ids' in vals:
            if not (self.confirm_wpskillplan or vals.get('confirm_wpskillplan')):
                raise ValidationError(
                    _('Please confirm the information provided for Planned Beneficiaries of Training'))

        if 'pivotal_planned_beneficiaries_ids' in vals:
            if not (self.confirm_pivotal_planned_beneficiaries or vals.get('confirm_pivotal_planned_beneficiaries')):
                raise ValidationError(
                    _('Please confirm the information provided for PIVOTAL Planned beneficiaries'))

        # if not self._context.get('allow_write'):
        #      if self.state in ('approve','reject'):
        #         raise ValidationError(_('You cannot modify an Approved or Rejected WSP'))
        return super(InsetaWspAtr, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You cannot delete an approved or Rejected WSP'))
        return super(InsetaWspAtr, self).unlink()

    def copy(self):
        res = super(InsetaWspAtr, self).copy()

        ''' Inherited to avoid duplicating records '''
        raise Warning(
            _('Forbidden! You are not allowed to duplicate WSP/ATR, please create the new one.!'))
# --------------------------------------------
# Business Logic
# --------------------------------------------

    def _get_internal_users_ids(self):
        Group = self.env['res.groups']
        skill_specialist_group_id = self.env.ref(
            'inseta_skills.group_skills_specialist').id
        skill_manager_group_id = self.env.ref(
            'inseta_skills.group_skills_manager').id
        skill_admin_group_id = self.env.ref(
            'inseta_skills.group_skills_admin').id
        users = Group.browse(
            [skill_specialist_group_id, skill_manager_group_id, skill_admin_group_id]).users
        return users and users.ids or []

    def get_employer_contact_email(self):
        emails = []
        # since this is a new registration,
        # it means all employers linked to this SDF are new and we will notify all of them
        for sdforg in self.organisation_ids:
            # retrieve contact emails
            if sdforg.organisation_id:
                contact_emails = [str(contact.email)
                                  for contact in sdforg.organisation_id.child_ids]
                employer_emails = [str(c.organisation_id.email)
                                   for c in self.organisation_ids]
                emails = contact_emails or employer_emails
        return ",".join(emails) if emails else ''

    def _get_skills_spec(self):
        grp_skills_spec = self.env.ref(
            'inseta_skills.group_skills_specialist', raise_if_not_found=False)
        return grp_skills_spec and self.env['res.groups'].sudo().browse([grp_skills_spec.id]).users or []

    def get_skills_spec_email(self):
        emails = [str(user.partner_id.email)
                  for user in self._get_skills_spec()]
        return ",".join(emails) if emails else ''

    def _get_skills_admin(self):
        grp = self.env.ref('inseta_skills.group_skills_admin',
                           raise_if_not_found=False)
        return grp and self.env['res.groups'].sudo().browse([grp.id]).users or []

    def get_skills_admin_email(self):
        emails = [str(user.partner_id.email)
                  for user in self._get_skills_admin()]
        return ",".join(emails) if emails else ''

    def get_skills_mgr(self):
        return self.env['res.users'].sudo().search([('is_skills_mgr', '=', True)]) or []

    def get_skill_managers_email(self):
        emails = [str(user.partner_id.email)
                  for user in self.get_skills_mgr()]
        return ",".join(emails) if emails else ''

    def action_update_organisation_details(self):
        view = self.env.ref(
            'inseta_skills.view_organization_address_contact_form')
        view_id = view and view.id or False
        context = dict(self._context or {})

        return {
            'name': 'Update Organisation Contact',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'inseta.organisation',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'res_id': self.organisation_id.id,
            'target': 'new',
            'context': context,
        }

    def action_set_to_draft(self):
        self.with_context({'allow_write': True}).write({"state": "draft"})
        self._update_child_wsp({"state": "draft"})

        wsp_evaluation = self.env['inseta.wspatr.evaluation'].search(
            [('wspatr_id', '=', self.id)], order="id desc", limit=1)
        if wsp_evaluation:
            wsp_evaluation.with_context({'force_delete': True}).unlink()


    def action_submit(self):
        """ SDF submits new OR reworked wsp
        """

        #we will not validate wsp period if SDF is submitting a rework
        if self.state != 'rework':
            if self.wspatr_period_id and fields.Date.today() > self.wspatr_period_id.end_date:

                raise ValidationError(_(
                    "WSP Period '{period}' has closed on '{due}'. Please contact the System Administrator."
                    ).format(
                        period=self.wspatr_period_id.name,
                        due=self.wspatr_period_id.end_date
                    )
                )

        # Check if organisation has submitted a WSP/ATR for current window
        #    pending_assessment
        # pending_validation
        # pending_evaluation
        wsp = self.search([
            ('organisation_id', '=', self.organisation_id.id),
            ('financial_year_id', '=', self.financial_year_id.id),
            ('state', 'in', (
                'approve', 
                'reject', 
                'pending_validation',
                'pending_assessment', 
                'pending_evaluation'))
        ])
        if wsp:
            raise ValidationError(_(
                'WSP for financial year "{fy}" is already '
                'submitted / evaluated for employer {org}!'
            ).format(
                fy=self.financial_year_id.name,
                org=self.organisation_id.name
            )
            )

        # validate organisation details are complete
        if not self.organisation_id.is_confirmed:
            raise ValidationError(_('Please confirm the organisation details'))
        # validate organisation linked organisations
        for child in self.organisation_id.linkage_ids:
            if not child.childorganisation_id.is_confirmed:
                raise ValidationError(
                    _(f'Please confirm the details of the child organisation - {child.childorganisation_id.name}'))

            if not child.childorganisation_id.confirm_contact:
                raise ValidationError(
                    _(f'Please confirm CONTACT details of child organisation - {child.childorganisation_id.name}'))

        error_list = []

        error_dict = {}
        """
            {
                "general":[]
                "form_name": [
                    "line_id": ["error","error"]
                ]
            }
        """
        # ensure employer has minimum of 2 contacts persons
        records = self.organisation_id.mapped('child_ids')
        if len(records) < 2:
            msg = _(
                'A minimum of two contacts are required for WSP Submission\n'
                'Please update organisation "{org} " profile and provide at least 2 contact persons.'
            ).format(
                org=self.organisation_id.name
            )
            error_list.append(msg)

        # WSP Fileds Validation
        if not self.skillsdevconsultplanning_ids:
            msg = _(
                'Please provide "WSP form 1: Skills Development Consultation and Planning."')
            error_list.append(msg)

        if not self.employement_profile_ids:
            msg = _('Please provide "WSP: Current Employment Profile"')
            error_list.append(msg)

        if not self.highest_educational_profile_ids:
            msg = _('Please provide "WSP: Highest Educational Profile"')
            error_list.append(msg)

        if not self.provincialbreakdown_ids:
            msg = _('Please provide "Provincial Breakdown"')
            error_list.append(msg)

        if self.form_type == "Large" and not self.planned_beneficiaries_ids:
            msg = _('Please provide "WSP: Planned Beneficiaries of Training"')
            error_list.append(msg)

        if self.form_type == "Small" and not self.workplaceskillsplan_ids:
            msg = _('Please provide "WSP: Planned Beneficiaries of Training"')
            error_list.append(msg)

        if self.form_type == "Large" and not self.planned_aet_training_ids:
            msg = _('Please provide "WSP: Planned AET"')
            error_list.append(msg)

        if not self.not_hosted_plannedpivotalprogrammes and not self.pivotal_planned_beneficiaries_ids:
            msg = _('Please provide "WSP: Pivotal Planned Beneficiaries"')
            error_list.append(msg)

        # ATR Fields Validation
        if self.form_type == "Large" and not self.trained_beneficiaries_report_ids:
            msg = _('Please provide "ATR Trained Beneficiaries Report"')
            error_list.append(msg)

        if self.form_type == "Large" and not self.trained_aet_ids:
            msg = _('Please provide "ATR: Trained AET" ')
            error_list.append(msg)

        if self.form_type == "Large" and not self.learning_programmes_ids:
            msg = _('Please provide "ATR Learning Programmes"')
            error_list.append(msg)

        # when We did not host any PIVOTAL programmes checkbox is ticked
        # then the SDF is not required to complete any information
        if not self.not_hosted_pivotalprogrammes and not self.pivotal_trained_beneficiaries_ids:
            msg = _('Please provide "ATR: Pivotal Trained Beneficiaries"')
            error_list.append(msg)

        if self.form_type == "Small" and not self.implementation_report_ids:
            msg = _('Please provide "ATR: Implementation Report"')
            error_list.append(msg)

        if self.not_hosted_hardtofillvacancies == False and not self.hardtofillvacancies_ids:
            msg = _('Please provide "ATR: Hard To Fill Vacancies"')
            error_list.append(msg)

        if not self.not_hosted_hardtofillvacancies and not self.vacanciesskillsgap_ids:
            msg = _('Please provide "ATR: Skills Gaps Report"')
            error_list.append(msg)

        # confirm details before submission
        if self.variance_ids and not self.confirm_variance:
            msg = _('Please confirm the information provided for Variance Report')
            error_list.append(msg)

        if self.trained_beneficiaries_report_ids and not self.confirm_trained_beneficiaries:
            msg = _(
                'Please confirm the information provided for Trained Beneficiaries Report')
            error_list.append(msg)

        if self.learning_programmes_ids and not self.confirm_learning_programmes:
            msg = _('Please confirm the information provided for Learning Programmes')
            error_list.append(msg)

        if self.trained_aet_ids and not self.confirm_trained_aet:
            msg = _('Please confirm the information provided for Trained AET')
            error_list.append(msg)

        if self.hardtofillvacancies_ids and not self.confirm_hardtofillvacancies:
            msg = _(
                'Please confirm the information provided for Hard To Fill Vacancies')
            error_list.append(msg)

        if self.vacanciesskillsgap_ids and not self.confirm_skillsgap:
            msg = _('Please confirm the information provided for Skills Gaps')
            error_list.append(msg)

        if self.pivotal_trained_beneficiaries_ids:
            if not self.confirm_pivotaltrained:
                msg = _(
                    'Please confirm the information provided for PIVOTAL Trained Beneficiaries')
                error_list.append(msg)

        # wsp confirm
        if self.skillsdevconsultplanning_ids and not self.confirm_skillsdevconsult:
            msg = _(
                'Please confirm that the information provided for Skills Development & Consultation is correct')
            error_list.append(msg)

        if self.employement_profile_ids and not self.confirm_currentemploymentprofile:
            msg = _(
                'Please confirm that the information provided for Current Employment Profile is correct')
            error_list.append(msg)

        if self.highest_educational_profile_ids and not self.confirm_highesteduprofile:
            msg = _('Please tick the confirm checkBox to validate the information provided for Highest Eduicational Profile is correct')
            error_list.append(msg)

        if self.provincialbreakdown_ids and not self.confirm_provincialbreakdown:
            msg = _(
                'Please tick the confirm checkBox to validate the information provided for provincial Breakdown Report is correct')
            error_list.append(msg)

        if self.planned_aet_training_ids and not self.confirm_plannedaet:
            msg = _(
                'Please tick the confirm checkbox to validate the information provided for Planned AET is correct')
            error_list.append(msg)

        if self.planned_beneficiaries_ids and not self.confirm_planned_beneficiaries:
            msg = _('Please tick the confirm checkbox to validate the information provided for Planned Beneficiaries of Training is correct')
            error_list.append(msg)

        if self.workplaceskillsplan_ids and not self.confirm_wpskillplan:
            msg = _('Please tick the confirm checkbox to validate the information provided for Planned Beneficiaries of Training is correct')
            error_list.append(msg)

        if self.pivotal_planned_beneficiaries_ids and not self.confirm_pivotal_planned_beneficiaries:
            msg = _('Please tick the confirm checkbox to validate the information provided for PIVOTAL Planned beneficiaries is correct')
            error_list.append(msg)

        if self.implementation_report_ids and not self.confirm_impl_report:
            msg = _(
                'Please confirm the information provided for Implementation Report')
            error_list.append(msg)

        if not self.upload_ids.filtered(lambda x: x.documentrelates_id.name == 'Authorisation Page'):
            msg = _('Please upload Authorisation Page')
            error_list.append(msg)

        if not self.upload_ids.filtered(lambda x: x.documentrelates_id.name == 'Banking Details'):
            msg = _('Please Upload Banking Details')
            error_list.append(msg)

        if not self.upload_ids.filtered(lambda x: x.documentrelates_id.name == 'FSP License'):
            msg = _('Please Upload FSP License')
            error_list.append(msg)

        # balance the number of employees that are captured on the
        # Organisation details,
        # Current employent profile,
        # highest education profile and
        # the Provincial breakdown.
        # when the numbers are not balancing then the SDF must not be able to submitt the WSP/ATR
        # should be same as no employees emp profile
        no_employees = self.organisation_id.current_fy_numberof_employees
        total_provincial_beakdown = self._get_no_employees_provincial_breakdown()
        # no_employees_emp_profile = self.no_employees_emp_profile
        no_employees_highest_edu_profile = self.no_employees_highest_edu_profile

        if no_employees != total_provincial_beakdown:
            msg = _(
                "Total sum of employees in all Provinces ( Provincial Breakdown Report) Must equal "
                "Number of Employees (Employment Profile) recorded in Organisation Details for '{org}'\n\n"
                "Number of Employees (Employment Profile) = {no_emp}\n"
                "No of Employees (Provincial Breakdown) = {total_pb}"
            ).format(
                org=self.organisation_id.name,
                no_emp=no_employees,
                total_pb=total_provincial_beakdown
            )
            error_list.append(msg)

        # if no_employees != no_employees_emp_profile:
        #     msg = _(
        #         "Total sum of employees in Current Employment Profile Report Must equal "
        #         "Number of Employees (Employment Profile) recorded in Organisation Details '{org}'\n\n"
        #         "Number of Employees (Current FY) = {no_emp}\n"
        #         "No of Employees (Employment Profile) = {no_emp_profile}"
        #     ).format(
        #         org=self.organisation_id.name,
        #         no_emp = no_employees_curr_fy,
        #         no_emp_profile = no_employees_emp_profile
        #     )
        #     error_list.append(msg)

        if no_employees != no_employees_highest_edu_profile:
            msg = _(
                "Total sum of employees in Highest Educational Profile Report Must equal "
                "Number of Employees (Employment Profile) recorded in Organisation Details for '{org}'\n\n"
                "Number of Employees (Employment Profile) = {no_emp}\n"
                "No of Employees (Highest Edu. Profile) = {no_emp_eduprofile}"
            ).format(
                org=self.organisation_id.name,
                no_emp=no_employees,
                no_emp_eduprofile=no_employees_highest_edu_profile
            )
            error_list.append(msg)

        variance_errors = []
        for variance in self.variance_ids:
            if (variance.ofo_majorgroup_id and (variance.totaltrained < variance.totalplanned)) and not (variance.variancereason_id or variance.variancereason_other):
                msg = _("Please provide reason for Variance")
                variance_errors.append({"line": variance, "error": msg})
        error_dict['variance'] = variance_errors

        impl_report_errors = []
        for rec in self.implementation_report_ids:
            # if others is selected then 'Other NQF Level of Skill Priority' must be required
            if (rec.formspl_id and rec.formspl_id.id == self.env.ref("inseta_base.data_formspl12").id) and not rec.formspl_notes:
                msg = _(
                    "Please provide 'Other NQF Level of Skill Priority'"
                ).format(
                    occ=rec.ofo_occupation_id.name
                )
                # error_list.append(msg)
                impl_report_errors.append({"line": rec, "error": msg})

        error_dict['implementation_report'] = impl_report_errors

        # When records are copied/moved from trained beneficiraies, there could be some missing mandatory fields
        # lets validate them
        pivotal_trained_beneficiaries_errors = []
        for rec in self.pivotal_trained_beneficiaries_ids:
            # if others is selected then 'Other NQF Level of Skill Priority' must be required
            required_fields = []
            if not rec.pivotal_programme_id:
                required_fields.append('Pivotal Programme')
            if not rec.socio_economic_status:
                required_fields.append('Socio Economic Status')
            if not rec.start_date:
                required_fields.append('Start Date')
            if not rec.end_date:
                required_fields.append('End Date')
            if not rec.nqf_level_id:
                required_fields.append('NQF Level')

            if required_fields:
                msg = _(
                    "Please provide the following mandatory fields:\n{fields}"
                ).format(
                    fields="\n".join(required_fields)
                )
                # error_list.append(msg)
                pivotal_trained_beneficiaries_errors.append(
                    {"line": rec, "error": msg})

        _logger.info(f" Pivotal Error {pivotal_trained_beneficiaries_errors}")

        error_dict['pivotal_trained_beneficiaries'] = pivotal_trained_beneficiaries_errors

        # if not self.upload_ids:
        #     msg = _('Please Upload the mandatory documents before submission')
        #     error_list.append(msg)

        numbered_error_list = []
        sn = 1
        if len(error_list):
            for err in error_list:
                numbered_error_list.append(f"{sn}. {err}")
                sn += 1

        if numbered_error_list:

            error_dict["general"] = numbered_error_list
            msg = "\n".join(numbered_error_list)
            view = self.env.ref('inseta_skills.wspatr_error_wizard_view_form')
            view_id = view and view.id or False
            context = dict(self._context or {})

            context.update({
                'default_message': "The system encountered some exceptions while submitting the WSP. "
                "Please click on the link below to download the exception report.",
                'default_error_file': f"""<a href="{self._generate_error_file(error_dict)}" target="_blank">Click to download exception report </a>"""
            })

            # raise ValidationError("Please fix the following issues:\n\n" + msg)
            return {
                'name': 'WSPATR Exception Report',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'inseta.wspatr.error.wizard',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'context': context,
            }

        if self.state == 'draft':
            vals = {
                'state': 'pending_validation',
                'submitted_date': fields.Date.today(),
                'submitted_by': self.env.user.id,
            }
            self.write(vals)
            self._submit_child_wsp()

        else:
            vals = {
                'state': 'pending_validation',
                'reworked_date': fields.Date.today(),
                'reworked_by': self.env.user.id
            }
            self.write(vals)
            self._update_child_wsp(vals)

        # update the state of any existing wsp evluation
        wsp_evaluation = self.env['inseta.wspatr.evaluation'].search(
            [('wspatr_id', '=', self.id)], order="id desc", limit=1)
        if wsp_evaluation:
            wsp_evaluation.with_context(allow_write=True).write({"state": "submitted"})
        self.activity_update()


    def _submit_child_wsp(self, state='pending_validation'):
        # submit wsp for the child organisations
        WspAtr = self
        for link in  self.organisation_id.linkage_ids:
            if link.is_active():
                child = link.childorganisation_id
                child_wsp = WspAtr.search([
                    ('organisation_id','=',child.id),
                    ('financial_year_id','=', self.financial_year_id.id)
                ])
                if not child_wsp:
                    parent_wsp = self
                    WspAtr.create({
                        'state': state,
                        'sdf_id': parent_wsp.sdf_id.id,
                        'organisation_id': child.id,
                        'financial_year_id': parent_wsp.financial_year_id.id,
                        'report_title': parent_wsp.report_title,
                        'atr_year': parent_wsp.atr_year,
                        'wsp_year': parent_wsp.wsp_year,
                        'wspatr_period_id': parent_wsp.wspatr_period_id.id,
                        'sic_code_id': parent_wsp.sic_code_id and parent_wsp.sic_code_id.id or False,
                        'organisation_size_id': child.organisation_size_id and child.organisation_size_id.id or False,
                        'start_date': parent_wsp.start_date,
                        'due_date': parent_wsp.due_date,
                        'form_type': parent_wsp.form_type,
                        'submitted_by': parent_wsp.submitted_by and parent_wsp.submitted_by.id or False,
                        'submitted_date': parent_wsp.submitted_date and parent_wsp.submitted_date or False,
                    })

    def _update_child_wsp(self, vals):
        WspAtr = self.env['inseta.wspatr']
        for link in  self.organisation_id.linkage_ids:
            if link.is_active():
                child = link.childorganisation_id
                child_wsp = WspAtr.search([
                    ('organisation_id','=',child.id),
                    ('financial_year_id','=', self.financial_year_id.id)
                ])
                child_wsp.with_context(allow_write=True).write(vals)


    def rework_submission(self):
        """Skill admin or spec reworks submission.
        This method is called from the wspatr validate wizard

        Args:
            comment (str): Reason for rework
        """
        # Skills manager, reworks WSP to skill skills spec
        if self._context.get('is_evaluation'):
            self.write({'state': 'rework_skill_spec'})
            self._update_child_wsp({'state': 'rework_skill_spec'})

        # Skills specialist, reworks WSP to skill admin
        elif self._context.get('is_assessment'):
            self.write({'state': 'rework_skill_admin'})
            self._update_child_wsp({'state': 'rework_skill_admin'})

        else:  # validation rework to sdf
            vals = {
                'state': 'rework',
                'rework_date': fields.Date.today()
            }
            self.write(vals)
            self._update_child_wsp(vals)

        self.activity_update()

    def recommend_submission(self):
        """Skill admin recommend or not recommend submission.
        When the submission is recommended or not recommended, change the status
        to "pending assessment".
        This method is called from the wspatr validate wizard
        """
        if self._context.get('is_assessment'):  # assesment by skills specialist
            self.write({'state': 'pending_evaluation'})
            self._update_child_wsp({'state': 'pending_evaluation'})
        else:
            self.write({'state': 'pending_assessment'})
            self._update_child_wsp({'state': 'pending_assessment'})

        self.activity_update()



    def reject_submission(self):
        """Skill mgr rejects wsp submission. changes WSP status to "rejected".
        This method is called from the wspatr validate wizard
        """
        _logger.info('Rejecting WSP Submission...')

        self.with_context(allow_write=True).write({'state': 'reject'})
        self._update_child_wsp({'state': 'reject'})

        self.activity_update()

    def approve_submission(self):
        """Skill mgr approves wsp submission. changes WSP status to "approved".
        This method is called from the wspatr validate wizard
        """
        _logger.info('Approving WSP Submission...')

        # copy and link the submission to all child companies
        # parent_wsps = self.organisation_id.wspatr_ids.filtered(lambda x: x.financial_year_id.id == self.financialyearstart_id.id and x.state not in ('draft,'))
        # self.childorganisation_id.write({'wspatr_ids': parent_wsps})

        self.with_context(allow_write=True).write({'state': 'approve'})
        self._update_child_wsp({'state': 'approve'})

        self.activity_update()

    def _get_no_employees_provincial_breakdown(self):
        return sum(
            self.provincialbreakdown_ids.mapped('easterncape') +
            self.provincialbreakdown_ids.mapped('freestate') +
            self.provincialbreakdown_ids.mapped('gauteng') +
            self.provincialbreakdown_ids.mapped('kwazulunatal') +
            self.provincialbreakdown_ids.mapped('limpopo') +
            self.provincialbreakdown_ids.mapped('northwest') +
            self.provincialbreakdown_ids.mapped('northerncape') +
            self.provincialbreakdown_ids.mapped('mpumalanga') +
            self.provincialbreakdown_ids.mapped('westerncape')
        )

    def action_print_approval_letter(self):
        return self.env.ref('inseta_skills.action_wspatr_approval_letter_report').report_action(self)

    def action_print_rejection_letter(self):
        return self.env.ref('inseta_skills.action_wspatr_rejection_letter_report').report_action(self)

    def action_print_report(self):
        return self.env.ref('inseta_skills.action_wspatr_submission_report').with_context(landscape=True).report_action(self)

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(InsetaWspAtr, self)._message_auto_subscribe_followers(
            updated_values, subtype_ids)
        if updated_values.get('user_id'):
            user = self.env['res.users'].browse(
                updated_values['user_id'])
            if user:
                res.append(
                    (user.partner_id.id, subtype_ids, False))
        return res

    def _message_post(self, template):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            self.message_post_with_template(
                template.id, composition_mode='comment',
                model='inseta.wspatr', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template, mail_template_admin = False, False
        # SDF submits WSP, set state  pending_validation and Notify sdf and skill admin
        if self.state == 'pending_validation':
            #Rework submission by SDF
            if self.reworked_by:
                mail_template = self.env.ref('inseta_skills.mail_template_notify_wsp_reworked_sdf', raise_if_not_found=False) #
            else: #new submission by SDF
                mail_template = self.env.ref(
                    'inseta_skills.mail_template_notify_wsp_submit_sdf', raise_if_not_found=False)
                mail_template_admin = self.env.ref(
                    'inseta_skills.mail_template_notify_wsp_submit_skilladmin', raise_if_not_found=False)

        # Specilist request rework, state chnages to rework, notify SDF and SDF Employer
        if self.state == 'rework':
            # delete existing rework activity
            self.activity_unlink(['inseta_skills.mail_act_wspatr_rework'])
            # schedule an activity for rework expiration for  SDF user
            self.activity_schedule(
                'inseta_skills.mail_act_wspatr_rework',
                user_id=self.env.user.id,
                date_deadline=self.rework_expiration_date)
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_rework_sdf2', raise_if_not_found=False)
            # mail_template_admin = self.env.ref('inseta_skills.mail_template_notify_organisation_rework', raise_if_not_found=False)
        # Skill spec queries submission,  SKill admin to rework. state changes to rework_skill_admin
        if self.state == 'rework_skill_admin':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_rework_skilladmin', raise_if_not_found=False)
        # Skill mgr queries submission, SKill spec to rework. state changes to rework_skill_spec
        if self.state == 'rework_skill_spec':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_rework_skillspec', raise_if_not_found=False)

        # Skill admin recommends or not recommends wsp, set state  pending_assessment and Notify skill spec
        if self.state == 'pending_assessment':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_recommend_skillspec', raise_if_not_found=False)
        # Skills specialist recommends or not recommends wsp, set state  pending_evaluation and Notify skills manager
        if self.state == 'pending_evaluation':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_recommend_skillmgr', raise_if_not_found=False)
        # Skills mgr rejects wsp, set state  rejected and Notify SDF
        if self.state == 'reject':
            # auto send rejection letter as email attachment
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_rejection_sdf', raise_if_not_found=False)
        # Skills mgr approves wsp, set state approved and Notify SDF
        if self.state == 'approve':
            # auto send approval letter as email attachment
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_wsp_approval_sdf', raise_if_not_found=False)
        # unlink wsp rework activity if rework is resubmitted
        self.filtered(lambda s: s.state in ('pending_validation', 'pending_assessment', 'pending_approval')
                      ).activity_unlink(['inseta_skills.mail_act_wspatr_rework'])

        self.with_context(allow_write=True)._message_post(
            mail_template)  # notify sdf
        self.with_context(allow_write=True)._message_post(
            mail_template_admin)  # notify employers

    def _validate_ofo_code(self, ofo_occupation_id, ofo_specialization_id):
        ofo_occ = ofo_occupation_id
        ofo_spec = ofo_specialization_id

        ofo_occ_code = ofo_occ and ofo_occ.code or False
        ofo_spec_code = ofo_spec and ofo_spec.code
        if ofo_occ_code and ofo_occ_code != ofo_spec_code:
            raise ValidationError(
                _(
                    "Mixing of Ofo Code is not Allowed\n"
                    "Ofo Occupation Code '{occ_code}' for Occupation {occ}."
                    "must be the same as ofo specilization code '{spec_code}' for specialization {spec} "
                ).format(
                    occ_code=ofo_occ.code,
                    occ=ofo_occ.name,
                    spec_code=ofo_spec.code,
                    spec=ofo_spec.name
                )
            )

    def _get_previous_year_wsp(self):
        prev_wsp = False
        if self.financial_year_id:
            wsp_fy_start_date = self.financial_year_id.date_from
            _logger.info(f"Current FY Start Date => {wsp_fy_start_date}")
            previous_fy_start_date = date_utils.subtract(
                wsp_fy_start_date, years=1)
            _logger.info(f"Previous FY Start Date => {previous_fy_start_date}")

            previous_fy = self.env['res.financial.year'].search([
                ('date_from', '=', previous_fy_start_date)
            ])
            _logger.info(f"Previous FY => {previous_fy.name}")
            if previous_fy:
                prev_wsp = self.search([
                    ('organisation_id', '=', self.organisation_id.id),
                    ('financial_year_id', '=', previous_fy.id),
                    ('state', '=', 'approve')
                ])
                if len(prev_wsp) > 1:
                    raise ValidationError(_(
                        'Employer "{org}" has multiple WSP for the financial year "{fy}".'
                        'Please contact the System Administrator'
                    ).format(
                        fy=self.financial_year_id.name,
                        org=self.organisation_id.name
                    )
                    )
        return prev_wsp

    def _prepare_previous_year_planned_beneficiaries_vals(self):
        """Compute the no of learners for each major group for previous WSP
        Returns:
            [dict]: dictionary containing the major groupds and total no of learners
        """
        training_last_actual_dict = {}
        prev_wsp = self._get_previous_year_wsp()
        # step 1: Get WSP for previous fiscal year
        if prev_wsp:
            for beneficiary in prev_wsp.planned_beneficiaries_ids:
                major_group = beneficiary.ofo_majorgroup_id
                if major_group:
                    no_of_learner = beneficiary.total_male + beneficiary.total_female
                    if training_last_actual_dict.get(major_group.name.lower(), {}):
                        training_last_actual_dict[major_group.name.lower(
                        )]['no_of_learner'] = training_last_actual_dict[major_group.name.lower()]['no_of_learner'] + no_of_learner
                    else:
                        training_last_actual_dict.update(
                            {major_group.name.lower(): {'no_of_learner': no_of_learner}})

        return training_last_actual_dict

    def _prepare_current_year_trainned_beneficiaries_vals(self):
        """Compute the no of learners for each major group for current WSP
        Returns:
            [dict]: dictionary containing the major groupds and total no of learners
        """
        training_actual_dict = {}
        for beneficiary in self.trained_beneficiaries_report_ids:
            major_group = beneficiary.ofo_majorgroup_id
            if major_group:
                no_of_learner = beneficiary.total_male + beneficiary.total_female
                if training_actual_dict.get(major_group.name.lower(), {}):
                    training_actual_dict[major_group.name.lower(
                    )]['no_of_learner'] = training_actual_dict[major_group.name.lower()]['no_of_learner'] + no_of_learner
                else:
                    training_actual_dict.update(
                        {major_group.name.lower(): {'no_of_learner': no_of_learner}})

        return training_actual_dict

    def _get_previous_wsp_no_employees(self):
        """ Returns no of employees for previous year WSP.
            We will compute it from the previous WSP current emp. profile
        This figure is important when generating WSP approval List
        """
        prev_wsp = self._get_previous_year_wsp()
        total = 0
        if prev_wsp:
            age1 = sum(prev_wsp.employement_profile_ids.mapped('age1'))
            age2 = sum(prev_wsp.employement_profile_ids.mapped('age2'))
            age3 = sum(prev_wsp.employement_profile_ids.mapped('age3'))
            age4 = sum(prev_wsp.employement_profile_ids.mapped('age4'))
            total = sum([age1, age2, age3, age4])
        return total


    def _generate_error_file(self, error_mapping):

        wb = Workbook(encoding='utf8')
        col_heading_style = easyxf(
            'font: colour white, height 200; pattern: pattern solid, fore_color dark_blue;')

        if error_mapping.get("general"):
            row = 0
            col = 0
            worksheet0 = wb.add_sheet('General')
            heading = "Error Description"
            worksheet0.write(row, col, heading, col_heading_style)
            worksheet0.col(col).width = 24000

            row = 1
            for error in error_mapping.get("general"):
                worksheet0.write(row, 0, error)
                row += 1

        # variance
        if error_mapping.get("variance"):
            worksheet1 = wb.add_sheet('Variance')
            worksheet1.write(1, 0, _('Major Group'), col_heading_style)
            worksheet1.write(1, 1, _('Planned'), col_heading_style)
            worksheet1.write(1, 2, _('Trained'), col_heading_style)
            worksheet1.write(1, 3, _('Variance'), col_heading_style)
            worksheet1.write(1, 4, _('Variance Reason'), col_heading_style)
            worksheet1.write(1, 5, _('Other Reasons'), col_heading_style)
            worksheet1.write(1, 6, _('Error Description'), col_heading_style)

            row = 2
            #variance_errors.append({"line": variance, "error": msg})
            #[{"line": variance, "error": msg}]
            variance_errors = error_mapping.get("variance")
            for data in error_mapping.get("variance"):
                line = data.get("line")
                worksheet1.write(row, 0, line.ofo_majorgroup_id.name)
                worksheet1.write(row, 1, line.totalplanned)
                worksheet1.write(row, 2, line.totaltrained)
                worksheet1.write(row, 3, line.variance_perc)
                worksheet1.write(row, 4, line.variancereason_id.name)
                worksheet1.write(row, 5, line.variancereason_other)
                worksheet1.write(row, 6, data.get("error"))
                row += 1

        # implementation report
        if error_mapping.get("implementation_report"):

            worksheet2 = wb.add_sheet('Implementation report')
            worksheet2.write(1, 0, _('Major Group'), col_heading_style)
            worksheet2.write(1, 1, _('Sub Major Group'), col_heading_style)
            worksheet2.write(1, 2, _('Occupation'), col_heading_style)
            worksheet2.write(1, 3, _('Specialization'), col_heading_style)
            worksheet2.write(
                1, 4, _('Scarce and Critical Skills Priority'), col_heading_style)
            worksheet2.write(1, 5, _('Intervention'), col_heading_style)
            worksheet2.write(
                1, 6, _('NQF Level of Skill Priority'), col_heading_style)

            worksheet2.write(
                1, 7, _('Other NQF Level of Skill Priority'), col_heading_style)
            worksheet2.write(1, 8, _('Foreign Country'), col_heading_style)
            worksheet2.write(1, 9, _('INSETA Funding'), col_heading_style)
            worksheet2.write(1, 10, _('Other Funding'), col_heading_style)
            worksheet2.write(1, 11, _('Company Funding'), col_heading_style)
            worksheet2.write(1, 12, _('African Male'), col_heading_style)

            worksheet2.write(1, 13, _('African Female'), col_heading_style)
            worksheet2.write(1, 14, _('Afican Disabled'), col_heading_style)
            worksheet2.write(1, 15, _('Colored Male'), col_heading_style)
            worksheet2.write(1, 16, _('Colored Female'), col_heading_style)
            worksheet2.write(1, 17, _('Colored Disabled'), col_heading_style)

            worksheet2.write(1, 18, _('Indian Male'), col_heading_style)
            worksheet2.write(1, 19, _('Indian Female'), col_heading_style)
            worksheet2.write(1, 20, _('Indian Disabled'), col_heading_style)

            worksheet2.write(1, 21, _('White Male'), col_heading_style)
            worksheet2.write(1, 22, _('White Female'), col_heading_style)
            worksheet2.write(1, 23, _('White Disabled'), col_heading_style)

            worksheet2.write(
                1, 24, _('Foreign National Male'), col_heading_style)
            worksheet2.write(
                1, 25, _('Foreign National Female'), col_heading_style)
            worksheet2.write(
                1, 26, _('Foreign National Disabled'), col_heading_style)

            worksheet2.write(1, 27, _('Age Grp 1'), col_heading_style)
            worksheet2.write(1, 28, _('Age Grp 2'), col_heading_style)
            worksheet2.write(1, 29, _('Age Grp 3'), col_heading_style)
            worksheet2.write(1, 30, _('Age Grp 4'), col_heading_style)
            worksheet2.write(1, 31, _('Error Description'), col_heading_style)
            worksheet2.col(31).width = 16000

            row = 2
            #variance_errors.append({"line": variance, "error": msg})
            #[{"line": variance, "error": msg}]
            for data in error_mapping.get("implementation_report"):
                line = data.get("line")
                worksheet2.write(row, 0, line.ofo_majorgroup_id.name)
                worksheet2.write(row, 1, line.ofo_submajorgroup_id.name)
                worksheet2.write(row, 2, line.ofo_occupation_id.name)
                worksheet2.write(row, 3, line.ofo_specialization_id.name)
                worksheet2.write(row, 4, line.formsp_id.name)
                worksheet2.write(row, 5, line.intervention_id.name)
                worksheet2.write(row, 6, line.formspl_id.name)
                worksheet2.write(row, 7, line.formspl_notes)
                worksheet2.write(row, 8, line.other_country or '')
                worksheet2.write(row, 9, line.inseta_funding)
                worksheet2.write(row, 10, line.other_funding)
                worksheet2.write(row, 11, line.company_funding)

                worksheet2.write(row, 12, line.african_male)
                worksheet2.write(row, 13, line.african_female)
                worksheet2.write(row, 14, line.african_disabled)
                worksheet2.write(row, 15, line.colored_male)
                worksheet2.write(row, 16, line.colored_female)
                worksheet2.write(row, 17, line.colored_disabled)

                worksheet2.write(row, 18, line.indian_male)
                worksheet2.write(row, 19, line.indian_female)
                worksheet2.write(row, 20, line.indian_disabled)

                worksheet2.write(row, 21, line.white_male)
                worksheet2.write(row, 22, line.white_female)
                worksheet2.write(row, 23, line.colored_disabled)

                worksheet2.write(row, 24, line.other_male)
                worksheet2.write(row, 25, line.other_female)
                worksheet2.write(row, 26, line.other_disabled)

                worksheet2.write(row, 27, line.age1)
                worksheet2.write(row, 28, line.age2)
                worksheet2.write(row, 29, line.age3)
                worksheet2.write(row, 30, line.age4)
                worksheet2.write(row, 31, data.get("error"))
                row += 1

        # pivotal_trained_beneficiaries
        if error_mapping.get("pivotal_trained_beneficiaries"):
            worksheet3 = wb.add_sheet('Pivotal trained beneficiaries')
            worksheet3.write(1, 0, _('Major Group'), col_heading_style)
            worksheet3.write(1, 1, _('Sub Major Group'), col_heading_style)
            worksheet3.write(1, 2, _('Occupation'), col_heading_style)
            worksheet3.write(1, 3, _('Specialization'), col_heading_style)
            worksheet3.write(1, 4, _('Programme Level'), col_heading_style)
            worksheet3.write(1, 5, _('Training Provider'), col_heading_style)
            worksheet3.write(1, 6, _('Municipality'), col_heading_style)
            worksheet3.write(1, 7, _('Pivotal programme'), col_heading_style)
            worksheet3.write(1, 8, _('Socio economic status'),
                             col_heading_style)
            worksheet3.write(1, 9, _('Start Date'), col_heading_style)
            worksheet3.write(1, 10, _('End Date'), col_heading_style)
            worksheet3.write(1, 11, _('Completion status'), col_heading_style)

            worksheet3.write(1, 12, _('African Male'), col_heading_style)
            worksheet3.write(1, 13, _('African Female'), col_heading_style)
            worksheet3.write(1, 14, _('Afican Disabled'), col_heading_style)
            worksheet3.write(1, 15, _('Colored Male'), col_heading_style)
            worksheet3.write(1, 16, _('Colored Female'), col_heading_style)
            worksheet3.write(1, 17, _('Colored Disabled'), col_heading_style)

            worksheet3.write(1, 18, _('Indian Male'), col_heading_style)
            worksheet3.write(1, 19, _('Indian Female'), col_heading_style)
            worksheet3.write(1, 20, _('Indian Disabled'), col_heading_style)

            worksheet3.write(1, 21, _('White Male'), col_heading_style)
            worksheet3.write(1, 22, _('White Female'), col_heading_style)
            worksheet3.write(1, 23, _('White Disabled'), col_heading_style)

            worksheet3.write(
                1, 24, _('Foreign National Male'), col_heading_style)
            worksheet3.write(
                1, 25, _('Foreign National Female'), col_heading_style)
            worksheet3.write(
                1, 26, _('Foreign National Disabled'), col_heading_style)

            worksheet3.write(1, 27, _('Age Grp 1'), col_heading_style)
            worksheet3.write(1, 28, _('Age Grp 2'), col_heading_style)
            worksheet3.write(1, 29, _('Age Grp 3'), col_heading_style)
            worksheet3.write(1, 30, _('Age Grp 4'), col_heading_style)
            worksheet3.write(1, 31, _('Error Description'), col_heading_style)
            worksheet3.col(31).width = 16000

            row = 2
            #variance_errors.append({"line": variance, "error": msg})
            #[{"line": variance, "error": msg}]
            for data in error_mapping.get("pivotal_trained_beneficiaries"):
                line = data.get("line")
                worksheet3.write(row, 0, line.ofo_majorgroup_id.name)
                worksheet3.write(row, 1, line.ofo_submajorgroup_id.name)
                worksheet3.write(row, 2, line.ofo_occupation_id.name)
                worksheet3.write(row, 3, line.ofo_specialization_id.name)
                worksheet3.write(row, 4, line.programme_level or '')
                worksheet3.write(row, 5, line.training_provider or '')
                worksheet3.write(row, 6, line.municipality_id.name or '')
                worksheet3.write(row, 7, line.pivotal_programme_id.name or '')
                worksheet3.write(row, 8, line.socio_economic_status or '')
                worksheet3.write(row, 9, str(line.start_date) or '')
                worksheet3.write(row, 10, str(line.end_date) or '')
                worksheet3.write(row, 11, line.completion_status or '')

                worksheet3.write(row, 12, line.african_male)
                worksheet3.write(row, 13, line.african_female)
                worksheet3.write(row, 14, line.african_disabled)
                worksheet3.write(row, 15, line.colored_male)
                worksheet3.write(row, 16, line.colored_female)
                worksheet3.write(row, 17, line.colored_disabled)

                worksheet3.write(row, 18, line.indian_male)
                worksheet3.write(row, 19, line.indian_female)
                worksheet3.write(row, 20, line.indian_disabled)

                worksheet3.write(row, 21, line.white_male)
                worksheet3.write(row, 22, line.white_female)
                worksheet3.write(row, 23, line.colored_disabled)

                worksheet3.write(row, 24, line.other_male)
                worksheet3.write(row, 25, line.other_female)
                worksheet3.write(row, 26, line.other_disabled)

                worksheet3.write(row, 27, line.age1)
                worksheet3.write(row, 28, line.age2)
                worksheet3.write(row, 29, line.age3)
                worksheet3.write(row, 30, line.age4)
                worksheet3.write(row, 31, data.get("error"))
                row += 1
        # if isinstance(val, date):
        #     style = date_style

        fp = BytesIO()
        wb.save(fp)
        filename = f"WSPATR_error_log_{self.sdl_no}.xls"
        file_binary = base64.encodebytes(fp.getvalue())
        fp.close()
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_binary,
            'type': 'binary',
            'mimetype': 'application/vnd.ms-excel',
            'res_id': self.id,
            'res_model': 'inseta.wspatr',
            'description': f"WSPATR Error log for employer [{self.sdl_no}] created on {fields.Datetime.now()}"
        })
        return f"/web/content/{attachment.id}/{filename}?download=true"


class InsetaWspAtrOrgnaisationContact(models.Model):
    _name = 'inseta.wspatr.organisationcontact'
    _description = "WSP/ATR Organisation Contact"
    _order = "id desc"

    wspatr_id = fields.Many2one('inseta.wspatr')
    title = fields.Many2one('res.partner.title')
    first_name = fields.Char('Person Name')
    last_name = fields.Char('Person Surname')
    id_no = fields.Char(string="Person ID No")
    person_email = fields.Char('Person Email')
    person_phone = fields.Char('Telephone Number')
    person_mobile = fields.Char('Cell Number')
    legacy_system_id = fields.Integer(string='Legacy System ID')


class InsetaWspAtrDocument(models.Model):
    _name = 'inseta.wspatr.documentupload'
    _description = "WSP/ATR Document Upload"
    _order = "id desc"
    _rec_name = "documentrelates_id"

    wspatr_id = fields.Many2one(
        'inseta.wspatr',
        index=True,
        ondelete='cascade'
    )
    financial_year_id = fields.Many2one('res.financial.year')
    file = fields.Binary(string="Select File", required=True)
    file_name = fields.Char("File Name")
    legacy_filepath = fields.Char()
    documentrelates_id = fields.Many2one(
        'res.wspdocument.relates', 'Document Relates to')
    comment = fields.Text()
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
