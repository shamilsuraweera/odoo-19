# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HospitalDoctor(models.Model):
    _name = 'hospital.doctor'
    _description = 'Doctor'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Related User', help='Used to restrict a doctor to their own appointments.')
    department_id = fields.Many2one('hospital.department', tracking=True)
    specialization = fields.Char()
    qualification = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    bio = fields.Html()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    consultation_fee = fields.Monetary(currency_field='currency_id', tracking=True)
    appointment_ids = fields.One2many('hospital.appointment', 'doctor_id')
    appointment_count = fields.Integer(compute='_compute_appointment_count')

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        data = self.env['hospital.appointment']._read_group(
            [('doctor_id', 'in', self.ids)], ['doctor_id'], ['__count'])
        counts = {doctor.id: count for doctor, count in data}
        for doctor in self:
            doctor.appointment_count = counts.get(doctor.id, 0)

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Appointments'),
            'res_model': 'hospital.appointment',
            'view_mode': 'list,calendar,form',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id},
        }
