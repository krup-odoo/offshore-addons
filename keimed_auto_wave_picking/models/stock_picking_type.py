# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    def pick_line_action_button(self):
        return {
            'name': 'Picklist',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [
                ('picking_type_id.name', '=', 'Pick'),
                ('picking_id.state', '=', 'assigned'),
                ('product_id.detailed_type', '=', 'product'),
                ('keimed_wave_id', '=', False),
                ('is_used_in_wave', '=', False)
            ],
            'context': {'create': False},
        }

    def action_check_in_or_check_out(self):
        return {
            'name': 'Check In/ Check Out',
            'type': 'ir.actions.act_window',
            'res_model': 'picker.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
