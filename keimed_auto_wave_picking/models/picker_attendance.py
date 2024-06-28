# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class PickerAttendance(models.Model):
    _name = 'picker.attendance'
    _description = 'Picker Attendance'

    user_id = fields.Many2one(
        'res.users', string='User', required=True, readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Location', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True)
    checkin_date = fields.Datetime(string='Check-In Time', required=True,
        default=lambda self: fields.Datetime.now())
    checkout_date = fields.Datetime(string='Check-Out Time')
