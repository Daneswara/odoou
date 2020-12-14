from odoo import api, fields, models, _
from odoo.exceptions import UserError
from pygments.lexer import _inherit
from datetime import datetime
from datetime import timedelta

class ka_general_ledger(models.TransientModel):
    _name = "ka_general.ledger"     
    _template_ledger = 'ka_account.template_laporan_buku_besar'   
    
    name = fields.Char('Name', default='LAPORAN BUKU BESAR')
    account_id = fields.Many2one('account.account', 'Account', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    partner_id = fields.Many2one('res.partner', 'Partner')
    date_from = fields.Date('Date From', default=fields.Date.context_today, required=True)
    date_to = fields.Date('Date To', default=fields.Date.context_today, required=True)
    account_move_line_ids = fields.Many2many('account.move.line', 'general_ledger_move_line_rel', 'ka_general_ledger_id', 'move_line_id', 'Journal Items')
    show_table = fields.Boolean('Show Table')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id.id)
    opening_balance = fields.Monetary('Opening Balance')
    ending_balance = fields.Monetary('Ending Balance')

    
    def get_company(self):
        return self.env.user.company_id.name
    
    @api.multi
    def action_show_general_ledger(self):
        for general_ledger in self.env['ka_general.ledger'].search([('id','!=',self.id)]):
            general_ledger.unlink()
        # check if date from > date to, raise warning
        if self.date_from > self.date_to:
            raise UserError('Date From should be less than or equal to Date To')

        date_from = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from_awal_tahun = date_from.replace(month=1, day=1)
        date_to = datetime.strptime(self.date_to, '%Y-%m-%d')
        if date_from.year != date_to.year:
            raise UserError('Tidak boleh berbeda tahun!')

        # fill table
        domain_src = [('account_id','=',self.account_id.id),
                      ('date','>=',self.date_from),
                      ('date','<=',self.date_to),
                      ('move_id.state','=','posted')]

        if self.analytic_account_id:
            domain_src.append(('analytic_account_id','=',self.analytic_account_id.id))
        if self.partner_id:
            domain_src.append(('partner_id','=',self.partner_id.id))
        if self._context.get('is_cashflow'):
            domain_src.append(('journal_id.type','in',('cash','bank')))
            
        move_line_src = self.env['account.move.line'].search(domain_src, order='date asc')
        self.account_move_line_ids = move_line_src
        # compute starting & ending balance
        start_balance_query = "SELECT sum(ml.balance) FROM account_move_line ml JOIN account_journal aj " \
                              "ON aj.id = ml.journal_id JOIN account_move am ON am.id = ml.move_id " \
                              "WHERE am.state = 'posted' AND ml.account_id = %s AND ml.date < %s AND ml.date >= %s"

        if self.analytic_account_id:
            start_balance_query += (" AND ml.analytic_account_id = " + str(self.analytic_account_id.id))
        if self.partner_id:
            start_balance_query += (" AND ml.partner_id = " + str(self.partner_id.id))
        if self._context.get('is_cashflow'):
            start_balance_query += " AND aj.type in ('cash','bank')"

        # TODO update Rugi Laba
        #special for P/L account
        # if not self.account_id.user_type_id.include_initial_balance:
        #     dateto = datetime.strptime(self.date_to, "%Y-%m-%d") + timedelta(hours=7)
        #     if int(dateto.year) >= 2020:
        #         if not self._context.get('is_cashflow'):
        #             date_from1 = fields.Date.from_string(self.date_from).replace(day=1, month=1)
        #             start_balance_query += (" AND ml.date >= '%s'" % fields.Date.to_string(date_from1))

        self._cr.execute(start_balance_query, (self.account_id.id, self.date_from, date_from_awal_tahun))
        self.opening_balance = self._cr.fetchone()[0]
        self.ending_balance = self.opening_balance + sum(move_line.balance for move_line in move_line_src)
        # check need to show table or not
        if len(self.account_move_line_ids) == 0:
            self.show_table = False
        else:
            self.show_table = True
        return True
    
    @api.multi
    def do_print_general_ledger(self):
        for this in self:
            report_obj = self.env['report']
            template = self._template_ledger
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
        return report_obj.get_action(self, template, data=datas)
    

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def action_show_journal_entry(self):
        view_id = self.env.ref('ka_account.view_move_from_general_ledger').id
        return {
            'name': _('Journal Entry from General Ledger'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.move_id.id,
            }

