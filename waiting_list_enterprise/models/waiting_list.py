# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class WaitingListEnterprise(models.Model):
    """Enterprise extensions for waiting list with POS Restaurant integration"""
    
    _inherit = 'waiting.list'
    _order = 'priority desc, create_date asc'  # Priority-based ordering for enterprise
    
    # Configuration field for auto-notification
    auto_send_queue_notification = fields.Boolean(
        string='Auto-Send Queue Notification',
        default=True,
        help='Automatically send notification when customer is added to waiting list'
    )
    
    # POS Restaurant Integration Fields
    pos_config_id = fields.Many2one(
        'pos.config',
        string='POS Configuration',
        domain="[('module_pos_restaurant', '=', True)]",
        default=lambda self: self._default_pos_config_id(),
        help='The Point of Sale configuration for this waiting list entry'
    )
    
    floor_id = fields.Many2one(
        'restaurant.floor',
        string='Floor',
        domain="[('pos_config_ids', '=', pos_config_id)]",
        default=lambda self: self._default_floor_id(),
        help='The restaurant floor for table assignment',
        tracking=True
    )
    
    table_id = fields.Many2one(
        'restaurant.table',
        string='Table',
        domain="[('floor_id', '=', floor_id), ('active', '=', True)]",
        help='The assigned table for this customer',
        tracking=True
    )
    
    # Priority & VIP Management
    priority = fields.Selection([
        ('0', 'No Priority'),
        ('1', '⭐'),
        ('2', '⭐⭐'),
        ('3', '⭐⭐⭐'),
        ('4', '⭐⭐⭐⭐'),
        ('5', '⭐⭐⭐⭐⭐'),
    ], string='Priority', default='0', tracking=True,
       help='Priority level (0-5 stars). Higher priority customers are served first. VIP customers automatically get 5-star priority.')
    
    is_vip = fields.Boolean(
        string='VIP Customer',
        compute='_compute_is_vip',
        store=True,
        help='Automatically set based on customer category'
    )
    
    # Enhanced Party Information
    preferred_seating = fields.Selection([
        ('indoor', 'Indoor'),
        ('outdoor', '(Smoking)Outdoor'),
        ('window', 'Window Side'),
        ('booth', 'Booth'),
        ('bar', 'Bar Area'),
    ], string='Preferred Seating', tracking=True, default='outdoor')
    
    # Table Assignment Timing
    table_assigned_time = fields.Datetime(
        string='Table Assigned Time',
        readonly=True,
        help='When the table was assigned to this customer'
    )
    
    # Estimated Wait Time (Enterprise Feature)
    calculation_type = fields.Selection([
        ('auto', 'Auto Calculation'),
        ('manual', 'Manual Entry'),
    ], string='Calculation Type', default='auto', required=True,
       help='Choose how wait time is determined: Auto uses intelligent calculation, Manual allows custom entry')
    
    estimated_wait_time = fields.Float(
        string='Estimated Wait (minutes)',
        store=True,
        aggregator='avg',
        help='Intelligent wait time prediction based on historical data and current queue. Can be manually adjusted by host.'
    )
    
    manual_wait_time = fields.Float(
        string='Manual Wait Time (minutes)',
        help='Manually entered wait time when calculation type is set to Manual'
    )
    
    wait_time_source = fields.Char(
        string='Estimate Source',
        store=True,
        help='Data source used for wait time estimate (historical data vs simple queue calculation)'
    )
    
    wait_time_variance = fields.Float(
        string='Wait Time Variance (minutes)',
        compute='_compute_wait_time_variance',
        store=True,
        help='Difference between actual and estimated wait time (positive = waited longer, negative = waited less)'
    )
    
    wait_time_accuracy = fields.Float(
        string='Wait Time Accuracy (%)',
        compute='_compute_wait_time_variance',
        store=True,
        help='Accuracy percentage of the wait time estimate (100% = perfect match)'
    )
    
    # Notification Preferences
    notification_sent = fields.Boolean(
        string='Notification Sent',
        default=False,
        help='Whether notification was sent to customer'
    )
    
    notification_type = fields.Selection([
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('sms_whatsapp', 'SMS + WhatsApp'),
        ('call', 'Phone Call'),
    ], string='Notification Method', default='sms_whatsapp',
       help='Choose notification method. SMS + WhatsApp sends both for maximum delivery.')
    
    notification_time = fields.Datetime(
        string='Notification Sent At',
        readonly=True
    )
    
    # Notification Queue Management
    notification_ids = fields.One2many(
        'waiting.list.notification',
        'waiting_list_id',
        string='Notifications',
        help='All notifications sent for this waiting list entry'
    )
    
    notification_count = fields.Integer(
        string='Notification Count',
        compute='_compute_notification_count',
        help='Total number of notifications'
    )
    
    notification_pending_count = fields.Integer(
        string='Pending Notifications',
        compute='_compute_notification_count',
        help='Number of pending notifications'
    )
    
    notification_sent_count = fields.Integer(
        string='Sent Notifications',
        compute='_compute_notification_count',
        help='Number of successfully sent notifications'
    )
    
    notification_failed_count = fields.Integer(
        string='Failed Notifications',
        compute='_compute_notification_count',
        help='Number of failed notifications'
    )
    
    # Table Information
    table_capacity = fields.Integer(
        related='table_id.seats',
        string='Table Capacity',
        store=True,
        readonly=True
    )
    
    # Customer Intelligence Fields (POS Order Analytics)
    last_visit_date = fields.Datetime(
        string='Last Visit',
        compute='_compute_customer_intelligence',
        store=False,
        help='Date and time of customer\'s last visit'
    )
    
    last_visit_amount = fields.Monetary(
        string='Last Visit Spend',
        compute='_compute_customer_intelligence',
        currency_field='currency_id',
        store=False,
        help='Amount spent on last visit'
    )
    
    total_visits = fields.Integer(
        string='Total Visits',
        compute='_compute_customer_intelligence',
        store=False,
        help='Total number of visits to restaurant'
    )
    
    last_10_visits_total = fields.Monetary(
        string='Last 10 Visits Total',
        compute='_compute_customer_intelligence',
        currency_field='currency_id',
        store=False,
        help='Total spending over last 10 visits'
    )
    
    average_spend_per_visit = fields.Monetary(
        string='Average Spend Per Visit',
        compute='_compute_customer_intelligence',
        currency_field='currency_id',
        store=False,
        help='Average spending per visit (based on last 10 visits)'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    @api.depends('customer_id', 'customer_id.waiting_list_count')
    def _compute_customer_intelligence(self):
        """Compute customer visit history and spending from POS orders"""
        for record in self:
            if not record.customer_id:
                record.last_visit_date = False
                record.last_visit_amount = 0.0
                record.total_visits = 0
                record.last_10_visits_total = 0.0
                record.average_spend_per_visit = 0.0
                continue
            
            # Query POS orders for this customer (only paid/completed orders)
            pos_orders = self.env['pos.order'].search([
                ('partner_id', '=', record.customer_id.id),
                ('state', 'in', ['paid', 'done', 'invoiced'])
            ], order='date_order desc')
            
            if pos_orders:
                # Last visit information from POS
                last_order = pos_orders[0]
                record.last_visit_date = last_order.date_order
                record.last_visit_amount = last_order.amount_total
                
                # Total visits (POS orders count)
                record.total_visits = len(pos_orders)
                
                # Last 10 visits statistics
                last_10_orders = pos_orders[:10]
                record.last_10_visits_total = sum(last_10_orders.mapped('amount_total'))
                record.average_spend_per_visit = record.last_10_visits_total / len(last_10_orders) if last_10_orders else 0.0
            else:
                # No POS orders yet - use waiting list data instead
                # Exclude current record to get actual LAST visit
                waiting_lists = self.env['waiting.list'].search([
                    ('customer_id', '=', record.customer_id.id),
                    ('id', '!=', record.id),  # Exclude current record
                    ('status', 'in', ['seated', 'done'])
                ], order='create_date desc', limit=1)
                
                if waiting_lists:
                    record.last_visit_date = waiting_lists[0].seated_time or waiting_lists[0].create_date
                elif record.customer_id.last_visit_date:
                    # Fallback to partner's computed last_visit_date
                    record.last_visit_date = record.customer_id.last_visit_date
                else:
                    record.last_visit_date = False
                
                record.last_visit_amount = 0.0
                record.total_visits = record.customer_id.waiting_list_count  # Use waiting list count
                record.last_10_visits_total = 0.0
                record.average_spend_per_visit = 0.0
    
    @api.depends('customer_id', 'customer_id.category_id')
    def _compute_is_vip(self):
        """Automatically identify VIP customers based on categories"""
        vip_category = self.env.ref('waiting_list_base.customer_category_vip', raise_if_not_found=False)
        for record in self:
            if vip_category and record.customer_id:
                record.is_vip = vip_category in record.customer_id.category_id
                # Automatically set 5-star priority for VIP customers
                if record.is_vip and record.priority in ['0', '1', '2', '3', '4', False]:
                    record.priority = '5'
            else:
                record.is_vip = False
    
    @api.depends('notification_ids', 'notification_ids.state')
    def _compute_notification_count(self):
        """Compute notification counts by state"""
        for record in self:
            notifications = record.notification_ids
            record.notification_count = len(notifications)
            record.notification_pending_count = len(notifications.filtered(lambda n: n.state == 'pending'))
            record.notification_sent_count = len(notifications.filtered(lambda n: n.state == 'sent'))
            record.notification_failed_count = len(notifications.filtered(lambda n: n.state == 'failed'))
    
    @api.depends('actual_wait_time', 'estimated_wait_time')
    def _compute_wait_time_variance(self):
        """Compute wait time variance and accuracy"""
        for record in self:
            if record.actual_wait_time and record.estimated_wait_time:
                # Variance: positive means waited longer, negative means waited less
                record.wait_time_variance = record.actual_wait_time - record.estimated_wait_time
                
                # Accuracy: 100% - percentage of error
                error_percentage = abs(record.wait_time_variance / record.estimated_wait_time) * 100
                record.wait_time_accuracy = max(0, 100 - error_percentage)
            else:
                record.wait_time_variance = 0
                record.wait_time_accuracy = 0
    
    def _calculate_estimated_wait_time(self):
        """
        Calculate estimated wait time using intelligent algorithm based on historical data.
        Returns tuple: (estimated_time, source_text)
        
        Algorithm:
        1. Analyze last 7 days of actual wait times
        2. Match by: day of week, hour of day, party size
        3. Calculate average from historical data
        4. Add current queue position adjustment
        5. Fallback to simple estimate if insufficient data
        """
        self.ensure_one()
        
        if self.status not in ['waiting', 'ready']:
            return (0, '')
        
        # Try intelligent prediction based on historical data
        historical_estimate = self._get_historical_wait_time(self)
        
        if historical_estimate > 0:
            # Use historical data + current queue adjustment
            queue_adjustment = self._get_queue_adjustment(self)
            estimated_time = historical_estimate + queue_adjustment
            
            # Set source indicator
            if self.create_date:
                day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][self.create_date.weekday()]
                hour = self.create_date.hour
                source = f'Based on {day_name} {hour}:00 historical data'
            else:
                source = 'Based on historical data'
        else:
            # Fallback to simple queue-based estimate
            estimated_time, source = self._get_simple_estimate(self)
        
        return (estimated_time, source)
    
    @api.onchange('pos_config_id', 'floor_id', 'table_id', 'calculation_type', 'manual_wait_time')
    def _onchange_calculate_wait_time(self):
        """Auto-calculate wait time when POS, floor, or table changes (only in auto mode)"""
        if self.status in ['waiting', 'ready']:
            if self.calculation_type == 'manual':
                # Use manual wait time
                self.estimated_wait_time = self.manual_wait_time
                self.wait_time_source = 'Manually entered by host'
            else:
                # Auto calculation
                estimated_time, source = self._calculate_estimated_wait_time()
                self.estimated_wait_time = estimated_time
                self.wait_time_source = source
    
    def _get_historical_wait_time(self, record):
        """
        Analyze historical wait times for similar conditions.
        
        Returns average wait time in minutes, or 0 if insufficient data.
        """
        if not record.create_date:
            return 0
        
        # Get configuration parameters
        historical_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'waiting_list_enterprise.historical_days', 7))
        hour_tolerance = int(self.env['ir.config_parameter'].sudo().get_param(
            'waiting_list_enterprise.hour_tolerance', 1))
        
        # Get current time context
        entry_time = record.create_date
        day_of_week = entry_time.weekday()  # 0=Monday, 6=Sunday
        hour_of_day = entry_time.hour
        party_size = record.party_size
        
        # Look back N days for similar entries
        lookback_days = entry_time - timedelta(days=historical_days)
        
        # Find completed entries (seated or done) with similar characteristics
        domain = [
            ('status', 'in', ['seated', 'done']),
            ('create_date', '>=', lookback_days),
            ('create_date', '<', entry_time),
            ('actual_wait_time', '>', 0),  # Only entries with valid wait times
            ('party_size', '=', party_size),  # Same party size
        ]
        
        # Search for similar entries
        similar_entries = self.env['waiting.list'].search(domain)
        
        if not similar_entries:
            # Try broader search without party size match
            domain = [
                ('status', 'in', ['seated', 'done']),
                ('create_date', '>=', lookback_days),
                ('create_date', '<', entry_time),
                ('actual_wait_time', '>', 0),
            ]
            similar_entries = self.env['waiting.list'].search(domain)
        
        if not similar_entries:
            return 0  # No historical data available
        
        # Filter by same day of week and similar hour
        matching_entries = similar_entries.filtered(
            lambda e: e.create_date.weekday() == day_of_week and 
                     abs(e.create_date.hour - hour_of_day) <= hour_tolerance
        )
        
        if not matching_entries:
            # Fallback: same hour of day on any day of week
            matching_entries = similar_entries.filtered(
                lambda e: abs(e.create_date.hour - hour_of_day) <= hour_tolerance
            )
        
        if not matching_entries:
            # Fallback: any time, same day of week
            matching_entries = similar_entries.filtered(
                lambda e: e.create_date.weekday() == day_of_week
            )
        
        if not matching_entries:
            return 0  # Still no matches
        
        # Calculate average wait time from matching entries
        total_wait = sum(matching_entries.mapped('actual_wait_time'))
        average_wait = total_wait / len(matching_entries)
        
        return round(average_wait, 1)
    
    def _get_queue_adjustment(self, record):
        """Calculate adjustment based on current queue position."""
        # Get configuration parameter
        queue_time_per_person = int(self.env['ir.config_parameter'].sudo().get_param(
            'waiting_list_enterprise.queue_time_per_person', 1))
        
        # Count customers ahead in queue with equal or higher priority
        ahead_count = self.search_count([
            ('status', 'in', ['waiting', 'ready', 'called']),
            ('create_date', '<', record.create_date),
            ('id', '!=', record.id),
            '|',
            ('priority', '>', record.priority),
            '&',
            ('priority', '=', record.priority),
            ('create_date', '<', record.create_date)
        ])
        
        # Each person ahead adds configured minutes
        return ahead_count * queue_time_per_person
    
    def _get_simple_estimate(self, record):
        """
        Simple fallback estimate when historical data is unavailable.
        Based on queue position only (party size not considered).
        Result is clamped between configured minimum and maximum values.
        Returns tuple: (estimated_time, source_text)
        """
        # Get configuration parameters
        simple_time_per_person = int(self.env['ir.config_parameter'].sudo().get_param(
            'waiting_list_enterprise.simple_time_per_person', 1))
        minimum_wait_time = int(self.env['ir.config_parameter'].sudo().get_param(
            'waiting_list_enterprise.minimum_wait_time', 10))
        maximum_wait_time = int(self.env['ir.config_parameter'].sudo().get_param(
            'waiting_list_enterprise.maximum_wait_time', 60))
        
        # Get current waiting customers with higher priority
        higher_priority_count = self.search_count([
            ('status', 'in', ['waiting', 'ready', 'called']),
            ('priority', '>', record.priority),
            ('create_date', '<', record.create_date),
            ('id', '!=', record.id)
        ])
        
        # Base estimate: configured minutes per party ahead in queue
        base_estimate = higher_priority_count * simple_time_per_person
        
        # Clamp result between minimum and maximum wait time and set source
        if base_estimate < minimum_wait_time:
            base_estimate = minimum_wait_time
            source = f'Minimum wait time ({minimum_wait_time} min) - {higher_priority_count} customers ahead'
        elif base_estimate > maximum_wait_time:
            base_estimate = maximum_wait_time
            source = f'Maximum wait time limit ({maximum_wait_time} min) - {higher_priority_count} customers ahead'
        else:
            source = f'Based on current queue position ({higher_priority_count} customers ahead)'
        
        return (base_estimate, source)
    
    def _default_pos_config_id(self):
        """Get the last used POS config for current user, or first available"""
        # Try user's last used POS
        if self.env.user.last_waiting_list_pos_id:
            return self.env.user.last_waiting_list_pos_id.id
        
        # Fallback: get first available POS with restaurant module
        pos_config = self.env['pos.config'].search([
            ('module_pos_restaurant', '=', True)
        ], limit=1)
        
        return pos_config.id if pos_config else False
    
    def _default_floor_id(self):
        """Get the last used floor for current user, or first available"""
        # Try user's last used floor
        floor = self.env.user.last_waiting_list_floor_id
        if floor and floor.exists():
            return floor.id
        
        # Fallback: get first floor from default POS
        pos_id = self._default_pos_config_id()
        if pos_id:
            floor = self.env['restaurant.floor'].search([
                ('pos_config_ids', 'in', [pos_id])
            ], limit=1)
            return floor.id if floor else False
        
        return False
    
    @api.onchange('pos_config_id')
    def _onchange_pos_config_id(self):
        """Save last used POS config and reset floor if POS changes"""
        if self.pos_config_id:
            # Save to user preferences
            self.env.user.sudo().write({
                'last_waiting_list_pos_id': self.pos_config_id.id
            })
            # Reset floor if it doesn't belong to this POS
            if self.floor_id and self.pos_config_id not in self.floor_id.pos_config_ids:
                self.floor_id = False
    
    @api.onchange('floor_id')
    def _onchange_floor_id(self):
        """Reset table when floor changes and save preference"""
        if self.floor_id:
            # Save to user preferences
            self.env.user.sudo().write({
                'last_waiting_list_floor_id': self.floor_id.id
            })
            self.table_id = False
    
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """Set preferred seating based on customer's last selection"""
        if self.customer_id:
            # Find customer's last waiting list entry
            last_entry = self.env['waiting.list'].search([
                ('customer_id', '=', self.customer_id.id),
                ('preferred_seating', '!=', False)
            ], order='create_date desc', limit=1)
            
            if last_entry and last_entry.preferred_seating:
                # Use customer's last preference
                self.preferred_seating = last_entry.preferred_seating
            else:
                # New customer - default to outdoor
                self.preferred_seating = 'outdoor'
    
    @api.onchange('party_size')
    def _onchange_number_of_guests(self):
        """Suggest appropriate table based on number of guests"""
        if self.party_size and self.floor_id:
            # Find tables that can accommodate the party
            suitable_tables = self.env['restaurant.table'].search([
                ('floor_id', '=', self.floor_id.id),
                ('seats', '>=', self.party_size),
                ('active', '=', True)
            ], order='seats asc', limit=1)
            
            if suitable_tables:
                self.table_id = suitable_tables[0]
    
    def action_assign_table(self):
        """Assign a table to the waiting customer"""
        self.ensure_one()
        
        if not self.table_id:
            raise UserError(_('Please select a table first.'))
        
        if self.status not in ['waiting', 'ready', 'called']:
            raise UserError(_('Can only assign tables to waiting, ready, or called customers.'))
        
        # Check if table is already occupied
        occupied = self.search([
            ('table_id', '=', self.table_id.id),
            ('status', '=', 'seated'),
            ('id', '!=', self.id)
        ], limit=1)
        
        self.write({
            'table_assigned_time': fields.Datetime.now(),
            'status': 'ready'
        })
        
        # Show warning if table is occupied, but still allow assignment
        if occupied:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning: Table Occupied'),
                    'message': _('⚠️ Table %s is currently occupied by %s, but has been assigned to %s') % (
                        self.table_id.display_name, 
                        occupied.customer_name,
                        self.customer_id.name
                    ),
                    'type': 'warning',
                    'sticky': True,
                }
            }
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Table Assigned'),
                'message': _('Table %s has been assigned to %s') % (self.table_id.display_name, self.customer_id.name),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_seat_at_table(self):
        """Seat the customer at the assigned table"""
        self.ensure_one()
        
        if not self.table_id:
            raise UserError(_('Please assign a table first.'))
        
        self.action_mark_seated()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Customer Seated'),
                'message': _('%s has been seated at %s') % (self.customer_id.name, self.table_id.display_name),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_send_notification(self):
        """Send notification to customer that table is ready"""
        self.ensure_one()
        
        if not self.table_id:
            raise UserError(_('Please assign a table before notifying the customer.'))
        
        if not self.customer_mobile and not self.customer_phone:
            raise UserError(_('Customer has no phone number for notification.'))
        
        # Determine notification type from field or default to SMS
        notification_type = self.notification_type or 'sms'
        
        # Create notification in queue
        notification = self.env['waiting.list.notification'].create_notification(
            waiting_list_id=self.id,
            notification_type=notification_type,
            scheduled_time=fields.Datetime.now()  # Send immediately
        )
        
        # Mark notification as sent (queued)
        self.write({
            'notification_sent': True,
            'notification_time': fields.Datetime.now(),
            'status': 'called'
        })
        
        # Trigger immediate send (or let cron handle it)
        try:
            notification.action_send()
            message = _('Customer %s will be notified via %s that table %s is ready') % (
                self.customer_id.name,
                dict(notification._fields['notification_type'].selection).get(notification_type),
                self.table_id.display_name
            )
            notification_title = _('Notification Queued')
        except Exception as e:
            _logger.error('Failed to send notification immediately: %s', str(e))
            message = _('Notification queued for %s. Will be sent shortly.') % self.customer_id.name
            notification_title = _('Notification Queued')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': notification_title,
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_suggest_tables(self):
        """Suggest tables for this party - show all tables with occupied ones highlighted"""
        self.ensure_one()
        
        if not self.floor_id:
            raise UserError(_('Please select a floor first.'))
        
        # Find suitable tables
        suitable_tables = self.env['restaurant.table'].search([
            ('floor_id', '=', self.floor_id.id),
            ('seats', '>=', self.party_size),
            ('active', '=', True)
        ])
        
        # Get occupied table IDs (don't filter them out, just mark them)
        occupied_table_ids = self.search([
            ('status', '=', 'seated'),
            ('table_id', 'in', suitable_tables.ids)
        ]).mapped('table_id.id')
        
        if not suitable_tables:
            raise UserError(_('No suitable tables available on this floor for %d guests.') % self.party_size)
        
        # Return action to select from all suitable tables
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tables for %d Guests (Red = Occupied)') % self.party_size,
            'res_model': 'restaurant.table',
            'view_mode': 'kanban,list',
            'domain': [('id', 'in', suitable_tables.ids)],
            'context': {
                'default_floor_id': self.floor_id.id,
                'search_default_floor_id': self.floor_id.id,
                'occupied_table_ids': occupied_table_ids,  # Pass occupied table IDs to view
            },
            'target': 'new',
        }
    
    def action_recalculate_wait_time(self):
        """Recalculate estimated wait time based on current queue and conditions"""
        self.ensure_one()
        
        if self.status not in ['waiting', 'ready']:
            raise UserError(_('Wait time can only be calculated for waiting or ready customers.'))
        
        if self.calculation_type == 'manual':
            raise UserError(_('Cannot recalculate wait time in Manual mode. Please switch to Auto Calculation or adjust the Manual Wait Time field.'))
        
        estimated_time, source = self._calculate_estimated_wait_time()
        self.write({
            'estimated_wait_time': estimated_time,
            'wait_time_source': source
        })
        
        # Show notification and reload form to display updated value
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Wait Time Recalculated'),
                'message': _('New estimated wait time: %d minutes\n%s') % (int(estimated_time), source),
                'type': 'info',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'waiting.list',
                    'res_id': self.id,
                    'views': [(False, 'form')],
                    'target': 'current',
                }
            }
        }
    
    def action_view_notifications(self):
        """View all notifications for this waiting list entry"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Notifications for %s') % self.name,
            'res_model': 'waiting.list.notification',
            'view_mode': 'list,form',
            'domain': [('waiting_list_id', '=', self.id)],
            'context': {
                'default_waiting_list_id': self.id,
                'default_customer_id': self.customer_id.id,
                'default_notification_type': self.notification_type or 'sms',
                'default_phone_number': self.customer_mobile or self.customer_phone,
            },
        }
    
    @api.constrains('table_id', 'party_size')
    def _check_table_capacity(self):
        """Ensure selected table can accommodate party size"""
        for record in self:
            if record.table_id and record.party_size > record.table_id.seats:
                raise ValidationError(_(
                    'The selected table (capacity: %d) cannot accommodate a party of %d guests. '
                    'Please select a larger table.'
                ) % (record.table_id.seats, record.party_size))
    
    @api.constrains('waiting_type', 'table_id', 'status')
    def _check_walkin_table(self):
        """Ensure walk-ins have a table selected before seating"""
        for record in self:
            # Only check if it's a walk-in and not in terminal status
            if (record.waiting_type == 'walkin' and 
                not record.table_id and 
                record.status not in ['cancelled', 'no_show', 'done', 'seated']):
                raise ValidationError(_(
                    'Walk-in customers must have a table assigned. '
                    'Please select a table before saving.'
                ))
    
    @api.model
    def create(self, vals):
        """Override create to send initial queue notification or auto-seat walk-ins"""
        record = super(WaitingListEnterprise, self).create(vals)
        
        # Calculate estimated wait time if not provided
        if record.status in ['waiting', 'ready'] and not record.estimated_wait_time:
            if record.calculation_type == 'manual' and record.manual_wait_time:
                # Use manual wait time
                record.write({
                    'estimated_wait_time': record.manual_wait_time,
                    'wait_time_source': 'Manually entered by host'
                })
            else:
                # Auto calculation
                estimated_time, source = record._calculate_estimated_wait_time()
                record.write({
                    'estimated_wait_time': estimated_time,
                    'wait_time_source': source
                })
        
        # Walk-in workflow: auto-seat if table is selected
        if record.waiting_type == 'walkin' and record.table_id:
            try:
                # Mark as seated immediately (bypass status check for walk-ins)
                record.write({
                    'status': 'seated',
                    'seated_time': fields.Datetime.now(),
                    'table_assigned_time': fields.Datetime.now()
                })
                _logger.info('Walk-in %s auto-seated at table %s', record.name, record.table_id.display_name)
            except Exception as e:
                _logger.warning('Failed to auto-seat walk-in %s: %s', record.name, str(e))
        
        # Regular waiting list workflow: send queue notification
        elif record.waiting_type == 'waitlist' and record.auto_send_queue_notification and (record.customer_mobile or record.customer_phone):
            try:
                record.action_send_queue_notification()
            except Exception as e:
                _logger.warning('Failed to send queue notification for %s: %s', record.name, str(e))
        
        return record
    
    def write(self, vals):
        """Override write to auto-seat walk-ins when table is assigned"""
        # Before write, check if we're assigning a table to a walk-in
        for record in self:
            # Check if table is being assigned and it's a walk-in
            table_being_assigned = 'table_id' in vals and vals['table_id'] and not record.table_id
            is_walkin = vals.get('waiting_type') == 'walkin' or (record.waiting_type == 'walkin' and 'waiting_type' not in vals)
            not_already_seated = record.status not in ['seated', 'done', 'cancelled', 'no_show']
            
            if table_being_assigned and is_walkin and not_already_seated:
                # Auto-seat the walk-in customer
                vals.update({
                    'status': 'seated',
                    'seated_time': fields.Datetime.now(),
                    'table_assigned_time': fields.Datetime.now()
                })
                _logger.info('Walk-in %s auto-seated at table via write', record.name)
        
        return super(WaitingListEnterprise, self).write(vals)
    
    def action_send_queue_notification(self):
        """Send notification that customer has been added to queue"""
        self.ensure_one()
        
        if not self.customer_mobile and not self.customer_phone:
            raise UserError(_('Customer has no phone number for notification.'))
        
        # Determine notification type from field or default to SMS
        notification_type = self.notification_type or 'sms'
        
        # Create notification with queue message
        notification = self.env['waiting.list.notification'].create({
            'waiting_list_id': self.id,
            'customer_id': self.customer_id.id,
            'notification_type': notification_type,
            'phone_number': self.customer_mobile or self.customer_phone,
            'message': self._prepare_queue_notification_message(),
            'template_type': 'queue_added',  # Explicitly set template type
            'state': 'pending',
            'scheduled_time': fields.Datetime.now(),
        })
        
        # Try to send immediately
        try:
            notification.action_send()
            _logger.info('Queue notification sent to %s for waiting list %s', self.customer_name, self.name)
        except Exception as e:
            _logger.error('Failed to send queue notification: %s', str(e))
        
        return True
    
    def _prepare_queue_notification_message(self):
        """Prepare message for queue notification
        
        This message is used to trigger WhatsApp template selection.
        The actual message sent will be the approved WhatsApp template.
        """
        self.ensure_one()
        
        # Simple message to trigger template selection
        # The wa_template_id will be set based on keywords "added to" and "waiting list"
        message = f"You have been added to the waiting list at {self.company_id.name}"
        
        return message

    def action_refresh_table_status(self):
        """Refresh table status from Foodics API
        
        This method fetches the current table status from Foodics and updates
        the table information in Odoo. It uses the company_id from the waiting
        list entry to ensure proper multi-company isolation.
        """
        self.ensure_one()
        
        if not self.table_id:
            raise UserError(_('No table assigned to refresh status.'))
        
        # Check if table has Foodics ID
        if not hasattr(self.table_id, 'foodics_id') or not self.table_id.foodics_id:
            raise UserError(_('Table "%s" is not linked to Foodics. Cannot refresh status.') % self.table_id.display_name)
        
        # Get company for this waiting list entry
        company_id = self.company_id.id if self.company_id else self.env.company.id
        
        try:
            # Search for Foodics table sync configuration for this company
            table_sync = self.env['foodics.table.sync'].search([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ], limit=1)
            
            if not table_sync:
                raise UserError(_('Foodics table synchronization is not configured for company "%s".\n\nPlease configure it in Foodics > Table Sync.') % self.company_id.name)
            
            # Get table status from Foodics
            _logger.info('Refreshing table status from Foodics for table %s (Foodics ID: %s) - Company: %s', 
                        self.table_id.display_name, self.table_id.foodics_id, self.company_id.name)
            
            table_data = table_sync.get_table_status_from_foodics(self.table_id.foodics_id)
            
            # Log full response for debugging
            _logger.info('Full Foodics table data: %s', table_data)
            
            # Map Foodics status to Odoo (if needed)
            foodics_status = table_data.get('status')
            status_mapping = {
                0: 'Inactive/Unavailable',
                1: 'Available',
                2: 'Occupied',
                3: 'Reserved'
            }
            status_text = status_mapping.get(foodics_status, f'Unknown ({foodics_status})')
            
            # Extract additional information from response
            table_name = table_data.get('name', 'N/A')
            seats = table_data.get('seats', 'N/A')
            section_data = table_data.get('section', {})
            section_name = section_data.get('name', 'N/A') if section_data else 'N/A'
            
            _logger.info('Table %s status from Foodics: %s (%s), Seats: %s, Section: %s', 
                        self.table_id.display_name, foodics_status, status_text, seats, section_name)
            
            # Update the table's foodics_status field for display
            if hasattr(self.table_id, 'foodics_status'):
                self.table_id.write({'foodics_status': foodics_status})
            
            # Post message to chatter with status update
            self.message_post(
                body=_('<b>Table Status Refreshed from Foodics</b><br/>'
                      'Table: %s<br/>'
                      'Foodics ID: %s<br/>'
                      'Status: %s<br/>'
                      'Seats: %s<br/>'
                      'Section: %s') % (
                    table_name,
                    self.table_id.foodics_id,
                    status_text,
                    seats,
                    section_name
                ),
                message_type='notification'
            )
            
            # Show success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Table Status Refreshed'),
                    'message': _('Table "%s" status: %s') % (self.table_id.display_name, status_text),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except UserError as e:
            # Re-raise UserError as-is
            raise
        except Exception as e:
            _logger.error('Error refreshing table status from Foodics: %s', str(e), exc_info=True)
            raise UserError(_('Failed to refresh table status from Foodics:\n\n%s\n\nPlease check the logs for more details.') % str(e))
