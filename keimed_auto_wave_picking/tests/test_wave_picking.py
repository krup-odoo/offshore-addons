# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, Form


class TestWavePicking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'login': 'bob',
            'name': "Bob Bobman",
            'groups_id': [(4, cls.env.ref('base.group_user').id),
                          (4, cls.env.ref(
                              'keimed_auto_wave_picking.group_stock_picking_picker').id),
                          (4, cls.env.ref('stock.group_stock_picking_wave').id)],
        })
        cls.user1 = cls.env['res.users'].create({
            'login': 'checkbob',
            'name': "check Bob Bobman",
            'groups_id': [(4, cls.env.ref('base.group_user').id),
                          (4, cls.env.ref(
                              'keimed_auto_wave_picking.group_stock_picking_checker').id),
                          (4, cls.env.ref('stock.group_stock_picking_wave').id)],
        })
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_pick = cls.env['ir.model.data']._xmlid_to_res_id(
            'stock.stock_location_pick')
        cls.user_demo = cls.env['res.users'].search([('login', '=', 'demo')])

        cls.productA = cls.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'tracking': 'lot',
            'categ_id': cls.env.ref('product.product_category_all').id,
        })
        cls.lots_p_a = cls.env['stock.lot'].create([{
            'name': 'lot_product_a_' + str(i + 1),
            'product_id': cls.productA.id,
            'company_id': cls.env.company.id,
        } for i in range(4)])
        cls.productB = cls.env['product.product'].create({
            'name': 'Product B',
            'type': 'product',
            'tracking': 'serial',
            'categ_id': cls.env.ref('product.product_category_all').id,
        })
        cls.lots_p_b = cls.env['stock.lot'].create([{
            'name': 'lot_product_a_' + str(i + 1),
            'product_id': cls.productB.id,
            'company_id': cls.env.company.id,
        } for i in range(10)])

        Quant = cls.env['stock.quant']
        for lot in cls.lots_p_a:
            Quant._update_available_quantity(
                cls.productA, cls.stock_location, 5.0, lot_id=lot)
        for lot in cls.lots_p_b:
            Quant._update_available_quantity(
                cls.productB, cls.stock_location, 1.0, lot_id=lot)

        cls.picking_client_1 = cls.env['stock.picking'].create({
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'picking_type_id': cls.picking_type_pick,
            'company_id': cls.env.company.id,
            'state': 'draft',
        })

        cls.env['stock.move'].create({
            'name': cls.productA.name,
            'product_id': cls.productA.id,
            'product_uom_qty': 15,
            'product_uom': cls.productA.uom_id.id,
            'picking_id': cls.picking_client_1.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

        cls.env['stock.move'].create({
            'name': cls.productB.name,
            'product_id': cls.productB.id,
            'product_uom_qty': 5,
            'product_uom': cls.productB.uom_id.id,
            'picking_id': cls.picking_client_1.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

        cls.picking_client_2 = cls.env['stock.picking'].create({
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'picking_type_id': cls.picking_type_pick,
            'company_id': cls.env.company.id,
            'state': 'draft',
        })

        cls.env['stock.move'].create({
            'name': cls.productA.name,
            'product_id': cls.productA.id,
            'product_uom_qty': 5,
            'product_uom': cls.productA.uom_id.id,
            'picking_id': cls.picking_client_2.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

        cls.picking_client_3 = cls.env['stock.picking'].create({
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'picking_type_id': cls.picking_type_pick,
            'company_id': cls.env.company.id,
            'state': 'draft',
        })

        cls.env['stock.move'].create({
            'name': cls.productB.name,
            'product_id': cls.productB.id,
            'product_uom_qty': 5,
            'product_uom': cls.productB.uom_id.id,
            'picking_id': cls.picking_client_3.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

        cls.picking_client_4 = cls.env['stock.picking'].create({
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'picking_type_id': cls.picking_type_pick,
            'state': 'draft',
        })

        cls.env['stock.move'].create({
            'name': cls.productA.name,
            'product_id': cls.productA.id,
            'product_uom_qty': 10,
            'product_uom': cls.productA.uom_id.id,
            'picking_id': cls.picking_client_4.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

        cls.env['stock.move'].create({
            'name': cls.productB.name,
            'product_id': cls.productB.id,
            'product_uom_qty': 15,
            'product_uom': cls.productB.uom_id.id,
            'picking_id': cls.picking_client_4.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

        cls.all_pickings = cls.picking_client_1 | cls.picking_client_2 | cls.picking_client_3
        cls.all_pickings.action_confirm()

    def test_user_existence(self):
        """Test user existence."""

        bob_user = self.env['res.users'].search(
            [('login', '=', 'bob')], limit=1)
        self.assertTrue(self.env.ref('stock.group_stock_picking_wave')
                        in bob_user.groups_id, "Wave picking should be enabled for Bob")
        checkbob_user = self.env['res.users'].search(
            [('login', '=', 'checkbob')], limit=1)
        self.assertTrue(self.env.ref('stock.group_stock_picking_wave')
                        in checkbob_user.groups_id, "Wave picking should be enabled for checkbob")

    def test_generate_picking(self):
        """ Select all the move_lines and create a wave from them """
        wave = self.env['stock.picking.batch'].search([
            ('is_wave', '=', True)
        ])
        self.assertTrue(wave)

    def test_create_waves(self):
        """ Select all the move_lines and create a wave from them """
        all_lines = self.all_pickings.move_line_ids
        res_dict = all_lines.action_split_waves()
        res_dict['context'] = {
            'active_model': 'stock.move.line', 'active_ids': all_lines.ids}

        context = res_dict['context']
        context['default_no_of_lines_to_be_picked'] = len(all_lines)

        wizard_form = Form(
            self.env[res_dict['res_model']].with_context(context))
        wizard_form.no_of_waves_to_be_created = 1
        wizard_form.save().attach_pickings()
        wave = self.env['stock.picking.batch'].search([
            ('is_wave', '=', True)
        ])

        self.assertEqual(res_dict.get('res_model'), 'split.wave.wizard')
        self.assertTrue(wave)
