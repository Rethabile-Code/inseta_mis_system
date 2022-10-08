# -*- coding: utf-8 -*-

from logging import fatal
from odoo import api, fields, models


class WspatrMovetoPivotal(models.TransientModel):
    """Move lines to pivotal trained or planned beneficiaries
    """

    _name = "inseta.wspatr.movetopivotal" #inseta_wspatr_movetopivotal
    _description = "WSPATR: Move line to pivotal"

    @api.model
    def default_get(self, fields):
        res = super(WspatrMovetoPivotal, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        active_id = active_ids[0] if active_ids else False
        trained_beneficiaries, planned_beneficiaries, impl_reports, workplaceskillsplan_ids  = [], [], [], []

        if self._context.get('is_trained_beneficiaries'):
            trained_beneficiaries = self.env['inseta.wspatr.trained.beneficiaries.report'].search([('wspatr_id','=',active_id),('is_pivotal','=',True)])
        
        if self._context.get('is_implementation_report'):
            impl_reports = self.env['inseta.wspatr.implementation.report'].search([('wspatr_id','=',active_id),('is_pivotal','=',True)])

        if self._context.get('is_planned_beneficiaries'):
            planned_beneficiaries = self.env['inseta.wspatr.planned.beneficiaries'].search([('wspatr_id','=',active_id),('is_pivotal','=',True)])

        if self._context.get('is_workplaceskillsplan'):
            workplaceskillsplan_ids = self.env['inseta.wspatr.workplaceskillsplan'].search([('wspatr_id','=',active_id),('is_pivotal','=',True)])

        res.update({
            'wspatr_id': active_id,
            'is_implementation_report': self._context.get('is_implementation_report'),
            'is_trained_beneficiaries': self._context.get('is_trained_beneficiaries'), 
            'is_planned_beneficiaries': self._context.get('is_planned_beneficiaries'), 
            'is_workplaceskillsplan': self._context.get('is_workplaceskillsplan'), 
            'trained_beneficiaries_ids': [(6,0,[tb.id for tb in trained_beneficiaries])],
            'implementation_report_ids': [(6,0,[ir.id for ir in impl_reports])],
            'planned_beneficiaries_ids': [(6,0,[pb.id for pb in planned_beneficiaries])],
            'workplaceskillsplan_ids': [(6,0,[ws.id for ws in  workplaceskillsplan_ids])],
        })
        return res


    wspatr_id = fields.Many2one('inseta.wspatr')
    is_implementation_report = fields.Boolean()
    is_trained_beneficiaries = fields.Boolean()
    is_planned_beneficiaries = fields.Boolean()
    is_workplaceskillsplan = fields.Boolean()
    trained_beneficiaries_ids = fields.Many2many(
        'inseta.wspatr.trained.beneficiaries.report',
        'movetopivotal_wizard_trainedbeneficiaries_rel',
        'wizard_id',
        'beneficiary_id',
        string='Trained beneficiaries Line'
    )
    implementation_report_ids = fields.Many2many(
        'inseta.wspatr.implementation.report',
        'movetopivotal_wizard_implementationreport_rel',
        'wizard_id',
        'beneficiary_id',
        string="Implementation Reports"
    )
    planned_beneficiaries_ids = fields.Many2many(
        'inseta.wspatr.planned.beneficiaries',
        'movetopivotal_wizard_plannedbeneficiaries_rel',
        'wizard_id',
        'beneficiary_id',
        string='Planned beneficiaries Line'
    )

    workplaceskillsplan_ids  = fields.Many2many(
        'inseta.wspatr.workplaceskillsplan',
        'movetopivotal_wizard_workplaceskillsplan_rel',
        'wizard_id',
        'beneficiary_id',
        string="Workplace Skills Plan"
    )


    def move(self):
        self.ensure_one()
        if self.is_trained_beneficiaries:
            #It would have made more sense to create the trained beneficiaries from self.trained_beneficiaries_ids
            #but since i need to delete the moved records from main wspatr form, I will loop through the main recordset
            # and delete the record set when im done 
            trained_beneficiaries = self.env['inseta.wspatr.trained.beneficiaries.report'].search([('wspatr_id','=',self.wspatr_id.id),('is_pivotal','=',True)])
            vals_list = []
            for rec in trained_beneficiaries:
                vals_list.append(dict(
                    wspatr_id = rec.wspatr_id.id,
                    ofo_occupation_id  = rec.ofo_occupation_id.id,
                    ofo_specialization_id = rec.ofo_specialization_id.id,
                    programme_level =  rec.programme_level,
                    training_provider = rec.training_provider,
                    completion_status = rec.completion_status,
                    start_date = False,
                    end_date = False,
                    nqf_level_id = False,
                    municipality_id = rec.municipality_id.id,
                    socio_economic_status = False,
                    pivotal_programme_id = False,
                    other_pivotal_programme = False,
                    other_country = rec.other_country,
                    african_male = rec.african_male,
                    african_female = rec.african_female,
                    african_disabled = rec.african_disabled,
                    colored_male = rec.colored_male,
                    colored_female = rec.colored_female,
                    colored_disabled = rec.colored_disabled,
                    indian_male = rec.indian_male,
                    indian_female = rec.indian_female,
                    indian_disabled = rec.indian_disabled,
                    white_male = rec.white_male,
                    white_female = rec.white_female,
                    white_disabled = rec.white_disabled,
                    other_male = rec.other_male,
                    other_female = rec.other_female,
                    other_disabled = rec.other_disabled,
                    age1 = rec.age1,
                    age2 = rec.age2,
                    age3 = rec.age3,
                    age4 = rec.age4,
                ))
            self.env['inseta.wspatr.pivotal.trained.beneficiaries'].create(vals_list)
            #lets delete after the records have been moved
            #trained_beneficiaries.unlink()

        if self.is_implementation_report: #small form equivalent of trained beneficiaries
            vals_list = []
            implementation_report_ids = self.env['inseta.wspatr.implementation.report'].search([('wspatr_id','=',self.wspatr_id.id),('is_pivotal','=',True)])
            for rec in implementation_report_ids:
                vals_list.append(dict(
                    wspatr_id = rec.wspatr_id.id,
                    ofo_occupation_id  = rec.ofo_occupation_id.id,
                    ofo_specialization_id = rec.ofo_specialization_id.id,
                    programme_level =  rec.programme_level,
                    training_provider = rec.training_provider,
                    completion_status = rec.completion_status,
                    start_date = False,
                    end_date = False,
                    nqf_level_id = False,
                    municipality_id = False,
                    socio_economic_status = False,
                    pivotal_programme_id = False,
                    other_pivotal_programme = False,
                    other_country = rec.other_country,
                    african_male = rec.african_male,
                    african_female = rec.african_female,
                    african_disabled = rec.african_disabled,
                    colored_male = rec.colored_male,
                    colored_female = rec.colored_female,
                    colored_disabled = rec.colored_disabled,
                    indian_male = rec.indian_male,
                    indian_female = rec.indian_female,
                    indian_disabled = rec.indian_disabled,
                    white_male = rec.white_male,
                    white_female = rec.white_female,
                    white_disabled = rec.white_disabled,
                    other_male = rec.other_male,
                    other_female = rec.other_female,
                    other_disabled = rec.other_disabled,
                    age1 = rec.age1,
                    age2 = rec.age2,
                    age3 = rec.age3,
                    age4 = rec.age4,
                ))
            self.env['inseta.wspatr.pivotal.trained.beneficiaries'].create(vals_list)
            #implementation_report_ids.unlink()

        if self.is_planned_beneficiaries:
            planned_beneficiaries_ids = self.env['inseta.wspatr.planned.beneficiaries'].search([('wspatr_id','=',self.wspatr_id.id),('is_pivotal','=',True)])
            vals_list = []
            for rec in planned_beneficiaries_ids:
                vals_list.append(dict(
                    wspatr_id = rec.wspatr_id.id,
                    ofo_occupation_id  = rec.ofo_occupation_id.id,
                    ofo_specialization_id = rec.ofo_specialization_id.id,
                    programme_level =  rec.programme_level,
                    training_provider = False,
                    start_date = False,
                    end_date = False,
                    municipality_id = rec.municipality_id.id,
                    socio_economic_status = rec.socio_economic_status,
                    pivotal_programme_id = False,
                    other_pivotal_programme = False,
                    other_country = rec.other_country,
                    african_male = rec.african_male,
                    african_female = rec.african_female,
                    african_disabled = rec.african_disabled,
                    colored_male = rec.colored_male,
                    colored_female = rec.colored_female,
                    colored_disabled = rec.colored_disabled,
                    indian_male = rec.indian_male,
                    indian_female = rec.indian_female,
                    indian_disabled = rec.indian_disabled,
                    white_male = rec.white_male,
                    white_female = rec.white_female,
                    white_disabled = rec.white_disabled,
                    other_male = rec.other_male,
                    other_female = rec.other_female,
                    other_disabled = rec.other_disabled,
                    age1 = rec.age1,
                    age2 = rec.age2,
                    age3 = rec.age3,
                    age4 = rec.age4,
                ))
            self.env['inseta.wspatr.pivotal.planned.beneficiaries'].create(vals_list)
            #planned_beneficiaries_ids.unlink() 

        if self.is_workplaceskillsplan: #small form equivalent of planned beneficiaries
            vals_list = []
            workplaceskillsplans = self.env['inseta.wspatr.workplaceskillsplan'].search([('wspatr_id','=',self.wspatr_id.id),('is_pivotal','=',True)])
            for rec in workplaceskillsplans:
                vals_list.append(dict(
                    wspatr_id = rec.wspatr_id.id,
                    ofo_occupation_id  = rec.ofo_occupation_id.id,
                    ofo_specialization_id = rec.ofo_specialization_id.id,
                    municipality_id = False,
                    socio_economic_status = False,
                    pivotal_programme_id = False,
                    other_pivotal_programme = False,
                    other_country = rec.other_country,
                    african_male = rec.african_male,
                    african_female = rec.african_female,
                    african_disabled = rec.african_disabled,
                    colored_male = rec.colored_male,
                    colored_female = rec.colored_female,
                    colored_disabled = rec.colored_disabled,
                    indian_male = rec.indian_male,
                    indian_female = rec.indian_female,
                    indian_disabled = rec.indian_disabled,
                    white_male = rec.white_male,
                    white_female = rec.white_female,
                    white_disabled = rec.white_disabled,
                    other_male = rec.other_male,
                    other_female = rec.other_female,
                    other_disabled = rec.other_disabled,
                    age1 = rec.age1,
                    age2 = rec.age2,
                    age3 = rec.age3,
                    age4 = rec.age4,
                ))
            self.env['inseta.wspatr.pivotal.planned.beneficiaries'].create(vals_list)
            #workplaceskillsplans.unlink()
        return {'type': 'ir.actions.act_window_close'}
