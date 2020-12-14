from odoo import models, fields, api

class CashflowMappingReportWizard(models.TransientModel):
    _name = 'cashflow.mapping.report.wizard'
    _description = "Penggolongan move line terhadap report cash flow"

    wizard_line = fields.One2many('cashflow.mapping.report.wizard.line', 'wizard_id', string='Move Line Details')
    report_id = fields.Many2one('account.financial.report', 'Report', help='Manual mapping on cashflow report', domain="[('is_cashflow','=',True),('type','=','manual_mapping')]")
    company_id = fields.Many2one('res.company', string='Perusahaan', default=lambda self: self.env.user.company_id.id)

    @api.model
    def default_get(self, fields_list):
        res = super(CashflowMappingReportWizard, self).default_get(fields_list)
        line_ids = self._context.get('active_ids', [])
        move_lines = self.env['account.move.line'].browse(line_ids)

        data = []

        for line in move_lines:

            vals = {
                'move_line_id' : line.id,
                'date' : line.date,
                'account_id' : line.account_id.id,
                'name' : line.name,
                'partner_id' : line.partner_id.id,
                'analytic_account_id' : line.analytic_account_id.id,
                'debit' : line.debit,
                'credit' : line.credit,
            }

            data.append([0, 0, vals])
            
        res.update(
            wizard_line = data
        )

        return res

    def report_mapping(self):
        for wiz in self:
            lines = []
            for line in wiz.wizard_line:
                line.move_line_id.report_id = wiz.report_id

class CashflowMappingReportWizardLines(models.TransientModel):
    _name = 'cashflow.mapping.report.wizard.line'
    _description = "Penggolongan move line terhadap report cash flow"

    wizard_id = fields.Many2one('cashflow.mapping.report.wizard', string='Wizard Report Mapping')
    move_line_id = fields.Many2one('account.move.line', string="Journal Item")
    date = fields.Date(related="move_line_id.date", readonly=True)
    account_id = fields.Many2one(related="move_line_id.account_id", readonly=True)
    name = fields.Char(related="move_line_id.name", readonly=True)
    partner_id = fields.Many2one(related="move_line_id.partner_id", readonly=True)
    analytic_account_id = fields.Many2one(related="move_line_id.analytic_account_id",readonly=True)
    debit = fields.Monetary(related="move_line_id.debit", readonly=True)
    credit = fields.Monetary(related="move_line_id.credit", readonly=True)
    company_currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)

    