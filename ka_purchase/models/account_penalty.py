from openerp import models, fields, api
from datetime import datetime
import pytz

class AccountPenalty(models.Model):
    _name = "account.penalty"
    _description = "Account Penalty for Overdue Shipping"

    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    product_id = fields.Many2one("product.product", string="Product")
    amount = fields.Monetary(string="Amount")
    penalty_date = fields.Date(string="Penalty Date")
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True)

    
class AccountPenaltyConfig(models.Model):
    _name = "account.penalty.config"
    _description = "Configuration for Account Penalty"
    
    min_days = fields.Integer(string="Min Days")
    max_days = fields.Integer(string="Max Days")
    percent_penalty = fields.Float(string="Penalty (%)")
    

class AccountConfigSettings(models.TransientModel):
    _inherit = "account.config.settings"
    
    @api.one
    @api.depends('company_id')
    def _compute_account_penalty(self):
        self.penalty_account_id = self.company_id.penalty_account_id
    
    @api.one
    def _set_account_penalty(self):
        if self.penalty_account_id != self.company_id.penalty_account_id:
            self.company_id.penalty_account_id = self.penalty_account_id
            
    penalty_account_id = fields.Many2one("account.account", string="Penalty Account", compute="_compute_account_penalty", inverse="_set_account_penalty")


class ResCompany(models.Model):
    _inherit = "res.company"
    
    penalty_account_id = fields.Many2one("account.account", string="Penalty Account")