# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import json
import logging

_logger = logging.getLogger(__name__)


class WaitingListSpreadsheet(models.Model):
    """Spreadsheet analytics for waiting list system"""
    
    _name = 'waiting.list.spreadsheet'
    _description = 'Waiting List Spreadsheet Analytics'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Dashboard Name', required=True, default='Waiting List Analytics')
    dashboard_id = fields.Many2one('spreadsheet.dashboard', string='Spreadsheet Dashboard', ondelete='cascade')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Date range for analysis
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    
    # Analytics data (computed)
    total_entries = fields.Integer(string='Total Entries', compute='_compute_analytics')
    avg_wait_time = fields.Float(string='Avg Wait Time (min)', compute='_compute_analytics')
    no_show_rate = fields.Float(string='No-Show Rate (%)', compute='_compute_analytics')
    satisfaction_score = fields.Float(string='Avg Satisfaction', compute='_compute_analytics')
    total_spends = fields.Monetary(string='Total Spends', compute='_compute_analytics', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    @api.depends('date_from', 'date_to')
    def _compute_analytics(self):
        """Compute key analytics metrics"""
        for record in self:
            domain = [
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to),
            ]
            
            entries = self.env['waiting.list'].search(domain)
            record.total_entries = len(entries)
            
            if entries:
                # Average wait time (only for seated/done)
                completed = entries.filtered(lambda e: e.status in ('seated', 'done') and e.actual_wait_time > 0)
                record.avg_wait_time = sum(completed.mapped('actual_wait_time')) / len(completed) if completed else 0
                
                # No-show rate
                no_shows = entries.filtered(lambda e: e.status == 'no_show')
                record.no_show_rate = (len(no_shows) / len(entries)) * 100 if entries else 0
                
                # Satisfaction score
                rated = entries.filtered(lambda e: e.customer_satisfaction)
                if rated:
                    scores = [int(r.customer_satisfaction) for r in rated]
                    record.satisfaction_score = sum(scores) / len(scores)
                else:
                    record.satisfaction_score = 0
                
                # Total spends (from average_spend_per_visit if available)
                entries_with_spend = entries.filtered(lambda e: hasattr(e, 'average_spend_per_visit') and e.average_spend_per_visit)
                record.total_spends = sum(entries_with_spend.mapped('average_spend_per_visit')) if entries_with_spend else 0
            else:
                record.avg_wait_time = 0
                record.no_show_rate = 0
                record.satisfaction_score = 0
                record.total_spends = 0
    
    @api.model
    def _create_default_template(self):
        """Create default spreadsheet template during module installation"""
        _logger.info("Creating default Waiting List Spreadsheet template...")
        
        # Check if template already exists
        existing = self.search([('name', '=', 'Waiting List Analytics Dashboard')], limit=1)
        if existing:
            _logger.info("Default template already exists, skipping creation.")
            return existing
        
        # Create spreadsheet dashboard
        dashboard_data = self._get_default_dashboard_data()
        
        try:
            dashboard = self.env['spreadsheet.dashboard'].create({
                'name': 'Waiting List Analytics',
                'dashboard_group_id': self._get_or_create_dashboard_group().id,
                'spreadsheet_data': json.dumps(dashboard_data),
            })
            
            # Create spreadsheet record
            spreadsheet = self.create({
                'name': 'Waiting List Analytics Dashboard',
                'dashboard_id': dashboard.id,
            })
            
            _logger.info(f"Created default spreadsheet template: {spreadsheet.name}")
            return spreadsheet
            
        except Exception as e:
            _logger.error(f"Failed to create default spreadsheet template: {str(e)}")
            return False
    
    @api.model
    def _get_or_create_dashboard_group(self):
        """Get or create dashboard group for waiting list"""
        group = self.env['spreadsheet.dashboard.group'].search([
            ('name', '=', 'Waiting List Reports')
        ], limit=1)
        
        if not group:
            group = self.env['spreadsheet.dashboard.group'].create({
                'name': 'Waiting List Reports',
                'sequence': 10,
            })
        
        return group
    
    @api.model
    def _get_default_dashboard_data(self):
        """Generate default spreadsheet structure with pivots and charts"""
        
        # Get waiting list pivot definitions
        pivots = self._get_pivot_definitions()
        charts = self._get_chart_definitions()
        
        return {
            'version': 18,
            'sheets': [
                {
                    'id': 'sheet1',
                    'name': 'Dashboard',
                    'colNumber': 26,
                    'rowNumber': 100,
                    'cells': self._get_dashboard_cells(),
                    'merges': [],
                    'pivots': pivots,
                    'charts': charts,
                }
            ],
            'pivots': pivots,
            'charts': charts,
        }
    
    @api.model
    def _get_pivot_definitions(self):
        """Define pivot tables for analytics"""
        return {
            'status_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [],
                'measures': [{'field': 'id', 'operator': 'count'}],
                'colGroupBys': ['status'],
                'rowGroupBys': [],
                'context': {},
            },
            'hourly_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [],
                'measures': [{'field': 'id', 'operator': 'count'}],
                'colGroupBys': ['create_date:hour'],
                'rowGroupBys': [],
                'context': {},
            },
            'wait_time_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [('status', 'in', ['seated', 'done'])],
                'measures': [{'field': 'actual_wait_time', 'operator': 'avg'}],
                'colGroupBys': ['create_date:day'],
                'rowGroupBys': [],
                'context': {},
            },
            'table_usage_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [('table_id', '!=', False)],
                'measures': [{'field': 'id', 'operator': 'count'}],
                'colGroupBys': ['table_id'],
                'rowGroupBys': [],
                'context': {},
            },
            'party_size_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [],
                'measures': [{'field': 'id', 'operator': 'count'}],
                'colGroupBys': ['party_size'],
                'rowGroupBys': [],
                'context': {},
            },
            'satisfaction_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [('customer_satisfaction', '!=', False)],
                'measures': [{'field': 'id', 'operator': 'count'}],
                'colGroupBys': ['customer_satisfaction'],
                'rowGroupBys': [],
                'context': {},
            },
            'daily_comparison_pivot': {
                'type': 'ODOO',
                'model': 'waiting.list',
                'domain': [],
                'measures': [
                    {'field': 'id', 'operator': 'count'},
                    {'field': 'actual_wait_time', 'operator': 'avg'}
                ],
                'colGroupBys': ['create_date:day'],
                'rowGroupBys': ['status'],
                'context': {},
            },
        }
    
    @api.model
    def _get_chart_definitions(self):
        """Define charts for the dashboard"""
        return [
            {
                'id': 'chart_status',
                'type': 'pie',
                'title': 'Status Distribution',
                'dataSets': ['status_pivot'],
                'labelRange': 'Dashboard!A1',
                'background': '#FFFFFF',
            },
            {
                'id': 'chart_hourly',
                'type': 'bar',
                'title': 'Hourly Entry Trends',
                'dataSets': ['hourly_pivot'],
                'labelRange': 'Dashboard!A10',
                'background': '#FFFFFF',
            },
            {
                'id': 'chart_wait_time',
                'type': 'line',
                'title': 'Average Wait Time by Day',
                'dataSets': ['wait_time_pivot'],
                'labelRange': 'Dashboard!A20',
                'background': '#FFFFFF',
            },
            {
                'id': 'chart_tables',
                'type': 'bar',
                'title': 'Table Utilization',
                'dataSets': ['table_usage_pivot'],
                'labelRange': 'Dashboard!A30',
                'background': '#FFFFFF',
            },
            {
                'id': 'chart_party_size',
                'type': 'pie',
                'title': 'Party Size Distribution',
                'dataSets': ['party_size_pivot'],
                'labelRange': 'Dashboard!A40',
                'background': '#FFFFFF',
            },
            {
                'id': 'chart_satisfaction',
                'type': 'bar',
                'title': 'Customer Satisfaction',
                'dataSets': ['satisfaction_pivot'],
                'labelRange': 'Dashboard!A50',
                'background': '#FFFFFF',
            },
        ]
    
    @api.model
    def _get_dashboard_cells(self):
        """Define cell content for the dashboard"""
        return {
            'A1': {'content': 'Waiting List Analytics Dashboard', 'style': 1},
            'A2': {'content': 'Last 30 Days Performance', 'style': 2},
            
            # KPIs
            'A4': {'content': 'Total Entries'},
            'B4': {'content': '=ODOO.PIVOT("status_pivot", "measure", "count")'},
            
            'A5': {'content': 'Avg Wait Time'},
            'B5': {'content': '=ODOO.PIVOT("wait_time_pivot", "measure", "avg") & " min"'},
            
            'A6': {'content': 'No-Show Rate'},
            'B6': {'content': '=ODOO.PIVOT.HEADER("status_pivot", "no_show") / ODOO.PIVOT("status_pivot", "measure", "count") * 100 & "%"'},
            
            # Chart placeholders
            'A10': {'content': 'Hourly Trends'},
            'A20': {'content': 'Wait Time Analysis'},
            'A30': {'content': 'Table Usage'},
            'A40': {'content': 'Party Sizes'},
            'A50': {'content': 'Satisfaction Scores'},
        }
    
    def action_open_dashboard(self):
        """Open the spreadsheet dashboard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'action_spreadsheet_dashboard',
            'params': {
                'dashboard_id': self.dashboard_id.id,
            },
        }
    
    def action_refresh_data(self):
        """Refresh analytics data"""
        self.ensure_one()
        self._compute_analytics()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Dashboard data refreshed successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model
    def get_performance_summary(self, date_from=None, date_to=None):
        """Get performance summary for API/external use"""
        if not date_from:
            date_from = fields.Date.today() - timedelta(days=30)
        if not date_to:
            date_to = fields.Date.today()
        
        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ]
        
        entries = self.env['waiting.list'].search(domain)
        
        return {
            'total_entries': len(entries),
            'status_breakdown': {
                status: len(entries.filtered(lambda e: e.status == status))
                for status in ['waiting', 'ready', 'called', 'seated', 'done', 'cancelled', 'no_show']
            },
            'avg_wait_time': sum(e.actual_wait_time for e in entries if e.actual_wait_time > 0) / len(entries) if entries else 0,
            'avg_party_size': sum(entries.mapped('party_size')) / len(entries) if entries else 0,
            'vip_count': len(entries.filtered(lambda e: e.is_vip)),
            'allergen_count': len(entries.filtered(lambda e: e.has_allergens)),
        }
