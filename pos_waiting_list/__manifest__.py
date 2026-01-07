{
    'name': 'POS Waiting List',
    'version': '19.0.1.0.0',
    'summary': 'Core waiting list functionality with allergen tracking and survey integration (Community compatible)',
    'description': """
Restaurant Waiting List System - Base Module
=============================================

Core waiting list management for restaurants (Community Edition compatible):

* Customer waiting list management with basic queue
* Simple table assignment
* Customer information tracking
* **Allergen Management & Safety Tracking**
* Customer allergen profiles with auto-population
* Visual allergen alerts and warnings
* Bilingual allergen support (English/Arabic)
* Basic reporting
* Multi-company support
* Community Edition compatible

This is the base module that works with Odoo Community Edition.
For advanced features (VIP priority, restaurant integration, etc.),
install the pos_waiting_list_enterprise module.
""",
    'author': 'Mazen',
    'website': 'https://www.odoo.com',
    'category': 'Sales',
    'depends': [
        'base',
        'mail',
        'survey',
    ],
    'data': [
        # Security
        'security/waiting_list_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ir_sequence_data.xml',
        'data/customer_categories.xml',
        'data/waiting_list_allergen_data.xml',
        
        # Views
        'views/dashboard_views.xml',
        'views/waiting_list_views.xml',
        'views/waiting_list_allergen_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/waiting_list_customer_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pos_waiting_list/static/src/scss/waiting_list.scss',
            'pos_waiting_list/static/src/js/dashboard.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'price': 199.00,
    'currency': 'USD',
    'images': ['static/description/banner.png'],
}