# -*- coding: utf-8 -*-
{
    'name': "POPI Act",

    'summary': """
        POPI Act consent wizard""",

    'description': """
        POPI Act consent wizard
    """,

    'author': "Ohia George - ohiageorge@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'website',
        'inseta_etqa',
        'inseta_skills',
        'inseta_dg'
    ],
    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        #'wizard/popi_act_consent_wizard_views.xml',
        'views/popiact.xml',
        'views/assets.xml',
        'views/res_users.xml'
    ],
    "active": False,
    "sequence": 5
}
