# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WaitingListQuickCustomer(models.TransientModel):
    """Quick customer creation/selection for waiting list"""
    
    _name = 'waiting.list.quick.customer'
    _description = 'Quick Customer Selection/Creation'
    
    waiting_list_id = fields.Many2one('waiting.list', string='Waiting List Entry', required=True)
    
    # Customer fields
    name = fields.Char(string='Customer Name', required=True)
    mobile = fields.Char(string='Mobile', required=True)
    email = fields.Char(string='Email')
    
    # Duplicate detection
    existing_customers = fields.Many2many(
        'res.partner',
        string='Existing Customers',
        compute='_compute_existing_customers',
        help='Customers found with the same mobile number'
    )
    
    has_duplicates = fields.Boolean(
        string='Has Duplicates',
        compute='_compute_existing_customers'
    )
    
    selected_customer_id = fields.Many2one(
        'res.partner',
        string='Select Existing Customer',
        domain="[('id', 'in', existing_customers)]"
    )
    
    @api.depends('mobile')
    def _compute_existing_customers(self):
        """Search for existing customers with the same mobile"""
        for record in self:
            if record.mobile:
                # Clean mobile number (remove spaces, dashes, etc.)
                clean_mobile = record.mobile.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                
                # Search for existing customers
                existing = self.env['res.partner'].search([
                    '|', 
                    ('mobile', 'ilike', clean_mobile),
                    ('phone', 'ilike', clean_mobile)
                ])
                
                record.existing_customers = existing
                record.has_duplicates = len(existing) > 0
            else:
                record.existing_customers = False
                record.has_duplicates = False
    
    @api.constrains('mobile')
    def _check_mobile(self):
        """Validate mobile number format"""
        for record in self:
            if record.mobile:
                # Basic validation - should contain at least 10 digits
                digits = ''.join(filter(str.isdigit, record.mobile))
                if len(digits) < 10:
                    raise ValidationError(_('Mobile number must contain at least 10 digits.'))
    
    def action_create_new_customer(self):
        """Create a new customer and link to waiting list"""
        self.ensure_one()
        
        # Create new customer
        customer = self.env['res.partner'].create({
            'name': self.name,
            'mobile': self.mobile,
            'email': self.email or False,
            'is_waiting_list_customer': True,
        })
        
        # Update waiting list entry
        self.waiting_list_id.write({
            'customer_id': customer.id
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def action_link_existing_customer(self):
        """Link selected existing customer to waiting list"""
        self.ensure_one()
        
        if not self.selected_customer_id:
            raise ValidationError(_('Please select a customer to link.'))
        
        # Ensure customer is flagged
        if not self.selected_customer_id.is_waiting_list_customer:
            self.selected_customer_id.write({'is_waiting_list_customer': True})
        
        # Update waiting list entry
        self.waiting_list_id.write({
            'customer_id': self.selected_customer_id.id
        })
        
        return {'type': 'ir.actions.act_window_close'}
