
from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError


class InsetaQualification(models.Model):
    _name = 'inseta.qualification'
    _description = "Inseta qualification"
    _order= "id desc" 

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.saqa_id, rec.name.title())
            arr.append((rec.id, name))
        return arr

    name = fields.Char('SAQA Qualification Name')
    unit_standard_id = fields.Many2one('inseta.unit.standard', 'Unit standard', domain=lambda act: [('active', '=', True)])
    # qualification_unit_standard_ids = fields.Many2many("inseta.qualification.unit.standard", 'inseta_qualification_unit_standards_rel', 'inseta_qualification_unit_standards_id', string='Qualification Unit standards')
    qualification_unit_standard_ids = fields.One2many("inseta.qualification.unit.standard", 'qualification_id', string='Qualification Unit standards')
    unit_standard_ids = fields.Many2many("inseta.unit.standard", 'inseta_qualification_unit_standard_rel', 'inseta__qualification_unit_standard_id', string='Unit standards')
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    qualification_programme_type_id = fields.Many2one('inseta.qualification.programme.type', 'Qualification Programme type')
    # , default=lambda self: self.env.ref('inseta_etqa.inseta_qualification_programme_type_01').id)
    active = fields.Boolean('Active', default=True)
    saqa_id = fields.Char('SAQA ID', default=False)
    # saqa_qualification_id = fields.Many2one('inseta.saqa.qualification', 'Saqa ID')
    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    minimum_credits = fields.Integer('Minimum Credits', default=False)# , compute="compute_total_credits") 
    credits = fields.Integer('Total Credits', default=False, compute="compute_total_credits")
    elective_credits = fields.Integer('Elective Credits', default=False, compute="compute_credits")
    core_credits = fields.Integer('Core Credits', default=False,  compute="compute_credits")
    fundamental_credits = fields.Integer('Fundamental Credits', default=False, compute="compute_credits")
    registration_start_date = fields.Date('Registration Start date')
    registration_end_date = fields.Date('Registration end date')
    last_enroll_date = fields.Date('Last enrollment date')
    last_achievement_date = fields.Date('Last achievement date') 
    quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')
    qualification_type_id = fields.Many2one('inseta.qualification.type', 'Qualification type')
    is_unit_base = fields.Boolean('Us unit base', compute="_onchange_qualification_type_id") 

    legacy_system_id = fields.Integer(help="Financial Year ID from INSETA legacy system")
    ofo_occupation_id = fields.Many2one('res.ofo.occupation', 'Ofo occupation')

    is_registered = fields.Boolean('Is re-registered', default=False)
    new_registration_start_date = fields.Date('New Registration Start date')
    new_registration_end_date = fields.Date('New Registration end date')
    new_last_enroll_date = fields.Date('New Last enrollment date')
    new_last_achievement_date = fields.Date('New Last achievement date') 
    programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'qualification')], limit=1))
    is_replaced = fields.Boolean('Is this Replacement', default=False)
    replaced_qualification_id = fields.Many2one('inseta.qualification', 'Qualification to replace?')
    # unit_standard_type = fields.Many2one('inseta.unit.standard.type', string='Unit standard type ID')
    is_south_african_programme = fields.Boolean('South Africa Programme')

    ## discard
    qualification_line = fields.One2many('inseta.qualification.line', 'line_id', 'Qualification Lines')

    # @api.depends('fundamental_credits', 'elective_credits', 'core_credits')
    # def total_credit_compute(self):
    # 	for rec in self:
    # 		if self.fundamental_credits and self.elective_credits and self.core_credits:
    # 			self.minimum_credits = self.fundamental_credits + self.elective_credits + self.core_credits
    # 			self.credits = self.fundamental_credits + self.elective_credits + self.core_credits
    # 		else:
    # 			self.minimum_credits = False
    # 			self.credits = False

    @api.onchange('minimum_credits')
    def _onchange_mminimum_credits(self):
        for rec in self:
            if self.minimum_credits > 0 and self.minimum_credits > self.credits:
                raise ValidationError("Minimum credit should not be greater than total credits")

    @api.depends('core_credits', 'elective_credits', 'fundamental_credits')
    def compute_total_credits(self):
        for rec in self:
            if rec.core_credits and rec.elective_credits and rec.fundamental_credits:
                rec.credits = rec.core_credits + rec.elective_credits + rec.fundamental_credits
                # rec.minimum_credits = rec.core_credits + rec.elective_credits + rec.fundamental_credits

            else:
                rec.credits = False
                # rec.minimum_credits = False

    @api.depends('qualification_unit_standard_ids')
    def compute_credits(self):
        for rec in self:
            if rec.qualification_unit_standard_ids:
                core = rec.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['core', 'Core'])
                elective = rec.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['elective', 'Elective'])
                fundamental = rec.mapped('qualification_unit_standard_ids').filtered(lambda s: s.unit_standard_type_id.name in ['fundamental', 'Fundamental'])
                rec.core_credits = sum([core.unit_standard_id.credits for core in core])
                rec.elective_credits = sum([elective.unit_standard_id.credits for elective in elective])
                rec.fundamental_credits = sum([fundamental.unit_standard_id.credits for fundamental in fundamental])
            else:
                rec.core_credits = False
                rec.elective_credits = False
                rec.fundamental_credits = False

    @api.depends('qualification_type_id')
    def _onchange_qualification_type_id(self):
        if self.qualification_type_id and self.qualification_type_id.name.startswith('Unit'):
            self.is_unit_base = True 
        else:
            self.is_unit_base = False

    @api.onchange('last_achievement_date', 'new_last_enroll_date','last_enroll_date')
    def _onchange_end_date(self):
        enroll_date = self.last_enroll_date
        if self.last_achievement_date and self.last_enroll_date:
            if self.last_enroll_date < self.last_achievement_date:
                self.last_achievement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Last Achievement date cannot be less than the last Enrollment date"
                    }
                }

        if self.last_enroll_date and self.registration_start_date:
            if self.last_enroll_date < self.registration_start_date:
                self.last_enroll_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Registration date must be less than the Enrollment date"
                    }
                }
        
        if self.new_last_achievement_date and self.new_last_enroll_date:
            if self.new_last_enroll_date < self.new_last_achievement_date:
                self.new_last_achievement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"New Last Achievement date cannot be less than the New last Enrollment date"
                    }
                } 

    @api.onchange('registration_end_date', 'new_registration_end_date')
    def _onchange_end_date(self):
        end_date = self.registration_end_date
        if self.registration_end_date:
            if self.registration_start_date:
                if self.registration_end_date < self.registration_start_date:
                    self.registration_end_date = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
                        }
                    }
            else:
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': "Start date must first be selected"
                    }
                }
            if self.registration_end_date >= fields.Date.today():
                    self.active = True
            else:
                self.active = False
             
        if self.new_registration_end_date:
            if self.new_registration_start_date:
                if self.new_registration_end_date < self.new_registration_start_date:
                    self.new_registration_end_date = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"End date {end_date} cannot be less than the start date {self.new_registration_start_date}"
                        }
                    }
            else:
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': "New reistration start date must first be selected"
                    }
                }

    @api.onchange('saqa_id')
    def _onchange_saqa_id(self):
        if self.saqa_id != 0:
            qualification_duplicate = self.env['inseta.qualification'].search([('saqa_id', '=', self.saqa_id)])
            if len(qualification_duplicate) > 1:
                raise ValidationError('Please no duplicate SAQA qualification ID is allowed')

    @api.constrains('qualification_unit_standard_ids')
    def _check_unit_standard(self):
        if self.qualification_type_id:
            if self.qualification_type_id.name.startswith('Unit') and not self.qualification_unit_standard_ids:
                raise ValidationError('Please ensure you provide qualification unit standards for unit based qualifications')

    # @api.onchange('registration_end_date')
    # def _onchange_registration_end_date(self):
    # 	if self.registration_end_date:
    # 		if self.registration_start_date < self.registration_end_date:
    # 			raise ValidationError('Registration end date must not be greater than Registration start date')
    # 		else:
    # 			raise ValidationError('oooo')
    # 	else:
    # 		raise ValidationError('xxxxx')


    # @api.onchange('new_registration_end_date')
    # def _onchange_registration_end_date(self):
    # 	if self.new_registration_end_date:
    # 		if self.new_registration_start_date < self.new_registration_end_date:
    # 			raise ValidationError('New Registration end date must not be greater than new Registration start date')

