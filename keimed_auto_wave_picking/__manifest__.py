# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wave Picking',
    'version': '17.0.2.2.0',
    'description': """
        Auto Wave Picking
        -----------------
        Task ID: 3861564
    """,
    'category': 'Inventory',

    'depends': [
        'sale_management',
        'stock_picking_batch',
        'oi_keimed_respartner_inherit',
        'purchase_order_scheduler',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/stock_security.xml',

        'data/stock_data.xml',

        'views/res_company_views.xml',
        'views/stock_location_views.xml',
        'wizards/picker_attendance_wizard_views.xml',
        'wizards/stock_move_lines_wizard_view.xml',

        'views/stock_picking_type.xml',
        'views/pick_line_view.xml',

        'wizards/groupby_filterby_wizard_view.xml',
        'wizards/split_into_waves_wizard_view.xml',

        'views/stock_move_line_views.xml',
        'views/stock_move_views.xml',

        'views/keimed_wave_views.xml',
        'views/keimed_stock_move_views.xml',
        'views/menuitems.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'keimed_auto_wave_picking/static/src/**/*.js',
            'keimed_auto_wave_picking/static/src/**/*.xml'
        ],
    },

    'installable': True,
    'license': 'LGPL-3'
}
