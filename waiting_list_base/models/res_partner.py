# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Flag for POS and Waiting List customers
    is_waiting_list_customer = fields.Boolean(
        string='Is Waiting List/POS Customer',
        default=False,
        help='Automatically set to True when customer is added via waiting list or POS'
    )
    
    # Birthday field for customer
    birthday = fields.Date(
        string='Birthday',
        help='Customer birthday for special occasions and marketing'
    )
    
    waiting_list_ids = fields.One2many(
        'waiting.list', 
        'customer_id', 
        string='Waiting List Entries'
    )
    
    # Statistics fields
    waiting_list_count = fields.Integer(
        string='Total Visits',
        compute='_compute_waiting_list_stats',
        store=True
    )
    
    last_visit_date = fields.Datetime(
        string='Last Visit',
        compute='_compute_waiting_list_stats',
        store=True
    )
    
    no_show_count = fields.Integer(
        string='No Shows',
        compute='_compute_waiting_list_stats',
        store=True
    )
    
    cancelled_count = fields.Integer(
        string='Cancellations',
        compute='_compute_waiting_list_stats',
        store=True
    )
    
    # Allergen Management Fields
    allergen_ids = fields.Many2many(
        'waiting.list.allergen',
        'partner_allergen_rel',
        'partner_id',
        'allergen_id',
        string='Allergens',
        help='Customer permanent allergen information for safety tracking'
    )
    
    allergen_notes = fields.Text(
        string='Allergen Notes',
        translate=True,
        help='Additional allergen information, special dietary requirements, or preparation instructions'
    )
    
    has_allergens = fields.Boolean(
        string='Has Allergens',
        compute='_compute_has_allergens',
        store=True,
        help='Quick check if customer has any allergen restrictions'
    )
    
    allergen_warning = fields.Char(
        string='Allergen Warning',
        compute='_compute_allergen_warning',
        help='Formatted allergen warning message for display'
    )
    
    @api.depends('allergen_ids')
    def _compute_has_allergens(self):
        """Check if customer has any allergen restrictions"""
        for partner in self:
            partner.has_allergens = bool(partner.allergen_ids)
    
    @api.depends('allergen_ids', 'allergen_ids.name')
    def _compute_allergen_warning(self):
        """Generate formatted allergen warning message"""
        for partner in self:
            if partner.allergen_ids:
                allergen_names = ', '.join(partner.allergen_ids.mapped('name'))
                partner.allergen_warning = f"⚠️ ALLERGENS: {allergen_names}"
            else:
                partner.allergen_warning = False
    
    @api.depends('waiting_list_ids', 'waiting_list_ids.status', 'waiting_list_ids.create_date')
    def _compute_waiting_list_stats(self):
        """Compute waiting list statistics for each customer"""
        for partner in self:
            waiting_lists = partner.waiting_list_ids
            
            # Total visits (seated and done customers)
            completed = waiting_lists.filtered(lambda w: w.status in ('seated', 'done'))
            partner.waiting_list_count = len(completed)
            
            # Last visit date
            if completed:
                partner.last_visit_date = max(completed.mapped('create_date'))
            else:
                partner.last_visit_date = False
            
            # No shows
            partner.no_show_count = len(waiting_lists.filtered(lambda w: w.status == 'no_show'))
            
            # Cancellations
            partner.cancelled_count = len(waiting_lists.filtered(lambda w: w.status == 'cancelled'))