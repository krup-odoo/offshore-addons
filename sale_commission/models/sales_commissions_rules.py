# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class SalesCommissionsModel(models.Model):
    _name = "sales.commissions.rule"
    _description = "Sales commissions"

    commission_rate = fields.Integer(required=True)
    commission_for = fields.Selection(
        string='Commission For',
        selection=[('salesperson', 'Salesperson'), ('salesteam', 'Salesteam')],
        copy=False
    )
    due_at = fields.Selection(
        selection=[('invoicing','Invoicing')],
        required=True, 
        copy=False, 
        string="Due At", 
        default="invoicing"
    )
    sequence = fields.Integer('Sequence', default=10)

    product_category_id = fields.Many2one(
        comodel_name='product.category', 
        string='Product Category'
    )
    product_id = fields.Many2one(
        comodel_name='product.product', 
        string='Product',
        domain="[('categ_id', 'child_of', product_category_id)]"
    )
    product_expired = fields.Selection(
        selection=[('noimpact', 'No Impact'),('yes', 'YES'),('no', 'NO')],
        required=True,
        copy=False
    )
    sales_person_id = fields.Many2one(
        comodel_name='res.users', 
        string="Salesperson", 
        required=True
    )
    sales_team_id = fields.Many2one(
        comodel_name='crm.team', 
        string="Salesteam", 
        required=True
    )
    max_discount = fields.Integer(
        required=True
    )
    on_fast_payment = fields.Boolean(
        string="On Fast Payment"
    )
    before_days = fields.Integer()
    condition = fields.Char(
        string="Condition",
        compute='_compute_condition',
        store=True
    )

    @api.onchange('on_fast_payment')
    def _onchange_payment(self):
        if self.on_fast_payment:
            self.before_days = 0
        else :
            self.before_days = False
    
    @api.depends('product_category_id','sales_team_id')
    def _compute_condition(self):
        for record in self:
            condition_value = ""
            if record.product_category_id and record.sales_team_id:
                condition_value = f"Category : {record.product_category_id.name} AND Team : {record.sales_team_id.name}"
            record.condition = condition_value
    