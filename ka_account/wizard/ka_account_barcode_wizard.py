from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import time

class ka_account_payment_confirm_wizard(models.TransientModel):
    _name = "ka_account.barcode.wizard"
    _inherit = ['barcodes.barcode_events_mixin']
    
    name = fields.Char('Name', default='', readonly=True)
    res_id = fields.Integer('Record ID')
    res_model = fields.Char('Model', size=64)
    barcode = fields.Text('QRCode', default="")
        
    
    @api.multi
    def action_tranfer_barcode(self):
        active_id = self._context.get('active_ids', False)[0]
        if active_id <> self.id:
            self.res_id = active_id
            self.res_model = self._context.get('active_model')
        self.name=""
        self.env[self.res_model].browse(self.res_id).action_barcode_scanned(self.barcode)
        return {
            'name': 'Scan Barcode Pengajuan',
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'ka_account.barcode.wizard',
            'res_id': self.id,
            'target': 'new',  
        }
        
    def on_barcode_scanned(self, barcode):    
        if barcode:
            self.barcode = barcode
            self.name="Klik Tranfer"
            