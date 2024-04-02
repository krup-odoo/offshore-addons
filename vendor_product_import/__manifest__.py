# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Vendor Product Import',
    'version' : '17.0.1.0.0',
    'category': 'Sales',
    'summary' : 'Vendor Product Import ',
    'website' : 'https://www.odoo.com',
    'description' : """Vendor Product Import
                       Task ID = 3822095""",
    'author' : 'Odoo Ps',
    'depends' : [
        'sale_management',
        'purchase',
        'stock_delivery',
    ],
    'data' : [
        "security/ir.model.access.csv",
        "data/vendor_product_import_sequence.xml",
        "views/vendor_product_template_views.xml",
        "views/vendor_product_import_views.xml",
        "views/product_template_views.xml",
        "views/vendor_product_import_menus.xml",
    ],
    'installable': True,
    'application': False,
}
