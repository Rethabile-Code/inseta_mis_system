##############################################################################
#    Copyright (C) 2021 Bitlect. All Rights Reserved
#    BItlect Extensions to Sms module


{
    'name': 'Generic Import Module',
    'version': '14.0.0',
    'author': "Bitlect Technology",
    'category': 'Sales',
    'summary': 'BItlect Extensions to Odoo Sales',
    'description': "BItlect Extensions to OdooS ales",
    "website": "https://www.bitlect.net",
    'depends': ['base', 'inseta_base'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/import_view.xml',
        'wizard/skills_data_import_view.xml',
        'wizard/etqa_data_import.xml',
        'wizard/ofo_code_import_view.xml'
    ],
    "sequence": 3,
    'installable': True,
    'application': True,
}
