from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
    
class stock_move(models.Model):
    _inherit = "stock.move"
    
    move_daily_id = fields.Many2one("stock.move.daily.sugar", string="Stock Move Daily Sugar")
    move_daily_sugar_retail_id = fields.Many2one("stock.move.daily.sugar.retail", string="Stock Move Daily Sugar Retail")
#     move_daily_sugar_premium_id = fields.Many2one("stock.move.daily.sugar.premium", string="Stock Move Daily Sugar Premium")
    move_daily_molasses_id = fields.Many2one("stock.move.daily.molasses", string="Move Daily Molasses")
    move_daily_bagasse_id = fields.Many2one("stock.move.daily.bagasse", string="Move Daily Bagasse")

    @api.multi
    def name_get(self):
        res = []
        for move in self:
            if move.location_dest_id.usage == 'production':
                    res.append((move.id, '%s > %s' % (
                        move.picking_id.name or '',
                        move.no_bukti_pengeluaran or ''
                )))
            else:
                res.append((move.id, '%s%s%s>%s' % (
                    move.picking_id.origin and '%s/' % move.picking_id.origin or '',
                    move.product_id.code and '%s: ' % move.product_id.code or '',
                    move.location_id.name, move.location_dest_id.name)))
    
        return res            