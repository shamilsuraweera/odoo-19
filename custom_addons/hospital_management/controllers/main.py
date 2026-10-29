# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class HospitalController(http.Controller):

    @http.route('/hospital/api/doctors', type='jsonrpc', auth='user', methods=['POST'])
    def doctors(self, department_code=None):
        """List active doctors, optionally filtered by department code."""
        domain = []
        if department_code:
            domain.append(('department_id.code', '=', department_code))
        doctors = request.env['hospital.doctor'].search(domain)
        return [{
            'id': doctor.id,
            'name': doctor.name,
            'department': doctor.department_id.name,
            'specialization': doctor.specialization,
            'fee': doctor.consultation_fee,
        } for doctor in doctors]

    @http.route('/hospital/prescription/<int:prescription_id>/pdf', type='http', auth='user')
    def prescription_pdf(self, prescription_id, **kwargs):
        """Download a prescription as PDF (access rules apply to the current user)."""
        prescription = request.env['hospital.prescription'].browse(prescription_id).exists()
        if not prescription:
            return request.not_found()
        report = request.env.ref('hospital_management.action_report_prescription')
        pdf, _content_type = report.with_context(force_report_rendering=True)._render_qweb_pdf(
            report, prescription.ids)
        return request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'inline; filename="{prescription.name}.pdf"'),
        ])
