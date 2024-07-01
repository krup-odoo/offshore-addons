# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class KeimedStockMoveLine(models.Model):
    _name = 'keimed.stock.move.line'
    _inherit = ['mail.thread']
    _description = 'Keimed Stock Move Line'

    keimed_move_id = fields.Many2one(
        'keimed.stock.move', 'Stock Operation',
        check_company=True, index=True)
    move_line_id = fields.Many2one('stock.move.line', required=True)
    keimed_wave_id = fields.Many2one(
        related='keimed_move_id.keimed_wave_id')
    keimed_wave_state = fields.Selection(related='keimed_wave_id.state')
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, required=True,
        index=True)
    product_id = fields.Many2one(
        'product.product', 'Product', ondelete="cascade",
        check_company=True, domain="[('type', '!=', 'service')]", index=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure', required=True,
        domain="[('category_id', '=', product_uom_category_id)]",
        compute="_compute_product_uom_id", store=True, readonly=False,
        precompute=True)
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    product_category_name = fields.Char(
        related="product_id.categ_id.complete_name", store=True,
        string="Product Category")
    quantity = fields.Float(
        'Quantity', digits='Product Unit of Measure', copy=False)
    picked = fields.Boolean(
        'Picked', compute='_compute_picked', store=True, readonly=False,
        copy=False)
    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id)]", check_company=True)
    package_id = fields.Many2one(
        'stock.quant.package', 'Source Package', ondelete='restrict',
        check_company=True,
        domain="[('location_id', '=', location_id)]")
    result_package_id = fields.Many2one(
        'stock.quant.package', 'Destination Package',
        ondelete='restrict', required=False, check_company=True,
        domain="['|', '|', ('location_id', '=', False), ('location_id', '=', location_dest_id), ('id', '=', package_id)]",
        help="If set, the operations are packed into this package")
    location_id = fields.Many2one(
        'stock.location', 'From', domain="[('usage', '!=', 'view')]",
        check_company=True, required=True, compute="_compute_location_id",
        store=True, readonly=False, precompute=True)
    location_dest_id = fields.Many2one(
        'stock.location', 'To', domain="[('usage', '!=', 'view')]",
        check_company=True, required=True, compute="_compute_location_id",
        store=True, readonly=False, precompute=True)
    location_usage = fields.Selection(
        string="Source Location Type", related='location_id.usage')
    location_dest_usage = fields.Selection(
        string="Destination Location Type", related='location_dest_id.usage')
    state = fields.Selection(
        related='keimed_move_id.state', store=True, related_sudo=False)
    tracking = fields.Selection(related='product_id.tracking', readonly=True)
    origin = fields.Char(related='keimed_move_id.origin', string='Source')
    # Dummy field for the detailed operation view
    quant_id = fields.Many2one('stock.quant', "Pick From", store=False)
    to_do = fields.Float(string='To-Do', copy=False)
    checked = fields.Boolean(string='Checked', readonly=True, copy=False)
    to_do_change_count = fields.Integer(
        compute='_compute_to_do_count', string="To-do count",
        store=True, default=-1)
    to_do_check = fields.Boolean(default=True)
    picker_id = fields.Many2one(
        related='keimed_move_id.picker_id', string='Picker', copy=False)
    note = fields.Text(string='Note')

    @api.depends('product_uom_id.category_id', 'product_id.uom_id.category_id', 'keimed_move_id.product_uom', 'product_id.uom_id')
    def _compute_product_uom_id(self):
        for line in self:
            if not line.product_uom_id or line.product_uom_id.category_id != line.product_id.uom_id.category_id:
                if line.keimed_move_id.product_uom:
                    line.product_uom_id = line.keimed_move_id.product_uom.id
                else:
                    line.product_uom_id = line.product_id.uom_id.id

    @api.depends('state')
    def _compute_picked(self):
        for line in self:
            if line.keimed_move_id.state == 'done':
                line.picked = True

    @api.depends('keimed_move_id', 'keimed_move_id.location_id', 'keimed_move_id.location_dest_id')
    def _compute_location_id(self):
        for line in self:
            if not line.location_id:
                line.location_id = line.keimed_move_id.location_id or line.picking_id.location_id
            if not line.location_dest_id:
                line.location_dest_id = line.keimed_move_id.location_dest_id or line.picking_id.location_dest_id

    @api.depends('to_do')
    def _compute_to_do_count(self):
        for rec in self:
            if not rec.picked and rec.to_do_check:
                rec.to_do_change_count += 1
                rec.to_do_check = False

    def picked_button_action(self):
        if self.keimed_wave_id.is_snake_picking_wave and self.picker_id != self.env.user:
            raise ValidationError(
                _('You can not pick this product. You can only pick the products, where you are assigned as a picker.'))
        self.picked = True
        self.move_id.write({
            'to_do': 0,
            'to_do_check': True
        })
        if self.move_id and all(line.picked for line in self.keimed_wave_id.move_line_ids.filtered(lambda x: x.move_id == self.move_id)):
            self.move_id.picked = True

    def change_basket_button_action(self):
        if self.result_package_id:
            other_lines = self.keimed_wave_id.move_line_ids.filtered(
                lambda m: not m.picked and not m.to_do)
            other_lines.write({
                'result_package_id': self.result_package_id
            })
