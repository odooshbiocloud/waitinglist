# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Add birthday columns to res_partner and waiting_list tables"""
    _logger.info('Adding birthday field to res_partner table')
    
    # Add birthday to res_partner if not exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='res_partner' AND column_name='birthday'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE res_partner 
            ADD COLUMN birthday DATE
        """)
        _logger.info('Birthday column added to res_partner')
    else:
        _logger.info('Birthday column already exists in res_partner')
    
    # Add customer_birthday to waiting_list if not exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='waiting_list' AND column_name='customer_birthday'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE waiting_list 
            ADD COLUMN customer_birthday DATE
        """)
        _logger.info('customer_birthday column added to waiting_list')
    else:
        _logger.info('customer_birthday column already exists in waiting_list')
