from odoo import models, fields

class logistik_spm(models.Model):
    _inherit = 'logistik.spm'

    sp_ids = fields.One2many('purchase.order', 'spm_id', string='Realisasi SP', readonly=True)
    
class KaLogistikSpmLines(models.Model):
    _inherit = 'logistik.spm.lines'
    
    def open_order_lines(self):
        action = self.env.ref('purchase.action_purchase_line_product_tree')
        result = action.read()[0]
        result['domain'] = [('spm_line_id', '=', self.id)]
        return result    
   
    