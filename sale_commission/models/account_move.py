# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    commission_created = fields.Boolean(default=False)

    def create_commission(self):
        self.commission_created = True
        curr_user = self.invoice_user_id
        curr_team = self.team_id

        commssion_rule = self.env['sales.commissions.rule']
        user_rule = commssion_rule.search([('sales_person_id', '=', curr_user.id)])
        user_team = commssion_rule.search([('sales_team_id', '=', curr_team.id)])

        all_rules = user_rule + user_team
        priority_rules = sorted(all_rules,key=lambda r: r.sequence)
    
        user_commission_amount = 0
        for line in self.invoice_line_ids:
            print("Invoice Line:", line)
            for rule in priority_rules:
                if rule.product_id == line.product_id:
                    user_commission_amount = (rule.commission_rate * line.price_subtotal)/100
                    if user_commission_amount > 0 and rule.commission_for == 'salesperson':
                        sales_person_id = curr_user.id
                        sales_team_id = False
                        break
           
        if user_commission_amount != 0:
            self.env["sales.commissions"].create({
                'date': fields.Date.today(),
                'sales_person_id': self.invoice_user_id.id,
                'invoice_id': self.id,
                'currency_id': self.currency_id.id,
                'amount': user_commission_amount,
            })

        team_commission_amount=0
        for line in self.invoice_line_ids:
            print('Invoice line :', line)
            for rule in priority_rules:
                if rule.product_id == line.product_id:
                    team_commission_amount = (rule.commission_rate * line.price_subtotal)/100
                    if team_commission_amount > 0 and rule.commission_for == 'salesteam':
                        sales_team_id = curr_team.id
                        sales_person_id = False
                        break
                    
        if team_commission_amount != 0:
            self.env["sales.commissions"].create({
                'date': fields.Date.today(),
                'sales_team_id': self.team_id.id,
                'invoice_id': self.id,
                'currency_id': self.currency_id.id,
                'amount': team_commission_amount,
            })
        
    def action_post(self):
        val=super().action_post()
        if not self.commission_created:
            self.create_commission()
        return val
    
    def action_register_payment(self):
        if not self.commission_created:
            self.create_commission()
        return super().action_register_payment()
