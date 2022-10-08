import base64
import json
import logging
from os import name
import re
import timeit

from xlrd import open_workbook

from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def cast_to_integer(val):
    """Convert float to integer
    Args:
        val (float): The item to convert
    Returns:
        int: the converted item
    """
    return int(val) if isinstance(val, float) else val

def get_wspstate(legacy_wspstatusid):
    """
        ('draft', 'Draft'), # legacy equiv => Created  - 8
        ('pending_validation', 'Pending Validation'), #legacy equiv =>  Pending 1
        ('rework', 'Pending Additional Information'), #legacy equiv =>  Query 5
        ('rework_skill_admin', 'Pending Additional Information'), #skill specs asks skill admin to rework
        ('rework_skill_spec', 'Pending Additional Information'), #skill mgr asks skill spec to rework
        ('pending_assessment', 'Pending Assessment'), #Evaluation In Progress 18
        ('pending_evaluation', 'Pending Evaluation'), #Recommended for Approval 17
        ('approve','Approved'), # Accepted = 6
        ('reject','Rejected') #Rejected = 4
    """

    if legacy_wspstatusid == 8:
        return 'draft'
    elif legacy_wspstatusid == 1:
        return 'pending_validation'
    elif legacy_wspstatusid == 5:
        return 'rework'
    elif legacy_wspstatusid == 18:
        return 'pending_assessment'
    elif legacy_wspstatusid == 17:
        return 'pending_evaluation'
    elif legacy_wspstatusid in (6,3):
        return 'approve'
    elif legacy_wspstatusid == 4:
        return 'reject'
    else:
        return 'draft'


def get_dgstate(legacy_dgstatusid):
    """
1	Pending	
2	Submitted	
3	Evaluated	E
4	Query	E
5	Rejected	A
6	Approved	A
8	Recommended	
    """

    if legacy_dgstatusid == 1:
        return 'draft'
    elif legacy_dgstatusid == 2:
        return 'submit'
    elif legacy_dgstatusid == 3:
        return 'pending_approval2'
    elif legacy_dgstatusid == 4:
        return 'rework'
    elif legacy_dgstatusid == 5:
        return 'reject'
    elif legacy_dgstatusid == 6:
        return 'approve'
    elif legacy_dgstatusid == 8:
        return 'recommend'

def get_dgevalstate(eval_stateid):
    """
1	Decline
2	Recommended
3	Query
    """

    if eval_stateid == 1:
        return 'Query'
    elif eval_stateid == 2:
        return 'Verified'
    elif eval_stateid == 3:
        return 'Query'

class SkillsDataImportWizard(models.TransientModel):
    _name = 'skills.data.import.wizard'
    _description = "Import Skiils Data"

    file_type = fields.Selection(
        [('xlsx', 'XLSX File')], default='xlsx', string='File Type')
    file = fields.Binary(string="Upload File (.xlsx)")
    file_col_count = fields.Selection(
        [('8', '8 Columns'), ('unknown', 'Unknown')], string='No. of File Columns')
    file_name = fields.Char("File Name")

    model_name = fields.Char()
    model_id = fields.Many2one('ir.model')
    is_partner_addr = fields.Boolean('Is partner Address?')
    # model = fields.Selection([
    #         ('res.partner.title', 'Title'),
    #         ('res.alternate.id.type', 'Alternate ID type'),
    #         ('res.partner', 'Partners'),
    #         ('inseta.sdf.register', 'SDF Register'),
    #         ('inseta.sdf', 'SDF'),
    #         ('inseta.organisation', 'Organisation'),
    #     ],
    #     string='Skills Model', required=True
    # )
    dgtype = fields.Selection([
        ('LRN','Learnership'),
        ('INT','Internship'),
        ('SP','Skills Programme'),
        ('BUR','BUR')
    ])

    def read_file(self, index=0):
        if not self.file:
            raise ValidationError('Please select a file')

        file_datas = base64.decodebytes(self.file)
        workbook = open_workbook(file_contents=file_datas)
        sheet = workbook.sheet_by_index(index)
        file_data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
        file_data.pop(0)
        return file_data

    def action_import(self):
        file_data = self.read_file()
        country_sa = self.env['res.country'].search([('code', '=', 'ZA')])
        model = self.model_id.model
        Model = self.env[model]

        if self.file_col_count == "8":
            if model in ("res.city", "res.suburb", "res.municipality", "res.district"):
                records = Model.search([])
                #records.write({'active': True})
                records.unlink()
            # else:
            #     records = Model.search([])
            #     records.write({'active': False})

