# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PickerAttendanceWizard(models.TransientModel):
    _name = 'picker.attendance.wizard'
    _description = 'Picker Attendance Wizard'

    user_id = fields.Many2one(
        'res.users', string='User', required=True, readonly=True,
        default=lambda self: self.env.user)
    location_id = fields.Many2one(
        'stock.location', string='Location', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    checkin_date = fields.Datetime(string='Check-In Time')
    picker_attandance_id = fields.Many2one('picker.attendance')
    picking_type = fields.Selection(related="company_id.picking_type")
    snake_picking_type = fields.Selection(
        related="company_id.snake_picking_type")

    @api.model
    def default_get(self, fields):
        defaults = super(PickerAttendanceWizard, self).default_get(fields)
        picker_attandance = self.env['picker.attendance'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
            ('checkin_date', '!=', False),
            ('checkout_date', '=', False),
        ], order='id desc', limit=1)
        if picker_attandance:
            defaults['picker_attandance_id'] = picker_attandance.id
            defaults['checkin_date'] = picker_attandance.checkin_date
            defaults['location_id'] = picker_attandance.location_id.id
        return defaults

    def action_check_in(self):
        if not self.location_id.is_zone:
            picker_attandance = self.env['picker.attendance'].search([
                ('user_id', '!=', self.env.user.id),
                ('company_id', '=', self.env.company.id),
                ('location_id', '=', self.location_id.id),
                ('checkin_date', '!=', False),
                ('checkout_date', '=', False),
            ], order='id desc', limit=1)
            if picker_attandance:
                raise ValidationError(
                    _('%s is already checked in at this location!' % picker_attandance.user_id.name))

        self.env['picker.attendance'].create({
            'user_id': self.user_id.id,
            'location_id': self.location_id.id,
            'company_id': self.company_id.id,
            'checkin_date': fields.Datetime.now(),
        })

    def action_check_out(self):
        self.picker_attandance_id.update({
            'checkout_date': fields.Datetime.now()
        })

    def action_check_out_and_check_in_again(self):
        self.picker_attandance_id.update({
            'checkout_date': fields.Datetime.now()
        })
        return self.env['stock.picking.type'].action_check_in_or_check_out()
