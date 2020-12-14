# -*- coding: utf-8 -*-
{
    "name": "KA Purchase",
     'description': """
Module Purchasing yang di sesuaikan dengan kebutuhan PT. Kebon Agung.
Yang dapat mendukung hutang piutang atas PG: 

- Create PO Direksi --> Create PO dan Penerimaan di PG
    """,
	"version": "1.01",
    "author": "PT. Kebon Agung",
    "license": "AGPL-3",
    "category": "Purchases",
    "website": "www.ptkebonagung.com",
    "depends": ["ka_base",
				"ka_logistik_spm",
                "product",
                "purchase", 
                "ka_account", 
                "stock_account", 
                "amount_to_text_id",
                "ka_hr_pegawai"
                ],
    "data": [
        "report/account_report.xml",
		"report/purchase_order_templates.xml",
        "wizard/rekap_sp_wizard.xml",
        "wizard/logistik_sp_cancel.xml",
        "wizard/account_invoice_merge.xml",
        "wizard/purchase_edit_wizard_view.xml",
        "wizard/product_uom_edit_wizard.xml",
        "report/report_rekap_sp.xml",
        "report/tmpl_rekap_sp.xml",
        "report/account_report.xml",
        "report/report_ntb.xml",
        'report/sp.xml',
        'report/sp_konsep.xml',
        'report/sp_sementara.xml',
        'report/sp_tandaterima.xml',
        'report/deleted_report.xml',
        'report/report_ntb_factory.xml',
        "views/purchase_view.xml",
        "views/product_template_view.xml",
        "views/account_invoice_view.xml",
        "views/account_invoice_translate_view.xml",
        "views/account_view.xml",
        "views/stock_view.xml",
        "views/res_partner_view.xml",
        "views/logistik_spm_view.xml",
        "views/res_partner_translate.xml",
        # "views/purchase_translation.xml",
        "security/ir.model.access.csv",
        ],
    'installable': True,
}