class InsetaQualificationline(models.Model):
    _name = 'inseta.qualification.line' # As developed by HWSETA
    _description = "Inseta qualification Lines" 
    _order= "id desc" 

    line_id = fields.Many2one('inseta.qualification')
    name = fields.Char('Name')
    legacy_system_id = fields.Integer(string='Legacy System ID', help="INSETA legacy system ID")


class InsetaQualificationUnitStandardType(models.Model):
    _name = 'inseta.unit.standard.type'
    _description = "Inseta qualification unit standard type" 
    _order= "id desc" 

    legacy_system_id = fields.Integer('Legacy System ID')
    code = fields.Char('SAQA CODE')
    name = fields.Char('Title')
    active = fields.Boolean('Active', default=True)
    # unit_standard_ids = fields.Many2many("inseta.unit.standard", 'unit_standard_type_rel', 'column1', 'inseta_unit_standard_id', string="Unit Standards")


class InsetaQualificationUnitStandard(models.Model):
    _name = 'inseta.qualification.unit.standard'
    _description = "Inseta qualification unit standard type" 
    _order= "id desc" 

    legacy_system_id = fields.Integer('Legacy System ID')
    code = fields.Char('SAQA CODE')
    name = fields.Char('Title')
    active = fields.Boolean('Active', default=True)
    unit_standard_id = fields.Many2one("inseta.unit.standard", string='Unit standard')
    unit_standard_type_id = fields.Many2one("inseta.unit.standard.type", string='Unit standard type')
    qualification_id = fields.Many2one("inseta.qualification", string='Qualififcation', domain=lambda act: [('active', '=', True)])
    credits = fields.Integer(string='Credit(s)', store=False, compute="compute_values")

    @api.depends('unit_standard_id')
    def compute_values(self):
        for rec in self:
            if rec.unit_standard_id:
                rec.credits = rec.unit_standard_id.credits
            else:
                rec.credits = False
 
