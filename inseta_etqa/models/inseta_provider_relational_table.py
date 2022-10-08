from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
from odoo.addons.inseta_tools.converters import  dd2dms

_logger = logging.getLogger(__name__)



class ProviderAssessor(models.Model):
    _name = 'inseta.provider.assessor'
    _description = 'Provider Assessor' 
    _rec_name = "provider_id"

    """This is the table that holds Provider Assessor"""

    active = fields.Boolean(default=True)
    assessor_id = fields.Many2one("inseta.assessor", string='Assessor Name')
    provider_id = fields.Many2one("inseta.provider", string='Provider')
    assessment_end_date = fields.Date('Assessment End date')


class ProviderModerator(models.Model):
    _name = 'inseta.provider.moderator'
    _description = 'Provider moderator' 
    _rec_name = "provider_id"
    """This is the table that holds Provider moderator"""

    active = fields.Boolean(default=True)
    moderator_id = fields.Many2one("inseta.moderator", string='Moderator Name')
    provider_id = fields.Many2one("inseta.provider", string='Provider')
    moderator_end_date = fields.Date('Moderation End date')


class ProviderLearner(models.Model):
    _name = 'inseta.provider.learner'
    _description = 'Provider learner' 
    """This is the table that holds Provider learner"""

    active = fields.Boolean(default=True)
    learner_id = fields.Many2one("inseta.learner", string='Learner Name')
    id_no = fields.Char(string='Identification', related="learner_id.id_no")
    provider_id = fields.Many2one("inseta.provider", string='Provider')


class ProviderAccreditationHistory(models.Model):
    _name = 'inseta.provider.accredit_history'
    _description = 'Provider History Learner' 
    """This is the table that holds Provider Accreditation history"""

    active = fields.Boolean(default=True)
    provider_accreditation_id = fields.Many2one("inseta.provider.accreditation", string='Accreditation ID')
    provider_id = fields.Many2one("inseta.provider", string='Provider')
    provider_status_id = fields.Many2one("inseta.provider.registration.status", 'Provider Status', default=lambda s: s.env.ref('inseta_etqa.data_inseta_provider_regis_status2'))
    accreditation_start_date = fields.Date('Accreditation Start date')
    accreditation_end_date = fields.Date('Accreditation End date')

