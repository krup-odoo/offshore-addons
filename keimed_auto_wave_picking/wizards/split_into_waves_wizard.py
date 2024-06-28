# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SplitWaveWizard(models.TransientModel):
    _name = 'split.wave.wizard'
    _description = 'Split into Waves Wizard'

    no_of_lines_to_be_picked = fields.Integer(
        string='No. of Lines to be Picked', readonly=True)
    wave_based_on = fields.Selection(selection=[
        ('max_no_of_wave', 'Maximum No. Of Waves'),
        ('max_no_of_lines', 'Maximum No. Of Lines')],
        default='max_no_of_wave',
        string='Create Waves Based On')
    no_of_waves_to_be_created = fields.Integer(
        string='No. of Waves to be Created')
    max_lines_per_wave = fields.Integer(string='No. of Lines')
    scheduled_date = fields.Date()
    user_id = fields.Many2one('res.users', string='Picker')
    picking_ids = fields.Many2many('stock.picking')
    line_ids = fields.Many2many('stock.move.line')
    wave_id = fields.Many2one(
        'stock.picking.batch', string='Wave Transfer',
        domain="[('is_wave', '=', True), ('state', 'in', ('draft', 'in_progress'))]")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        lines = self.env['stock.move.line'].browse(
            self.env.context.get('active_ids'))
        res['line_ids'] = self.env.context.get('active_ids')
        picking_types = lines.picking_type_id
        if len(picking_types) > 1:
            raise UserError(
                _("The selected operations should belong to the same operation type"))
        return res

    def attach_pickings(self):
        self.ensure_one()
        if self.user_id:
            self = self.with_context(active_owner_id=self.user_id.id)
        if self.line_ids:
            company = self.line_ids.company_id
            if len(company) > 1:
                raise UserError(
                    _("The selected operations should belong to a unique company."))

            elif self.wave_based_on == 'max_no_of_wave':
                if self.no_of_waves_to_be_created <= 0:
                    raise UserError(
                        _("The enter number of waves to be created."))
                if self.no_of_lines_to_be_picked < self.no_of_waves_to_be_created:
                    raise UserError(
                        _("The number of waves to be created should be less than number lines to be picked."))

            elif self.wave_based_on == 'max_no_of_lines':
                if self.max_lines_per_wave <= 0:
                    raise UserError(
                        _("The enter maximum number of lines per wave."))
                if self.no_of_lines_to_be_picked < self.max_lines_per_wave:
                    raise UserError(
                        _("The maximum number of lines per wave should be less than number lines to be picked."))

            return self.line_ids.new_add_to_wave(
                wave_based_on=self.wave_based_on,
                lines=self.line_ids,
                total_lines=self.no_of_lines_to_be_picked,
                waves_to_be_created=self.no_of_waves_to_be_created,
                max_lines_per_wave=self.max_lines_per_wave)

        else:
            raise UserError(_('Can not create wave transfers.'))
