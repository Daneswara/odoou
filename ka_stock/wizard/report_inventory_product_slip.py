from odoo import models, fields, api, _


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class ReportInvetoryProductSlipWizard(models.TransientModel):
    _name = "report.inventory.product.slip.wizard"

    @api.model
    def _compute_default_location(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    type = fields.Selection([('product', 'Kode Barang'),
                             ('category','Kelompok Barang')],
                            string='Berdasarkan', default='product')
    category_id = fields.Many2one('product.category', string='Kelompok Barang')
    default_code1 = fields.Char('Kode Awal', size=12)
    default_code2 = fields.Char('Kode Akhir', size=12)
    location_id = fields.Many2one('stock.location', sting='Lokasi', default=_compute_default_location, domain='[("company_id","=",company_id)]')
    qty_available = fields.Selection([('empty', 'Kosong'),
                                      ('set', 'Lebih dari 0')],
                                    string='Kuantum', default='set')
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.ref('base.lang_id').code)

    @api.multi
    def generate_report(self):
        report_obj = self.env['report']
        template = 'ka_stock.template_inventory_product_slip'
        report = report_obj._get_report_from_name(template)
        form = {
            'company_id': self.company_id.id,
            'type': self.type,
            'category_id': self.category_id.id,
            'default_code1': self.default_code1,
            'default_code2': self.default_code2,
            'qty_available': self.qty_available,
            'location_id': self.location_id.id,
            }
        data = {
            'ids': self.ids,
            'model': report.model,
            'form': form
            }
        return report_obj.get_action(self, template, data=data)