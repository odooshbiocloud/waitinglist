# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WaitingListAllergen(models.Model):
    """Master list of allergen types for customer safety tracking"""
    
    _name = 'waiting.list.allergen'
    _description = 'Allergen Type'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Allergen Name',
        required=True,
        translate=True,
        help='Name of the allergen (e.g., Dairy, Nuts, Gluten)'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of the allergen and what it includes'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of display in allergen lists'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide this allergen without deleting it'
    )
    
    color = fields.Integer(
        string='Color Index',
        default=0,
        help='Color for tag display in Odoo interface (0-10)'
    )
    
    icon = fields.Char(
        string='Icon',
        default='⚠️',
        help='Emoji or icon to display with this allergen'
    )
    
    # Computed field for display name with icon
    display_name_with_icon = fields.Char(
        string='Display Name',
        compute='_compute_display_name_with_icon'
    )
    
    @api.depends('name', 'icon')
    def _compute_display_name_with_icon(self):
        """Combine icon and name for display"""
        for allergen in self:
            if allergen.icon:
                allergen.display_name_with_icon = f"{allergen.icon} {allergen.name}"
            else:
                allergen.display_name_with_icon = allergen.name
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Allergen name must be unique!')
    ]
