from odoo.tests import TransactionCase
from odoo.osv import expression
from odoo import fields
from datetime import datetime, date, time


class TestGroupByFilterWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.wizard = self.env['groupby.filter.wizard'].create({})
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.picking_type = self.env.ref('stock.picking_type_out')
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.customer_category = self.env['customer.category'].create({
            'name': 'Test Customer Category',
        })
        self.product_category = self.env['product.category'].create({
            'name': 'Test Product Category',
        })
        self.route = self.env['route.info'].create({
            'name': 'Test Route',
        })
        self.movement_type = self.env['product.scheduler.configurator'].create({
            'name': 'Test Movement Type',
        })
        self.picking = self.env['stock.picking'].create({
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.picking_type.id,
            'state': 'assigned',
        })
        self.move_line = self.env['stock.move.line'].create({
            'picking_id': self.picking.id,
            'product_id': self.product.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_partner_id': self.partner.id,
            'customer_category_id': self.customer_category.id,
            'product_category_name': self.product_category.complete_name,
            'route_id': self.route.id,
            'movement_type_id': self.movement_type.id,
            'priority': '0',
            'scheduled_date': fields.Date.today(),
        })

    def test_apply_filters_and_group_by(self):
        self.wizard.filter_by_contact = self.partner
        self.wizard.filter_by_customer_category = self.customer_category
        self.wizard.filter_by_product_category = self.product_category
        self.wizard.filter_by_routes = self.route
        self.wizard.filter_by_movement_type = self.movement_type
        self.wizard.filter_by_priority = '0'
        self.wizard.filter_by_scheduled_date = fields.Date.today()
        self.wizard.group_by_contact = True
        self.wizard.group_by_customer_category = True
        self.wizard.group_by_product_category = True
        self.wizard.group_by_routes = True
        self.wizard.group_by_movement_type = True
        self.wizard.group_by_priority = True

        action = self.wizard.apply_filters_and_group_by()

        date_min = datetime.combine(
            self.wizard.filter_by_scheduled_date, time.min)
        date_max = datetime.combine(
            self.wizard.filter_by_scheduled_date, time.max)

        expected_domain = [
            '|', ('picking_type_id.name', '=', 'Pick'),
            '|', ('picking_id.state', '=', 'assigned'),
            '|', ('keimed_wave_id', '=', False),
            '|', ('picking_partner_id', '=', self.partner.id),
            '|', ('customer_category_id', '=', self.customer_category.id),
            '|', ('product_category_name', '=',
                  self.product_category.complete_name),
            '|', ('route_id', '=', self.route.id),
            '|', ('movement_type_id', '=', self.movement_type.id),
            '|', ('priority', '=', '0'),
            '|', ('scheduled_date', '>', date_min),
            ('scheduled_date', '<', date_max)
        ]
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertTrue(expected_domain)

    def test_onchange_group_by_sequence(self):
        # Test when a group_by field is selected
        self.wizard.group_by_contact = True
        self.wizard.onchange_group_by_sequence()
        self.assertEqual(self.wizard.group_by_sequence, 'picking_partner_id')

        # Test when a group_by field is deselected
        self.wizard.group_by_contact = False
        self.wizard.onchange_group_by_sequence()
        self.assertEqual(self.wizard.group_by_sequence, '')

        # Test when multiple group_by fields are selected
        self.wizard.group_by_contact = True
        self.wizard.group_by_customer_category = True
        self.wizard.onchange_group_by_sequence()
        self.assertEqual(self.wizard.group_by_sequence,
                         'picking_partner_id,customer_category_id')

        # Test when a group_by field is selected and then deselected
        self.wizard.group_by_contact = True
        self.wizard.onchange_group_by_sequence()
        self.wizard.group_by_contact = False
        self.wizard.onchange_group_by_sequence()
        self.assertEqual(self.wizard.group_by_sequence, 'customer_category_id')

        # Test when a group_by field is selected and then another group_by field is selected
        self.wizard.group_by_contact = True
        self.wizard.onchange_group_by_sequence()
        self.wizard.group_by_customer_category = True
        self.wizard.onchange_group_by_sequence()
        self.assertEqual(self.wizard.group_by_sequence,
                         'customer_category_id,picking_partner_id')

        # Test when a group_by field is selected and then another group_by field is deselected
        self.wizard.group_by_contact = True
        self.wizard.onchange_group_by_sequence()
        self.wizard.group_by_customer_category = False
        self.wizard.onchange_group_by_sequence()
        self.assertEqual(self.wizard.group_by_sequence, 'picking_partner_id')
