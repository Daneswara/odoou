from odoo import models, fields, api
from datetime import datetime
from docutils.nodes import field

class StockMoveDaily(models.Model):
    _name = "stock.move.daily"
    _description = "Stock Move Daily for PT Kebon Agung"
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name", default="New")
    date = fields.Date(string="Tanggal", default=fields.Datetime.now)
    state = fields.Selection([("draft", "Draft"),
                              ("done", "Done")],
                                string = "Status", default="draft", track_visibility="always")
    product_id = fields.Many2one("product.product", string="Product")
    real_qty = fields.Float("Real Qty")
    report_qty = fields.Float("Report Qty")
    product_uom = fields.Many2one("product.uom", string="Unit of Measure")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)
    
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.product_uom = self.product_id.uom_id
    