from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo.addons.inseta_tools.validators import validate_said
from odoo.addons.inseta_tools.converters import dd2dms

_logger = logging.getLogger(__name__)


class InsetaSDF(models.Model):
    _name = "inseta.sdf"
    _description = "SDF"
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(InsetaSDF, self).default_get(fields_list)
    #     return res

    image_512 = fields.Image("Image 512", max_width=512, max_height=512)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('rework', 'Pending Additional Information'),
        # skill manager asks specilist to rework
        ('rework_skill_spec', 'Pending Additional Information'),
        ('pending_verification', 'Pending Verification'),
        ('queried', 'Queried/Rework'),
        ('pending_approval', 'Pending Approval'),
        # if rework stays more than 10days, skill spec can request for rejection
        ('awaiting_rejection', 'Request Rejection'),
        ('awaiting_rejection2', 'Awaiting Rejection'),
        ('approve', 'Approved'),
        ('reject', 'Rejected')], 
        default='draft', 
        string="Status",
        index=True,
        tracking=True
    )

    reference = fields.Char(string='Reference No.')
    partner_id = fields.Many2one(
        'res.partner', 
        'Related Partner', 
        required=True,
        index=True, 
        ondelete='cascade', 
        help='Partner-related data of the SDF'
    )
    user_id = fields.Many2one('res.users', string='SDF Related User')
    username = fields.Char(string='SDF Username')
    password = fields.Char(string='SDF Password')

    # organisation_user_id = fields.Many2one('res.users', string='Org. Related User')
    # organisation_username = fields.Char(string='Org. Username')
    # organisation_password = fields.Char(string='Org. Password')

    # id_no = fields.Char(string="S.A Identification No")

    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    highest_edu_desc = fields.Text()
    # TODO: Change to Many2one field. dbo.lkpofomajorgroup
    occupational_group_id = fields.Char()
    current_occupation = fields.Char(string='Current Occupation')
    occupation_years = fields.Char(string='Years in Occupation')
    occupation_experience = fields.Char(string='Experience in Occupation')

    has_completed_sdftraining = fields.Boolean('Has completed SDF training?')
    has_requested_sdftraining = fields.Boolean('Has Requested SDF training?')
    accredited_trainingprovider_name = fields.Char(
        'Accredited Training Provider')
    is_interested_in_communication = fields.Boolean(
        'Is Interested in Communication?')
    general_comments = fields.Text()

    reregistration_state = fields.Selection(
        [('approve', 'Approved'), ('decline', 'Declined')], 'Reregistration State')
    reregistration_date = fields.Date()
    registration_date = fields.Date(
        'Registration Date', default=lambda self: fields.Date.today(), readonly=True)
    current_occupation = fields.Char(string='Current Occupation')
    occupation_experience = fields.Text(string='Experience')
    sdf_certificate = fields.Binary(string="Upload SDF Certificate")
    file_name = fields.Char()
    code_of_conduct = fields.Binary(string="Code of Conduct")
    file_name2 = fields.Char()

    # SDF organisation
    organisation_ids = fields.One2many(
        'inseta.sdf.organisation', 'sdf_id', string='SDF Organisation')

    child_organisations_html = fields.Html(compute="_compute_child_organisations_html")
    # Added new fields
    legacy_system_id = fields.Integer(string='Legacy System ID')
    # used to avoid auto generating reference sequence
    is_imported = fields.Boolean(string="Is Imported")
    is_confirmed = fields.Boolean()
    is_initial_update = fields.Boolean(
        help="Is set to True the first time the"
        "model is updated to trigger SDF registration Mail automated action"
    )

    # workflow fields
    approved_by = fields.Many2one('res.users')
    approval_date = fields.Date('Approval Date', readonly=True)
    rework_date = fields.Date(
        'Rework Date', help="Date Skills Specialist Requested the Rework")
    reworked_date = fields.Date(
        'Reworked Date', help="Date SDF Sumbitted the Rework")
    rework_expiration_date = fields.Date(
        'Rework Expiration Date', compute="_compute_rework_expiration", store=True)
    rework_comment = fields.Text()
    rejected_by = fields.Many2one('res.users')
    rejection_comment = fields.Text()
    rejection_date = fields.Date(
        'Rejection Date', help="Date Skills Manger Rejects SDF registraion")


