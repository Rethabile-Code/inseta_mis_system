# -*- coding: utf-8 -*-
{
    'name': "Vertical Tabs",

    'summary': """
        Display Odoo Notebook Pages Vertically""",

    'description': """
        This module will Display Odoo Notebook Pages Vertically
    """,

    'author': "Ohia George - ohiageorge@gmail.com (Bitlect Technology)",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
    ],
    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/backend_assets.xml',
    ],
    "active": False,
    "sequence": 3
}
