from odoo.addons.base.tests.common import SavepointCaseWithUserDemo


class TestStockMoveLine(SavepointCaseWithUserDemo):

    def setUp(self):
        super().setUp()
        self.category = self.env['uom.category'].create({
            'name': 'Test Category'
        })
        self.uom = self.env['uom.uom'].create({
            'name': 'Test UOM',
            'category_id': self.category.id,
            'uom_type': 'reference',
            'factor': 1.0,
            'rounding': 0.01
        })
        self.wave = self.env['keimed.wave'].create({
            'name': 'Test Wave'
        })

        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.picking_type_pick = self.env['ir.model.data']._xmlid_to_res_id(
            'stock.stock_location_pick')
        self.user_demo = self.env['res.users'].search([('login', '=', 'demo')])

        self.productA = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'tracking': 'lot',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        self.lots_p_a = self.env['stock.lot'].create([{
            'name': 'lot_product_a_' + str(i + 1),
            'product_id': self.productA.id,
            'company_id': self.env.company.id,
        } for i in range(4)])

        move = self.env['stock.move'].create({
            'name': self.productA.name,
            'product_id': self.productA.id,
            'product_uom_qty': 15,
            'product_uom': self.productA.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id
        })

        self.move_line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id,
            'quantity': 5,
            'picking_id': move.picking_id.id,
            'picking_partner_id': move.picking_id.partner_id.id,
            'customer_category_id': move.picking_id.partner_id.customer_category_id.id,
            'route_id': move.picking_id.partner_id.route_id.id,
            'movement_type_id': move.product_id.move_type_id.id,
            'scheduled_date': move.picking_id.scheduled_date,
            'priority': move.picking_id.priority
        })

    def test_split_stock_move_lines(self):
        lines = [self.move_line]
        total_lines = 1
        waves_to_be_created = 1
        max_lines_per_wave = 1
        chunks = self.move_line.split_stock_move_lines(
            wave_based_on='max_no_of_lines',
            lines=lines,
            total_lines=total_lines,
            waves_to_be_created=waves_to_be_created,
            max_lines_per_wave=max_lines_per_wave
        )
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(chunks[0]), 1)

        lines = [self.move_line, self.move_line]
        total_lines = 2
        waves_to_be_created = 1
        max_lines_per_wave = 1
        chunks = self.move_line.split_stock_move_lines(
            wave_based_on='max_no_of_lines',
            lines=lines,
            total_lines=total_lines,
            waves_to_be_created=waves_to_be_created,
            max_lines_per_wave=max_lines_per_wave
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0]), 1)

        lines = [self.move_line, self.move_line, self.move_line]
        total_lines = 3
        waves_to_be_created = 1
        max_lines_per_wave = 1
        chunks = self.move_line.split_stock_move_lines(
            wave_based_on='max_no_of_lines',
            lines=lines,
            total_lines=total_lines,
            waves_to_be_created=waves_to_be_created,
            max_lines_per_wave=max_lines_per_wave
        )
        self.assertEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0]), 1)

        lines = [self.move_line, self.move_line,
                 self.move_line, self.move_line]
        total_lines = 4
        waves_to_be_created = 1
        max_lines_per_wave = 2
        chunks = self.move_line.split_stock_move_lines(
            wave_based_on='max_no_of_lines',
            lines=lines,
            total_lines=total_lines,
            waves_to_be_created=waves_to_be_created,
            max_lines_per_wave=max_lines_per_wave
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0]), 2)
        self.assertEqual(len(chunks[1]), 2)

        lines = [self.move_line, self.move_line,
                 self.move_line, self.move_line, self.move_line]
        total_lines = 5
        waves_to_be_created = 1
        max_lines_per_wave = 2
        chunks = self.move_line.split_stock_move_lines(
            wave_based_on='max_no_of_lines',
            lines=lines,
            total_lines=total_lines,
            waves_to_be_created=waves_to_be_created,
            max_lines_per_wave=max_lines_per_wave
        )
        self.assertEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0]), 2)
        self.assertEqual(len(chunks[1]), 2)