# --------------------------------------------
# compute Methods
# --------------------------------------------

    @api.depends('organisation_ids.organisation_id.linkage_ids')
    def _compute_child_organisations_html(self):
        for rec in self:
            body = ""
            not_found_child_org = True
            if self.organisation_ids:
                #first, check if there is any sdf organisation that has child
                if not self.organisation_ids.organisation_id.mapped('linkage_ids'):
                        body = "<div class='alert alert-info' role='alert'>No child organisations found </div>"
                else:
                    for sdf_org in self.organisation_ids:
                        if sdf_org.organisation_id.linkage_ids:
                            body += f"""
                                <thead>
                                    <tr class="bg-primary">
                                        <th>Parent Organisation: {sdf_org.organisation_id.trade_name} - {sdf_org.organisation_id.sdl_no} </th>
                                    </tr>
                                </thead>
                            """
                            for link in sdf_org.organisation_id.linkage_ids:
                                body += f"""
                                    <tbody>
                                        <tr>
                                            <td> <a href="/web#id={link.childorganisation_id.id}&model=inseta.organisation&view_type=form&cids=1&menu_id={self._context.get('menu_id','')}">{link.childorganisation_id.sdl_no} -
                                            {link.childorganisation_id.trade_name} </a></td>
                                        </tr>
                                    </tbody>
                                """
            rec.child_organisations_html = body


    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            rec.rework_expiration_date = False
            if rec.rework_date:
                rec.rework_expiration_date = date_utils.add(
                    rec.rework_date, days=10)

    @api.depends(
        'first_name',
        'last_name',
        'middle_name')
    def _compute_name(self):
        for rec in self:
            rec.name = "{} {} {}".format(
                rec.first_name or '', rec.middle_name or '', rec.last_name or '')
# --------------------------------------------
# Onchange methods and overrides
# --------------------------------------------

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
            # update date of birth with identity
            self.update({"birth_date": identity.get('dob'),
                        "gender_id": 1 if identity.get("gender") == 'male' else 2})

    @api.onchange('physical_code')
    def _onchange_physical_code(self):
        if self.physical_code:
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.physical_code)], limit=1)
            if sub:
                self.physical_suburb_id = sub.id
                self.physical_municipality_id = sub.municipality_id.id
                self.physical_province_id = sub.district_id.province_id.id
                self.physical_city_id = sub.city_id.id
                #self.nationality_id = sub.nationality_id.id
                self.physical_urban_rural = sub.municipality_id.urban_rural

    @api.onchange('postal_code')
    def _onchange_postal_code(self):
        if self.postal_code:
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.postal_code)], limit=1)
            post_code = self.postal_code
            if not sub:
                self.postal_code = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _("Suburb with Postal Code {postcode} not found!").format(postcode=post_code)
                    }
                }
            self.postal_suburb_id = sub.id
            self.postal_municipality_id = sub.municipality_id.id
            self.postal_province_id = sub.district_id.province_id.id
            self.postal_city_id = sub.city_id.id
            #self.nationality_id = sub.nationality_id.id
            self.postal_urban_rural = sub.municipality_id.urban_rural

    @api.onchange('use_physical_for_postal_addr')
    def _onchange_use_physical_for_postal_addr(self):
        if self.use_physical_for_postal_addr:
            self.postal_municipality_id = self.physical_municipality_id.id
            self.postal_suburb_id = self.physical_suburb_id.id
            self.postal_province_id = self.physical_province_id.id
            self.postal_city_id = self.physical_city_id.id
            self.postal_urban_rural = self.physical_urban_rural
            self.postal_address1 = self.street,
            self.postal_address2 = self.street2
            self.postal_address3 = self.street3
            self.postal_code = self.physical_code
        else:
            self.postal_municipality_id = False
            self.postal_suburb_id = False
            self.postal_province_id = False
            self.postal_city_id = False
            self.postal_urban_rural = False
            self.postal_address1 = False
            self.postal_address2 = False
            self.postal_address3 = False
            self.postal_code = False

