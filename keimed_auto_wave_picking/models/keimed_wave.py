# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class KeimedWave(models.Model):
    _name = 'keimed.wave'
    _inherit = ['mail.thread']
    _description = 'Keimed Wave'

    name = fields.Char('Wave Reference', required=True,
                       copy=False, default='New')
    picker_id = fields.Many2one('res.users', string='Picker', tracking=True)
    login_user_id = fields.Many2one('res.users', compute='_compute_login_user')
    company_id = fields.Many2one(
        'res.company', tracking=True, required=True,
        default=lambda self: self.env.company)
    checker_id = fields.Many2one('res.users', tracking=True, copy=False)
    scheduled_date = fields.Datetime(tracking=True, copy=False)
    move_line_ids = fields.One2many(
        'keimed.stock.move.line', 'keimed_wave_id', string='Detailed Operations')
    move_ids = fields.One2many(
        'keimed.stock.move', 'keimed_wave_id', string='Operations')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')],
        string='Status', default='draft', required=True, copy=False,
        tracking=True)
    is_snake_picking_wave = fields.Boolean()

    # picker fields
    picked = fields.Boolean(
        string='Picked', compute='_compute_picked', store=True, copy=False)
    no_of_items_to_pick = fields.Integer(
        string='Remaining to Pick', compute='_compute_no_of_items_pick',
        store=True, copy=False)
    no_of_items_picked = fields.Integer(
        string='Items Picked', compute='_compute_no_of_items_pick',
        store=True, copy=False)

    # checker fields
    checked = fields.Boolean(
        string='Checked', compute='_compute_checked', store=True, copy=False)
    no_of_items_to_check = fields.Integer(
        string='Remaining to Check', compute='_compute_no_of_items_check',
        store=True, copy=False)
    no_of_items_checked = fields.Integer(
        string='Items Checked', compute='_compute_no_of_items_check',
        store=True, copy=False)

    def _compute_login_user(self):
        for rec in self:
            rec.login_user_id = self.env.user

    @api.depends('move_ids.picked', 'state')
    def _compute_picked(self):
        for rec in self:
            if rec.state == 'done' or all(move.picked for move in rec.move_ids):
                rec.picked = True
            else:
                rec.picked = False

    @api.depends('move_ids.checked', 'state')
    def _compute_checked(self):
        for rec in self:
            if rec.state == 'done' or all(move.checked for move in rec.move_ids):
                rec.checked = True
            else:
                rec.checked = False

    @api.depends('move_ids.picked')
    def _compute_no_of_items_pick(self):
        for rec in self:
            no_of_items_to_pick = len(
                rec.move_ids.filtered(lambda m: not m.picked).ids)
            rec.no_of_items_to_pick = no_of_items_to_pick
            rec.no_of_items_picked = len(
                rec.move_ids.ids) - no_of_items_to_pick

    @api.depends('move_ids.checked')
    def _compute_no_of_items_check(self):
        for rec in self:
            no_of_items_to_check = len(
                rec.move_ids.filtered(lambda m: not m.checked).ids)
            rec.no_of_items_to_check = no_of_items_to_check
            rec.no_of_items_checked = len(
                rec.move_ids.ids) - no_of_items_to_check

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                if vals.get('is_snake_picking_wave'):
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'snake.picking') or '/'
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'keimed.wave') or '/'
        return super(KeimedWave, self).create(vals_list)

    def action_confirm(self):
        """Sanity checks and mark the batch as confirmed."""
        self.ensure_one()
        if not self.move_ids:
            raise UserError(_("You have to set some operations to wave."))
        self._check_company()
        self.write({'state': 'in_progress'})
        return True

    def action_done(self):
        self._check_company()

        not_eligible_waves = self.filtered(
            lambda x: x.state not in ['in_progress', 'done'] or not x.picked or not x.checked)
        if not_eligible_waves:
            msg = 'Maybe ' + \
                ', '.join(not_eligible_waves.mapped('display_name'))
            if len(not_eligible_waves) > 1:
                msg += ' are'
            else:
                msg += ' is'
            msg += ' not in correct state. Wave should be in In Progress state to be done and it should be picked and checked.'
            raise UserError(_(msg))

        self.write({'state': 'done'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_view_stock_move_line_snake_picking(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'keimed_auto_wave_picking.action_stock_move_line_keimed_auto_wave_picking')
        action['domain'] = [('keimed_wave_id', 'in', self.ids)]
        action['context'] = {'keimed_wave_state': self.state}
        return action

    def action_view_stock_move_snake_picking(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'keimed_auto_wave_picking.action_stock_move_keimed_auto_wave_picking')
        action['domain'] = [('keimed_wave_id', 'in', self.ids)]
        action['context'] = {'keimed_wave_state': self.state}
        return action
