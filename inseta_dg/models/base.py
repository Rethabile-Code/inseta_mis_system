from odoo import fields, models, _


# discgranttype

class ResDgType(models.Model):
    _name = "res.dgtype"
    _description ="DG type"

    _order ="sequence"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    cost_per_learner = fields.Float()
    cost_per_disabled = fields.Float()
    is_max_cost = fields.Boolean('is maximum cost per learner?')
    for_hei = fields.Selection([
        ('yes','Yes'),
        ('no','No'),
        ('both','Both')
    ], 
    default="no",
    help='Indicates if a programme is for HEI')
    seta_mail_to = fields.Char()
    sequence = fields.Integer()
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')


class ResDgDocumentType(models.Model):
    _name = "res.dgdocumenttype"
    _description ="DG Document Type"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')


class ResDginternshipscarcecritical(models.Model):
    _name = "res.dginternshipscarcecritical"
    _description ="DG internship scarcecritical"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')

class ResDgPublicProvider(models.Model):
    _name = "res.dgpublicprovider"
    _description ="DG Public Provider"
    
    name = fields.Char('Name')
    saqacode = fields.Char(string='Saqa Code')
    active = fields.Boolean(string='Active', default=True)
    legacy_system_id = fields.Integer(string='Legacy System ID')
    

class ResUsersExtension(models.Model):
    _inherit = "res.users"
    
    dgfundingwindow_id = fields.Many2one('inseta.dgfunding.window', 'DG Funding Window')
    dgapplication_id = fields.Many2one('inseta.dgapplication', 'DG Application')
    hei_rep_id = fields.Many2one('mis.hei.representative', 'HEI Rep')

