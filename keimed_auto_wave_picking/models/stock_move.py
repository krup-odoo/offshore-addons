# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    keimed_wave_id = fields.Many2one('keimed.wave')
    keimed_wave_state = fields.Selection(related='keimed_wave_id.state')
    basket_number_id = fields.Many2one(
        "stock.quant.package", string='Basket No.',
        compute='_compute_basket_number', inverse='_inverse_basket_number',
        store=True, copy=False, readonly=False)
    to_do = fields.Float(
        string='To-Do', compute='_compute_to_do', store=True, copy=False, readonly=False)
    checked = fields.Boolean(string='Checked', readonly=True, copy=False)
    to_do_change_count = fields.Integer(
        compute='_compute_to_do_count', string="To-do count",
        store=True, default=-1)
    to_do_check = fields.Boolean(default=True)

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
                rec.basket_number_id = rec.move_line_ids[0].result_package_id if len(rec.move_line_ids) > 1 else rec.move_line_ids.result_package_id
            else:
                rec.basket_number_id = False

    def _inverse_basket_number(self):
        for move in self.filtered(lambda m: m.keimed_wave_id):
            move_line = move.move_line_ids[0] if len(move.move_line_ids) > 1 else move.move_line_ids
            move_line.result_package_id = move.basket_number_id

    @api.onchange('to_do')
    def on_change_to_do(self):
        if self.to_do < 0.0 or self.to_do > self.product_uom_qty:
            raise ValidationError(_("The to do quantity must be greater than zero and less than demanded quantity"))
        else:
            self.picked = False

    def checked_button_action(self):
        self.ensure_one()
        self.write({
            'checked': True,
            'picked': True
        })
        self.to_do = 0.0

        move_lines = self.keimed_wave_id.stock_move_line_ids.filtered(
            lambda x: x.move_ids == self and not x.picked)
        if move_lines:
            move_lines.write({
                'picked': True
            })

    def create_keimed_stock_move(self, move_lines):
        return self.env['keimed.stock.move'].create({
            'move_ids': self.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'stock_move_line_ids': [Command.create({
                'move_line_id': line.id,
                'company_id': line.company_id.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'lot_id': line.lot_id.id,
                'package_id': line.package_id.id,
                'result_package_id': line.result_package_id.id,
                'location_id': line.location_id.id,
                'location_dest_id': line.location_dest_id.id,
            }) for line in move_lines]
        })
