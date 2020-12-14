from odoo import api, fields, models, _
from odoo.exceptions import UserError

class KaAccountSettings(models.Model):
    _name = "ka_account.settings" 
    _description="Setting untuk custom feature yang berkaitan dengan akunting"
    
    
    autopost_rk = fields.Boolean('Auto Post R/K', default=False,
                    help="set TRUE jika ingin mengaktifkan fitur posting otomatis pada unit tujuan R/K. Fitur ini akan berfungsi dengan baik jika bagian TUK sumber R/K mengetahui dan memahami dengan baik perkiraan tujuan R/K")
    autopost_account_voucher = fields.Boolean('Auto Post Bukti Kas R/K', default=False,
                    help="Set TURE jika ingin mengaktifkan fitur posting otomatis pada unit tujuan R/K. Fitur ini dikhususkan pada R/K dengan tujuan kas/bank")
    autopost_account_move = fields.Boolean('Auto Post Jurnal R/K', default=False,
                    help="Set TURE jika ingin mengaktifkan fitur posting otomatis pada unit tujuan R/K. Fitur ini dikhususkan pada R/K dengan tujuan biaya")
    auto_fill_account_invoice_line = fields.Boolean('', default=False,
                    help="Fitur ini digunakan untuk override mengisi secara otomatis nomor perkiraan pada tiap account.invoice.line sesuai dengan tabel kombinasi di bawah")
    invoice_line_account_combination = fields.One2many('setting.invoice.line.account.combination', 'setting_id', 'Combination Line')

    @api.multi
    def open_settings(self):
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>. masuk ini")
        # memo    = self.mapped('account_move_id')
        # action = self.env.ref('ka_account.action_open_memorial_umum').read()[0]
        # if len(memo) > 1:
        #     action['domain'] = [('id', 'in', memo.ids)]

        # elif len(memo) == 1:
        #     action['views'] = [(False, 'form')]
        #     action['res_id'] = memo.ids[0]
            
        # else:
        #     res = self.env.ref('ka_account.action_open_memorial_umum', False)
        #     action['views'] = [(False, 'form')]
        
        # return action


class SettingInvoiceLineAccountCombination(models.Model):
    _name  = "setting.invoice.line.account.combination"

    setting_id = fields.Many2one("ka_account.settings",'Setting')
    order_type = fields.Selection([
        ('rkout', 'SP Untuk Unit'), 
        ('rkin', 'SP Dari Unit'), 
        ('lokal', 'SP Local')
        ], string='Jenis PO', default='rkin')
    product_type = fields.Selection([
        ('consu', 'Consumables'), 
        ('service', 'Service'), 
        ('product', 'Stockable Products')
        ], string='Tipe Produk', default='service')
    analytic_type = fields.Selection([
		('1','Investasi Baru'),#untuk initital G dan B 
		('2','Perbaikan Luar Biasa'),#untuk untial P
		('3','Inventaris'), #untuk initial I
		('4','Penggantian'), #untuk initial G
		('5','Memorandum'), #untuk memorial acuan
		('6','Rutin'), #untuk barang rutin
		('7','Default'), #nilai Default
	], string='Jenis Investasi')
    account_template_id = fields.Many2one("account.account.template", string="Account Template")