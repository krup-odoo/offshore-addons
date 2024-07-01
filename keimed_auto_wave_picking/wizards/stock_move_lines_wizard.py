# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockMoveLineWizard(models.TransientModel):
    _name = 'stock.move.lines.wizard'
    _description = 'Stock Move Lines Wizard'


    stock_move_line_ids = fields.Many2many('stock.move.line', string='Stock Move Lines')

    @api.model
    def default_get(self, fields):
        res = super(StockMoveLineWizard, self).default_get(fields)
        if 'default_stock_move_line_ids' in self.env.context:
            res['stock_move_line_ids']: [Command.link(id) for id in self.env.context['default_stock_move_line_ids']]
        return res
