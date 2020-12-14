from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

class ka_account_periodic_account_mapping(models.Model):
    _name = "ka_account.periodic.account.mapping"
    _description = "Model to map deferred charges form future year(s) to current year. Model untuk memetakan beban ditangguhkan tahun depan ke tahun berjalan"
    
    name = fields.Char('Name')
    account_src_id = fields.Many2one('account.account', 'Source Account')
    account_dest_id = fields.Many2one('account.account', 'Destination Account')
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,
        default=lambda self: self.env.user.company_id.id)
    
    @api.one
    @api.constrains('account_src_id','account_dest_id')
    def _check_account_id(self):
        if self.account_src_id.id == self.account_dest_id.id:
            raise ValidationError(_('Perkiraan asal dan Perkiraan tujuan tidak boleh sama!'))