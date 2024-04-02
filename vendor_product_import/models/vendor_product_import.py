# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, Command
import xlrd
import tempfile
import binascii 
from odoo.exceptions import UserError,ValidationError


class VendorProductImport(models.Model):
    _name = "vendor.product.import"
    _description = "Vendor Product Import"
    _inherit = ['mail.thread']

    sequence = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
        index=True,
        default=lambda self: ('New'))
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    file = fields.Binary(string="File To Process", required=True, attachment=True)
    vendor_template_id = fields.Many2one('vendor.product.template', domain="[('vendor_id', '=',  vendor_id)]", string='Vendor Template Format', required=True)
    date = fields.Datetime(string='Date')
    stage = fields.Selection([('pending', 'Pending'), ('processed', 'Processed'), ('error', 'Error')], default='pending', tracking=True)
    file_name = fields.Char('File Name')
    import_history_id = fields.Many2one('product.import.history')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['sequence'] = self.env['ir.sequence'].next_by_code('vendor.product.import')
        return super(VendorProductImport, self).create(vals_list)

    @api.onchange("vendor_id")
    def _onchange_vendor_id(self):
        if self.vendor_id:
            if self.env['vendor.product.template'].search([('vendor_id', '=', self.vendor_id.id)]):
                self.vendor_template_id = 1
            else:
                self.vendor_template_id = ''

    def product_maker(self, column_name, row_value, val, update):
        try:
            odoo_field = []
            num = 0
            uom_num = 0
            product_detail = {}
            for record in self.vendor_template_id.odoo_field_ids:
                field_type=self.env['ir.model.fields'].search([('model', '=', 'product.template'),('name', '=', record.odoo_field_id.name)]).ttype
                if record.odoo_field_id.name == 'uom_id':
                    uom_num = num
                if field_type == 'many2one' or field_type == 'int':
                    row_value[val][num] = int(float(row_value[val][num]))
                elif field_type == 'float':
                    row_value[val][num] = float(row_value[val][num])
                num+=1
                odoo_field.append(record.odoo_field_id.name)
            for number in range(0,len(odoo_field)):
                product_detail.update({odoo_field[number]: row_value[val][number]})
            
            if update==1:
                product_detail.update({'name' : row_value[val][0] + " Imported", 'uom_po_id' : row_value[val][uom_num], 'vendor_product_ids': [Command.create({'import_reference': self.sequence, 'filename' : self.file_name,
                    'date_of_import' : self.date,}),]})
                product = self.env['product.template'].search([('default_code','=',row_value[val][0])]).update(
                        product_detail,)
            else:
                product_detail.update({'name' : row_value[val][0] + " Imported", 'uom_po_id' : row_value[val][2], 'vendor_product_ids': self.env['product.import.history'].create({
                                'import_reference' : self.sequence,
                                'filename' : self.file_name,
                                'date_of_import' : self.date,
                        }),})
                product = self.env['product.template'].create(
                            product_detail,)
            
        except ValueError as e:
            message_body = (e)
            self.message_post(body=message_body, message_type='notification')
            return 1

        return 0
                        

    def action_manual_process(self):
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        column_name = []
        row_value = []
        i = 0
        error = 0
        err = 1
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                column_name = list(fields)
            else:
                line = (map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                row_value.append(list(line))

        for value in range(0,len(column_name)):
            column_name[value] = column_name[value].decode("utf-8")

        for value in range(0,len(row_value)):
            for val in range(0,len(row_value[0][0])):
                if type(row_value[value][val]) == bytes:
                    row_value[value][val]=row_value[value][val].decode("utf-8")

        for record in self.vendor_template_id.odoo_field_ids:
            if(len(column_name)!=len(self.vendor_template_id.odoo_field_ids.mapped("file_header"))):
                error = 1
                self.stage = 'error'
                message_body = ("Length are not match with Template")
                self.message_post(body=message_body, message_type='notification')
                break
        
            if(record.file_header!=column_name[i]):
                error = 1
                self.stage = 'error'
                message_body = (record.file_header + " is not match with " + column_name[i])
                self.message_post(body=message_body, message_type='notification')
                break
            i+=1
        
        if error == 0:
            err = 0
            for val in range(0,len(row_value)):
                if self.env['product.template'].search([('default_code','=',row_value[val][0])]):
                    update = 1
                    if(self.product_maker(column_name,row_value,val,update)):
                        self.stage = 'error'
                        err = 1
                        break
                else:
                    update = 0
                    if(self.product_maker(column_name,row_value,val,update)):
                        self.stage = 'error'
                        err = 1
                        break
            if err == 0:
                self.stage = 'processed'