# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo.exceptions import ValidationError
from odoo import api, models, fields, _


class KeimedStockMove(models.Model):
    _name = 'keimed.stock.move'
    _inherit = ['mail.thread']
    _description = 'Keimed Stock Move'

    move_id = fields.Many2one('stock.move', required=True)
    keimed_wave_id = fields.Many2one(
        'keimed.wave', string='Keimed Wave')
    keimed_wave_state = fields.Selection(related='keimed_wave_id.state')
    company_id = fields.Many2one(related='move_id.company_id')
    product_id = fields.Many2one(related='move_id.product_id')
    product_uom_qty = fields.Float(
        related='move_id.product_uom_qty', string='Demand',
        digits='Product Unit of Measure', default=0, required=True,
        help="This is the quantity of product that is planned to be moved.")
    product_uom = fields.Many2one(
        related='move_id.product_uom', string='UoM', required=True)
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template',
        related='product_id.product_tmpl_id')
    state = fields.Selection([
        ('draft', 'New'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Status',
        copy=False, default='draft', index=True, readonly=True)
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        auto_join=True, index=True, required=True,
        check_company=True,
        help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        auto_join=True, index=True, required=True,
        check_company=True,
        help="Location where the system will stock the finished products.")
    location_usage = fields.Selection(
        string="Source Location Type", related='location_id.usage')
    location_dest_usage = fields.Selection(
        string="Destination Location Type", related='location_dest_id.usage')
    picked = fields.Boolean(
        'Picked', copy=False,
        help="This checkbox is just indicative, it doesn't validate or generate any product moves.")

    price_unit = fields.Float(
        related='move_id.price_unit', string='Unit Price', copy=False)
    origin = fields.Char(related='move_id.origin', string='Source Document')
    move_line_ids = fields.One2many('keimed.stock.move.line', 'keimed_move_id')
    has_tracking = fields.Selection(
        related='product_id.tracking', string='Product with Tracking')
    quantity = fields.Float(
        'Quantity', compute='_compute_quantity',
        digits='Product Unit of Measure', inverse='_set_quantity', store=True)

    product_type = fields.Selection(
        related='product_id.detailed_type', readonly=True)
    lot_ids = fields.Many2many(
        'stock.lot', compute='_compute_lot_ids', store=True,
        string='Lot Numbers')
    show_quant = fields.Boolean("Show Quant", compute="_compute_show_info")
    show_lots_m2o = fields.Boolean("Show lot_id", compute="_compute_show_info")
    show_lots_text = fields.Boolean(
        "Show lot_name", compute="_compute_show_info")
    checked = fields.Boolean(string='Checked', readonly=True, copy=False)

    basket_number_id = fields.Many2one(
        "stock.quant.package", string='Basket No.',
        compute='_compute_basket_number', inverse='_inverse_basket_number',
        store=True, copy=False, readonly=False)
    to_do = fields.Float(
        string='To-Do', compute='_compute_to_do', store=True, copy=False,
        readonly=False)
    to_do_change_count = fields.Integer(
        compute='_compute_to_do_count', string="To-do count",
        store=True, default=-1)
    to_do_check = fields.Boolean(default=True)
    picker_id = fields.Many2one(
        'res.users', compute='_compute_picker', store=True, copy=False)
    note = fields.Text(string='Note')

    @api.depends('product_id')
    def _compute_product_uom(self):
        for move in self:
            move.product_uom = move.product_id.uom_id.id

    def _quantity_sml(self):
        self.ensure_one()
        quantity = 0
        for move_line in self.move_line_ids:
            quantity += move_line.product_uom_id._compute_quantity(
                move_line.quantity, self.product_uom, round=False)
        return quantity

    @api.depends('move_line_ids.quantity', 'move_line_ids.product_uom_id')
    def _compute_quantity(self):
        """ This field represents the sum of the move lines `quantity`. It allows the user to know
        if there is still work to do.

        We take care of rounding this value at the general decimal precision and not the rounding
        of the move's UOM to make sure this value is really close to the real sum.
        """
        move_lines_ids = set()
        for move in self:
            move_lines_ids |= set(move.move_line_ids.ids)

        data = self.env['keimed.stock.move.line']._read_group(
            [('id', 'in', list(move_lines_ids))],
            ['keimed_move_id', 'product_uom_id'], ['quantity:sum']
        )
        sum_qty = defaultdict(float)
        for move, product_uom, qty_sum in data:
            uom = move.product_uom
            sum_qty[move.id] += product_uom._compute_quantity(
                qty_sum, uom, round=False)

        for move in self:
            move.quantity = sum_qty[move.id]

    @api.depends('move_line_ids.lot_id', 'move_line_ids.quantity')
    def _compute_lot_ids(self):
        domain = [('keimed_move_id', 'in', self.ids), ('lot_id',
                                                       '!=', False), ('quantity', '!=', 0.0)]
        lots_by_move_id = self.env['keimed.stock.move.line']._read_group(
            domain,
            ['keimed_move_id'], ['lot_id:array_agg'],
        )
        lots_by_move_id = {move.id: lot_ids for move,
                           lot_ids in lots_by_move_id}
        for move in self:
            move.lot_ids = lots_by_move_id.get(move._origin.id, [])

    @api.depends('has_tracking', 'state', 'product_id.detailed_type')
    def _compute_show_info(self):
        for move in self:
            move.show_quant = move.product_id.detailed_type == 'product'
            move.show_lots_m2o = not move.show_quant\
                and move.has_tracking != 'none' and move.state == 'done'
            move.show_lots_text = move.has_tracking != 'none' and move.state != 'done'

    @api.depends('quantity', 'product_uom_qty')
    def _compute_to_do(self):
        for record in self:
            record.to_do = record.product_uom_qty - record.quantity

    @api.depends('to_do')
    def _compute_to_do_count(self):
        for rec in self:
            if not rec.picked and rec.to_do_check:
                rec.to_do_change_count += 1
                rec.to_do_check = False

    @api.depends('move_line_ids', 'move_line_ids.result_package_id')
    def _compute_basket_number(self):
        for rec in self:
            if rec.move_line_ids:
                rec.basket_number_id = rec.move_line_ids[0].result_package_id if len(
                    rec.move_line_ids) > 1 else rec.move_line_ids.result_package_id
            else:
                rec.basket_number_id = False

    def _inverse_basket_number(self):
        for move in self.filtered(lambda m: m.keimed_wave_id):
            move_line = move.move_line_ids[0] if len(
                move.move_line_ids) > 1 else move.move_line_ids
            move_line.result_package_id = move.basket_number_id

    @api.depends('location_id', 'company_id')
    def _compute_picker(self):
        for rec in self:
            picker = False
            if rec.keimed_wave_id and rec.keimed_wave_id.is_snake_picking_wave:
                picker_attendance = self.env['picker.attendance'].search([
                    ('location_id', '=', rec.location_id.id),
                    ('company_id', '=', rec.company_id.id),
                    ('checkin_date', '!=', False),
                    ('checkout_date', '=', False),
                ], order='id desc', limit=1)
                if picker_attendance:
                    picker = picker_attendance.user_id
            if rec.company_id.picking_type != 'snake_picking' or rec.company_id.snake_picking_type != 'zone':
                rec.picker_id = picker

    @api.onchange('to_do')
    def on_change_to_do(self):
        if self.to_do < 0.0 or self.to_do > self.product_uom_qty:
            raise ValidationError(
                _("The to do quantity must be greater than zero and less than demanded quantity"))
        else:
            self.picked = False

    def picked_button_action(self):
        picker_attendances = self.env['picker.attendance'].search([
                        ('location_id', '=', self.location_id.id),
                        ('company_id', '=', self.company_id.id),
                        ('checkin_date', '!=', False),
                        ('checkout_date', '=', False),
                    ])
        user_ids = [record.user_id.id for record in picker_attendances]
        print(user_ids)
        if self.keimed_wave_id.is_snake_picking_wave and self.picker_id and self.picker_id.id != self.env.user.id:
            raise ValidationError(
                _('You can not pick this product. %s is picking this product.', self.picker_id.name))
        elif self.keimed_wave_id.is_snake_picking_wave and self.env.user.id not in user_ids:
            raise ValidationError(
                _('You can not pick this product. You can only pick the products, where you are assigned as a picker.'))
        if self.keimed_wave_id.is_snake_picking_wave:
            locations = self.keimed_wave_id.move_ids.filtered(lambda move: move.location_id.id == self.location_id.id)
            for loc in locations:
                loc.picker_id = self.env.user
        self.write({
            'picked': True,
            'to_do': 0,
            'to_do_check': True
        })
        # if self.move_id and all(line.picked for line in self.keimed_wave_id.move_line_ids.filtered(lambda x: x.move_id == self.move_id)):
        #     self.move_id.picked = True

    def change_basket_button_action(self):
        if self.result_package_id:
            other_lines = self.keimed_wave_id.move_line_ids.filtered(
                lambda m: not m.picked and not m.to_do)
            other_lines.write({
                'result_package_id': self.result_package_id
            })

    def checked_button_action(self):
        self.ensure_one()
        self.write({
            'checked': True,
            'picked': True,
            'to_do': 0.0
        })

        # move_lines = self.keimed_wave_id.move_line_ids.filtered(
        #     lambda x: x.move_id == self and not x.picked)
        # if move_lines:
        #     move_lines.write({
        #         'picked': True
        #     })
