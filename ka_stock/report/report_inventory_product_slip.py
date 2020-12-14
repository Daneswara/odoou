from odoo import models, fields, api, _


class ReportInventoryProductSlip(models.AbstractModel):
    _name = 'report.ka_stock.template_inventory_product_slip'
    _template = 'ka_stock.template_inventory_product_slip'

    def get_product_lines(self, data):
        if data['type'] == 'category':
            products = self.env['product.product'].search([('categ_id', 'child_of', data['category_id'])])
        else:
            products = self.env['product.product'].search([('default_code', '>=', data['default_code1']),
                                                           ('default_code', '<=', data['default_code2'])])
        
        if data['qty_available'] == 'set':
            products = products.filtered(lambda z: sum(x.qty for x in z.stock_quant_ids.filtered(lambda r: r.location_id.id == data['location_id'])) > 0)
        else:
            products = products.filtered(lambda z: sum(x.qty for x in z.stock_quant_ids.filtered(lambda r: r.location_id.id == data['location_id'])) <= 0)

        return products


    @api.multi
    def _get_quants(self, location_id, product_id):
        return self.env['stock.quant'].search([
            ('location_id', '=', location_id.id),
            ('product_id','=', product_id.id)])

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        product_lines = self.get_product_lines(data.get('form'))
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'get_product_lines': product_lines,
        }
        return report_obj.render(self._template, docargs)
