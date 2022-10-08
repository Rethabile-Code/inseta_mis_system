
from odoo import fields, models ,api, _
from tempfile import TemporaryFile
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import base64
import copy
import io
import re
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta as rd
import xlrd
from xlrd import open_workbook
import csv
import base64
import sys
_logger = logging.getLogger(__name__)


class InsetaCertifiedProgrammes(models.Model):
    _name = 'inseta.certified.programmes'
    _description  = "Holds the programmes to be Certified"

    name = fields.Char('Programme Name')
    nqf_level = fields.Char('Nqf level')
    learnership_record_id = fields.Integer('Learnership Record ID')
    res_id = fields.Many2one('inseta.batch_certificate.wizard', 'Related record')
    learner_id = fields.Many2one('inseta.learner', 'Learner')
    provider_id = fields.Many2one('inseta.provider', required=False, store=True)

class InsetaLearnerBatchCert(models.Model):
    _name = 'inseta.batch_certificate.wizard'
    _description  = "Batch Print Certificate"
    _rec_name = "programme_type"
    _order= "id desc" 

    programme_type = fields.Selection([ 
            ('Learnership','Learnership'),
            ('Qualification','Qualification'),
            ('Skill','Skill'),
            ('Bursary','Bursary'),
            ('Candidacy','Candidacy'),
            ('Internship','Internship'),
            ('Wiltvet','WILTVET'),
            ('Unit','Unit standard'),
        ],
        default="Learnership", string="Programme Type", required=True,
    )
    action_type = fields.Selection([ 
            ('All','All'),
            ('Individual','Individual'),
        ],
        default="All", string="Action"
    )

    certificate_action = fields.Selection([ 
            ('All','Print Both'),
            ('Certificate','New Certificate'),
            ('Reprint','Reprint Certificate'),
        ],
        default="Certificate", string="Print Action"
    )
    num_of_records = fields.Integer(string="Number of Records ", store=True, )
    limit = fields.Integer(string="Limit", store=True, default = 10)
    total_pool = fields.Integer(string="Number of Pool", store=True, default = 0)
    learner_id = fields.Many2one('inseta.learner', required=False, store=True)
    provider_id = fields.Many2one('inseta.provider', required=False, store=True)
    provider_sdl = fields.Char(related="provider_id.employer_sdl_no", required=False, store=True)
    learner_ids = fields.Many2many('inseta.learner', 'inseta_learner_batch_certificate_rel', string="Learners")
    programme_certified_ids = fields.One2many('inseta.certified.programmes', 'res_id', string="Programmes")
    financial_year_id = fields.Many2one('res.financial.year', required=False, store=True)
    skill_programmes_id = fields.Many2one("inseta.skill.programme", string='Skill Programme')
    learner_programmes_id = fields.Many2one("inseta.learner.programme", string='Learnership Programme')#, default=lambda self: self._get_default_programme())
    qualification_id = fields.Many2one("inseta.qualification", string='Qualification')
    unit_standard_id = fields.Many2one("inseta.unit.standard", string='Unit standard')
    bursary_type_id = fields.Many2one("res.bursary.type", string='Bursary')
    # candidacy_id = fields.Many2one("inseta.candidacy.programme", string='Candidacy')
    # wiltvet_id = fields.Many2one("inseta.wiltvet.programme", string='Wiltvet')
    # internship_id = fields.Many2one("inseta.internship.programme", string='Internship')

    def learner_programme_data(self, model):
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        domain = ['|',('programme_status_id.id', '=', completed_status),
        ('programme_status_id.name', '=', 'Achieved')]

        # if self.certificate_action != "Reprint":
        #     domain += [('certificate_issued', '=', False)]
            
        if self.provider_id:
            domain += [('provider_id', '=', self.provider_id.id)]
            
        if self.learner_id:
            domain += [('learner_id', '=', self.learner_id.id)]

        if self.financial_year_id:
            domain += [('financial_year_id', '=', self.financial_year_id.id)]

        if self.learner_programmes_id:
            domain += [('learner_programme_id', '=', self.learner_programmes_id.id)]

        if self.qualification_id:
            domain += [('qualification_id', '=', self.qualification_id.id)]

        # if self.certificate_action in ["Reprint", 'All']:
        #     domain += [('certificate_issued', '=', True)]

        # if self.certificate_action in ["Certificate"]:
        #     # self.certificate_action not in ["Reprint", 'All']:
        #     domain += [('certificate_issued', '=', False)]
        data = self.env[f'{model}'].search(domain, limit=self.limit)
        return data 

    def action_generate_programme_pool(self, list, search_view_ref, form_view_ref, tree_view_ref,model):
        search_view_ref = search_view_ref 
        form_view_ref = form_view_ref 
        tree_view_ref = tree_view_ref 
        return {
            'domain': [('id', 'in', list)],
            'name': 'Certification',
            'res_model': model, #'inseta.certified.programmes',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        }
        
        
    def action_generate_certified_records(self):
        """Print certification for respective programmes"""
        data = None
        if self.skill_programmes_id:
            # to print(statement of result)
            pass 
            
            # model = "inseta.skill.learnership"
            # data = self.learner_programme_data(model)
            # for record in data:
            # 	programme_certified_ids
            # 	record.certificate_issued = True # set the boolean field to true when certificates are printed
            # 	self.env.ref('inseta_etqa.action_report_skill_learnership_certificate').sudo()._render_qweb_pdf([record.id])# [0]

        if self.learner_programmes_id or self.programme_type in ['Learnership']:
            model = "inseta.learner.learnership"
            data = self.learner_programme_data(model)
            if not data:
                raise ValidationError('No record available to print certificate')

            list = [rec.id for rec in data]

            search_view_ref = self.env.ref('inseta_etqa.view_inseta_learner_learnership_filter', False)
            form_view_ref = self.env.ref('inseta_etqa.view_inseta_learner_learnership_form', False)
            tree_view_ref = self.env.ref('inseta_etqa.view_inseta_learner_learnership_tree', False)
            for record in data:
                record.certificate_issued = True
            return self.action_generate_programme_pool(list, search_view_ref, form_view_ref, tree_view_ref,model)
 
        if self.qualification_id or self.programme_type in ['Qualification']:
            model = "inseta.qualification.learnership"
            data = self.learner_programme_data(model)
            if not data:
                raise ValidationError('No record available to print certificate')

            list = [rec.id for rec in data]
            search_view_ref = self.env.ref('inseta_etqa.view_inseta_qualification_learnership_filter', False)
            form_view_ref = self.env.ref('inseta_etqa.view_inseta_qualification_learnership_form', False)
            tree_view_ref = self.env.ref('inseta_etqa.view_inseta_qualification_learnership_tree')
            for record in data:
                record.certificate_issued = True
            return self.action_generate_programme_pool(list, search_view_ref, form_view_ref, tree_view_ref,model)


            # data = self.learner_programme_data(model)
            # for record in data:
            # 	record.certificate_issued = True # set the boolean field to true when certificates are printed
            # 	self.env.ref('inseta_etqa.action_report_qual_learnership_certificate').sudo()._render_qweb_pdf([record.id])# [0]


        if self.unit_standard_id:
            model = "inseta.unit_standard.learnership"
            data = self.learner_programme_data(model)
            for record in data:
                record.certificate_issued = True # set the boolean field to true when certificates are printed
                self.env.ref('inseta_etqa.action_report_unit_standard_learnership_certificate').sudo()._render_qweb_pdf([record.id])# [0]

        if self.bursary_type_id:
            model = "inseta.bursary.learnership"
            data = self.learner_programme_data(model)
            for record in data:
                record.certificate_issued = True # set the boolean field to true when certificates are printed
                self.env.ref('inseta_etqa.action_report_bursary_learnership_certificate').sudo()._render_qweb_pdf([record.id])# [0]
 
    @api.onchange('programme_type')
    def _onchange_programme_type(self):
        if self.programme_type:
            self.learner_programmes_id = False
            self.skill_programmes_id = False
            self.qualification_id = False
            self.unit_standard_id = False
            self.bursary_type_id = False

    @api.onchange('learner_id')
    def _onchange_learner(self):
        if self.learner_id:
            self.learner_ids = [(6, 0, [self.learner_id.id])]

    def action_fetch_records(self):
        list = []
        for learner in self.learner_ids:
            learnership_vals = self.get_learners_with_selected_programmes(learner)
            # self.programme_certified_ids = [(0,0, learnership_vals)]
            if learnership_vals:
                list.append(self.env['inseta.certified.programmes'].create(learnership_vals).id)

        search_view_ref = self.env.ref('inseta_etqa.inseta_certified_programmes_search_view', False)
        form_view_ref = self.env.ref('inseta_etqa.inseta_certified_programmes_form_view', False)
        tree_view_ref = self.env.ref('inseta_etqa.inseta_certified_programmes_tree_view', False)
        return {
            'domain': [('id', 'in', list)],
            'name': 'Certification',
            'res_model': 'inseta.certified.programmes',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        }

    def get_learners_with_selected_programmes(self, learnerObj):
        """This methods ensures the respective programmes with the selected financial year is capture
        This is done to prevent printing empty certificates
        """
        completed_status = self.env.ref('inseta_etqa.id_programme_status_02').id
        if self.programme_type in ['Learnership']:
            learnership_line = learnerObj.mapped('learner_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id \
            and val.learner_programme_id.id == self.learner_programmes_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.learner_programme_id.name, 'nqf_level': learnership_line.learner_programme_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False
        elif self.programme_type in ['Skill']:
            learnership_line = learnerObj.mapped('skill_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.skill_programme_id.id == self.skill_programmes_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.skill_programme_id.name, 'nqf_level': learnership_line.skill_programme_id.nqflevel_id.name, 'res_id': self.id, 'learner_id':  learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        elif self.programme_type in ['Qualification']:
            learnership_line = learnerObj.mapped('qualification_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        elif self.programme_type in ['Internship']:
            learnership_line = learnerObj.mapped('internship_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        elif self.programme_type in ['Candidacy']:
            learnership_line = learnerObj.mapped('candidacy_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        elif self.programme_type in ['Wiltvet']:
            learnership_line = learnerObj.mapped('wiltvet_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        elif self.programme_type in ['Bursary']:
            learnership_line = learnerObj.mapped('bursary_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.bursary_type_id.id == self.bursary_type_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        elif self.programme_type in ['Unit']:
            learnership_line = learnerObj.mapped('unit_standard_learnership_line').filtered(lambda val: val.financial_year_id.id == self.financial_year_id.id and val.unit_standard_id.id == self.unit_standard_id.id and val.programme_status_id.id == completed_status)
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name, 'res_id': self.id, 'learner_id': learnerObj.id, 'provider_id': learnership_line.provider_id.id} if learnership_line else False

        else:
            items = False
            learnership_line = False
        return items
        
    def check_report(self):
        data = {}
        read_docs = self.read(['financial_year_id', 'learner_ids', 'learner_programmes_id', 'programme_type',
            'skill_programmes_id','qualification_id','unit_standard_id','bursary_type_id'])[0] 
        data['form'] = read_docs
        return self._print_report(data)

    def _print_report(self, data):
        read_docs = self.read(['financial_year_id', 'learner_ids', 'learner_programmes_id', 'programme_type',
            'skill_programmes_id','qualification_id','unit_standard_id','bursary_type_id'])[0] 
        data['form'].update(read_docs)
        return self.env.ref('inseta_etqa.batch_learner_certificate_report').report_action(self, data)
 

class BatchLearnerCertificateReport(models.AbstractModel):
    _name = 'report.inseta_etqa.batch_cert'
    _order= "id desc" 
    _description  = "Batch Print Certificate"



    def get_learners_with_selected_programmes(self):
        """This methods ensures the respective programmes with the selected financial year is capture
        This is done to prevent printing empty certificates
        """
        if docs.programme_type in ['Learnership']:
            learnership_line = learnerObj.mapped('learner_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id \
            and val.learner_programme_id.id == docs.learner_programmes_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.learner_programme_id.name, 'nqf_level': learnership_line.learner_programme_id.nqflevel_id.name}
        elif docs.programme_type in ['Skill']:
            learnership_line = learnerObj.mapped('skill_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.skill_programme_id.id == docs.skill_programmes_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.skill_programme_id.name, 'nqf_level': learnership_line.skill_programme_id.nqflevel_id.name}

        elif docs.programme_type in ['Qualification']:
            learnership_line = learnerObj.mapped('qualification_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.qualification_id.id == docs.qualification_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name}

        elif docs.programme_type in ['Internship']:
            learnership_line = learnerObj.mapped('internship_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.qualification_id.id == docs.qualification_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name}

        elif docs.programme_type in ['Candidacy']:
            learnership_line = learnerObj.mapped('candidacy_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.qualification_id.id == docs.qualification_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name}

        elif docs.programme_type in ['Wiltvet']:
            learnership_line = learnerObj.mapped('wiltvet_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.qualification_id.id == docs.qualification_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name}

        elif docs.programme_type in ['Bursary']:
            learnership_line = learnerObj.mapped('bursary_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.bursary_type_id.id == docs.bursary_type_id.id and val.qualification_id.id == self.qualification_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name}

        elif docs.programme_type in ['Unit']:
            learnership_line = learnerObj.mapped('unit_standard_learnership_line').filtered(lambda val: val.financial_year_id.id == docs.financial_year_id.id and val.unit_standard_id.id == docs.unit_standard_id.id and val.programme_status_id.name == "Completed")
            items = {'name': learnership_line.qualification_id.name, 'nqf_level': learnership_line.qualification_id.nqflevel_id.name}

        else:
            learnership_line = False
        return items
    
    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        learneritems = []
        for learnerObj in docs.learner_ids:
            learnership_obj = self.get_learners_with_selected_programmes(learnerObj)
            if learnership_line:
                learneritems.append({'learner': learnerObj, 'learnership_obj': learnership_obj})

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'programme_type': docs.programme_type,
            'learneritems': learneritems,
        }
        return self.env.ref('inseta_etqa.batch_learner_certificate_report').report_action(self, docargs)

        # return self.env['report'].render('inseta_etqa.report_batch_learner_certificate_template_id', docargs)
