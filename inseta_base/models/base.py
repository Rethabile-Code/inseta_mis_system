from odoo import api, fields, models, _

#dbo.lkpbankname.csv
class InsetaBank(models.Model):
	_name = "inseta.bank"
	_description ="Inseta Bank"
	_order="name"
	
	name = fields.Char('Name')
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class AccountType(models.Model):
    _name = "res.accounttype" #dbo.lkpaccounttype.csv
    _description ="Account Type"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
class ResInternshipType(models.Model):
    _name = "res.internshiptype" #dbo.lkpinternshiptype.csv
    _description ="Intership Type"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResFundingType(models.Model):
    _name = "res.fundingtype"
    _description ="Funding Type"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResDisability(models.Model):
    _name = "res.disability"
    _description ="Disability"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResNationality(models.Model):
	_name = "res.nationality"
	_description ="Nationality"
	_order="name"
	
	name = fields.Char('Name')
	saqacode = fields.Char(string='SAQA Code')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResCitizenStatus(models.Model):
	_name = "res.citizen.status"
	_description ="Citizenship Status"

	name = fields.Char('Name')
	saqacode = fields.Char(string='Code')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

# For Locality in South Africa
class res_district(models.Model):
	_name = 'res.district'
	_description ="District"

	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Code')
	country_id = fields.Many2one('res.country')
	province_id = fields.Many2one('res.country.state', string='Province')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class res_municipality(models.Model):
	_name = 'res.municipality'
	_description = "Municipality"
	
	name = fields.Char(string='Name')
	district_id = fields.Many2one('res.district', string='District')
	country_id = fields.Many2one('res.country', string='Country')
	urban_rural = fields.Selection([('Urban','Urban'),('Rural','Rural'),('Unknown','Unknown')], string='Urban/Rural')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class res_city(models.Model):
	_name = 'res.city'
	_description = "City"
	
	name = fields.Char(string='Name')
	district_id = fields.Many2one('res.district', string='District')
	municipality_id = fields.Many2one('res.municipality', string='Municipality')
	country_id = fields.Many2one('res.country', string='Country')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class res_suburb(models.Model):
	_name = 'res.suburb'
	_description = "Suburb"
	
	name = fields.Char(string='Name')
	postal_code = fields.Char(string='Postal Code')
	municipality_id = fields.Many2one('res.municipality', string='Municipality')
	city_id = fields.Many2one('res.city',string='City')
	district_id = fields.Many2one('res.district', string='District')
	province_id = fields.Many2one('res.country.state', string='Province')
	country_id = fields.Many2one('res.country', string='Country') 
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResAlternateIdType(models.Model):
	_name = 'res.alternate.id.type'
	_description= "Alternate ID type"

	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Saqa code')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class resEquity(models.Model):
	_name = 'res.equity'
	_description = "Equity"

	name = fields.Char(string='Name')
	description = fields.Char()
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(string='Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResSchoolEmis(models.Model):
	""" More info about school EMIS can be found here  https://webapps.dhet.gov.za/USUS/SchoolSearch
	"""
	_name = 'res.school.emis'
	_description = "School EMIS"

	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(string='Active', default=True)
	province_id = fields.Many2one('res.country.state', 'Province')
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResSIC(models.Model):
	_name = "res.sic.code"
	_description = "SIC"

	legacy_system_id = fields.Integer(string='Legacy System ID')
	name = fields.Char(string="Name")
	description = fields.Text(string='Description')
	siccode = fields.Char(string='Sic Code')
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(default=True)
	
	def name_get(self):
		arr = []
		for rec in self:
			name = "[{}] {}".format(rec.siccode, rec.name)
			arr.append((rec.id, name))
		return arr



class ResSTATSSAAreaCode(models.Model):
	_name = "res.statssa.area.code"
	_description = "STATSSA Area Code"

	legacy_system_id = fields.Integer(string='Legacy System ID')
	name = fields.Char(string="Name")
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(default=True)
	province_id = fields.Many2one('res.country.state', 'Province')


class ResPopIActStatus(models.Model):
	_name = "res.popi.act.status"
	_description = "Popi Act Status"

	legacy_system_id = fields.Integer(string='Legacy System ID')
	name = fields.Char(string="Name")
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(default=True)

class ResSocioEconomicStatus(models.Model):
	_name="res.socio.economic.status"
	_description = 'Socio Economic Status'
	
	legacy_system_id = fields.Integer(string='Legacy System ID')
	name = fields.Char(string="Name")
	saqacode = fields.Char(string='Saqa Code')
	active = fields.Boolean(default=True)

class ResEmployerType(models.Model):
	_name = "res.employer.type"
	_description = "Employer Type"

	name = fields.Char(string="Employer Type")
	saqacode = fields.Char(string='Saqa code')
	description = fields.Text(string='Description')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)



class ResSubSector(models.Model):
	_name = "res.sub.sector"
	_description = "Sub Sector"
	
	name = fields.Char(string='Name')
	siccode = fields.Char(string='Sic code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)
class ResTypeOrganisation(models.Model):
	_name = "res.type.organisation"
	_description = "Type of Organisation"
	
	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)

class ResOrganisationSize(models.Model):
	_name = "res.organisation.size"
	_description = "Organisation Size"
	
	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)
	

class ResRegistrationNoType(models.Model):
	_name = "res.registration_no_type"
	_description = "Registration number Type"
	
	name = fields.Char(string='Name')
	description = fields.Text(string='Description')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)

class ResLegalStatus(models.Model):
	_name = "res.legal.status"
	_description = "Legal Status"
	
	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)