# --------------------------------------------
# ORM Methods override
# --------------------------------------------
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.sdf.register')
        if not vals.get('is_imported'):
            vals['reference'] = sequence or '/'
        name = '{} {} {}'.format(vals.get('first_name'), vals.get(
            'middle_name'), vals.get('last_name'))
        vals['name'] = name
        return super(InsetaSDF, self).create(vals)

    # def write(self, vals):
    #     return super(InsetaSDF, self).write(vals)

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.reference or '', rec.name and rec.name.title() or '')
            arr.append((rec.id, name))
        return arr

    def unlink(self):
        for rec in self:
            if rec.state in ('approve', 'reject'):
                raise ValidationError(
                    _('You can not delete an approved or rejected SDF'))
        return super(InsetaSDF, self).unlink()

# --------------------------------------------
# Business Logic
# --------------------------------------------
    def action_set_to_draft(self):
        self.state = 'draft'

    def action_submit(self):
        self.write({'state': 'pending_verification'})
        # lets notify employer from the inseta_sdf_organisation model
        # since we need each employer details in the email
        mail_template = self.env.ref(
            'inseta_skills.mail_template_notify_sdf_employer', raise_if_not_found=False)
        for sdforg in self.organisation_ids:
            sdforg._message_post(mail_template)

        self.activity_update()

    def rework_registration(self, comment):
        """Skill specialist query Registration and ask SDF to rework.
        This method is called from the rework wizard

        Args:
            comment (str): Reason for rework
        """
        # if Skills Manager, reworks a registration, worklow to sdf specialist
        if self.env.user.has_group("inseta_skills.group_skills_manager") and self.state == "pending_approval":
            self.write({
                'state': 'rework_skill_spec',
                'rework_comment': comment,
            })
        else:
            self.write({
                'state': 'rework',
                'rework_comment': comment,
                'rework_date': fields.Date.today()
            })
        self.activity_update()

    def reject_registration(self, comment):
        """Skill manger rejects SDF registration.
        This method is called from the reject wizard

        Args:
            comment (str): Reason for rejection
        """
        self.write({
            'state': 'reject',
            'rejected_by': self.env.user.id,
            'rejection_comment': comment,
            'rejection_date': fields.Date.today()
        })
        # email will be sent to the SDF along with the Rejection letter
        self.organisation_ids.reject_submission(comment)
        self.activity_update()

    def action_request_manager_rejection(self):
        """Skill specialist submits to Skill manager for rejection
        if SDF does not rework after 10 days
        """
        self.write({'state': 'awaiting_rejection2'})

    def action_sdf_submit_rework(self):  # rework

        self.write({
            'state': 'pending_verification',
            'reworked_date': fields.date.today()}
        )
        self.activity_update()

    def action_verify(self):
        """Skill specialist Verifies SDF registration
        """
        self.write({'state': 'pending_approval'})
        self.activity_update()

    def action_manager_approve(self):
        """Manager approves an SDF registration record, the actual SDF record is created in inseta.sdf model
        we will use the already generated user_id.partner_id
        as this will ensure SDF delegation inheritance will not create a new partner record
        """

        # Update SDF organisation_ids after approval
        self.write({
        "state": 'approve',
        'approval_date': fields.Date.today(),
        'approved_by': self.env.user.id,
        })
        # Approve SDF organisation . Approval Email with approval letter will be sent to the SDF 
        if not self.organisation_ids.filtered(lambda s: s.sdf_role == 'primary' and s.state == 'approve' and s.sdf_id.id == self.id ):

            self.organisation_ids.approve_submission()
        # update mail activity
        self.activity_update()

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
        return self.env['res.users'].sudo().search([('is_skills_mgr','=',True)]) or []

    def get_skills_mgr_email(self):
        emails = [str(user.partner_id.email)
                  for user in self.get_skills_mgr()]
        return ",".join(emails) if emails else ''

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(InsetaSDF, self)._message_auto_subscribe_followers(
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
                model='inseta.sdf', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        MAIL_TEMPLATE, MAIL_TEMPLATE_EMPLOYER, MAIL_TEMPLATE3 = False, False, False
        # Specilist request rework, state chnages to rework, notify SDF and SDF Employer
        if self.state == 'rework':
            # schedule an activity for rework expiration for  SDF user
            self.activity_schedule(
                'inseta_skills.mail_act_sdf_rework',
                user_id=self.user_id.id or self.env.user.id,
                date_deadline=self.rework_expiration_date)
            MAIL_TEMPLATE = self.env.ref(
                'inseta_skills.mail_template_notify_sdf_rework', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref(
                'inseta_skills.mail_template_notify_organisation_rework', raise_if_not_found=False)
        # 1. SDF does initial submission of application, change status to pending verification
        if self.state == 'pending_verification' and not self.reworked_date:
            MAIL_TEMPLATE = self.env.ref(
                'inseta_skills.mail_template_notify_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE3 = self.env.ref(
                'inseta_skills.mail_template_notify_skills_specialist', raise_if_not_found=False)

        # 2. SDF reworks and resubmits, state chnanges to pending_verification. Notify skill specialist
        if self.state == 'pending_verification' and self.reworked_date == fields.date.today():
            MAIL_TEMPLATE = self.env.ref(
                'inseta_skills.mail_template_notify_skills_spec_after_rework', raise_if_not_found=False)

        # Skill Specilist verifies registration, state changes to pending_approval. notify skill mgr and SDF Employer
        if self.state == 'pending_approval':
            MAIL_TEMPLATE = self.env.ref(
                'inseta_skills.mail_template_notify_manager_after_verify_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref(
                'inseta_skills.mail_template_notify_organisation_after_verify_sdf', raise_if_not_found=False)
        # Skill Manager queries registration, and asks SKill specialist to rework. state changes to rework_skill_spec
        if self.state == 'rework_skill_spec':
            MAIL_TEMPLATE = self.env.ref(
                'inseta_skills.mail_template_notify_skills_spec_after_mgr_rework_sdf', raise_if_not_found=False)
        # Skill Manager Rejects registration, state changes to reject. notify SDF and SDF Employer
        if self.state == 'reject':
            #MAIL_TEMPLATE =  self.env.ref('inseta_skills.mail_template_notify_rejection_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref(
                'inseta_skills.mail_template_notify_organisation_after_rejection_sdf', raise_if_not_found=False)
        # Skill Manager Approves registration, state changes to approve. notify SDF and SDF Employer
        if self.state == 'approve':
            #MAIL_TEMPLATE =  self.env.ref('inseta_skills.mail_template_notify_approval_sdf', raise_if_not_found=False)
            MAIL_TEMPLATE_EMPLOYER = self.env.ref(
                'inseta_skills.mail_template_notify_organisation_approval_sdf', raise_if_not_found=False)

        # unlink sdf rework activity if rework is resubmitted
        self.filtered(lambda s: s.state in ('pending_verification', 'pending_approval')
                      ).activity_unlink(['inseta_skills.mail_act_sdf_rework'])

        self.with_context(allow_write=True)._message_post(
            MAIL_TEMPLATE)  # notify sdf
        self.with_context(allow_write=True)._message_post(
            MAIL_TEMPLATE_EMPLOYER)  # notify employers
        self.with_context(allow_write=True)._message_post(
            MAIL_TEMPLATE3)  # notify employers

    def action_work_addr_map(self):
        street = f"{self.street or ''} {self.street2 or ''} {self.street3 or ''}"
        city = self.physical_city_id
        state = self.state_id
        country = self.country_id
        zip = self.physical_code
        self.open_map(street, city, state, country, zip)

    def action_postal_addr_map(self):
        street = f"{self.postal_address1 or ''} {self.postal_address2 or ''} {self.postal_address3 or ''}"
        city = self.postal_city_id
        state = self.state_id
        country = self.country_id
        zip = self.postal_code
        self.open_map(street, city, state, country, zip)

    def open_map(self, street, city, state, country, zip):
        url = "http://maps.google.com/maps?oi=map&q="
        if street:
            url += street.replace(' ', '+')
        if city:
            url += '+'+city.name.replace(' ', '+')
        if state:
            url += '+'+state.name.replace(' ', '+')
        if country:
            url += '+'+country.name.replace(' ', '+')
        if zip:
            url += '+'+zip.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    def get_geolocation(self):
        # We need country names in English below
        for rec in self.with_context(lang='en_US'):
            result = self.env['res.partner']._geo_localize(
                rec.street,
                rec.physical_code,
                rec.physical_city_id.name,
                rec.physical_province_id.name,
                rec.country_id.name
            )

            if result:
                cordinates = dd2dms(result[0], result[1])
                if cordinates:
                    _logger.info(
                        f"{cordinates[0]} {cordinates[1]} {cordinates[2]} {cordinates[3]} {cordinates[4]} {cordinates[5]}")
                    rec.write({
                        'latitude_degree': cordinates[0],
                        'latitude_minutes': cordinates[1],
                        'latitude_seconds': cordinates[2],
                        'longitude_degree': cordinates[3],
                        'longitude_minutes': cordinates[4],
                        'longitude_seconds': cordinates[5],
                    })
        return True


class SDFOrganisation(models.Model):
    _name = "inseta.sdf.organisation"
    _description = "SDF Organisation Linking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"
    _rec_name = "reference"

    # @api.model
    # def default_get(self, fields):
    #     res = super(SDFOrganisation, self).default_get(fields)

    #     return res


    reference = fields.Char()
    active = fields.Boolean(default=True)
    state = fields.Selection([  # sdfstatusid
        ('draft', 'Draft'),  # pending
        ('rework', 'Pending Additional Information'),
        ('rework_skill_spec', 'Pending Additional Information'),
        ('submit', 'Pending Recommendation'),
        ('pending_approval', 'Pending Approval'),
        ('approve', 'Approved'),  # approved
        ('reject', 'Rejected'),  # rejected
        ('deactivate', 'Deactivated')
    ],
        default="draft",
        index=True
    )

    sdf_role = fields.Selection([
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('contract', 'Contract')],
        index=True,
        string="SDF Role"
    )
    sdf_id = fields.Many2one('inseta.sdf',         
        index=True, 
        ondelete='cascade', 
    )

    sdl_no = fields.Char(index=True)
    organisation_id = fields.Many2one(
        'inseta.organisation', 
        domain="[('state','=','approve')]",
        index=True, 
        ondelete='cascade'
    )
    appointment_letter = fields.Binary("Appointment Letter")
    file_name = fields.Char()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    # note recently started using in legacy
    sdf_function_id = fields.Many2one(
        'res.sdf.function', 'Will you perform your SDF functions in respect of')
    appointment_procedure_id = fields.Many2one(
        'res.sdf.appointment.procedure', 'Please indicate method of appointment to SDF position')  # note recently started using in legacy
    require_appointment_procedure_other = fields.Boolean(
        compute="_compute_require_appointment_procedure_other")
    # note recently started using in legacy
    appointment_procedure_other = fields.Char('Other appointment method')
    is_acting_for_employer = fields.Boolean('Are you acting for Employer?')
    # TODO Clarify this Field #note not in use in legacy
    is_replacing_primary_sdf = fields.Boolean(
        'Are you replacing the previous primary SDF of this Company?')
    # TODO Clarify this Field  #note not in use in legacy
    is_secondary_sdf = fields.Boolean(
        'Are you regestering as secondary SDF for this Company?')
    wsp_open = fields.Char()
    financial_year_id = fields.Many2one('res.financial.year')
    require_registration_date = fields.Boolean(
        compute="_compute_require_registration_date",
        help="Trchnical field used When approving, the skill spec, "
        "admin or mgr must provide reg date. SDF is not required to"
    )
    registration_start_date = fields.Datetime()
    registration_end_date = fields.Datetime()
    application_date = fields.Date(default=fields.Date.today())

    # workflow fields
    recommendation_status = fields.Selection([
        ('Recommended', 'Recommended'),
        ('Not Recommended', 'Not Recommended'),
    ],
        help="Recommendation status"
    )
    recommendation_comment = fields.Text()
    approval_date = fields.Datetime()
    approved_by = fields.Many2one('res.users')
    rework_by = fields.Many2one('res.users', 'User who requested rework')
    rework_date = fields.Date(
        'Rework Date', help="Date Skills Specialist Requested the Rework")
    reworked_date = fields.Date(
        'Reworked Date', help="Date SDF Sumbitted the Rework")
    rework_expiration_date = fields.Date(
        'Rework Expiration Date', compute="_compute_rework_expiration", store=True)
    rework_comment = fields.Text()
    rework_comment_mgr = fields.Text()
    rejected_by = fields.Many2one('res.users')
    rejection_comment = fields.Text()
    rejection_date = fields.Date(
        'Rejection Date', help="Date Skills Manger Rejects SDF registraion")

    is_existing_sdf = fields.Boolean(default=True,
                                     help="Technical field used to determine if an sdf is an existing SDF. "
                                     "When linking existing sdf to organisation, its used to decide if a refence should be generated"
                                     )
    is_sdf = fields.Boolean(help="while  linking organisations, SDF Should not see a dropdown list of companies. "
                            "We will use this compute field  to identify an SDF so that we can allow him search for companies "
                            "via a char field instead of a many2one"
                            )
    legacy_system_id = fields.Integer()


# --------------------------------------------
# compute Methods
# --------------------------------------------

    @api.depends('state')
    def _compute_is_sdf(self):
        """
            while  linking organisations, SDF Should not see a dropdown list of companies. We will use this
            compute field  to identify an SDF so that we can allow him search for companies
            via a char field instead of a many2one
        """
        user = self.env.user
        for rec in self:
            rec.is_sdf = True if (user.has_group("inseta_skills.group_sdf_user") or user.has_group(
                "inseta_skills.group_sdf_secondary")) else False

    @api.depends('rework_date')
    def _compute_rework_expiration(self):
        """Compute rework_expiration_date. 
            According to INSETA SLA, rework expires 10 days following request
        """
        for rec in self:
            rec.rework_expiration_date = False
            if rec.rework_date:
                rec.rework_expiration_date = date_utils.add(
                    rec.rework_date, days=10)

    @api.depends("sdf_id")
    def _compute_require_registration_date(self):
        for rec in self:
            # inseta_skills.group_skills_specialist,inseta_skills.group_skills_admin,inseta_skills.group_skills_manager
            if self.organisation_id and (self.env.user.has_group("inseta_skills.group_skills_specialist") or \
                    self.env.user.has_group("inseta_skills.group_skills_admin") or \
                    self.env.user.has_group("inseta_skills.group_skills_manager")):
                rec.require_registration_date = True
            else:
                rec.require_registration_date = False

    @api.depends('appointment_procedure_id')
    def _compute_require_appointment_procedure_other(self):
        for rec in self:
            other = self.env.ref("inseta_base.data_sdf_appt_procedure_others")
            if rec.appointment_procedure_id.id == other.id:
                rec.require_appointment_procedure_other = True
            else:
                rec.require_appointment_procedure_other = False

    # @api.onchange("sdf_role")
    # def _onchange_sdf_role(self):
    #     if self.sdf_role:
    #         if self.sdf_role == 'primary' and self.organisation_id.sdf_ids.filtered(lambda s: s.sdf_role == 'primary' and s.state == 'approve'):
    #             self.sdf_role = False
    #             return {
    #                 'warning': {
    #                     'title': "Validation Error",
    #                     'message': _(
    #                         "'{org}' already has a Primary SDF"
    #                     ).format(
    #                         org=self.organisation_id.legal_name,
    #                     )
    #                 }
    #             }

    @api.onchange('organisation_id')
    def _onchange_organisation_id(self):
        # if self.organisation_id:
        active_id = self._context.get('default_sdf_id')
        self.sdf_id = active_id

    @api.onchange('organisation_id', 'registration_start_date')
    def _onchange_organisation_registration(self):
        if self.organisation_id and self.registration_start_date:
            records = self.search([
                ('organisation_id', '=', self.organisation_id.id),
                ('sdf_id', '=', self.sdf_id.id),
                ('registration_start_date', '=', self.registration_start_date)
            ])
            org = self.organisation_id
            start_dt = self.registration_start_date
            _logger.info(f"linked records {records}")
            if len(records):
                self.registration_start_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _(
                            "'{org}' has already been registered to the SDF for the selected registration date '{dt}'"
                        ).format(
                            org=org.legal_name,
                            dt=start_dt
                        )
                    }
                }

