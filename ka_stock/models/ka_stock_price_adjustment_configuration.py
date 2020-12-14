from odoo import models, fields, api
from datetime import datetime
import time
from odoo.exceptions import UserError

class KAStockInventoryPriceAdjustment(models.Model):
    _name           = "ka_stock.inventory.price.adjustment.configuration"
    _description    = "Stock standard price adjustment configuration"
    _inherit        = ['mail.thread']

    company_id          = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id, track_visibility="onchange")
    account_input_id    = account_id = fields.Many2one('account.account', string="Stock Difference Input Account")
    account_output_id   = account_id = fields.Many2one('account.account', string="Stock Difference Output Account")

    _sql_constraints = [
		('res_config_company_id_unique', 'unique(company_id)', 'Configurasi PG/Unit sudah ada, silahkan buat konfigurasi PG/Unit lain!'),
	]
    
   