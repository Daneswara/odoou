from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class StockProductRequest(models.Model):
    _name = "stock.product.request"
    _description = "Permintaan Barang Antar Unit"
    _inherit = ['mail.thread']
    _order = "name desc"
    
    name = fields.Char('Number', default='New', copy=False, track_visibility='always')
    requester_id = fields.Many2one('res.users', 'Requester', default=lambda self: self.env.user.id)
    source_unit_id = fields.Many2one('res.partner', string="Dari Unit", domain=[('is_operating_unit', '=', True)])
    destination_unit_id = fields.Many2one('res.partner', string="Ke Unit", domain=[('is_operating_unit', '=', True)],
                                          default=lambda self: self.env.user.company_id.partner_id)
    order_date = fields.Date('Tanggal Order', help='Tanggal dokumen disubmit', copy=False, readonly=True)
    requested_date = fields.Date('Tanggal Diminta', track_visibility='onchange',
                                 help='Diisi dengan tanggal unit tujuan menerima produk.')
    state = fields.Selection([('draft', 'Draft'), 
                              ('submit', 'Submitted'), 
                              ('approved', 'Approved'),
                              ('cancel', 'Cancelled')], default='draft', string='Status', 
                             copy=False, track_visibility='onchange')
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    request_line_ids = fields.One2many('stock.product.request.line', 'product_request_id', 'Request Lines')
    picking_ids = fields.One2many('stock.picking', 'product_request_id', 'Created Transfers', copy=False)
    
    @api.multi
    def action_submit(self):
        for this in self:
            if this.name == 'New':
                this.name = this.source_unit_id.sequence_permintaan_barang_id.next_by_id()   
            this.order_date = datetime.now()
            this.state = 'submit' 
                
    @api.multi
    def action_approve(self):
        for this in self:
            so_line_vals = []
            so_categ_id = False
            for line in this.request_line_ids:
                line_vals = {'product_id': line.product_id.id,
                             'name': line.product_id.display_name,
                             'product_uom': line.uom_id.id,
                             'product_uom_qty': line.requested_qty,
                             'price_unit': line.product_id.lst_price}
                if so_categ_id == False:
                    categ_src = self.env['ka_sale.order.category'].search([('product_ids','=',line.product_id.id)], limit=1)
                    if categ_src:
                        so_categ_id = categ_src.id
                so_line_vals.append((0, 0, line_vals))
                
            source_uid = self.env.user.company_id.intercompany_user_id.id
            ou_company = self.sudo(source_uid).source_unit_id.get_company_ref()[0]
            ou_warehouse = self.env['stock.warehouse'].sudo(source_uid).search([('company_id','=',ou_company.id)], limit=1)
            
            so_vals = {'name': this.name,
                       'partner_id': this.destination_unit_id.id,
                       'so_categ_id': so_categ_id,
                       'requested_date': this.requested_date,
                       'date_order': datetime.now(),
                       'origin': this.name,
                       'operating_unit_id': ou_company.partner_id.id,
                       'company_id': ou_company.id,
                       'warehouse_id': ou_warehouse.id,
                       'is_product_request_src_id': True,
                       'order_line': so_line_vals}
            new_so = self.sudo(source_uid).env['sale.order'].create(so_vals)
            new_so.sudo(source_uid).action_confirm()
            this.state = 'approved'
            
    @api.multi
    def action_cancel(self):
        for this in self:
            this.state = 'cancel'
    
    @api.multi
    def action_set_draft(self):
        for this in self:
            this.state = 'draft'
    
    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('Sorry, you cannot delete non-draft transaction.')
        return super(StockProductRequest, self).unlink()
    
    @api.multi
    def action_view_picking(self):
        for this in self:
            if len(this.picking_ids) == 1:
                return {
                    'name': 'Stock Picking',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': this.picking_ids[0].id,
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'target': 'current',  
                }
            else:
                return {
                    'name': 'Stock Picking',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain': [('id','in',[x.id for x in this.picking_ids])],
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'target': 'current',  
                }
            
    
class StockProductRequestLine(models.Model):
    _name = "stock.product.request.line"
    
    product_request_id = fields.Many2one('stock.product.request', 'Product Request')
    product_id = fields.Many2one('product.product', 'Produk', domain="[('sale_ok','=',True)]")
    uom_id = fields.Many2one('product.uom', 'Satuan')
    requested_qty = fields.Float('Kuantum')
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
    
    
    