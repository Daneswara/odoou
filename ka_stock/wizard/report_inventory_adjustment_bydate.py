from openerp import models, fields, api, _


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class ReportInvetoryAdjustmentWizardBydate(models.TransientModel):
    _name = "report.inventory.adjustment.bydate.wiz"

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    date_start = fields.Date('Mulai')
    date_end = fields.Date('S / D')
    status = fields.Selection([
        ('confirm', 'In Progress'),
        ('done','Validated'),
        ('all','-- Semua --')], string='Status', default='all')
    type = fields.Selection([('inventory', 'Stock Opname'),('product','Belum Stok Opname')], string='Sumber', default='inventory')
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.ref('base.lang_id').code,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")
    advance_type = fields.Selection([
        ('different', 'Selisih'),
        ('equal','Tidak Selisih')], string='Tipe Lanj.', default='different')

    @api.multi
    def generate_report(self):
        report_obj = self.env['report']
        template = 'ka_stock.template_inventory_adjustment_bydate'
        report = report_obj._get_report_from_name(template)
        form = {
            'date_start': self.date_start,
            'date_end': self.date_end,
            'status': self.status,
            'company_id': self.company_id.id,
            'type': self.type,
            'advance_type': self.advance_type,
            }
        data = {
            'ids': self.ids,
            'model': report.model,
            'form': form
            }
        return report_obj.get_action(self, template, data=data)