class InsetaSkillUnitStandard(models.Model):
    _name = 'inseta.skill.unit.standard'
    _description = "Inseta skill unit standard type" 
    _order= "id desc" 

    legacy_system_id = fields.Integer('Legacy System ID')
    code = fields.Char('SAQA CODE')
    name = fields.Char('Title')
    active = fields.Boolean('Active', default=True)
    unit_standard_id = fields.Many2one("inseta.unit.standard", string='Unit standard')
    unit_standard_type_id = fields.Many2one("inseta.unit.standard.type", string='Unit standard type')
    skill_programme_id = fields.Many2one("inseta.skill.programme", string='Qualififcation')
    credits = fields.Integer(string='Credit(s)', store=False, compute="compute_values")

    @api.depends('unit_standard_id')
    def compute_values(self):
        for rec in self:
            if rec.unit_standard_id:
                rec.credits = rec.unit_standard_id.credits
            else:
                rec.credits = False


class InsetaLearnershipUnitStandard(models.Model):
    _name = 'inseta.learnership.unit.standard'
    _description = "Inseta Learnership unit standard type" 
    _order= "id desc"

    legacy_system_id = fields.Integer('Legacy System ID')
    code = fields.Char('SAQA CODE')
    name = fields.Char('Title')
    active = fields.Boolean('Active', default=True)
    unit_standard_id = fields.Many2one("inseta.unit.standard", string='Unit standard')
    unit_standard_type_id = fields.Many2one("inseta.unit.standard.type", string='Unit standard type')
    learner_programme_id = fields.Many2one("inseta.learner.programme", string='Qualififcation')
    credits = fields.Integer(string='Credit(s)', store=False, compute="compute_values")

    @api.depends('unit_standard_id')
    def compute_values(self):
        for rec in self:
            if rec.unit_standard_id:
                rec.credits = rec.unit_standard_id.credits
            else:
                rec.credits = False


