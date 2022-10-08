# -*- coding: utf-8 -*-
import base64
import json
import logging
import time
import random

from odoo import http, fields
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.inseta_tools.validators import (
	validate_email, 
	format_to_odoo_date, 
	validate_said
)

_logger = logging.getLogger(__name__)


class ThemeInseta(http.Controller):


	@http.route('/hei-rep-registration', type='http', auth='public', methods=['GET', 'POST'], website=True, website_published=True)
	def hei_rep_registration(self, **post):

		domain = [('institution_type','in', ('TVET','UoT','University'))]
		vals = {
			"titles": request.env["res.partner.title"].sudo().search([]),
			"heis": request.env["inseta.organisation"].sudo().search(domain),
		}
		return request.render("theme_inseta.hei_rep_registration", vals)

	@http.route('/hei-rep-registration-ajax', type='http', auth='public', methods=['POST'], website=True, website_published=True)
	def hei_rep_registration_ajax(self, **post):
		if request.httprequest.method == 'POST':
			headers = [('Content-Type', 'application/json')]
			#Maximum of 3 Reps is allowed for a HEI
			orgs = request.env["mis.hei.representative"].sudo().search([('organisation_id','=',post.get('selectHEI'))])
			if len(orgs) > 2:
				return json.dumps({'status': False, 'message': "Maximum of 3 Representative is allowed for an HEI"})

			vals = dict(
				organisation_id = post.get('selectHEI'),
				title = post.get('selectTitle'),
				first_name = post.get('inputFname'),
				last_name = post.get('inputSurname'),
				mobile = f"+{post.get('inputTelDialCode','')}{post.get('inputTel','')[1:]}",
				email = post.get('inputEmail'),
				designation = post.get('inputDesignation'),
				signatory_title = post.get('selectSignatoryTitle'),
				signatory_first_name = post.get('inputSignatoryFname'),
				signatory_last_name = post.get('inputSignatorySurname'),
				signatory_mobile = f"+{post.get('inputSignatoryTelDialCode','')}{post.get('inputSignatoryTel','')[1:]}",
				signatory_email = post.get('inputSignatoryEmail'),
				signatory_designation = post.get('inputSignatoryDesignation')
			)
			group_list = []
			Group = request.env['res.groups'].sudo()
			## Applying Portal and Employer Group to Emp Org. relateduser.
			#groups = Group.search(['|',('name','=','Portal'),('name','=','SDF')])
			group = request.env.ref("inseta_dg.group_hei_representative")
			group_list.append((4,group.id)) if group else False

			## Removing Contact Creation and Employee group from Org. relateduser.
			groups = Group.search(['|','|',('name', '=', 'Contact Creation'),('name','=','Employee'),('name','=','Portal')])
			for group in groups:
				tup = (3,group.id)
				group_list.append(tup)

			password =  ''.join(random.choice('adminpassword1234567') for _ in range(10))
			name =f"{vals.get('first_name')} {vals.get('last_name')}"
			user_vals = {
				'name' : name,
				'login' : vals.get('email'),
				'password': password,
				# 'groups_id': group_list
			}
			_logger.info("Creating HEI Rep User...")
			User = request.env['res.users'].sudo()
			user = User.search([('login', '=', vals.get('email'))],limit=1)
			if user:
				user.write(user_vals)
			else:
				user = User.create(user_vals)
			_logger.info('Adding user to group ...')
			user.sudo().write({'groups_id':group_list})

			#update user partner details
			_logger.info('Updating partner with user ...')
			user.partner_id.write({
				'name': name, 
				'title': vals.get('title'),
				'mobile': vals.get('mobile'),
				'email': vals.get('email')
			})
			vals['user_id'] = user.id
			vals['password'] = password

			try:
				hei = request.env["mis.hei.representative"].sudo().create(vals)
				user.sudo().write({'hei_rep_id':hei.id})
				hei.action_submit()
				return json.dumps({'status': True, 'message': "Form Submitted!"})
			except Exception as ex:
				_logger.exception(ex)
				return json.dumps({'status': False, 'message': f"{str(ex)}"})



	@http.route('/nonlevy-registration', type='http', auth='public', website=True, website_published=True)
	def nonlevy_registration(self):
		"""Non levy organisation registration
		"""

		vals = {
			"registrationno_types": request.env["res.registration_no_type"].sudo().search([]),
			"sic_codes": request.env['res.sic.code'].sudo().search([]),
			"country": request.env['res.country'].sudo().search([('code', '=', 'ZA')]),
			"org_sizes": request.env['res.organisation.size'].sudo().search([('saqacode','=','small_nonlevy')]),
			"org_sizes_list": json.dumps([{"id": size.id, "name": size.name, "saqacode": size.saqacode} for size in request.env['res.organisation.size'].sudo().search([('saqacode','=','small_nonlevy')])]),
			"titles": request.env["res.partner.title"].sudo().search([]),
			"designations":  request.env['res.designation'].sudo().search([]),
			"districts": request.env['res.district'].sudo().search([]),
			"cities": request.env['res.city'].sudo().search([]),
			"municipalities": request.env['res.municipality'].sudo().search([]),
			"suburbs": request.env['res.suburb'].sudo().search([]),
			"banks": request.env['inseta.bank'].sudo().search([]),
			"account_types": request.env['res.accounttype'].sudo().search([]),
			"bee_status": request.env['res.bee.status'].sudo().search([]),
		}
		return request.render("theme_inseta.nonlevy_registration", vals)


	@http.route('/sdf-registration', type='http', auth='public', website=True, website_published=True)
	def sdf_registration(self):

		vals = {
			"titles": request.env["res.partner.title"].sudo().search([]),
			"disability_statuses": request.env['res.disability'].sudo().search([]),
			"country": request.env['res.country'].sudo().search([('code', '=', 'ZA')]),
			"nationalities": request.env['res.nationality'].sudo().search([]),
			"citizenship_statuses": request.env['res.citizen.status'].sudo().search([]),
			"districts": request.env['res.district'].sudo().search([]),
			"cities": request.env['res.city'].sudo().search([]),
			"municipalities": request.env['res.municipality'].sudo().search([]),
			"suburbs": request.env['res.suburb'].sudo().search([]),
			"id_types": request.env['res.alternate.id.type'].sudo().search([]),
			"equities": request.env['res.equity'].sudo().search([]),
			"langs": request.env['res.lang'].sudo().search([('active', '=', True)]),
			"edu_levels":  request.env['res.education.level'].sudo().search([]),
			"reg_date": fields.Date.today()
		}
		return request.render("theme_inseta.sdf_registration", vals)

	# API controllers

	@http.route(['/nonlevy_registration_ajax'], type='http', methods=['POST'],  website=True, auth="public", csrf=True)
	def nonlevy_registration_ajax(self, **post):
		"""
		Returns:
			json: JSON reponse
		"""
		_logger.info(f"{post}")
		if post.get('checkConfirm', False):
			#process training committee data
			contacts, ceo, cfo, banks = [], [], [], []
			# if post.get('training_committee'):
			#     member_list = [(0,0,{
			#         "title": member.get('inputMemberTitle'),
			#         "first_name": member.get('inputMemberFname'),
			#         "last_name": member.get('inputMemberLname'),
			#         #"name":f"{member.get('inputMemberFname')} {member.get('inputMemberLname')}",
			#         "initials": member.get('inputMemberInitials'),
			#         "phone": member.get('inputItiMemberTel'),
			#         "mobile": member.get('inputItiMemberCell'),
			#         "fax_number": member.get('inputMemberFax'),
			#         "email": member.get('inputMemberEmail'),
			#         "designation_id": member.get('selectMemberDesignation'),
			#         "member_type": member.get('selectMemberType'),
			#         "name_of_union": member.get('inputMemberNameUnion'),
			#         "position_in_union": member.get('inputMemberPositionUnion')
			#     }) for member in  json.loads(post.get('training_committee'))]

			if post.get('inputContactFname'):
				contacts = [(0,0,{
					"title": post.get('inputContactTitle'),
					"first_name": post.get('inputContactFname'),
					"last_name": post.get('inputContactLname'),
					"name":f"{post.get('inputContactFname')} {post.get('inputContactLname')}",
					"initials": post.get("inputContactInitials"),
					"mobile": f"+{post.get('inputContactCellDialCode','')}{post.get('inputContactCellPhone','')[1:]}",
					"phone": f"+{post.get('inputContactTelDialCode')}{post.get('inputContactTel','')[1:]}" if post.get('inputContactTel') else False,
					"email": post.get("inputContactEmail"),
					"function": post.get("inputContactDesignation")
				})]

			if post.get('inputCeoFname'):
				ceo = [(0,0,{
					"type": "CEO",
					"title": post.get('inputCeoTitle'),
					"first_name": post.get('inputCeoFname'),
					"last_name": post.get('inputCeoLname'),
					"name":f"{post.get('inputCeoFname')} {post.get('inputCeoLname')}",
					"initials": post.get("inputCeoInitials"),
					"phone": f"+{post.get('inputCeoTelDialCode')}{post.get('inputCeoTel','')[1:]}" if post.get('inputCeoTel') else False,
					"mobile": f"+{post.get('inputCeoCellDialCode','')}{post.get('inputCeoCellPhone','')[1:]}",
					"email": post.get("inputCeoEmail"),
					"function": post.get("inputCeoDesignation")
				})]

			if post.get('inputCfoFname'):
				cfo = [(0,0,{
					"type": "CFO",
					"title": post.get('inputCfoTitle'),
					"first_name": post.get('inputCfoFname'),
					"last_name": post.get('inputCfoLname'),
					"name":f"{post.get('inputCfoFname')} {post.get('inputCfoLname')}",
					"initials": post.get("inputCfoInitials"),
					"phone": f"+{post.get('inputCfoTelDialCode')}{post.get('inputCfoTel','')[1:]}" if post.get('inputCfoTel') else False,
					"mobile": f"+{post.get('inputCfoCellDialCode','')}{post.get('inputCfoCellPhone','')[1:]}",
					"email": post.get("inputCfoEmail"),
					"function": post.get("inputCfoDesignation")
				})]

			# we will create bank account after we create org since we need the partner id
			if post.get("selectBankName"):
				banks = [(0,0,{
					"bank_id": post.get('selectBankName'),
					"accountnumber": post.get('inputAccNo'),
					"branchname": post.get('inputBranchName'),
					"branchcode": post.get('inputBranchCode'),
					"verification_status": "Not Verified",
					"accountholder": post.get('inputlegalName'),
					"accounttype_id":post.get("selectAccType",False),
					#"accounttype_id": request.env.ref("inseta_base.data_acctype1").id, #default to current account
				})]

			try:

				partner_vals = {
					"name": post.get('inputlegalName'),
					"company_type": "company",
					"mobile": f"+{post.get('inputCellDialCode','')}{post.get('inputCellPhone','')[1:]}",
					"phone": f"+{post.get('inputTelDialCode','')}{post.get('inputTel','')[1:]}" if post.get('inputTel') else False,
					"fax_number": f"+{post.get('inputFaxDialCode')}{post.get('inputFax','')[1:]}" if post.get('inputFax') else False,
					"email": post.get("inputEmail"), # if validate_email(post.get("inputEmail")) else False,
					"physical_code": post.get("inputPhysicalCode"),
					"street": post.get("inputPhysicalAddr1",""),
					"street2": post.get("inputPhysicalAddr2",""),
					"street3": post.get("inputPhysicalAddr3",""),
					"physical_province_id": post.get("selectPhysicalProvince",False),
					"state_id": post.get("selectPhysicalProvince",False),
					"physical_city_id": post.get("selectPhysicalCity",False),
					"physical_municipality_id": post.get("selectPhysicalMunicipality",False),
					"physical_suburb_id": post.get("selectPhysicalSuburb",False),
					"physical_urban_rural": post.get("selectPhysicalUrbanRural", "").title(),
					"use_physical_for_postal_addr": True if post.get("checkUsePhysicalForPostal") == "on" else False,
					"postal_code": post.get("inputPostalCode", False),
					"postal_address1": post.get("inputPostalAddr1",""),
					"postal_address2": post.get("inputPostalAddr2",""),
					"postal_address3": post.get("inputPostalAddr3",""),
					"postal_suburb_id": post.get("selectPostalSuburb", False),
					"postal_city_id": post.get("selectPostalCity",False),
					"postal_municipality_id": post.get("selectPostalMunicipality", False),
					"postal_province_id": post.get("selectPostalProvince",False),
					"postal_urban_rural": post.get("selectPostalUrbanRural","").title(),
				}
				group_list = []
				Group = request.env['res.groups'].sudo()
				## Applying Portal and Employer Group to Emp Org. relateduser.
				#groups = Group.search(['|',('name','=','Portal'),('name','=','SDF')])
				group = request.env.ref("inseta_skills.group_employer")
				group_list.append((4,group.id)) if group else False

				## Removing Contact Creation and Employee group from Org. relateduser.
				groups= Group.search(['|',('name', '=', 'Contact Creation'),('name','=','Employee')])
				for group in groups:
					tup = (3,group.id)
					group_list.append(tup)

				password =  ''.join(random.choice('adminpassword') for _ in range(10))
				user_vals = {
					'name' : partner_vals.get("name"),
					'login' : partner_vals.get('email'),
					'password': password
				}
				_logger.info("Creating Organisation User...")
				User = request.env['res.users'].sudo()
				user = User.search([('login', '=', partner_vals.get('email'))])
				if user:
					user.write(user_vals)
				else:
					user = User.create(user_vals)
				_logger.info('Adding user to group ...')
				user.sudo().write({'groups_id':group_list})

				#update user partner details
				_logger.info('Updating partner with user ...')
				user.partner_id.write(partner_vals)

				uploads = []
				#mandatory docs for non-levy registration
				#Registration form, CIPC Documents, Tax Clerance, Confirmation of Banking Details
				#BEE Certificate, FSP License, EMP201 or Confirmation of registration with SARS (EMPSA)
				_logger.info('Preparing Uploaded documents ...')

				if post.get("fileRegForm"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc12").id,
						"file": base64.b64encode(post.get("fileRegForm").read()),
						"file_name": post.get("fileRegForm").filename
					}))
				if post.get("fileCIPC"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc9").id,
						"file": base64.b64encode(post.get("fileCIPC").read()),
						"file_name": post.get("fileCIPC").filename
					}))
				if post.get("fileTaxClearance"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc10").id,
						"file": base64.b64encode(post.get("fileTaxClearance").read()),
						"file_name": post.get("fileTaxClearance").filename
					}))

				if post.get("fileConfirmBnkDtl"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc13").id,
						"file": base64.b64encode(post.get("fileConfirmBnkDtl").read()),
						"file_name": post.get("fileConfirmBnkDtl").filename
					}))

				if post.get("fileBeeCert"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc11").id,
						"file": base64.b64encode(post.get("fileBeeCert").read()),
						"file_name": post.get("fileBeeCert").filename
					}))

				if post.get("fileFsp"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc8").id,
						"file": base64.b64encode(post.get("fileFsp").read()),
						"file_name": post.get("fileFsp").filename
					}))

				if post.get("fileEMP201"):
					uploads.append((0,0,{
						"documentrelates_id": request.env.ref("inseta_skills.data_crmdoc14").id,
						"file": base64.b64encode(post.get("fileEMP201").read()),
						"file_name": post.get("fileEMP201").filename
					}))

				vals = {
					'user_id': user.id, 
					'partner_id': user.partner_id.id, 
					'password': password, 
					'username':user_vals.get('login'),
					"levy_status": "Non-Levy Paying",
					"bee_status_id": request.env.ref("inseta_base.data_bee_status11").id,
					"name": post.get('inputTradeName') or post.get('inputlegalName'),
					"trade_name":post.get('inputTradeName'),
					"legal_name": post.get('inputlegalName'),
					"registration_no": post.get('inputRegno'),
					"registration_no_type_id": post.get("selectRegnoType"),
					"organisation_status": "Active",
					"sic_code_id": post.get('selectSicCode'),
					"core_business": post.get("inputCoreBusiness"),
					"other_sector": "others",
					"no_employees": post.get('inputNoEmployees'),
					"will_submit_wsp":  'yes' if post.get("checkWillSubmitWSP") == "on" else 'no',
					"is_confirmed": True if post.get("checkConfirm") == "on" else False,
					"mobile": f"+{post.get('inputCellDialCode','')}{post.get('inputCellPhone','')[1:]}",
					"phone": f"+{post.get('inputTelDialCode','')}{post.get('inputTel','')[1:]}" if post.get('inputTel') else False,
					"fax_number": f"+{post.get('inputFaxDialCode')}{post.get('inputFax','')[1:]}" if post.get('inputFax') else False,
					"email": post.get("inputEmail"), # if validate_email(post.get("inputEmail")) else False,
					"child_ids": contacts,
					"cfo_ids": cfo,
					"ceo_ids": ceo,
					"bank_ids": banks,
					'document_ids': uploads,
					"confirm_contact": True,
					"confirm_training_committee": True,
					"confirm_cfo": True,
					"confirm_ceo": True,
					"confirm_bank": True,
				}

				#_logger.info(f"POST DATA {json.dumps(vals, indent=4)}")
				_logger.info('Creating Non levy Organisation with uploaded documents ...')

				organisation = request.env['inseta.organisation'].sudo().create(vals)
				organisation._compute_organisation_size()
				organisation.action_submit()
				_logger.info('Non Levy organisation Successfully Registered!')
				return json.dumps({'status': True, 'message': "Form Submitted!"})
			except Exception as ex:
				_logger.exception(ex)
				return json.dumps({'status': False, 'message': f"{str(ex)}"})


	@http.route(['/sdf_registration_ajax'], type='http', methods=['POST'],  website=True, auth="public", csrf=True)
	def sdf_registration_ajax(self, **post):
		"""
		'S000123_sdf_appointment_letter': <FileStorage: 'Elite Policy Proposal For JAIZ - EPIS proposal for partners - Google Docs.pdf' ('application/pdf')>, 'fileSdfCert': <FileStorage: '' ('application/octet-stream')>} 
		Returns:
			json: JSON reponse
		"""
		_logger.info('Creating SDF Register ...')
		if post.get('checkConfirm', False):

			vals = {
				"title": post.get('inputTitle'),
				"first_name": post.get("inputFname"),
				"last_name": post.get("inputLname"),
				"middle_name": post.get("inputMname", ""),
				"initials": post.get("inputInitials"),
				"id_no": post.get("inputIdNo") if post.get("inputIdNo") else post.get("inputPassportNo"),
				"birth_date": format_to_odoo_date(post.get("inputDob",'')),
				"gender_id": 1 if post.get("inputGender") == 'male' else 2,
				#phone, cell and fax is submitted in format 0803 527 9300. Remove the first digit and add the dialling code
				"mobile": f"+{post.get('inputCellDialCode','')}{post.get('inputCellPhone','')[1:]}",
				"phone": f"+{post.get('inputTelDialCode')}{post.get('inputTel','')[1:]}" if post.get('inputTel') else False,
				"fax_number": f"+{post.get('inputFaxDialCode')}{post.get('inputFax','')[1:]}" if post.get('inputFax') else False,
				"email": post.get("inputEmail") if validate_email(post.get("inputEmail")) else False,
				"physical_code": post.get("inputPhysicalCode", ""),
				"street": post.get("inputPhysicalAddr1",""),
				"street2": post.get("inputPhysicalAddr2",""),
				"street3": post.get("inputPhysicalAddr3",""),
				"physical_province_id": post.get("selectPhysicalProvince",False),
				"physical_city_id": post.get("selectPhysicalCity",False),
				"physical_municipality_id": post.get("selectPhysicalMunicipality",False),
				"physical_suburb_id": post.get("selectPhysicalSuburb",False),
				"physical_urban_rural": post.get("selectPhysicalUrbanRural", "").title(),
				"use_physical_for_postal_addr": True if post.get("checkUsePhysicalForPostal") == "on" else False,
				"postal_code": post.get("inputPostalCode", False),
				"postal_address1": post.get("inputPostalAddr1",""),
				"postal_address2": post.get("inputPostalAddr2",""),
				"postal_address3": post.get("inputPostalAddr3",""),
				"postal_suburb_id": post.get("selectPostalSuburb", False),
				"postal_city_id": post.get("selectPostalCity",False),
				"postal_municipality_id": post.get("selectPostalMunicipality", False),
				"postal_province_id": post.get("selectPostalProvince",False),
				"postal_urban_rural": post.get("selectPostalUrbanRural","").title(),
				"alternateid_type_id": post.get("selectAlternateIDtype"),
				"equity_id": post.get("selectEquity"),
				"disability_id": post.get("selectDisabilityStatus"),
				"home_language_id": post.get("selectHomeLanguage"),
				"nationality_id": post.get("selectNationality"),
				"citizen_resident_status_id": post.get("selectResidentialStatus"),
				"socio_economic_status_id": 1 if  post.get("selectSocioEconomicStatus","") == "Employed" else 2,
				"highest_edu_level_id":post.get("selectHighestEducation"),
				"highest_edu_desc": post.get("inputHighestEducationDesc"),
				"current_occupation": post.get("inputCurrentOccupation"),
				"occupation_years": post.get("inputYearsInOccupation",0),
				"occupation_experience":post.get("inputExperience"),
				"general_comments":post.get("inputComments"),
				"accredited_trainingprovider_name":post.get("inputAccreditedTrainer"),
				"has_completed_sdftraining": True if post.get("checkCompletedSDFtraining") == "on" else False,
				"has_requested_sdftraining": True if post.get("inputDontHaveSdfCert","") == "Yes" else False,
				"is_confirmed": True if post.get("checkConfirm") == "on" else False,
				# "state": "pending_verification",
			}
			_logger.info(f"POST DATA {vals}")

			#add SDF certificate upload
			if post.get("fileSdfCert"):
				file_name = post.get("fileSdfCert").filename
				sdf_cert = base64.b64encode(post.get("fileSdfCert").read())
				vals.update({'sdf_certificate': sdf_cert, 'file_name': file_name})

			#code of conduct
			if post.get('fileCodeOfConduct'):
				file_name2 = post.get('fileCodeOfConduct').filename
				code_of_conduct = base64.b64encode(post.get('fileCodeOfConduct').read())
				vals.update({'code_of_conduct':code_of_conduct, 'file_name2': file_name2})

			#id proof
			if post.get('fileIdProof'):
				file_name3 = post.get('fileIdProof').filename
				idproof = base64.b64encode(post.get('fileIdProof').read())
				vals.update({'alternate_id_proof':idproof, 'file_name3': file_name3})

			try:
				# we will create an SDF before creating a user because we need to
				# link the SDF partner ID to the sdf user. 
				sdf = request.env['inseta.sdf'].sudo().create(vals)
				#create employer apppointment letter attachments
				sdl_nos = request.httprequest.form.getlist('sdlNoList')
				employer_lines = []
				for sdl_no in sdl_nos:
					Organisation = request.env['inseta.organisation'].sudo()
					organisation = Organisation.search([('sdl_no', '=', sdl_no)],order="id desc", limit=1) #take the latest org.
					# for line in sdf_organisations:
					sdf_appointment_letter = '{}_sdf_appointment_letter'.format(sdl_no)
					# Attachments = request.env['ir.attachment']
					# name = post.get(sdf_appointment_letter).filename
					# file = post.get(sdf_appointment_letter)
					# attachment = file.read()
					# attachment_id = Attachments.sudo().create({
					#     'name': name,
					#     'res_name': name,
					#     'type': 'binary',
					#     'res_model': 'inseta.sdf.register',
					#     'res_id': sdf_id.id,
					#     'datas': base64.b64encode(attachment),
					# })

					sdf_emp_vals = {
					   # 'sdf_id': sdf.id,
						'organisation_id': organisation.id,
						'sdf_role': post.get("selectSdfRole"),
						# 'appointment_letter_id': attachment_id.id,
						'state': 'draft',
						'reference':sdf.reference,#for new registration, we reuse the sdf ref as the sdf organisation reference
						'is_existing_sdf': False, #This will prevent a reference no from being generated
					}

					if post.get(sdf_appointment_letter):
						fname = post.get(sdf_appointment_letter).filename
						appt_letter = base64.b64encode(post.get(sdf_appointment_letter).read())
						sdf_emp_vals.update({'appointment_letter': appt_letter, 'file_name':fname})

					employer_lines.append((0, 0, sdf_emp_vals))

				#create user and associate with the SDF
				group_list = []
				Group = request.env['res.groups'].sudo()
				## Applying Portal and SDF groups to SDF related user.
				#groups = Group.search(['|',('name','=','Portal'),('name','=','SDF')])
				group = Group.search([('name','=','Primary SDF')]) if post.get("selectSdfRole") == "primary" else Group.search([('name','=','Secondary SDF')])
				group_list.append((4,group.id)) if group else False

				## Removing Contact Creation and Employee group from SDF related user.
				groups= Group.search(['|',('name', '=', 'Contact Creation'),('name','=','Employee')])
				for group in groups:
					tup = (3,group.id)
					group_list.append(tup)

				password =  ''.join(random.choice('admin') for _ in range(10))
				user_vals = {
					'name' : f"{vals.get('first_name')} {vals.get('middle_name')} {vals.get('last_name')}",
					'first_name': vals.get('first_name'),
					'last_name': vals.get('last_name'),
					'login' : vals.get('email'),
					'password': password,
					'partner_id': sdf.partner_id.id,
					'sdf_id': sdf and sdf.id or False,
				}
				_logger.info("Creating SDF User...")
				User = request.env['res.users'].sudo()
				user = User.search([('login', '=', vals.get('email'))])
				if user:
					user.write(user_vals)
				else:
					user = User.create(user_vals)
				user.sudo().write({'groups_id':group_list})

				sdf.write({
					"organisation_ids": employer_lines, 
					"is_initial_update": True,
					"user_id": user.id, 
					"password": password
				})
				sdf.action_submit()

				_logger.info('SDF Successfully Registered!')
				return json.dumps({'status': True, 'message': "Form Submitted!"})
			except Exception as ex:
				_logger.error('Error Occured while registering SDF')
				_logger.exception(ex)
				return json.dumps({'status': False, 'message': f"{str(ex)}"})


	@http.route(['/check_sa_idno/<id_num>'], type='json', website=True, auth="public", csrf=False)
	def check_sa_idno(self, id_num):
		"""Check SA Identification No.

		Args:
			id_num (str): The Id No to be validated

		Returns:
			dict: Response
		"""
		_logger.info('Checking RSA ID No ...')

		if request.env['inseta.sdf'].sudo().search([('id_no', '=', id_num)]):
			return dict(status = False, message = f"SDF with same ID NO {id_num} exists!")

		identity = validate_said(id_num)
		if not identity:
			return dict(status = False, message = f"Invalid R.S.A ID No {id_num}")

		_logger.info('Checking RSA ID No Completed ...')
		return dict(status = True, data = identity)

	@http.route(['/assessor-moderator/<programmeCode>/<sdlno>/<modsdlno>'], type='json',  website=True, auth="public", csrf=False)
	def check_assessor_moderator_no(self, programmeCode, sdlno, modsdlno):
		status = ''
		programme = {}
		assessor_search_obj = request.env['inseta.assessor'].sudo().search(
			[('employer_sdl_no', '=', sdlno),('active', '=', True)], limit=1)

		moderator_search_obj = request.env['inseta.moderator'].sudo().search(
			[('employer_sdl_no', '=', modsdlno),('active', '=', True)], limit=1)

		skill_programme_search_obj = request.env['inseta.skill.programme'].sudo().search(
			[('programme_code', '=', programmeCode),('active', '=', True)], limit=1)

		qual_programme_search_obj = request.env['inseta.qualification'].sudo().search(
			[('saqa_id', '=', programmeCode),('active', '=', True)], limit=1)

		learnership_programme_search_obj = request.env['inseta.learner.programme'].sudo().search(
			[('programme_code', '=', programmeCode),('active', '=', True)], limit=1)

		if assessor_search_obj and moderator_search_obj:
			programme['moderator'] = moderator_search_obj.name
			programme['assessor'] = assessor_search_obj.name
			status = f"Moderator {moderator_search_obj.name} or Assessor {assessor_search_obj.name} Found" 
		
		else:
			status = "None"

		if skill_programme_search_obj:
			programme['programme_name'] = skill_programme_search_obj.name
			programme['programme_code'] = skill_programme_search_obj.programme_code
			programme['programme_id'] = skill_programme_search_obj.id
			programme['programme_type'] = "skills"
			status = "Skill Programme code Found" 

		elif qual_programme_search_obj:
			programme['programme_name'] = qual_programme_search_obj.name
			programme['programme_code'] = qual_programme_search_obj.saqa_id
			programme['programme_id'] = qual_programme_search_obj.id
			programme['programme_type'] = "qual"
			status = "Qualification Programme code Found" 

		elif learnership_programme_search_obj:
			programme['programme_name'] = learnership_programme_search_obj.name
			programme['programme_code'] = skill_programme_search_obj.programme_code

			programme['programme_id'] = learnership_programme_search_obj.id
			programme['programme_type'] = "learnership"
			status = "Learnership Programme code Found" 

		else:
			programme['programme_code'] = ''
			programme['programme_type'] = ""
			programme['programme_id'] = ""
			programme['programme_name'] = ""
			status = "None"

		# if not any([programme.get('programme_code')]):
		#     status = "No Programme code Found" 

		return {
			"status": status, 
			"data": {
				'assessor_search_id': assessor_search_obj.id,
				'moderator_search_id': moderator_search_obj.id,
				'programme_codes': programme,
			}
		}

	@http.route(['/get-programme/<code>/<type>'], type='json',  website=True, auth="public", csrf=False)
	def get_programme_id(self, code, type):
		if type == "unitstandard":
				unit_standard_search_obj = request.env['inseta.unit.standard'].sudo().search(
					[('code', '=', code)], limit=1)
				if unit_standard_search_obj:
					return {
						'status': True,
						"data": {
							'name': unit_standard_search_obj.name,
							'id': unit_standard_search_obj.id,
							'code': unit_standard_search_obj.code,
						}
					}

				else:
					return {"status": False}

		if code and type:
			if type == "qualification":
				qual_programme_search_obj = request.env['inseta.qualification'].sudo().search(
				[('saqa_id', '=', code),('active', '=', True)], limit=1)
				if qual_programme_search_obj:
					return {
						'status': True,
						"data": {
							'name': qual_programme_search_obj.name,
							'id': qual_programme_search_obj.id,
							'code': qual_programme_search_obj.saqa_id,
						}
					}
				else:
					return {"status": False}

			if type == "skill":
				skill_programme_search_obj = request.env['inseta.skill.programme'].sudo().search(
					[('programme_code', '=', code),('active', '=', True)], limit=1)
				if skill_programme_search_obj:
					return {
						'status': True,
						"data": {
							'name': skill_programme_search_obj.name,
							'id': skill_programme_search_obj.id,
							'code': skill_programme_search_obj.programme_code,
						}
					}

				else:
					return {"status": False}

			if type == "learnership":
				learnership_programme_search_obj = request.env['inseta.learner.programme'].sudo().search(
				[('programme_code', '=', code),('active', '=', True)], limit=1)
				if learnership_programme_search_obj:
					return {
						'status': True,
						"data": {
							'name': learnership_programme_search_obj.name,
							'id': learnership_programme_search_obj.id,
							'code': learnership_programme_search_obj.programme_code,
						}
					}
				else:
					return {"status": False}

	@http.route(['/get-assessor-moderator/<idno>/<type>'], type='json',  website=True, auth="public", csrf=False)
	def get_assessor_moderator(self, idno, type):
		if idno and type:
			if type == "assessor":
				assessor = request.env['inseta.assessor'].sudo().search(
				['|', ('id_no', '=', idno), ('registration_number', '=', idno)], limit=1)
				if assessor:
					udata = []
					quality_assurance_id = request.env.ref('inseta_etqa.data_inseta_quality_assurance15')
					# unit standards
					unit_standard_ids = assessor.mapped('unit_standard_ids').filtered(lambda self: self.unit_standard_id.quality_assurance_id.id == quality_assurance_id.id)
					if unit_standard_ids:
						for rec in unit_standard_ids:
							udata.append({
								'name': rec.unit_standard_id.name,
								'id': rec.unit_standard_id.id,
								'code': rec.unit_standard_id.code,
							})
					else:
						udata = False
					# qualifications 
					qdata = []
					qualification_ids = assessor.mapped('qualification_ids').filtered(lambda self: self.qualification_id.quality_assurance_id.id == quality_assurance_id.id)
					if qualification_ids:
						for rec in qualification_ids:
							qdata.append({
								'name': rec.qualification_id.name,
								'id': rec.qualification_id.id,
								'code': rec.qualification_id.saqa_id,
							})
					else:
						qdata = False
					return {
						'status': True,
						'qdata': qdata, 
						'udata': udata, 
						"data": {
							'name': assessor.name,
							'id': assessor.id,
							'code': assessor.employer_sdl_no or "",
							"title_id": assessor.title.id or "",
							"first_name": assessor.first_name,
							"last_name": assessor.last_name,
							"middle_name": assessor.middle_name,
							"initials": assessor.initials,
							"passport_no": assessor.passport_no,
							"id_no": assessor.id_no,
							"alternateid_type_id": assessor.alternateid_type_id.id or "",
							"birth_date": assessor.birth_date.strftime("%m/%d/%Y") if assessor.birth_date else "",
							"gender_id": 'male' if assessor.gender_id.id == 1 else 'female',
							"cell_phone_number": assessor.mobile or "",
							"telephone_number": assessor.phone or "",
							"fax_number": assessor.fax_number or "",
							"email": assessor.email or "",
							"physical_code": assessor.physical_code or "",
							"physical_address1": assessor.street or "",
							"physical_address2":assessor.street2 or "",
							"physical_address3": assessor.street3,
							"physical_province_id": assessor.state_id.id or "",
							"physical_city_id": assessor.physical_city_id.id or "",
							"physical_municipality_id": assessor.physical_municipality_id.id or "",
							"physical_suburb_id": assessor.physical_suburb_id.id or "",
							"physical_urban_rural": assessor.physical_urban_rural or "",
							"use_physical_for_postal_addr": 'on' if assessor.use_physical_for_postal_addr else "off",
							"is_permanent_consultant": 'on' if assessor.is_permanent_consultant else "off", 
							"postal_code": assessor.postal_code or "",
							"postal_address1": assessor.postal_address1 or "",
							"postal_address2": assessor.postal_address2 or "",
							"postal_address3": assessor.postal_address3 or "",
							"postal_suburb_id": assessor.postal_suburb_id.id or "",
							"postal_city_id": assessor.postal_city_id.id or "",
							"postal_municipality_id": assessor.postal_municipality_id.id or "",
							"postal_province_id":assessor.postal_province_id.id or "",
							"postal_urban_rural": assessor.postal_urban_rural,
							"equity_id": assessor.equity_id.id or "",
							# "unit_standard_ids": [(4, rec) for rec in request.httprequest.form.getlist('unit_standard_ids')] if post.get("unit_standard_ids",False) != "" else False,
							# "qualification_ids": [(6, rec) for rec in request.httprequest.form.getlist('qualification_ids')] if post.get("qualification_ids",False) != "" else False,
							"disability_id": assessor.disability_id.id or "",
							"home_language_id": assessor.home_language_id.id or "",
							"nationality_id": assessor.nationality_id.id or "",
							"job_title": assessor.job_title or "",
							"latitude_degree": assessor.latitude_degree or "",
							"longitude_degree": assessor.longitude_degree or "",
							"popi_act_status_id": assessor.popi_act_status_id.id or "",
							"school_emis_id": assessor.school_emis_id.id or "",
							"statssa_area_code_id": assessor.statssa_area_code_id.id or "",
							"popi_act_status_date": assessor.popi_act_status_date.strftime("%m/%d/%Y") if assessor.popi_act_status_date else ""
						}
					}
				else:
					return {"status": False}

			if type == "moderator":
				moderator = request.env['inseta.moderator'].sudo().search(
					['|', ('id_no', '=', idno), ('registration_number', '=', idno)], limit=1)
				if moderator:
					return {
						'status': True,
						"data": {
							'name': moderator.name,
							'id': moderator.id,
							'code': moderator.employer_sdl_no or "",
						}
					}

				else:
					return {"status": False}
 
			if type == "facilitator":
				assessor = request.env['inseta.assessor'].sudo().search(
				['|', ('id_no', '=', idno), ('registration_number', '=', idno)], limit=1)
				if assessor:
					return {
						'status': True,
						"data": {
							'name': assessor.name,
							'id': assessor.id,
							'code': assessor.employer_sdl_no or "",
						}
					}

				else:
					return {"status": False}
 
	@http.route(['/organisation/<sdlno>'], type='json',  website=True, auth="public", csrf=False)
	def check_sdl_no(self, sdlno):
		"""Check if employer with SDL exists

		Args:
			sdlno (str): The SDL no to check

		Returns:
			dict: Returns dict with a status of True if found or False
		"""

		org = request.env['inseta.organisation'].sudo().search(
			[
				('sdl_no', '=ilike', sdlno),
				# ('state','=','approve')
			],
			limit=1
		)
		if org:
			return {
				"status": True,
				"name": org.legal_name,
				"id": org.id,
				"code": org.sdl_no,
			}
		return {"status": False, "name":"", 'id':"", 'code': ""}


	@http.route(['/organisation/check_sdf_role'], type='json', methods=['POST'],  website=True, auth="public", csrf=False)
	def check_sdf_role(self, **post):
		"""Validate, there can only be one Primary SDF in an organization
			and not more than 3 Secondary SDFs
		Args:
			sdlno (dict): Post data

		Returns:
			dict: Returns dict with a status of True if check passes or False if it fails
		"""
		_logger.info(f"Checking Organisation SDF role ...{post}")
		role = post.get('role')
		sdlno_list = post.get('sdl_nos',[])
		if not sdlno_list:
			return {'status': True}

		if not role:
			return {'status': True}

		organisations = request.env['inseta.organisation'].sudo().search(
			[
				('sdl_no', 'in', sdlno_list)
			],
		)
		for organisation in organisations:
			#check there can only be one Primary SDF in an organization
			if role == 'primary' and organisation.sdf_ids.filtered(lambda s: s.sdf_role == 'primary' and s.state == 'approve'):
				return {
					"status": False,
					"message": f"Organisation with SDL No {organisation.sdl_no} already has a Primary SDF"
				}
			#check not more than 3 Secondary SDFs
			if role == 'secondary' and len(organisation.sdf_ids.filtered(lambda s: s.sdf_role == 'secondary' and s.state == 'approve')) >=3:
				return {
					"status": False,
					"message": f"Organisation with SDL No {organisation.sdl_no} already has 3 Secondary SDFs"
				}
		_logger.info("Checking Organisation SDF role completed ...")
		return {'status': True}


	@http.route(['/users/<email>'], type='json',  website=True, auth="public", csrf=False)
	def check_email(self, email):
		"""check if User with same email already exists

		Args:
			email (string): Email to be checked

		Returns:
			dict: Returns dict with a status of True if found or False
		"""
		user = request.env['res.users'].sudo().search(
			[('email', '=', email)], limit=1)
		# TODO: check sdf_register,
		# assessors_moderators_register and final_state != Rejected
		# provider_accreditation  and final_state != Rejected

		if user:
			return {"status": True}
		return {"status": False}

	@http.route(['/sdf/check_physical_code/<code>'], type='json',  website=True, auth="public", csrf=False)
	def check_physical_code(self, code):
		"""check if Physical code Exists
		Args:
			code (string): The physical code to be checked

		Returns:
			dict: Returns dict with a status of True if found or False
		"""
		suburb = request.env['res.suburb'].sudo().search(
			[('postal_code', '=', code)], limit=1)
		if suburb:
			return {
				"status": True,
				"urban_rural": suburb.municipality_id and suburb.municipality_id.urban_rural or "",
				"suburb": {"name": suburb.name, "id": suburb.id},
				"nationality": {"name": suburb.municipality_id.district_id.province_id.country_id.name, "id": suburb.municipality_id.district_id.province_id.country_id.id},
				"municipality": {"name": suburb.municipality_id and suburb.municipality_id.name or '', "id": suburb.municipality_id and suburb.municipality_id.id or ''},
				"city":  {"name": suburb.city_id and suburb.city_id.name or '', "id": suburb.city_id and suburb.city_id.id or ''},
				"district":  {"name": suburb.district_id and suburb.district_id.name or '', "id": suburb.district_id and suburb.district_id.id or ''},
				"province":  {"name": suburb.province_id and suburb.province_id.name or suburb.municipality_id.district_id.province_id.name, "id": suburb.province_id and suburb.province_id.id or suburb.municipality_id.district_id.province_id.id},
			}
		return {"status": False}

	@http.route(['/get_geolocation/<physical_address1>/<physical_code>/<physical_city_name>/<physical_province_name>/<country_name>'], type='json',  website=True, auth="public", csrf=False)
	def get_geolocation(self,physical_address1,physical_code,physical_city_name,physical_province_name,country_name):
		# We need country names in English below
		result = request.env['res.partner'].sudo()._geo_localize(
			physical_address1,
			physical_code,
			physical_city_name,
			physical_province_name,
			country_name
		)
		if result:
			return {
				'status': True,
				'latitude_degree': result[0] if result else "",
				'longitude_degree': result[1] if result else "",
			}
		return {"status": False}

	# generate attachment
	def generate_attachment(self, name, title, datas, model='inseta.provider.accreditation'):
		attachment = request.env['ir.attachment'].sudo()
		attachment_id = attachment.create({
			'name': f'{title} for {name}',
			'type': 'binary',
			'datas': datas,
			'res_name': name,
			'res_model': model,
		})
		return attachment_id

	# Provider Accreditation 

	@http.route('/provider-accreditation', type='http', auth='public', website=True, website_published=True)
	def provider_accreditation(self):
		quality_assurance_id = request.env.ref('inseta_etqa.data_inseta_quality_assurance15')
		vals = {
			"sic_code": request.env['res.sic.code'].sudo().search([]),
			"bee_status": request.env['res.bee.status'].sudo().search([]),
			"country": request.env['res.country'].sudo().search([('code', '=', 'ZA')]),
			"nationalities": request.env['res.nationality'].sudo().search([]),
			"cities": request.env['res.city'].sudo().search([]),
			"delivery_centers": request.env['inseta.delivery.center'].sudo().search([]),
			"titles": request.env["res.partner.title"].sudo().search([('name', '!=', False)]),
			"municipalities": request.env['res.municipality'].sudo().search([]),
			"suburbs": request.env['res.suburb'].sudo().search([]),
			"provider_type_id": request.env['res.provider.type'].sudo().search([('active', '=', True)]),
			"provider_class_id": request.env['res.provider.class'].sudo().search([('active', '=', True)]),
			"provider_category_id": request.env['res.provider.category'].sudo().search([('active', '=', True)]),
			"provider_quality_assurance_id": request.env['inseta.quality.assurance'].sudo().search([('id', '=', quality_assurance_id.id)], limit=1),
			"provider_qualifications": request.env['inseta.qualification.programme'].sudo().search([]),
			"qualification_ids": request.env['inseta.qualification'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"provider_skill_programme": request.env['inseta.skill.programme'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"provider_unit_standard_ids": request.env['inseta.unit.standard'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"provider_learning_programme": request.env['inseta.learner.programme'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"training_material": request.env['inseta.training.material'].sudo().search([('active', '=', True)]),
			"reg_date": fields.Date.today()
		}
		return request.render("theme_inseta.provider_accreditation", vals)

	# Provider Accreditation form post
	@http.route(['/provider_accreditation_ajax'], type='http', methods=['POST'],  website=True, auth="public", csrf=True)
	def provider_accreditation_ajax(self, **post):
		"""
		Returns:
			json: JSON reponse
		"""
		_logger.info('Creating provider Register ...')
		if post.get('checkConfirm', False): 
			vals = {
				"trade_name": post.get("inputTradename"),
				"provider_name": post.get("inputProvidername"),
				"registration_no": post.get("inputregNumber"), 
				# "accreditation_number": post.get("inputregNumber"),
				"vat_number": post.get("inputvat", ""),
				"cell_phone": post.get("inputCellPhone"),
				"phone": post.get("inputTel"),
				"email": post.get("inputEmail"),
				"campus_name": post.get("inputcampusName"),
				"campus_phone": post.get("inputCampusCell"),
				"mobile": post.get("inputCampusCell"),
				"postal_address2": post.get("inputPostalAddr2",""),
				"employer_sdl_no": post.get("inputSDLNumber"),
				"campus_code": post.get("inputPhysicalCode"),
				"campus_email": post.get("inputCampusEmail"),
				"campus_address1": post.get("inputCampusAddress1"),
				"campus_street_number": post.get("inputCampusStreetNumber"),
				"fax": post.get("inputCampusFax"),
				"number_staff_members": post.get("inputNumberStaff"),
				"sic_code": post.get("selectSicCode", False),
				"bee_status": post.get("selectBeeStatus", False),
				"physical_code": post.get("inputPhysicalCode", ""),
				"physical_province_id": post.get("selectPhysicalProvince",False),
				"physical_city_id": post.get("selectPhysicalCity",False),
				"physical_suburb_id": post.get("selectPhysicalSuburb",False),
				"postal_code": post.get("inputPostalCode", ""), 
				"physical_address1": post.get("inputPhysicalAddr1",""),
				"physical_address2": post.get("inputPhysicalAddr2",""),
				"physical_address3": post.get("inputPhysicalAddr3",""),
				"postal_address1": post.get("inputPostalAddr1",""),
				"postal_address2": post.get("inputPostalAddr2","") or post.get("inputPhysicalAddr2","") or "22 demo",
				"postal_address3": post.get("inputPostalAddr3",""),
				"postal_suburb_id": post.get("selectPostalSuburb", False) if post.get("selectPostalSuburb",False) != "" else False,
				"postal_city_id": post.get("selectPostalCity",False) if post.get("selectPostalCity",False) != "" else False,
				"postal_municipality_id": post.get("selectPostalMunicipality", False) if post.get("selectPostalMunicipality",False) != "" else False,
				"postal_province_id": post.get("selectPostalProvince",False) if post.get("selectPostalProvince",False) != "" else False,
				"postal_urban_rural": post.get("selectPostalUrbanRural","").title(),

				"training_material_id": post.get("inputTrainingMaterial",False),
				"current_business_years": post.get("current_business_years"),
				"campus_building":  post.get("inputCampusBuilding"),

				"provider_type_id": post.get("provider_type_id",False),
				"provider_class_id": post.get("provider_class_id",False),
				"provider_category_id": post.get("provider_category_id",False),
				"provider_quality_assurance_id": post.get("provider_quality_assurance_id",False),
				"delivery_center_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('delivery_center_ids')])] if post.get("delivery_center_ids",False) else False,
				"qualification_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('qualification_ids')])] if post.get("qualification_ids",False) else False,
				"skill_programmes_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('provider_skill_programme')])] if post.get("provider_skill_programme",False) else False,
				"learner_programmes_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('provider_learning_programme')])] if post.get("provider_learning_programme",False) else False,
				"unit_standard_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('provider_unit_standard_ids')])] if post.get("provider_unit_standard_ids",False) else False,

				"latitude_degree": post.get("inputLatitude"),
				"longitude_degree": post.get("inputLongtitude"),
				"assessor_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('assessor_ids')])] if post.get("assessor_ids",False) else False,
				"facilitator_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('facilitator_ids')])] if post.get("facilitator_ids",False) else False,
				"moderator_ids": [(6, 0, [rec for rec in request.httprequest.form.getlist('moderator_ids')])] if post.get("moderator_ids",False) else False,
				"tax_clearance_ids": False,
				"qualification_certificate_copy_ids": False,
				"director_cv_ids": False,
				"cipc_dsd_ids": False,
				"company_profile": False,
				"company_organogram": False,
				"appointment_letter": False,
				"proof_of_ownership":False,
				"workplace_agreement": False,
				"skills_registration_letter": False,
				"learning_approval_report": False,
				"referral_letter": False,
				"primary_accreditation_letter": False,
				"contact_person_id": False,
				"accreditation_status": "secondary" if post.get("checkAccStatus") == "on" else "Primary",
				"provider_status": False, 

			}
			_logger.info(f"POST DATA {vals}")
			# #add attachment upload
			name = vals.get('trade_name')
			if post.get("tax_clearance_ids"):
				data = base64.b64encode(post.get("tax_clearance_ids").read())
				attachment = self.generate_attachment(name, 'Tax Clearance', data)
				vals.update({'tax_clearance_ids':  [(6, 0, [attachment.id])]})
 
			if post.get("skill_programmes_ids"):
				data = base64.b64encode(post.get("skill_programmes_ids").read())
				attachment = self.generate_attachment(name, 'Skill Programmes', data)
				vals.update({'skill_programmes_ids':  [(6, 0, [attachment.id])]})

			if post.get("director_cv_ids"):
				data = base64.b64encode(post.get("director_cv_ids").read())
				attachment = self.generate_attachment(name, 'Director CV', data)
				vals.update({'director_cv_ids':  [(6, 0, [attachment.id])]})

			if post.get("cipc_dsd_ids"):
				data = base64.b64encode(post.get("cipc_dsd_ids").read())
				attachment = self.generate_attachment(name, 'CIPC', data)
				vals.update({'cipc_dsd_ids':  [(6, 0, [attachment.id])]})

			if post.get("company_profile"):
				data = base64.b64encode(post.get("company_profile").read())
				attachment = self.generate_attachment(name, 'Company profile', data)
				vals.update({'company_profile':  attachment.id})

			if post.get("bank_account_confirmation"):
				data = base64.b64encode(post.get("bank_account_confirmation").read())
				attachment = self.generate_attachment(name, 'bank account confirmation', data)
				vals.update({'bank_account_confirmation': attachment.id})

			if post.get("company_organogram"):
				data = base64.b64encode(post.get("company_organogram").read())
				attachment = self.generate_attachment(name, 'Company Organogram', data)
				vals.update({'company_organogram': attachment.id})

			if post.get("proof_of_ownership"):
				data = base64.b64encode(post.get("proof_of_ownership").read())
				attachment = self.generate_attachment(name, 'proof of ownership', data)
				vals.update({'proof_of_ownership': attachment.id})

			if post.get("account_business_solvency_letter"):
				data = base64.b64encode(post.get("account_business_solvency_letter").read())
				attachment = self.generate_attachment(name, 'account_business_solvency_letter', data)
				vals.update({'account_business_solvency_letter': attachment.id})

			if post.get("learner_details_achievement_spreadsheet"):
				data = base64.b64encode(post.get("learner_details_achievement_spreadsheet").read())
				attachment = self.generate_attachment(name, 'learner_details_achievement_spreadsheet', data)
				vals.update({'learner_details_achievement_spreadsheet': attachment.id})

			if post.get("it_servicing"):
				data = base64.b64encode(post.get("it_servicing").read())
				attachment = self.generate_attachment(name, 'it_servicing', data)
				vals.update({'it_servicing': attachment.id})

			if post.get("business_lease_agreement"):
				data = base64.b64encode(post.get("business_lease_agreement").read())
				attachment = self.generate_attachment(name, 'business_lease_agreement', data)
				vals.update({'business_lease_agreement': attachment.id})

			if post.get("programme_curriculum"):
				data = base64.b64encode(post.get("programme_curriculum").read())
				attachment = self.generate_attachment(name, 'programme_curriculum', data)
				vals.update({'programme_curriculum': attachment.id})

			if post.get("bbbeee_affidavit"):
				data = base64.b64encode(post.get("bbbeee_affidavit").read())
				attachment = self.generate_attachment(name, 'bbbeee_affidavit', data)
				vals.update({'bbbeee_affidavit': attachment.id}) 

			if post.get("business_occupational_certificate_report"):
				data = base64.b64encode(post.get("business_occupational_certificate_report").read())
				attachment = self.generate_attachment(name, 'business_occupational_certificate_report', data)
				vals.update({'business_occupational_certificate_report': attachment.id})
 
			if post.get("referral_letter"):
				data = base64.b64encode(post.get("referral_letter").read())
				attachment = self.generate_attachment(name, 'referral letter', data)
				vals.update({'referral_letter': attachment.id})

			if post.get("quality_management_system"):
				data = base64.b64encode(post.get("quality_management_system").read())
				attachment = self.generate_attachment(name, 'Quality Management System', data)
				vals.update({'quality_management_system': attachment.id})

			if post.get("qcto_referral_letter"):
				data = base64.b64encode(post.get("qcto_referral_letter").read())
				attachment = self.generate_attachment(name, 'QCTO referral letter', data)
				vals.update({'qcto_referral_letter': attachment.id})

			try:
				#create  Provider User
				group_list = []
				Group = request.env['res.groups'].sudo()
				## Applying Portal and Provider groups to Provider related user.
				group = Group.search([('name','=','PROVIDER')])
				group_list.append((4, group.id)) if group else False
				etqa_user = request.env.ref('inseta_etqa.group_etqa_user')
				provider_user = request.env.ref('inseta_etqa.group_approved_provider')
				# group_list.append((4, etqa_user.id))
				group_list.append((4, provider_user.id))

				## Removing Contact Creation and Employee group from Provider related user.
				groups= Group.search(['|',('name', '=', 'Contact Creation'),('name','=','Employee')])
				for group in groups:
					tup = (3,group.id)
					group_list.append(tup)

				password =  ''.join(random.choice('admin') for _ in range(10))
				provider_id = request.env['inseta.provider.accreditation'].sudo().create(vals)
				inputCampusDetails = json.loads(post.get('campusDetails'))  # A list of records
				for camp in inputCampusDetails:
					delivery_vals = {
						'name': camp.get('campusName'),
						'contact_person_name': camp.get('contactperson'),
						'contact_person_surname': camp.get('contactpersonSurname'),
						'contact_person_tel': camp.get('contactphone'),
						'contact_person_cell': camp.get('contactcell'),
						'contact_person_email': camp.get('campusEmail'),
						'campus_address': camp.get('campusAddr'),
						'provider_id': provider_id.id,
						}
					delivery_id = request.env['inseta.delivery.center'].create(delivery_vals)

					contact_vals = {
						'name': camp.get('contactperson'),
						'contact_person_surname': camp.get('contactpersonSurname'),
						'contact_person_tel': camp.get('contactphone'),
						'contact_person_cell': camp.get('contactcell'),
						'contact_person_email': camp.get('campusEmail'),
						# 'campus_address': camp.get('campusAddr'),
						'provider_id': provider_id.id,
						}
					contact_id = request.env['inseta.provider.contact'].create(contact_vals)
					provider_id.write({
						'delivery_center_ids': [(4, delivery_id.id)],
						'provider_contact_person_ids': [(4, contact_id.id)]
						})
				 
				provider_id.write({
				'provider_skill_accreditation_ids': [
					(0, 0, {'programme_id': int(rec) if rec else False, 
					'provider_accreditation_skill_id': provider_id.id}) for rec in request.httprequest.form.getlist('provider_skill_programme')],
				'provider_learnership_accreditation_ids': [
					(0, 0, {'programme_id': int(rec) if rec else False, 
					'provider_accreditation_learnership_id': provider_id.id}) for rec in request.httprequest.form.getlist('provider_learning_programme')],

				'provider_qualification_ids': [
					(0, 0, {'qualification_id': int(rec) if rec else False, 
					'provider_accreditation_qualification_id': provider_id.id}) for rec in request.httprequest.form.getlist('qualification_ids')],

				'provider_unit_standard_ids': [
					(0, 0, {'programme_id': int(rec) if rec else False, 
					'provider_accreditation_unit_standard_id': provider_id.id}) for rec in request.httprequest.form.getlist('provider_unit_standard_ids')],
				})
				'''This error occurs if no login email found,
				msg = _("You cannot create a new user from here.\n 
				To create new user please go to configuration panel.")'''

				user_vals = {
					'name' : f"{vals.get('provider_name')}",
					'first_name': vals.get('provider_name'),
					'last_name': '',
					'login' : vals.get('email'), 
					'password': password 
				}
				_logger.info("Creating provider User...")
				User = request.env['res.users'].sudo()
				user = User.search([('login', '=', user_vals.get('login'))])
				if user:
					pass 
					# user.write(user_vals)
				else:
					user = User.create(user_vals)
					user.sudo().write({'groups_id':group_list})
				#set user credentails before creating a provider
				provider_id.update({'user_id': user.id, 'password': password})
				provider_id.action_submit_button()

				_logger.info('Provider Successfully Registered!')
				return json.dumps({'status': True, 'message': "Form Submitted!"})
			except Exception as ex:
				_logger.error('Error Occured while registering Provider')
				_logger.exception(ex)
				return json.dumps({'status': False, 'message': f"{str(ex)}"})

	# Assessor / Moderator registration 
	@http.route(['/moderator-registration', '/assessor-registration'], type='http', auth='public', website=True, website_published=True)
	def moderator_assessor_registration(self):
		# raise ValidationError([rec.id for rec in request.env['res.nationality'].sudo().search([])])
		quality_assurance_id = request.env.ref('inseta_etqa.data_inseta_quality_assurance15')
		vals = {
			"titles": request.env["res.partner.title"].sudo().search([]),
			"disability_statuses": request.env['res.disability'].sudo().search([]),
			"country": request.env['res.country'].sudo().search([('code', '=', 'ZA')]),
			"nationalities": request.env['res.nationality'].sudo().search([('active', '=', True)]),
			"cities": request.env['res.city'].sudo().search([]),
			"municipalities": request.env['res.municipality'].sudo().search([]),
			"suburbs": request.env['res.suburb'].sudo().search([]),
			"equities": request.env['res.equity'].sudo().search([]),
			"alternativetype": request.env['res.alternate.id.type'].sudo().search([]),
			"langs": request.env['res.lang'].sudo().search([('active', '=', True)]),
			"unit_standard_ids": request.env['inseta.unit.standard'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"qualification_ids": request.env['inseta.qualification'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"skill_programmes_ids": request.env['inseta.skill.programme'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"learning_programmes_ids": request.env['inseta.learner.programme'].sudo().search([('quality_assurance_id', '=', quality_assurance_id.id),('active', '=', True)]),
			"reg_date": fields.Date.today(),
			"popi_act_status_id": request.env["res.popi.act.status"].sudo().search([('active', '=', True)]),
			"statssa_area_code_id": request.env["res.statssa.area.code"].sudo().search([('active', '=', True)]),
			"school_emis_id": request.env["res.school.emis"].sudo().search([('active', '=', True)], limit=100),
			
		}
		return request.render("theme_inseta.assessor_moderator_register", vals)

	# moderator / assessor registration form post
	@http.route(['/moderator_assessor_registration_ajax'], type='http', methods=['POST'],  website=True, auth="public", csrf=False)
	def moderator_assessor_registration_ajax(self, **post):
		"""
		Returns:
			json: JSON reponse
		"""
		_logger.info('Creating Assessor Register ...')
		if post.get('checkConfirm', False):
			try:
				moderator_register_type = post.get("reqister_type")#  == "on"
				assessor_no = post.get("InputAssessorNo") if post.get("InputAssessorNo",False) != "" else False
				assessor_id = request.env['inseta.assessor'].sudo().search([('id_no', '=', assessor_no)], limit=1)
				passport = post.get("inputIdNo") if post.get("inputIdNo", "") else post.get("inputPassportNo")
				# raise ValidationError(passport)
				vals = {
					"title_id": post.get('inputTitle', False),
					"first_name": post.get("inputFname"),
					"last_name": post.get("inputLname"),
					"middle_name": post.get("inputMname", ""),
					"initials": post.get("inputInitials"),
					"passport_no": passport, # post.get("inputPassportNo", ""),
					"id_no": passport, # post.get("inputIdNo") if post.get("inputIdNo", "") else post.get("inputPassportNo"),
					"alternateid_type_id": post.get("selectAlternativeType",False) if post.get("selectAlternativeType",False) != "" else False,
					"birth_date": format_to_odoo_date(post.get("inputDob",'')),
					"gender_id": 1 if post.get("inputGender") == 'male' else 2,
					#phone, cell and fax is submitted in format 0803 527 9300. Remove the first digit and add the dialling code
					"cell_phone_number": f"+{post.get('inputCellDialCode','')}{post.get('inputCellPhone','')[1:]}",
					"telephone_number": f"+{post.get('inputTelDialCode')}{post.get('inputTel','')[1:]}" if post.get('inputTel') else False,
					"fax_number": f"+{post.get('inputFaxDialCode')}{post.get('inputFax','')[1:]}" if post.get('inputFax') else False,
					"email": post.get("inputEmail"),#  if validate_email(post.get("inputEmail")) else False,
					"physical_code": post.get("inputPhysicalCode", ""),
					"physical_address1": post.get("inputPhysicalAddr1",""),
					"physical_address2": post.get("inputPhysicalAddr2",""),
					"physical_address3": post.get("inputPhysicalAddr3",""),
					"physical_province_id": post.get("selectPhysicalProvince",False) if post.get("selectPhysicalProvince",False) != "" else False,
					"physical_city_id": post.get("selectPhysicalCity",False) if post.get("selectPhysicalCity",False) != "" else False,
					"physical_municipality_id": post.get("selectPhysicalMunicipality",False) if post.get("selectPhysicalMunicipality",False) != "" else False,
					"physical_suburb_id": post.get("selectPhysicalSuburb",False) if post.get("selectPhysicalSuburb",False) != "" else False,
					"physical_urban_rural": post.get("selectPhysicalUrbanRural", "").title(),
					"use_physical_for_postal_addr": True if post.get("checkUsePhysicalForPostal") == "on" else False,
					"is_permanent_consultant": True if post.get("is_permanent_consultant") == "on" else False,
					"postal_code": post.get("inputPostalCode", False),
					"postal_address1": post.get("inputPostalAddr1",""),
					"postal_address2": post.get("inputPostalAddr2",""),
					"postal_address3": post.get("inputPostalAddr3",""),
					"postal_suburb_id": post.get("selectPostalSuburb", False) if post.get("selectPostalSuburb",False) != "" else False,
					"postal_city_id": post.get("selectPostalCity",False) if post.get("selectPostalCity",False) != "" else False,
					"postal_municipality_id": post.get("selectPostalMunicipality", False) if post.get("selectPostalMunicipality",False) != "" else False,
					"postal_province_id": post.get("selectPostalProvince",False) if post.get("selectPostalProvince",False) != "" else False,
					"postal_urban_rural": post.get("selectPostalUrbanRural","").title(),
					"equity_id": post.get("selectEquity") if post.get("selectEquity",False) != "" else False,
					"qualification_document_ids": False,
					"unit_standard_ids": [(4, rec) for rec in request.httprequest.form.getlist('unit_standard_ids')] if post.get("unit_standard_ids") != "" else False,
					"qualification_ids": [(4, rec) for rec in request.httprequest.form.getlist('qualification_ids')] if post.get("qualification_ids",False) != "" else False,
					"disability_id": post.get("selectDisabilityStatus") if post.get("selectDisabilityStatus",False) != "" else False,
					"home_language_id": post.get("selectHomeLanguage") if post.get("selectHomeLanguage",False) != "" else False,
					"nationality_id": post.get("selectNationality") if post.get("selectNationality",False) != "" else False,
					"popi_act_status_id": post.get("popi_act_status_id") if post.get("popi_act_status_id",False) != "" else False,
					"statssa_area_code_id": post.get("statssa_area_code_id") if post.get("statssa_area_code_id",False) != "" else False,
					"school_emis_id": post.get("school_emis_id") if post.get("school_emis_id",False) != "" else False,
					"popi_act_status_date": format_to_odoo_date(post.get("popi_act_status_date",'')),
					"latitude_degree": post.get("inputLatitude"),
					"longitude_degree": post.get("inputLongtitude"),
					"is_confirmed": True if post.get("checkConfirm") == "on" else False,
					"job_title": post.get("job_title",""),
					"assessor_id": assessor_id.id if moderator_register_type == "on" else False,
				}
				if moderator_register_type == "on":
					# Updating the moderator with Assessors unit standards
					assessor_unit_standard_ids = assessor_id.mapped('unit_standard_ids')
					assessor_qualification_ids = assessor_id.mapped('qualification_ids')
					vals['unit_standard_ids'] = [(4, rec.unit_standard_id.id) for rec in assessor_unit_standard_ids]
					vals['qualification_ids'] = [(4, rec.qualification_id.id) for rec in assessor_qualification_ids]

				_logger.info(f"POST Assesor DATA {vals}")
				# #add attachment upload
				name = f"{vals.get('first_name')} {vals.get('middle_name')} {vals.get('last_name')}",
				model = 'inseta.moderator.register' if moderator_register_type == "on" else 'inseta.assessor.register'
				if post.get("qualification_document_ids"):
					data = base64.b64encode(post.get("qualification_document_ids").read())
					attachment = self.generate_attachment(name, 'Qualification Document', data, model)
					vals.update({'qualification_document_ids':  [(6, 0, [attachment.id])]})

				if post.get("statement_of_result_ids"):
					data = base64.b64encode(post.get("statement_of_result_ids").read())
					attachment = self.generate_attachment(name, 'Statement of result', data, model)
					vals.update({'statement_of_result_ids':  [(6, 0, [attachment.id])]})

				if post.get("additional_document_ids"):
					data = base64.b64encode(post.get("additional_document_ids").read())
					attachment = self.generate_attachment(name, 'Additional documents', data, model)
					vals.update({'additional_document_ids':  [(6, 0, [attachment.id])]})

				if post.get("id_document_ids"):
					data = base64.b64encode(post.get("id_document_ids").read())
					attachment = self.generate_attachment(name, 'Identity documents', data, model)
					vals.update({'id_document_ids':  [(6, 0, [attachment.id])]})

				if post.get("cv_ids"):
					data = base64.b64encode(post.get("cv_ids").read())
					attachment = self.generate_attachment(name, 'CV', data, model)
					vals.update({'cv_ids':  [(6, 0, [attachment.id])]})

				if post.get("fileCodeOfConduct"):
					data = base64.b64encode(post.get("fileCodeOfConduct").read())
					attachment = self.generate_attachment(name, 'Code of Conduct', data, model)
					vals.update({'code_of_conduct': attachment.id})
				# create  assessor / moderator User
				group_list = []
				Group = request.env['res.groups'].sudo()
				## Applying Portal and Provider groups to Provider related user.
				group = request.env.ref('inseta_etqa.group_moderator_access_user') if moderator_register_type == "on" else request.env.ref('inseta_etqa.group_accessor_access_user')
				group_list.append((4, group.id)) if group else False
				base_user = request.env.ref('base.group_user')
				group_list.append((4, base_user.id))

				## Removing Contact Creation and Employee group from Provider related user.
				groups= Group.search(['|',('name', '=', 'Contact Creation'),('name','=','Employee')])
				for group in groups:
					tup = (3,group.id)
					group_list.append(tup)

				password =  ''.join(random.choice('admin') for _ in range(10))
				usr_name = f"{vals.get('first_name')} {vals.get('middle_name')} {vals.get('last_name')}"
				login_mail = vals.get('email'),
				if not login_mail:
					raise ValidationError("Name / Email must be valid")
				user_vals = {
					'name' : usr_name,
					'first_name': vals.get('first_name'),
					'last_name': vals.get('last_name'),
					'login' : ''.join(login_mail),
					'password': password,
				}
				_logger.info("Creating Assessor User...")
				User = request.env['res.users'].sudo()
				user = User.search([('login', '=', vals.get('email'))])
				if user:
					pass 
					# user.write(user_vals)
				else:
					user = request.env['res.users'].sudo().create(user_vals)
					user.sudo().write({'groups_id':group_list})
				
				# set user credentails before creating an provider
				vals.update({'user_id': user.id, 'password': password})
				register_obj = request.env[model].sudo().create(vals)
				register_obj.action_submit_button()

				_logger.info('Assessor / MODERATOR Successfully Registered!')
				return json.dumps({'status': True, 'message': "Form Submitted!"})
			except Exception as ex:
				_logger.error('Error Occured while registering Assessor')
				_logger.exception(ex)
				return json.dumps({'status': False, 'message': f"{str(ex)}"})

