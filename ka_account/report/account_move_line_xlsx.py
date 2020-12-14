from openerp import api, fields, models, _
from datetime import datetime
from calendar import monthrange
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
  

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass


class AccountMoveLineXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, download_b3_wizard):
        # ====================== PRE-DEFINED FORMAT =====================================
        
        header_format = workbook.add_format({'bold': 1,'valign':'vcenter','align':'left'})
        
        #################################################################################

        normal_format = workbook.add_format({'align':'left'})

        #################################################################################

        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        #################################################################################

        number_format = workbook.add_format({'num_format': '0.00','valign':'vcenter'})

        # ====================== END OF PRE-DEFINED FORMAT =====================================
        
        # ====================== NAMING WORKSHEET =================================
        worksheet = workbook.add_worksheet("account_move_line")
        worksheet.set_paper(9)
        worksheet.set_portrait()
        worksheet.set_margins(0.3, 0.3, 0.5, 0.5)

        # =================== FREEZE PANES ========================
        worksheet.freeze_panes(1, 0)

        # ==================== SET COLUMN WIDTH =====================
        worksheet.set_column('A:A', 22)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 36)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 40)
        worksheet.set_column('G:G', 18)
        worksheet.set_column('H:H', 40)
        worksheet.set_column('I:I', 40)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 15)
        worksheet.set_column('L:L', 15)
        
        # ================== SET ROW HEIGHT ========================
        worksheet.set_row(0,22)        
        
        # ================== SET HEADER INFO =====================================
        worksheet.write(0,0,'NOBU',header_format)
        worksheet.write(0,1,'TGBU',header_format)
        worksheet.write(0,2,'NOPERK',header_format)
        worksheet.write(0,3,'PERK',header_format)
        worksheet.write(0,4,'KODE_PARTNER',header_format)
        worksheet.write(0,5,'PARTNER',header_format)
        worksheet.write(0,6,'KODE_SUBP',header_format)
        worksheet.write(0,7,'SUBP',header_format)
        worksheet.write(0,8,'URAI',header_format)
        worksheet.write(0,9,'DEB',header_format)
        worksheet.write(0,10,'KRED',header_format)
        worksheet.write(0,11,'JUML',header_format)

        # ========================= QUERY TIME ^_^ ===============================
        date_from = datetime.strptime(download_b3_wizard.date_from, DF)
        date_to = datetime.strptime(download_b3_wizard.date_to, DF)

        params = []
        query = """ SELECT move.name as nobu,
                            move_line.date as tgbu,
                            account.code as noperk,
                            account.name as perk,
                            partner.code as kode_partner,
                            partner.name as partner,
                            analytic.code as kode_subp,
                            analytic.name as subp,
                            move_line.name as urai,
                            move_line.debit as deb,
                            move_line.credit as kred,
                            move_line.balance as juml
                            FROM account_move_line as move_line
                            JOIN account_move as move ON move_line.move_id = move.id
                            JOIN account_account as account ON move_line.account_id = account.id
                            LEFT JOIN res_partner as partner ON move_line.partner_id = partner.id
                            LEFT JOIN account_analytic_account as analytic ON move_line.analytic_account_id = analytic.id
                            WHERE move.state = 'posted' AND (move_line.date >= %s AND move_line.date <= %s) AND move_line.company_id = %s"""
        
        params.append(date_from)
        params.append(date_to)
        params.append(self.env.user.company_id.id)

        if download_b3_wizard.account_id:
            query += (" AND move_line.account_id = %s")
            params.append(download_b3_wizard.account_id.id)

        if download_b3_wizard.analytic_account_id:
            query += (" AND move_line.analytic_account_id = %s")
            params.append(download_b3_wizard.analytic_account_id.id)

        if download_b3_wizard.partner_id:
            query += (" AND move_line.partner_id = %s")
            params.append(download_b3_wizard.partner_id.id)

        query += (" ORDER BY move_line.date, move_line.id ASC")
        
        self.env.cr.execute(query,params)
        
        move_lines = self.env.cr.dictfetchall()

        row = 0

        for line in move_lines:
            row = row + 1
            tgbu = datetime.strptime(line['tgbu'], DF)

            worksheet.write(row,0,line['nobu'])
            worksheet.write_datetime(row, 1, tgbu, date_format)
            worksheet.write(row,2,line['noperk'])
            worksheet.write(row,3,line['perk'])
            worksheet.write(row,4,line['kode_partner'])
            worksheet.write(row,5,line['partner'],normal_format)
            worksheet.write(row,6,line['kode_subp'])
            worksheet.write(row,7,line['subp'],normal_format)
            worksheet.write(row,8,line['urai'],normal_format)
            worksheet.write(row,9,line['deb'],number_format)
            worksheet.write(row,10,line['kred'],number_format)
            worksheet.write(row,11,line['juml'],number_format)

        workbook.close()
        
        
AccountMoveLineXlsx('report.account_move_line.xlsx',
            'download.account.move.line.wizard')