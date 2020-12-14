from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class KaAccountDailyClose(models.Model):
    _name = "ka_account.daily.close" 
    _order = "close_date desc"
    _rec_name = "close_date"
    _inherit = ['mail.thread']
    _description="Tutupan Kas Bank Harian"
    
    @api.one
    @api.depends('statement_ids')
    def _compute_balance(self):
        self.balance_start = sum([line.balance_start for line in self.statement_ids])
        self.balance_end = sum([line.balance_end for line in self.statement_ids])
        self.inbound_total = sum([line.inbound_total for line in self.statement_ids])
        self.outbound_total = sum([line.outbound_total for line in self.statement_ids])
        self.cash_opname = sum([line.balance_end_real for line in self.statement_ids if line.journal_id.type=='cash'])
    
    close_date = fields.Date('Tanggal Tutupan', required=True, default=fields.Date.context_today)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    balance_start = fields.Monetary(string='Saldo Awal', compute = '_compute_balance', store=False)
    inbound_total = fields.Monetary('Kas Masuk', compute='_compute_balance', store=False, help='Total Inbound as calculated based on transaction lines')
    outbound_total = fields.Monetary('Kas Keluar', compute='_compute_balance', store=False, help='Total Outbound as calculated based on Opening Balance and transaction lines')
    balance_end = fields.Monetary('Saldo Akhir', compute='_compute_balance', store=False, help='Balance as calculated based on Opening Balance and transaction lines')
    statement_ids = fields.Many2many('account.bank.statement', 'ka_account_close_statement', 'daily_close_id', 'statement_id', 'Jurnal')
    cash_opname = fields.Monetary('Cash Opname', compute='_compute_balance', store=False)
    state = fields.Selection([('draft', 'draft'), ('validate', 'Validate')], string='Status', required=True, readonly=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', string='PG/Unit', default=lambda self: self.env['res.company']._company_default_get('ka_account.daily.close'))
    report_date = fields.Date('Tanggal Laporan')
    
    def open_cashbox_end(self):
        cash_stm = [stm for stm in self.statement_ids if stm.journal_id.type=='cash']
        if cash_stm:
            return cash_stm[0].open_cashbox_end()
            
            
    def action_get_statement(self):
        statement_ids = self.env['account.bank.statement'].search([('date', '=', self.close_date), ('company_id','=',self.company_id.id)])
        journal_ids = self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))])
        for journal_id in journal_ids:
            statement = self.env['account.bank.statement'].search([('date', '=', self.close_date), ('journal_id', '=', journal_id.id)])
            if not statement:
                vals = {
                    'date': self.close_date,
                    'name': self.close_date.replace('-',''),
                    'journal_id': journal_id.id,
                    'balance_start': statement._get_opening_balance(journal_id.id)
                }
                statement = self.env['account.bank.statement'].create(vals)
                statement_ids += statement
        
        if statement_ids:
            self.statement_ids =  [(6,0,statement_ids._ids)]
        else:
            self.statement_ids = False
        
    def action_validate(self):
        for stm in self.statement_ids:
            if stm.journal_id.type == 'bank':
                stm.balance_end_real = stm.balance_end
            else:
                if stm.balance_end <> stm.balance_end_real:
                    raise UserError('Perkiraan %s Nilai perhitungan Fisik tidak cocok' % stm.journal_id.name)
            stm.check_confirm_bank()
        self.state = 'validate'

    def action_draft(self):
        self.statement_ids.write({'state': 'open'})
        self.state = 'draft'
        
    def action_print(self):
        for stm in self.statement_ids:
            if stm.journal_id.type == 'bank':
                stm.balance_end_real = stm.balance_end
                
        self.report_date = self.close_date
        report = self.env['cash.bank.report'].create({'close_date': self.report_date})
        return report.generate_pdf_cash_bank()