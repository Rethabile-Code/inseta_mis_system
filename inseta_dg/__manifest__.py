# -*- coding: utf-8 -*-
{
    'name': "Discretionary Grant",

    'summary': """
        Apply for Discretionary Grant""",

    'description': """
        INSETA Discretionary Grant application
    """,

    'author': "Ohia George - ohiageorge@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'DG',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'inseta_base',
        'inseta_skills',
        'inseta_etqa',
    ],
    # always loaded
    'data': [
        'security/inseta_dg_security.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'reports/dg_decline_letter.xml',
        'reports/dg_letter_body.xml',
        'reports/dg_recommendation_letter.xml',
        'data/base.xml',
        'data/sequence.xml',
        'data/mail_data.xml',
        'data/automated_action.xml',
        'wizard/inseta_dgapplication_recommend_wizard_views.xml',
        'wizard/inseta_dgapplication_approve_wizard_views.xml',
        'wizard/inseta_dgapplication_review_wizard_views.xml',
        'wizard/inseta_dgbulkapproval_wizard_views.xml',
        'wizard/inseta_dgbulkrecommend_wizard_views.xml',
        'views/inseta_dgevaluation_views.xml',
        'views/inseta_dgapplication_views.xml',
        'views/base_views.xml',
        'views/inseta_dgwindow_views.xml',
        'views/inseta_dgindustryfunndedwindow_views.xml',
        'wizard/inseta_dg_report_wizard_views.xml',
        'views/inseta_dgapproval_views.xml',
        'views/inseta_dgrecommendation_views.xml',
        'views//inseta_dgbulksigning_views.xml',
        'views/inseta_organisation_views.xml',
        'views/mis_hei_representative_views.xml'
        # 'views/templates.xml',
    ],
    "active": False,
    'application': True,
    "sequence": 4
}
