from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    product_request_id = fields.Many2one('stock.product.request', 'Related Product Request')
        
    @api.multi
    def do_transfer(self):
        super(StockPicking, self).do_transfer()
        # create incoming shipment in destination unit if is_product_request_src_id = True
        for this in self:
            if this.sale_id.is_product_request_src_id == True:
                source_uid = self.env.user.company_id.intercompany_user_id.id
                ou_company = self.sudo(source_uid).partner_id.get_company_ref()[0]
                #search warehouse of destination unit
                warehouse_dest_id = False
                warehouse_dest_src = self.sudo(source_uid).env['stock.warehouse'].search([('company_id','=',ou_company.id)], limit=1)
                if warehouse_dest_src:
                    warehouse_dest_id = warehouse_dest_src
                #define move vals
                stock_moves = []
                for move in this.move_lines:
                    move_vals = {'product_id': move.product_id.id,
                                 'name': move.product_id.display_name,
                                 'product_uom': move.product_uom.id,
                                 'product_uom_qty': move.product_uom_qty,
                                 'location_id': self.env.ref('stock.stock_location_suppliers').id,
                                 'location_dest_id': warehouse_dest_id.in_type_id.default_location_dest_id.id,
                                 'picking_type_id': warehouse_dest_id.in_type_id.id,
                                 'warehouse_id': warehouse_dest_id.id,
                                 'state': 'draft',
                                 'origin': this.origin,
                                 'group_id': False,
                                 'company_id': ou_company.id}
                    stock_moves.append((0, 0, move_vals))
                    
                #search related product request
                product_request_id = False
                product_request_src = self.sudo(source_uid).env['stock.product.request'].search([('name','=',this.origin)], limit=1)
                if product_request_src:
                    product_request_id = product_request_src
                #create stock picking
                picking_vals = {'partner_id': self.env.user.company_id.partner_id.id,
                                'picking_type_id': warehouse_dest_id.in_type_id.id,
                                'location_id': self.env.ref('stock.stock_location_suppliers').id,
                                'location_dest_id': warehouse_dest_id.in_type_id.default_location_dest_id.id,
                                'min_date': this.min_date,
                                'origin': this.origin,
                                'product_request_id': product_request_id.id,
                                'company_id': ou_company.id,
                                'move_lines': stock_moves}
                new_picking = self.sudo(source_uid).env['stock.picking'].create(picking_vals)
                #mark as todo
                new_picking.action_confirm()

                    