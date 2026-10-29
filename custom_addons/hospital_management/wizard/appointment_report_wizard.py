# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import UserError


class AppointmentReportWizard(models.TransientModel):
    _name = 'hospital.appointment.report.wizard'
    _description = 'Appointment Report Wizard'

    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    doctor_id = fields.Many2one('hospital.doctor')
    department_id = fields.Many2one('hospital.department')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status')

    def _get_appointments(self):
        self.ensure_one()
        domain = [
            ('start_datetime', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('start_datetime', '<', fields.Datetime.to_datetime(self.date_to) + timedelta(days=1)),
        ]
        if self.doctor_id:
            domain.append(('doctor_id', '=', self.doctor_id.id))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.state:
            domain.append(('state', '=', self.state))
        return self.env['hospital.appointment'].search(domain, order='start_datetime')

    def action_print_pdf(self):
        appointments = self._get_appointments()
        if not appointments:
            raise UserError(self.env._("No appointments match the selected criteria."))
        return self.env.ref('hospital_management.action_report_appointment_summary').report_action(
            appointments, data=None)

    def action_open_list(self):
        appointments = self._get_appointments()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Appointments'),
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', appointments.ids)],
        }
