from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from calendar import monthrange
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as for_date


class ka_trial_balance_report_wizard(models.TransientModel):
    _name = "ka_trial.balance.report.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(ka_trial_balance_report_wizard, self).default_get(fields)
        # default financial report
        report_src = self.env['account.financial.report'].search([('name','=','NERACA BULANAN')])
        if report_src:
            res['account_report_id'] = report_src.id
        # default date
        year = datetime.now().year
        month = datetime.now().month
        last_day = monthrange(year, month)[1]
        res['date_from'] = datetime.strftime(datetime(year, month, 1), '%Y-%m-%d')
        res['date_to'] = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
        return res
    
    account_report_id = fields.Many2one('account.financial.report', 'Financial Report', required=True)
    date_from = fields.Date('Dari Tanggal', required=True)
    date_to = fields.Date('Sampai Tanggal', required=True)
    file_type = fields.Selection([('pdf','PDF'),('xlsx','Excel')], 'Format File', default='pdf', required=True)
    
    @api.onchange('date_from')
    def onchange_date_from(self):
        if self.date_from:
            date_from = datetime.strptime(self.date_from, '%Y-%m-%d')
            year = date_from.year
            month = date_from.month
            last_day = monthrange(year, month)[1]
            self.date_to = datetime.strftime(datetime(year, month, last_day), '%Y-%m-%d')
    
    @api.multi
    def generate_pdf_trial_balance_report(self):
        if self.date_from > self.date_to:
            raise UserError('Date To should be greater than Date From')
        
        report_obj = self.env['report']
        template = 'ka_account.ka_trial_balance_report_tmpl'
        report = report_obj._get_report_from_name(template)
        domain = {
            'account_report_id': self.account_report_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)

    @api.multi
    def generate_pdf_trial_balance_report_detail(self):
        if self.date_from > self.date_to:
            raise UserError('Date To should be greater than Date From')

        report_obj = self.env['report']
        template = 'ka_account.ka_trial_balance_report_detail_tmpl'
        report = report_obj._get_report_from_name(template)
        domain = {
            'account_report_id': self.account_report_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)
    
    @api.multi
    def generate_xlsx_trial_balance_report(self):
        return self.env['report'].get_action(self, 'trial.balance.xlsx')

    @api.multi
    def generate_xlsx_trial_balance_report_detail(self):
        return self.env['report'].get_action(self, 'trial.balance.xlsx.detail')


class ka_trial_balance_report_qweb(models.AbstractModel):
    _name = 'report.ka_account.ka_trial_balance_report_tmpl'
    _template = 'ka_account.ka_trial_balance_report_tmpl'

    def get_trial_balance_data(self, account_report_id):
        report = self.env['account.financial.report'].search([('parent_id','=',account_report_id)], order='sequence asc')
        if report:
            report = report.filtered(lambda x: len(x.account_ids) != 0)
        
        return report
    
    def get_amount(self, account_id, date_from, date_to):
        # TODO update Rugi Laba
        date_from = datetime.strptime(date_from, for_date)
        date_jan = date_from.replace(month=1, day=1).strftime(for_date)
        # dateto = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(hours=7)
        # if account_id.user_type_id.include_initial_balance or int(dateto.year) < 2020:
        self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            join account_journal journal on move_line.journal_id = journal.id
                            join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date < %s and move_line.date >= %s''', (account_id.id, date_from, date_jan))
        # else:
        #     date_from1 = fields.Date.from_string(date_from).replace(day=1, month=1)
        #     self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
        #                         join account_journal journal on move_line.journal_id = journal.id
        #                         join account_move move on move_line.move_id = move.id
        #                         join account_account account on move_line.account_id = account.id
        #                         where move.state = 'posted' and account_id = %s and move_line.date >= %s and move_line.date < %s''',
        #                         (account_id.id, date_from1, date_from))

        # # TODO update Rugi Laba DELETE
        # self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
        #                                 join account_account account on move_line.account_id = account.id
        #                                 where account_id = %s and date < %s''', (account_id.id, date_from))
        # # Batas delete

        open_balance = self._cr.fetchone()[0] or 0.0
        
        self._cr.execute('''select sum(move_line.debit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            join account_journal journal on move_line.journal_id = journal.id
                            join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s''', (account_id.id, date_from, date_to))
        debit = self._cr.fetchone()[0] or 0.0
        
        self._cr.execute('''select sum(move_line.credit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            join account_journal journal on move_line.journal_id = journal.id
                            join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s''', (account_id.id, date_from, date_to))
        credit = self._cr.fetchone()[0] or 0.0
        
        res = {'open_balance': open_balance,
               'debit': debit,
               'credit': credit,
               'end_balance': open_balance + debit - credit
               }
        return res

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_trial_balance_data': self.get_trial_balance_data,
            'get_amount': self.get_amount,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)


class ka_trial_balance_report_detail_qweb(models.AbstractModel):
    _name = 'report.ka_account.ka_trial_balance_report_detail_tmpl'
    _template = 'ka_account.ka_trial_balance_report_detail_tmpl'

    def get_trial_balance_data(self, account_report_id):
        report = self.env['account.financial.report'].search([('parent_id', '=', account_report_id)],
                                                             order='sequence asc')
        if report:
            report = report.filtered(lambda x: len(x.account_ids) != 0)

        return report

    def get_partner_data(self, account_id, date_from, date_to):
        move_line = self.env['account.move.line'].search([('account_id', '=', account_id.id), ('date','<',date_to), ('date','>=',date_from)])
        if move_line:
            move_line = move_line.filtered(lambda x: x.move_id.state == 'posted')

        move_line.read_group(domain=None, fields='partner_id, account_id', groupby='partner_id')

        # print('batas masuk')
        # print(move_line)
        # print('batas keluar')

        return move_line

    def get_amount(self, account_id, date_from, date_to):
        # TODO update Rugi Laba
        date_from = datetime.strptime(date_from, for_date)
        date_jan = date_from.replace(month=1, day=1).strftime(for_date)
        # dateto = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(hours=7)
        # if account_id.user_type_id.include_initial_balance or int(dateto.year) < 2020:
        self._cr.execute('''select COALESCE(open.kode, debkred.kode) as p_kode, COALESCE(open.a_kode, debkred.a_kode) as a_kode, 
                            COALESCE(open.nama,debkred.nama) as nama, COALESCE(open.a_nama,debkred.a_nama) as a_nama, 
                            COALESCE(open.awal,0.0) as awal, COALESCE(debkred.debet, 0.0) as debet, 
                            COALESCE(debkred.kredit,0.0) as kredit, 
                            (COALESCE(open.awal,0.0) + COALESCE(debkred.debet, 0.0) - COALESCE(debkred.kredit,0.0)) as saldo, open.nomer 
                                from (
                                    select sum(move_line.balance) as awal, partner.name as nama, 
                                    partner.code as kode, partner.id as id, 
                                    analytic.id as aid, analytic.code as a_kode, analytic.name as a_nama, 
                                    CONCAT('P',partner.id,'A',analytic.id) as nomer 
                                    from account_move_line move_line
                                    join account_account account on move_line.account_id = account.id 
                                    join account_journal journal on move_line.journal_id = journal.id 
                                    join account_move move on move_line.move_id = move.id 
                                    left join res_partner partner on move_line.partner_id = partner.id
                                    left join account_analytic_account analytic on move_line.analytic_account_id = analytic.id
                                    where move.state = 'posted' and move_line.account_id = %s and 
                                    move_line.date < %s and move_line.date >= %s group by partner.id, analytic.id) 
                                    as open
                                full outer join (
                                    select sum(move_line.credit) as kredit, sum(move_line.debit) as debet, 
                                    partner.name as nama, partner.code as kode, partner.id as id, 
                                    analytic.id as aid, analytic.code as a_kode, analytic.name as a_nama, 
                                    CONCAT('P',partner.id,'A',analytic.id) as nomer 
                                    from account_move_line move_line
                                    join account_account account on move_line.account_id = account.id
                                    join account_journal journal on move_line.journal_id = journal.id
                                    join account_move move on move_line.move_id = move.id
                                    left join res_partner partner on move_line.partner_id = partner.id
                                    left join account_analytic_account analytic on move_line.analytic_account_id = analytic.id
                                    where move.state = 'posted' and move_line.account_id = %s and 
                                    move_line.date <= %s and move_line.date >= %s 
                                    group by partner.id, analytic.id) 
                                    as debkred
                                on open.nomer = debkred.nomer order by p_kode, a_kode''',
                         (account_id.id, date_from, date_jan, account_id.id, date_to, date_from))

        open_balance = self._cr.fetchall() or 0.0

        res = {'open_balance': open_balance,}
        return res

    def get_amount_perkiraan(self, account_id, date_from, date_to):
        # TODO update Rugi Laba
        date_from = datetime.strptime(date_from, for_date)
        date_jan = date_from.replace(month=1, day=1).strftime(for_date)
        # dateto = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(hours=7)
        # if account_id.user_type_id.include_initial_balance or int(dateto.year) < 2020:
        self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            join account_journal journal on move_line.journal_id = journal.id
                            join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date < %s and move_line.date >= %s''',
                         (account_id.id, date_from, date_jan))
        # else:
        #     date_from1 = fields.Date.from_string(date_from).replace(day=1, month=1)
        #     self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
        #                         join account_journal journal on move_line.journal_id = journal.id
        #                         join account_move move on move_line.move_id = move.id
        #                         join account_account account on move_line.account_id = account.id
        #                         where move.state = 'posted' and account_id = %s and move_line.date >= %s and move_line.date < %s''',
        #                         (account_id.id, date_from1, date_from))

        # # TODO update Rugi Laba DELETE
        # self._cr.execute('''select sum(move_line.balance) from account_move_line move_line
        #                                 join account_account account on move_line.account_id = account.id
        #                                 where account_id = %s and date < %s''', (account_id.id, date_from))
        # # Batas delete

        open_balance = self._cr.fetchone()[0] or 0.0

        self._cr.execute('''select sum(move_line.debit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            join account_journal journal on move_line.journal_id = journal.id
                            join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s''',
                         (account_id.id, date_from, date_to))
        debit = self._cr.fetchone()[0] or 0.0

        self._cr.execute('''select sum(move_line.credit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            join account_journal journal on move_line.journal_id = journal.id
                            join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s''',
                         (account_id.id, date_from, date_to))
        credit = self._cr.fetchone()[0] or 0.0

        res = {'open_balance': open_balance,
               'debit': debit,
               'credit': credit,
               'end_balance': open_balance + debit - credit
               }
        return res

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_trial_balance_data': self.get_trial_balance_data,
            'get_amount': self.get_amount,
            'get_amount_perkiraan': self.get_amount_perkiraan,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)

