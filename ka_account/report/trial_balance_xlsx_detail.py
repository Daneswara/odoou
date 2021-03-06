from openerp import api, fields, models, _
from datetime import datetime
from calendar import monthrange
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as for_date

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass


class Trial_Balance_Xlsx_Detail(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, account_report):
        date_from = datetime.strptime(account_report.date_from, for_date)
        date_jan = date_from.replace(month=1, day=1).strftime(for_date)
        #################################################################################
        header_style = workbook.add_format({'bold': 1, 'align': 'center', 'valign': 'vcenter'})
        header_style.set_font_name('Arial')
        header_style.set_font_size('10')
        header_style.set_text_wrap()
        header_style.set_bottom(8)
        #################################################################################
        header1_center = workbook.add_format({'bold': 1, 'align': 'center', 'valign': 'vcenter'})
        header1_center.set_font_name('Arial')
        header1_center.set_font_size('8')
        header1_center.set_border()
        header1_center.set_text_wrap()
        #################################################################################
        header2_left = workbook.add_format({'bold': 1, 'align': 'left', 'valign': 'vcenter'})
        header2_left.set_font_name('Arial')
        header2_left.set_font_size('8')
        header2_left.set_text_wrap()
        #################################################################################
        header3_style = workbook.add_format({'bold': 1, 'align': 'center', 'valign': 'vcenter'})
        header3_style.set_font_name('Arial')
        header3_style.set_font_size('8')
        header3_style.set_text_wrap()
        #################################################################################
        normal_left_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        normal_left_border.set_text_wrap()
        normal_left_border.set_font_name('Arial')
        normal_left_border.set_font_size('8')
        normal_left_border.set_border()
        normal_left_border.set_text_wrap()
        #################################################################################
        bold_left_border = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        bold_left_border.set_text_wrap()
        bold_left_border.set_font_name('Arial')
        bold_left_border.set_font_size('8')
        bold_left_border.set_border()
        #################################################################################
        normal_right_border = workbook.add_format({'valign': 'vcenter', 'align': 'right'})
        normal_right_border.set_text_wrap()
        normal_right_border.set_font_name('Arial')
        normal_right_border.set_font_size('8')
        normal_right_border.set_border()
        #################################################################################
        bold_right_border = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        bold_right_border.set_text_wrap()
        bold_right_border.set_font_name('Arial')
        bold_right_border.set_font_size('8')
        bold_right_border.set_border()
        #################################################################################
        normal_center_border = workbook.add_format({'valign': 'vcenter', 'align': 'center'})
        normal_center_border.set_text_wrap()
        normal_center_border.set_font_name('Arial')
        normal_center_border.set_font_size('8')
        normal_center_border.set_border()
        #################################################################################
        bold_center_border = workbook.add_format({'valign': 'vcenter', 'align': 'center'})
        bold_center_border.set_text_wrap()
        bold_center_border.set_font_name('Arial')
        bold_center_border.set_font_size('8')
        bold_center_border.set_border()

        worksheet = workbook.add_worksheet("Neraca Bulanan")
        worksheet.set_paper(9)
        worksheet.set_portrait()
        worksheet.set_margins(0.3, 0.3, 0.5, 0.5)
        worksheet.freeze_panes(5, 0)
        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)

        worksheet.set_row(0, 18)
        worksheet.set_row(1, 18)
        worksheet.set_row(2, 18)
        worksheet.set_row(4, 22)

        date_to = datetime.strftime(datetime.strptime(account_report.date_to, '%Y-%m-%d'), '%d-%m-%Y')
        date_from2 = datetime.strftime(datetime.strptime(account_report.date_from, '%Y-%m-%d'), '%d-%m-%Y')

        worksheet.merge_range('A1:B1', 'PT. KEBON AGUNG', header2_left)
        worksheet.merge_range('A2:B2', self.env.user.company_id.name.upper(), header2_left)
        worksheet.merge_range('A3:B3', self.env.user.company_id.city.upper(), header2_left)
        worksheet.merge_range('C2:I2', 'DETAIL NERACA BULANAN', header_style)
        worksheet.merge_range('C3:I3', date_from2+ ' s/d ' + date_to, header3_style)

        worksheet.write(4, 0, 'No. Perk', header1_center)
        worksheet.write(4, 1, 'Nama Perkiraan', header1_center)
        worksheet.write(4, 2, 'Kode', header1_center)
        worksheet.write(4, 3, 'Partner', header1_center)
        worksheet.write(4, 4, 'Kode', header1_center)
        worksheet.write(4, 5, 'Sub. Perk', header1_center)
        worksheet.write(4, 6, 'Saldo Awal', header1_center)
        worksheet.write(4, 7, 'Debit', header1_center)
        worksheet.write(4, 8, 'Kredit', header1_center)
        worksheet.write(4, 9, 'Saldo Akhir', header1_center)
        # worksheet.write(4,10,'R.A.B.P \n(1=1000)',header1_center)

        opening_str = 0.0
        debit_str = 0.0
        credit_str = 0.0
        ending_str = 0.0

        total_opening_balance = 0.0
        total_debit = 0.0
        total_credit = 0.0
        total_ending_balance = 0.0

        row = 4
        for account in self.env['account.financial.report'].search(
                [('parent_id', '=', account_report.account_report_id.id)], order='sequence asc').filtered(
                lambda x: len(x.account_ids) != 0):
            # row +=1
            # worksheet.set_row(row,18)
            # if account.code:
            #     worksheet.write(row,0,account.code,normal_center_border)
            # worksheet.merge_range(row,1,row,6,account.name,bold_left_border)
            # worksheet.write(row,6,'',normal_center_border)

            for acc in account.account_ids:
                subtotal_opening_balance = 0.0
                subtotal_debit = 0.0
                subtotal_credit = 0.0
                subtotal_ending_balance = 0.0


                # date_from = datetime.strptime(date_from, for_date)
                date_jan = date_from.replace(month=1, day=1).strftime(for_date)
                # dateto = datetime.strptime(account_report.date_to, "%Y-%m-%d") + timedelta(hours=7)
                # if acc.user_type_id.include_initial_balance or int(dateto.year) < 2020:
                self.env.cr.execute("""select sum(move_line.balance) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_journal journal on move_line.journal_id = journal.id
                                join account_move move on move_line.move_id = move.id
                                where move.state = 'posted' and move_line.account_id = %s and move_line.date < %s and move_line.date >= %s""",
                                    (acc.id, account_report.date_from, date_jan))
                open_balance = self.env.cr.dictfetchone()
                if open_balance['sum'] == None:
                    open_balance['sum'] = 0.0
                opening_str = str('{0:,.2f}'.format(float(open_balance['sum']))).replace('.', '%').replace(',',
                                                                                                           '.').replace(
                    '%', ',')

                self.env.cr.execute("""select sum(move_line.debit) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_journal journal on move_line.journal_id = journal.id
                                join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s""",
                                    (acc.id, account_report.date_from, account_report.date_to))
                debit = self.env.cr.dictfetchone()
                if debit['sum'] == None:
                    debit['sum'] = 0.0
                debit_str = str('{0:,.2f}'.format(float(debit['sum']))).replace('.', '%').replace(',', '.').replace('%',
                                                                                                                    ',')

                self.env.cr.execute("""select sum(move_line.credit) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                join account_journal journal on move_line.journal_id = journal.id
                                join account_move move on move_line.move_id = move.id
                            where move.state = 'posted' and move_line.account_id = %s and move_line.date >= %s and move_line.date <= %s""",
                                    (acc.id, account_report.date_from, account_report.date_to))
                credit = self.env.cr.dictfetchone()
                if credit['sum'] == None:
                    credit['sum'] = 0.0
                credit_str = str('{0:,.2f}'.format(float(credit['sum']))).replace('.', '%').replace(',', '.').replace(
                    '%', ',')

                end_balance = open_balance['sum'] + debit['sum'] - credit['sum']
                ending_str = str('{0:,.2f}'.format(float(end_balance))).replace('.', '%').replace(',', '.').replace('%',
                                                                                                                    ',')

                self.env.cr.execute('''select COALESCE(open.kode, debkred.kode) as p_kode, COALESCE(open.a_kode, debkred.a_kode) as a_kode, 
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
                                    (acc.id, account_report.date_from, date_jan, acc.id, account_report.date_to,
                                     account_report.date_from))

                details = self.env.cr.dictfetchall() or 0

                # print(details)
                # print("-------------------------detailsss-----------------------------")
                if float(open_balance['sum']) == 0.0 and float(debit['sum']) == 0.0 and float(credit['sum']) == 0.0:
                    a = 1
                else:
                    row += 1
                    worksheet.set_row(row, 18)
                    worksheet.write(row, 0, acc.code, bold_center_border)
                    worksheet.write(row, 1, acc.name, bold_left_border)
                    if details != 0:
                        for detail in details:
                            if float(detail['awal']) == 0.0 and float(detail['debet']) == 0.0 and float(
                                    detail['kredit']) == 0.0:
                                a = 2
                            else:
                                saldo_awal = str('{0:,.2f}'.format(float(detail['awal']))).replace('.', '%').replace(',',
                                                                                                                     '.').replace(
                                    '%', ',')
                                saldo_debet = str('{0:,.2f}'.format(float(detail['debet']))).replace('.', '%').replace(',',
                                                                                                                       '.').replace(
                                    '%', ',')
                                saldo_kredit = str('{0:,.2f}'.format(float(detail['kredit']))).replace('.', '%').replace(',',
                                                                                                                         '.').replace(
                                    '%', ',')
                                saldo_akhir = str('{0:,.2f}'.format(float(detail['saldo']))).replace('.', '%').replace(',',
                                                                                                                       '.').replace(
                                    '%', ',')

                                worksheet.write(row, 2, detail['p_kode'], normal_center_border)
                                worksheet.write(row, 3, detail['nama'], normal_left_border)
                                worksheet.write(row, 4, detail['a_kode'], normal_center_border)
                                worksheet.write(row, 5, detail['a_nama'], normal_left_border)
                                worksheet.write(row, 6, saldo_awal, normal_right_border)
                                worksheet.write(row, 7, saldo_debet, normal_right_border)
                                worksheet.write(row, 8, saldo_kredit, normal_right_border)
                                worksheet.write(row, 9, saldo_akhir, normal_right_border)

                                subtotal_opening_balance += float(detail['awal'])
                                subtotal_debit += float(detail['debet'])
                                subtotal_credit += float(detail['kredit'])
                                subtotal_ending_balance += float(detail['saldo'])
                                row += 1
                    else:
                        worksheet.write(row, 2, '', normal_center_border)
                        worksheet.write(row, 3, '', normal_left_border)
                        worksheet.write(row, 4, '', normal_center_border)
                        worksheet.write(row, 5, '', normal_left_border)
                        worksheet.write(row, 6, opening_str, normal_right_border)
                        worksheet.write(row, 7, debit_str, normal_right_border)
                        worksheet.write(row, 8, credit_str, normal_right_border)
                        worksheet.write(row, 9, ending_str, normal_right_border)

                        subtotal_opening_balance += float(open_balance['sum'])
                        subtotal_debit += float(debit['sum'])
                        subtotal_credit += float(credit['sum'])
                        subtotal_ending_balance += float(end_balance)
                        row += 1

                    worksheet.set_row(row, 18)
                    worksheet.write(row, 0, '', normal_left_border)
                    worksheet.merge_range(row, 0, row, 5, 'JUMLAH '+acc.code +' :', bold_right_border)
                    worksheet.write(row, 6,
                                    str('{0:,.2f}'.format(float(subtotal_opening_balance))).replace('.', '%').replace(
                                        ',', '.').replace('%', ','), bold_right_border)
                    worksheet.write(row, 7, str('{0:,.2f}'.format(float(subtotal_debit))).replace('.', '%').replace(',',
                                                                                                                    '.').replace(
                        '%', ','), bold_right_border)
                    worksheet.write(row, 8,
                                    str('{0:,.2f}'.format(float(subtotal_credit))).replace('.', '%').replace(',',
                                                                                                             '.').replace(
                                        '%', ','), bold_right_border)
                    worksheet.write(row, 9,
                                    str('{0:,.2f}'.format(float(subtotal_ending_balance))).replace('.', '%').replace(
                                        ',', '.').replace('%', ','), bold_right_border)

                    total_opening_balance += subtotal_opening_balance
                    total_debit += subtotal_debit
                    total_credit += subtotal_credit
                    total_ending_balance += subtotal_ending_balance

        row += 1
        worksheet.set_row(row, 18)
        worksheet.write(row, 0, '', normal_left_border)
        worksheet.merge_range(row, 0, row, 5, 'JUMLAH SEMUA', bold_right_border)
        worksheet.write(row, 6, str('{0:,.2f}'.format(float(total_opening_balance))).replace('.', '%').replace(',',
                                                                                                               '.').replace(
            '%', ','), bold_right_border)
        worksheet.write(row, 7,
                        str('{0:,.2f}'.format(float(total_debit))).replace('.', '%').replace(',', '.').replace('%',
                                                                                                               ','),
                        bold_right_border)
        worksheet.write(row, 8,
                        str('{0:,.2f}'.format(float(total_credit))).replace('.', '%').replace(',', '.').replace('%',
                                                                                                                ','),
                        bold_right_border)
        worksheet.write(row, 9,
                        str('{0:,.2f}'.format(float(total_ending_balance))).replace('.', '%').replace(',', '.').replace(
                            '%', ','), bold_right_border)
        # worksheet.write(row, 6, '-', normal_center_border)

        workbook.close()


Trial_Balance_Xlsx_Detail('report.trial.balance.xlsx.detail',
                          'ka_trial.balance.report.wizard')
