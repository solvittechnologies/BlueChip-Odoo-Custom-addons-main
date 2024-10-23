{
    'name': 'fastra payslip print',
    'version': '1.0',
    'category': 'tool',
    'summary': 'Résumé de mon module',
    'description': """
        Description détaillée de mon module
    """,
    'author': 'Mon nom',
    'depends': ['base','fastra_hr_customize'],
    'data': [
        'views/view.xml',
        'reports/report.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
