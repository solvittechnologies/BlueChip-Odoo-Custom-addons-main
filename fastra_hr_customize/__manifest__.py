# -*- coding: utf-8 -*-

{
    'name': 'Fastra HR Customize',
    'version': '12.0.1.0.0',
    'summary': 'Fastra HR Customize',
    'depends': ['hr', 'stock', 'account', 'hr_menus', 'hr_timesheet', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'security/fastra_hr_payroll_security.xml',
        'data/payroll_sequence.xml',

        'views/hr_payslip_custom.xml',
        'views/salaries_excel_sheet.xml',
        'views/employee_loan.xml',
        'views/employee_checklist_for_staff.xml',
        'views/employee_checklist_for_staff_employee.xml',
        'views/employee_induction_form.xml',
        'views/employee_induction_for_master_data.xml',
        'views/staff_induction_master_data.xml',
        'views/staff_induction_sheet.xml',
        'views/payroll.xml',
        'views/master_data_salary_computation.xml',
        'views/interview_rating_guide.xml',
        'views/fastra_leave_request.xml',

        'reports/salaries_excel_sheet_report.xml',
        'reports/payroll_report.xml',
        'wizard/cancel_reason_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
