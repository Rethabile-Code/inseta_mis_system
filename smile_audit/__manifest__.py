
{
    "name": "Inseta Audit Trail",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Nkululeko",
    "description": """
This module allows Inseta administrators to  track all the user actions on the system.
    """,
    "depends": [
        'base',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/audit_rule_view.xml',
        'views/audit_log_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
