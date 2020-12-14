# -*- coding: utf-8 -*-
"""
 * Copyright Cak Juice 2016
 * untuk Nerita - Kebon Agung..
 * Gaween sakkarepmu..
"""

import time, datetime, calendar
from odoo import api, models
from operator import itemgetter
from datetime import datetime as dt
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

global_account_report_custom = []
long_cmonth = ['DESEMBER', 'JANUARI', 'FEBRUARI', 'MARET', 'APRIL', 'MEI', 'JUNI', 'JULI', 'AGUSTUS', 'SEPTEMBER',
               'OKTOBER', 'NOVEMBER', 'DESEMBER']
short_cmonth = ['TAHUN', 'JAN', 'FEB', 'MART', 'APRL', 'MEI', 'JUN', 'JUL', 'AGU', 'SEP', 'OKT', 'NOV', 'DES']


class BaseReportFinancialCustom(models.AbstractModel):
    _name = 'base_report_financial_custom'

    _report_name = None
    _report_vals = None

    def _compute_account_balance(self, accounts, cashflow_type=None):
        """ compute the balance, debit and credit for the provided accounts
        """

        date_obj = dt.strptime(self._context.get('date_from', False),DATE_FORMAT)
        date_to_obj = dt.strptime(self._context.get('date_to', False),DATE_FORMAT)
        # if date_obj.month == 1:
        #     date_obj = date_obj - timedelta(days=1)
        date_jan_obj = date_obj.replace(month=1,day=1)
        date_jan = date_jan_obj.strftime(DATE_FORMAT)

        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        if date_to_obj.month == 1:
            sql_cashflow = """(
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            to_date('{1}', 'YYYY-MM-DD') AS date, 
                            SUM(debit) AS debit, sum(credit) AS credit,
                            'ob' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id  
                            WHERE move_line.date >= '{0}' AND move_line.date < '{1}' AND move.state = 'posted' 
                            AND move.closing_fiscal_year_id is not null
                            AND journal.type in ('cash','bank') 
                            GROUP BY 1, 2, 3, 4
                        UNION ALL
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            move_line.date, 
                            sum(debit) as credit, sum(credit) as debit,
                            'in' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id
                            WHERE move_line.date >='{1}' AND move_line.date <= '{2}' AND move.state = 'posted' 
                            AND move.closing_fiscal_year_id is null
                            AND journal.type in ('cash','bank') 
                            GROUP BY  1, 2, 3, 4
                        UNION ALL
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            move_line.date, 
                            SUM(debit) AS credit, SUM(credit) AS debit,
                            'out' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id 
                            WHERE move_line.date >= '{1}' AND move_line.date <= '{2}' AND move.state = 'posted' 
                            AND move.closing_fiscal_year_id is null
                            AND journal.type in ('cash','bank')
                            GROUP BY  1, 2, 3, 4
                        UNION ALL
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            to_date('{1}', 'YYYY-MM-DD') AS date, 
                            SUM(debit) AS debit, sum(credit) AS credit,
                            'bl' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id
                            WHERE move_line.date >= '{0}' AND move_line.date <= '{2}' AND move.state = 'posted'
                            AND journal.type in ('cash','bank')
                            GROUP BY  1, 2, 3, 4) as cashflow""".format(date_jan, self._context.get('date_from', False),
                                                                        self._context.get('date_to', False))
        else:
            sql_cashflow = """(
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            to_date('{1}', 'YYYY-MM-DD') AS date, 
                            SUM(debit) AS debit, sum(credit) AS credit,
                            'ob' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id  
                            WHERE move_line.date >= '{0}' AND move_line.date < '{1}' AND move.state = 'posted' 
                            AND journal.type in ('cash','bank') 
                            GROUP BY 1, 2, 3, 4
                        UNION ALL
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            move_line.date, 
                            sum(debit) as credit, sum(credit) as debit,
                            'in' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id
                            WHERE move_line.date >='{1}' AND move_line.date <= '{2}' AND move.state = 'posted' 
                            AND journal.type in ('cash','bank') 
                            GROUP BY  1, 2, 3, 4
                        UNION ALL
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            move_line.date, 
                            SUM(debit) AS credit, SUM(credit) AS debit,
                            'out' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id 
                            WHERE move_line.date >= '{1}' AND move_line.date <= '{2}' AND move.state = 'posted' 
                            AND journal.type in ('cash','bank')
                            GROUP BY  1, 2, 3, 4
                        UNION ALL
                        SELECT  move_line.company_id,
                            move_line.journal_id,
                            account_id, 
                            to_date('{1}', 'YYYY-MM-DD') AS date, 
                            SUM(debit) AS debit, sum(credit) AS credit,
                            'bl' AS type
                            FROM account_move_line as move_line
                            JOIN account_move as move
                            ON move_line.move_id = move.id
                            JOIN account_journal as journal
                            ON move_line.journal_id = journal.id
                            WHERE move_line.date >= '{0}' AND move_line.date <= '{2}' AND move.state = 'posted'
                            AND journal.type in ('cash','bank')
                            GROUP BY  1, 2, 3, 4) as cashflow""".format(date_jan, self._context.get('date_from', False),
                                                                        self._context.get('date_to', False))
        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line "
            tables = tables + " JOIN account_move as move ON move_id = move.id"
            report_cashflow = self._context.get('financial_report_type', False) == 'cashflow'
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)

            # spesific for cashflow report
            if report_cashflow:
                tables = sql_cashflow
                if cashflow_type:
                    filters = filters + " AND type = '%s' " % cashflow_type
                filters = filters.replace('account_move_line', 'cashflow')
            else:
                filters = filters + " AND move.state = 'posted' "

            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            
            params = (tuple(accounts._ids),) + tuple(where_params)
        
            self.env.cr.execute(request, params)

            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
                
        return res

    def _compute_manual_mapping(self, report_id, accounts):
        date_from = self._context.get('date_from', False)
        date_to = self._context.get('date_to', False)

        date_obj = dt.strptime(self._context.get('date_from', False),DATE_FORMAT)
        if date_obj.month == 1:
            date_obj = date_obj - timedelta(days=1)
        date_jan_obj = date_obj.replace(month=1,day=1)
        date_jan = date_jan_obj.strftime(DATE_FORMAT)

        query = """
                SELECT account_id as id, 
                COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance, 
                COALESCE(SUM(debit), 0) as debit,
                COALESCE(SUM(credit), 0) as credit
                FROM (
                    SELECT move_line.company_id,
                        move_line.journal_id,
                        move_line.report_id,
                        account_id, 
                        sum(debit) AS debit, sum(credit) AS credit
                        FROM account_move_line as move_line
                        JOIN account_journal as journal 
                        ON move_line.journal_id = journal.id
                        JOIN account_move as move
                        ON move_line.move_id = move.id
                        WHERE (move_line.date >= %s AND move_line.date <= %s)
                        AND move.state = 'posted' AND journal.type in ('cash','bank')
                        GROUP BY 1,2,3,4 ORDER BY account_id ASC
                ) as cashflow
                WHERE cashflow.report_id = %s AND cashflow.account_id in %s
                GROUP BY account_id
        """

        res = {}

        params = (date_from, date_to ,report_id,tuple(accounts))

        self.env.cr.execute(query,params)

        for row in self.env.cr.dictfetchall():
            res[row['id']] = row

        return res

    def _compute_report_balance(self, reports):
        # returns a dictionary with key = the ID of a record and value = the credit, debit and balance amount
        # computed for this record. If the record is of type :
        # 'accounts' : it's the sum of the linked accounts
        # 'account_type' : it's the sum of leaf accoutns with such an account_type
        # 'account_report' : it's the amount of the related report
        # 'sum' : it's the sum of the children of this record (aka a 'view' record)
        res = {}
        fields = ['credit', 'debit', 'balance']
        
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':                
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, report.cashflow_type)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts, report.cashflow_type)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'manual_mapping':
                # it's the sum move_line with manual mapping on report_id
                mapped_accounts =  self.env['ka_account.cashflow.account.mapping'].search([])
                account_ids = [line.account_id.id for line in mapped_accounts]

                res[report.id]['account'] = self._compute_manual_mapping(report.id,account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)


        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        # filtered_child_reports = child_reports.filtered(lambda x: len(x.account_ids) !=0 or x.type != 'accounts')
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'company_id': self._context.get('company_id', False),
                'sequence': report.sequence,
                'name': report.name,
                'id': report.id,
                'balance': res[report.id]['balance'] * report.sign,
                # 'type': 'report',
                'type': report.type,
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False,  # used to underline the financial report balances
                'display_value': report.display_value,
            }

            if report.is_cashflow:
                vals['cashflow_type'] = report.cashflow_type

            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    # if there are accounts to display, we add them to the lines with a level equals to their level in
                    # the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    # financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'company_id': self.env.user.company_id.id,
                        'sequence': report.sequence,
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    def _get_periode(self, month, year):
        date_from = None
        date_to = None
        m = month
        y = year

        if m == 0:
            date_from = datetime.date(y, 1, 1)
            date_to = datetime.date(y, 12, calendar.monthrange(y, 12)[1])
        else:
            date_from = datetime.date(y, m, 1)
            date_to = datetime.date(y, m, calendar.monthrange(y, m)[1])

        return (date_from, date_to)

    def _generate_pivot_data(self, data):
        ldata = len(data)
        idx = 0
        res = []
        while idx < ldata:
            row = data[idx]
            key = row['sequence']
            last_key = key
            col_values = []
            while last_key == key:
                balance = data[idx]['balance']
                col_values.append(balance)
                idx = idx + 1
                if idx == ldata:
                    break
                key = data[idx]['sequence']
            del row['company_id']
            # # ubah urutan col_values yaa
            # col_values_back = []
            # l = len(col_values)
            # for x in range(l):
            #     col_values_back.append(col_values.pop())
            row['values'] = col_values
            res.append(row)
        return res

    # def _generate_pivot_data(self, data, total=True):
    #     ldata = len(data)
    #     idx = 0
    #     res = []
    #     while idx < ldata:
    #         row = data[idx]
    #         key = row['sequence']
    #         last_key = key
    #         col = 0
    #         total_balance = 0
    #         while last_key == key:
    #             col = col + 1
    #             balance = data[idx]['balance']
    #             total_balance = total_balance + balance
    #             row['balance_%s' % col] = balance
    #             idx = idx + 1
    #             if idx == ldata:
    #                 break
    #             key = data[idx]['sequence']
    #         del row['company_id']
    #         row['balance'] = total_balance if total else balance
    #         res.append(row)
    #     return res

    def _prepare_report_data(self, report_type, report_id, date_from, date_to, company_ids):
        docs = []
        if report_type == 'cashflow':
            journal_ids = [j.id for j in self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))])]
        else:
            journal_ids = [j.id for j in self.env['account.journal'].search([])]

        for c in self.env['res.company'].browse(map(int, company_ids)):
            user_id = c.get_internal_user()
            wizard = self.env['accounting.report']
            rec = wizard.sudo(user_id).create({
                'enable_filter': False,
                'account_report_id': report_id,
                'debit_credit': False,
                'date_from': date_from,
                'date_to': date_to,
                'target_move': 'all',
                'journal_ids': [(4, [journal_ids])],
            })

            report = rec.sudo(user_id).check_report()
            report_company_id = 99 if c.id == 1 else c.id
            report['data']['form']['used_context']['financial_report_type'] = report_type
            doc = self.sudo(user_id).with_context({'company_id': report_company_id}).get_account_lines(
                report['data']['form'])
            docs = docs + doc
        return rec, report, docs

    def _get_opening_balance(self, report_type, report_id, date_from, company_ids):
        from_date = None
        to_date = date_from - datetime.timedelta(days=1)  # last day of prev month
        if report_type == 'profitloss':
            from_date = to_date.replace(day=1)
        return self._prepare_report_data(report_type, report_id, from_date, to_date, company_ids)

    def _get_report_balance(self, report_type, report_id, from_date, date_to, company_ids):
        return self._prepare_report_data(report_type, report_id, from_date, date_to, company_ids)

    def _get_periode_balance(self, report_type, report_id, date_from, date_to, company_ids):
        return self._prepare_report_data(report_type, report_id, date_from, date_to, company_ids)

    @api.model
    def get_financial_report(self, model_name, report_type, report_id, month, year, company):
        # 0 -> Consolidation
        # 1 -> Main company

        report_data = []
        if company == 0:
            companies = self.env['res.company'].search([])
        else:
            companies = self.env['res.company'].browse(company)
        
        company_ids = [c.id for c in companies]
        company_names = [c.name for c in companies]
        cname = company_names[0] if len(company_names) == 1 else 'KONSOLIDASI'

        if report_type == 'profitloss':
            # tahunan
            if month == 0:
                date_from1, date_to1 = self._get_periode(month, year - 1)
                date_from2, date_to2 = self._get_periode(month, year)
                # if date_to1.year < 2020:
                # date_from1 = date_from2.replace(year=2010)
                # if date_to2.year < 2020:
                # date_from2 = date_from2.replace(year=2010)

                col_header = [year, year - 1]
                report_header = "TAHUN %d" % (year)
            # bulanan
            else:
                date_from1, date_to1 = self._get_periode(month - 1, year)
                if month == 1:
                    date_from1, date_to1 = self._get_periode(12, year - 1)
                date_from2, date_to2 = self._get_periode(month, year)
                # date_from3 = date_from2.replace(month=1)
                # if year < 2020:
                date_from3 = date_from2.replace(year=year, month=1)

                date_to3 = date_to2
                col_header = [
                    long_cmonth[month],
                    long_cmonth[month - 1] if month > 1 else "%s %d" % (long_cmonth[month - 1], year - 1),
                    "S/D %s" % long_cmonth[month]
                ]
                report_header = "BULAN %s %d" % (long_cmonth[month], year)

            # single unit
            if len(company_ids) == 1:
                # P/L perioder ini
                rec, form, data2 = self._get_report_balance(report_type, report_id, date_from2, date_to2, company_ids)
                report_data = report_data + data2
                # P/L periode sebelumnya
                rec, form, data1 = self._get_report_balance(report_type, report_id, date_from1, date_to1, company_ids)
                report_data = report_data + data1
                # P/L Jan s/d periode ini
                if month > 0:
                    if month == 1:
                        data3 = data2
                        report_data = report_data + data3
                    else:
                        rec, form, data3 = self._get_report_balance(report_type, report_id, date_from3, date_to3,
                                                                    company_ids)
                        report_data = report_data + data3

            # gabungan/konsolidasi
            else:
                rec, form, report_data = self._get_report_balance(report_type, report_id, date_from2, date_to2,
                                                                  company_ids)
                col_header = ['KANTOR DIREKSI', 'PG KEBON AGUNG', 'PG TRANGKIL', 'PT KEBON AGUNG']

            report_data = sorted(report_data, key=itemgetter('sequence', 'company_id'))
            pivot = self._generate_pivot_data(report_data)

        if report_type in ('balancesheet_horizontal', 'balancesheet_vertical', 'arus_kas'):
            # tahunan
            if month == 0:
                date_from1, date_to1 = self._get_periode(month, year - 1)
                date_from2, date_to2 = self._get_periode(month, year)
                date_from1 = date_from1.replace(month=1)
                date_from2 = date_from2.replace(month=1)
                col_header = [year, year - 1]
                report_header = "S/D TAHUN %d" % (year)
            # bulanan
            else:
                date_from1, date_to1 = self._get_periode(month - 1, year)
                if month == 1:
                    date_from1, date_to1 = self._get_periode(12, year - 1)
                date_from2, date_to2 = self._get_periode(month, year)
                date_from1 = date_from1.replace(month=1)
                date_from2 = date_from2.replace(month=1)
                col_header = ["S/D " + long_cmonth[month], "S/D " + long_cmonth[month - 1]]
                report_header = "S/D BULAN %s %d" % (long_cmonth[month], year)

            # single unit
            if len(company_ids) == 1:
                rec, form, data1 = self._get_report_balance(report_type, report_id, date_from1, date_to1, company_ids)
                rec, form, data2 = self._get_report_balance(report_type, report_id, date_from2, date_to2, company_ids)
                report_data = data2 + data1
            # gabungan/konsolidasi
            else:
                rec, form, report_data = self._get_report_balance(report_type, report_id, date_from2, date_to2, company_ids)
                col_header = ['KANTOR DIREKSI', 'PG KEBON AGUNG', 'PG TRANGKIL', 'PT KEBON AGUNG']

            report_data = sorted(report_data, key=itemgetter('sequence', 'company_id'))
            pivot = self._generate_pivot_data(report_data)

        if report_type == 'cashflow':  # cash flow
            if month == 0:
                date_from1, date_to1 = self._get_periode(month, year - 1)
                date_from2, date_to2 = self._get_periode(month, year)
                date_from3, date_to3 = self._get_periode(month, year - 2)
                date_to1 = date_to1.replace(month=12)
                date_to2 = date_to2.replace(month=12)
                date_from1 = date_from1.replace(month=1)
                date_from2 = date_from2.replace(month=1)

                prev_date_to = date_to1
                prev_date_from = date_from1.replace(month=1)

                col_header = [year, year - 1]
                report_header = "TAHUN %d" % (year)
            else:
                date_from1, date_to1 = self._get_periode(month - 1, year)
                if month == 1:
                    date_from1, date_to1 = self._get_periode(12, year - 1)
                date_from2, date_to2 = self._get_periode(month, year)

                prev_date_to = date_from2 - datetime.timedelta(days=1)
                prev_date_from = prev_date_to.replace(day=1)

                date_from3 = date_from2.replace(year=year, month=1)
                date_to3 = date_to2

                col_header = [long_cmonth[month], long_cmonth[month - 1], "S/D " + long_cmonth[month]]
                report_header = "S/D BULAN %s %d" % (long_cmonth[month], year)

            # single unit
            if len(company_ids) == 1:
                rec, form, report_data = self._get_periode_balance(report_type, report_id, date_from1, date_to1,
                                                                   company_ids)
                rec, form, current_balance = self._get_periode_balance(report_type, report_id, date_from2, date_to2,
                                                                       company_ids)

                report_data = current_balance + report_data
                if month > 0:
                    rec, form, data3 = self._get_periode_balance(report_type, report_id, date_from3, date_to3, company_ids)
                    report_data = report_data + data3

            # gabungan/konsolidasi
            else:
                rec, form, report_data = self._get_periode_balance(report_type, report_id, date_from2, date_to2,
                                                                       company_ids)
                col_header = ['KANTOR DIREKSI', 'PG KEBON AGUNG', 'PG TRANGKIL', 'PT KEBON AGUNG']

            form['data']['form']['prev_date_from'] = prev_date_from
            form['data']['form']['prev_date_to'] = prev_date_to
            report_data = sorted(report_data, key=itemgetter('sequence', 'company_id'))
            pivot = self._generate_pivot_data(report_data)

        # for l in pivot:
        # print l['sequence'], l['level'],  l['type'], l['name'], l['balance_1'], l['balance_2']
        form['data']['form']['date_from'] = date_from2
        form['data']['form']['date_to'] = date_to2
        _data = form['data']['form']
        _data.update({'company_name': cname})
        _data.update({'financial_report_type': report_type})
        _data.update({'column_header': col_header})
        _data.update({'report_header': report_header})
        vals = {
            'doc_ids': [rec.id],
            'doc_model': model_name,
            'data': _data,
            'docs': rec,
            'time': time,
            'get_account_lines': pivot,
        }
        return rec.id, vals

    @api.model
    def get_html_financial_report(self, model_name, report_type, report_id, month, year, company):
        rec_id, vals = self.get_financial_report(model_name, report_type, report_id, month, year, company)
        return self.env['report'].render(self._report_name, vals)

    @api.model
    def get_pdf_financial_report(self, model_name, report_type, report_id, month, year, company):
        rec_id, vals = self.get_financial_report(model_name, report_type, report_id, month, year, company)
        global global_account_report_custom

        global_account_report_custom.append({
            'uid': self.env.uid,
            'vals': vals
        })

        return self.env['report'].get_action([rec_id], self._report_name)

    @api.model
    def render_html(self, docids, data=None):
        global global_account_report_custom

        is_exists = False
        idx = 0
        temp_vals = None
        for g in global_account_report_custom:
            if g['uid'] == self.env.uid:
                is_exists = True
                temp_vals = g['vals']
                break
            idx += 1

        if is_exists:
            del global_account_report_custom[idx]

        return self.env['report'].render(self._report_name, temp_vals)


class ReportFinancialPortrait(models.AbstractModel):
    _name = 'report.ka_account.report_financial_portrait_view'
    _inherit = 'base_report_financial_custom'

    _report_name = 'ka_account.report_financial_portrait_view'
    _report_vals = None


class ReportFinancialLandscape(models.AbstractModel):
    _name = 'report.ka_account.report_financial_landscape_view'
    _inherit = 'base_report_financial_custom'

    _report_name = 'ka_account.report_financial_landscape_view'
    _report_vals = None
