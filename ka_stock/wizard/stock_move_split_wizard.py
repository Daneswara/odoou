from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class stock_move_split_wizard(models.TransientModel):
    _name = "stock.move.split.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(stock_move_split_wizard,self).default_get(fields)
        move_id = self._context.get('active_id', False)
        move_vals = []
        for move in self.env['stock.move'].browse(move_id):
            move_vals.append((0,0,{'product_qty': move.product_uom_qty,
                                   'truck_number': move.truck_number,
                                   'agent_partner_id': move.agent_partner_id.id or False,
                                   'delivery_number': move.delivery_number,
                                   'brix_percent': move.brix_percent,
                                   'tank_id': move.tank_id.id or False}))
        res['move_id'] = move_id
        res['split_lines'] = move_vals
        return res
    
    move_id = fields.Many2one('stock.move', 'Stock Move')
    split_lines = fields.One2many('stock.move.split.wizard.line', 'split_id', 'Split Lines')
    
    @api.multi
    def do_split_stock_move(self):
        for this in self:
            if this.split_lines:
                picking_id = this.move_id.picking_id
                product_id = this.move_id.product_id
                total_qty = 0.0
                for line in this.split_lines:
                    total_qty += line.product_qty
                if total_qty > this.move_id.product_uom_qty:
                    raise UserError('Sorry, the total quantity cannot greater than quantity in stock move')
                # create moves per line in wizard
                for line in this.split_lines:
                    this.move_id.copy({'product_uom_qty': line.product_qty,
                                       'truck_number': line.truck_number,
                                       'agent_partner_id': line.agent_partner_id.id or False,
                                       'delivery_number': line.delivery_number,
                                       'brix_percent': line.brix_percent,
                                       'tank_id': line.tank_id.id})
                # create move for rest qty
                move_rest = False
                qty_rest = this.move_id.product_uom_qty - total_qty
                if qty_rest > 0:
                    move_rest = this.move_id.copy({'product_uom_qty': qty_rest})
                # cancel and delete old stock move
                this.move_id.action_cancel()
                this.move_id.unlink()
                # confirm and reserve picking
                picking_id.action_confirm()
                picking_id.action_assign()
                #unreserve res move
                if move_rest:
                    for move in move_rest:
                        move.do_unreserve()
                # change qty done in pack operation
                packop_qty = 0.0
                for move in picking_id.move_lines:
                    packop_qty += move.reserved_availability
                packop_src = self.env['stock.pack.operation'].search([('picking_id','=',picking_id.id),('product_id','=',product_id.id)])
                for packop in packop_src:
                    packop.write({'qty_done': packop_qty})
                
    
class stock_move_split_wizard_line(models.TransientModel):
    _name = "stock.move.split.wizard.line"
    
    split_id = fields.Many2one('stock.move.split.wizard', 'Move Split')
    product_qty = fields.Float('Quantity')
    truck_number = fields.Char('No. Kendaraan')
    agent_partner_id = fields.Many2one('res.partner', string="Agen", domain=[('company_type', '=', 'person')])
    delivery_number = fields.Char('No. Kirim')
    brix_percent = fields.Float('Brix (%)')
    tank_id = fields.Many2one('stock.tank', 'Tangki')
    
    