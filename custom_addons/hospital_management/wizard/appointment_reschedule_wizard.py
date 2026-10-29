# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class AppointmentRescheduleWizard(models.TransientModel):
    _name = 'hospital.appointment.reschedule.wizard'
    _description = 'Reschedule Appointment Wizard'

    appointment_id = fields.Many2one('hospital.appointment', required=True, readonly=True)
    new_start = fields.Datetime(string='New Start', required=True)
    reason = fields.Char()

    def action_reschedule(self):
        self.ensure_one()
        appointment = self.appointment_id
        if appointment.state in ('done', 'cancel'):
            raise UserError(self.env._("A completed or cancelled appointment cannot be rescheduled."))
        old_start = appointment.start_datetime
        appointment.start_datetime = self.new_start
        appointment.message_post(body=self.env._(
            "Rescheduled from %(old)s to %(new)s. %(reason)s",
            old=fields.Datetime.to_string(old_start),
            new=fields.Datetime.to_string(self.new_start),
            reason=self.reason or ''))
        return {'type': 'ir.actions.act_window_close'}
