from odoo import models, fields, api
from datetime import datetime
import time
from odoo.exceptions import UserError

class KAStockInventoryPriceAdjustment(models.Model):
    _name           = "ka_stock.inventory.price.adjustment"
    _description    = "Stock standard price adjustment and auto create journal"
    _inherit        = ['mail.thread']
    _order          = 'date desc, id desc'
    
    @api.model
    def _compute_default_location(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    name            = fields.Char(string="Reference", copy=False)
    date            = fields.Date(string="Tanggal", default=fields.Datetime.now, track_visibility="onchange")
    state           = fields.Selection([("draft", "Draft"),
                              ("confirm", "In Progress"),
                              ("done", "Validated"),
                              ("cancel", "Cancelled")],
                                string = "Status", default="draft", track_visibility="onchange", copy=False)

    line_ids        = fields.One2many("inventory.price.adjustment.line", "price_adjustment_id", string="Products", states={'confirm':[('readonly',True)]})
    location_id     = fields.Many2one("stock.location", string="Inventoried Location", default=_compute_default_location, track_visibility="onchange")
    company_id      = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id, track_visibility="onchange")
    accounting_date = fields.Date(string="Force Accounting", default=fields.Datetime.now, track_visibility="onchange")
    journal_ids     = fields.One2many("account.move", "price_adjustment_id", string="Journals")

    def action_confirm(self):
        self.state = "confirm"
    
    def action_to_draft(self):
        self.state = "draft"

    def action_process(self):

        #add journal items
        line_items  = []
        jumlah_deb  = 0
        jumlah_kred = 0
        for x in self.line_ids:
            if x.product_id.categ_id == False:
                raise UserError('Product category pada '+ x.product_id.display_name + 'tidak ditemukan!')
            else:
                if x.product_id.categ_id.property_stock_account_input_categ_id == False or \
                    x.product_id.categ_id.property_stock_account_output_categ_id == False:

                    raise UserError('Jurnal masuk/keluar pada category product '+ x.product_id.categ_id + 'tidak ditemukan!')


            if x.difference < 0:
                jumlah_kred =+ x.difference
                vals = (0,0,{
                            'account_id':x.product_id.categ_id.property_stock_account_output_categ_id.id,
                            'name':x.product_id.display_name,
                            'debit':0,
                            'credit':abs(x.difference)
                        })
            elif x.difference > 0:
                jumlah_deb =+ x.difference
                vals = (0,0,{
                            'account_id':x.product_id.categ_id.property_stock_account_input_categ_id.id,
                            'name':x.product_id.display_name,
                            'debit':abs(x.difference),
                            'credit':0,
                        })

            line_items.append(vals)

            # set new standard price
            x.product_id.standard_price = x.standard_price_new
        
        #add opposite journal items
        #-------------Search for Configuration Journal-------------
        config = self.env['ka_stock.inventory.price.adjustment.configuration'].search(['company_id','=',self.company_id.id])

        last_vals1 = (0,0,{
                        'account_id':1463,
                        'name':'Jurnal balik price adjustment : '+self.name,
                        'debit':abs(jumlah_kred),
                        'credit':0,
                    })

        line_items.append(last_vals1)

        last_vals2 = (0,0,{
                        'account_id':1463,
                        'name':'Jurnal balik price adjustment : '+self.name,
                        'debit':0,
                        'credit':abs(jumlah_deb),
                    })

        line_items.append(last_vals2)
        line_items.reverse()

        #create journal
        data = {
            'price_adjustment_id':self.id,
            'journal_id':self.env['account.journal'].search([('name','=','Stock Journal'), ('company_id','=', self.env.user.company_id.id)]).id,
            'date':datetime.now(),
            'ref':'Price adjustment : '+self.name,
            'company_id':self.env.user.company_id.id,
            'line_ids': line_items,
        }

        if self.accounting_date:
            data['date'] = self.accounting_date

        new_journal = self.env['account.move'].create(data)
        new_journal.post()

        self.state = 'done'

    def action_view_journal_price_adjustment(self):
        """To open `account.move (journal entries)`.

        Returns:
            Dict -- Action result.
        """
        if len(self.journal_ids) == 1:
            return {
                'name': 'Journal Entry',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id' : self.journal_ids[0].id,
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'target': 'current',  
            }
        else:
            action = self.env.ref('account.action_move_journal_line')
            result = action.read()[0]
            result['domain'] = [('price_adjustment_id', '=', self.id)]
            result['context'] = {
                'default_price_adjustment_id': self.id
            }
            return result



class KAStockInventoryPriceAdjustmentLine(models.Model):
    _name           = "inventory.price.adjustment.line"
    _description    = "Inventory Price Adjustment Line"
    _inherit        = ['mail.thread']

    price_adjustment_id = fields.Many2one("ka_stock.inventory.price.adjustment")
    product_id          = fields.Many2one("product.product", string="Product")
    product_description = fields.Text(string="Spesifikasi", related="product_id.description")
    product_qty         = fields.Float(string="Qty", related="product_id.qty_available")
    standard_price      = fields.Float(string="Harga", compute="_compute_old_product_value", store=True)
    product_value       = fields.Float(string="Valuasi", compute="_compute_old_product_value")
    standard_price_new  = fields.Float(string="Harga Baru")
    product_value_new   = fields.Float(string="Valuasi Baru", compute="_compute_new_product_value")
    difference          = fields.Float(string="Selisih")
    location_id         = fields.Many2one("stock.location", string="Inventoried Location", related="price_adjustment_id.location_id", track_visibility="always")
    company_id          = fields.Many2one("res.company", string="Company", related="price_adjustment_id.company_id", track_visibility="always")

    @api.depends('product_id')
    @api.onchange('product_id')
    def _compute_old_product_value(self):
        for line in self:
            line.standard_price = line.product_id.standard_price
            line.product_value = line.product_qty*line.standard_price

    @api.depends('product_id','standard_price_new')
    @api.onchange('product_id','standard_price_new')
    def _compute_new_product_value(self):
        for line in self:
            line.product_value_new = line.product_qty*line.standard_price_new

    @api.depends('product_value','product_value_new')
    @api.onchange('product_value','product_value_new')
    def _compute_difference(self):
        for line in self:
            line.difference = line.product_value_new-line.product_value

class KAAccountMovePriveAdjustment(models.Model):
    _inherit        = ['account.move']

    price_adjustment_id = fields.Many2one("ka_stock.inventory.price.adjustment", string="Price Adjustment")