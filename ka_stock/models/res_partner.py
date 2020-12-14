from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    sequence_permintaan_barang_id = fields.Many2one('ir.sequence', 'Sequence Permintaan Barang',
                                                    help='Sequence yang digunakan pada permintaan barang antar unit.')