# -*- coding: utf-8 -*-

from odoo import models


class WhatsAppComposer(models.TransientModel):
    _inherit = 'whatsapp.composer'

    def _get_records_based_on_model(self):
        """Add support for waiting.list model"""
        if self._context.get('active_model') == 'waiting.list':
            return self.env['waiting.list'].browse(self._context.get('active_id'))
        return super()._get_records_based_on_model()
