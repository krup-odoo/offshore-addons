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
    stock_move_line_ids = fields.Many2many('stock.move.line')
    keimed_wave_id = fields.Many2one(
        'keimed.wave', string='Keimed Wave')
    keimed_wave_state = fields.Selection(related='keimed_wave_id.state')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, index=True)
    product_uom_qty = fields.Float(
        string='Demand', digits='Product Unit of Measure',
        default=0, required=True,
        help="This is the quantity of product that is planned to be moved.")
    product_uom = fields.Many2one('uom.uom', string='UoM', required=True)
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

    price_unit = fields.Float(string='Unit Price', copy=False)
    has_tracking = fields.Selection(
        related='product_id.tracking', string='Product with Tracking')
    quantity = fields.Float(
        'Quantity', compute='_compute_quantity',
        digits='Product Unit of Measure', store=True)

    product_type = fields.Selection(
        related='product_id.detailed_type', readonly=True)
    lot_ids = fields.Many2many(
        'stock.lot', compute='_compute_lot_ids', store=True,
        string='Lot Numbers', index=True)
    show_quant = fields.Boolean("Show Quant", compute="_compute_show_info")
    show_lots_m2o = fields.Boolean("Show lot_id", compute="_compute_show_info")
    show_lots_text = fields.Boolean(
        "Show lot_name", compute="_compute_show_info")
    checked = fields.Boolean(string='Checked', readonly=True, copy=False)

    basket_number_id = fields.Many2one(
        "stock.quant.package", string='Basket No.',
        compute='_compute_basket_number', inverse='_inverse_basket_number',
        store=True, copy=False, readonly=False, index=True)
    to_do = fields.Float(
        string='To-Do', compute='_compute_to_do', store=True, copy=False)
    to_do_change_count = fields.Integer(string='To-do count')
    to_do_check = fields.Boolean(default=True)
    picker_id = fields.Many2one(
        'res.users', compute='_compute_picker', store=True, copy=False,
        index=True)
    note = fields.Text(string='Note')

    @api.depends('stock_move_line_ids.quantity')
    def _compute_quantity(self):
        for move in self:
            move.quantity = sum(move.stock_move_line_ids.mapped('quantity'))

    @api.depends('stock_move_line_ids.lot_id', 'stock_move_line_ids.quantity')
    def _compute_lot_ids(self):
        for move in self:
            move.lot_ids = move.stock_move_line_ids.mapped('lot_id')

    @api.depends('has_tracking', 'state', 'product_id.detailed_type')
    def _compute_show_info(self):
        for move in self:
            move.show_quant = move.product_id.detailed_type == 'product'
            move.show_lots_m2o = not move.show_quant\
                and move.has_tracking != 'none' and move.state == 'done'
            move.show_lots_text = move.has_tracking != 'none' and move.state != 'done'

    @api.depends('stock_move_line_ids.to_do')
    def _compute_to_do(self):
        for move in self:
            move.to_do = sum(move.stock_move_line_ids.mapped('to_do'))

    @api.depends('stock_move_line_ids', 'stock_move_line_ids.result_package_id')
    def _compute_basket_number(self):
        for rec in self:
            if rec.stock_move_line_ids:
                rec.basket_number_id = rec.stock_move_line_ids[0].result_package_id if len(
                    rec.stock_move_line_ids) > 1 else rec.stock_move_line_ids.result_package_id
            else:
                rec.basket_number_id = False

    def _inverse_basket_number(self):
        for move in self.filtered(lambda m: m.keimed_wave_id):
            move_line = move.stock_move_line_ids[0] if len(
                move.stock_move_line_ids) > 1 else move.stock_move_line_ids
            move_line.result_package_id = move.basket_number_id

    @api.depends('location_id', 'company_id')
    def _compute_picker(self):
        PickerAttendance = self.env['picker.attendance']
        for rec in self:
            picker = False
            if rec.keimed_wave_id and rec.keimed_wave_id.is_snake_picking_wave:
                picker_attendance = PickerAttendance.search([
                    ('location_id', '=', rec.location_id.id),
                    ('company_id', '=', rec.company_id.id),
                    ('checkin_date', '!=', False),
                    ('checkout_date', '=', False),
                ], order='id desc', limit=1)
                if picker_attendance:
                    picker = picker_attendance.user_id
            if rec.company_id.picking_type != 'snake_picking' or rec.company_id.snake_picking_type != 'zone':
                rec.picker_id = picker
            else:
                rec.picker_id = False

    def picked_button_action(self):
        self.ensure_one()
        if self.keimed_wave_id.is_snake_picking_wave and self.picker_id and self.picker_id.id != self.env.user.id:
            raise ValidationError(
                _('You can not pick this product. %s is picking this product.', self.picker_id.name))

        elif self.keimed_wave_id.is_snake_picking_wave:
            user_ids = self.env['picker.attendance'].search([
                ('location_id', '=', self.location_id.id),
                ('company_id', '=', self.company_id.id),
                ('checkin_date', '!=', False),
                ('checkout_date', '=', False),
            ]).mapped('user_id').ids

            if self.env.user.id not in user_ids:
                raise ValidationError(
                    _('You can not pick this product. You can only pick the products, where you are assigned as a picker.'))

            move_ids = self.keimed_wave_id.move_ids.filtered(
                lambda move: move.location_id.id == self.location_id.id)
            for move in move_ids:
                move.picker_id = self.env.user

        for line in self.stock_move_line_ids:
            line.to_do = 0

        self.write({
            'picked': True,
            'to_do_check': True
        })

    def change_basket_button_action(self):
        if self.result_package_id:
            other_lines = self.keimed_wave_id.stock_move_line_ids.filtered(
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

    def show_stock_move_lines(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Detailed Picklist",
            "res_model": "stock.move.line",
            "views": [[self.env.ref(
                'keimed_auto_wave_picking.stock_move_line_tree_view_as_wizard_keimed_auto_wave_picking'
            ).id, "tree"]],
            "target": "new",
            "domain": [("id", "in", self.stock_move_line_ids.ids)],
            "context": {
                'default_stock_move_line_ids': self.stock_move_line_ids.ids,
                'operation_type': 'detailed_operation' if self.env.context.get(
                    'detailed_operation') else 'operation',
                'checked': self.checked,
            }
        }

    def action_unlink_move(self):
        self.ensure_one()
        self.keimed_wave_id = False

    def action_approve_unlink(self):
        self.ensure_one()
        self.unlink()

    def action_reject_unlink(self):
        self.ensure_one()
        self.keimed_wave_id = self.stock_move_line_ids.mapped('keimed_wave_id')
