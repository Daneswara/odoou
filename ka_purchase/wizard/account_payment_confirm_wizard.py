from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class account_payment_confirm_wizard(models.TransientModel):
    _name = "account.payment.confirm.wizard"
    
    name = fields.Char('Name', default='Are you sure to confirm all selected payments?')
    
    @api.multi
    def action_confirm_payments(self):
        active_ids = self._context.get('active_ids', False)
        if active_ids:
            for payment in self.env['account.payment'].browse(active_ids):
                if payment.payment_type != 'outbound':
                    raise UserError('Sorry, this action can be proceeded only for purchase payments.')
                if payment.state != 'proposed':
                    raise UserError('Sorry, this action can be proceeded only for proposed payments.')
                
            date_now = datetime.strftime(datetime.now().date(), '%Y-%m-%d')
            confirm_name = self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.confirm')
            confirm_id = self.env['account.payment.confirm'].create({'name': confirm_name,
                                                                     'currency_id': self.env.user.company_id.currency_id.id,
                                                                     'confirm_date': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')})
            for payment in self.env['account.payment'].browse(active_ids):
                payment.write({'account_payment_confirm_id': confirm_id.id, 'state': 'confirm'})
            
            return {
                'name': 'Confirm Payments',
                'res_model': 'account.payment.confirm',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': confirm_id.id,
                'target': 'current'
            }