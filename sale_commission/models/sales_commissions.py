# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SalesCommission(models.Model):
    _name = "sales.commissions"
    
    date = fields.Date()
    sales_person_id = fields.Many2one('res.users')
    sales_team_id = fields.Many2one('crm.team')
    invoice_id = fields.Many2one('account.move')
    currency_id = fields.Many2one('res.currency')
    amount = fields.Monetary(string="Amount")
