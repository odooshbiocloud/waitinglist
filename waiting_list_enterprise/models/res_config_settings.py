# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Wait Time Calculation Settings
    waiting_list_queue_time_per_person = fields.Integer(
        string='Time per Person in Queue (minutes)',
        default=1,
        config_parameter='waiting_list_enterprise.queue_time_per_person',
        help='Minutes added to wait time for each person ahead in queue (default: 1)'
    )
    
    waiting_list_simple_time_per_person = fields.Integer(
        string='Simple Estimate: Time per Person (minutes)',
        default=1,
        config_parameter='waiting_list_enterprise.simple_time_per_person',
        help='Minutes per person in simple queue calculation when no historical data (default: 1)'
    )
    
    waiting_list_minimum_wait_time = fields.Integer(
        string='Minimum Wait Time (minutes)',
        default=10,
        config_parameter='waiting_list_enterprise.minimum_wait_time',
        help='Minimum wait time when there is a queue (default: 10)'
    )
    
    waiting_list_maximum_wait_time = fields.Integer(
        string='Maximum Wait Time (minutes)',
        default=60,
        config_parameter='waiting_list_enterprise.maximum_wait_time',
        help='Maximum wait time ceiling to prevent unrealistic estimates (default: 60)'
    )
    
    waiting_list_large_party_multiplier = fields.Float(
        string='Large Party Multiplier (>6 guests)',
        default=1.5,
        config_parameter='waiting_list_enterprise.large_party_multiplier',
        help='Wait time multiplier for parties larger than 6 guests (default: 1.5x)'
    )
    
    waiting_list_medium_party_multiplier = fields.Float(
        string='Medium Party Multiplier (>4 guests)',
        default=1.2,
        config_parameter='waiting_list_enterprise.medium_party_multiplier',
        help='Wait time multiplier for parties larger than 4 guests (default: 1.2x)'
    )
    
    waiting_list_large_party_threshold = fields.Integer(
        string='Large Party Threshold',
        default=6,
        config_parameter='waiting_list_enterprise.large_party_threshold',
        help='Party size considered "large" for wait time calculation (default: 6)'
    )
    
    waiting_list_medium_party_threshold = fields.Integer(
        string='Medium Party Threshold',
        default=4,
        config_parameter='waiting_list_enterprise.medium_party_threshold',
        help='Party size considered "medium" for wait time calculation (default: 4)'
    )
    
    waiting_list_historical_days = fields.Integer(
        string='Historical Data Analysis Period (days)',
        default=7,
        config_parameter='waiting_list_enterprise.historical_days',
        help='Number of days to look back for historical wait time analysis (default: 7)'
    )
    
    waiting_list_hour_tolerance = fields.Integer(
        string='Hour Matching Tolerance (hours)',
        default=1,
        config_parameter='waiting_list_enterprise.hour_tolerance',
        help='Hour tolerance for matching historical data (±hours, default: 1)'
    )
