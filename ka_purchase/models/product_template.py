from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from datetime import datetime
import pytz

class ProductTemplate(models.Model):
    _inherit = 'product.template'
     
    _status_compute_last_order = False
 
    last_order = fields.Date(compute='_compute_last_order', string='TBTE', type='date')
    last_order_id = fields.Many2one('purchase.order', compute='_compute_last_order', string='No SP')
    last_consume_date = fields.Datetime('Tgl. Terakhir Pakai', compute='get_last_consume_date', search='search_last_consume_date')
    last_consume_id = fields.Many2one('stock.move', compute='get_last_consume_id', string='No Bon', search='search_last_consume_id')

    @api.multi
    def get_last_consume_id(self):
        
        company_id  = self.env.user.company_id._ids
        company_ids = self.env['res.company'].search([('id','child_of', company_id)])._ids
        
        str_company = "("
        for c in company_ids:
            str_company += str(c) + ","
            
        str_company = str_company[:-1]
        str_company += ")"
        
        for this in self:
            self._cr.execute('''select sm.id from stock_picking sp
                                join stock_move sm on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sm.company_id in %s and sl_dest.usage = 'production' and sp.state = 'done' and pp.product_tmpl_id = %s
                                order by sp.date_transfer desc limit 1''' %(str_company, this.id,))
            no_bukti = False
            datas = self._cr.fetchall()
            for data in datas:
                no_bukti = data[0]
            this.last_consume_id = no_bukti


    def search_last_consume_id(self, operator, value):
        if value == False:
            company_id  = self.env.user.company_id._ids
            company_ids = self.env['res.company'].search([('id','child_of', company_id)])._ids
            
            str_company = "("
            for c in company_ids:
                str_company += str(c) + ","
                
            str_company = str_company[:-1]
            str_company += ")"

            self._cr.execute('''select pp.product_tmpl_id from stock_picking sp
                                join stock_move sm on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sm.company_id in %s and sl_dest.usage = 'production' and sp.state = 'done'
                                group by pp.product_tmpl_id''' %(str_company,))

            
            datas = self._cr.fetchall()
            products = [data for data in datas]
            res_opr = 'in'
            if operator == '=':
                res_opr = 'not in'
            return [('id', res_opr, products)]
        else:
            products = []
            for product in self.env['product.template'].search([('active','=',True)]):
                self._cr.execute('''select sp.date_transfer from stock_move sm
                                join stock_picking sp on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sl_dest.usage = 'production' and sp.state = 'done' and pp.product_tmpl_id = %s
                                order by sp.date_transfer desc limit 1''', (product.id,))
                
                date_transfer = False
                datas = self._cr.fetchall()
                for data in datas:
                    date_transfer = data[0]
                
                if date_transfer:
                    if operator == '>' and date_transfer > value:
                        products.append(product.id)
                    elif operator == '<' and date_transfer < value:
                        products.append(product.id)
                    elif operator == '>=' and date_transfer >= value:
                        products.append(product.id)
                    elif operator == '<=' and date_transfer <= value:
                        products.append(product.id)
                    elif operator == '=' and date_transfer == value:
                        products.append(product.id)
                    elif operator == '!=' and date_transfer != value:
                        products.append(product.id)
            return [('id', 'in', products)]



    @api.multi
    def get_last_consume_date(self):
        
        company_id  = self.env.user.company_id._ids
        company_ids = self.env['res.company'].search([('id','child_of', company_id)])._ids
        
        str_company = "("
        for c in company_ids:
            str_company += str(c) + ","
            
        str_company = str_company[:-1]
        str_company += ")"
        
        for this in self:
            self._cr.execute('''select sp.date_transfer from stock_move sm
                                join stock_picking sp on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sm.company_id in %s and sl_dest.usage = 'production' and sp.state = 'done' and pp.product_tmpl_id = %s
                                order by sp.date_transfer desc limit 1''' %(str_company, this.id,))
            date_transfer = False
            datas = self._cr.fetchall()
            for data in datas:
                date_transfer = data[0]
            this.last_consume_date = date_transfer

    def search_last_consume_date(self, operator, value):
        if value == False:
            self._cr.execute('''select pp.product_tmpl_id from stock_move sm
                                join stock_picking sp on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sl_dest.usage = 'production' and sp.state = 'done'
                                group by pp.product_tmpl_id''')
            datas = self._cr.fetchall()
            products = [data for data in datas]
            res_opr = 'in'
            if operator == '=':
                res_opr = 'not in'
            return [('id', res_opr, products)]
        else:
            products = []
            for product in self.env['product.template'].search([('active','=',True)]):
                self._cr.execute('''select sp.date_transfer from stock_move sm
                                join stock_picking sp on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sl_dest.usage = 'production' and sp.state = 'done' and pp.product_tmpl_id = %s
                                order by sp.date_transfer desc limit 1''', (product.id,))
                
                date_transfer = False
                datas = self._cr.fetchall()
                for data in datas:
                    date_transfer = data[0]
                
                if date_transfer:
                    if operator == '>' and date_transfer > value:
                        products.append(product.id)
                    elif operator == '<' and date_transfer < value:
                        products.append(product.id)
                    elif operator == '>=' and date_transfer >= value:
                        products.append(product.id)
                    elif operator == '<=' and date_transfer <= value:
                        products.append(product.id)
                    elif operator == '=' and date_transfer == value:
                        products.append(product.id)
                    elif operator == '!=' and date_transfer != value:
                        products.append(product.id)
            return [('id', 'in', products)]

    @api.model
    def default_get(self, field):
        res = super(ProductTemplate, self).default_get(field)
        res['supplier_taxes_id'] = False
        return res

    @api.multi
    def _compute_last_order(self):
        if self._status_compute_last_order:
            return
 
        self._status_compute_last_order = True
        ids = [s.id for s in self]
 
        company_id  = self.env.user.company_id._ids
        company_ids = self.env['res.company'].search([('id','child_of', company_id)])._ids

        self._cr.execute('''SELECT DISTINCT ON(p.id)
            p.id, o.date_order, l.order_id FROM purchase_order_line l
            JOIN purchase_order o ON o.id = l.order_id
            RIGHT OUTER JOIN product_product p ON p.id = l.product_id
            WHERE o.company_id in %s and p.product_tmpl_id IN %s ORDER BY 1, 2 DESC''', (company_ids, tuple(ids),))
 
        fetch = self._cr.fetchall()
        for pid, odate, order_id in fetch:
            for s in self:
                if s.id == pid:
                    s.last_order = odate
                    s.last_order_id = order_id  

    def search_last_order_id(self, operator, value):
        if value == False:
            company_id  = self.env.user.company_id._ids
            company_ids = self.env['res.company'].search([('id','child_of', company_id)])._ids
            
            str_company = "("
            for c in company_ids:
                str_company += str(c) + ","
                
            str_company = str_company[:-1]
            str_company += ")"

            self._cr.execute('''select pp.product_tmpl_id from stock_picking sp
                                join stock_move sm on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sm.company_id in %s and sl_dest.usage = 'production' and sp.state = 'done'
                                group by pp.product_tmpl_id''' %(str_company,))

            
            datas = self._cr.fetchall()
            products = [data for data in datas]
            res_opr = 'in'
            if operator == '=':
                res_opr = 'not in'
            return [('id', res_opr, products)]
        else:
            products = []
            for product in self.env['product.template'].search([('active','=',True)]):
                self._cr.execute('''select sp.date_transfer from stock_move sm
                                join stock_picking sp on sp.id = sm.picking_id
                                join product_product pp on pp.id = sm.product_id
                                join stock_location sl_dest on sl_dest.id = sm.location_dest_id
                                where sl_dest.usage = 'production' and sp.state = 'done' and pp.product_tmpl_id = %s
                                order by sp.date_transfer desc limit 1''', (product.id,))
                
                date_transfer = False
                datas = self._cr.fetchall()
                for data in datas:
                    date_transfer = data[0]
                
                if date_transfer:
                    if operator == '>' and date_transfer > value:
                        products.append(product.id)
                    elif operator == '<' and date_transfer < value:
                        products.append(product.id)
                    elif operator == '>=' and date_transfer >= value:
                        products.append(product.id)
                    elif operator == '<=' and date_transfer <= value:
                        products.append(product.id)
                    elif operator == '=' and date_transfer == value:
                        products.append(product.id)
                    elif operator == '!=' and date_transfer != value:
                        products.append(product.id)
            return [('id', 'in', products)]                  