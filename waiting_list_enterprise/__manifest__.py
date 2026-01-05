{
    'name': 'Waiting List Enterprise',
    'version': '18.0.1.21.0',
    'summary': 'Advanced waiting list features for Enterprise/Odoo.sh',
    'description': """
Restaurant Waiting List System - Enterprise Extensions
======================================================

Advanced features for Enterprise Edition and Odoo.sh:

* VIP and repeat customer prioritization
* Full POS Restaurant integration
* Advanced table management with floor layouts
* Real-time SMS and WhatsApp notifications
* Advanced analytics and reporting
* Restaurant-specific workflows
* Enterprise-only features

This module extends waiting_list_base with Enterprise-specific functionality.
Requires Odoo Enterprise or Odoo.sh.

WhatsApp Integration:
--------------------
Uses Odoo Enterprise WhatsApp module for customer notifications.
Configure WhatsApp Business Account in Settings > Technical > WhatsApp.
""",
    'author': 'Mazen',
    'website': 'https://www.odoo.com',
    'category': 'Sales/Point Of Sale',
    'depends': [
        'waiting_list_base',  # Base module
        'pos_restaurant',     # Enterprise module
        'base_setup',         # For configuration settings
        'sms',                # SMS messaging (optional but recommended)
    ],
    'data': [
        # Security
        'security/waiting_list_notification_security.xml',
        'security/ir.model.access.csv',
        
        # Views
        'views/waiting_list_views.xml',
        'views/waiting_list_notification_views.xml',
        'views/restaurant_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_actions.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'point_of_sale.assets': [
            'waiting_list_enterprise/static/src/**/*',
        ],
        'web.assets_backend': [
            'waiting_list_enterprise/static/src/js/enterprise_dashboard.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OEEL-1',  # Enterprise license
    'price': 499.00,
    'currency': 'USD',
    'external_dependencies': {},
}