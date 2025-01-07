odoo.define('contribution.Dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var _t = core._t;

    var ContributionDashboard = AbstractAction.extend({
        template: 'contribution_dashboard_template',
        events: {
            'click .o_refresh_dashboard': '_onRefreshDashboard',
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.dashboardData = {};
            this.charts = {};
        },

        willStart: function() {
            var self = this;
            return $.when(
                this._super.apply(this, arguments),
                this._loadDashboardData()
            );
        },

        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                self._renderCharts();
                self._setupRefreshTimer();
            });
        },

        _loadDashboardData: function() {
            var self = this;
            return rpc.query({
                model: 'contribution.goal',
                method: 'get_dashboard_data',
                args: []
            }).then(function(result) {
                self.dashboardData = result;
            });
        },

        _renderCharts: function() {
            this._renderGoalProgressChart();
            this._renderContributionTrendChart();
        },

        _renderGoalProgressChart: function() {
            var ctx = this.$('#goalProgressChart')[0].getContext('2d');
            if (this.charts.goalProgress) {
                this.charts.goalProgress.destroy();
            }

            this.charts.goalProgress = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: this.dashboardData.goals.map(g => g.name),
                    datasets: [{
                        data: this.dashboardData.goals.map(g => g.progress),
                        backgroundColor: [
                            '#875A7B',
                            '#00A09D',
                            '#F06050',
                            '#F4A460',
                            '#40E0D0'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        position: 'right'
                    }
                }
            });
        },

        _renderContributionTrendChart: function() {
            var ctx = this.$('#contributionTrendChart')[0].getContext('2d');
            if (this.charts.contributionTrend) {
                this.charts.contributionTrend.destroy();
            }

            this.charts.contributionTrend = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.dashboardData.trends.labels,
                    datasets: [{
                        label: _t('Contributions'),
                        data: this.dashboardData.trends.data,
                        borderColor: '#875A7B',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    }
                }
            });
        },

        _setupRefreshTimer: function() {
            var self = this;
            setInterval(function() {
                self._loadDashboardData().then(function() {
                    self._renderCharts();
                });
            }, 300000); // Refresh every 5 minutes
        },

        _onRefreshDashboard: function(ev) {
            ev.preventDefault();
            this._loadDashboardData().then(this._renderCharts.bind(this));
        },

        destroy: function() {
            Object.values(this.charts).forEach(chart => chart.destroy());
            this._super.apply(this, arguments);
        }
    });

    core.action_registry.add('contribution_dashboard', ContributionDashboard);

    return ContributionDashboard;
});
