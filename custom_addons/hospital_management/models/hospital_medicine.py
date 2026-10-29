# -*- coding: utf-8 -*-
from odoo import fields, models


class HospitalMedicine(models.Model):
    _name = 'hospital.medicine'
    _description = 'Medicine'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(string='Reference')
    active = fields.Boolean(default=True)
    dosage_form = fields.Selection([
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
    ], default='tablet')
    description = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    unit_price = fields.Monetary(currency_field='currency_id')
    stock_qty = fields.Integer(string='In Stock', tracking=True)

    _stock_positive = models.Constraint('CHECK(stock_qty >= 0)', 'Stock cannot be negative.')
    _code_uniq = models.Constraint('unique(code)', 'The medicine reference must be unique.')
