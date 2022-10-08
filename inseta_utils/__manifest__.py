##############################################################################
#    Copyright (C) 2021. All Rights Reserved
#    Maach / QIS Solutions

{
    'name': 'inseta Utils',
    'version': '1.5',
    'author': "Maduka Chris Sopulu / QIS Solution",
    'summary': 'inseta Utility module',
    'depends': ['base', 'hr', 'mail', 'website'],
    'description': "inseta Utility module that accomodates all methods and utilities",
    "data": [
            # 'security/security_view.xml',
            'security/ir.model.access.csv',
            'views/utils_view.xml',
            'wizard/inseta_confirm_dialog.xml', 
        ],

    'css': [],
    'js': [],
    'qweb': [

    ],
    "active": False,
    'application': True,
    "sequence": 3
}
