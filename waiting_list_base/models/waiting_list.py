# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class WaitingListBase(models.Model):
    @api.depends('party_size', 'create_date')
    def _compute_estimated_wait_time(self):
        for record in self:
            record.estimated_wait_time = 0
    _name = 'waiting.list'
    _description = 'Restaurant Waiting List - Base'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date asc'  # Simple FIFO for base version
    _rec_name = 'display_name'
    
    # Core Fields
    name = fields.Char(
        string='Reference',
        default=lambda self: _('New'),
        copy=False,
        readonly=True
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Waiting Type
    waiting_type = fields.Selection([
        ('waitlist', 'Waiting List'),
        ('walkin', 'Walk-in'),
    ], string='Type', default='waitlist', required=True, tracking=True,
       help='Waiting List: Full workflow with notifications. Walk-in: Direct seating, feedback only after order completion.')
    
    # Customer Information
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=False,
        domain=[('is_company', '=', False)]
    )
    customer_name = fields.Char(
        string='Customer Name',
        compute='_compute_customer_name',
        inverse='_inverse_customer_name',
        store=True
    )
    customer_phone = fields.Char(
        string='Phone',
        compute='_compute_customer_phone',
        inverse='_inverse_customer_phone',
        store=True
    )
    customer_mobile = fields.Char(
        string='Mobile',
        compute='_compute_customer_mobile',
        inverse='_inverse_customer_mobile',
        store=True
    )
    customer_email = fields.Char(
        string='Email',
        compute='_compute_customer_email',
        inverse='_inverse_customer_email',
        store=True
    )
    customer_birthday = fields.Date(
        string='Birthday',
        compute='_compute_customer_birthday',
        inverse='_inverse_customer_birthday',
        store=True,
        help='Customer birthday (saved to customer profile)'
    )
    
    # Customer Reliability
    customer_no_show_count = fields.Integer(
        related='customer_id.no_show_count',
        string='Customer No-Shows',
        readonly=True,
        help='Number of historical no-shows for this customer'
    )
    
    # Allergen Management (Related from customer profile)
    allergen_ids = fields.Many2many(
        'waiting.list.allergen',
        related='customer_id.allergen_ids',
        string='Allergens',
        readonly=False,  # Allow editing which updates customer profile
        help='Customer allergen information (saved to customer profile)'
    )
    
    allergen_notes = fields.Text(
        related='customer_id.allergen_notes',
        string='Allergen Notes',
        readonly=False,  # Allow editing which updates customer profile
        translate=True,
        help='Additional allergen information (saved to customer profile)'
    )
    
    has_allergens = fields.Boolean(
        related='customer_id.has_allergens',
        string='Has Allergens',
        store=True,
        help='Quick check if customer has any allergen restrictions'
    )
    
    allergen_warning = fields.Char(
        related='customer_id.allergen_warning',
        string='Allergen Warning',
        help='Formatted allergen warning message'
    )

    # Estimated Wait Time (for analytics compatibility)
    estimated_wait_time = fields.Float(
        string='Estimated Wait (minutes)',
        compute='_compute_estimated_wait_time',
        aggregator='avg',
        readonly=True,
        help='Estimated wait time based on current queue and table availability'
    )
    
    # Basic Party Information
    party_size = fields.Integer(
        string='Number of Guests',
        required=True,
        default=1
    )
    
    # Status Management
    status = fields.Selection([
        ('waiting', 'Waiting'),
        ('ready', 'Ready'),
        ('called', 'Called'),
        ('seated', 'Seated'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], string='Status', default='waiting', required=True, tracking=True)
    
    # Company Support
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    # Basic Timing
    create_date = fields.Datetime(
        string='Created',
        readonly=True
    )
    seated_time = fields.Datetime(
        string='Seated Time',
        readonly=True
    )
    cancelled_time = fields.Datetime(
        string='Cancelled Time', 
        readonly=True
    )
    
    # Wait Time Calculation
    actual_wait_time = fields.Float(
        string='Actual Wait Time (minutes)',
        compute='_compute_wait_times',
        store=True
    )
    
    # Basic Preferences
    special_requests = fields.Text(string='Special Requests')
    customer_notes = fields.Text(string='Notes')
    
    # Feedback (simple version)
    customer_satisfaction = fields.Selection([
        ('1', 'Very Dissatisfied'),
        ('2', 'Dissatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied'),
    ], string='Satisfaction')
    
    cancellation_reason = fields.Selection([
        ('too_long', 'Wait too long'),
        ('changed_mind', 'Changed mind'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ], string='Cancellation Reason')
    
    # Survey Integration
    survey_id = fields.Many2one(
        'survey.survey',
        string='Feedback Survey',
        help='Survey to send to customer after visit'
    )
    survey_token = fields.Char(
        string='Survey Token',
        readonly=True,
        copy=False,
        help='Unique token for customer survey access'
    )
    survey_url = fields.Char(
        string='Survey Link',
        compute='_compute_survey_url',
        help='Full survey URL for customer'
    )
    survey_sent = fields.Boolean(
        string='Survey Sent',
        default=False,
        readonly=True,
        help='Whether feedback survey has been sent to customer'
    )
    survey_sent_date = fields.Datetime(
        string='Survey Sent Date',
        readonly=True
    )
    survey_input_id = fields.Many2one(
        'survey.user_input',
        string='Survey Response',
        readonly=True,
        help='Link to customer survey response'
    )
    survey_completed = fields.Boolean(
        string='Survey Completed',
        compute='_compute_survey_completed',
        store=True,
        help='Whether customer has completed the survey'
    )
    
    # Compute methods for customer fields
    @api.depends('survey_input_id', 'survey_input_id.state')
    def _compute_survey_completed(self):
        """Check if customer completed the survey"""
        for record in self:
            record.survey_completed = record.survey_input_id and record.survey_input_id.state == 'done'
    
    @api.depends('customer_id', 'customer_id.name')
    def _compute_customer_name(self):
        for record in self:
            record.customer_name = record.customer_id.name if record.customer_id else False
    
    def _inverse_customer_name(self):
        # This is just to make the field editable, actual logic is in onchange
        pass
    
    @api.depends('customer_id', 'customer_id.phone')
    def _compute_customer_phone(self):
        for record in self:
            record.customer_phone = record.customer_id.phone if record.customer_id else False
    
    def _inverse_customer_phone(self):
        pass
    
    @api.depends('customer_id', 'customer_id.mobile')
    def _compute_customer_mobile(self):
        for record in self:
            record.customer_mobile = record.customer_id.mobile if record.customer_id else record.customer_mobile
    
    def _inverse_customer_mobile(self):
        pass
    
    @api.depends('customer_id', 'customer_id.email')
    def _compute_customer_email(self):
        for record in self:
            record.customer_email = record.customer_id.email if record.customer_id else False
    
    def _inverse_customer_email(self):
        pass
    
    @api.depends('customer_id', 'customer_id.birthday')
    def _compute_customer_birthday(self):
        for record in self:
            record.customer_birthday = record.customer_id.birthday if record.customer_id else False
    
    def _inverse_customer_birthday(self):
        """Update customer birthday when changed in waiting list"""
        for record in self:
            if record.customer_id and record.customer_birthday:
                record.customer_id.birthday = record.customer_birthday
    
    @api.depends('survey_id', 'survey_token')
    def _compute_survey_url(self):
        """Generate public survey URL"""
        for record in self:
            if record.survey_id:
                base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                # Use public survey URL without token - customer can start fresh
                # Token is stored separately and linked after survey submission
                record.survey_url = f"{base_url}/survey/start/{record.survey_id.access_token}"
            else:
                record.survey_url = False
    
    @api.constrains('customer_mobile')
    def _check_customer_mobile(self):
        """Validate mobile number format"""
        for record in self:
            if record.customer_mobile:
                # Remove all non-digit characters
                cleaned_mobile = ''.join(filter(str.isdigit, record.customer_mobile))
                
                # Check if it contains only digits
                if not cleaned_mobile:
                    raise ValidationError(_('Mobile number must contain numbers.'))
                
                # Check minimum length (9 digits)
                if len(cleaned_mobile) < 9:
                    raise ValidationError(_('Mobile number must be at least 9 digits long.'))
    
    def _normalize_phone_number(self, phone):
        """Normalize phone number for search - UNIVERSAL (works with any country code)
        
        Handles all formats including spaces, dashes, parentheses, and plus signs.
        Automatically detects and removes ANY country code (2-3 digits with +/00 or without)
        
        Examples: 
        - "+971 50 123 4567" -> core: "501234567"
        - "00 44 20 1234 5678" -> core: "201234567"
        - "+1 555 123 4567" -> core: "5551234567"
        - "0501234567" -> core: "501234567"
        
        Returns tuple: (core_number, search_patterns)
        - core_number: The base number without country code or leading zero
        - search_patterns: List of variations to search for (handles spaces in DB)
        """
        if not phone:
            return None, []
        
        # Clean the phone number (remove all non-digit characters: spaces, dashes, parentheses, plus signs, etc.)
        cleaned = ''.join(filter(str.isdigit, phone))
        
        _logger.info(f'Normalizing phone number: "{phone}" -> "{cleaned}"')
        
        if len(cleaned) < 9:
            _logger.warning(f'Phone number too short after cleaning: {cleaned} (length: {len(cleaned)})')
            return None, []
        
        # Universal country code detection
        # Try to detect if first 2-3 digits are a country code
        country_code = None
        core_number = cleaned
        
        # Check for 3-digit country code (e.g., 971, 966, 001)
        if len(cleaned) >= 12:  # 3-digit code + 9-digit number minimum
            potential_code = cleaned[:3]
            remaining = cleaned[3:]
            if len(remaining) >= 9:
                country_code = potential_code
                core_number = remaining
                _logger.info(f'Detected 3-digit country code: {country_code}')
        
        # Check for 2-digit country code (e.g., 20, 44, 91)
        if not country_code and len(cleaned) >= 11:  # 2-digit code + 9-digit number minimum
            potential_code = cleaned[:2]
            remaining = cleaned[2:]
            if len(remaining) >= 9:
                country_code = potential_code
                core_number = remaining
                _logger.info(f'Detected 2-digit country code: {country_code}')
        
        # Check for 1-digit country code (e.g., 1 for US/Canada)
        if not country_code and len(cleaned) >= 11:  # 1-digit code + 10-digit number
            potential_code = cleaned[:1]
            remaining = cleaned[1:]
            if len(remaining) == 10:  # Typical for US/Canada
                country_code = potential_code
                core_number = remaining
                _logger.info(f'Detected 1-digit country code: {country_code}')
        
        # Remove leading zero from core number if present
        if core_number.startswith('0'):
            core_number = core_number[1:]
        
        _logger.info(f'Core number extracted: {core_number} (country code: {country_code or "none"})')
        
        # Generate comprehensive search patterns to handle various DB storage formats
        # IMPORTANT: All patterns must include the FULL core number to avoid false matches
        patterns = []
        
        # 1. Core patterns (no country code)
        patterns.append(core_number)  # "501234567"
        patterns.append('0' + core_number)  # "0501234567"
        
        # 2. Patterns with spaces (handle various spacing formats)
        if len(core_number) >= 9:
            # Format: XX XXX XXXX (common in many countries)
            spaced = f"{core_number[:2]} {core_number[2:5]} {core_number[5:]}"
            patterns.append(spaced)  # "50 123 4567"
            patterns.append('0 ' + spaced)  # "0 50 123 4567"
            patterns.append(f"0{core_number[:2]} {core_number[2:5]} {core_number[5:]}")  # "050 123 4567"
            
            # Format: XXX XXX XXXX (common in US)
            if len(core_number) >= 10:
                spaced_us = f"{core_number[:3]} {core_number[3:6]} {core_number[6:]}"
                patterns.append(spaced_us)  # "555 123 4567"
        
        # 3. With detected country code (if any)
        if country_code:
            patterns.append(country_code + core_number)  # "971501234567"
            patterns.append(country_code + ' ' + core_number)  # "971 501234567"
            patterns.append(country_code + '0' + core_number)  # "9710501234567"
            
            # With country code and spacing (FULL number only - no partial matches)
            if len(core_number) >= 9:
                patterns.append(f"{country_code} {core_number[:2]} {core_number[2:5]} {core_number[5:]}")  # "971 50 123 4567"
                patterns.append(f"+{country_code} {core_number[:2]} {core_number[2:5]} {core_number[5:]}")  # "+971 50 123 4567"
                patterns.append(f"+{country_code} 0{core_number[:2]} {core_number[2:5]} {core_number[5:]}")  # "+971 050 123 4567"
        
        _logger.info(f'Generated {len(patterns)} search patterns including: {patterns[:3]}')
        
        return core_number, patterns
    
    @api.onchange('customer_mobile')
    def _onchange_customer_mobile(self):
        """Search for existing customer by mobile number
        
        Automatically searches when mobile number is entered.
        Handles all formats: +971 50 123 4567, 971501234567, 0501234567, etc.
        """
        if self.customer_mobile:
            _logger.info(f'Mobile onchange triggered with value: "{self.customer_mobile}"')
            
            # Normalize and get search patterns
            core_number, patterns = self._normalize_phone_number(self.customer_mobile)
            
            if core_number and len(core_number) >= 9:
                _logger.info(f'Searching for customer with core number: {core_number}')
                _logger.info(f'Search patterns: {patterns}')
                
                # Build OR domain for all patterns (to handle various DB formats like "+971 50 123 4567")
                # Domain structure: (pattern1 OR pattern2 OR ... OR patternN) AND is_company=False
                pattern_conditions = []
                for pattern in patterns:
                    pattern_conditions.append(('mobile', 'ilike', pattern))
                    pattern_conditions.append(('phone', 'ilike', pattern))
                
                # Build domain with proper OR structure
                if len(pattern_conditions) == 2:
                    # Only one pattern: simple OR
                    domain = ['&', '|', pattern_conditions[0], pattern_conditions[1], ('is_company', '=', False)]
                else:
                    # Multiple patterns: chain ORs
                    domain = ['&']
                    # Build OR chain: '|', '|', '|', cond1, cond2, cond3, cond4, ...
                    domain.extend(['|'] * (len(pattern_conditions) - 1))
                    domain.extend(pattern_conditions)
                    domain.append(('is_company', '=', False))
                
                _logger.info(f'Search domain (showing first 10 elements): {domain[:10]}')
                
                # Search for existing partner
                partner = self.env['res.partner'].search(domain, limit=1)
                
                if partner:
                    # Found existing customer - populate fields
                    _logger.info(f'Found existing customer: {partner.name} (ID: {partner.id}, mobile: {partner.mobile}, phone: {partner.phone})')
                    self.customer_id = partner
                    self.customer_name = partner.name
                    self.customer_phone = partner.phone
                    self.customer_email = partner.email
                    # return {
                    #     'warning': {
                    #         'title': _('Existing Customer Found'),
                    #         'message': _('Customer "%s" found with this mobile number. Details have been loaded.') % partner.name
                    #     }
                    # }
                else:
                    # No existing customer - clear customer_id to allow new creation
                    _logger.info('No existing customer found with this mobile number')
                    self.customer_id = False
            else:
                _logger.warning(f'Mobile number too short or invalid: {self.customer_mobile}')
    
    @api.onchange('customer_id')
    def _onchange_customer_allergens(self):
        """Show warning if customer has allergen restrictions"""
        if self.customer_id and self.customer_id.has_allergens:
            allergen_names = ', '.join(self.customer_id.allergen_ids.mapped('name'))
            return {
                'warning': {
                    'title': _('⚠️ Allergen Alert'),
                    'message': _('This customer has allergen restrictions:\n\n%s\n\nPlease ensure kitchen staff are informed.') % allergen_names
                }
            }
    
    def action_search_customer_by_mobile(self):
        """Button action to search for customer by mobile number"""
        self.ensure_one()
        
        if not self.customer_mobile:
            raise UserError(_('Please enter a mobile number to search.'))
        
        # Normalize and get search patterns
        core_number, patterns = self._normalize_phone_number(self.customer_mobile)
        
        if not core_number or len(core_number) < 9:
            raise UserError(_('Mobile number must be at least 9 digits long.'))
        
        # Build OR domain for all patterns (to handle various DB formats like "+971 50 123 4567")
        pattern_conditions = []
        for pattern in patterns:
            pattern_conditions.append(('mobile', 'ilike', pattern))
            pattern_conditions.append(('phone', 'ilike', pattern))
        
        # Build domain with proper OR structure
        if len(pattern_conditions) == 2:
            # Only one pattern: simple OR
            domain = ['&', '|', pattern_conditions[0], pattern_conditions[1], ('is_company', '=', False)]
        else:
            # Multiple patterns: chain ORs
            domain = ['&']
            # Build OR chain: '|', '|', '|', cond1, cond2, cond3, cond4, ...
            domain.extend(['|'] * (len(pattern_conditions) - 1))
            domain.extend(pattern_conditions)
            domain.append(('is_company', '=', False))
        
        # Search for existing partner
        partner = self.env['res.partner'].search(domain, limit=1)
        
        if partner:
            # Found existing customer - populate fields
            self.customer_id = partner
            self.customer_name = partner.name
            self.customer_phone = partner.phone
            self.customer_email = partner.email
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Customer Found'),
                    'message': _('Customer "%s" found and loaded!') % partner.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            # No customer found
            self.customer_id = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Customer Found'),
                    'message': _('No customer found with mobile "%s". You can create a new customer.') % self.customer_mobile,
                    'type': 'info',
                    'sticky': False,
                }
            }
    
    @api.depends('customer_id', 'party_size', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.customer_id:
                record.display_name = f"{record.name} - {record.customer_id.name} ({record.party_size} guests)"
            elif record.customer_name:
                record.display_name = f"{record.name} - {record.customer_name} ({record.party_size} guests)"
            elif record.party_size:
                record.display_name = f"{record.name} - {record.party_size} Guests"
            else:
                record.display_name = record.name or _('New')
    
    @api.depends('create_date', 'seated_time', 'cancelled_time', 'status')
    def _compute_wait_times(self):
        for record in self:
            if record.create_date:
                end_time = record.seated_time or record.cancelled_time
                if end_time:
                    delta = end_time - record.create_date
                    record.actual_wait_time = delta.total_seconds() / 60.0
                elif record.status in ['waiting', 'ready', 'called']:
                    delta = fields.Datetime.now() - record.create_date
                    record.actual_wait_time = delta.total_seconds() / 60.0
                else:
                    record.actual_wait_time = 0
            else:
                record.actual_wait_time = 0
    
    @api.model
    def create(self, vals):
        # Auto-create customer if mobile/name provided but no customer_id
        if not vals.get('customer_id'):
            # Check if we have enough info to create a customer
            has_mobile = vals.get('customer_mobile')
            has_name = vals.get('customer_name')
            
            if has_mobile and has_name:
                # We have enough info - create customer automatically
                customer_vals = {
                    'name': vals.get('customer_name'),
                    'mobile': vals.get('customer_mobile'),
                    'phone': vals.get('customer_phone'),
                    'email': vals.get('customer_email'),
                    'birthday': vals.get('customer_birthday'),
                    'is_waiting_list_customer': True,
                    'is_company': False,
                }
                # Remove None/False values
                customer_vals = {k: v for k, v in customer_vals.items() if v}
                
                # Create new customer
                new_customer = self.env['res.partner'].create(customer_vals)
                vals['customer_id'] = new_customer.id
            elif has_mobile:
                # Has mobile but no name - use mobile as name
                customer_vals = {
                    'name': vals.get('customer_mobile'),  # Use mobile as name temporarily
                    'mobile': vals.get('customer_mobile'),
                    'phone': vals.get('customer_phone'),
                    'email': vals.get('customer_email'),
                    'birthday': vals.get('customer_birthday'),
                    'is_waiting_list_customer': True,
                    'is_company': False,
                }
                customer_vals = {k: v for k, v in customer_vals.items() if v}
                new_customer = self.env['res.partner'].create(customer_vals)
                vals['customer_id'] = new_customer.id
        
        # Only raise error if still no customer_id after auto-creation attempts
        if not vals.get('customer_id'):
            raise ValidationError(_('Customer is required. Please provide at least customer name and mobile number.'))
        
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('waiting.list') or _('New')
        
        # Mark customer as waiting list customer
        if vals.get('customer_id'):
            customer = self.env['res.partner'].browse(vals['customer_id'])
            if customer and not customer.is_waiting_list_customer:
                customer.write({'is_waiting_list_customer': True})
        
        record = super().create(vals)
        
        # Queue notification when customer is added to waiting list (only for 'waiting' status)
        if record.status == 'waiting' and (record.customer_mobile or record.customer_phone):
            try:
                record._queue_added_notification()
            except Exception as e:
                _logger.warning('Failed to queue added notification for %s: %s', record.name, str(e))
        
        return record
    
    def write(self, vals):
        """Override write to flag customers when they are added to waiting list"""
        # Auto-create customer if mobile/name changed but no customer_id
        for record in self:
            if not vals.get('customer_id') and not record.customer_id:
                if vals.get('customer_mobile') or (record.customer_mobile and 'customer_name' in vals):
                    customer_vals = {
                        'name': vals.get('customer_name', record.customer_name or 'Guest'),
                        'mobile': vals.get('customer_mobile', record.customer_mobile),
                        'phone': vals.get('customer_phone', record.customer_phone),
                        'email': vals.get('customer_email', record.customer_email),
                        'birthday': vals.get('customer_birthday', record.customer_birthday),
                        'is_waiting_list_customer': True,
                        'is_company': False,
                    }
                    # Remove None/False values
                    customer_vals = {k: v for k, v in customer_vals.items() if v}
                    
                    if customer_vals.get('mobile'):
                        # Create new customer
                        new_customer = self.env['res.partner'].create(customer_vals)
                        vals['customer_id'] = new_customer.id
        
        # If customer_id is being explicitly removed, prevent it
        if 'customer_id' in vals and vals['customer_id'] is False:
            # Allow removal only if we're setting customer fields
            if not any(k in vals for k in ['customer_mobile', 'customer_name']):
                raise ValidationError(_('Customer cannot be removed from a waiting list entry.'))
        
        result = super().write(vals)
        
        # If customer_id is being updated, mark the new customer
        if vals.get('customer_id'):
            for record in self:
                if record.customer_id and not record.customer_id.is_waiting_list_customer:
                    record.customer_id.write({'is_waiting_list_customer': True})
        
        return result
    
    def action_mark_seated(self):
        """Mark customer as seated"""
        for record in self:
            if record.status not in ['ready', 'called']:
                raise UserError(_('Only customers who are ready or called can be seated.'))
            
            # Validate table assignment for waiting list type
            # Walk-in can be seated without table (for takeaway scenarios)
            if record.waiting_type == 'waitlist' and not record.table_id:
                raise UserError(_('Please assign a table before marking customer as seated.\n\nUse "Select Table" button to choose a table.'))
            
            record.write({
                'status': 'seated',
                'seated_time': fields.Datetime.now()
            })
            
            # Show wait time comparison notification
            if record.estimated_wait_time and record.actual_wait_time:
                difference = record.actual_wait_time - record.estimated_wait_time
                accuracy_percentage = 100 - abs((difference / record.estimated_wait_time) * 100) if record.estimated_wait_time > 0 else 0
                
                if abs(difference) <= 2:
                    # Very accurate (within 2 minutes)
                    notification_type = 'success'
                    title = _('Excellent Wait Time Accuracy! 🎯')
                    icon = '🎯'
                elif abs(difference) <= 5:
                    # Good accuracy (within 5 minutes)
                    notification_type = 'success'
                    title = _('Good Wait Time Estimate ✓')
                    icon = '✓'
                elif abs(difference) <= 10:
                    # Acceptable (within 10 minutes)
                    notification_type = 'info'
                    title = _('Wait Time Variance')
                    icon = 'ℹ️'
                else:
                    # Significant difference
                    notification_type = 'warning'
                    title = _('Large Wait Time Variance')
                    icon = '⚠️'
                
                if difference > 0:
                    message = _('{icon} Customer waited {actual:.0f} minutes (estimated {estimated:.0f} minutes)\n\n'
                               'Waited {diff:.0f} minutes LONGER than estimated\n'
                               'Accuracy: {accuracy:.0f}%').format(
                        icon=icon,
                        actual=record.actual_wait_time,
                        estimated=record.estimated_wait_time,
                        diff=abs(difference),
                        accuracy=accuracy_percentage
                    )
                elif difference < 0:
                    message = _('{icon} Customer waited {actual:.0f} minutes (estimated {estimated:.0f} minutes)\n\n'
                               'Seated {diff:.0f} minutes FASTER than estimated\n'
                               'Accuracy: {accuracy:.0f}%').format(
                        icon=icon,
                        actual=record.actual_wait_time,
                        estimated=record.estimated_wait_time,
                        diff=abs(difference),
                        accuracy=accuracy_percentage
                    )
                else:
                    message = _('{icon} Customer waited exactly {actual:.0f} minutes\n\n'
                               'Perfect match with estimated time!\n'
                               'Accuracy: 100%').format(
                        icon=icon,
                        actual=record.actual_wait_time
                    )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': title,
                        'message': message,
                        'type': notification_type,
                        'sticky': False,
                    }
                }
        
        return True
    
    def action_mark_done(self):
        """Mark waiting list entry as done (visit completed successfully)"""
        for record in self:
            if record.status != 'seated':
                raise UserError(_('Only seated customers can be marked as done.'))
            
            # Additional validation: waiting list entries should have table assignment
            if record.waiting_type == 'waitlist' and not record.table_id:
                raise UserError(_('Waiting list entries must have a table assigned before completion.\n\nPlease assign a table first.'))
            
            record.write({
                'status': 'done'
            })
            # Queue survey notification for all waiting list entries 1
            if not record.survey_sent and (record.customer_mobile or record.customer_phone):
                try:
                    record._generate_survey_token()
                    record._queue_survey_notification()
                except Exception as e:
                    _logger.warning('Failed to queue survey notification for %s: %s', record.name, str(e))
        return True
    
    def _generate_survey_token(self):
        """ Generate unique survey token and create survey input record """
        import uuid
        for record in self:
            if not record.survey_token and record.survey_id:
                # Generate token
                token = str(uuid.uuid4())
                
                # Create survey.user_input record for this customer
                survey_input = self.env['survey.user_input'].sudo().create({
                    'survey_id': record.survey_id.id,
                    'access_token': token,
                    'partner_id': record.customer_id.id if record.customer_id else False,
                    'email': record.customer_email or False,
                    'state': 'new',  # Not started yet
                })
                
                record.write({
                    'survey_token': token,
                    'survey_input_id': survey_input.id
                })
                _logger.info(f'Generated survey token for waiting list {record.name}: {token} (survey_input: {survey_input.id})')
    
    def _queue_survey_notification(self):
        """Queue feedback survey notification to be sent via SMS/WhatsApp"""
        self.ensure_one()
        
        if not self.survey_id:
            # Get default survey from config
            config = self.env['ir.config_parameter'].sudo()
            default_survey_id = config.get_param('waiting_list.default_survey_id')
            if default_survey_id:
                self.survey_id = int(default_survey_id)
            else:
                _logger.warning('No default survey configured for waiting list %s', self.name)
                return False
        
        # Generate token if not exists
        if not self.survey_token:
            self._generate_survey_token()
        
        if not self.customer_mobile and not self.customer_phone:
            _logger.warning('No phone number for survey notification: %s', self.name)
            return False
        
        # Prepare survey message
        message = self._prepare_survey_message()
        
        # Check if enterprise notification model exists
        if 'waiting.list.notification' in self.env:
            # Queue notification using enterprise model
            notification_type = getattr(self, 'notification_type', 'sms') or 'sms'
            notification = self.env['waiting.list.notification'].create({
                'waiting_list_id': self.id,
                'customer_id': self.customer_id.id,
                'notification_type': notification_type,
                'phone_number': self.customer_mobile or self.customer_phone,
                'message': message,
                'template_type': 'survey',
                'state': 'pending',
                'scheduled_time': fields.Datetime.now(),
            })
            _logger.info('Survey notification queued for %s', self.name)
            # Try to send immediately
            try:
                notification.action_send()
            except Exception as e:
                _logger.warning('Failed to send survey notification immediately: %s', str(e))
        else:
            # Fallback: post to chatter only
            self.message_post(
                body=message,
                subject=_('Feedback Survey'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        
        self.write({
            'survey_sent': True,
            'survey_sent_date': fields.Datetime.now()
        })
        
        return True
    
    def _queue_added_notification(self):
        """Queue notification when customer is added to waiting list"""
        self.ensure_one()
        
        if not self.customer_mobile and not self.customer_phone:
            _logger.warning('No phone number for queue added notification: %s', self.name)
            return False
        
        # Prepare queue added message
        message = self._prepare_queue_added_message()
        
        # Check if enterprise notification model exists
        if 'waiting.list.notification' in self.env:
            # Queue notification using enterprise model
            notification_type = getattr(self, 'notification_type', 'sms') or 'sms'
            notification = self.env['waiting.list.notification'].create({
                'waiting_list_id': self.id,
                'customer_id': self.customer_id.id,
                'notification_type': notification_type,
                'phone_number': self.customer_mobile or self.customer_phone,
                'message': message,
                'template_type': 'queue_added',
                'state': 'pending',
                'scheduled_time': fields.Datetime.now(),
            })
            _logger.info('Queue added notification queued for %s', self.name)
            # Try to send immediately
            try:
                notification.action_send()
            except Exception as e:
                _logger.warning('Failed to send queue added notification immediately: %s', str(e))
        else:
            # Fallback: post to chatter only
            self.message_post(
                body=message,
                subject=_('Added to Waiting List'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        
        return True
    
    def _queue_cancellation_notification(self):
        """Queue cancellation notification to be sent via SMS/WhatsApp"""
        self.ensure_one()
        
        if not self.customer_mobile and not self.customer_phone:
            _logger.warning('No phone number for cancellation notification: %s', self.name)
            return False
        
        # Prepare cancellation message
        message = self._prepare_cancellation_message()
        
        # Check if enterprise notification model exists
        if 'waiting.list.notification' in self.env:
            # Queue notification using enterprise model
            notification_type = getattr(self, 'notification_type', 'sms') or 'sms'
            notification = self.env['waiting.list.notification'].create({
                'waiting_list_id': self.id,
                'customer_id': self.customer_id.id,
                'notification_type': notification_type,
                'phone_number': self.customer_mobile or self.customer_phone,
                'message': message,
                'template_type': 'cancel',
                'state': 'pending',
                'scheduled_time': fields.Datetime.now(),
            })
            _logger.info('Cancellation notification queued for %s', self.name)
            # Try to send immediately
            try:
                notification.action_send()
            except Exception as e:
                _logger.warning('Failed to send cancellation notification immediately: %s', str(e))
        else:
            # Fallback: post to chatter only
            self.message_post(
                body=message,
                subject=_('Reservation Cancelled'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        
        return True
    
    def _queue_no_show_notification(self):
        """Queue no-show notification to be sent via SMS/WhatsApp"""
        self.ensure_one()
        
        if not self.customer_mobile and not self.customer_phone:
            _logger.warning('No phone number for no-show notification: %s', self.name)
            return False
        
        # Prepare no-show message
        message = self._prepare_no_show_message()
        
        # Check if enterprise notification model exists
        if 'waiting.list.notification' in self.env:
            # Queue notification using enterprise model
            notification_type = getattr(self, 'notification_type', 'sms') or 'sms'
            notification = self.env['waiting.list.notification'].create({
                'waiting_list_id': self.id,
                'customer_id': self.customer_id.id,
                'notification_type': notification_type,
                'phone_number': self.customer_mobile or self.customer_phone,
                'message': message,
                'template_type': 'no_show',
                'state': 'pending',
                'scheduled_time': fields.Datetime.now(),
            })
            _logger.info('No-show notification queued for %s', self.name)
            # Try to send immediately
            try:
                notification.action_send()
            except Exception as e:
                _logger.warning('Failed to send no-show notification immediately: %s', str(e))
        else:
            # Fallback: post to chatter only
            self.message_post(
                body=message,
                subject=_('Marked as No-Show'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        
        return True
    
    def _queue_ready_notification(self):
        """Queue ready notification to be sent via SMS/WhatsApp"""
        self.ensure_one()
        
        if not self.customer_mobile and not self.customer_phone:
            _logger.warning('No phone number for ready notification: %s', self.name)
            return False
        
        # Prepare ready message
        message = self._prepare_ready_message()
        
        # Check if enterprise notification model exists
        if 'waiting.list.notification' in self.env:
            # Queue notification using enterprise model
            notification_type = getattr(self, 'notification_type', 'sms') or 'sms'
            notification = self.env['waiting.list.notification'].create({
                'waiting_list_id': self.id,
                'customer_id': self.customer_id.id,
                'notification_type': notification_type,
                'phone_number': self.customer_mobile or self.customer_phone,
                'message': message,
                'template_type': 'ready',
                'state': 'pending',
                'scheduled_time': fields.Datetime.now(),
            })
            _logger.info('Ready notification queued for %s', self.name)
            # Try to send immediately
            try:
                notification.action_send()
            except Exception as e:
                _logger.warning('Failed to send ready notification immediately: %s', str(e))
        else:
            # Fallback: post to chatter only
            self.message_post(
                body=message,
                subject=_('Table Ready'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        
        return True
    
    def _prepare_survey_message(self):
        """Prepare survey message content"""
        self.ensure_one()
        
        # Get customer's preferred language
        lang = self.customer_id.lang or self.env.user.lang or 'en_US'
        
        # Generate URL with token for direct access
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        survey_url = f"{base_url}/survey/start/{self.survey_id.access_token}/{self.survey_token}" if self.survey_token else self.survey_url
        
        # Bilingual message (English + Arabic)
        if lang.startswith('ar'):
            message = f"""شكراً لزيارتك! نود معرفة رأيك:
{survey_url}

Thank you for visiting! Please share your feedback:
{survey_url}"""
        else:
            message = f"""Thank you for visiting! Please share your feedback:
{survey_url}

شكراً لزيارتك! نود معرفة رأيك:
{survey_url}"""
        
        return message
    
    def _prepare_queue_added_message(self):
        """Prepare queue added notification message"""
        self.ensure_one()
        
        # Get customer's preferred language
        lang = self.customer_id.lang or self.env.user.lang or 'en_US'
        
        # Get estimated wait time if available
        wait_info = ''
        if hasattr(self, 'estimated_wait_time') and self.estimated_wait_time:
            if lang.startswith('ar'):
                wait_info = f"\n\nوقت الانتظار المتوقع: {int(self.estimated_wait_time)} دقيقة"
            else:
                wait_info = f"\n\nEstimated wait time: {int(self.estimated_wait_time)} minutes"
        
        # Bilingual message (English + Arabic)
        if lang.startswith('ar'):
            message = f"""مرحباً {self.customer_name},

تم إضافتك إلى قائمة الانتظار! ({self.name})
عدد الضيوف: {self.party_size}{wait_info}

سنقوم بإعلامك عندما تكون طاولتك جاهزة.

---

Hello {self.customer_name},

You've been added to the waiting list! ({self.name})
Party size: {self.party_size}{wait_info}

We'll notify you when your table is ready."""
        else:
            message = f"""Hello {self.customer_name},

You've been added to the waiting list! ({self.name})
Party size: {self.party_size}{wait_info}

We'll notify you when your table is ready.

---

مرحباً {self.customer_name},

تم إضافتك إلى قائمة الانتظار! ({self.name})
عدد الضيوف: {self.party_size}{wait_info}

سنقوم بإعلامك عندما تكون طاولتك جاهزة."""
        
        return message
    
    def _prepare_cancellation_message(self):
        """Prepare cancellation notification message"""
        self.ensure_one()
        
        # Get customer's preferred language
        lang = self.customer_id.lang or self.env.user.lang or 'en_US'
        
        # Bilingual message (English + Arabic)
        if lang.startswith('ar'):
            message = f"""مرحباً {self.customer_name},

تم إلغاء حجزك في قائمة الانتظار ({self.name}).

نتطلع لرؤيتك مرة أخرى قريباً!

---

Hello {self.customer_name},

Your waiting list reservation ({self.name}) has been cancelled.

We hope to see you again soon!"""
        else:
            message = f"""Hello {self.customer_name},

Your waiting list reservation ({self.name}) has been cancelled.

We hope to see you again soon!

---

مرحباً {self.customer_name},

تم إلغاء حجزك في قائمة الانتظار ({self.name}).

نتطلع لرؤيتك مرة أخرى قريباً!"""
        
        return message
    
    def _prepare_no_show_message(self):
        """Prepare no-show notification message"""
        self.ensure_one()
        
        # Get customer's preferred language
        lang = self.customer_id.lang or self.env.user.lang or 'en_US'
        
        # Bilingual message (English + Arabic)
        if lang.startswith('ar'):
            message = f"""مرحباً {self.customer_name},

لم تتمكن من الحضور لحجزك ({self.name}).

نأمل أن نراك قريباً. يرجى إعلامنا مسبقاً في المرة القادمة إذا لم تتمكن من الحضور.

---

Hello {self.customer_name},

You were marked as a no-show for your reservation ({self.name}).

We hope to see you soon. Please let us know in advance if you cannot make it next time."""
        else:
            message = f"""Hello {self.customer_name},

You were marked as a no-show for your reservation ({self.name}).

We hope to see you soon. Please let us know in advance if you cannot make it next time.

---

مرحباً {self.customer_name},

لم تتمكن من الحضور لحجزك ({self.name}).

نأمل أن نراك قريباً. يرجى إعلامنا مسبقاً في المرة القادمة إذا لم تتمكن من الحضور."""
        
        return message
    
    def _prepare_ready_message(self):
        """Prepare ready notification message"""
        self.ensure_one()
        
        # Get customer's preferred language
        lang = self.customer_id.lang or self.env.user.lang or 'en_US'
        
        # Get table info if available (enterprise feature)
        table_info = ''
        if hasattr(self, 'table_id') and self.table_id:
            if lang.startswith('ar'):
                table_info = f"\n\nالطاولة: {self.table_id.display_name}"
            else:
                table_info = f"\n\nTable: {self.table_id.display_name}"
        
        # Bilingual message (English + Arabic)
        if lang.startswith('ar'):
            message = f"""مرحباً {self.customer_name},

طاولتك جاهزة الآن! ({self.name}){table_info}

يرجى التوجه إلى مضيف الاستقبال.

---

Hello {self.customer_name},

Your table is ready! ({self.name}){table_info}

Please proceed to the host stand."""
        else:
            message = f"""Hello {self.customer_name},

Your table is ready! ({self.name}){table_info}

Please proceed to the host stand.

---

مرحباً {self.customer_name},

طاولتك جاهزة الآن! ({self.name}){table_info}

يرجى التوجه إلى مضيف الاستقبال."""
        
        return message
    
    def action_send_survey(self):
        """Send feedback survey to customer (manual action)"""
        self.ensure_one()
        
        # Use queue method
        success = self._queue_survey_notification()
        
        if not success:
            raise UserError(_('Failed to queue survey notification. Check configuration and customer phone number.'))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Survey Queued'),
                'message': _('Feedback survey has been queued for sending to customer.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_cancel_waitlist(self):
        """Cancel waiting list entry and send notification"""
        for record in self:
            if record.status in ['seated', 'cancelled', 'no_show']:
                raise UserError(_('Cannot cancel this entry.'))
            record.write({  
                'status': 'cancelled',
                'cancelled_time': fields.Datetime.now()
            })
            
            # Queue cancellation notification if customer has phone
            if record.customer_mobile or record.customer_phone:
                try:
                    record._queue_cancellation_notification()
                except Exception as e:
                    _logger.warning('Failed to queue cancellation notification for %s: %s', record.name, str(e))
        return True
    
    def action_no_show(self):
        """Mark as no show, send notification, and update customer record"""
        for record in self:
            if record.status in ['seated', 'cancelled']:
                raise UserError(_('Cannot mark this entry as no show.'))
            record.write({
                'status': 'no_show',
                'cancelled_time': fields.Datetime.now()
            })
            
            # Increment customer no-show count
            if record.customer_id:
                record.customer_id.no_show_count = (record.customer_id.no_show_count or 0) + 1
            
            # Queue no-show notification if customer has phone
            if record.customer_mobile or record.customer_phone:
                try:
                    record._queue_no_show_notification()
                except Exception as e:
                    _logger.warning('Failed to queue no-show notification for %s: %s', record.name, str(e))
        return True
    
    def action_mark_ready(self):
        """Mark customer as ready and send notification"""
        for record in self:
            if record.status != 'waiting':
                raise UserError(_('Only waiting customers can be marked as ready.'))
            record.write({
                'status': 'ready'
            })
            
            # Queue ready notification if customer has phone
            if record.customer_mobile or record.customer_phone:
                try:
                    record._queue_ready_notification()
                except Exception as e:
                    _logger.warning('Failed to queue ready notification for %s: %s', record.name, str(e))
        return True
    
    def action_call_customer(self):
        """Call customer"""
        for record in self:
            if record.status not in ['waiting', 'ready']:
                raise UserError(_('Only waiting or ready customers can be called.'))
            record.write({
                'status': 'called'
            })
        return True
    
    @api.model
    def get_dashboard_statistics(self):
        """Get dashboard statistics"""
        # Use create_date field to filter records created today
        today = fields.Date.today()
        today_str = today.strftime('%Y-%m-%d')
        next_day = (today + timedelta(days=1)).strftime('%Y-%m-%d')

        # Odoo stores create_date as UTC datetime, so we filter by string date
        waiting_count = self.search_count([
            ('status', 'in', ['waiting', 'ready', 'called']),
            ('create_date', '>=', today_str),
            ('create_date', '<', next_day)
        ])

        seated_count = self.search_count([
            ('status', '=', 'seated'),
            ('create_date', '>=', today_str),
            ('create_date', '<', next_day)
        ])

        total_count = self.search_count([
            ('create_date', '>=', today_str),
            ('create_date', '<', next_day)
        ])

        seated_records = self.search([
            ('status', '=', 'seated'),
            ('create_date', '>=', today_str),
            ('create_date', '<', next_day),
            ('actual_wait_time', '>', 0)
        ])
        
        avg_wait_time = 0
        if seated_records:
            avg_wait_time = sum(seated_records.mapped('actual_wait_time')) / len(seated_records)
        
        return {
            'waiting_count': waiting_count,
            'seated_count': seated_count,
            'total_count': total_count,
            'avg_wait_time': round(avg_wait_time, 1)
        }

    def action_quick_add_customer(self):
        """Open wizard for quick customer creation/selection"""
        self.ensure_one()
        
        return {
            'name': _('Add/Select Customer'),
            'type': 'ir.actions.act_window',
            'res_model': 'waiting.list.quick.customer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_waiting_list_id': self.id,
            },
        }

    @api.model  
    def action_dashboard(self):
        """Return dashboard action with statistics in context"""
        stats = self.get_dashboard_statistics()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Restaurant Waiting List Dashboard',
            'res_model': 'waiting.list',
            'view_mode': 'kanban,tree,form',
            'target': 'main',
            'context': {
                'dashboard_stats': stats,
                'create': False,
            },
            'domain': [],
        }