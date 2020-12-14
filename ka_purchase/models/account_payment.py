from odoo import models, fields, api, _
import urllib2
from datetime import datetime
from odoo.exceptions import UserError
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang

class account_payment(models.Model):
    _inherit = "account.payment"        
    
    state = fields.Selection([('draft', 'Draft'), 
                              ('proposed', 'Proposed'),
                              ('confirm', 'Confirmed'),
                              ('posted', 'Posted'), 
                              ('sent', 'Sent'), 
                              ('reconciled', 'Reconciled')], 
                             readonly=True, default='draft', copy=False, string="Status")
    invoice_id = fields.Many2one('account.invoice', 'No. NTB/ Invoice')
    no_kwitansi = fields.Char('No. Kwitansi')
    vendor_invoice_date = fields.Date('Tanggal Kwitansi')
    efaktur_url = fields.Char('URL Barcode')
    tax_number = fields.Char('Nomor Faktur')
    tax_date = fields.Date('Tanggal Faktur')
    amount_dpp = fields.Monetary('DPP')
    amount_ppn = fields.Monetary('PPn')
    amount_invoice = fields.Monetary('Total')
    pph = fields.Boolean('PPh')
    amount_penalty = fields.Monetary('Denda')
    account_payment_confirm_id = fields.Many2one('account.payment.confirm', 'Confirmed Payment')
    is_full_confirm = fields.Boolean('Fully Confirmed')
    is_purchase_payment = fields.Boolean('Purchase Payment')
    
    @api.model
    def default_get(self, fields):
        res = super(account_payment, self).default_get(fields)
        if self._context.get('default_is_purchase_payment',False) == True:
            company_obj = self.env.user.company_id.id
            for journal in self.env['account.journal'].search([('type','=','bank'),('company_id','=',company_obj)]):
                res['journal_id'] = journal.id
        return res
    
    @api.multi
    def propose_payment(self):
        for rec in self:
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
            rec.state = 'proposed'
        return True
    
    @api.multi
    def set_draft_payment(self):
        for rec in self:
            rec.name = 'Draft Payment'
            rec.state = 'draft'
        return True
    
    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id.id
            self.amount = self.invoice_id.amount_untaxed
            self.amount_penalty = self.invoice_id.amount_penalty
            self.amount_tax = self.invoice_id.amount_tax
    
    def find_between( self,s, first, last ):
        try:
            start = s.index( first ) + len( first )
            end = s.index( last, start )
            return s[start:end]
        except ValueError:
            return ""

    @api.onchange('efaktur_url')
    def _onchange_url(self):
        if not self.efaktur_url or self.efaktur_url == '' or self.efaktur_url[0:7] != 'http://':
            self.tax_number = ''
            self.tax_date = ''
            self.amount_dpp = ''
            self.amount_ppn = ''
            return

        self.result = ''

        try:
            urllib2.urlopen(self.efaktur_url)
        except urllib2.HTTPError as err:
            if err.code == 404:
                self.tax_number = ''
                self.tax_date = ''
                self.amount_dpp = ''
                self.amount_ppn = ''
                return
            else:
                raise

        self.result = urllib2.urlopen(self.efaktur_url).read()

        if self.result == '' or not self.result:
            return

        self.tax_number = self.find_between(self.result,"<nomorFaktur>","</nomorFaktur>")
        self.tax_date = datetime.strftime(datetime.strptime(self.find_between(self.result,"<tanggalFaktur>","</tanggalFaktur>"), "%d/%m/%Y"), "%Y-%m-%d")
        self.amount_dpp = float(self.find_between(self.result,"<jumlahDpp>","</jumlahDpp>"))
        self.amount_ppn = float(self.find_between(self.result,"<jumlahPpn>","</jumlahPpn>"))
        self.amount_invoice = self.amount_dpp + self.amount_ppn
        
    @api.multi
    def delete_payment_relation(self):
        for rec in self:
            rec.write({'account_payment_confirm_id': False, 'is_full_confirm': False, 'state': 'proposed'})
        return True
    
    def get_payment_history(self):
        res = self.env['account.payment'].search([('invoice_id','=',self.invoice_id.id),('state','=','confirm')], order='payment_date desc')
        return res

class account_payment_confirm(models.Model):
    _name = "account.payment.confirm"  
    
    @api.depends('account_payment_ids.amount', 'account_payment_ids.amount_ppn', 'account_payment_ids.amount_penalty')
    def compute_amount(self):
        for rec in self:
            total_amount_untaxed = 0.0
            total_ppn = 0.0
            total_penalty = 0.0
            for payment in rec.account_payment_ids:
                total_amount_untaxed += payment.amount
                total_ppn += payment.amount_ppn
                total_penalty += payment.amount_penalty
            rec.total_amount_untaxed = total_amount_untaxed
            rec.total_ppn = total_ppn
            rec.total_penalty = total_penalty
            rec.amount_total = rec.total_amount_untaxed + rec.total_ppn + rec.total_penalty
    
    name = fields.Char('Name')
    confirm_date = fields.Datetime('Confirm Date')
    state = fields.Selection([('draft', 'Draft'),('confirm', 'Confirmed')], string='State', default='draft')
    account_payment_ids = fields.One2many('account.payment', 'account_payment_confirm_id', 'Payments')  
    currency_id = fields.Many2one('res.currency', 'Currency')
    total_amount_untaxed = fields.Monetary('Untaxed Amount', compute='compute_amount')
    total_ppn = fields.Monetary('Total PPN', compute='compute_amount')
    total_penalty = fields.Monetary('Total Penalty', compute='compute_amount')
    amount_total = fields.Monetary('Total Amount', compute='compute_amount')
    
    @api.multi
    def action_confirm(self):
        for rec in self:
            for payment in rec.account_payment_ids:
                payment.write({'is_full_confirm': True})
            rec.write({'confirm_date': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'state': 'confirm'})
        return True
    
    @api.multi
    def action_set_draft(self):
        for rec in self:
            for payment in rec.account_payment_ids:
                payment.write({'is_full_confirm': False})
            rec.write({'state': 'draft'})
        return True
    
    @api.multi
    def unlink(self):
        if self.state == 'confirm':
            raise UserError('Sorry, you can not delete confirmed payments. Please set to draft first.')
        return super(account_payment_confirm, self).unlink()
    
    @api.multi
    def get_partners(self):
        partner_array = []
        for this in self:
            payment_obj = this.account_payment_ids
            for payment in payment_obj:
                if payment.partner_id not in partner_array:
                    partner_array.append(payment.partner_id)
        return partner_array
    
    @api.multi
    def get_payments(self,partner):
        payment_array = []
        for this in self:
            payment_obj = this.account_payment_ids
            for payment in payment_obj:
                if payment.partner_id.id == partner.id:
                    payment_array.append(payment)
        return payment_array
    
            
    def amount_to_text_id(self, amount):
        return Terbilang(amount) + " Rupiah"
        