class InsetaUnitStandard(models.Model):
    _name = 'inseta.unit.standard'
    _description = "Inseta qualification unit standard"
    _order= "id desc" 

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.code, rec.name.title())
            arr.append((rec.id, name))
        return arr

    name = fields.Char('Name')
    verifier_name = fields.Many2one("res.users", string='Verifier Name')
    verified_date = fields.Date('Verifier Date')
    legacy_system_id = fields.Integer('Legacy System ID')
    programme_type_id = fields.Many2one('inseta.programme.type', 'Programme type', default=lambda self: self.env['inseta.programme.type'].search([('is_type', '=', 'unit')], limit=1))
    qualification_ids = fields.One2many('inseta.qualification', 'unit_standard_id', 'Qualification Lines')
    programme_ids = fields.One2many('inseta.skill.programme', 'programme_unit_id', 'Programmes Lines')
    code = fields.Char('SAQA ID')
    saqa_title = fields.Char('SAQA Title')
    highest_edu_level_id = fields.Many2one(
        'res.education.level', string='Highest Level Of Education')
    highest_edu_desc = fields.Text('Highest Education Description')
    saqa_qualification_code = fields.Many2one('inseta.saqa.qualification', '')
    unit_standard_type = fields.Many2one('inseta.unit.standard.type', string='Unit standard type')
    unit_standard_type_id = fields.Selection([('1', '1'), ('2', '2'),('3', '3')], string='')

    nqflevel_id = fields.Many2one('res.nqflevel', 'NQF Level')
    credits = fields.Integer('Total Credits')#, compute="compute_total_credits")
    elective_credits = fields.Integer('Elective Credits')
    core_credits = fields.Integer('Core Credits', default=False)
    fundamental_credits = fields.Integer('Fundamental Credits', default=False)
    registration_start_date = fields.Date('Registration Start date')
    registration_end_date = fields.Date('Registration end date')
    last_enroll_date = fields.Date('Last enrollment date')
    last_achievement_date = fields.Date('Last achievement date')
    active = fields.Boolean('Active', default=True)
    select_option = fields.Boolean('', default=False)
    is_registered = fields.Boolean('Is re-registered', default=False)
    is_replaced = fields.Boolean('Is this Replacement', default=False)
    replaced_unit_standard = fields.Many2one('inseta.unit.standard', 'Unit standard to replace?')
    new_registration_start_date = fields.Date('New Registration Start date')
    new_registration_end_date = fields.Date('New Registration end date')
    new_last_enroll_date = fields.Date('New Last enrollment date')
    new_last_achievement_date = fields.Date('New Last achievement date') 
    quality_assurance_id = fields.Many2one('inseta.quality.assurance', 'Quality Assurance Body')

    @api.onchange('last_achievement_date', 'new_last_enroll_date','last_enroll_date')
    def onchange_end_date(self):
        if self.last_achievement_date and self.last_enroll_date:
            if self.last_achievement_date < self.last_enroll_date:
                self.last_achievement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Last Achievement date cannot be less than the last Enrollment date"
                    }
                }

        if self.last_enroll_date and self.registration_start_date:
            if self.last_enroll_date < self.registration_start_date:
                self.last_enroll_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"Registration date must be less than the Enrollment date"
                    }
                }
        
        if self.new_last_achievement_date and self.new_last_enroll_date:
            if self.new_last_achievement_date < self.new_last_enroll_date:
                self.new_last_achievement_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"New Last Achievement date cannot be less than the New last Enrollment date"
                    }
                }


    @api.onchange('registration_end_date', 'new_registration_end_date')
    def _onchange_end_date(self):
        end_date = self.registration_end_date
        if self.registration_end_date:
            if self.registration_start_date:
                if self.registration_end_date < self.registration_start_date:
                    self.registration_end_date = False
                    return {
                        'warning': {
                            'title': "Validation Error!",
                            'message': f"End date {end_date} cannot be less than the start date {self.registration_start_date}"
                        }
                    }
            
            if self.registration_end_date >= fields.Date.today():
                self.active = True
                
            else:
                self.active = False
            
        if self.new_registration_end_date and self.new_registration_start_date:
            if self.new_registration_end_date < self.new_registration_start_date:
                self.new_registration_end_date = False
                return {
                    'warning': {
                        'title': "Validation Error!",
                        'message': f"End date {end_date} cannot be less than the start date {self.new_registration_start_date}"
                    }
                }

    @api.onchange('code')
    def _onchange_code(self):
        if self.code != 0:
            duplicate = self.env['inseta.unit.standard'].search([('code', '=', self.code)])
            if len(duplicate) > 1:
                raise ValidationError('Please no duplicate SAQA ID is allowed')


class InsetaQualityAssurance(models.Model):
    _name = 'inseta.quality.assurance'
    _description = "Inseta quality Assurance"
    _order= "id desc" 

    def name_get(self):
        arr = []
        for rec in self:
            name = "[{}] {}".format(rec.code, rec.name.title())
            arr.append((rec.id, name))
        return arr

    name = fields.Char('Name')
    code = fields.Char('SAQA Code')
    legacy_system_id = fields.Integer('Legacy System ID')
    active = fields.Boolean('Active', default=True)

class InsetaQualificationType(models.Model):
    _name = 'inseta.qualification.type'
    _order= "id desc" 

    name = fields.Char('Name')
    legacy_system_id = fields.Integer('Legacy System ID')
    code = fields.Char('SAQA Code')
    active = fields.Boolean('Active', default=True)