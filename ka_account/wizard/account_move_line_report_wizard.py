from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dbfpy import dbf


class account_move_line_report_wizard(models.TransientModel):
    _name = "account.move.line.report.wizard"
    _description = "Export to B2"

    @api.model
    def default_get(self, fields):
        res = super(account_move_line_report_wizard, self).default_get(fields)
        # default financial report
        report_src = self.env['account.journal'].search(
            [('name', '=', 'Stock Journal'), ('company_id', '=', self.env.user.company_id.id)])
        if report_src:
            res['account_journal_id'] = report_src.id
        return res

    company_id = fields.Many2one('res.company', string="Unit/PG", required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id, )
    account_journal_id = fields.Many2one('account.journal', 'Journal Type', required=True)
    date_from = fields.Date('Dari Tanggal', required=True, default=fields.Datetime.now)
    date_to = fields.Date('Sampai Tanggal', required=True, default=fields.Datetime.now)
    date = fields.Date("Tanggal Input", default=fields.Date.context_today)
    password = fields.Char("Password", required=True)

    def action_export_dbf(self):
        active_ids = self._context.get('active_ids', [])
        self.env['ka_account.voucher'].browse(active_ids).export_to_dbf()

    @api.multi
    def transaksi_pengadaan_to_dbf(self):
        if self.password != "Proses123":
            raise UserError('Password Salah!')

        if self.date_from > self.date_to:
            raise UserError('Date To should be greater than Date From')

        list_transaksi_pengadaan = self.env['account.move.line'].search(
            [('journal_id', '=', self.account_journal_id.id), ('date', '>=', self.date_from),
             ('date', '<=', self.date_to)])

        for list in list_transaksi_pengadaan:
            cek = self.env['ka_account.mapping.import'].search([('account_id','=',list.account_id.id)])
            if not cek:
                raise UserError('Perkiraan '+ list.account_id.code +' belum ada mapping ke perkiraan foxpro')


        db = dbf.Dbf("/var/lib/odoo/work/LOGISTIK/LOGODOO/AU4B2.DBF")

        bari = 0
        for a in db:
            bari = a['BARI']

        for list in list_transaksi_pengadaan:
            date = datetime.strptime(list.date, '%Y-%m-%d')
            nobu = 'L'+date.strftime("%d%m%y")

            jumlah = 0
            if list.debit == 0:
                jumlah = list.credit*-1
            else:
                jumlah = list.debit

            nope = self.env['ka_account.mapping.import'].search([('account_id', '=', list.account_id.id)])

            sub_perk = list.partner_id.code
            if not sub_perk:
                sub_perk = ''

            bari += 1
            rec = db.newRecord()
            rec["KD_TRANS"] = ''
            rec["PERK"] = nope.no_perk
            rec["SUBP"] = sub_perk
            rec["NOBU"] = nobu
            rec["TGBU"] = list.date[:4] + list.date[5:7] + list.date[8:]
            rec["BARI"] = bari
            rec["URAI"] = list.name
            rec["JUML"] = jumlah
            rec["SALD"] = 0.0
            rec["SALDS"] = 0.0
            rec["TGL_MAINT"] = self.date[:4] + self.date[5:7] + self.date[8:]
            rec["USR_MAINT"] = self.env.user.name
            rec.store()

        db.close()

        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message']="Data berhasil ditambahkan ke AU4B2 Logistik"

        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode':'form',
            'res_model':'sh.message.wizard',
            'views':[(view.id,'form')],
            'view_id':view.id,
            'target':'new',
            'context':context,
        }
