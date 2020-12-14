# -*- coding: utf-8 -*-

import time
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime


class CashflowAccountMapping(models.Model):
    _name = 'ka_account.cashflow.account.mapping'

    account_id = fields.Many2one('account.account', 'Account', help='Account that has to manually mapped on cashflow report')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                    default=lambda self: self.env.user.company_id.id)

class CashflowAccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line','ir.needaction_mixin']
    
    def action_view_cashflow_account_mapping(self):
        mapped_accounts = self.env['ka_account.cashflow.account.mapping'].search([('company_id','child_of', self.env.user.company_id.id)])
        account_ids = [line.account_id.id for line in mapped_accounts]
        
        action = self.env.ref('account.action_account_moves_all_a')
        result = action.read()[0]
        result['domain'] = [
            ('report_id', '=', False),
            ('account_id', 'in', account_ids),
            ('move_id.state', '=', 'posted'),
            ('journal_id.type', 'in', ['cash','bank']),
        ]

        # result['context'] = {
        #     'count_menu': 'cashflow_mapping'
        # }
        
        return result

    # @api.model
    # def _needaction_domain_get(self):
    #     if self.env.context.get('count_menu') == 'cashflow_mapping':
    #         mapped_accounts = self.env['ka_account.cashflow.account.mapping'].search([('company_id','child_of', self.env.user.company_id.id)])
    #         account_ids = [line.account_id.id for line in mapped_accounts]
            
    #         return [('report_id', '=', False),
    #         ('account_id', 'in', account_ids),
    #         ('move_id.state', '=', 'posted'),
    #         ('journal_id.type', 'in', ['cash','bank'])]

    #     return False

# class IrUiMenu(models.Model):
#     _inherit = 'ir.ui.menu'

#     @api.multi
#     def get_needaction_data(self):
#         res = dict()

#         for menu in self:
#             if menu.action and menu.action.context:
#                 new_context = dict()
#                 try:
#                     new_context = ast.literal_eval(menu.action.context)
#                     new_context.update(self.env.context)
#                 except:
#                     new_context = self.env.context
#             res.update(
#                 super(IrUiMenu,
#                       menu.with_context(new_context)).get_needaction_data())

#         return res