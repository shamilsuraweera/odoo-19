# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HospitalPatientTag(models.Model):
    _name = 'hospital.patient.tag'
    _description = 'Patient Tag'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer()

    _name_uniq = models.Constraint('unique(name)', 'This tag already exists.')


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _order = 'ref desc'

    name = fields.Char(required=True, tracking=True)
    ref = fields.Char(string='Patient ID', default='New', readonly=True, copy=False)
    active = fields.Boolean(default=True)
    birth_date = fields.Date(tracking=True)
    age = fields.Integer(compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], tracking=True)
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-'),
    ])
    phone = fields.Char()
    email = fields.Char()
    address = fields.Text()
    height = fields.Float(help='Height in cm')
    weight = fields.Float(help='Weight in kg')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', digits=(4, 1))
    allergies = fields.Text()
    chronic_conditions = fields.Text()
    tag_ids = fields.Many2many('hospital.patient.tag', string='Tags')
    partner_id = fields.Many2one('res.partner', string='Contact', copy=False,
                                 help='Contact used for invoicing. Created automatically.')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    appointment_ids = fields.One2many('hospital.appointment', 'patient_id')
    prescription_ids = fields.One2many('hospital.prescription', 'patient_id')
    appointment_count = fields.Integer(compute='_compute_counts')
    prescription_count = fields.Integer(compute='_compute_counts')

    _ref_uniq = models.Constraint('unique(ref)', 'The patient ID must be unique.')

    @api.depends('birth_date')
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for patient in self:
            patient.age = relativedelta(today, patient.birth_date).years if patient.birth_date else 0

    @api.depends('height', 'weight')
    def _compute_bmi(self):
        for patient in self:
            meters = patient.height / 100.0
            patient.bmi = patient.weight / (meters ** 2) if meters else 0.0

    @api.depends('appointment_ids', 'prescription_ids')
    def _compute_counts(self):
        for patient in self:
            patient.appointment_count = len(patient.appointment_ids)
            patient.prescription_count = len(patient.prescription_ids)

    @api.depends('name', 'ref')
    def _compute_display_name(self):
        for patient in self:
            patient.display_name = f"[{patient.ref}] {patient.name}" if patient.ref and patient.ref != 'New' else patient.name

    @api.constrains('birth_date')
    def _check_birth_date(self):
        today = fields.Date.context_today(self)
        for patient in self:
            if patient.birth_date and patient.birth_date > today:
                raise ValidationError(self.env._("The birth date cannot be in the future."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'
            if not vals.get('partner_id') and vals.get('name'):
                vals['partner_id'] = self.env['res.partner'].create({
                    'name': vals['name'],
                    'phone': vals.get('phone'),
                    'email': vals.get('email'),
                }).id
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        # keep the invoicing contact in sync
        sync = {key: vals[key] for key in ('name', 'phone', 'email') if key in vals}
        if sync:
            self.mapped('partner_id').write(sync)
        return res

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Appointments'),
            'res_model': 'hospital.appointment',
            'view_mode': 'list,calendar,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_view_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Prescriptions'),
            'res_model': 'hospital.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
        }
