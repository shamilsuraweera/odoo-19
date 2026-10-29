# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'hospital')
class TestHospital(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env['hospital.department'].create({'name': 'Test Dept', 'code': 'TST'})
        cls.doctor = cls.env['hospital.doctor'].create({
            'name': 'Dr. Test', 'department_id': cls.department.id, 'consultation_fee': 1000,
        })
        cls.patient = cls.env['hospital.patient'].create({
            'name': 'Test Patient', 'email': 'patient@example.com',
            'height': 180, 'weight': 81,
        })
        cls.medicine = cls.env['hospital.medicine'].create({
            'name': 'Test Medicine', 'unit_price': 10, 'stock_qty': 5,
        })
        cls.start = fields.Datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)

    def _appointment(self, start=None, **kwargs):
        return self.env['hospital.appointment'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'start_datetime': start or self.start,
            'duration': 1,
            **kwargs,
        })

    def test_patient_defaults(self):
        self.assertTrue(self.patient.ref.startswith('PAT'))
        self.assertTrue(self.patient.partner_id, "A contact must be created for invoicing")
        self.assertEqual(self.patient.bmi, 25.0)

    def test_patient_future_birth_date(self):
        with self.assertRaises(ValidationError):
            self.patient.birth_date = fields.Date.today() + timedelta(days=1)

    def test_appointment_fee_and_end(self):
        appointment = self._appointment()
        self.assertEqual(appointment.fee, 1000)
        self.assertEqual(appointment.end_datetime, self.start + timedelta(hours=1))
        self.assertEqual(appointment.department_id, self.department)

    def test_doctor_cannot_be_double_booked(self):
        self._appointment()
        with self.assertRaises(ValidationError):
            self._appointment(start=self.start + timedelta(minutes=30))
        # back-to-back is fine
        self._appointment(start=self.start + timedelta(hours=1))

    def test_workflow(self):
        appointment = self._appointment()
        appointment.action_confirm()
        self.assertEqual(appointment.state, 'confirmed')
        appointment.action_start()
        appointment.action_done()
        self.assertEqual(appointment.state, 'done')
        with self.assertRaises(UserError):
            appointment.unlink()

    def test_reschedule_wizard(self):
        appointment = self._appointment()
        new_start = self.start + timedelta(days=2)
        wizard = self.env['hospital.appointment.reschedule.wizard'].create({
            'appointment_id': appointment.id, 'new_start': new_start, 'reason': 'Patient request',
        })
        wizard.action_reschedule()
        self.assertEqual(appointment.start_datetime, new_start)

    def test_prescription_stock(self):
        appointment = self._appointment()
        prescription = self.env['hospital.prescription'].create({
            'appointment_id': appointment.id,
            'line_ids': [(0, 0, {'medicine_id': self.medicine.id, 'quantity': 3})],
        })
        self.assertEqual(prescription.total_amount, 30)
        prescription.action_issue()
        self.assertEqual(self.medicine.stock_qty, 2)
        prescription.action_cancel()
        self.assertEqual(self.medicine.stock_qty, 5, "Cancelling must restore the stock")

        too_many = self.env['hospital.prescription'].create({
            'appointment_id': appointment.id,
            'line_ids': [(0, 0, {'medicine_id': self.medicine.id, 'quantity': 50})],
        })
        with self.assertRaises(UserError):
            too_many.action_issue()

    def test_invoice(self):
        appointment = self._appointment()
        with self.assertRaises(UserError):
            appointment.action_create_invoice()  # not done yet
        appointment.write({'state': 'done'})
        if not self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.env.company.id)]):
            self.skipTest("No accounting chart installed")
        appointment.action_create_invoice()
        self.assertEqual(appointment.invoice_id.partner_id, self.patient.partner_id)
        self.assertEqual(appointment.invoice_id.amount_untaxed, 1000)

    def test_dashboard_data(self):
        self._appointment()
        data = self.env['hospital.appointment'].get_dashboard_data()
        self.assertIn('today', data)
        self.assertGreaterEqual(data['patients'], 1)
