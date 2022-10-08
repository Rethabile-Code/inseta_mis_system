from odoo.addons.inseta_tools.validators import (
    validate_said, 
    validate_phone,
    validate_mobile,
    validate_passportno,
    validate_name,
    validate_email
)
from odoo import fields, api, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(ResPartner, self).default_get(fields_list)

        inverted = self._get_inverse_name(
            self._get_whitespace_cleaned_name(result.get("name", "")),
            result.get("is_company", False),
        )

        for field in list(inverted.keys()):
            if field in fields_list:
                result[field] = inverted.get(field)
        return result


    type = fields.Selection(selection_add=[
            ('CEO','CEO'), 
            ('CFO', 'CFO'), 
        ],
        ondelete={'consignor': 'set null'}
    )
    employer_sdl_no = fields.Char()
    first_name = fields.Char(string='First Name', tracking=True)
    last_name = fields.Char(string='Last Name', tracking=True)
    middle_name = fields.Char(string='Middle Name')
    initials = fields.Char(string='Initials', tracking=True)
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True,
        readonly=False,
    )
    legacy_system_id = fields.Integer()
    contact_type = fields.Selection([
        ('provider', 'Provider'), 
        ('employer', 'Employer'),
        ('moderator', 'Moderator'),
        ('assessor', 'Assessor'),
        ('sdf', 'Facilitator'),
        ('learner', 'Learner'),
        ('others', 'Others')], default="others")

    code = fields.Char('Code')
    birth_date = fields.Date(string='Birth Date')
    gender_id = fields.Many2one('res.gender', 'Gender')
    equity_id = fields.Many2one('res.equity', 'Equity')
    disability_id = fields.Many2one('res.disability', string="Disability Status")
    home_language_id = fields.Many2one('res.lang', string='Home Language',)
    nationality_id = fields.Many2one('res.nationality', string='Nationality')
    alternateid_type_id = fields.Many2one('res.alternate.id.type', string='Alternate ID TYPE')
    alternate_id_proof = fields.Binary(string="Alternate ID Type Proof")
    file_name3 = fields.Char("Alternate ID Filename", size=30)
    passport_no = fields.Char(string='Passport ID')
    id_no = fields.Char(string="R.S.A.Identification No", index=True)
    citizen_resident_status_id = fields.Many2one('res.citizen.status', string='Citizen Status')
    socio_economic_status_id = fields.Many2one('res.socio.economic.status', string='Socio Economic Status')
    fax_number = fields.Char(string='Fax Number')
    school_emis_id = fields.Many2one('res.school.emis', 'School EMIS')
    school_year = fields.Char()
    statssa_area_code_id = fields.Many2one('res.statssa.area.code')
    popi_act_status_id = fields.Many2one('res.popi.act.status', 'POPI Act Status')
    popi_act_status_date = fields.Date()
    sic_code = fields.Many2one('res.sic.code', string='SIC CODE') # MUST EXIST IN THE SYSTEM
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref("base.za").id)
    street3 = fields.Char(string='Physical Address Line 3',tracking=True)
    physical_code = fields.Char('Physical Code',tracking=True)
    physical_suburb_id = fields.Many2one('res.suburb',string='Physical Suburb',tracking=True)
    physical_city_id = fields.Many2one('res.city', string='Physical City',tracking=True)
    physical_municipality_id = fields.Many2one(
        'res.municipality', string='Physical Municipality',tracking=True)
    physical_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')], string='Physical Urban/Rural',tracking=True)
    physical_province_id = fields.Many2one(
        'res.country.state', string='Physical Province', domain=[('code', '=', 'ZA')],tracking=True)

    use_physical_for_postal_addr = fields.Boolean(string= "Use physical address for postal address?",tracking=True)
    postal_code = fields.Char(string='Postal Code')
    postal_address1 = fields.Char(string='Postal Address Line 1',tracking=True)
    postal_address2 = fields.Char(string='Postal Address Line 2',tracking=True)
    postal_address3 = fields.Char(string='Postal Address Line 3',tracking=True)
    postal_suburb_id = fields.Many2one('res.suburb',string='Postal Suburb',tracking=True)
    postal_city_id = fields.Many2one('res.city', string='Postal City', tracking=True)
    postal_municipality_id = fields.Many2one(
        'res.municipality', 
        'Postal Municipality',
        tracking=True
    )
    postal_urban_rural = fields.Selection(
        [('Urban', 'Urban'), ('Rural', 'Rural'), ('Unknown', 'Unknown')],
        string='Postal Urban/Rural',
        tracking=True
    )
    postal_province_id = fields.Many2one(
        'res.country.state', 
        'Postal Province', 
        domain=[('country_id.code', '=', 'ZA')],
        tracking=True
    )

    child_ids = fields.One2many('res.partner', 'parent_id', 
        'Contact Person', 
        domain=[('active', '=', True),('type','=','contact')],
        tracking=True
    )  # force "active_test" domain to bypass _search() override

    ceo_ids = fields.One2many(
		'res.partner', 
		'parent_id', 
		string='CEO', 
		domain=[('active','=',True),('type','=','CEO')],
        tracking=True
	)

    cfo_ids = fields.One2many(
		'res.partner', 
		'parent_id', 
		string='CFO', 
		domain=[('active','=',True),('type','=','CFO')],
        tracking=True
	)
    # confirm = fields.Boolean('I hereby confirm that the following information submitted is complete, accurate and not missleading')
    gps_coordinates = fields.Char()
    latitude_degree = fields.Char(string='Latitude Degree', size=3, tracking=True)
    latitude_minutes = fields.Char(string='Latitude Minutes', size=2, tracking=True)
    latitude_seconds = fields.Char(string='Latitude Seconds', size=6, tracking=True)
    
    longitude_degree = fields.Char(string='Longitude Degree', size=3, tracking=True)
    longitude_minutes = fields.Char(string='Longitude Minutes',size=2, tracking=True)
    longitude_seconds = fields.Char(string='Longitude Seconds', size=6, tracking=True)

    #WARNING: Legacy system Fields , DO NOT DELETE!
    # DHET address Lines - Legacy system fields 
    dhet_gps_coordinates = fields.Char('DHET Gps Coordinates')
    dhet_physical_code = fields.Char(string='DHET Physical Code')
    dhet_physical_address1 = fields.Char(string='DHET Physical Address Line 1')
    dhet_physical_address2 = fields.Char(string='DHET Physical Address Line 2')
    dhet_physical_address3 = fields.Char(string='DHET Physical Address Line 3')
    dhet_physical_suburb_id = fields.Many2one('res.suburb',string='DHET Physical Suburb')
    dhet_physical_city_id = fields.Many2one('res.city', string='DHET Physical City',)
    dhet_physical_municipality_id = fields.Many2one('res.municipality', string='DHET Physical Municipality')
    dhet_physical_urban_rural = fields.Selection(
        [
            ('Urban', 'Urban'), 
            ('Rural', 'Rural'), 
            ('Unknown', 'Unknown')
        ], 
        string='DHET Physical Urban/Rural'
    )
    dhet_physical_province_id = fields.Many2one(
        'res.country.state', 
        string='DHET Physical Province', 
        domain=[('country_id.code', '=', 'ZA')]
    )
    dhet_postal_code = fields.Char(string='DHET Postal Code')
    dhet_postal_address1 = fields.Char(string='DHET Postal Address Line 1')
    dhet_postal_address2 = fields.Char(string='DHET Postal Address Line 2')
    dhet_postal_address3 = fields.Char(string='DHET Postal Address Line 3')
    dhet_postal_suburb_id = fields.Many2one('res.suburb',string='DHET Postal Suburb')
    dhet_postal_city_id = fields.Many2one('res.city', string='DHET Postal City',)
    dhet_postal_municipality_id = fields.Many2one('res.municipality', string='DHET Postal Municipality')
    dhet_postal_urban_rural = fields.Selection(
        [
            ('Urban', 'Urban'), 
            ('Rural', 'Rural'), 
            ('Unknown', 'Unknown')
        ], 
        string='DHET Postal Urban/Rural'
    )
    dhet_postal_province_id = fields.Many2one(
        'res.country.state', 
        string='DHET Postal Province', 
        domain=[('country_id.code', '=', 'ZA')]
    )
    
    @api.depends("first_name", "last_name")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        for record in self:
            record.name = record._get_computed_name(record.last_name, record.first_name)

    @api.onchange('first_name')
    def _onchange_first_name(self):
        if self.first_name:
            self.initials = self.first_name[:1]

    @api.onchange('email')
    def _onchange_email(self):
        email = self.email
        if email and not validate_email(email):
            self.email = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': f"Provided email '{email}' is invalid "
                }
            }

    @api.onchange('phone')
    def _onchange_phone(self):
        phone = self.phone
        if phone and len(phone) > 10:
            self.phone = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': f"Provided phone '{phone}' should not exceed 10 digits "
                }
            }

    @api.onchange('mobile')
    def _onchange_mobile(self):
        mobile = self.mobile
        if mobile and len(mobile) > 10:
            self.mobile = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': f"Provided mobile '{mobile}' should not exceed 10 digits "
                }
            }

    @api.onchange('passport_no')
    def _onchange_passportno(self):
        passportno = self.passport_no
        if passportno and not validate_passportno(passportno):
            self.passport_no = False
            return {
                'warning': {
                    'title': "Validation Error!",
                    'message': f"Provided passport no '{passportno}' is invalid "
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
            post_code = self.postal_code
            sub = self.env['res.suburb'].search(
                [('postal_code', '=', self.postal_code)], limit=1)
            if not sub:
                self.postal_code = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': _("Suburb with Postal Code {postcode} not found!").format(postcode=post_code)
                    }
                } 
            if sub:
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
            self.postal_address1 = self.street
            self.postal_address2 = self.street2
            self.postal_address3 = self.street3
        else:
            self.postal_municipality_id = False
            self.postal_suburb_id = False
            self.postal_province_id = False
            self.postal_city_id = False
            self.postal_urban_rural = False
            self.postal_address1 = False
            self.postal_address2 = False
            self.postal_address3 = False


    @api.model
    def create(self, vals):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))
        if name is not None:
            # Calculate the splitted fields
            inverted = self._get_inverse_name(
                self._get_whitespace_cleaned_name(name),
                vals.get("is_company", self.default_get(["is_company"])["is_company"]),
            )
            for key, value in inverted.items():
                if not vals.get(key) or context.get("copy"):
                    vals[key] = value

            # Remove the combined fields
            if "name" in vals:
                pass #del vals["name"]
            if "default_name" in context:
                del context["default_name"]
        
        return super(ResPartner, self.with_context(context)).create(vals)
    
    def copy(self, default=None):
        """Ensure partners are copied right.
         Odoo adds ``(copy)`` to the end of :attr:`~.name`, but that would get
         ignored in :meth:`~.create` because it also copies explicitly firstname
         and lastname fields.
		"""
        return super(ResPartner, self.with_context(copy=True)).copy(default)


    @api.model
    def _names_order_default(self):
        return "first_last"


    @api.model
    def _get_names_order(self):
        """Get names order configuration from system parameters.
        You can override this method to read configuration from language,
        country, company or other"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_names_order", self._names_order_default())
        )

    @api.model
    def _get_computed_name(self, last_name, first_name):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        order = self._get_names_order()
        if order == "last_first_comma":
            return ", ".join(p for p in (last_name, first_name) if p)
        elif order == "first_last":
            return " ".join(p for p in (first_name, last_name) if p)
        else:
            return " ".join(p for p in (last_name, first_name) if p)


    def _inverse_name_after_cleaning_whitespace(self):
        """Clean whitespace in :attr:`~.name` and split it.
        The splitting logic is stored separately in :meth:`~._inverse_name`, so
        submodules can extend that method and get whitespace cleaning for free.
        """
        for record in self:
            # Remove unneeded whitespace
            clean = record._get_whitespace_cleaned_name(record.name)
            record.name = clean
            record._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name, comma=False):
        """Remove redundant whitespace from :param:`name`.
        Removes leading, trailing and duplicated whitespace.
        """
        if isinstance(name, bytes):
            # With users coming from LDAP, name can be a byte encoded string.
            # This happens with FreeIPA for instance.
            name = name.decode("utf-8")

        try:
            name = " ".join(name.split()) if name else name
        except UnicodeDecodeError:
            # with users coming from LDAP, name can be a str encoded as utf-8
            # this happens with ActiveDirectory for instance, and in that case
            # we get a UnicodeDecodeError during the automatic ASCII -> Unicode
            # conversion that Python does for us.
            # In that case we need to manually decode the string to get a
            # proper unicode string.
            name = " ".join(name.decode("utf-8").split()) if name else name

        if comma:
            name = name.replace(" ,", ",")
            name = name.replace(", ", ",")
        return name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        """Compute the inverted name.
        - If the partner is a company, save it in the lastname.
        - Otherwise, make a guess.
        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes
        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """
        # Company name goes to the lastname
        if is_company or not name:
            parts = [name or False, False]
        # Guess name splitting
        else:
            order = self._get_names_order()
            # Remove redundant spaces
            name = self._get_whitespace_cleaned_name(
                name, comma=(order == "last_first_comma")
            )
            parts = name.split("," if order == "last_first_comma" else " ", 1)
            if len(parts) > 1:
                if order == "first_last":
                    parts = [" ".join(parts[1:]), parts[0]]
                else:
                    parts = [parts[0], " ".join(parts[1:])]
            else:
                while len(parts) < 2:
                    parts.append(False)
        return {"last_name": parts[0], "first_name": parts[1]}


    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        for record in self:
            parts = record._get_inverse_name(record.name, record.is_company)
            record.last_name = parts["last_name"]
            record.first_name = parts["first_name"]


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    branch_name = fields.Char(string='Branch Name')
    branch_code = fields.Char(string='Branch Code')
    verification_status = fields.Selection([
        ('Verified','Verified'),
        ('Not Verified', 'Not Verified')
    ], default="Not Verified")
    

    @api.onchange('bank_id')
    def _onchange_bank_id(self):
        if self.bank_id:
            self.bank_name = self.bank_id.name

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.acc_holder_name = self.partner_id.name


    @api.model
    def create(self, vals):
        account_number = vals.get('acc_number',False)
        if account_number:
            ## Getting existing bank account numbers    
            acc_numbers = [partner_bank.acc_number for partner_bank in self.search([])]
            if account_number in acc_numbers :
                raise Warning(_('Account number already exists !'))
            ## TO DO : Parent and child employer should share the same account number. Need to add enhancement in the future for the same.
        res = super(ResPartnerBank, self).create(vals)
        return res

class ResPartnerTitle(models.Model):
    _inherit = "res.partner.title"
    saqacode = fields.Char()
    legacy_system_id = fields.Integer()