# --------------------------------------------
# Migrate dbo.dgapplication.csv to inseta.dgapplication
# --------------------------------------------
        if model == "inseta.dgapplication":
            _logger.info("Importing dg application ...")
            loop = 0
            for count, row in enumerate(file_data):
                organisation = self.env['inseta.organisation'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
                if organisation:
                    if "." in row[9]:
                        submit_dt =  row[9].split(".") 
                    elif "+" in row[9]:
                        submit_dt =  row[9].split("+") 
                    else:
                        submit_dt =  row[9].split(" ") 


                    if "." in row[11]:
                        apprv_dt = row[11].split(".")
                    elif "+" in row[11]:
                        apprv_dt = row[11].split("+")
                    else:
                        apprv_dt = row[11].split(" ")


                    if "." in row[13]:
                        rjct_dt = row[13].split(".")
                    elif "+" in row[13]:
                        rjct_dt = row[13].split("+")
                    else:
                        rjct_dt = row[13].split(" ")

                    if "." in row[7]:
                        due_dt = row[7].split(".")
                    elif "+" in row[7]:
                        due_dt = row[7].split("+")
                    else:
                        due_dt = row[7].split(" ")

                    val = dict(
                        legacy_system_id = int(row[0]),
                        # organisation_id = organisation.id,
                        # financial_year_id = self._get_object_by_legacy_id('res.financial.year', row[2]),
                        # state = get_dgstate(cast_to_integer(row[3])),
                        is_ceo_approved = True if cast_to_integer(row[3]) in (6,8) else False,
                        decline_comment = "Declined" if cast_to_integer(row[3]) == 5 else ' ',
                        # dgtype_id = self._get_object_by_legacy_id('res.dgtype', row[4]) if not cast_to_integer(row[3]) == 1 else self.env.ref('inseta_dg.data_dgtypelnr1').id,
                        # dgfundingwindow_id = self._get_object_by_legacy_id('inseta.dgfunding.window', row[5]),
                        # name = row[6],
                        # due_date =  due_dt and due_dt[0] or False,
                        # submitted_date = submit_dt and submit_dt[0] or False,
                        # submitted_by = self._get_object_by_legacy_id('res.users', row[10]) or self.env.user.id, 
                        # approved_date = apprv_dt and  apprv_dt[0] or False,
                        # approved_by = self._get_object_by_legacy_id('res.users', row[12]) or self.env.user.id, 
                        # rejected_date = rjct_dt and rjct_dt[0] or False,
                        # rejected_by =  self._get_object_by_legacy_id('res.users', row[14]) or self.env.user.id, 
                        # create_date = row[15].split(".")[0],
                        # create_uid =  self._get_object_by_legacy_id('res.users', row[16]) or self.env.user.id, 
                        # write_date = row[17].split(".")[0],
                        # write_uid = self._get_object_by_legacy_id('res.users', row[18]) or self.env.user.id,
                    )
                    #_logger.info(f"{json.dumps(val, indent=4)}")
                    #only create. we will not update since write operation is time consuming 
                    #obj = Model.create(val) 
                    obj = Model.search([('legacy_system_id', '=', val.get('legacy_system_id'))])
                    if obj:
                        obj.write(val)
                    # else:
                    #     obj = Model.create(val)
                    _logger.info(f"{json.dumps(obj.id, indent=4)}")
                    # Model.create(val) if not user_dict else Model.write(val)
                    if loop == 100:
                        _logger.info('100 User records created ')
                        self.env.cr.commit()
                        #reset loop
                        loop = 0
                    loop += 1

# --------------------------------------------
# Migrate dbo.dgapplication.csv to inseta.dgapplication
# --------------------------------------------
        if model == "inseta.dgapplicationdetails":
            _logger.info("Importing dg applicationdetails ...")

            if self.is_partner_addr:
                loop = 0
                for count, row in enumerate(file_data):
                    """
                    contact_person_name = fields.Char()
                    contact_person_email = fields.Char()
                    contact_person_phone = fields.Char() #for migration of dborganisation contact
                    contact_person_mobile = fields.Char() #for migration of dborganisation contact
                    contact_person_idno = fields.Char() #for migration of dborganisation contact
                    """
                    dg = self.env['inseta.dgapplication'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)

                    val = dict(
                        contact_person_name = row[3],
                        contact_person_surname = row[4],
                        contact_person_idno = row[5],
                        contact_person_email = row[6],
                        contact_person_phone = row[7],
                        contact_person_mobile = row[8]
                    )
                    if dg:
                        recs = self.env['inseta.dgapplicationdetails'].search([('dgapplication_id','=', dg.id)])
                        recs.write(val)
                    _logger.info(f"{json.dumps(val, indent=4)}")
                    if loop == 100:
                        _logger.info('100 records updated ')
                        self.env.cr.commit()
                        loop = 0
                loop += 1
            else:
                if self.dgtype in ('BUR',):
                    loop = 0
                    for count, row in enumerate(file_data):
                        dg = self.env['inseta.dgapplication'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
                        if dg:
                            val = dict(
                                legacy_system_id_bursp = int(row[0]),
                                dgapplication_id = dg.id,
                                financial_year_id = dg.financial_year_id.id,
                                organisation_id = dg.organisation_id.id,
                                publicprovider_id = self._get_object_by_legacy_id('res.dgpublicprovider', row[17]), 
                                publicproviderother = row[18],
                                qualification_saqaid = cast_to_integer(row[19]),
                                privateprovider = row[20],
                                privateproviderqualification = row[21],
                                providercode = cast_to_integer(row[38]),
                                provideretqeid = cast_to_integer(row[39]),
                                funding_amount_required = row[44],
                                duration =  cast_to_integer(row[45]),
                                fullqualification_title = row[46],
                                programme_name = row[47],
                                provider_name = row[48],
                                no_learners = cast_to_integer(row[49]),
                                scarcecritical_id  = self._get_object_by_legacy_id('res.dginternshipscarcecritical', row[50]),
                                create_date = row[51].split(".")[0],
                                create_uid =  self._get_object_by_legacy_id('res.users', row[52]) or self.env.user.id, 
                                write_date = row[53].split(".")[0],
                                write_uid = self._get_object_by_legacy_id('res.users', row[54]) or self.env.user.id,
                            )
                            _logger.info(f"{json.dumps(val, indent=4)}")
                            #only create. we will not update since write operation is time consuming 
                            #obj = Model.create(val) 
                            obj = Model.search([('legacy_system_id_bursp', '=', val.get('legacy_system_id_bursp'))])
                            if obj:
                                obj.write(val)
                            else:
                                obj = Model.create(val)
                            _logger.info(f"{json.dumps(obj.id, indent=4)}")
                            if obj and not isinstance(obj, bool):
                                obj._compute_dgtype_code()
                                obj._compute_total_learners()
                                obj._compute_amount_applied()
                                # obj._compute_learnership_code()
                            # Model.create(val) if not user_dict else Model.write(val)
                            if loop == 100:
                                _logger.info('100 User records created ')
                                self.env.cr.commit()
                                #reset loop
                                loop = 0
                        loop += 1
                        
                if self.dgtype in ('LRN',):
                    loop = 0
                    for count, row in enumerate(file_data):
                        dg = self.env['inseta.dgapplication'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
                        if dg:

                            val = dict(
                                legacy_system_id_lrn = int(row[0]),
                                dgapplication_id = dg.id,
                                financial_year_id = dg.financial_year_id.id,
                                organisation_id = dg.organisation_id.id,
                                fundingtype_id = self._get_object_by_legacy_id('res.fundingtype', row[2]),
                                learnership_id = self._get_object_by_legacy_id('inseta.learner.programme', row[3]),
                                learnership_other = row[4],
                                learnership_code = row[5],
                                socio_economic_status_id = self._get_object_by_legacy_id('res.socio.economic.status', row[6]),
                                province_id = self._get_object_by_legacy_id('res.country.state', row[7]),
                                provider_id = self._get_object_by_legacy_id('inseta.provider', row[8]),
                                provider_other = row[9],
                                provider_scope_expirydate = row[10].split(" ")[0] if len(row[10]) > 3 else False,
                                start_date = row[11].split(" ")[0],
                                end_date = row[12].split(" ")[0],
                                no_learners = cast_to_integer(row[13]),
                                disabled = cast_to_integer(row[14]),
                                firsttime_applicant = "Yes" if cast_to_integer(row[15]) == 1 else "No",
                                create_date = row[16].split(".")[0],
                                create_uid =  self._get_object_by_legacy_id('res.users', row[17]) or self.env.user.id, 
                                write_date = row[18].split(".")[0],
                                write_uid = self._get_object_by_legacy_id('res.users', row[19]) or self.env.user.id,
                            )
                            _logger.info(f"{json.dumps(val, indent=4)}")
                            #only create. we will not update since write operation is time consuming 
                            #obj = Model.create(val) 
                            obj = Model.search([('legacy_system_id_lrn', '=', val.get('legacy_system_id_lrn'))])
                            if obj:
                                obj.write(val)
                            else:
                                obj = Model.create(val)
                            _logger.info(f"{json.dumps(obj.id, indent=4)}")
                            if obj and not isinstance(obj, bool):
                                obj._compute_dgtype_code()
                                obj._compute_total_learners()
                                obj._compute_amount_applied()

                            #update DG type
                            if cast_to_integer(val.get('socio_economic_status_id')) == 1:
                                obj.dgapplication_id.with_context(allow_write=True).write({'dgtype_id': self.env.ref('inseta_dg.data_dgtypelnr2').id})
                            else:
                                obj.dgapplication_id.with_context(allow_write=True).write({'dgtype_id': self.env.ref('inseta_dg.data_dgtypelnr1').id})
                                # obj._compute_learnership_code()
                            # Model.create(val) if not user_dict else Model.write(val)
                            if loop == 100:
                                _logger.info('100 User records created ')
                                self.env.cr.commit()
                                #reset loop
                                loop = 0
                        loop += 1

                if self.dgtype in ('INT',):
                    loop = 0
                    for count, row in enumerate(file_data):
                        dg = self.env['inseta.dgapplication'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
                        if dg:
                            dur_id = cast_to_integer(row[6])
                            if dur_id == 3:
                                dur = 12
                            elif dur_id == 2:
                                dur = 6
                            else:
                                dur = 3

                            val = dict(
                                legacy_system_id_int = int(row[0]),
                                dgapplication_id = dg.id,
                                financial_year_id = dg.financial_year_id.id,
                                organisation_id = dg.organisation_id.id,
                                programme_name = row[2],
                                start_date = row[3].split(" ")[0],
                                end_date = row[4].split(" ")[0],
                                #row[5] terminationdate
                                duration = dur,
                                scarcecritical_id = self._get_object_by_legacy_id('res.dginternshipscarcecritical', row[7]),
                                create_date = row[8].split(".")[0],
                                create_uid =  self._get_object_by_legacy_id('res.users', row[9]) or self.env.user.id, 
                                write_date = row[10].split(".")[0],
                                write_uid = self._get_object_by_legacy_id('res.users', row[11]) or self.env.user.id,
                            )
                            _logger.info(f"{json.dumps(val, indent=4)}")
                            #only create. we will not update since write operation is time consuming 
                            #obj = Model.create(val) 
                            obj = Model.search([('legacy_system_id_int', '=', val.get('legacy_system_id_int'))])
                            if obj:
                                obj.write(val)
                            else:
                                obj = Model.create(val)
                            _logger.info(f"{json.dumps(obj.id, indent=4)}")
                            if obj and not isinstance(obj, bool):
                                obj._compute_dgtype_code()
                                # obj._compute_total_learners()
                                # obj._compute_amount_applied()
                                # obj._compute_learnership_code()
                            # Model.create(val) if not user_dict else Model.write(val)
                            if loop == 100:
                                _logger.info('100 User records created ')
                                self.env.cr.commit()
                                #reset loop
                                loop = 0
                        loop += 1

# --------------------------------------------
# Migrate dg evaluation
# --------------------------------------------
        if model == "inseta.dgevaluation":
            _logger.info("Importing inseta.dgevaluation...")

            if self.dgtype in ('LRN',):
                loop = 0
                for count, row in enumerate(file_data):
                    dg = self.env['inseta.dgapplication'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
                    dgdtl = self.env['inseta.dgapplicationdetails'].search([('legacy_system_id_lrn','=', cast_to_integer(row[2]))],limit=1) 
                    if dg and dgdtl:

                        val = dict(
                            legacy_system_id_lrn = int(row[0]),
                            dgapplication_id = dg.id,
                            state = 'signed' if dg.state == "recommend" else dg.state,
                            dgapplicationdetails_id = dgdtl.id,
                            no_learners = dgdtl.no_learners,
                            disabled = dgdtl.disabled,
                            total_learners = dgdtl.total_learners,
                            cost_per_student = dg.dgtype_id.cost_per_learner,
                            actual_cost_per_student = dg.dgtype_id.cost_per_learner,
                            cost_per_disabled = dg.dgtype_id.cost_per_disabled,
                            option = "Verified",
                            no_learners_recommended = cast_to_integer(row[3]),
                            disabled_recommended = cast_to_integer(row[4]),
                            no_learners_approved =  cast_to_integer(row[3]) if dg.state in ("approve", "recommend") else 0,
                            disabled_approved =  cast_to_integer(row[4]) if dg.state in ("approve", "recommend") else 0,
                            start_date = row[5].split(" ")[0],
                            end_date = row[6].split(" ")[0],
                            name = row[7],
                            lganumber = row[7],
                            comment =row[8],
                            create_date = row[9].split(".")[0],
                            create_uid =  self._get_object_by_legacy_id('res.users', row[10]) or self.env.user.id, 
                            write_date = row[11].split(".")[0],
                            write_uid = self._get_object_by_legacy_id('res.users', row[12]) or self.env.user.id,
                        )
                        _logger.info(f"{json.dumps(val, indent=4)}")
                        #only create. we will not update since write operation is time consuming 
                        obj = Model.search([('legacy_system_id_lrn', '=', val.get('legacy_system_id_lrn'))])
                        if obj:
                            obj.write(val)
                        else:
                            obj = Model.create(val)
                        _logger.info(f"{json.dumps(obj.id, indent=4)}")
                        if obj and not isinstance(obj, bool):
                            obj._compute_is_learnership()
                            obj._compute_total_recommended()
                            obj._compute_amount_recommended()
                            obj._compute_total_learners_approved()

                        dgdtl.update({
                            'disabled_approved':  cast_to_integer(row[4]) if dg.state in ("approve", "recommend") else 0, 
                            'no_learners_approved': cast_to_integer(row[3]) if dg.state in ("approve", "recommend") else 0,
                        })

                        dg._compute_amount_total_applied()
                        dg._compute_total_learners()
                        dg._compute_total_learners_approved()
                        dg._compute_amount_total_approved()
                        if loop == 100:
                            _logger.info('100 eval records created ')
                            self.env.cr.commit()
                            #reset loop
                            loop = 0
                    loop += 1

            if self.dgtype in ('BUR',):
                loop = 0

                for count, row in enumerate(file_data):
                    dg = self.env['inseta.dgapplication'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
                    dgdtl = self.env['inseta.dgapplicationdetails'].search([('legacy_system_id_bursp','=', cast_to_integer(row[2]))],limit=1) 
                    if dg and dgdtl:

                        val = dict(
                            legacy_system_id_bursp = int(row[0]),
                            dgapplication_id = dg.id,
                            state = 'signed' if dg.state == "recommend" else dg.state,
                            dgapplicationdetails_id = dgdtl.id, 
                            option = get_dgevalstate(cast_to_integer(row[3])),
                            lganumber = row[4],
                            name =  row[4],
                            no_learners = dgdtl.no_learners,
                            disabled = dgdtl.disabled,
                            total_learners = dgdtl.total_learners,
                            no_learners_recommended = cast_to_integer(row[5]),
                            amount_total_recommended = row[6],
                            cost_per_student = row[7],
                            actual_cost_per_student = row[7],
                            amount_learners_recommended = row[7],
                           
                            no_learners_approved =  cast_to_integer(row[5]) if dg.state in ("approve", "recommend") else 0,
                            total_learners_approved =  cast_to_integer(row[5]) if dg.state in ("approve", "recommend") else 0,
                            amount_learners_approved = row[7] if dg.state in ("approve", "recommend") else 0.00,
                            amount_total_approved =  row[6] if dg.state in ("approve", "recommend") else 0.00,
                            comment =row[8],

                            create_date = row[9].split(".")[0],
                            create_uid =  self._get_object_by_legacy_id('res.users', row[10]) or self.env.user.id, 
                            write_date = row[11].split(".")[0],
                            write_uid = self._get_object_by_legacy_id('res.users', row[12]) or self.env.user.id,
                        )
                        _logger.info(f"{json.dumps(val, indent=4)}")
                        #only create. we will not update since write operation is time consuming 
                        obj = Model.search([('legacy_system_id_bursp', '=', val.get('legacy_system_id_bursp'))])
                        if obj:
                            obj.write(val)
                        else:
                            obj = Model.create(val)
                        _logger.info(f"{json.dumps(obj.id, indent=4)}")
                        if obj and not isinstance(obj, bool):
                            obj._compute_is_learnership()
                            obj._compute_total_recommended()
                            obj._compute_amount_recommended()
                            obj._compute_total_learners_approved()
                        
                        dgdtl._compute_total_recommended()
                        #dgdtl._compute_amount_recommended()
                        dgdtl._compute_total_learners_approved()
                        dtlvals = {
                            'total_recommended':  cast_to_integer(row[5])  if dg.state in ("pending_approval2", "approve", "recommend") else 0,
                            'no_learners_recommended': cast_to_integer(row[5])  if dg.state in ("pending_approval2", "approve", "recommend") else 0,
                            'amount_learners_recommended': row[7]  if dg.state in ("pending_approval2", "approve", "recommend") else 0,
                            'amount_total_recommended':  row[6]  if dg.state in ("pending_approval2", "approve", "recommend") else 0,
                            'no_learners_approved': cast_to_integer(row[5]) if dg.state in ("approve", "recommend") else 0,
                            'total_learners_approved':  cast_to_integer(row[5]) if dg.state in ("approve", "recommend") else 0,
                            'amount_learners_approved': row[7] if dg.state in ("approve", "recommend") else 0.00,
                            'amount_total_approved':  row[6] if dg.state in ("approve", "recommend") else 0.00,
                        }
                        # _logger.info(f"DTL VALS => {json.dumps(dtlvals)}")
                        # _logger.info(f"DTL ID {dgdtl}")
                        dgdtl.write(dtlvals)

                        dg._compute_amount_total_applied()
                        dg._compute_total_learners()
                        dg._compute_total_learners_approved()
                        dg._compute_amount_total_approved()
                     
                        if loop == 100:
                            _logger.info('100 eval records created ')
                            self.env.cr.commit()
                            #reset loop
                            loop = 0
                    loop += 1

# --------------------------------------------
# Migrate dbo.wspatr to inseta_wspatr
# --------------------------------------------

        if model == "inseta.wspatr":
            _logger.info("Importing wspatr ...")

            wsps = self.env['inseta.wspatr'].search([])
            loop = 0
            for wsp in wsps:
                # small_levy = self.env.ref('inseta_base.data_orgsize_small_levy')
                # small_non_levy = self.env.ref('inseta_base.data_orgsize_small_non_levy')
                # medium  =  self.env.ref('inseta_base.data_orgsize_medium')
                # large =  self.env.ref('inseta_base.data_orgsize_large')

                # orgsize = wsp.organisation_id and wsp.organisation_id.organisation_size_id or False
                # if orgsize and orgsize.id ==  small_levy.id:
                #     size = "Small"
                # elif orgsize and orgsize.id == small_non_levy.id:
                #     size = "Small"
                # elif orgsize and orgsize.id== medium.id: 
                #     size = "Large"
                # elif orgsize and orgsize.id == large.id: 
                #     size = "Large"
                # else:
                #     size = "Small"
                sdf = self.env['inseta_sdf'].search([('partner_id','=',wsp.create_uid.partner_id.id)])
                vals = dict(
                    sdf_id = sdf and sdf.id or False
                )
                wsp.write(vals) 
                _logger.info(f"{json.dumps(wsp.id, indent=4)}")
                # Model.create(val) if not user_dict else Model.write(val)
                if loop == 100:
                    _logger.info('100 WSP records updated')
                    self.env.cr.commit()
                    #reset loop
                    loop = 0
                loop += 1
 
            # loop = 0
            # for count, row in enumerate(file_data):
            #     organisation = self.env['inseta.organisation'].search([('legacy_system_id','=', cast_to_integer(row[1]))],limit=1)
            #     if organisation:
            #         submit_dt = row[7].split(" ")
            #         apprv_dt = row[9].split(" ")
            #         rjct_dt = row[11].split(" ")
            #         val = dict(
            #             user_group_id = self.env.ref('inseta_skills.group_sdf_user',raise_if_not_found=False).id,
            #             legacy_system_id = int(row[0]),
            #             organisation_id = organisation.id,
            #             financial_year_id = self._get_object_by_legacy_id('res.financial.year', row[2]),
            #             state = get_wspstate(cast_to_integer(row[3])),
            #             wpsstatus_id = self._get_object_by_legacy_id('res.wspstatus', row[3]),
            #             due_date =  row[5].split(" ")[0],
            #             submitted_date = submit_dt and submit_dt[0] or False,
            #             submitted_by = self._get_object_by_legacy_id('res.users', row[8]) or self.env.user.id, 
            #             approved_date = apprv_dt and  apprv_dt[0] or False,
            #             approved_by = self._get_object_by_legacy_id('res.users', row[10]) or self.env.user.id, 
            #             rejected_date = rjct_dt and rjct_dt[0] or False,
            #             rejected_by =  self._get_object_by_legacy_id('res.users', row[12]) or self.env.user.id, 
            #             create_date = row[13].split(" ")[0],
            #             create_uid =  self._get_object_by_legacy_id('res.users', row[14]) or self.env.user.id, 
            #             write_date = row[15].split(" ")[0],
            #             write_uid = self._get_object_by_legacy_id('res.users', row[16]) or self.env.user.id,
            #             is_imported = True
            #         )
            #         # _logger.info(f"{json.dumps(val, indent=4)}")
            #         #only create. we will not update since write operation is time consuming 
            #         obj = Model.create(val) 
            #         _logger.info(f"{json.dumps(obj.id, indent=4)}")
            #         # Model.create(val) if not user_dict else Model.write(val)
            #         if loop == 100:
            #             _logger.info('100 User records created ')
            #             self.env.cr.commit()
            #             #reset loop
            #             loop = 0
            #     loop += 1

# --------------------------------------------
# Migrate dbo.user to res_users
# --------------------------------------------
        if model == "res.users":
            """
                self.env.cr.execute('''UPDATE res_partner SET mobile='123' WHERE id=5''')
                self.env.cr.execute('''INSERT INTO res_partner(name) VALUES('ABC')''')

            """
            _logger.info("Importing res.users ...")

            # starttime = timeit.default_timer()
            # _logger.info(f"The start time RAW SQL is : {starttime}")
            loop = 0
            for count, row in enumerate(file_data):
                self.env.cr.execute("""SELECT id, id_no FROM res_partner where id_no = '%s' limit 1""" % cast_to_integer(row[3]))
                partner_dict = self.env.cr.dictfetchone()
                if partner_dict:
                    # r = {
                    #     'id_no': partner_dict.get('id_no'),
                    #     'partner_id': partner_dict.get('id')
                    # }
                    _logger.info("Related Partner ID => %s" % partner_dict.get('id'))
                    
                self.env.cr.execute("""SELECT login, partner_id FROM res_users where login = '%s' """ % cast_to_integer(row[8]))
                user_dict = self.env.cr.dictfetchone()
                curr_partner_id = False
                if user_dict:
                    curr_partner_id = user_dict.get('partner_id')
                    # _logger.info("User Login => %s" %  json.dumps(user_dict.get('login')))
                # _logger.info(f"The time difference RAW SQL is : {timeit.default_timer() - starttime}") 

                # starttime2 = timeit.default_timer()
                # _logger.info(f"The start time ORM is:  {starttime2}")

                val = dict(
                    partner_id = partner_dict.get('id') if partner_dict else curr_partner_id,
                    legacy_system_id = int(row[0]),
                    first_name = row[1],
                    last_name = row[2],
                    name = f"{row[1]} {row[2]}",
                    id_no = str(cast_to_integer(row[3])),
                    user_phone = str(cast_to_integer(row[4])),
                    user_mobile = str(cast_to_integer(row[5])),
                    user_faxnumber = cast_to_integer(row[6]),
                    user_email = row[7],
                    login = str(cast_to_integer(row[8])),
                    password = str(cast_to_integer(row[8])),
                    # active = True if int(row[10]) == 1 else False 
                    active = True, #activate all users to prevent "You cannot perform this action on an archived user."
                )
                #only create. we will not update since write operation is time consuming 
                if not user_dict:
                    Model.create(val) 
                    # Model.create(val) if not user_dict else Model.write(val)
                    if loop == 100:
                        _logger.info('100 User records created ')
                        self.env.cr.commit()
                        #reset loop
                        loop = 0
                loop += 1
                # _logger.info(f"The time difference ORM is: {timeit.default_timer() - starttime2}") 

        loop = 0
        # self.env.cr.execute('''BEGIN; ALTER TABLE res_partner DISABLE TRIGGER ALL;''')
        for count, row in reversed(list(enumerate(file_data))):
            error = []
            if self.file_col_count == "8":

                col0 = int(row[0])  # legacy system ID
                col1 = row[1]  # name
                col2 = row[2]  # saqacode

                if model == "res.country.state": #migrate Province
                    #by default odoo imports states for SA. we just need to update the saqacode and legacy ID
                    #adjust freestate to Free State before importing
                    state = Model.search([('name', '=', col1)])
                    state.write({'legacy_system_id': col0,'saqacode': int(col2)})

                elif model == "res.district": #migrate District
                    province_id = self._get_object_by_legacy_id('res.country.state', col2)
                    vals = {'legacy_system_id': col0, 'name': col1, 'country_id': country_sa.id, 'province_id': province_id}
                    d = Model.create(vals)
                    _logger.info(f"District ID {d.id}")

                elif model == "res.municipality": #migrate municipality
                    district_id = self._get_object_by_legacy_id('res.district', col2)
                    vals = {'legacy_system_id': col0, 
                    'name': col1, 'country_id': country_sa.id, 'district_id': district_id,
                    'urban_rural': 'Urban' if row[3] == 1 else 'Rural'}
                    m = Model.create(vals)
                    _logger.info(f"Municipality ID {m.id}")

                elif model == "res.city": #migrate city
                    muni_id = self._get_object_by_legacy_id('res.municipality', col2)
                    district_id = self._get_object_by_legacy_id('res.district', row[3])
                    vals = {'legacy_system_id': col0, 
                    'name': col1, 'country_id': country_sa.id, 'district_id': district_id,
                    'municipality_id': muni_id}
                    r = Model.create(vals)
                    _logger.info(f"city ID {r.id}")

                elif model == "res.suburb": #migrate suburb
                    postcode = int(row[2])
                    city = row[3]
                    muni = row[4]
                    district = row[5]
                    city_id = self._get_object_by_legacy_id('res.city', city)
                    muni_id = self._get_object_by_legacy_id('res.municipality', muni)
                    district_id = self._get_object_by_legacy_id('res.district', district)

                    vals = {'legacy_system_id': col0, 
                    'name': col1, 'country_id': country_sa.id, 
                    'postal_code': postcode,
                    'city_id': city_id,
                    'district_id': district_id,
                    'municipality_id': muni_id}
                    s = Model.create(vals)
                    _logger.info(f"suburb ID {s.id}")

                else:
                    saqa = int(col2) if isinstance(col2, float) else col2
                    data = {'legacy_system_id': col0, 'name': col1, 'saqacode': saqa}
                    if model == "res.partner.title":
                        data['shortcut'] = col1

                    obj = Model.search([('legacy_system_id', '=', data.get('legacy_system_id'))])
                    if obj:
                        obj.write(data)
                    else:
                        Model.create(data)
            else:
                col0 = int(row[0])  # legacy system ID
                col1 = row[1]  # name
                col2 = row[2]  # saqacode
                if model == "res.school.emis":
                    data = {
                        'legacy_system_id': col0,
                        'name': col1,
                        'saqacode': int(col2) if isinstance(col2, float) else col2,
                        "province_id": self._get_object_by_legacy_id('res.country.state', row[3])
                    }
                    Model.create(data)
                if model == "res.statssa.area.code":
                    data = {
                        'legacy_system_id': col0,
                        'name': col1,
                        'saqacode': int(col2) if isinstance(col2, float) else col2,
                        "province_id": self._get_object_by_legacy_id('res.country.state', row[8])
                    }
                    Model.create(data)
# --------------------------------------------
# Migrate ofo tables 
# --------------------------------------------
                if model == "res.ofo.majorgroup":
                    vals = dict(
                        legacy_system_id=int(row[0]),  # legacy system ID
                        code = int(row[1]) if isinstance(row[1], float) else row[1],
                        name = row[2],
                        ofoyear = int(row[3]) if isinstance(row[3], float) else row[3],
                        version_no = int(row[4]) if isinstance(row[4], float) else row[4],
                        create_date = row[5].split(" ")[0],
                        write_date = row[7].split(" ")[0],
                    )
                    obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    if obj:
                        obj.write(vals)
                    else:
                        Model.create(vals)
                if model == "res.ofo.submajorgroup":
                    vals = dict(
                        legacy_system_id=int(row[0]),  # legacy system ID
                        major_group_id = self._get_object_by_legacy_id('res.ofo.majorgroup', row[1]),
                        code = int(row[2]) if isinstance(row[2], float) else row[2],
                        name = row[3],
                        create_date = row[4].split(" ")[0],
                        write_date = row[6].split(" ")[0],
                    )
                    obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    if obj:
                        obj.write(vals)
                    else:
                        Model.create(vals)
                if model == "res.ofo.unitgroup":
                    vals = dict(
                        legacy_system_id=int(row[0]),  # legacy system ID
                        sub_major_group_id = self._get_object_by_legacy_id('res.ofo.submajorgroup', row[1]),
                        code = int(row[2]) if isinstance(row[2], float) else row[2],
                        name = row[3],
                        create_date = row[4].split(" ")[0],
                        write_date = row[6].split(" ")[0],
                    )
                    obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    if obj:
                        obj.write(vals)
                    else:
                        Model.create(vals)
                if model == "res.ofo.occupation":
                    vals = dict(
                        legacy_system_id=int(row[0]),  # legacy system ID
                        unit_group_id = self._get_object_by_legacy_id('res.ofo.unitgroup', row[1]),
                        code = int(row[2]) if isinstance(row[2], float) else row[2],
                        name = row[3],
                        create_date = row[4].split(" ")[0],
                        write_date = row[6].split(" ")[0],
                    )
                    obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    if obj:
                        obj.write(vals)
                    else:
                        Model.create(vals)
                if model == "res.ofo.specialization":
                    vals = dict(
                        legacy_system_id=int(row[0]),  # legacy system ID
                        occupation_id = self._get_object_by_legacy_id('res.ofo.occupation', row[1]),
                        code = int(row[2]) if isinstance(row[2], float) else row[2],
                        name = row[3],
                        create_date = row[4].split(" ")[0],
                        write_date = row[6].split(" ")[0],
                    )
                    _logger.info(f"Ofo Spec {row[3]}")
                    # obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    # if obj:
                    #     obj.write(vals)
                    # else:
                    Model.create(vals)
# --------------------------------------------
# Migrate dbo.person to res_partner
# --------------------------------------------
                elif model == "res.partner" :
                    if self.is_partner_addr:
                        _logger.info('starting person adddres import...')
                        personid = int(row[1])
                        partner = Model.search([('legacy_system_id','=', personid)],limit=1)
                        u_r = False
                        row9 = int(row[9])
                        if row9 == 1:
                            u_r = 'Urban'
                        elif row9 == 2:
                            u_r = 'Rural'

                        pu_r = False
                        row19 = cast_to_integer(row[19])
                        if row19 == 1:
                            pu_r = 'Urban'
                        elif row19 == 2:
                            pu_r = 'Rural'
                            
                        is_deleted = int(row[25]) if (isinstance(row[25], float) or isinstance(row[25], str))  else row[25]
                        if not is_deleted == 1: #import only active address
                            vals  = dict(
                                street = row[2],
                                street2 = row[3],
                                street3 = row[4],
                                physical_code = int(row[5]) if isinstance(row[5], float) else row[5],
                                physical_suburb_id = self._get_object_by_legacy_id('res.suburb', row[6]),
                                physical_city_id = self._get_object_by_legacy_id('res.city', row[7]),
                                physical_municipality_id = self._get_object_by_legacy_id('res.municipality', row[8]),
                                physical_urban_rural = u_r,
                                physical_province_id =  self._get_object_by_legacy_id('res.country.state', row[10]),
                                use_physical_for_postal_addr = True if int(row[11]) == 1 else False,
                                postal_address1 = row[12],
                                postal_address2 = row[13],
                                postal_address3 = row[14],
                                postal_code = int(row[15]) if isinstance(row[15], float) else row[15],
                                postal_suburb_id = self._get_object_by_legacy_id('res.suburb', row[16]),
                                postal_city_id = self._get_object_by_legacy_id('res.city', row[17]),
                                postal_municipality_id = self._get_object_by_legacy_id('res.municipality', row[18]),
                                postal_urban_rural = pu_r,
                                postal_province_id =  self._get_object_by_legacy_id('res.country.state', row[20]),
                            )
                            if not partner.street:
                                partner.write(vals)

                                if loop == 100:
                                    _logger.info('100 adddres records updated...')
                                    self.env.cr.commit()
                                    #reset loop
                                    loop = 0
                                loop += 1
                            # street = str(row[2]).replace("'", "")
                            # street2 = str(row[3]).replace("'", "")
                            # street3 = str(row[4]).replace("'", "")
                            # physical_code = int(row[5]) if isinstance(row[5], float) else row[5]
                            # physical_suburb_id = self._get_object_by_legacy_id('res.suburb', row[6])
                            # physical_city_id = self._get_object_by_legacy_id('res.city', row[7])
                            # physical_municipality_id = self._get_object_by_legacy_id('res.municipality', row[8])
                            # physical_urban_rural = u_r
                            # physical_province_id =  self._get_object_by_legacy_id('res.country.state', row[10])
                            # use_physical_for_postal_addr = True if int(row[11]) == 1 else False
                            # postal_address1 = str(row[12]).replace("'", "")
                            # postal_address2 = str(row[13]).replace("'", "")
                            # postal_address3 = str(row[14]).replace("'", "")
                            # postal_code = int(row[15]) if isinstance(row[15], float) else row[15]
                            # postal_suburb_id = self._get_object_by_legacy_id('res.suburb', row[16])
                            # postal_city_id = self._get_object_by_legacy_id('res.city', row[17])
                            # postal_municipality_id = self._get_object_by_legacy_id('res.municipality', row[18])
                            # postal_urban_rural = pu_r
                            # postal_province_id =  self._get_object_by_legacy_id('res.country.state', row[20])

                            # self.env.cr.execute("""SELECT street FROM res_partner WHERE legacy_system_id = '%s' LIMIT 1 """ % cast_to_integer(row[1]))
                            # partner_dict = self.env.cr.dictfetchone()
                            # street = False
                            # if partner_dict:
                            #     street = partner_dict.get('street')
                            # #We will update partner if there is no street set already
                            # if not street:
                            #     sql = f'''
                            #         UPDATE res_partner 
                            #         SET street='{ street or ""}', street2='{street2 or ""}', street3='{street3 or ""}',
                            #         physical_code='{physical_code or ""}', physical_suburb_id={physical_suburb_id or 0},
                            #         physical_city_id={physical_city_id or 0},physical_municipality_id={physical_municipality_id or 0},
                            #         physical_urban_rural='{physical_urban_rural or ""}',physical_province_id={physical_province_id or 0},
                            #         use_physical_for_postal_addr={use_physical_for_postal_addr}, postal_address1='{postal_address1 or ""}',
                            #         postal_address2='{postal_address2 or ""}', postal_address3='{postal_address3 or ""}',
                            #         postal_code='{postal_code or ""}',postal_suburb_id={postal_suburb_id or 0},
                            #         postal_city_id={postal_city_id or 0},postal_municipality_id={postal_municipality_id or 0},
                            #         postal_urban_rural='{postal_urban_rural or ""}',postal_province_id={postal_province_id or 0}
                            #         WHERE legacy_system_id={personid or 0}
                            #     '''
                            #     self.env.cr.execute(sql)
                            #     if loop == 100:
                            #         _logger.info('100 adddres records updated...')
                            #         self.env.cr.commit()
                            #         #reset loop
                            #         loop = 0
                            #     loop += 1
                    else:
                        vals = dict(
                            legacy_system_id=int(row[0]),  # legacy system ID
                            title = self._get_object_by_legacy_id('res.partner.title', row[1]),  # name
                            first_name=row[2],
                            middle_name=row[3],
                            last_name=row[4],
                            name = f"{row[2]} {row[3]} {row[4]}",
                            initials = row[5],
                            id_no = int(row[6]) if isinstance(row[6], float) else row[6],
                            alternateid_type_id = self._get_object_by_legacy_id('res.alternate.id.type', row[7]),
                            birth_date = row[8].split(" ")[0],
                            gender_id =  self._get_object_by_legacy_id('res.gender', row[9]),
                            equity_id = self._get_object_by_legacy_id('res.equity', row[10]),
                            disability_id = self._get_object_by_legacy_id('res.disability', row[11]),
                            home_language_id = self._get_object_by_legacy_id('res.lang', row[12]),
                            nationality_id = self._get_object_by_legacy_id('res.nationality', row[13]),
                            citizen_resident_status_id = self._get_object_by_legacy_id('res.citizen.status', row[14]),
                            socio_economic_status_id = self._get_object_by_legacy_id('res.socio.economic.status', row[15]),
                            phone = int(row[16]) if isinstance(row[16], float) else row[16],
                            mobile = int(row[17]) if isinstance(row[17], float) else row[17],
                            fax_number = int(row[18]) if isinstance(row[18], float) else row[18],
                            email = row[19],
                            create_date = row[20].split(" ")[0],
                            write_date = row[22].split(" ")[0],
                            school_emis_id = self._get_object_by_legacy_id('res.school.emis', row[25]),
                            school_year = int(row[26]) if isinstance(row[26], float) else row[26],
                            statssa_area_code_id = self._get_object_by_legacy_id('res.statssa.area.code', row[27]),
                            popi_act_status_id = self._get_object_by_legacy_id('res.popi.act.status', row[28]),
                            popi_act_status_date = row[29].split(" ")[0] if row[28] else False
                        )
                        #_logger.info(f"PARTNER DATA => {json.dumps(vals, indent=4)}")

                        # partner = Model.search([
                        #     ('id_no', '=', vals.get('id_no')),
                        #     ('mobile', '=', vals.get('mobile')),
                        #     ('email', '=', vals.get('email'))
                        # ])
                        # if partner:
                        #     partner.write(vals)
                        # else:
                        Model.create(vals)

# --------------------------------------------
# Migrate dbo.sdf to inseta.sdf
# --------------------------------------------
                elif model == "inseta.sdf" :
                    #lets purge existing SDFs
                    #existing_sdfs = Model.search([])
                    #existing_sdfs.unlink()
                    legacy_sys_id = int(row[0])
                    person_legacy_system_id = int(row[1])
                    _logger.info(f"Person Legacy sys ID {person_legacy_system_id}")
                    partner = self.env['res.partner'].search([('legacy_system_id','=', person_legacy_system_id)],limit=1)
                    completed_sdf_training, requested_training = False, False
                    row9 = row[9]
                    row17 = row[17]
                    if isinstance(row9, int) or isinstance(row9, float):
                        completed_sdf_training =  True if int(row9) == 1 else False

                    if isinstance(row17, int) or isinstance(row17, float):
                        requested_training =  True if int(row9) == 2 else False

                    #is possible SDF does not have a partner record, 
                    # i dont know but during testing of this script, it happened and raise a validation error 
                    #ERROR: new row for relation "res_partner" violates check constraint "res_partner_check_name"
                    #We will only create SDF, if partner record exists
                    if partner:
                        vals = dict(
                            legacy_system_id = int(row[0]),
                            partner_id = partner.id,
                            highest_edu_level_id = self._get_object_by_legacy_id('res.education.level', row[2]),
                            highest_edu_desc = row[3],
                            current_occupation = row[4],
                            occupation_years = int(row[5]),
                            occupational_group_id = False, #dbo.lkpofomajorgroup
                            occupation_experience = row[7],
                            is_interested_in_communication = row[8],
                            has_completed_sdftraining = completed_sdf_training,
                            accredited_trainingprovider_name = row[10],
                            general_comments = row[11],
                            create_date = row[12].split(".")[0],
                            create_uid = self._get_object_by_legacy_id('res.users', row[13]) or self.env.user.id, 
                            write_date = row[14].split(".")[0],
                            write_uid = self._get_object_by_legacy_id('res.users', row[15]) or self.env.user.id, 
                            active = True if int(row[16]) == 0 else False,
                            has_requested_sdftraining = requested_training,
                            reregistration_state = 'approve' if int(row[18]) == 1 else 'decline',
                            registration_date = row[19].split(".")[0] if row[19].strip() != "" else False,
                            reregistration_date = row[20].split(".")[0] if row[20].strip() != "" else False,
                            # state = 'approve',
                            is_imported = True
                        )
                        _logger.info(f"SDF DATA => {json.dumps(vals.get('legacy_system_id'), indent=4)}")
                        #we can use this script to upload multiple times without fear of duplicate
                        obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                        if obj:
                            obj.write(vals)
                        else:
                            Model.create(vals)
# --------------------------------------------
# Migrate dbo.sdf to inseta.organisation
# --------------------------------------------
                elif model == "inseta.organisation" :
                    if self.is_partner_addr:
                        legacy_sys_id = int(row[0])
                        organisation = self.env['inseta.organisation'].search([('legacy_system_id', '=', int(row[1]))])
                        #update records that are found
                        if organisation:
                            u_r = False
                            row9 = int(row[9])
                            if row9 == 1:
                                u_r = 'Urban'
                            elif row9 == 2:
                                u_r = 'Rural'

                            pu_r = False
                            row19 = int(row[20])
                            if row19 == 1:
                                pu_r = 'Urban'
                            elif row19 == 2:
                                pu_r = 'Rural'
                            vals = dict(
                                street = row[2],
                                street2 = row[3],
                                street3 = row[4],
                                physical_code = int(row[5]) if isinstance(row[5], float) else row[5],
                                physical_suburb_id = self._get_object_by_legacy_id('res.suburb', row[6]),
                                physical_city_id = self._get_object_by_legacy_id('res.city', row[7]),
                                physical_municipality_id = self._get_object_by_legacy_id('res.municipality', row[8]),
                                physical_urban_rural = u_r,
                                physical_province_id =  self._get_object_by_legacy_id('res.country.state', row[10]),
                                gps_coordinates = row[11],
                                use_physical_for_postal_addr = True if int(row[12]) == 1 else False,
                                postal_address1 = row[13],
                                postal_address2 = row[14],
                                postal_address3 = row[15],
                                postal_code = int(row[16]) if isinstance(row[16], float) else row[16],
                                postal_suburb_id = self._get_object_by_legacy_id('res.suburb', row[17]),
                                postal_city_id = self._get_object_by_legacy_id('res.city', row[18]),
                                postal_municipality_id = self._get_object_by_legacy_id('res.municipality', row[19]),
                                postal_urban_rural = pu_r,
                                postal_province_id =  self._get_object_by_legacy_id('res.country.state', row[21]),
                                #dhet address -> legacy system fields
                                dhet_physical_address1 = row[22],
                                dhet_physical_address2 = row[23],
                                dhet_physical_address3 = row[24],
                                dhet_physical_code = int(row[25]) if isinstance(row[25], float) else row[25],
                                dhet_physical_suburb_id = self._get_object_by_legacy_id('res.suburb', row[26]),
                                dhet_physical_city_id = self._get_object_by_legacy_id('res.city', row[27]),
                                dhet_physical_municipality_id = self._get_object_by_legacy_id('res.municipality', row[28]),
                                dhet_physical_urban_rural = u_r,
                                dhet_physical_province_id =  self._get_object_by_legacy_id('res.country.state', row[30]),
                                dhet_gps_coordinates = row[31],

                                dhet_postal_address1 = row[32],
                                dhet_postal_address2 = row[33],
                                dhet_postal_address3 = row[34],
                                dhet_postal_code = int(row[35]) if isinstance(row[35], float) else row[35],
                                dhet_postal_suburb_id = self._get_object_by_legacy_id('res.suburb', row[36]),
                                dhet_postal_city_id = self._get_object_by_legacy_id('res.city', row[37]),
                                dhet_postal_municipality_id = self._get_object_by_legacy_id('res.municipality', row[38]),
                                dhet_postal_urban_rural = pu_r,
                                dhet_postal_province_id =  self._get_object_by_legacy_id('res.country.state', row[40]),
                            )
                            _logger.info(f"ORG ADDR DATA => {json.dumps(vals, indent=4)}")
                            organisation.write(vals)
                        
                    else:
                        legacy_sys_id = int(row[0])
                        
                        if isinstance(row[59], float) and int(row[59]) == 1:
                            org_status = 'Active'
                        elif isinstance(row[59], float) and int(row[59]) == 0:
                            org_status = 'Inactive'
                        else:
                            org_status = False
                        sdl_no = str(row[1]).replace(" ", "")
                        sdl_no_lower =  sdl_no.lower()
                        if sdl_no_lower.startswith('l'):
                            register_type ='Levy Paying'
                        elif sdl_no_lower.startswith('n'):
                            register_type = 'Non-Levy Paying'
                        else:
                            register_type = False

                        # ('Levy Paying','Levy Paying'),
                        # ('Non-Levy Paying','Non-Levy Paying')

                        vals = dict(
                            legacy_system_id = legacy_sys_id,
                            sdl_no = sdl_no,
                            levy_status = register_type,
                            state = 'approve',
                            possible_sdl_no = row[2],
                            name = row[3], #legal_name
                            legal_name = row[3],
                            trade_name = row[4],
                            registration_no_type_id = self._get_object_by_legacy_id('res.registration_no_type', row[5]),
                            registration_no = int(row[6]) if isinstance(row[6], float) else row[6],
                            type_of_organisation_id = self._get_object_by_legacy_id('res.type.organisation',row[7]),
                            legal_status_id = self._get_object_by_legacy_id('res.legal.status', row[8]),
                            partnership_id = self._get_object_by_legacy_id('res.partnership', row[9]),
                            phone = int(row[10]) if isinstance(row[10], float) else row[10],
                            fax_number = int(row[11]) if isinstance(row[11], float) else row[11],
                            sic_code_id = self._get_object_by_legacy_id('res.sic.code', row[12]),
                            no_employees = int(row[13]),
                            total_annual_payroll = float(row[14]),
                            sars_number = str(int(row[15])) if isinstance(row[15], float) else row[15],
                            cipro_number = str(int(row[16])) if isinstance(row[16], float) else row[16],
                            paye_number =  str(int(row[17])) if isinstance(row[17], float) else row[17],
                            uif_number =  str(int(row[18])) if isinstance(row[18], float) else row[18],
                            organisation_size_id = self._get_object_by_legacy_id('res.organisation.size', row[19]),
                            bee_status_id = self._get_object_by_legacy_id('res.bee.status', row[22]),
                            #DHET Fields
                            dhet_sdl_no = str(row[23]).replace(" ", ""),
                            dhet_legal_name = row[24],
                            dhet_trade_name = row[25],
                            dhet_registration_no_type_id = self._get_object_by_legacy_id('res.type.organisation',row[26]),
                            dhet_registration_no = row[27],
                            dhet_type_of_organisation_id = self._get_object_by_legacy_id('res.type.organisation', row[28]),
                            dhet_legal_status_id = self._get_object_by_legacy_id('res.legal.status', row[29]),
                            dhet_partnership_id = self._get_object_by_legacy_id('res.partnership',row[30]),
                            dhet_phone = int(row[31]) if isinstance(row[31], float) else row[31],
                            dhet_fax_number =  int(row[32]) if isinstance(row[32], float) else row[32],
                            dhet_sic_code_id = self._get_object_by_legacy_id('res.sic.code',row[33]),
                            dhet_no_employees = int(row[34]),
                            dhet_total_annual_payroll = float(row[35]),
                            dhet_sars_number = str(int(row[36])) if isinstance(row[36], float) else row[36],
                            dhet_cipro_number = str(int(row[37])) if isinstance(row[37], float) else row[37],
                            dhet_paye_number =  str(int(row[38])) if isinstance(row[38], float) else row[38],
                            dhet_uif_number =  str(int(row[39])) if isinstance(row[39], float) else row[39],
                            dhet_organisation_size_id = self._get_object_by_legacy_id('res.organisation.size', row[40]),
                            #jump cols 41,42 => dhetcurrentvsnoncurrent, dhetcurrentsetaregionid
                            dhet_bee_status_id = self._get_object_by_legacy_id('res.bee.status', row[43]),
                            levy_number_type_id = self._get_object_by_legacy_id('res.levy.number.type', row[44]),
                            is_interested_in_communication = True if int(row[45]) == 1 else False,
                            is_confirmed =  True if isinstance(row[46], float) and int(row[46]) == 1 else False,
                            email = str(row[47]),
                            website = str(row[48]),
                            #jump cols 49  => leviesuptodate
                            create_date = row[50].split(".")[0],
                            create_uid = self.env.user.id,
                            #jump cols 51 => createdby
                            write_date = row[52].split(".")[0],
                            write_uid = self.env.user.id,
                            #jump cols 53 - 56 => updatedby
                            current_fy_numberof_employees =  int(row[57]) if isinstance(row[57], float) else row[57], 
                            fsp_number = str(int(row[58])) if isinstance(row[58], float) else row[58],
                            organisation_status = org_status,
                            dhet_organisation_status = False, 
                            #jump col 60
                            other_sector = str(row[61]),
                            dhet_other_sector = str(row[62]),
                            annual_turnover = row[63],
                            dhet_annual_turnover = row[64]
                        )
                        _logger.info(f"ORG DATA => {json.dumps(vals.get('sdl_no'), indent=4)}")
                        # org = Model.search([('sdl_no', '=', vals.get('sdl_no'))])
                        # if org:
                        #     org.write(vals)
                        # else:
                        Model.create(vals)

# --------------------------------------------
# Migrate dbo.sdf to inseta.sdf.organisation
# --------------------------------------------
                elif model == "inseta.sdf.organisation" :
                    legacy_sys_id = row[0]
                    state_id = int(row[5]) if (isinstance(row[5], float) or isinstance(row[5], int))  else 0
                    recommed = False
                    if state_id == 1:
                        state = 'draft'
                    elif state_id == 2:
                        state = 'approve'
                        recommed = 'Recommended'
                    elif state_id == 3:
                        state = 'reject'
                        recommed = 'Not Recommended'
                    elif state_id == 0:
                        state = False
                    else:
                        state = 'deactivate'

                    role_id = int(row[6]) if (isinstance(row[6], float) or isinstance(row[6], int))  else 0
                    if role_id == 1:
                        role = 'primary'
                    elif role_id == 2:
                        role = 'secondary'
                    elif role_id == 0:
                        role = False
                    else:
                        role = 'contract'

                    sdf_legacy_id = int(row[1])
                    org_legacy_id = int(row[2])
                    vals = dict(
                        legacy_system_id = int(row[0]),
                        sdf_id= self._get_object_by_legacy_id('inseta.sdf',sdf_legacy_id),
                        organisation_id = self._get_object_by_legacy_id('inseta.organisation',org_legacy_id),
                        start_date = row[3].split(" ")[0] if str(row[3]) else False,
                        end_date  = row[4].split(" ")[0] if str(row[4]) else False,
                        state = state,
                        recommendation_status = recommed,
                        sdf_role = role,
                        approval_date = str(row[7]).split(" ")[0] if str(row[7]) else False,
                        approved_by = self._get_object_by_legacy_id('res.users', row[8]) or self.env.user.id, 
                        rejection_date = str(row[9]).split(" ")[0] if str(row[9]) else False,
                        rejected_by = self._get_object_by_legacy_id('res.users', row[10]) or self.env.user.id, 
                        is_acting_for_employer =  True if isinstance(row[11], float) and int(row[11]) == 1 else False,
                        sdf_function_id = self._get_object_by_legacy_id('res.sdf.function', row[12]),
                        appointment_procedure_id = self._get_object_by_legacy_id('res.sdf.appointment.procedure', row[13]),
                        appointment_procedure_other = str(row[14]),
                        is_replacing_primary_sdf = True if isinstance(row[15], float) and int(row[15]) == 1 else False,
                        is_secondary_sdf = True if isinstance(row[16], float) and int(row[16]) == 1 else False,
                        create_date =  str(row[17]).split(" ")[0] if str(row[17]) else False,
                        create_uid = self._get_object_by_legacy_id('res.users', row[18]) or self.env.user.id,
                        write_date =  str(row[19]).split(" ")[0]  if str(row[19]) else False,
                        write_uid = self._get_object_by_legacy_id('res.users', row[20]) or self.env.user.id,
                        wsp_open = str(row[22]),
                        financial_year_id =  self._get_object_by_legacy_id('res.financial.year', row[23]),
                        registration_start_date =  str(row[24]).split(" ")[0] if str(row[24]) else False,
                        registration_end_date =  str(row[25]).split(" ")[0] if str(row[25]) else False,
                    )
                    _logger.info(f"SDF ORG DATA => {json.dumps(vals.get('legacy_system_id'), indent=4)}")
                    #let us handle multiple re-imports
                    # sdf_org = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    # if sdf_org:
                    #     sdf_org.write(vals)
                    # else:
                    Model.create(vals)
# --------------------------------------------
# Migrate dbo.organisationtrainingcommittee to inseta.organisation.training.committee
# --------------------------------------------
                elif model == "inseta.organisation.training.committee":
                    vals = dict(
                        legacy_system_id = int(row[0]),
                        organisation_id = self._get_object_by_legacy_id('inseta.organisation', row[1]),
                        title = self._get_object_by_legacy_id('res.partner.title', row[2]),
                        first_name = row[3],
                        last_name = row[4],
                        initials = row[5],
                        designation_id = self._get_object_by_legacy_id('res.designation', row[6]),
                        designation_desc = row[7],
                        phone = int(row[8]) if isinstance(row[8], float) else row[8],
                        mobile =  int(row[9]) if isinstance(row[9], float) else row[9],
                        fax_number =  int(row[10]) if isinstance(row[10], float) else row[10],
                        email = row[11],
                        name_of_union = row[12],
                        position_in_union = row[13],
                        create_date = str(row[14]).split(" ")[0],
                        write_date = str(row[16]).split(" ")[0],
                    )
                    _logger.info(f"TRAINING COMMITTEE DATA => {json.dumps(vals.get('legacy_system_id'), indent=4)}")
                    #let us handle multiple re-imports
                    # obj = Model.search([('legacy_system_id', '=', vals.get('legacy_system_id'))])
                    # if obj:
                    #     obj.write(vals)
                    # else:
                    Model.create(vals)
        # self.env.cr.execute('''ALTER TABLE res_partner ENABLE TRIGGER ALL; COMMIT;''')



    def _get_object_by_legacy_id(self, model, legacy_id):
        if legacy_id: 
            if isinstance(legacy_id, int) or isinstance(legacy_id, float):
                # _logger.info(f" Model: {model}, Legacy ID: {int(legacy_id)} ")
                obj = self.env[model].search([('legacy_system_id', '=', int(legacy_id))], limit=1)
                return obj and int(obj.id) or False
        return False