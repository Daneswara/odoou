/**
 * Copyright Cak Juice 2016
 * untuk Nerita - Kebon Agung..
 * Gaween sakkarepmu..
 */

openerp.ka_account = function(instance, local) {
	var _t = instance.web._t,
		_lt = instance.web._lt;
	var QWeb = instance.web.qweb;

	local.userCompany = 0;
	local.templateName = 'financial_report';
	local.modelName = 'accounting.report';
	local.modelId = 1;
	local.statusReady = false;

	local.setInitData = function(self) {
		self.title = 'Financial Report';
		self.icon1 = 'fa fa-calendar-check-o';
		self.icon2 = 'fa fa-calendar-plus-o';
		self.filter1 = 'Bulan';
		self.childFilter1 = [];
		var bulanName = ['-- Semua Bulan --', 'Januari', 'Pebruari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
			'Agustus', 'September', 'Oktober', 'November', 'Desember'];
		
		for (var i=0;i<=12;i++) {
			self.childFilter1.push({li_role: '', li_class: 'child-filter-1', a_href: '#', a_html: bulanName[i], data_index: i})
		}

		self.filter2 = 'Tahun';
		self.childFilter2 = [];
	}

	local.setDefaultFilter = function(self, idxObj, idxFilter) {
		self.$('a.filter-link-'+idxFilter).each(function(index) {
			var dataIndex = parseInt($(this).attr('data-index'));
			if (dataIndex == idxObj) {
				local.linkClicked($(this), idxFilter, self);
				return false;
			}
		});
	}

	local.setStartData = function(self) {
		var d = new Date();
		var bulanIdx = d.getMonth() + 1;
		var tahunIdx = d.getFullYear();
		local.setDefaultFilter(self, bulanIdx, 1);

		var tahun = new instance.web.Model('account.move');
		tahun.call('get_year').then(function(results) {
			self.childFilter2 = JSON.parse(results);
			if (self.childFilter2.length > 0) {
				cf = self.childFilter2;
				for (var i=0;i<cf.length;i++) {
					var obj = '<li class="child-filter-2" role><a data-index="' + cf[i] + '" class="filter-link-2">' + cf[i] + '</a></li>';
					self.$('#ul-dropdown-2').append(obj);
				}

				local.setDefaultFilter(self, tahunIdx, 2);
			}

			result = null;
		});
		
		var user = new instance.web.Model('res.users');
		user.call('get_current_user').then(function(result) {
			result = JSON.parse(result);
			local.userCompany = result.company_id;
				
			var company = new instance.web.Model('res.company');
			company.query(['id', 'name'])
				.all()
				.then(function(results) {
					if (results.length > 1) {
						self.$('#submit-filter-list').append('<button class="btn btn-primary submit-filter" data-company-id="0">KONSOLIDASI</button>');
					}

					if (results.length > 0) {
						$.each(results, function(iterate, item) {
							var obj = ' <button class="btn btn-primary submit-filter" data-company-id="' + item.id + '">' + item.name + '</button>';
							if (results.length > 1) {
								self.$('#submit-filter-list').append(obj);
							}
						});

						local.getDefaultReport(local.userCompany);
					}

					results = null;
					local.statusReady = true;
				});
		});
	}

	local.setEventsData = function(self) {
		return {
			'click .span-caret': function(e) {
				var element = $(e.target);
				if (element.hasClass('fa-caret-down')) {
					element.removeClass('fa-caret-down');
					element.addClass('fa-caret-right');
				} else if (element.hasClass('fa-caret-right')) {
					element.removeClass('fa-caret-right');
					element.addClass('fa-caret-down');
				}
			},
			'click .filter-link-1': function(e) {
				e.preventDefault();
				local.linkClicked($(e.target), 1, self);
			},
			'click .filter-link-2': function(e) {
				e.preventDefault();
				local.linkClicked($(e.target), 2, self);
			},
			'click .submit-filter': function(e) {
				e.preventDefault();
				local.submitClicked($(e.target));
			}
		};
	}

	local.linkClicked = function(obj, idxLink, self) {
		self.$('a.filter-link-' + idxLink).each(function(iterate) {
			if ($(this).hasClass('selected') && $(this) != obj) {
				$(this).removeClass('selected');
			}
		});

		if (!obj.hasClass('selected')) obj.addClass('selected');

		self.$('#dropdown-toggle-' + idxLink).attr('data-index', obj.attr('data-index'));
		self.$('#child-text-' + idxLink).html(obj.html());

		if (local.statusReady && $('.submit-filter').length <= 0) {
			local.getDefaultReport(local.userCompany);
		}
	}

	local.getDefaultReport = function(company) {
		var params = local.getParams();
		params.company = company;
		local.getContent(params);
	}

	local.submitClicked = function(obj) {
		var params = local.getParams();
		params.company = parseInt(obj.attr('data-company-id'));
		local.getContent(params);
	}

	local.getParams = function() {
		var filter1Value = parseInt($('#dropdown-toggle-1').attr('data-index'));
		var filter2Value = parseInt($('#dropdown-toggle-2').attr('data-index'));

		return {
			month: filter1Value,
			year: filter2Value,
		};
	}

	local.getContent = function(params) {
		// if (!params.month || !params.year || !params.company) {
		// 	alert('Data tidak bisa diproses!');
		// 	return;
		// }

		var month = params.month;
		var year = params.year;
		var company = params.company;

		var content = new instance.web.Model('report.account.report_financial');
		$('#report-content').html('<h3>Sedang memuat report...</h3>');
		content.call('get_financial_report', [local.modelName, local.modelId, month, year, company]).then(function(results) {
			var page = $(results).find('div.page');
			if (page && page.length > 0) {
				$('#report-content').html(page[0]);
			} else {
				$('#report-content').html('<h3>Data tidak ditemukan.</h3>');
			}

			params = null;
			page = null;
			results = null;
		});
	}

	local.profitLossReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 9;
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.profitLossReportByStasiun = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 9;
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.balanceSheetReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 42;
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	instance.web.client_actions.add('report.profit_loss_report', 'instance.ka_account.profitLossReport');
	instance.web.client_actions.add('report.profit_loss_report_by_stasiun', 'instance.ka_account.profitLossReportByStasiun');
	instance.web.client_actions.add('report.balance_sheet_report', 'instance.ka_account.balanceSheetReport');
}