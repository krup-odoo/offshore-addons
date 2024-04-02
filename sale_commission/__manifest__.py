# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Commission',
    'version': '17.0.1.0.0',
    'summary': 'Sales Commissions rule',
    'category':'Sales',
    'description': """
        Sales Commissions rule,
        Task ID : 3822094
    """,
    'author': 'Odoo Ps',
    'website': "https://www.odoo.com",
    'depends':[
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_commission_rule_view.xml',
        'views/sales_commission_view.xml',
        'views/sales_commission_menu.xml',
    ],
    'installable': True,
    'application':True,
    'license': 'LGPL-3',
}
