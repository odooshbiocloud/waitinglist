# -*- coding: utf-8 -*-

from odoo import models, _


class WaitingList(models.Model):
    _inherit = 'waiting.list'

    def _get_whatsapp_safe_fields(self):
        """Define safe fields for WhatsApp template variables"""
        return {
            'customer_id.name',
            'name',
            'display_name',
            'party_size',
            'table_id.display_name',
            'floor_id.name',
            'estimated_wait_time',
            'company_id.name',
            'company_id.phone',
            'company_id.mobile',
        }

    def action_send_whatsapp(self):
        """Open WhatsApp composer for manual message"""
        self.ensure_one()
        return {
            'name': _('Send WhatsApp'),
            'view_mode': 'form',
            'res_model': 'whatsapp.composer',
            'type': 'ir.actions.act_window',
            'context': {
                'default_res_model': 'waiting.list',
                'default_res_id': self.id,
                'active_model': 'waiting.list',
                'active_id': self.id,
            },
            'target': 'new'
        }
