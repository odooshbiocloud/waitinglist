# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    """Extend users with waiting list preferences"""
    
    _inherit = 'res.users'
    
    # Last used POS and Floor for waiting list
    last_waiting_list_pos_id = fields.Many2one(
        'pos.config',
        string='Last Used POS',
        domain="[('module_pos_restaurant', '=', True)]",
        help='Last POS configuration used when creating waiting list entries'
    )
    
    last_waiting_list_floor_id = fields.Many2one(
        'restaurant.floor',
        string='Last Used Floor',
        help='Last floor used when creating waiting list entries'
    )
    
    def action_clear_waiting_list_preferences(self):
        """Clear saved waiting list preferences"""
        self.ensure_one()
        self.write({
            'last_waiting_list_pos_id': False,
            'last_waiting_list_floor_id': False,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preferences Cleared'),
                'message': _('Waiting list preferences have been reset.'),
                'type': 'success',
                'sticky': False,
            }
        }
