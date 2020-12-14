from odoo import models, fields, api, _


class ReportInventoryValuation(models.AbstractModel):
    _name = 'report.ka_stock.template_inventory_valuation'
    _template = 'ka_stock.template_inventory_valuation'

    def get_inventory_value(self, data):

        params = []

        query = """SELECT account.id, account.code, account.name, COUNT(product_id) as item, SUM(quant.qty) as kuantum, SUM(quant.qty * property1.value_float) as nilai
						FROM product_product as product
                        JOIN product_template as template ON product.product_tmpl_id = template.id
						JOIN product_category as category ON template.categ_id = category.id
 						JOIN (
								SELECT * 
									FROM ir_property WHERE name = 'standard_price'
						) as property1 ON property1.res_id = CONCAT('product.product,',product.id)
						JOIN (
								SELECT *
									FROM ir_property WHERE name = 'property_stock_valuation_account_id' 
						) as property2 ON property2.res_id = CONCAT('product.category,',category.id)
						JOIN account_account as account ON property2.value_reference = CONCAT('account.account,',account.id)
                        JOIN stock_quant as quant ON quant.product_id = product.id
						JOIN stock_location as location ON location.id = quant.location_id
                        WHERE account.company_id = %s AND property1.company_id = %s AND property2.company_id = %s AND location.id = %s
                        GROUP BY account.id 
                        ORDER BY account.code ASC"""
        
        params.append(data['company_id'])
        params.append(data['company_id'])
        params.append(data['company_id'])
        params.append(data['location_id'])

        self.env.cr.execute(query,params)
        
        results = self.env.cr.dictfetchall()

        return results


    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        
        vals = {
            'company_id': data['form']['company_id'],
            'location_id': data['form']['location_id']
        }

        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'get_inventory_value': self.get_inventory_value(vals),
        }
        
        return report_obj.render(self._template, docargs)
