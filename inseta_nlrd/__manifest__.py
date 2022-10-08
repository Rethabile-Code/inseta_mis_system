##############################################################################
#    Copyright (C) 2021 MAACH MEDIA. All Rights Reserved
#    MAACH MEDIA Extensions to Sms module


{
    'name': 'INSETA NLRD / SETMIS Report Module',
    'version': '14.0.0',
    'author': "MAACH MEDIA",
    'category': 'Sales',
    'summary': 'INSETA NLRD /SETMIS Report Module',
    'description': "INSETA NLRD Report Module",
    'depends': ['inseta_etqa'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/inseta_nlrd_view.xml',
        'wizard/inseta_setmis.xml',
    ],
    "sequence": 3,
    'installable': True,
    'application': True,
}
