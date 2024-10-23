# -*- coding: utf-8 -*-

{
    'name': 'Fastra Account invoice extends',
    'version': '12.0.1.0.0',
    'summary': 'Fastra Accoun invoice extends',
    'depends': ['account','web_extend','web'],
    'data': [
            'views/account_invoice.xml',
            'views/res_company_views.xml',
            'report/account_invoice_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
