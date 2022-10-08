# -*- coding: utf-8 -*-
from xlwt import easyxf, Workbook
import logging
from io import BytesIO
from odoo import models, fields, api
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
from odoo.addons.inseta_tools.validators import validate_said

_logger = logging.getLogger(__name__)


class InsetalproDocument(models.Model):
	_name = "inseta.lpro.document"


class InsetaDgEvaluation(models.Model):
	_inherit = "inseta.dgevaluation"

	lp_data_file = fields.Binary(string="Upload file")
	filename = fields.Char("Filename")
	lpro_id = fields.Many2one("inseta.lpro", string="Learning programming ID")


class InsetaDgApplicationDetails(models.Model):
	_inherit = "inseta.dgapplicationdetails"

	lp_data_file = fields.Binary(string="Upload file")
	filename = fields.Char("Filename")
	lpro_id = fields.Many2one("inseta.lpro", string="Learning programming ID")


class InsetaDgApplicationInherited(models.Model):
	_inherit = "inseta.dgapplication"



class Insetalpro(models.Model):
	_name = 'inseta.lpro'
	_description = "Inseta lpro"
	_order= "id desc"
	_inherit = ['mail.thread'] #, 'mail.activity.mixin', 'rating.mixin']
	_rec_name = "organisation_id"

	"""Upload learners using an excel sheet with headers ,
	 learner Identification, skillprogramme QAQA code, 
	 learning programme QAQA code and qualification QAQA code"""

	def get_employer_default_user(self):
		user = self.env.user.id
		employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
		return employer.id

	sic_code_id = fields.Many2one('res.sic.code', 'SIC Code', store=True)
	sic_code_desc = fields.Char('SIC Code Description',  store=True )
	dgtype_code = fields.Char(string="DG Type code", store=True)
	
	sdf_id = fields.Many2one("inseta.sdf")
	dgapproval_id = fields.Many2one('inseta.dgapproval', string='DG Bulk approval')
	dgrecommend_id = fields.Many2one('inseta.dgrecommendation', string='DG Bulk Recommendation')
	programmetype_id = fields.Many2one('inseta.programme.type', 'Programme type', store=True)
	dgtype_id = fields.Many2one('res.dgtype', 'DG type', store=True)
	due_date = fields.Datetime('Due Date')
	approved_date = fields.Datetime('Approved date')
	approved_by = fields.Many2one('res.users')
	no_learners = fields.Integer(store=True, string="No Learners Applied")
	no_learners_recommended = fields.Integer('No. Learners Recommended', store=True)
	amount_total_recommended =fields.Float(
		'Amt. Recommended', 
		help="Amount in user currency"
	)
	cost_per_student = fields.Float(store=True, string="Cost Per Learner")
	amount_recommended_perlearner = fields.Float('Amt. Recommended Per Learner', 
	)
	no_learners_approved = fields.Integer('No Learners Approved')
	amount_total_approved =fields.Float(
		'Amt. Approved', 
		help="Amount in user currency"
	) 
	organisation_sdl = fields.Char(string='Employer SDL / N', required=True)
	dg_reference = fields.Char(string='DG Application No:', required=False, readonly=True)
	sequence = fields.Char(string='Reference ID', readonly=True)
	organisation_id = fields.Many2one(
		'inseta.organisation', 
		domain="[('state','=','approve')]", 
		required=False, 
		tracking=True, default=lambda s: s.get_employer_default_user())
	active = fields.Boolean(string="Active", default=True)
	learner_ids = fields.One2many('inseta.learner.register', 'lpro_learner_id', string='Learners', required=False)
	programme_id = fields.Many2one('inseta.programme', string='Programme ID', required=False)	
	learning_programming_id = fields.Many2one('inseta.learner.programme', string='Learnership Programme ID', required=False)	
	skills_programming_id = fields.Many2one('inseta.bursary.programme', string='Skills Programme ID', required=False)	
	qualificationid = fields.Many2many("inseta.qualification", string='Qualifications')
	bursary_programme_id = fields.Many2one('inseta.bursary.programme', string='Bursary Programme ID', required=False)	
	learner_id = fields.Many2one('inseta.learner', string="Learner ID")#, compute="_get_learner_lines")
	learnership_ids = fields.Many2many('inseta.learner.programme', 'lpro_learnership_learner_programme_rel', 'column1', string='Learnerships', required=False)	
	skill_ids = fields.Many2many('inseta.learner.programme', 'lpro_skill_learner_programme_rel', 'column1',string='Skills', required=False)	
	qualification_ids = fields.Many2many('inseta.qualification', 'lpro_qualification_learner_programme_rel','column1', string='Qualifications', required=False)	
	bursary_ids = fields.Many2many('inseta.bursary.programme', 'lpro_bursary_learner_programme_rel', 'column1',string='Bursary', required=False)	
	# discard
	qualification_id = fields.Many2many("inseta.qualification", 'inseta_lpro_qualification_rel', 'column1', string='Qualifications')
	qualification_programming_id = fields.Many2one('inseta.qualification.programme', string='Qualification Programme ID', required=False)	
	learning_report_attachment_id = fields.Binary(string="Upload Learning Report") # learning reporting visible to employer
	upload_funding_agreement = fields.Binary(string="Upload Funding Agreement") # learning reporting visible to employer
	financial_year_id = fields.Many2one('res.financial.year', string="Financial year", required=False, store=True)
	dg_application_id = fields.Many2one('inseta.dgapplication', string="DG application", required=False, store=True)
	project_id = fields.Many2one('project.project', string="Project", required=False)
	total_learners = fields.Integer(string='Total learners Recommended', store=True) #, compute="_compute_learners_total_number")
	total_employed_learners = fields.Integer(string='Total of Employed', compute="_compute_learners_employed", store=True)
	total_unemployed_learners = fields.Integer(string='Total of Unemployed', compute="_compute_learners_employed", store=True)
	approved_learners = fields.Integer(string='Approved learners', store=True)
	rework = fields.Boolean(string='Rework')
	verified = fields.Boolean(string='Verified')
	recommend = fields.Boolean(string='Recommended')
	comments = fields.Text(string='Comments')	
	rework_comment = fields.Text()
	rejection_comment = fields.Text()
	# For learner batch upload 
	file_type = fields.Selection(
		[('xlsx', 'XLSX File')], default='xlsx', string='File Type')
	file = fields.Binary(string="Upload File (.xlsx)")
	file_name = fields.Char("Filename")
	overwrite = fields.Boolean("Overwrite Lines")
	import_type = fields.Selection([
			('manual', 'Manual'),
			('system', 'System Generated'),
			('excel', 'Auto Upload'),
		],
		string='Load Type', index=True,
		copy=False, default='manual',
	)
	
	template_type = fields.Selection([
			('bursary', 'Bursary'),
			('skills', 'Skills'),
			('internship', 'Internship'),
			('other', 'Others'),
		],
		string='Template Type', index=True,
		copy=False, default='bursary',
	)

	state = fields.Selection([
		('draft', 'Draft'),
		('Project Admin', 'Project Admin'),
		('Pending Approval', 'Pending Approval'),
		('Learning Specialist', 'Learning Specialist'), # Pending Approval
		('Learning Manager', 'Manager'),
		('COO', 'COO'),
		('CFO', 'CFO'),
		('CEO', 'CEO'),
		('refuse', 'Refused'),
		('done', 'Approved'),
		],string="Status", default="draft")
	
	id_no = fields.Char('Learner Identification ID', store=False)
	inseta_learner_ids = fields.Many2many('inseta.learner', 'lpro_learner_rel', string="Learners", store=True)
	compliant = fields.Selection([('no', 'No'),('yes', 'Yes')], string="Evidence Compliance / Submitted", default="no", store=True)

	agreement_attachment_id = fields.Many2one('ir.attachment', string='Agreement')
	agree_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

	cert_attachment_id = fields.Many2one('ir.attachment', string='Certificate Copy')
	cert_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

	fix_term_contract_attachment_id = fields.Many2one('ir.attachment', string='Fixed term contract')
	fixed_term_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

	popi_act_attachment_id = fields.Many2one('ir.attachment', string='Popi Act Consent')
	popi_act_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

	disability_proof_attachment_id = fields.Many2one('ir.attachment', string='Disability proof')
	disability_proof_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

	internship_agreement_attachment_id = fields.Many2one('ir.attachment', string='internship agreement')
	internship_agreement_compliant = fields.Selection([('no', 'No'),('yes', 'Yes')],  default="no", store=True)

	applicationdetails_ids = fields.One2many(
		'inseta.dgapplicationdetails',
		'lpro_id', 
		string='Application Details',
	)

	learnershipdetails_ids = fields.One2many(
		'inseta.dgapplicationdetails',
		'lpro_id', 
		string='Learnership Details',
	)

	internshipdetails_ids = fields.One2many(
		'inseta.dgapplicationdetails',
		'lpro_id', 
		string='Internship Details',
	)
	burlearnerdetails_ids = fields.One2many(
		'inseta.dgapplicationdetails',
		'lpro_id', 
		string='Bursary Learnership Details',
	)
	splearnerdetails_ids = fields.One2many(
		'inseta.dgapplicationdetails',
		'lpro_id', 
		string='Skills Programme Details',
	)

	evaluation_ids = fields.One2many(
		'inseta.dgevaluation', 
		'lpro_id', 
		'DG Evaluation'
	)

	dg_evaluation_id = fields.Many2one(
		'inseta.dgevaluation', 
		string='DG Evaluation'
	)
	document_ids = fields.Many2many("inseta.learner.document", "lpro_document_ids_rel", string="Learner Documents", compute="compute_uploaded_documents")
	programme_line_ids = fields.One2many(
		'inseta.lp.programe.lines', 
		'lpro_id', 
		'Programme lines'
	)

	@api.depends('inseta_learner_ids')
	def compute_uploaded_documents(self):
		for record in self:
			if record.inseta_learner_ids:
				for rec in record.inseta_learner_ids:
					learner_docs = self.env['inseta.learner.document'].search([('lpro_id','=', record.id)])
					if learner_docs:
						record.document_ids = [(4, doc.id) for doc in learner_docs]
						for rex in record.document_ids:
							rex.state = self.state
					else:
						record.document_ids = False
			else:
				record.document_ids = False

	@api.onchange("id_no")
	def action_add_learner(self):
		if self.id_no:
			existing_learner = self.env['inseta.learner'].search([('id_no', '=', self.id_no)], limit=1)
			if not existing_learner:
				return {
					'warning': {
						'title': "Validation Error!",
						'message': f"Learner with ID No. does not exists"
					}
				}
			else:
				self.id_no = False
				self.update({'inseta_learner_ids': [(4, existing_learner.id)]})

	@api.onchange('organisation_id')
	def _get_related_organisation_dg(self):
		if self.organisation_id:
			self.financial_year_id = False
			self.dg_application_id = False

			dg = self.env['inseta.dgapplication'].search([
				('organisation_id', '=', self.organisation_id.id), ('state', 'in', ['approve', 'signed'])])
			if dg:
				self.organisation_sdl = self.organisation_id.sdl_no
				return {
					'domain': {
						'financial_year_id': [('id', 'in', [rec.financial_year_id.id for rec in dg])] if dg else [('id', 'in', None)]
					},
				}
			else:
				return {
					'warning': {
						'title': "Validation Error!",
						'message':"No DG found for this Employer !"
					},
					'domain': {
						'financial_year_id': [('id', '=', None)]
					}
				} 

	@api.onchange('organisation_sdl')
	def _get_related_dg(self):
		if self.organisation_sdl:
			self.financial_year_id = False
			self.dg_application_id = False
			dg = self.env['inseta.dgapplication'].search([('sdl_no', '=', self.organisation_sdl), ('state', 'in', ['approve', 'signed'])])
			if dg:
				self.organisation_id = dg[0].organisation_id.id
				return {
					'domain': {
						'financial_year_id': [('id', 'in', [rec.financial_year_id.id for rec in dg])] if dg else [('id', 'in', None)]
					}
				}
			else:
				return {
					'warning': {
						'title': "Validation !!!",
						'message':"No DG found for this Employer"
					},
					'domain': {
						'financial_year_id': [('id', '=', None)]
					}
				}
		else:
			self.set_fields_to_none() 

	@api.onchange('financial_year_id')
	def _onchange_financial_year(self):
		if self.organisation_sdl:
			self.dg_application_id = False
			self.set_fields_to_none()
			dg = self.env['inseta.dgapplication'].search([
				('financial_year_id', '=', self.financial_year_id.id),
				('organisation_id', '=', self.organisation_id.id), 
				('state', 'in', ['approve', 'signed'])
				])
			
			return {
					'domain': {
						'dg_application_id': [('id', 'in', [rec.id for rec in dg])] if dg else [('id', 'in', None)]
					}
				}
		else:
			return {
					'domain': {
						'dg_application_id': [('id', 'in', None)]
					}
				}

	@api.onchange('dg_application_id')
	def compute_dg_details(self):
		if self.dg_application_id:
			self.write({
				'applicationdetails_ids': self.dg_application_id.applicationdetails_ids.ids, 
				'learnershipdetails_ids': self.dg_application_id.learnershipdetails_ids.ids, 
				'internshipdetails_ids': self.dg_application_id.internshipdetails_ids.ids,
				'burlearnerdetails_ids': self.dg_application_id.burlearnerdetails_ids.ids,
				'splearnerdetails_ids': self.dg_application_id.splearnerdetails_ids.ids,
				# 'evaluation_ids': self.dg_application_id.evaluation_ids.ids,
			})
			# if self.learnershipdetails_ids:
			# 	self.learnership_ids = [(6, 0, [rec.learnership_id.id for rec in self.mapped('learnershipdetails_ids')])]
			dg = self.dg_application_id
			self.sic_code_desc = dg.sic_code_desc
			self.due_date = dg.due_date
			self.approved_date = dg.approved_date
			self.no_learners = dg.total_learners
			self.no_learners_approved = dg.no_learners_approved
			self.amount_total_approved = dg.amount_total_approved
			self.sdf_id = dg.sdf_id.id
			self.dgapproval_id = dg.dgapproval_id.id
			self.dgtype_id = dg.dgtype_id.id
			self.dgtype_code = dg.dgtype_code
			return {
					'domain': {
						'dg_evaluation_id': [('id', 'in', dg.evaluation_ids.ids)] if dg else [('id', 'in', None)]
					}
				}
		else:
			self.set_fields_to_none()
			return {
					'domain': {
						'dg_evaluation_id': [('id', 'in', None)]
					}
				}

	@api.onchange('dg_evaluation_id')
	def onchange_dg_evaluation_id(self):
		if self.dg_evaluation_id:
			existing_related_lps = self.search_count([
				('dg_evaluation_id', '=', self.dg_evaluation_id.id),
				# ('state', '=', 'draft'),
				])
			if existing_related_lps:
				raise ValidationError('You have already used this DG approval No. Kindly locate and continue the process')
			self.write({'evaluation_ids': [(6, 0, [self.dg_evaluation_id.id])]})
		else:
			self.set_fields_to_none()

	def set_fields_to_none(self):
		self.write({
				'applicationdetails_ids': False,
				'learnershipdetails_ids': False,
				'internshipdetails_ids': False,
				'burlearnerdetails_ids': False,
				'splearnerdetails_ids': False,
				'evaluation_ids': False,
				'dg_evaluation_id': False,
			})
		self.sic_code_desc = False
		self.due_date =False
		self.approved_date = False
		self.no_learners = False
		self.no_learners_approved = False
		self.amount_total_approved = False
		self.sdf_id = False
		self.dgapproval_id = False
		self.dgtype_id = False
		self.dgtype_code = False
		 
	def check_updated_learners(self):
		for rec in self:
			if not rec.inseta_learner_ids:
				raise ValidationError('Learners must be captured before submitting')
			# learner_docs = [lrn.learner_document2_id.id for lrn in rec.mapped('document_ids')]
			# """learner_document2_id is pointing to inseta.learner"""
			programme_line_learner_ids = [
				lrn.learner_id.id for lrn in rec.mapped('programme_line_ids')
				]
			for learn in rec.inseta_learner_ids:
				if learn.id not in programme_line_learner_ids:
					raise ValidationError(f'Please register at least a programme for this learner [{learn.id_no} - {learn.name}]')
					 
	@api.constrains('learner_ids')
	def _validate_learner_programme(self):
		pass 
		count_programme = 0
		num_of_learners = 0
		learner_prog_list = []
		learner_dict = {}
		learners = self.mapped('learner_ids')
		learnership_ids = [prog.learnership_id.id for prog in self.dg_application_id.mapped('learnershipdetails_ids')]
		for lrn in learners:
			lrn_learnership = lrn.mapped('learner_learnership_line').filtered(lambda gt: gt.learner_programme_id.id in learnershipdetails_ids)
			if lrn_learnership:

				num_of_learners = sum([prog.number_of_learners for prog in self.dg_application_id.mapped('learnershipdetails_ids').filtered(lambda pr: pr.learnership_id.id in [prog.learner_programme_id.id for prog in lrn.mapped('learner_learnership_line')])])
				count_programme += 1
				learner_prog_list.append({'learner': lrn.id_no, 'programme': lrn_learnership[0].learner_programme_id.name})
		if count_programme > num_of_learners:
			raise ValidationError("Sorry...the following learners have programmes that have exceeded number of applied programme\
			 for the DG\n {}".format(',\n'.join([vals.get('learner') +': '+vals.get('programme') for vals in learner_prog_list]))
			)
		
	def _compute_learners_employed(self):
		for rec in self:
			employed = len([rec.id for rec in self.mapped('learner_ids').filtered(lambda emp: emp.socio_economic_status_id.name == 'Employed')])
			unemployed = len([rec.id for rec in self.mapped('learner_ids').filtered(lambda emp: emp.socio_economic_status_id.name != 'Employed')])
			rec.total_employed_learners = employed
			rec.total_unemployed_learners = unemployed
	
	def action_reset_to_draft(self): 
		self.write({'state': 'draft'})

	def action_submit(self): # Employer uses to submit application
		self.check_updated_learners()
		if self.state == "draft":
			self.activity_update()
		if self.state == "Pending Approval":
			proj_admin, learn_spec_users, lmanager_users, coo_users, cfo_users, ceo_users = self._get_group_users()
			proj_admin = [rec.login for rec in proj_admin]
			learn_spec_users = [rec.login for rec in learn_spec_users]
			lmanager_users = [rec.login for rec in lmanager_users]
			all_follower_login = proj_admin + learn_spec_users + lmanager_users 
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_followers_for_rework_submit'
			self.action_send_mail(MAIL_TEMPLATE, all_follower_login, None) 
		self.write({'state': 'Project Admin'})

	def validate_documents(self):
		learner_not_validated = ["The following learners with ID's document is not compliant"]
		for rec in self.inseta_learner_ids:
			if not rec.document_ids:
				learner_not_validated.append(rec.id_no)
			else:
				not_compliant_documents = rec.mapped('document_ids').filtered(lambda s: s.compliant != 'yes')
				if not_compliant_documents:
					learner_not_validated.append(rec.id_no)
		if len(learner_not_validated) > 1:
			msg = ',\n'.join(learner_not_validated)
			raise ValidationError(msg)

	def action_padmin_to_learning_specialist(self):
		# self.validate_documents()
		if self.compliant == 'yes' or not self.mapped('document_ids').filtered(lambda s: s.compliant == "no"):
			self.activity_update()
			self.write({'state': 'Learning Specialist', 'verified': True})
		else:
			raise ValidationError('All documents must be compliant before submission / Approval')

	def action_learning_specialist_to_learning_manager(self):
		if self.compliant != "yes":
			raise ValidationError("Please select evidence compliant as Yes before recommending !!!")
		self.activity_update()
		self.write({'state': 'Learning Manager', 'recommend': True})

	def action_learning_manager_to_coo(self):
		self.activity_update()
		self.write({'state': 'done'})
		# self.write({'state': 'COO'})
	
	def action_coo_to_cfo(self):
		self.activity_update()
		self.write({'state': 'CFO'})

	def action_cfo_to_ceo(self):
		self.activity_update()
		self.write({'state': 'CEO'})

	def action_ceo_to_done(self):
		self.activity_update()
		self.write({'state': 'done'})

	# def get_designated_funding_agreement_template(self):
	# 	internship_template = "inseta_learning_programme.internship_funding_agreement_report"
	# 	learnership_template = "inseta_learning_programme.learning_funding_agreement_report"
	# 	rural_learnership_template = "inseta_learning_programme.learning_rural_funding_agreement_report"
	# 	worker_learnership_template = "inseta_learning_programme.learning_worker_funding_agreement_template"
	# 	youth_learnership_template = "inseta_learning_programme.learning_youth_funding_agreement_report"
	# 	template_name = None 
	# 	learning_learnership = ['LRN-Y','LRN-D', 'LRN']
	# 	rural_learning_learnership = ['LRN-R']
	# 	worker_learning_learnership = ['LRN-W']
	# 	internship_learnership = ['IT-DEGREE','IT-MATRIC', 'INT']

	# 	if self.dgtype_code in learning_learnership:
	# 		template_name = youth_learnership_template

	# 	elif self.dgtype_code in rural_learning_learnership:
	# 		template_name = rural_learnership_template

	# 	elif self.dgtype_code in worker_learning_learnership:
	# 		template_name =  worker_learnership_template

	# 	elif self.dgtype_code in internship_learnership:
	# 		template_name =  internship_template

	# 	return template_name
		 
	def action_view_funding_agreement(self):
		self.ensure_one()
		# switch offer letter type to pdf
		internship_template = "inseta_learning_programme.internship_funding_agreement_report"
		learnership_template = "inseta_learning_programme.learning_funding_agreement_report"
		rural_learnership_template = "inseta_learning_programme.learning_rural_funding_agreement_report"
		worker_learnership_template = "inseta_learning_programme.learning_worker_funding_agreement_report"
		youth_learnership_template = "inseta_learning_programme.learning_youth_funding_agreement_report"
		template_name = None 
		learning_learnership = ['LRN-Y','LRN-D', 'LRN']
		rural_learning_learnership = ['LRN-R']
		worker_learning_learnership = ['LRN-W']
		internship_learnership = ['IT-DEGREE','IT-MATRIC', 'INT']

		if self.dgtype_code in learning_learnership:
			template_name = youth_learnership_template

		elif self.dgtype_code in rural_learning_learnership:
			template_name = rural_learnership_template

		elif self.dgtype_code in worker_learning_learnership:
			template_name =  worker_learnership_template

		elif self.dgtype_code in internship_learnership:
			template_name =  internship_template
		if not template_name:
			raise ValidationError("Template have not been configured for the request DG TYPE")

		report_template = self.env.ref(template_name)
		report = self.env['ir.actions.report'].search([('report_name', '=', template_name)], limit=1)
		if report:
			report.write({'report_type': 'qweb-pdf'})
		return report_template.report_action(self)

	def action_send_funding_agreement(self):
		self.ensure_one()
		# workerprogrammes@inseta.org.za
		learnership_mail_template = "mail_template_send_learnership_funding_agreement"
		internship_mail_template = "mail_template_send_internship_funding_agreement"

		internship_template = "inseta_learning_programme.internship_funding_agreement_report"
		learnership_template = "inseta_learning_programme.learning_funding_agreement_report"
		rural_learnership_template = "inseta_learning_programme.learning_rural_funding_agreement_report"
		worker_learnership_template = "inseta_learning_programme.learning_worker_funding_agreement_report"
		youth_learnership_template = "inseta_learning_programme.learning_youth_funding_agreement_report"
		learning_learnership = ['LRN-Y','LRN-D', 'LRN']
		rural_learning_learnership = ['LRN-R']
		worker_learning_learnership = ['LRN-W']
		internship_learnership = ['IT-DEGREE','IT-MATRIC', 'INT']
		learnership_mail_template_ref = self.env.ref('inseta_learning_programme.mail_template_send_learnership_funding_agreement')
		internship_mail_template_ref = self.env.ref('inseta_learning_programme.mail_template_send_internship_funding_agreement')

		if self.dgtype_code in learning_learnership:
			mail_template = learnership_mail_template
			youth_learnership_template_ref = self.env.ref(youth_learnership_template)
			learnership_mail_template_ref.write({'report_template': youth_learnership_template_ref.id})

		elif self.dgtype_code in rural_learning_learnership:
			mail_template = learnership_mail_template
			rural_learnership_template_ref = self.env.ref(rural_learnership_template)
			learnership_mail_template_ref.write({'report_template': rural_learnership_template_ref.id})

		elif self.dgtype_code in worker_learning_learnership:
			mail_template = learnership_mail_template
			worker_learnership_template_ref = self.env.ref(worker_learnership_template)
			learnership_mail_template_ref.write({'report_template': worker_learnership_template_ref.id})

		elif self.dgtype_code in internship_learnership:
			mail_template = internship_mail_template
			internship_template_ref = self.env.ref(internship_template)
			internship_mail_template_ref.write({'report_template': internship_template_ref.id})

		# else:
		# 	mail_template = learnership_mail_template
		# 	worker_learnership_template_ref = self.env.ref(worker_learnership_template)
		# 	mail_template_ref.write({'report_template': worker_learnership_template_ref.id})
		 
		MAIL_TEMPLATE = mail_template
		employer_email = [self.organisation_id.email or self.organisation_id.user_id.login]
		self.action_send_mail(MAIL_TEMPLATE, employer_email, None) 

	def _message_post(self, template):
		"""Wrapper method for message_post_with_template
		Args:
			template (str): email template
		"""
		if template:
			ir_model_data = self.env['ir.model.data']
			template_id = ir_model_data.get_object_reference('inseta_learning_programme', template)[1]         

			self.message_post_with_template(
				template_id, composition_mode='comment',
				model=f'{self._name}', res_id=self.id,
				email_layout_xmlid='mail.mail_notification_light',
			)

	def rework_registration(self, comment):
		proj_admin, learn_spec_users, lmanager_users, coo_users, cfo_users, ceo_users = self._get_group_users()
		proj_admin = [rec.login for rec in proj_admin] if proj_admin else ""
		lmanager_users = [rec.login for rec in lmanager_users]
		if self.state == "Project Admin":
			EMPLOYER_MAIL_TEMPLATE = "mail_template_notify_learning_programme_employer_rework"
			employer_login = self.organisation_id.email or self.organisation_id.user_id.login
			self.action_send_mail(EMPLOYER_MAIL_TEMPLATE, [employer_login], None) 
			self._message_post(EMPLOYER_MAIL_TEMPLATE) # notify sdf
			self.write({
				'state': 'draft', 
				'rework_comment': comment, 
			})
			
		if self.state == "Learning Specialist":
			MAIL_TEMPLATE = "mail_template_notify_learning_programme_followers_rework"
			self.action_send_mail(MAIL_TEMPLATE, proj_admin, None) 
			self._message_post(MAIL_TEMPLATE) # notify sdf
			self.write({
				'state': 'Project Admin', 
				'rework_comment': comment, 
			})

		if self.state == "Learning Manager":
			recipients = lmanager_users + proj_admin
			MAIL_TEMPLATE = "mail_template_notify_learning_programme_followers_rework"
			self.action_send_mail(MAIL_TEMPLATE, recipients, None) 
			self._message_post(MAIL_TEMPLATE) # notify sdf
			self.write({
				'state': 'Learning Specialist', 
				'rework_comment': comment, 
			})

		# raise ValidationError(self.state)
		# self.activity_update()

	def action_rework(self):
		return self.popup_notification(False, 'query') 

	def action_reject(self):
		return self.popup_notification(False, 'refusal') 

	def popup_notification(self, subject, action):
		self.write({'comments': '', 'rework_comment': ''})
		view = self.env.ref('inseta_learning_programme.inseta_lpro_reject_wizard_form_view')
		view_id = view and view.id or False
		context = {
					'default_subject': subject, 
					'default_date': fields.Date.today(),
					'default_reference': self.id,
					'default_action': action,
					'default_model_name': self._name,
					}
		return {'name':'Dialog',
					'type':'ir.actions.act_window',
					'view_type':'form',
					'res_model':'inseta.lpro.main.wizard',
					'views':[(view.id, 'form')],
					'view_id':view.id,
					'target':'new',
					'context':context,
				}

	def action_learner_wizard(self):
		view = self.env.ref('inseta_learning_programme.inseta_lpro_register_learner_wizard_form_view')
		view_id = view and view.id or False
		context = {
					'default_action': "upload_id", 
					'default_reference': self.id,
					'default_organisation_sdl': self.organisation_sdl,
					'default_dgtype_code': self.dgtype_code,
					
					}
		return {'name':'Dialog',
					'type':'ir.actions.act_window',
					'view_type':'form',
					'res_model':'inseta.lpro.register.learner.wizard',
					'views':[(view.id, 'form')],
					'view_id':view.id,
					'target':'new',
					'context':context,
				}

	def action_add_programme(self):
		if not self.learner_id:
			raise ValidationError('Please select a learner to register a programme')
		view = self.env.ref('inseta_etqa.inseta_programme_register_learner_wizard_form_view')
		view_id = view and view.id or False
		learning_learnership = ['LRN-Y','LRN-D', 'LRN']
		rural_learning_learnership = ['LRN-R']
		worker_learning_learnership = ['LRN-W']
		internship_learnership = ['IT-MATRIC', 'INT']
		internship_degree_learnership = ['IT-DEGREE']
		bursary_learnership= ['BUR']
		skill_learnership= ['SP']
		programme_type = "Learnership"
		if self.dgtype_code in internship_learnership:
			programme_type = "Internship"

		elif self.dgtype_code in internship_degree_learnership or self.dgtype_id.name.startswith('Internship Diploma/Degree'):
			programme_type = "Internship-diploma-degree"

		elif self.dgtype_code in bursary_learnership and self.dgtype_id.name.startswith('Bursaries for Workers'):
			programme_type = "Bursary-W"

		elif self.dgtype_code in bursary_learnership and not self.dgtype_id.name.startswith('Bursaries for Workers'):
			programme_type = "Bursary"

		elif self.dg_evaluation_id.name.startswith('SPY'):
			programme_type = "Skill"

		elif self.dgtype_code in skill_learnership and self.dg_evaluation_id.name.startswith('SPW') or self.dgtype_id.name.startswith('Skills Programmes for Workers'):
			programme_type = "Skill-W"

		elif self.dgtype_code.startswith('SPW') or self.dgtype_id.name.startswith('Skills Programmes for Workers'):
			programme_type = "Skill-W"

		elif self.dgtype_code in rural_learning_learnership or self.dgtype_id.name.startswith('Learnership for Rural Learners'):
			programme_type = "Learnership-Rural"

		elif self.dgtype_code in worker_learning_learnership or self.dgtype_id.name.startswith('Learnership for Workers'):
			programme_type = "Learnership-Worker"

		elif self.dgtype_code in learning_learnership or self.dgtype_id.name.startswith('Learnerships for Youth (including PwD)'):
			programme_type = "Learnership"

		else:
			programme_type = "Learnership"
		
		context = {
					'default_learner_id': self.learner_id.id, 
					'default_learner_id_no': self.learner_id.id_no,
					'default_dgtype_code': self.dgtype_code,
					'default_financial_year_id': self.financial_year_id.id,
					'default_is_from_lp': 'LP',
					'default_dg_number': self.dg_evaluation_id.name,
					'default_programme_type': programme_type,
					'default_lpro_id': self.id,
					}
		return {'name':'Register Programme',
					'type':'ir.actions.act_window',
					'view_type':'form',
					'res_model':'inseta.programme.register',
					'views':[(view.id, 'form')],
					'view_id':view.id,
					'target':'new',
					'context':context,
				}

	def action_validate_learner_document(self):
		self.compliant = 'no'
		view = self.env.ref('inseta_learning_programme.inseta_lpro_register_learner_wizard_form_view')
		view_id = view and view.id or False
		context = {
					'default_action': 'doc_validity', 
					'default_reference': self.id,
					'default_state': self.state,
					'default_dgtype_id': self.dgtype_id.id,
					'default_organisation_sdl': self.organisation_sdl,
					'default_document_validation': True,
					'default_dgtype_code': self.dgtype_code,
					}
		return {'name':'Dialog',
					'type':'ir.actions.act_window',
					'view_type':'form',
					'res_model':'inseta.lpro.register.learner.wizard',
					'views':[(view.id, 'form')],
					'view_id':view.id,
					'target':'new',
					'context':context,
				}

	def action_send_mail(self, with_template_id, email_items= None, email_from=None):
		'''args: email_items = [lists of emails]'''
		# email_items = list(filter(bool, email_items))
		email_to = (','.join([m for m in list(filter(bool, email_items))])) if email_items else False
		ir_model_data = self.env['ir.model.data']
		template_id = ir_model_data.get_object_reference('inseta_learning_programme', with_template_id)[1]         
		if template_id:
			ctx = dict()
			ctx.update({
				'default_model': f'{self._name}',
				'default_res_id': self.id,
				'default_use_template': bool(template_id),
				'default_template_id': template_id,
				'default_composition_mode': 'comment',
			})
			template_rec = self.env['mail.template'].browse(template_id)
			if email_to:
				template_rec.write({'email_to': email_to})
			template_rec.with_context(ctx).send_mail(self.id, True)

	def _get_group_users(self):
		group_obj = self.env['res.groups']
		project_admin = self.env.ref('inseta_dg.group_pmo_admin').id
		learn_spec = self.env.ref('inseta_learning_programme.group_learning_specialist_id').id
		learn_manager = self.env.ref('inseta_learning_programme.group_learning_manager_id').id
		coo_group_id = self.env.ref('inseta_dg.group_coo').id
		cfo_group_id = self.env.ref('inseta_learning_programme.group_learning_programme_cfo_id').id
		ceo_group_id = self.env.ref('inseta_dg.group_ceo').id
		padmin = group_obj.browse([project_admin])
		learnspecialist = group_obj.browse([learn_spec])
		lmanager = group_obj.browse([learn_manager])
		coo = group_obj.browse([coo_group_id])
		cfo = group_obj.browse([cfo_group_id])
		ceo = group_obj.browse([ceo_group_id])

		proj_admin, learn_spec_users, lmanager_users, coo_users,cfo_users,ceo_users = \
		False, False, False, False, False, False
		if padmin:
			proj_admin = padmin.mapped('users')

		if learnspecialist:
			learn_spec_users = learnspecialist.mapped('users') 

		if lmanager:
			lmanager_users = lmanager.mapped('users') 

		if coo:
			coo_users = coo.mapped('users') 

		if cfo:
			cfo_users = cfo.mapped('users') 

		if ceo:
			ceo_users = ceo.mapped('users') 
		return proj_admin, learn_spec_users, lmanager_users, coo_users, cfo_users, ceo_users

	def activity_update(self):
		"""Updates the chatter and send neccessary email to followers or respective groups
		"""
		proj_admin, learn_spec_users, lmanager_users, coo_users, cfo_users, ceo_users = self._get_group_users()
		proj_admin = [rec.login for rec in proj_admin] if proj_admin else ""
		lmanager_users = [rec.login for rec in lmanager_users]

		learn_spec_users = [rec.login for rec in learn_spec_users]
		coo_users = [rec.login for rec in coo_users]
		cfo_users = [rec.login for rec in cfo_users]
		ceo_users = [rec.login for rec in ceo_users]
		learner_reciepients = [rec.email for rec in self.mapped('learner_ids')]
		employer_login = self.organisation_id.email or self.organisation_id.user_id.login
		employer_email = [employer_login]
		all_follower_login = proj_admin + learn_spec_users + lmanager_users 
		# send to registrants
		EMPLOYER_MAIL_TEMPLATE = "mail_template_notify_learning_programme_employer_after_registration" 
		MAIL_TEMPLATE = False
		if self.state == 'draft':
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_project_admin'
			self.action_send_mail(EMPLOYER_MAIL_TEMPLATE, employer_email, None) 
			self.action_send_mail(MAIL_TEMPLATE, proj_admin, None) 

		if self.state == 'Project Admin':
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_specialist'
			self.action_send_mail(MAIL_TEMPLATE, None, None) 

		if self.state == 'Learning Specialist':
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_manager'
			self.action_send_mail(MAIL_TEMPLATE, None, None) 

		if self.state == 'Learning Manager':
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_coo'
			self.action_send_mail(MAIL_TEMPLATE, None, None) 

		if self.state == 'COO':
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_cfo'
			self.action_send_mail(MAIL_TEMPLATE, None, None) 

		if self.state == 'CFO':
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_ceo'
			self.action_send_mail(MAIL_TEMPLATE, None, None) 

		if self.state == 'CEO':
			all_reciepients = learner_reciepients.append(employer_email)
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_all'
			self.action_send_mail(MAIL_TEMPLATE, None, None) 

		if self.state in ["Project Admin", "Learning Manager"]:
			EMPLOYER_MAIL_TEMPLATE = "mail_template_notify_to_employer_after_approval"
			MAIL_TEMPLATE = 'mail_template_notify_to_employer_after_approval'
			# MAIL_TEMPLATE = 'mail_template_notify_learning_programme_followers_rework'
			self.action_send_mail(EMPLOYER_MAIL_TEMPLATE, employer_email, None) 
			self.action_send_mail(MAIL_TEMPLATE, all_follower_login, None) 

		if self.state in ["Pending Approval"]:
			EMPLOYER_MAIL_TEMPLATE = "mail_template_notify_learning_programme_employer_rework"
			MAIL_TEMPLATE = 'mail_template_notify_learning_programme_followers_rework'
			# MAIL_TEMPLATE = 'mail_template_notify_learning_programme_followers_rework'
			self.action_send_mail(EMPLOYER_MAIL_TEMPLATE, employer_email, None) 
			self.action_send_mail(MAIL_TEMPLATE, all_follower_login, None) 

		self._message_post(MAIL_TEMPLATE) #notify sdf

	def action_view_learners(self): 
		form_view_ref = self.env.ref('inseta_etqa.view_learner_form', False)
		tree_view_ref = self.env.ref('inseta_etqa.view_learner_tree', False) 
		search_view_ref = self.env.ref('inseta_etqa.view_learner_tree', False) 
		if self.inseta_learner_ids:
			return {
				'domain': [('id', 'in', [learn.id for learn in self.inseta_learner_ids])],
				'name': 'Learners',
				'res_model': 'inseta.learner',
				'type': 'ir.actions.act_window',
				'views': [(tree_view_ref.id, 'tree'),(form_view_ref.id, 'form')], 
				'search_view_id': search_view_ref and search_view_ref.id,
			}
		else:
			raise ValidationError('No Learner record added!!!') 

	def read_file(self, index=0):
		if not self.file:
			raise ValidationError('Please select a file')

		file_datas = base64.decodestring(self.file)
		workbook = open_workbook(file_contents=file_datas)
		sheet = workbook.sheet_by_index(index)
		file_data = [[sheet.cell_value(r, c) for c in range(
			sheet.ncols)] for r in range(sheet.nrows)]
		file_data.pop(0)
		file_data.pop(1)
		return file_data
	
	# def load_excel_learnersz(self):
	# 	file_data = self.read_file()
	# 	for count, row in enumerate(file_data): 
	# 		learner_line = self.env['inseta.learner']
	# 		reg_no = row[0] 
	# 		identification_no = row[1]
	# 		programme_code = row[2]
	# 		learner_id = self.env['inseta.learner'].search(['|', ('id_no', '=', identification_no), ('registration_no', '=', reg_no)], limit=1)
	# 		learner_progrm = self.env['inseta.learner.programme'].search([('programme_code', '=', programme_code)], limit=1)
	# 		skill_progrm = self.env['inseta.skill.programme'].search([('programme_code', '=', programme_code)], limit=1)
	# 		qual_progrm = self.env['inseta.qualification.programme'].search([('programme_code', '=', programme_code)], limit=1)
	# 		vals = dict(
	# 			learner_id = learner_id.id, 
	# 			learning_programming_id = learner_progrm.id, 
	# 			skills_programming_id = skill_progrm.id, 
	# 			qualification_programming_id = qual_progrm.id, 
	# 			lpro_id = self.id,
	# 			)
	# 		if learner_id:
	# 			learner_line.create(vals)

	def action_import_learners(self):
		if self.import_type == "system":
			organisation_sdf = self.env['inseta.sdf.organisation'].search([('organisation_id', '=', self.organisation_id.id)], limit=1)
			provider_id = self.env['inseta.provider'].search([('organisation_id', '=', organisation_sdf.id)], limit=1)
			related_learners = self.env['inseta.learner'].search(['|', ('provider_id', '=', provider_id.id), ('create_uid', '=', self.env.user.id)])
			for rec in related_learners:
				self.learner_ids = [(4, self.id)]

		elif self.import_type == "excel":
			self.load_excel_learners()

		else:
			raise ValidationError('You can only add learners maually if the import type is in excel or system generated')

	def clear_learners_action(self):
		self.learner_ids = False
				

	def validate_id_number(self, id_number):
		if type(id_number) in [int, float]:
			id_number = int(id_number)
		id_number = str(id_number).strip()
		return id_number

	def validate_phone_fax_number(self, number):
		if type(number) in [int, float]:
			number = int(number)
		if type(number) == str:
			number = number.split('.')[0]
		number = str(number).strip()
		return number

	def get_genders(self, gender_value):
		gender = ''
		if gender_value in ['M', 'm', 'Male', 'male']:
			gender_id = self.env['res.gender'].search([('name', 'like', 'male')], limit=1)
			gender = gender_id.id

		if gender_value in ['F', 'f', 'Female', 'female']:
			gender_id = self.env['res.gender'].search([('name', 'like', 'female')], limit=1)
			gender = gender_id.id
		return gender
	
	def get_value_id(self, model, value):
		name = "" if not value else value
		value_id = self.env[f'{model}'].search([('name', 'like', value)], limit=1)
		return value_id.id
 
	def validate_rsa_number(self, id_no):
		"""Update gender and birth_date fields on validation of R.S.A id_no"""
		if id_no and type(id_no) in [str]:
			original_idno = id_no
			identity = validate_said(id_no)
			if not identity:
				return False#, f"Invalid R.S.A Identification No. {original_idno}"
			else:
				return identity
				# identity.get('dob'), 'Male' if identity.get("gender") == 'male' else 'Female'
			return True
		else:
			return False 



	def validate_date(self,date_str):

		"""
		Rearranges date if the provided date and month is misplaced 
			:param date_str is date in format mm/dd/yy
			:return date string 'Y-m-d'

		"""
		if not date_str or type(date_str) is not str:
			return False
		
		data = date_str.split('/')
		if len(data) > 2:
			try:
				mm, dd, yy = int(data[0]), int(data[1]), data[2]
				if mm > 12: #eg 21/04/2021" then reformat to 04/21/2021"
					dd, mm = mm, dd
				if mm > 12 or dd > 31 or len(yy) != 4:
					return False
				return "{}-{}-{}".format(yy, mm, dd)
			except Exception as e:
				_logger.exception(e)
				return False

	def load_excel_learners(self):
		file_data = self.read_file()[1:]
		error = ['Notification: ']
		for count, row in enumerate(file_data):
			if self.template_type == "bursary":
				id_num = str(row[0]) if row[0] else "-"
				gender = False 
				dob = False 
				err_message = False
				identity = self.validate_rsa_number(id_num)
				if identity:
					gender = 'Male' if identity.get("gender") == 'male' else 'Female' # rsa_number[2]
					dob = identity.get('dob'),  #rsa_number[1]
				else:
					error.append(f'Learner with {id_num} was not imported: RSA Number not found')

				organisation_sdf = self.env['inseta.sdf.organisation'].search([('organisation_id', '=', self.organisation_id.id)], limit=1)
				provider_ref = self.env['inseta.provider'].search([('organisation_id', '=', organisation_sdf.id)], limit=1)
				provider_sdl_no = row[37]
				employer_sdl_no = row[38]
				start_date = self.validate_date(row[39])
				end_date = datetime.strptime(row[40], '%d/%m/%Y') # self.validate_date(str(row[40]))
				provider_id = self.record_reference_for_import('inseta.provider', 'employer_sdl_no', provider_sdl_no) or provider_ref
				organisation_id = self.record_reference_for_import('inseta.organisation', 'employer_sdl_no', employer_sdl_no) or organisation_sdf
				financial_year_id = self.get_value_id('res.financial.year', row[43])
				qualification_saqa_id = row[44]
				nqflevel_id = self.get_value_id('res.nqflevel', row[45])
				ofo_id = self.get_value_id('res.ofo.occupation', row[46])
				institution = self.get_value_id('res.dgpublicprovider', row[48]) # Institution
				publicprovider_id = institution
				if not provider_id:
					error.append(f'Learner with {id_num} was not imported. Reason: No provider with SDL Number {provider_sdl_no} found. ')
				vals = dict(
					id_no = id_num, # self.validate_rsa_number(id_num),
					alternateid_type_id = self.get_value_id('res.alternate.id.type', row[1]),
					title = self.get_value_id('res.partner.title', row[2]),  # name
					first_name=row[3],
					middle_name=row[4],
					last_name=row[5],
					name = f"{row[3]} {row[4]} {row[5]}",
					initials = row[6],
					birth_date = self.validate_date(row[7]), # row[8].split(" ")[0],
					gender_id =  self.get_value_id('res.gender', row[8]) or dob,
					equity_id = self.get_value_id('res.equity', row[9]),
					disability_id = self.get_value_id('res.disability', row[10]),
					home_language_id = self.get_value_id('res.lang', row[11]),
					nationality_id = self.get_value_id('res.nationality', row[12]),
					citizen_resident_status_id = self.get_value_id('res.citizen.status', row[13]),
					phone = self.validate_phone_fax_number(row[14]), 
					mobile = self.validate_phone_fax_number(row[15]),#int(row[17]) if isinstance(row[17], float) else row[17],
					fax_number = self.validate_phone_fax_number(row[16]),
					email = row[17],
					physical_code = row[18] if row[18] else "",
					physical_address1 = row[19], # Physical Address Line 1
					physical_address2 = row[20], # Physical Address Line 2
					physical_address3 = row[21], # Physical Address Line 3
					physical_municipality_id = self.get_value_id('res.municipality', row[22]),
					physical_urban_rural = 'Urban' if row[23] == "Urban" else "Rural",
					physical_province_id = self.get_value_id('res.country.state', row[24]),
					postal_code = row[25],
					postal_address1 = row[26],
					postal_address2 = row[27],
					postal_address3 = row[28],
					postal_municipality_id = self.get_value_id('res.municipality', row[29]),
					postal_urban_rural = 'Urban' if row[30] == "Urban" else "Rural",
					postal_province_id = self.get_value_id('res.country.state', row[31]),
					school_emis_id = self.get_value_id('res.school.emis', row[32]),
					statssa_area_code_id = self.get_value_id('res.statssa.area.code', row[34]),
					popi_act_status_id = self.get_value_id('res.popi.act.status', row[35]),
					popi_act_status_date = self.validate_date(row[36]),
					provider_id = provider_id.id,  # 37
					socio_economic_status_id = self.get_value_id('res.socio.economic.status', row[41]),
					funding_type = self.get_value_id('res.fundingtype', row[42]),
					lpro_learner_id = self.id,
					)
				learner_obj = self.env['inseta.learner.register']
				learner_ref = learner_obj.search([('id_no', '=', id_num)], limit=1)
				learner_id = False
				if not learner_ref:
					learner_id = learner_obj.create(vals)
				else:
					learner_ref.write(vals)
					learner_id = learner_ref
				# raise ValidationError(f'{start_date} and {type(row[40])}')
				bursary_details = dict(
					organisation_id = organisation_id.id,
					provider_id = provider_id.id,
					financial_year_id = financial_year_id,
					publicproviderother = row[48],
					qualification_saqaid = qualification_saqa_id,
					nqflevel_id = nqflevel_id,
					start_date = start_date,
					end_date = end_date,
				)
				dgbursary_detail_id = self.env['inseta.dgapplicationdetails'].create(bursary_details)
				learner_id.write({'financial_budget_ids': [(0, 0, {
					'financial_year_id': financial_year_id,
					'funding_type': self.get_value_id('res.fundingtype', row[42]),
					'approved_amount': 0,
					'learner_register_id': learner_id.id,
					'dgbursary_detail_id': dgbursary_detail_id.id
					})]
				})

			elif self.template_type == "skills":
				error = []
				gender = False 
				dob = False 
				err_message = False
				rsa_number = self.validate_rsa_number(row[4])
				if rsa_number:
					gender = rsa_number[2]
					dob = rsa_number[1]
				else:
					error.append(f'Learner with {row[4]} was not imported. Reason {rsa_number[1]}')

				organisation_sdf = self.env['inseta.sdf.organisation'].search([('organisation_id', '=', self.organisation_id.id)], limit=1)
				provider_ref = self.env['inseta.provider'].search([('organisation_id', '=', organisation_sdf.id)], limit=1)
				start_date = self.validate_date(row[10])
				end_date = self.validate_date(row[11])
				duration = self.validate_date(row[12])
				provider_id = provider_ref
				organisation_id = organisation_sdf
				financial_year_id = self.get_value_id('res.financial.year', row[43])
				nqflevel_id = self.get_value_id('res.nqflevel', row[9])
				ofo_id = self.get_value_id('res.ofo.occupation', row[6])
				institution = self.get_value_id('res.dgpublicprovider', row[48]) # Institution
				publicprovider_id = institution
				if not provider_id:
					error.append(f'Learner with {row[0]} was not imported. Reason: No provider with SDL Number {provider_sdl_no} found. ')
				vals = dict(
					id_no = self.validate_rsa_number(row[4]),
					first_name=row[0],
					last_name=row[1],
					name = f"{row[0]} {row[1]}",
					gender_id =  self.get_value_id('res.gender', row[2]) or dob,
					equity_id = self.get_value_id('res.equity', row[3]),
					provider_id = provider_id.id,
					organisation_id = organisation_id.id,
					disability_id = self.get_value_id('res.disability', row[15]),
					physical_code = row[16],
					)
				learner_obj = self.env['inseta.learner']
				learner_ref = learner_obj.search([('id_no', '=', id_num)], limit=1)
				learner_id = False
				if not learner_ref:
					learner_id = learner_obj.create(vals)
				else:
					learner_ref.write(vals)
					learner_id = learner_ref
				
				bursary_details = dict(
					organisation_id = organisation_id,
					provider_id = provider_id,
					duration = duration,
					nqflevel_id = nqflevel_id,
					start_date = start_date,
					end_date = end_date,
					publicproviderother = row[13],
					skillsprogramme_title = row[8],
					scarcecritical_id = self.get_value_id('res.equity', row[7]),
					funding_amount_required = row[14], )
				dgbursary_detail_id = self.env['inseta.dgapplicationdetails'].create(bursary_details)
				learner_id.write({'financial_budget_ids': [(0, 0, {
					'financial_year_id': financial_year_id,
					'funding_type': self.get_value_id('res.fundingtype', row[42]),
					'approved_amount': 0,
					'learner_register_id': learner_id.id,
					'dgbursary_detail_id': dgbursary_detail_id.id,
					})]
				})
		self.file = False 
		self.import_type = "manual" 
		if len(error) > 1:
			message = '\n'.join(error)
			return self.confirm_notification(message)

	def record_reference_for_import(self, model, key_id, compare_value, limit=1):
		model_obj = self.env[f'{model}']
		record_ref = model_obj.search([(f'{key_id}', '=', compare_value)], limit)
		return False if not record_ref else record_ref.id

	def confirm_notification(self,popup_message):
		view = self.env.ref('inseta_utils.inseta_confirm_dialog_view')
		view_id = view and view.id or False
		context = dict(self._context or {})
		context['message'] = popup_message
		return {
				'name':'Message!',
				'type':'ir.actions.act_window',
				'view_type':'form',
				'res_model':'inseta.confirm.dialog',
				'views':[(view.id, 'form')],
				'view_id':view.id,
				'target':'new',
				'context':context,
				}

	@api.model
	def create(self, vals):
		sequence = self.env['ir.sequence'].next_by_code('inseta.lpro')
		vals['sequence'] = sequence or '/'
		return super(Insetalpro, self).create(vals)

