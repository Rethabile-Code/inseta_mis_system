from odoo import fields, models, _


class ResCrmDocument(models.Model):
    """relates to dbo.lkpcrmdocumentrelates.csv
    """
    _name = "res.crmdocumentrelates"
    _description ="Organisation CRM Documents"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
class ResFormClass(models.Model):
    """relates to dbo.lkpformclass.csv
    """
    _name = "res.formclass"
    _description ="WSP Form Class"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResWorkplacesp(models.Model):
    """relates to dbo.lkpworkplacesp.csv
    """
    _name = "res.workplacesp"
    _description ="Work Place Skill Plan"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResVarianceReason(models.Model):
    """relates to dbo.lkpvariancereason.csv
    """
    _name = "res.variancereason"
    _description ="WSPATR Variance Reason"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResSkillsGapReason(models.Model):
    """relates to dbo.lkpformskillsgapreasons.csv
    """
    _name = "res.formskillsgapreasons"
    _description ="WSPATR Skill Gap Reason"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResSkillsGap(models.Model):
    """relates to #dbo.lkpformskillsgap.csv
    """
    _name = "res.formskillsgap"
    _description ="WSPATR Skill Gap" #dbo.lkpformskillsgap.csv
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResVacancyreason(models.Model):
    """relates to dbo.lkpformvacancyreasons.csv
    """
    _name = "res.vacancyreason"
    _description ="WSP Vacancy Reason"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResWspDocument(models.Model):
    """relates to dbo.lkpwspatrdocumentrelates.csv
    """
    _name = "res.wspdocument.relates"
    _description ="WSP Document Relates"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')



class ResIstChangereason(models.Model):
    """relates to dbo.lkpistchangereason.csv
    """
    _name = "res.istchangereason"
    _description ="Inter SETA Change reason"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')


class ResIstTransferStatus(models.Model):
    """relates to dbo.lkpisttransferstatus.csv
    """
    _name = "res.isttransferstatus"
    _description ="Inter SETA Transfer Status"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')


class ResWspStatus(models.Model):
    """relates to dbo.lkpwspstatus.csv
    this is for legacy backward compatibility
    """
    _name = "res.wspstatus"
    _description ="WSP Status"
    
    name = fields.Char('Name')
    active = fields.Boolean(default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
