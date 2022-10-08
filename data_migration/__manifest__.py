# -*- coding: utf-8 -*-
{
    'name': "Data Migration Tool",

    'summary': """Data Migration Tool""",

    'description': """
        This module is used to run data migration scripts from the ERP.
        Migration is applied when the module is upgraded
    """,

    'author': "Ohia George",
    'website': "http://bitlect.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Others',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/migration.xml',
    ],
    'active' : 'False',
    'auto-install':'False',
    'installable': True,
}