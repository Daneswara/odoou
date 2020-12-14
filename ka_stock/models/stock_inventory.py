from odoo import api, fields, models


class Inventory(models.Model):
    _inherit = 'stock.inventory'


    date_start  = fields.Date('Tanggal Entry')
    date_end    = fields.Date('S / D')
    product_ids = fields.Many2one('product.product', related='line_ids.product_id', string='Product')


    @api.multi
    def _get_inventory_lines_values(self):
        # Override methode
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        # case 0: Filter on company
        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)

        # case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)
        # case 2: Filter on One Lot/Serial Number
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)
        # case 3: Filter on One product
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        # case 4: Filter on A Pack
        if self.package_id:
            domain += ' AND package_id = %s'
            args += (self.package_id.id,)
        # case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            #categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            #replace with
            cat_ids = self.env['product.category'].search([('id', 'child_of', self.category_id.id)])
            categ_products = Product.search([('categ_id', 'in', cat_ids._ids)])
            #end replace
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

        self.env.cr.execute("""SELECT product_id, sum(qty) as product_qty, 
                location_id, lot_id as prod_lot_id, package_id, 
                owner_id as partner_id
            FROM stock_quant 
            WHERE %s
            GROUP BY product_id, location_id, lot_id, package_id, partner_id""" % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        if self.exhausted:
            exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
            vals.extend(exhausted_vals)
        return vals


    @api.multi
    def action_print_report_inventory_adjustment(self):
        return self.env['report'].get_action(self, 'ka_stock.template_inventory_adjustment')

class InventoryLine(models.Model):
    _inherit = 'stock.inventory.line'
    _order = "product_code ,inventory_id, location_name, prodlot_name"


    product_description = fields.Text('Spesifikasi', compute='_compute_product_description', strore=True)
    theoretical_value = fields.Float('Nilai Buku', compute='_compute_theoretical_value', store=True)
    difference_qty = fields.Float(string='Selisih', compute='_compute_difference_qty_price',store=True)
    product_standard_price = fields.Float('Harga', compute='_compute_theoretical_value', store=True)
    product_value = fields.Float('Nilai Opname', compute='_compute_difference_qty_price', store=True)
    difference_value = fields.Float(string='Selisih', compute='_compute_difference_qty_price',store=True)

    @api.multi
    @api.depends('product_id')
    def _compute_theoretical_value(self):
        for this in self:
            product_price = this.product_id.standard_price
            this.product_standard_price = product_price
            this.theoretical_value = this.theoretical_qty * product_price

    @api.multi
    @api.depends('product_id')
    def _compute_product_description(self):
        for this in self:
            this.product_description = this.product_id.description

    @api.multi
    @api.depends('product_qty')
    def _compute_difference_qty_price(self):
        for this in self:
            product_price = this.product_id.standard_price
            this.product_value = this.product_qty * product_price
            this.difference_qty = this.product_qty - this.theoretical_qty
            this.difference_value = this.difference_qty * product_price


