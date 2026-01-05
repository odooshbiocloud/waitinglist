# -*- coding: utf-8 -*-

from odoo import models, api


class WhatsAppTemplate(models.Model):
    _inherit = 'whatsapp.template'

    @api.model
    def _get_model_field_mapping(self):
        """Add waiting.list model field mappings"""
        res = super()._get_model_field_mapping()
        res['waiting.list'] = {
            'customer_id': 'customer_id.name',
            'name': 'name',
            'display_name': 'display_name',
            'party_size': 'party_size',
            'table_id': 'table_id.name',
            'floor_id': 'floor_id.name',
            'estimated_wait_time': 'estimated_wait_time',
            'company_id': 'company_id.name',
        }
        return res
