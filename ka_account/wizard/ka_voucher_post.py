from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class KaVoucherPost(models.TransientModel):
    _name = "ka_voucher.post.wizard" 
    _inherit = ['barcodes.barcode_events_mixin']
    
    date = fields.Date('Tanggal Posting', required=True)
    voucher_id = fields.Many2one('ka_account.voucher', 'Nomor Bukti')
    line_ids = fields.One2many('ka_voucher.post.line', 'post_id', string='Kas Bon')
            
    def on_barcode_scanned(self, barcode):    
        if barcode:
            voucher_ids = self.line_ids.mapped('voucher_id')
            voucher = self.env['ka_account.voucher'].search([
                ('name','=',barcode),
                ('state', 'in', ('proposed','approved')),
                ('id', 'not in', voucher_ids.ids)
                ])
                
            if voucher:
                self.voucher_id = voucher.id
            else:
                raise UserError('Nomor Bukti Kas tidak ditemukan')
            
    @api.onchange('line_ids')
    def _onchange_allowed_voucher_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
        result = {}

        # A kas bon can be selected only if at least one kas bon line is not already in the lines
        voucher_ids = self.line_ids.mapped('voucher_id')
        result['domain'] = {'voucher_id': [
            ('state', 'in', ('proposed','approved')),
            ('id', 'not in', voucher_ids.ids),
            ]}
        return result
      
    @api.onchange('voucher_id')
    def onchange_voucher(self):
        if not self.voucher_id:
            return {}

        new_lines = self.env['ka_voucher.post.line']
        # Load a line only once
        if self.voucher_id in self.line_ids.mapped('voucher_id'):
            return
        data = {'voucher_id':self.voucher_id.id,}
        new_line = new_lines.new(data)
        new_lines += new_line

        self.line_ids += new_lines
        self.voucher_id = False
        return {}
    
    def action_post_voucher(self):
        for line in self.line_ids:
            vals = {'date_approve': self.date, 'state':'approved'}
            line.voucher_id.write(vals)
            line.voucher_id.reconcile_voucher()
            
class KaVoucherPostLine(models.TransientModel):
    _name = "ka_voucher.post.line"

    post_id = fields.Many2one('ka_voucher.post.wizard')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    voucher_id = fields.Many2one('ka_account.voucher', 'Kas Bon')
    name = fields.Char(related='voucher_id.name') 
    journal_id = fields.Many2one('account.journal', related='voucher_id.journal_id',  string="Journal")
    description = fields.Char(related='voucher_id.description', string="Keperluan")
    partner_id = fields.Many2one('res.partner', related='voucher_id.partner_id', string="Rekanan")
    date = fields.Date(related='voucher_id.date', string='Tanggal')
    total_amount = fields.Monetary(related='voucher_id.total_amount', string='Total')
    type = fields.Selection([("inbound", "Kas Masuk"),
                             ("outbound", "Kas Keluar"),
                             ("internal", "Internal"),
                             ("intercompany", "Intercompany")], related='voucher_id.type', string = "Type")    


