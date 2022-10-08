{
    'name': 'INSETA Base',
    'description': '''Contains the base models and data used across all INSETA modules.''',
    'category': 'INSETA',
    'version': '14.0.1.0.0',
    'depends': ['base', 'contacts','website','hr', 'vertical_tabs', 'project'],
    "data": [
            'security/ir.model.access.csv',
            'security/inseta_base_security.xml',
            'views/res_users.xml',
            'views/base_view.xml',
            'views/res_partner.xml',
            'views/res_country_view.xml',
            'data/data.xml',
            'data/res_institution.xml',
        ],
    "sequence": 0,
    "application": True
}
