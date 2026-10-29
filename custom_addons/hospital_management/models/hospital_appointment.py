# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc, id desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    patient_id = fields.Many2one('hospital.patient', required=True, tracking=True, index=True)
    patient_phone = fields.Char(related='patient_id.phone', string='Phone')
    doctor_id = fields.Many2one('hospital.doctor', required=True, tracking=True, index=True)
    department_id = fields.Many2one(related='doctor_id.department_id', store=True, string='Department')
    start_datetime = fields.Datetime(string='Start', required=True, tracking=True,
                                     default=lambda self: fields.Datetime.now().replace(minute=0, second=0) + timedelta(hours=1))
    duration = fields.Float(string='Duration (h)', default=0.5)
    end_datetime = fields.Datetime(string='End', compute='_compute_end_datetime', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, tracking=True, copy=False, group_expand='_group_expand_states')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], default='0')
    reason = fields.Char(string='Reason for Visit')
    diagnosis = fields.Text()
    notes = fields.Html(string='Internal Notes')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    fee = fields.Monetary(compute='_compute_fee', store=True, readonly=False, currency_field='currency_id')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    payment_state = fields.Selection(related='invoice_id.payment_state', string='Payment Status')
    prescription_ids = fields.One2many('hospital.prescription', 'appointment_id')
    prescription_count = fields.Integer(compute='_compute_prescription_count')
    color = fields.Integer(compute='_compute_color')

    # ------------------------------------------------------------------
    # compute / constraints
    # ------------------------------------------------------------------
    @api.model
    def _group_expand_states(self, states, domain):
        return [key for key, _label in self._fields['state'].selection]

    @api.depends('start_datetime', 'duration')
    def _compute_end_datetime(self):
        for appointment in self:
            if appointment.start_datetime:
                appointment.end_datetime = appointment.start_datetime + timedelta(hours=appointment.duration)
            else:
                appointment.end_datetime = False

    @api.depends('doctor_id.consultation_fee')
    def _compute_fee(self):
        for appointment in self:
            appointment.fee = appointment.doctor_id.consultation_fee

    @api.depends('prescription_ids')
    def _compute_prescription_count(self):
        for appointment in self:
            appointment.prescription_count = len(appointment.prescription_ids)

    @api.depends('state')
    def _compute_color(self):
        colors = {'draft': 0, 'confirmed': 4, 'in_consultation': 2, 'done': 10, 'cancel': 1}
        for appointment in self:
            appointment.color = colors.get(appointment.state, 0)

    @api.constrains('duration')
    def _check_duration(self):
        for appointment in self:
            if appointment.duration <= 0:
                raise ValidationError(self.env._("The duration must be greater than zero."))

    @api.constrains('doctor_id', 'start_datetime', 'duration', 'state')
    def _check_doctor_availability(self):
        for appointment in self:
            if appointment.state == 'cancel':
                continue
            overlap = self.search_count([
                ('id', '!=', appointment.id),
                ('doctor_id', '=', appointment.doctor_id.id),
                ('state', '!=', 'cancel'),
                ('start_datetime', '<', appointment.end_datetime),
                ('end_datetime', '>', appointment.start_datetime),
            ])
            if overlap:
                raise ValidationError(self.env._(
                    "%(doctor)s already has an appointment during this time slot.",
                    doctor=appointment.doctor_id.name))

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or 'New'
        return super().create(vals_list)

    def unlink(self):
        if any(appointment.state not in ('draft', 'cancel') for appointment in self):
            raise UserError(self.env._("Only draft or cancelled appointments can be deleted."))
        return super().unlink()

    # ------------------------------------------------------------------
    # workflow
    # ------------------------------------------------------------------
    def action_confirm(self):
        template = self.env.ref('hospital_management.mail_template_appointment_confirmation', raise_if_not_found=False)
        for appointment in self.filtered(lambda a: a.state == 'draft'):
            appointment.state = 'confirmed'
            if appointment.doctor_id.user_id:
                appointment.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=fields.Date.to_date(appointment.start_datetime),
                    summary=self.env._("Consultation with %s", appointment.patient_id.name),
                    user_id=appointment.doctor_id.user_id.id,
                )
            if template and appointment.patient_id.email:
                template.send_mail(appointment.id, force_send=False)

    def action_start(self):
        self.filtered(lambda a: a.state == 'confirmed').state = 'in_consultation'

    def action_done(self):
        for appointment in self.filtered(lambda a: a.state == 'in_consultation'):
            appointment.state = 'done'
            appointment.activity_feedback(['mail.mail_activity_data_todo'])

    def action_cancel(self):
        self.filtered(lambda a: a.state != 'done').state = 'cancel'
        self.activity_unlink(['mail.mail_activity_data_todo'])

    def action_draft(self):
        self.filtered(lambda a: a.state == 'cancel').state = 'draft'

    # ------------------------------------------------------------------
    # smart buttons, invoicing, wizards
    # ------------------------------------------------------------------
    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            return self.action_view_invoice()
        if self.state != 'done':
            raise UserError(self.env._("You can only invoice a completed appointment."))
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.company_id.id)], limit=1)
        if not journal:
            raise UserError(self.env._("No sales journal found. Please configure the Accounting app first."))
        lines = [(0, 0, {
            'name': self.env._("Consultation %(ref)s - %(doctor)s", ref=self.name, doctor=self.doctor_id.name),
            'quantity': 1,
            'price_unit': self.fee,
        })]
        for prescription in self.prescription_ids.filtered(lambda p: p.state == 'issued'):
            for line in prescription.line_ids:
                lines.append((0, 0, {
                    'name': line.medicine_id.name,
                    'quantity': line.quantity,
                    'price_unit': line.unit_price,
                }))
        self.invoice_id = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.partner_id.id,
            'journal_id': journal.id,
            'invoice_origin': self.name,
            'invoice_line_ids': lines,
        })
        self.message_post(body=self.env._("Invoice %s created.", self.invoice_id.name or self.env._("(draft)")))
        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Invoice'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
        }

    def action_view_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Prescriptions'),
            'res_model': 'hospital.prescription',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {'default_appointment_id': self.id},
        }

    def action_open_reschedule_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Reschedule Appointment'),
            'res_model': 'hospital.appointment.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_appointment_id': self.id, 'default_new_start': self.start_datetime},
        }

    # ------------------------------------------------------------------
    # cron, dashboard
    # ------------------------------------------------------------------
    @api.model
    def _cron_send_reminders(self):
        """Remind patients about confirmed appointments in the next 24 hours."""
        now = fields.Datetime.now()
        template = self.env.ref('hospital_management.mail_template_appointment_reminder', raise_if_not_found=False)
        if not template:
            return
        upcoming = self.search([
            ('state', '=', 'confirmed'),
            ('start_datetime', '>', now),
            ('start_datetime', '<=', now + timedelta(hours=24)),
            ('patient_id.email', '!=', False),
        ])
        for appointment in upcoming:
            template.send_mail(appointment.id, force_send=False)
        return len(upcoming)

    @api.model
    def get_dashboard_data(self):
        """Counters displayed by the OWL dashboard client action."""
        today_start = fields.Datetime.to_datetime(fields.Date.context_today(self))
        today_end = today_start + timedelta(days=1)
        today_domain = [('start_datetime', '>=', today_start), ('start_datetime', '<', today_end)]
        return {
            'today': self.search_count(today_domain),
            'confirmed': self.search_count([('state', '=', 'confirmed')]),
            'in_consultation': self.search_count([('state', '=', 'in_consultation')]),
            'done': self.search_count([('state', '=', 'done')]),
            'patients': self.env['hospital.patient'].search_count([]),
            'doctors': self.env['hospital.doctor'].search_count([]),
            'low_stock': self.env['hospital.medicine'].search_count([('stock_qty', '<', 20)]),
            'today_domain': [
                ['start_datetime', '>=', fields.Datetime.to_string(today_start)],
                ['start_datetime', '<', fields.Datetime.to_string(today_end)],
            ],
        }
