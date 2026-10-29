# -*- coding: utf-8 -*-
{
    'name': 'Hospital Management',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Patients, doctors, appointments, prescriptions and billing',
    'description': """
Hospital Management
===================
A showcase module covering most of the Odoo framework:

* Models with computed / related / stored fields, SQL and Python constraints
* Chatter, activities and field tracking (mail.thread, mail.activity.mixin)
* Sequences, statusbar workflows and smart buttons
* List, form, kanban, calendar, pivot, graph and search views
* Security groups, access rights and record rules (incl. multi-company)
* Wizards (transient models), QWeb PDF reports and e-mail templates
* Scheduled actions (cron) and server actions
* Invoicing integration with the Accounting app
* OWL client-action dashboard and a JSON controller
* Demo data and unit tests
""",
    'author': 'Shamil Suraweera',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/hospital_security.xml',
        'security/ir.model.access.csv',
        'data/hospital_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'report/hospital_reports.xml',
        'report/prescription_report_templates.xml',
        'report/appointment_report_templates.xml',
        'views/hospital_department_views.xml',
        'views/hospital_doctor_views.xml',
        'views/hospital_patient_views.xml',
        'views/hospital_medicine_views.xml',
        'views/hospital_appointment_views.xml',
        'views/hospital_prescription_views.xml',
        'wizard/appointment_reschedule_wizard_views.xml',
        'wizard/appointment_report_wizard_views.xml',
        'views/hospital_dashboard_views.xml',
        'views/hospital_menus.xml',
    ],
    'demo': [
        'data/hospital_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hospital_management/static/src/scss/dashboard.scss',
            'hospital_management/static/src/js/dashboard.js',
            'hospital_management/static/src/xml/dashboard.xml',
        ],
    },
    'application': True,
    'installable': True,
}
