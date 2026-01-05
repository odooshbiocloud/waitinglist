# -*- coding: utf-8 -*-

{
    'name': 'WhatsApp - Waiting List',
    'version': '18.0.1.2.0',
    'category': 'WhatsApp',
    'summary': 'Send WhatsApp notifications for waiting list updates',
    'description': """
WhatsApp Integration for Restaurant Waiting List
=================================================

This module integrates the Restaurant Waiting List system with WhatsApp,
allowing automatic sending of notifications via WhatsApp for:

* Table Ready notifications
* Cancellation notices
* No-show alerts
* Survey/feedback requests
* Custom notifications

Features:
---------
* WhatsApp template configuration per notification type
* Automatic WhatsApp sending from notification queue
* Bilingual support (English/Arabic)
* Integration with waiting.list.notification model
* Configuration settings for templates
* Fallback to SMS if WhatsApp fails
    """,
    'author': 'Mazen',
    'website': 'https://www.odoo.com',
    'depends': [
        'whatsapp',
        'waiting_list_enterprise',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/whatsapp_template_data.xml',
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
        'views/waiting_list_notification_views.xml',
        'views/waiting_list_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OEEL-1',
    'price': 150.00,
    'currency': 'USD',
}
