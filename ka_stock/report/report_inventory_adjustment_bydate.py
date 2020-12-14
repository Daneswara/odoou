from openerp import models, fields, api, _


class ReportInventoryAdjustmentBydate(models.AbstractModel):
    _name = 'report.ka_stock.template_inventory_adjustment_bydate'
    _template = 'ka_stock.template_inventory_adjustment_bydate'


    def get_product_lines(self, data):
        
        product_lines = self.env['stock.inventory.line'].search([('inventory_id.date','>=',data['date_start']),
                                                                 ('inventory_id.date','<=',data['date_end']),
                                                                 ('company_id','=', data['company_id'])])


        if data['status'] != 'all':
            product_lines = product_lines.filtered(lambda r: r.state == data['status'])

        if data['type'] == 'product':
            # self._template = 'ka_stock.template_inventory_adjustment_bydate_not_done'

            p_ids = [l.product_id.id for l in product_lines]
            product_lines = self.env['product.product'].search([('id', 'not in', p_ids),
                                                                  ('qty_available', '>', 0)])

            #get stock location 
            company_user = self.env.user.company_id
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
            if warehouse:
                location = warehouse.lot_stock_id.id
            else:
                raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))
            
            #get qty available by quant on certain location
            product_lines = product_lines.filtered(lambda z: sum(x.qty for x in z.stock_quant_ids.filtered(lambda r: r.location_id.id == location)) > 0)
        else:
            if data['advance_type'] == 'different':
                product_lines = product_lines.filtered(lambda r: r.difference_qty != 0)
            else:
                product_lines = product_lines.filtered(lambda r: r.difference_qty == 0)
                
        return product_lines


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