# --------------------------------------------
# ORM Methods override
# --------------------------------------------

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('inseta.sdf.register')
        if vals.get('is_existing_sdf') == True:
            vals['reference'] = sequence or '/'
        else:
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'inseta.sdf.register')
        return super(SDFOrganisation, self).create(vals)

    def unlink(self):
        if self.state in ('approve', 'reject'):
            raise ValidationError(
                _('You cannot delete an approved or Rejected Record'))
        return super(SDFOrganisation, self).unlink()

# --------------------------------------------
# Business logic and action methods
# --------------------------------------------

    def action_search_organisation(self):
        if self.sdl_no:
            org = self.env['inseta.organisation'].search(
                [('sdl_no', '=', self.sdl_no)], limit=1)
            sdlno = self.sdl_no
            if not org:
                self.sdl_no = False
                raise ValidationError(_(
                    "Organisation with SDL NO '{sdlno}' is not found"
                ).format(
                    sdlno=sdlno,
                ))

            if org and org.state not in ('approve',):
                self.sdl_no = False
                raise ValidationError(_(
                    " Organisation with SDL NO '{sdlno}' is not yet approved. Kindly contact INSETA"
                ).format(
                    sdlno=sdlno,
                ))
            self.organisation_id = org.id

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_submit(self):
        
        self.write({'state': 'submit'})
        self.activity_update()

    def rework_submission(self, comment):
        """Skill admin/mgr reworks registration.
        This method is called from the sdf recommend wizard

        Args:
            comment (str): Reason for rework
        """
        # Skills manager, reworks WSP to skill skills spec
        for rec in self:
            if rec._context.get('is_approval'):
                rec.write({
                    'state': 'rework_skill_spec',
                    'rework_comment_mgr': comment,
                    'rework_date': fields.Date.today(),
                    'rework_by': self.env.user.id,
                })
            else:  # skill spec rework to sdf/skill admin
                rec.write({
                    'state': 'rework',
                    'rework_comment': comment,
                    'rework_date': fields.Date.today(),
                    'rework_by': self.env.user.id,
                })
            rec.activity_update()

    def recommend_submission(self, comment, status):
        """Skill spec recommend or not recommend registration.
        When the submission is recommended or not recommended, change the status
        to "pending approval".
        This method is called from the sdf recommendation wizard

        Args:
            comment (str): Reason for recommending or not recommending for approval
        """

        for rec in self:
            rec.write({
                'state': 'pending_approval',
                'recommendation_status': status,
                'recommendation_comment': comment,
            })
            rec.activity_update()

    def reject_submission(self, comment):
        """Skill mgr rejects wsp submission. changes WSP status to "rejected".
        This method is called from the wspatr validate wizard

        Args:
            comment (str): Reason for rejection
        """
        _logger.info('Rejecting SDF Application Submission...')
        for rec in self:
            rec.with_context(allow_write=True).write({
                'state': 'reject',
                'rejection_comment': comment,
                'rejection_date': fields.Date.today(),
                'rejected_by': self.env.user.id,
            })
            rec.activity_update()

    def approve_submission(self, comment=False):
        """Skill mgr approves application. changes status to "approved".
        This method is called from the sdf recommend wizard

        Args:
            comment (str): Reason for approval
        """
        _logger.info('Approving SDF Application...')

        for rec in self:

            if rec.sdf_role == 'primary' and rec.organisation_id.sdf_ids.filtered(lambda s: s.sdf_role == 'primary' and s.state == 'approve'):
                raise ValidationError(_(
                    "'{org}' already has a Primary SDF. Please terminate the current SDF and try again"
                ).format(
                    org=rec.organisation_id.legal_name,
                ))

            rec.with_context(allow_write=True).write({
                'state': 'approve',
                'approval_date': fields.Date.today(),
                'approved_by': self.env.user.id,
            })
            # add current organisation to list of organisations SDF will have access to
            rec.sdf_id.user_id.sudo().write(
                {'allowed_organisation_ids': [(4, rec.organisation_id.id)]})
            rec.activity_update()

    def action_deactivate(self):
        """Deactivate SDF Application.
            This action is called from Automated action and can also be invoked by Sysadmin
        """
        # unlink the organisation
        self.sdf_id.user_id.sudo().write(
            {'allowed_organisation_ids': [(3, self.organisation_id.id)]})
        self.write({'state': 'deactivate'})
        self.message_post(
            body=f"SDF Deactivated for the organisation {self.organisation_id.name}")

    def extend_registration(self, start_date, end_date):
        """Internal Users can extend registration.
        This method is called from the sdf extend registration wizard

        Args:
            start date (date): Registration start date
            end date (date): Registration end date
        """
        _logger.info('Extensing SDF Registration...')
        #    registration_start_date = fields.Datetime()
        #registration_end_date = fields.Datetime()
        self.with_context(allow_write=True).write({
            'registration_start_date': start_date,
            'registration_end_date': end_date,
            # 'state': 'approve',
            'state': 'pending_approval',
            'recommendation_status': 'Recommended',
            'recommendation_comment': '',
        })
        self.message_post(
            body=f"SDF Registration extension approval request. Start Date - {start_date}, End Date - {end_date}")
        self.activity_update()

        #recommend_submission(self.comment, status="Recommended")
        # self.sdf_id.user_id.sudo().write(
        #     {'allowed_organisation_ids': [(4, self.organisation_id.id)]})
        # self.message_post(
        #     body=f"SDF Registration extended. Start Date - {start_date}, End Date - {end_date}")

    def action_print_approval_letter(self):
        return self.env.ref('inseta_skills.action_sdf_approval_letter_report').report_action(self)

    def action_print_rejection_letter(self):
        return self.env.ref('inseta_skills.action_sdf_rejection_letter_report').report_action(self)

    def export_appointment_letter(self):
        if self.appointment_letter:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model=inseta.sdf.organisation&id={}&field=appointment_letter&filename_field=file_name&download=true'.format(self.id),
                'target': 'self',
            }
            # return {
            #     'type' : 'ir.actions.act_url',
            #     'url':   '/web/binary/saveas?model=ir.attachment&field=datas&filename_field=self.file_name&id=%s' % ( self.excel_file.id ),
            #     'target': 'self',
            # }

