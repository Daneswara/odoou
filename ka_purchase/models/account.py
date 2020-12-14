from odoo import api, fields, models, _

class AccountPayableCategory(models.Model):
    _inherit="ka_account.payable.category"
   
    kode_ntb = fields.Char("Kode NTB", company_dependent=True)
    is_direct_purchase = fields.Boolean("Pembelian Langsung", help="Pembeliaan yang tidak akan menimbulkan Hutang, jadi nantinya langsung dibiayakan pada saat pembauaran")