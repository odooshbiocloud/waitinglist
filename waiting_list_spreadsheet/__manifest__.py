# -*- coding: utf-8 -*-
{
    'name': 'Waiting List Spreadsheet Analytics',
    'version': '18.0.1.0.0',
    'summary': 'Advanced spreadsheet analytics for waiting list with historical trends',
    'description': """
Waiting List Spreadsheet Analytics
===================================

Comprehensive spreadsheet-based analytics dashboard for the waiting list system.

Features:
---------
* Historical trend analysis (7 days, 30 days, custom ranges)
* Performance metrics and KPIs
* Status distribution and flow analysis
* Table utilization heatmaps
* Customer analytics and satisfaction trends
* Peak hour identification
* Wait time optimization insights
* Multi-company/branch filtering
* VIP customer tracking
* Export to Excel with live charts
* Manager-only access

Charts Included:
----------------
* Status Distribution (Pie Chart)
* Hourly Entry Trends (Bar Chart)
* Wait Time Analysis (Line Chart)
* Table Utilization (Bar Chart)
* Party Size Distribution (Pie Chart)
* Customer Satisfaction Trends (Line Chart)
* Weekly Comparison (Bar Chart)
* No-Show & Cancellation Rates (Gauge)

Perfect for:
------------
* Restaurant managers analyzing performance
* Operations teams optimizing table turnover
* Customer experience teams tracking satisfaction
* Multi-location restaurant groups

Requires Odoo 18 Enterprise Edition with Spreadsheet Dashboard module.
""",
    'author': 'Mazen',
    'website': 'https://www.odoo.com',
    'category': 'Sales/Point Of Sale',
    'license': 'OEEL-1',
    'depends': [
        'waiting_list_enterprise',  # Enterprise waiting list module
        'spreadsheet_dashboard',    # Odoo 18 Enterprise spreadsheet
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/spreadsheet_template.xml',
        
        # Views
        'views/waiting_list_spreadsheet_views.xml',
        'views/menu_actions.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 100.00,
    'currency': 'USD',
}
