from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ReportInvetoryValuationWizard(models.TransientModel):
    _name = "report.inventory.valuation.wizard"

    @api.model
    def _compute_default_location(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    report_date = fields.Datetime('Tanggal Cetak', default=fields.Datetime.now)
    location_id = fields.Many2one('stock.location', sting='Lokasi', default=_compute_default_location, domain='[("company_id","=",company_id)]')

    @api.multi
    def generate_report(self):
        report_obj = self.env['report']
        template = 'ka_stock.template_inventory_valuation'
        report = report_obj._get_report_from_name(template)
        form = {
            'company_id': self.company_id.id,
            'report_date': self.report_date,
            'location_id': self.location_id.id,
            }
        data = {
            'ids': self.ids,
            'model': report.model,
            'form': form
            }

        return report_obj.get_action(self, template, data=data)