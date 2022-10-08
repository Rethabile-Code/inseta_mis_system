from odoo import models, fields, api
import os
from pathlib import Path
import logging

_logger = logging.getLogger(__name__)

class DataMigration(models.Model):
    _name = "data.migration"

    @api.model
    def migrate(self):

        try:
            # products = self.env['product.product'].search([('type','=','policy')])
            # products.write({'purchase_ok':False})
            # evaluations.write({'doctor':reach_doc.id})
            # lab_tests.write({'pathologist':reach_doc.id})

            SQL = '''
                UPDATE inseta_organisation
                SET institution_type = 'TVET'
                WHERE legal_name like '%TVET%';

                UPDATE inseta_organisation
                SET institution_type = 'University'
                WHERE legal_name ilike '%University%';

                UPDATE inseta_organisation
                SET institution_type = 'UoT'
                WHERE legal_name ilike '%University Of Technology%';

            '''
            # SQL = ''' 
            #     ALTER TABLE res_users
            #     DROP CONSTRAINT code_partnerid_uniq;
            # '''
            self.env.cr.execute(SQL)
            
        except Exception as e:
            _logger.info(e)