
from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

class insetalLearnerProgrammeRegisterWizard(models.Model):
    _name = "inseta.learner.programme.register.wizard"
    _description  = "Inactive ETQA Programme register Wizards"


class insetalProgrammeRegister(models.Model):
    _name = 'inseta.programme.register'
    _description = "For registration of learners"
    _rec_name = "programme_type"

    # def _default_learner_register_get(self):
    #     rec_ids = self.env.context.get('active_ids', [])
    #     ids = []
    #     for rec in rec_ids:
    #         ids.append(rec)
    #     return ids

    # def _default_learner_get(self):
    #     rec_ids = self.env.context.get('active_ids', [])
    #     ids = []
    #     for rec in rec_ids:
    #         ids.append(rec)
    #     return ids
    
    programme_type = fields.Selection([ 
            ('Learnership','Learnership For Youth'),
            ('Learnership-Worker','Learnership For Worker'),
            ('Learnership-Rural','Learnership For Rural'),
            ('Skill','Skill-Youth'),
            ('Skill-W','Skill-Worker'),
            ('Qualification','Qualification'),
            ('Bursary','Bursary For Youth'),
            ('Bursary-W','Bursary for worker'),
            ('Candidacy','Candidacy'),
            ('Internship','Internship-Matric+'),
            # ('Internship','Internship-Matric+'),
            ('Internship-diploma-degree','Internship Diploma/Degree'),
            ('Wiltvet','WILTVET'),
            ('Unit','Unit standard'),
        ],
        default="Qualification", string="Programme Type"
    )

    is_from_lp = fields.Selection([ 
            ('LP','LP'),
            ('ETQA','ETQA'),
        ],
        default="LP", string=""
    )
    is_learner_register = fields.Selection([ 
            ('Yes','Yes'),
            ('No','No'),
        ],
        default="No", string=""
    )

    # active_register_list_ids = fields.Char(string="Active Learner Register IDS", default=_default_learner_get)
    # active_learner_list_ids = fields.Char(string="Learner IDS", default=_default_learner_get)
    learner_ids = fields.Many2many('inseta.learner', 'inseta_programme_register_learner_rel', 
    string="Learners", store=True)
    learner_register_ids = fields.Many2many('inseta.learner.register', 
    'inseta_programme_register_learner_register_rel', string="Learner Register", store=True)
    learner_id = fields.Many2one('inseta.learner', string="Learners", store=True)
    learner_id_no = fields.Char('Identification')
    dgtype_code = fields.Char('DG Type Code')
    financial_year_id = fields.Many2one('res.financial.year', required=False, store=True)
    lpro_id = fields.Integer()
    dg_number = fields.Char('Evalution(LGA) Number', store=True)
    document_ids = fields.One2many("inseta.learner.document", "programme_register_document_id", 
    string="Learner document")
    learner_learnership_line = fields.Many2many("inseta.learner.learnership", string='Learnership')
    skill_learnership_line = fields.Many2many("inseta.skill.learnership", string='Skill Programme')
    qualification_learnership_line = fields.Many2many("inseta.qualification.learnership", 
    string='Qualification')
    internship_learnership_line = fields.Many2many("inseta.internship.learnership", 
    string='Internship')
    unit_standard_learnership_line = fields.Many2many("inseta.unit_standard.learnership", 
    string='Unit standards', ondelete="cascade")
    bursary_learnership_line = fields.Many2many("inseta.bursary.learnership",string='Bursary')
    wiltvet_learnership_line = fields.Many2many("inseta.wiltvet.learnership", string='WIL(TVET)')
    candidacy_learnership_line = fields.Many2many("inseta.candidacy.learnership", string='Candidacy')
    
    def get_employer_default_user(self):
        user = self.env.user.id
        employer = self.env['inseta.organisation'].search([('user_id', '=', user)], limit=1)
        return employer.id

    @api.onchange('learner_id_no')
    def _onchange_learner_id_no(self):
        if self.learner_id_no:
            learner = self.env['inseta.learner'].search([('id_no', '=', self.learner_id_no)], limit=1)
            if learner:
                self.learner_id = learner.id
            else:
                self.learner_id_no = False
                self.learner_id = False
                return {'warning':{
                    'title':'Invalid Message',
                    'message':'The learner with ID is not a valid learner'
                    }
                    }
    
    def batch_add_programme_line(self):
        learner_lines = self.learner_register_ids if self.is_learner_register == "Yes" else self.learner_ids
        for learner in learner_lines:
            if self.learner_learnership_line:
                for line in self.learner_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('learner_learnership_line').\
                    filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id \
                    and l.learner_programme_id.id== line.learner_programme_id.id):
                        pass
                    else:
                        learner.learner_learnership_line = [(4, line.id)]
                        learner.learner_learnership_line.learner_id = learner.id

            if self.skill_learnership_line:
                for line in self.skill_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('skill_learnership_line').\
                    filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id \
                    and l.skill_programme_id.id== line.skill_programme_id.id):
                        pass
                    else:
                        learner.skill_learnership_line = [(4, line.id)]
                        learner.skill_learnership_line.learner_id = learner.id

            if self.qualification_learnership_line:
                for line in self.qualification_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('qualification_learnership_line').\
                    filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id \
                    and l.skill_programme_id.id== line.skill_programme_id.id):
                        pass
                    else:
                        learner.qualification_learnership_line = [(4, line.id)]
                        learner.qualification_learnership_line.learner_id = learner.id


            if self.internship_learnership_line:
                for line in self.internship_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('internship_learnership_line').filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id and l.qualification_id.id== line.qualification_id.id):
                        pass
                    else:
                        learner.internship_learnership_line = [(4, line.id)]
                        learner.internship_learnership_line.learner_id = learner.id

            if self.bursary_learnership_line:
                for line in self.bursary_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('bursary_learnership_line').filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id and l.bursary_type_id.id== line.bursary_type_id.id and l.qualification_id.id== line.qualification_id.id):
                        pass
                    else:
                        learner.update({
                            'bursary_learnership_line': [(4, line.id)]
                            })
                        lines = self.env['inseta.bursary.learnership'].search([('id', '=', line.id)], limit=1)
                        lines.learner_id = learner.id
                        # raise ValidationError(lines.learner_id.id)

            if self.candidacy_learnership_line:
                for line in self.candidacy_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('candidacy_learnership_line').filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id and l.qualification_id.id== line.qualification_id.id):
                        pass
                    else:
                        learner.candidacy_learnership_line = [(4, line.id)]
                        learner.candidacy_learnership_line.learner_id = learner.id

            if self.wiltvet_learnership_line:
                for line in self.wiltvet_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('wiltvet_learnership_line').filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id and l.programme_id.id== line.programme_id.id):
                        pass
                    else:
                        learner.wiltvet_learnership_line = [(4, line.id)]
                        learner.wiltvet_learnership_line.learner_id = learner.id

            if self.unit_standard_learnership_line:
                for line in self.unit_standard_learnership_line:
                    self.add_provider_learner(line)
                    if learner.mapped('unit_standard_learnership_line').filtered(lambda l: l.financial_year_id.id == line.financial_year_id.id and l.unit_standard_id.id== line.unit_standard_id.id):
                        pass
                    else:
                        learner.unit_standard_learnership_line = [(4, line.id)]
                        learner.unit_standard_learnership_line.learner_id = learner.id

            # learner.document_ids = [(4, doc.id) for doc in self.document_ids]

    def add_provider_learner(self, programeid):
        """Linking any registered learner to the provider"""
        if programeid:
            providerLearner = self.env['inseta.provider.learner']
            providerLearner.sudo().create({
                'provider_id': programeid.provider_id.id,
                'learner_id': programeid.learner_id.id,
                'id_no': programeid.learner_id.id_no,
            })

    def add_programme_line(self):
        if self.learner_learnership_line:
            ext = []
            for lineid in self.learner_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('learner_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if not exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().learner_learnership_line = [(4, lineid.id)]

        if self.skill_learnership_line:
            ext = []
            for lineid in self.skill_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('skill_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if not exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().skill_learnership_line = [(4, lineid.id)]

        if self.qualification_learnership_line:
            ext = []
            for lineid in self.qualification_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('qualification_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if not exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().qualification_learnership_line = [(4, lineid.id)]

        if self.internship_learnership_line:
            ext = []
            for lineid in self.internship_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('internship_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if not exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().internship_learnership_line = [(4, lineid.id)]

        if self.unit_standard_learnership_line:
            ext = []
            for lineid in self.unit_standard_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('unit_standard_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().unit_standard_learnership_line = [(4, lineid.id)]

        if self.bursary_learnership_line:
            ext = []
            for lineid in self.bursary_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('bursary_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().bursary_learnership_line = [(4, lineid.id)]

        if self.candidacy_learnership_line:
            ext = []
            for lineid in self.candidacy_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('candidacy_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().candidacy_learnership_line = [(4, lineid.id)]

        if self.wiltvet_learnership_line:
            ext = []
            for lineid in self.wiltvet_learnership_line:
                self.add_provider_learner(lineid)
                for exist in self.learner_id.mapped('wiltvet_learnership_line').filtered(lambda s: s.id == lineid.id and s.financial_year_id.id == self.financial_year_id.id):
                    if exist:
                        ext.append('exits')
                if not ext:
                    self.learner_id.sudo().wiltvet_learnership_line = [(4, lineid.id)]

        if self.lpro_id:
            """
                this option is used to determine if a learner has enrolled 
                to any programme    
            """
            vals = {
                'learner_id': self.learner_id.id,
                'has_enrolled': True, 
            }
            self.env['inseta.lp.programe.lines'].sudo().create(vals)

    def generate_learner_document_for_lp(self, learnership_line_id):
        """If lpro, system generates the document ids to lpro record for validation"""
        if self.lpro_id and learnership_line_id:
            self.lpro_id.document_ids = [(4, doc.id) for doc in learnership_line_id.mapped('document_ids')]

    @api.onchange('programme_type')
    def add_compulsory_document(self):
        if self.programme_type:
            # if self.programme_type in ['Learnership']:
            #     if not (self.env.user.has_group("inseta_etqa.group_etqa_evaluating_manager") or self.env.user.has_group("inseta_etqa.group_etqa_evaluating_admin")):
            #         self.programme_type = False
            #         return {'warning': {'title': 'ValidationError', 'message':'Only ETQA Admin Or ETQA manager is responsible to register learnership programme' }}  
            self.dgtype_code = self.programme_type
            self.document_ids = False
            if self.programme_type in ['Learnership', 'Qualification', 'Learnership-Rural']:
                learnership_docs = ['Learnership Agreement', 'Certified ID copy', 'Confirmation of Employment', 'POPI act consent']
                for rec in learnership_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id
                    }
                    self.document_ids = [(0, 0, vals)]

            if self.programme_type in ['Learnership-Worker']:
                learnership_docs = ['Learnership Agreement', 'Certified ID copy', 'Fixed term contract of employment', 'POPI act consent']
                for rec in learnership_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id
                    }
                    self.document_ids = [(0, 0, vals)]

            if self.programme_type in ['Skill', 'Skill-W']:
                skill_docs = ['Proof of Registration', 'Proof of Employment', 'Certified ID copy', 'Worker Programme Agreement', 'Quotation']
                for rec in skill_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id

                    }
                    self.document_ids = [(0, 0, vals)]

            if self.programme_type in ['Bursary', 'Bursary-W']:
                bursary_docs = ['Proof of Registration', 'Proof of Employment', 'Certified ID copy', 'Worker Programme Agreement', 'Quotation']
                for rec in bursary_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id

                    }
                    self.document_ids = [(0, 0, vals)]

            if self.programme_type in ['Candidacy']:
                candidacy_docs = ['Highest qualification','Worker Programme Agreement', 'Certified ID copy', 'Proof of Registration', 'Quotation', 'Proof of Employment']
                for rec in candidacy_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id

                    }
                    self.document_ids = [(0, 0, vals)]

            if self.programme_type in ['Internship', 'Internship-diploma-degree']:
                internship_docs = ['Internship Agreement', 'Certified ID copy', 'Confirmation of Employment', 'POPI act consent', 'Certified Copy of Qualification']
                for rec in internship_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id
                    }
                    self.document_ids = [(0, 0, vals)]

            if self.programme_type in ['Wiltvet']:
                wil_docs = [
                    'Work Base Placement Learning Agreement (WBPLA)', 'POPIA consent form', 
                    'Certified Learner ID copy', 'Leaner N4-N6 SOR or Certificate', 'Matric certificate',
                    'MOA with the college']
                for rec in wil_docs:
                    vals = {
                        'name': rec,
                        'programme_register_document_id': self.id,
                        'financial_year_id': self.financial_year_id.id
                    }
                    self.document_ids = [(0, 0, vals)]
        else:
            self.document_ids =[(3, rex.id) for rex in self.document_ids] 
        
    def validate_programme_lines(self):
        if not any([
            self.candidacy_learnership_line,
            self.wiltvet_learnership_line,
            self.bursary_learnership_line,
            self.unit_standard_learnership_line,
            self.internship_learnership_line,
            self.qualification_learnership_line,
            self.skill_learnership_line,
            self.learner_learnership_line]):
            raise ValidationError("You must add at least one programme")

    def post_action(self):
        # self.validate_programme_lines()
        # raise ValidationError("POP")
        self.add_programme_line()
        # self.validate_documents()
        # if self.is_from_lp in ['LP']:
        # 	if not self.learner_id:
        # 		raise ValidationError("Please add a learner and provider the programme's compulsory documents")
        # 	self.add_programme_line()
        # 	# self.learner_id.document_ids = [(4, doc.id) for doc in self.document_ids]
        # else:
        # 	if self.is_learner_register == "No":
        # 		if not self.learner_ids:
        # 			raise ValidationError("Select learners to enroll to a programme !!!")
        # 	else:
        # 		if not (self.learner_register_ids or self.learner_ids):
        # 			raise ValidationError("Select learners to enroll to a programme !!!")
        # 	self.batch_add_programme_line()
        return{'type': 'ir.actions.act_window_close'}
