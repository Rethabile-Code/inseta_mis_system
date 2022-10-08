{
  'name':'INSETA Portal',
  'description':""" INSETA Theme.""",
  'summary': """ Odoo 14 Version of INSETA Portal""",
  'version':'1.0',
  'author':'Ohia George',
  'category': 'Theme/Creative',
  'depends': [
    'base',
    'website',
    'inseta_base'
  ],
  'depends': ['website','inseta_base'],
  'data': [
            'views/assets.xml',
            'views/layout.xml',
            'views/pages.xml',
            'views/provider_accreditation_page.xml',
            'views/assessor_register_page.xml',
            'views/hei_rep_reg.xml',
            'views/contact.xml'
  ],
  'sequence': 1,
  'application': True,
}