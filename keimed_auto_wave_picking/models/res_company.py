# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    picking_type = fields.Selection([
        ('snake_picking', 'Snake Picking'),
        ('wave_picking', 'Wave Picking')
    ], default="wave_picking")
    snake_picking_type = fields.Selection([('zone', 'Zone'), ('rack', 'Rack')])
