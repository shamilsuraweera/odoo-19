# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HospitalDepartment(models.Model):
    _name = 'hospital.department'
    _description = 'Hospital Department'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(size=8)
    description = fields.Text()
    active = fields.Boolean(default=True)
    color = fields.Integer()
    head_doctor_id = fields.Many2one('hospital.doctor', string='Head of Department', tracking=True)
    doctor_ids = fields.One2many('hospital.doctor', 'department_id', string='Doctors')
    doctor_count = fields.Integer(compute='_compute_doctor_count')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _code_uniq = models.Constraint('unique(code)', 'The department code must be unique.')

    @api.depends('doctor_ids')
    def _compute_doctor_count(self):
        for department in self:
            department.doctor_count = len(department.doctor_ids)

    def action_view_doctors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Doctors'),
            'res_model': 'hospital.doctor',
            'view_mode': 'kanban,list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }
