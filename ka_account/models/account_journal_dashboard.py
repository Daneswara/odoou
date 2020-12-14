from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
import time
# from datetime import datetime as dt
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from datetime import datetime, timedelta

class ka_account_journal(models.Model):
	_inherit = 'account.journal'

	@api.multi
	def action_bank_masuk(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'bank', 'type': 'inbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'inbound')],
		}

	@api.multi
	def action_bank_keluar(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'bank', 'type': 'outbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'outbound')],
		}

	@api.multi
	def action_cash_masuk(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'cash', 'type': 'inbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'inbound')],
		}

	@api.multi
	def action_cash_keluar(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'cash', 'type': 'outbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'outbound')],
		}

	@api.multi
	def get_journal_dashboard_datas(self):
		date_obj = datetime.strptime(fields.Date.today(), DATE_FORMAT)
		date_jan_obj = date_obj.replace(month=1, day=1)
		date_jan = date_jan_obj.strftime(DATE_FORMAT)

		currency = self.currency_id or self.company_id.currency_id
		number_to_reconcile = last_balance = account_sum = 0
		ac_bnk_stmt = []
		title = ''
		number_draft = number_waiting = number_late = 0
		sum_draft = sum_waiting = sum_late = 0.0
		if self.type in ['bank', 'cash']:
			last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids)],
																	   order="date desc, id desc", limit=1)
			last_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0
			# Get the number of items to reconcile for that bank journal
			self.env.cr.execute("""SELECT COUNT(DISTINCT(statement_line_id)) 
	                        FROM account_move where statement_line_id 
	                        IN (SELECT line.id 
	                            FROM account_bank_statement_line AS line 
	                            LEFT JOIN account_bank_statement AS st 
	                            ON line.statement_id = st.id 
	                            WHERE st.journal_id IN %s and st.state = 'open')""", (tuple(self.ids),))
			already_reconciled = self.env.cr.fetchone()[0]
			self.env.cr.execute("""SELECT COUNT(line.id) 
	                            FROM account_bank_statement_line AS line 
	                            LEFT JOIN account_bank_statement AS st 
	                            ON line.statement_id = st.id 
	                            WHERE st.journal_id IN %s and st.state = 'open'""", (tuple(self.ids),))
			all_lines = self.env.cr.fetchone()[0]
			number_to_reconcile = all_lines - already_reconciled
			# optimization to read sum of balance from account_move_line
			account_ids = tuple(filter(None, [self.default_debit_account_id.id, self.default_credit_account_id.id]))
			if account_ids:
				amount_field = 'balance' if (
						not self.currency_id or self.currency_id == self.company_id.currency_id) else 'amount_currency'
				query = """SELECT sum(%s) FROM account_move_line move_line join account_move move on move_line.move_id = move.id 
				WHERE account_id in %%s AND move_line.date <= %%s AND move_line.date >= %%s AND move.state = 'posted';""" % (
				amount_field,)
				self.env.cr.execute(query, (account_ids, fields.Date.today(),date_jan))
				query_results = self.env.cr.dictfetchall()
				if query_results and query_results[0].get('sum') != None:
					account_sum = query_results[0].get('sum')
					print("----------------------------------------------------------------")
					print(account_sum)
		# TODO need to check if all invoices are in the same currency than the journal!!!!
		elif self.type in ['sale', 'purchase']:
			title = _('Bills to pay') if self.type == 'purchase' else _('Invoices owed to you')
			# optimization to find total and sum of invoice that are in draft, open state
			query = """SELECT state, amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND state NOT IN ('paid', 'cancel');"""
			self.env.cr.execute(query, (self.id,))
			query_results = self.env.cr.dictfetchall()
			today = datetime.today()
			query = """SELECT amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND date < %s AND state = 'open';"""
			self.env.cr.execute(query, (self.id, today))
			late_query_results = self.env.cr.dictfetchall()
			for result in query_results:
				if result['type'] in ['in_refund', 'out_refund']:
					factor = -1
				else:
					factor = 1
				cur = self.env['res.currency'].browse(result.get('currency'))
				if result.get('state') in ['draft', 'proforma', 'proforma2']:
					number_draft += 1
					sum_draft += cur.compute(result.get('amount_total'), currency) * factor
				elif result.get('state') == 'open':
					number_waiting += 1
					sum_waiting += cur.compute(result.get('amount_total'), currency) * factor
			for result in late_query_results:
				if result['type'] in ['in_refund', 'out_refund']:
					factor = -1
				else:
					factor = 1
				cur = self.env['res.currency'].browse(result.get('currency'))
				number_late += 1
				sum_late += cur.compute(result.get('amount_total'), currency) * factor

		difference = currency.round(last_balance - account_sum) + 0.0
		return {
			'number_to_reconcile': number_to_reconcile,
			'account_balance': formatLang(self.env, currency.round(account_sum) + 0.0, currency_obj=currency),
			'last_balance': formatLang(self.env, currency.round(last_balance) + 0.0, currency_obj=currency),
			'difference': formatLang(self.env, difference, currency_obj=currency) if difference else False,
			'number_draft': number_draft,
			'number_waiting': number_waiting,
			'number_late': number_late,
			'sum_draft': formatLang(self.env, currency.round(sum_draft) + 0.0, currency_obj=currency),
			'sum_waiting': formatLang(self.env, currency.round(sum_waiting) + 0.0, currency_obj=currency),
			'sum_late': formatLang(self.env, currency.round(sum_late) + 0.0, currency_obj=currency),
			'currency_id': currency.id,
			'bank_statements_source': self.bank_statements_source,
			'title': title,
		}