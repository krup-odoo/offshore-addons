# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ProductImportHistory(models.Model):
    _name = 'product.import.history'
    _description = 'Product Import History'

    vendor_product_id = fields.Many2one("product.template")
    import_reference = fields.Char()
    date_of_import = fields.Date()
    filename = fields.Char()
