from odoo import api, fields, models, _
        
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    is_product_request_src_id = fields.Boolean('Request Barang Dari Unit', default=False, copy=False)