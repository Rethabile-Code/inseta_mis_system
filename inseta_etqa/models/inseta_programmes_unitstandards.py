from datetime import datetime, timedelta
import logging

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InsetaLearnerLearnershipUnitstandard(models.Model):
    _name = "inseta.learnership.unitstandard"
    _description = "learner.learnership.unitstandard"

    learnership_id = fields.Many2one('inseta.learner.learnership', string='Learnership')	
    unit_standard_id = fields.Many2one('inseta.unit.standard', string='Unit standard')
    unit_standard_type = fields.Many2one('inseta.unit.standard.type', string='Unit standard type ID')
    programme_id = fields.Integer(string='Programme ID')
    select = fields.Boolean(default=False)
    credits = fields.Integer(string='Credit(s)', store=False, compute="compute_values")

    @api.depends('unit_standard_id')
    def compute_values(self):
        for rec in self:
            if rec.unit_standard_id:
                rec.credits = rec.unit_standard_id.credits
            else:
                rec.credits = False 
                
    @api.onchange('programme_id')
    def onchange_programme_id(self):
        if self.programme_id:
            items = None
            programme_id = self.env['inseta.learner.programme'].browse([self.programme_id])
            items = [rec.unit_standard_id.id for rec in programme_id.learnership_unit_standard_ids] if programme_id.learnership_unit_standard_ids else None
            return {
                'domain': {
                    'unit_standard_id': [('id', 'in', items)]
                }
            }

    # @api.constrains('unit_standard_id', 'unit_standard_type')
    # def onchange_unit_standard_id(self):
    #     programme_id = self.env['inseta.learner.learnership'].browse([self.programme_id])
    #     if programme_id:
    #         if self.unit_standard_type:
    #             # and self.unit_standard_id:
    #             duplicate_unit_standard = [rec.unit_standard_id.id for rec programme_id.mapped('learnership_unit_standard_ids').filtered(lambda x: x.unit_standard_id.id == self.unit_standard_id.id and x.unit_standard_type.id == self.unit_standard_type.id)]
    #             # if len(duplicate_unit_standard) > 0:
    #             # raise ValidationError('You have already selected the unit standard with the same unit standard type selected,, try another one')
    #             raise ValidationError(duplicate_unit_standard)
 
class InsetaLearnerQualificationnitstandard(models.Model):
    _name = "inseta.qualification.unitstandard"
    _description = "learner.qualification.unitstandard"

    qualification_learnership_id = fields.Many2one('inseta.qualification.learnership', string='Qualification Learnership')	
    unit_standard_id = fields.Many2one('inseta.unit.standard', string='Unit standard')
    unit_standard_type = fields.Many2one('inseta.unit.standard.type', string='Unit standard type ID')
    programme_id = fields.Integer(string='Programme ID')
    select = fields.Boolean(default=False)
    credits = fields.Integer(string='Credit(s)', store=False, compute="compute_values")

    @api.depends('unit_standard_id')
    def compute_values(self):
        for rec in self:
            if rec.unit_standard_id:
                rec.credits = rec.unit_standard_id.credits 
            else:
                rec.credits = False

    @api.onchange('programme_id')
    def onchange_programme_id(self):
        if self.programme_id:
            programme_id = self.env['inseta.qualification'].browse([self.programme_id])
            items = programme_id.qualification_unit_standard_ids.ids if programme_id.qualification_unit_standard_ids else None
            return {
                'domain': {
                    'unit_standard_id': [('id', 'in', items)]
                }
            }


class InsetaLearnerSkillUnitstandard(models.Model):
    _name = "inseta.skill.unitstandard"
    _description = "learner.skills.unitstandard"

    skill_learnership_id = fields.Many2one('inseta.skill.learnership', string='Learnership')	
    unit_standard_id = fields.Many2one('inseta.unit.standard', string='Unit standard')
    unit_standard_type = fields.Many2one('inseta.unit.standard.type', string='Unit standard type ID')
    programme_id = fields.Integer(string='Programme ID')
    select = fields.Boolean(default=False)
    credits = fields.Integer(string='Credit(s)', store=False, compute="compute_values")

    @api.depends('unit_standard_id')
    def compute_values(self):
        for rec in self:
            if rec.unit_standard_id:
                rec.credits = rec.unit_standard_id.credits 
            else:
                rec.credits = False

    @api.onchange('programme_id')
    def onchange_programme_id(self):
        if self.programme_id:
            programme_id = self.env['inseta.skill.programme'].browse([self.programme_id])
            items = programme_id.skill_unit_standard_ids.ids if programme_id.skill_unit_standard_ids else None
            return {
                'domain': {
                    'unit_standard_id': [('id', 'in', items)]
                }
            }