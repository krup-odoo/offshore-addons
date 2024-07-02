# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tools import groupby
from collections import defaultdict
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    keimed_wave_id = fields.Many2one('keimed.wave')
    keimed_wave_state = fields.Selection(related='keimed_wave_id.state')
    picking_partner_id = fields.Many2one(
        related='picking_id.partner_id', readonly=True, store=True)
    customer_category_id = fields.Many2one(
        related='picking_partner_id.customer_category_id',
        string='Customer Category', store=True)
    route_id = fields.Many2one(
        related='picking_id.partner_id.route_id', string='Route', store=True)
    movement_type_id = fields.Many2one(
        related="product_id.move_type_id", string='Movement Type', store=True)
    scheduled_date = fields.Datetime(
        related='picking_id.scheduled_date')
    priority = fields.Selection(
        related='picking_id.priority', string='Priority', store=True)
    to_do = fields.Float(
        string='To-Do', copy=False)
    user_id = fields.Many2one(
        'res.users', compute='_compute_picker', store=True)
    note = fields.Text(string='Note')
    is_stock_move_line_created = fields.Boolean(string='Is Stock Move Line Created')

    @api.depends('location_id', 'company_id')
    def _compute_picker(self):
        for rec in self:
            user = False
            if rec.keimed_wave_id and rec.keimed_wave_id.is_snake_picking_wave:
                picker_attendance = self.env['picker.attendance'].search([
                    ('location_id', '=', rec.location_id.id),
                    ('company_id', '=', rec.company_id.id),
                    ('checkin_date', '!=', False),
                    ('checkout_date', '=', False),
                ], order='id desc', limit=1)
                if picker_attendance:
                    user = picker_attendance.user_id
            rec.user_id = user

    def picked_button_action(self):
        if self.keimed_wave_id.is_snake_picking_wave and self.user_id != self.env.user:
            raise ValidationError(
                _('You can not pick this product. You can only pick the products, where you are assigned as a picker.'))
        self.picked = True
        self.move_ids.write({
            'to_do': 0,
            'to_do_check': True
        })
        if self.move_ids and all(line.picked for line in self.keimed_wave_id.stock_move_line_ids.filtered(lambda x: x.move_ids == self.move_ids)):
            self.move_ids.picked = True

    def change_basket_button_action(self):
        if self.result_package_id:
            other_lines = self.keimed_wave_id.stock_move_line_ids.filtered(
                lambda m: not m.picked and not m.to_do)
            other_lines.write({
                'result_package_id': self.result_package_id
            })

    def action_group_by_filter(self):
        return {
            'name': _("Group by / filter by"),
            'type': 'ir.actions.act_window',
            'res_model': 'groupby.filter.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_split_waves(self):
        view = self.env.ref(
            'keimed_auto_wave_picking.split_wave_wizard_view_form')
        return {
            'name': _('Split into Waves'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'split.wave.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_no_of_lines_to_be_picked': len(self)},
        }

    def create_keimed_stock_move(self, move):
        return self.env['keimed.stock.move'].create({
            'move_ids': move.ids.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'product_uom_qty': move.product_uom_qty.id,
            'product_uom': move.product_uom.id,
            'stock_move_line_ids': [Command.link(id) for id in self.ids],
        })

    def _add_to_keimed_wave(self):
        wave = self.env['keimed.wave'].create({
            'picker_id': self._context.get('active_owner_id'),
            'is_snake_picking_wave': self._context.get('is_snake_picking'),
        })
        wave_vals = {
            'move_ids': [],
        }
        grouped_stock_move_lines = groupby(self, lambda ml: (ml.product_id, ml.location_id, ml.lot_id))

        grouped_move_lines = {}
        for key, move_lines in grouped_stock_move_lines:
            grouped_move_lines[key] = self.env['stock.move.line'].concat(*list(move_lines))
        for key, lines in grouped_move_lines.items():
                product_id, location_id, lot_ids = key
                quantity = sum(line.quantity for line in lines if line.quantity)
                move_ids = [line.move_id.id for line in lines if line.move_id]
                location_dest_id = lines[0].location_dest_id.id if lines and lines[0].location_dest_id else None

                new_move_data = {
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'lot_ids': lot_ids.id if lot_ids else False, 
                    'quantity': quantity,
                    'location_dest_id': location_dest_id,
                    'stock_move_line_ids': [Command.link(id) for id in lines.ids],
                    'move_ids': [Command.link(id) for id in move_ids],
                }

                new_move = self.env['keimed.stock.move'].create(new_move_data)
                wave_vals['move_ids'].append(new_move.id)

        wave.write(wave_vals)
        self.write({'is_stock_move_line_created': True})

    def generate_pickings(self):
        move_lines = self.browse(self._context.get('active_ids'))
        if len(move_lines.company_id) > 1:
            raise UserError(
                _("The selected operations should belong to the same company."))
        elif len(move_lines.picking_type_id) > 1:
            raise UserError(
                _("The selected operations should belong to the same operation type."))
        return move_lines._add_to_keimed_wave()

    def action_create_snake_pickings(self):
        action = self.action_split_waves()
        action.update({
            'name': _('Split into Snake Pickings')
        })
        action.get('context').update({
            'is_snake_picking': True,
        })
        return action

    def split_stock_move_lines(self, wave_based_on='max_no_of_wave', lines=False, total_lines=0, waves_to_be_created=0, max_lines_per_wave=0):
        """
        Splits stock.move.line records into chunks.
        """
        chunks = []
        if wave_based_on == 'max_no_of_lines':
            # Split the move lines into chunks of the given size
            for i in range(0, total_lines, max_lines_per_wave):
                chunk = lines[i:i + max_lines_per_wave]
                chunks.append(chunk)
        else:
            # Splits move lines into given maximum waves
            wave_size = total_lines // waves_to_be_created
            # Calculate the size of the last wave
            last_wave_size = wave_size + (total_lines % waves_to_be_created)
            start_index = 0

            for i in range(waves_to_be_created - 1):
                end_index = start_index + wave_size
                chunks.append(lines[start_index:end_index])
                start_index = end_index

            # Add the last wave with the remaining lines
            chunks.append(lines[start_index:start_index + last_wave_size])
        return chunks

    def new_add_to_wave(self, wave_based_on='max_no_of_wave', lines=False, total_lines=0, waves_to_be_created=0, max_lines_per_wave=0):
        stock_move_lines = self.split_stock_move_lines(
            wave_based_on=wave_based_on,
            lines=lines,
            total_lines=total_lines,
            waves_to_be_created=waves_to_be_created,
            max_lines_per_wave=max_lines_per_wave)

        for move_lines in stock_move_lines:
            move_lines._add_to_keimed_wave()
