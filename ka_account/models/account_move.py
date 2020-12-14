import json
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class AccountMove(models.Model):
	_name = 'account.move'
	_inherit = ["account.move","ir.needaction_mixin"]
	_order = "name asc"

	statement_line_id = fields.Many2one('account.bank.statement.line', index=True, string='Bank statement line reconciled with this entry', copy=False, readonly=False)
	is_rk = fields.Boolean("is R/K")
	src_account_voucher = fields.Many2one("ka_account.voucher", string="Bukti Kas Sumber")

	@api.model
	@api.multi
	def get_year(self):
		self._cr.execute("""
			select date_part('year', date), count(*)
			from account_move
			group by date_part('year', date)
			order by date_part('year', date) DESC LIMIT 10
		""")
		years = self._cr.fetchall()
		year = [int(y[0]) for y in years]
		return json.dumps(year, ensure_ascii=False)

	@api.multi
	def post(self):
		super(AccountMove,self).post()
		for this in self:
			account_type_unpostable = self.env.ref('ka_account.data_account_type_unpostable').id
			line_unpostable_src = self.env['account.move.line'].search([('move_id','=',this.id),('account_id.user_type_id','=',account_type_unpostable)])
			if line_unpostable_src:
				raise UserError('Sorry, you cannot post account with type = Un-Postable.')

			if not self._context.get('no_check_periodic'):
				internal_user_id = self.env.user.company_id.internal_user_id.id
				account_periodic_ids = [account.account_src_id.id for account in self.env['ka_account.account.periodic'].sudo(internal_user_id).search([])]
				if account_periodic_ids:
					account_move_line_src = self.env['account.move.line'].sudo(internal_user_id).search([('move_id','=',this.id),('account_id','in',account_periodic_ids)])
					for move_line in account_move_line_src:
						amount = move_line.credit
						if move_line.debit > 0:
							amount = move_line.debit
						new_account_debit_id = new_account_credit_id = False
						account_periodic_id = self.env['ka_account.account.periodic'].sudo(internal_user_id).search([('account_src_id','=',move_line.account_id.id)],limit=1)
						if move_line.debit > 0:
							new_account_credit_id = account_periodic_id.account_src_id.id
							new_account_debit_id = account_periodic_id.account_dest_id.id
						else:
							new_account_credit_id = account_periodic_id.account_dest_id.id
							new_account_debit_id = account_periodic_id.account_src_id.id

						# create journal entry and journal items periodic
						move_name = self.env['ir.sequence'].next_by_code("ka_account.move.periodic")
						move_date = datetime.strptime(this.date, '%Y-%m-%d')
						date_planned = datetime(move_date.year + 1, move_date.month, move_date.day)
						if move_date.month == 2 and move_date.day == 29:
							date_planned = datetime(move_date.year + 1, 02, 28)
						date_planned = datetime.strftime(date_planned, '%Y-%m-%d')
						debit_line  = (0,0,{'name': move_line.name,
										  	'account_id': new_account_debit_id,
										  	'partner_id': move_line.partner_id.id or False,
										  	'analytic_account_id': move_line.analytic_account_id.id or False,
										  	'debit': amount})
						credit_line = (0,0,{'name': move_line.name,
									   		'account_id': new_account_credit_id,
									   		'partner_id': move_line.partner_id.id or False,
									   		'analytic_account_id': move_line.analytic_account_id.id or False,
									   		'credit': amount})
						self.env['ka_account.move.periodic'].sudo(internal_user_id).create({'name': move_name,
																	 						'journal_id': this.journal_id.id,
																	 						'date_planned': date_planned,
																	 						'account_periodic_id': account_periodic_id.id,
																	 						'move_src_id': this.id,
																	 						'move_line_periodic_ids': [debit_line,credit_line]})

	def cetak_bukti_memorial(self):
		report_obj = self.env['report']
		template = 'ka_account.report_bukti_memo'
		report = report_obj._get_report_from_name(template)
		domain = {}
		vals = {
			'ids': self.ids,
			'model':report.model,
			'form':domain
		}

		return report_obj.get_action(self, template, data=vals)

	@api.model
	def _needaction_domain_get(self):
		return [('src_account_voucher','!=',False),('is_rk','=',True),('state','=','draft')]

class ReportBuktiMemorial(models.AbstractModel):
	_name = 'report.ka_account.report_bukti_memo'
	_template = 'ka_account.report_bukti_memo'

	@api.multi
	def render_html(self, docids, data=None):
		report_obj = self.env['report']
		model = self.env.context.get('active_model')
		docs = self.env[model].browse(data['ids'])
		docargs = {
			'data': data['form'],
			'doc_ids': self.ids,
			'doc_model': model,
			'docs': docs,
		}
		print docargs

		return report_obj.render(self._template, values=docargs)



class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	account_template_id = fields.Many2one(related="account_id.account_template_id", readonly=True, store=True)
	reconcile_invoice_id = fields.Many2one('account.invoice', 'Related Invoice for Reconciliation', help='The journal items of this invoice will be reconciled with this journal item')
	report_id = fields.Many2one('account.financial.report', 'Report', help='Manual mapping on cashflow report', domain=[('is_cashflow','=',True),('type','=','manual_mapping')])

	@api.multi
	def write(self, vals):
		res = super(AccountMoveLine,self).write(vals)
		if 'debit' in vals or 'credit' in vals:
			for this in self:
				if this.move_id.statement_line_id and this.journal_id.type in ('cash','bank') and this.account_id.id == this.journal_id.default_debit_account_id.id:
					this.move_id.statement_line_id.write({'amount': this.balance})
		return res
