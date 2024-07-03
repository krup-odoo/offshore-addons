# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.osv import expression
from datetime import datetime, time
from odoo import fields, models, api, _


class GroupByFilterWizard(models.TransientModel):
    _name = 'groupby.filter.wizard'
    _description = 'Group By / Filter By Wizard'

    group_by_contact = fields.Boolean()
    group_by_customer_category = fields.Boolean()
    group_by_product_category = fields.Boolean()
    group_by_routes = fields.Boolean()
    group_by_movement_type = fields.Boolean()
    group_by_priority = fields.Boolean()
    group_by_location = fields.Boolean()

    group_by_sequence = fields.Char()

    filter_by_contact = fields.Many2one('res.partner')
    filter_by_customer_category = fields.Many2one('customer.category')
    filter_by_product_category = fields.Many2one('product.category')
    filter_by_routes = fields.Many2one('route.info')
    filter_by_movement_type = fields.Many2one('product.scheduler.configurator')
    filter_by_priority = fields.Selection(selection=[
        ('0', 'Normal'),
        ('1', 'Urgent')])
    filter_by_scheduled_date = fields.Date()
    filter_order_ids = fields.Many2many('sale.order',
        compute="_compute_display_sale_order")
    filter_by_sale_order = fields.Many2many('sale.order')

    @api.onchange('group_by_contact', 'group_by_customer_category',
                  'group_by_product_category', 'group_by_routes',
                  'group_by_movement_type', 'group_by_priority',
                  'group_by_location')
    def onchange_group_by_sequence(self):
        group_by_fields = [
            'group_by_contact', 'group_by_customer_category',
            'group_by_product_category', 'group_by_routes',
            'group_by_movement_type', 'group_by_priority',
            'group_by_location'
        ]
        dict_group_by_fields = {
            'group_by_contact': 'picking_partner_id',
            'group_by_customer_category': 'customer_category_id',
            'group_by_product_category': 'product_category_name',
            'group_by_routes': 'route_id',
            'group_by_movement_type': 'movement_type_id',
            'group_by_priority': 'priority',
            'group_by_location': 'location_id',
        }
        for field in group_by_fields:
            if self[field] and (self.group_by_sequence and dict_group_by_fields[field] not in self.group_by_sequence) or not self.group_by_sequence:
                if self.group_by_sequence:
                    self.group_by_sequence += ',' + dict_group_by_fields[field]
                else:
                    self.group_by_sequence = dict_group_by_fields[field]
            if not self[field] and self.group_by_sequence and dict_group_by_fields[field] in self.group_by_sequence:
                values = self.group_by_sequence
                substrings_to_remove = [dict_group_by_fields[field]]

                # Removing the specified substrings
                for substring in substrings_to_remove:
                    # Remove substring followed by a comma
                    values = values.replace(substring + ',', '')
                    # Remove comma followed by the substring
                    values = values.replace(',' + substring, '')
                    # Remove substring if it's the only one
                    values = values.replace(substring, '')

                # Remove any leading or trailing commas that may have been left
                values = values.strip(',')
                self.group_by_sequence = values

    @api.depends('group_by_contact')
    def _compute_display_sale_order(self):
        StockPicking = self.env['stock.picking']
        for record in self:
            record.filter_by_stock_picking = StockPicking.search([
                ('state', '=', "assigned"),
                ('picking_type_id.name', '=', 'Pick')
            ]).mapped('sale_id.order_line').filtered_domain([
                ('product_id.detailed_type', '=', 'product')
            ]).mapped('order_id')

    def apply_filters_and_group_by(self):
        tree_view = self.env.ref(
            'keimed_auto_wave_picking.inherit_view_id_stock_move_line_1')
        domain = expression.AND([
            [('picking_type_id.name', '=', 'Pick')],
            [('picking_id.state', '=', 'assigned')],
            [('product_id.detailed_type', '=', 'product')],
            [('keimed_wave_id', '=', False)]
        ])

        if self.filter_by_contact:
            domain = expression.AND(
                [domain, [('picking_partner_id', '=', self.filter_by_contact.id)]])
        if self.filter_by_customer_category:
            domain = expression.AND(
                [domain, [('customer_category_id', '=', self.filter_by_customer_category.id)]])
        if self.filter_by_product_category:
            domain = expression.AND(
                [domain, [('product_category_name', '=', self.filter_by_product_category.complete_name)]])
        if self.filter_by_routes:
            domain = expression.AND(
                [domain, [('route_id', '=', self.filter_by_routes.id)]])
        if self.filter_by_movement_type:
            domain = expression.AND(
                [domain, [('movement_type_id', '=', self.filter_by_movement_type.id)]])
        if self.filter_by_priority:
            domain = expression.AND(
                [domain, [('priority', '=', self.filter_by_priority)]])
        if self.filter_by_scheduled_date:
            date_min = datetime.combine(
                self.filter_by_scheduled_date, time.min)
            date_max = datetime.combine(
                self.filter_by_scheduled_date, time.max)
            domain = expression.AND([domain, [(
                'scheduled_date', '>', date_min),
                ('scheduled_date', '<', date_max)]])
        if self.filter_by_sale_order:
            domain = expression.AND(
                [domain, [('origin', 'in', self.filter_by_sale_order.mapped('name'))]])

        action = {
            'name': _('Picklist'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'tree',
            'views': [(tree_view.id, 'tree')],
            'domain': domain,
            'context': {'create': False},
        }
        if self.group_by_sequence:
            action.get('context').update({
                'group_by': self.group_by_sequence.split(',')
            })
        return action
