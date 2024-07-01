# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo.exceptions import ValidationError
from odoo import api, models, fields, _


class KeimedStockMove(models.Model):
    _name = 'keimed.stock.move'
    _inherit = ['mail.thread']
    _description = 'Keimed Stock Move'

    move_ids = fields.Many2many('stock.move', required=True)
    keimed_wave_id = fields.Many2one(
        'keimed.wave', string='Keimed Wave')
    keimed_wave_state = fields.Selection(related='keimed_wave_id.state')
    company_id = fields.Many2one(
    'res.company', string='Company', compute='_compute_company_id', store=True)
    product_id = fields.Many2one(
    'product.product', string='Product', compute='_compute_product_id', store=True)
    product_uom_qty = fields.Float(
        string='Demand',
        digits='Product Unit of Measure', default=0, required=True,
        help="This is the quantity of product that is planned to be moved.")
    product_uom = fields.Many2one(
        string='UoM', required=True)
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
        string='Unit Price', copy=False)
    origin = fields.Char(related='move_ids.origin', string='Source Document')
    move_line_ids = fields.One2many('keimed.stock.move.line', 'keimed_move_id')
    has_tracking = fields.Selection(
        related='product_id.tracking', string='Product with Tracking')
    quantity = fields.Float(
        'Quantity', compute='_compute_quantity',
        digits='Product Unit of Measure', store=True)

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
    stock_move_line_ids = fields.Many2many('stock.move.line')

    @api.depends('move_ids')
    def _compute_company_id(self):
        for record in self:
            if record.move_ids:
                record.company_id = record.move_ids.company_id

    @api.depends('move_ids')
    def _compute_product_id(self):
        for record in self:
            if record.move_ids:
                record.product_id = record.move_ids.product_id

    @api.depends('product_id')
    def _compute_product_uom(self):
        for move in self:
            move.product_uom = move.product_id.uom_id.id
    
    @api.depends('stock_move_line_ids.quantity')
    def _compute_quantity(self):
        for move in self:
            total_quantity = sum(move.stock_move_line_ids.mapped('quantity'))
            move.quantity = total_quantity

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
            rec.picker_id = picker

    @api.onchange('to_do')
    def on_change_to_do(self):
        if self.to_do < 0.0 or self.to_do > self.product_uom_qty:
            raise ValidationError(
                _("The to do quantity must be greater than zero and less than demanded quantity"))
        else:
            self.picked = False

    def picked_button_action(self):
        if self.keimed_wave_id.is_snake_picking_wave and self.picker_id != self.env.user:
            raise ValidationError(
                _('You can not pick this product. You can only pick the products, where you are assigned as a picker.'))
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

    def show_stock_move_lines(self):
        operation_type = 'detailed_operation' if self.env.context.get('detailed_operation') else 'operation'
        return {
            "type": "ir.actions.act_window",
            "name": "Stock Move Lines",
            "res_model": "stock.move.lines.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                'default_stock_move_line_ids': self.stock_move_line_ids.ids,
                'operation_type': operation_type
        }
    }
