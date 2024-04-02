# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class VendorProductTemplate(models.Model):
    _name = "vendor.product.template"
    _description = "Vendor Product Template"

    name = fields.Char(required=True)
    vendor_id = fields.Many2one("res.partner", domain="[('supplier_rank','>','0')]", required=True)
    odoo_field_ids = fields.One2many("vendor.product.template.line","field_id")