# --------------------------------------------
# Mail Thread
# --------------------------------------------

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(SDFOrganisation, self)._message_auto_subscribe_followers(
            updated_values, subtype_ids)
        if updated_values.get('user_id'):
            user = self.env['res.users'].browse(
                updated_values['user_id'])
            if user:
                res.append(
                    (user.partner_id.id, subtype_ids, False))
        return res

    def _message_post(self, template, comment=False):
        """Wrapper method for message_post_with_template

        Args:
            template (str): email template
        """
        if template:
            self.message_post_with_template(
                template.id, composition_mode='comment',
                model='inseta.sdf.organisation', res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def activity_update(self):
        """Updates the chatter and send neccessary email to followers or respective groups
        """
        mail_template, mail_template_employer, mail_template3, comment = False, False, False, False
        if self.state == 'submit' and not self.reworked_date:
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_skills_spec_existing_sdf', raise_if_not_found=False)
            mail_template3 = self.env.ref(
                'inseta_skills.mail_template_notify_existing_sdf', raise_if_not_found=False)
            mail_template_employer = self.env.ref(
                'inseta_skills.mail_template_notify_sdf_employer', raise_if_not_found=False)

        # rework submission
        if self.state == 'submit' and self.reworked_date == fields.Date.today():
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_skills_spec_after_rework_existingsdf', raise_if_not_found=False)

        # Specilist request rework, state chnages to rework, notify SDF and/or skill admin
        if self.state == 'rework':
            # schedule an activity for rework expiration for  SDF user
            self.activity_schedule(
                'inseta_skills.mail_act_sdf_rework',
                user_id=self.sdf_id.user_id.id or self.env.user.id,
                date_deadline=self.rework_expiration_date)
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_sdf_rework_existingsdf', raise_if_not_found=False)

        # Skill Spec. recommends registration, state changes to pending_approval. notify skill mgr
        if self.state == 'pending_approval':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_manager_after_verify_existing_sdf', raise_if_not_found=False)

        # Skill Manager queries registration, and asks SKill specialist to rework. state changes to rework_skill_spec
        if self.state == 'rework_skill_spec':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_skills_spec_after_mgr_rework_existingsdf', raise_if_not_found=False)
        # Skill Manager Rejects registration, state changes to reject. notify SDF and SDF Employer
        if self.state == 'reject':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_rejection_existingsdf', raise_if_not_found=False)
        # Skill Manager Approves registration, state changes to approve. notify SDF and SDF Employer
        if self.state == 'approve':
            mail_template = self.env.ref(
                'inseta_skills.mail_template_notify_approval_existingsdf', raise_if_not_found=False)

        # unlink sdf rework activity if rework is resubmitted
        self.filtered(lambda s: s.state in ('submit', 'pending_approval')
                      ).activity_unlink(['inseta_skills.mail_act_sdf_rework'])

        self.with_context(allow_write=True)._message_post(
            mail_template, comment)  # notify sdf
        self.with_context(allow_write=True)._message_post(
            mail_template_employer, comment)  # notify employers
        self.with_context(allow_write=True)._message_post(
            mail_template3)  # notify sdf
