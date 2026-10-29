# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class HospitalPrescription(models.Model):
    _name = 'hospital.prescription'
    _description = 'Prescription'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    appointment_id = fields.Many2one('hospital.appointment', required=True, ondelete='cascade', index=True)
    patient_id = fields.Many2one(related='appointment_id.patient_id', store=True, index=True)
    doctor_id = fields.Many2one(related='appointment_id.doctor_id', store=True)
    date = fields.Date(default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('cancel', 'Cancelled'),
    ], default='draft', tracking=True, copy=False)
    line_ids = fields.One2many('hospital.prescription.line', 'prescription_id', string='Medicines', copy=True)
    notes = fields.Text(string='Instructions')
    company_id = fields.Many2one(related='appointment_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    total_amount = fields.Monetary(compute='_compute_total_amount', store=True, currency_field='currency_id')

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for prescription in self:
            prescription.total_amount = sum(prescription.line_ids.mapped('subtotal'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.prescription') or 'New'
        return super().create(vals_list)

    def action_issue(self):
        """Issue the prescription and take the medicines out of the pharmacy stock."""
        for prescription in self.filtered(lambda p: p.state == 'draft'):
            if not prescription.line_ids:
                raise UserError(self.env._("Add at least one medicine before issuing the prescription."))
            for line in prescription.line_ids:
                if line.medicine_id.stock_qty < line.quantity:
                    raise UserError(self.env._(
                        "Not enough stock for %(medicine)s: %(available)s available, %(needed)s needed.",
                        medicine=line.medicine_id.name,
                        available=line.medicine_id.stock_qty,
                        needed=line.quantity))
            for line in prescription.line_ids:
                line.medicine_id.stock_qty -= line.quantity
            prescription.state = 'issued'

    def action_cancel(self):
        for prescription in self.filtered(lambda p: p.state != 'cancel'):
            if prescription.state == 'issued':
                for line in prescription.line_ids:
                    line.medicine_id.stock_qty += line.quantity
            prescription.state = 'cancel'

    def action_draft(self):
        self.filtered(lambda p: p.state == 'cancel').state = 'draft'


class HospitalPrescriptionLine(models.Model):
    _name = 'hospital.prescription.line'
    _description = 'Prescription Line'

    prescription_id = fields.Many2one('hospital.prescription', required=True, ondelete='cascade')
    medicine_id = fields.Many2one('hospital.medicine', required=True)
    dosage = fields.Char(help='e.g. 1 tablet, 3 times a day')
    days = fields.Integer(default=5)
    quantity = fields.Integer(default=1)
    currency_id = fields.Many2one(related='prescription_id.currency_id')
    unit_price = fields.Monetary(compute='_compute_unit_price', store=True, readonly=False, currency_field='currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')

    _quantity_positive = models.Constraint('CHECK(quantity > 0)', 'The quantity must be positive.')

    @api.depends('medicine_id')
    def _compute_unit_price(self):
        for line in self:
            line.unit_price = line.medicine_id.unit_price

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
