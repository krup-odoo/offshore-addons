# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Self order details',
    'version': '17.0.1.0.0',
    'category': 'Sales/Point Of Sale',
    'summary': 'Self order details',
    'website': 'https://www.odoo.com',
    'depends': [
        'pos_restaurant',
        'pos_self_order',
    ],
    'description': """
        Self order details,
        Task ID: 3822087
    """,
    'data':[],
    'assets': {
        'pos_self_order.assets': [
            "odoo_self_order_details/static/src/app/components/**/*",
        ],
    },
    'author': 'Odoo PS',
    'application':True,
    'installable':True,
    'licence':'LGPL-3',
}
