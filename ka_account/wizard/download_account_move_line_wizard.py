from odoo import api, fields, models, _
from odoo.exceptions import UserError
from pygments.lexer import _inherit
from datetime import datetime
from datetime import timedelta

class ka_general_ledger(models.TransientModel):
    _name = "download.account.move.line.wizard"     
    
    account_id          = fields.Many2one('account.account', 'Account')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    partner_id          = fields.Many2one('res.partner', 'Partner')
    date_from           = fields.Date('Date From', default=fields.Date.context_today, required=True)
    date_to             = fields.Date('Date To', default=fields.Date.context_today, required=True)


    @api.multi
    def action_download_move_line(self):
        return self.env['report'].get_action(self, 'account_move_line.xlsx')
