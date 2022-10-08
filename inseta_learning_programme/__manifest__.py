# -*- coding: utf-8 -*-
{
    'name': "Inseta Learning programming",

    'summary': """
        Learning programming""",

    'description': """
        Learning programming
    """,

    'author': "Maduka Sopulu - sperality@gmail.com",

    # for the full list
    'category': 'Learning Programme',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'inseta_etqa', 
        'inseta_dg',
    ],
    # always loaded
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/sequence.xml',
        'security/ir_rule.xml',
        'views/inseta_learning_programme_views.xml',
        'views/inseta_learner_inherit_view.xml',
        'views/inseta_dgapplication_views.xml',
        'wizard/inseta_lpro_rework_wizard.xml',
        'reports/internship_funding_letter.xml',
        'wizard/inseta_lpro_register_learner_wizard.xml',
        'data/mail_templates.xml',
        'views/inseta_report.xml',
        'reports/learnership_rural_funding_template.xml',
        'reports/learnership_worker_funding_template.xml',
        'reports/learnership_youth_funding_template.xml',
        'reports/internship_funding_letter.xml'

    ],
    "active": False,
    'application': True,
    "sequence": 4
}
