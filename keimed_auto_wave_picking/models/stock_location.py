# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_zone = fields.Boolean()
    is_rack = fields.Boolean()
    picking_type = fields.Selection(related="company_id.picking_type")
    snake_picking_type = fields.Selection(
        related="company_id.snake_picking_type")

    @api.depends('name')
    @api.depends_context('display_only_current_location_name')
    def _compute_display_name(self):
        if not self._context.get('display_only_current_location_name'):
            return super()._compute_display_name()
        for record in self:
            record.display_name = record.name