class ResPartnership(models.Model):
	_name = "res.partnership"
	_description = "Partnership"
	
	name = fields.Char(string='Name')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)

class ResEducationLevel(models.Model):
	_name = "res.education.level"
	_description = "Highest Education Level"

	name = fields.Char(string="Highest Edu. Level")
	description = fields.Text(string='Description')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)

class ResSdfFunction(models.Model):
	_name = "res.sdf.function"
	_description = "SDF Function"

	name = fields.Char(string="SDF Function")
	description = fields.Text(string='Description')
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)


# class ResOfoMajorGroup(models.Model):
# 	_name = "res.ofo.major.group"
# 	_description = "OFO Major Group"

# 	name = fields.Char(string="Major Group")
# 	saqacode = fields.Char(string='Saqa code')
# 	ofoyear = fields.Char()
# 	version_no = fields.Char()
# 	legacy_system_id = fields.Integer(string='Legacy System ID')
# 	active = fields.Boolean(default=True)

# class ResOfoSubMajorGroup(models.Model):
# 	_name = "res.ofo.sub.major.group"
# 	_description = "OFO Sub Major Group"

# 	name = fields.Char(string="Sub Major Group")
# 	major_group_id = fields.Many2one('res.ofo.major.group')
# 	saqacode = fields.Char(string='Saqa code')
# 	legacy_system_id = fields.Integer(string='Legacy System ID')
# 	active = fields.Boolean(default=True)

# class ResOfoUnitGroup(models.Model):
# 	_name = "res.ofo.unit.group"
# 	_description = "OFO Unit Group"

# 	name = fields.Char(string="Unit Group")
# 	sub_major_group_id = fields.Many2one()
# 	saqacode = fields.Char(string='Saqa code')
# 	legacy_system_id = fields.Integer(string='Legacy System ID')
# 	active = fields.Boolean(default=True)

# class ResOfoOccupation(models.Model):
# 	_name = "res.ofo.occupation"
# 	_description = "OFO Occupation"

# 	name = fields.Char(string="Occupation")
# 	unit_group_id = fields.Many2one('res.ofo.unit.group')
# 	saqacode = fields.Char(string='Saqa code')
# 	legacy_system_id = fields.Integer(string='Legacy System ID')
# 	active = fields.Boolean(default=True)


class ResAppointmentProcedure(models.Model):
	_name = "res.sdf.appointment.procedure"
	_description = "SDF appointment procedure"

	name = fields.Char(string="Name")
	saqacode = fields.Char(string='Saqa code')
	legacy_system_id = fields.Integer(string='Legacy System ID')
	active = fields.Boolean(default=True)

class ResSeta(models.Model):
	_name = "res.seta"
	_description = "SETA ID"

	name = fields.Char('Name', required=True)
	description = fields.Text(string='Description')
	saqacode = fields.Char('Saqa Code')
	seta_id = fields.Integer() #SETMIS SETA_Id
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResBeeStatus(models.Model):
	_name = "res.bee.status"
	_description = "Bee Status"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResLevyNumberType(models.Model):
	_name = "res.levy.number.type"
	_description = "Levy Number Type"

	name = fields.Char('Name', required=True)
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResDesignation(models.Model):
	_name = "res.designation"
	_description = "Designation"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResFormSpl(models.Model):
	"""dbo.lkpformspl.csv
		this is mostly a repetition of res.nfqlevel
		specifically for purposes of WSP/ATR Excel import
	"""
	_name = "res.formspl"
	_description = "FormnSpl"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResFormSp(models.Model):
	"""dbo.lkpformsp.csv
		this is mostly for purposes of WSP/ATR Excel import
	"""
	_name = "res.formsp"
	_description = "FormSP: Scarce and Critical Skills Priority"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResFormOccupation(models.Model):
	"""dbo.lkpformoccupation.csv
		this is mostly for purposes of WSP/ATR Excel import
	"""
	_name = "res.formoccupation"
	_description = "Form Occupation"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')


class ResAetLevel(models.Model):
	"""dbo.lkpaetlevel.csv
		this is mostly for purposes of WSP/ATR Excel import
	"""
	_name = "res.aetlevel"
	_description = "AET Level"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')
class ResAetLevel(models.Model):
	"""dbo.lkpaetsubject.csv
		this is mostly for purposes of WSP/ATR Excel import
	"""
	_name = "res.aetsubject"
	_description = "AET Subject"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResFormCred(models.Model):
	"""dbo.lkpformcred.csv
		this is mostly for purposes of WSP/ATR Excel import
	"""
	_name = "res.formcred"
	_description = "Form Cred"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResIntervention(models.Model):
	_name = "res.intervention"
	_description = "Intervention"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResPivotalProgramme(models.Model):
	_name = "res.pivotal.programme"
	_description = "Pivotal Programme"

	name = fields.Char('Name')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

	def name_get(self):
		arr = []
		for rec in self:
			name = f"{rec.saqacode} - {rec.name}"
			arr.append((rec.id, name))
		return arr

class ResGender(models.Model):
	_name = "res.gender"
	_description = "Gender"

	name = fields.Char('Name')
	description = fields.Text(string='Description')
	saqacode = fields.Char('Saqa Code')
	active = fields.Boolean('Active', default=True)
	legacy_system_id = fields.Integer(string='Legacy System ID')

class ResLang(models.Model):
	_inherit = "res.lang"

	saqacode = fields.Char('Saqa Code')
	country_id = fields.Many2one('res.country', 'Country')
	legacy_system_id = fields.Integer()


