# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class VendorProductTemplateLine(models.Model):
    _name = "vendor.product.template.line"
    _description = "Vendor Product Template Line"

    file_header = fields.Char(required=True)
    odoo_field_id = fields.Many2one("ir.model.fields", domain=[('model_id.model', '=', 'product.product')], required=True, ondelete="cascade")
    field_id = fields.Many2one("vendor.product.template", required=True)
