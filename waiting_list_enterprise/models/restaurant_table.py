# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RestaurantTable(models.Model):
    """Extend restaurant table with waiting list integration"""
    
    _inherit = 'restaurant.table'
    
    # Waiting List Integration
    waiting_list_ids = fields.One2many(
        'waiting.list',
        'table_id',
        string='Waiting List Entries',
        help='Waiting list entries assigned to this table'
    )
    
    current_waiting_list_id = fields.Many2one(
        'waiting.list',
        string='Current Guest',
        compute='_compute_current_waiting_list',
        help='Currently seated guest at this table'
    )
    
    is_occupied = fields.Boolean(
        string='Occupied',
        compute='_compute_table_status',
        help='Whether this table is currently occupied'
    )
    
    waiting_count = fields.Integer(
        string='Waiting Count',
        compute='_compute_waiting_count',
        help='Number of customers waiting for this specific table'
    )
    
    is_reserved_for_waiting = fields.Boolean(
        string='Reserved for Waiting List',
        compute='_compute_reservation_status',
        help='Table is assigned to a customer in waiting list (ready/called) but not seated yet'
    )
    
    reserved_customer_name = fields.Char(
        string='Reserved For',
        compute='_compute_reservation_status',
        help='Name of customer who has this table reserved'
    )
    
    reserved_waiting_list_id = fields.Many2one(
        'waiting.list',
        string='Reserved Waiting List',
        compute='_compute_reservation_status',
        help='Waiting list entry that has reserved this table'
    )
    
    table_status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved (Waiting List)'),
        ('occupied', 'Occupied'),
    ], string='Table Status', compute='_compute_table_status_combined', store=False)
    
    foodics_status = fields.Integer(
        string='Foodics Status',
        help='Real-time status from Foodics API: 0=Inactive, 1=Available, 2=Occupied, 3=Reserved'
    )
    
    foodics_status_text = fields.Char(
        string='Foodics Status Text',
        compute='_compute_foodics_status_text',
        help='Human-readable Foodics status'
    )
    
    @api.depends('waiting_list_ids', 'waiting_list_ids.status')
    def _compute_current_waiting_list(self):
        """Get the current seated guest at this table"""
        for table in self:
            current = table.waiting_list_ids.filtered(lambda w: w.status == 'seated')
            table.current_waiting_list_id = current[0] if current else False
    
    @api.depends('current_waiting_list_id')
    def _compute_table_status(self):
        """Determine if table is occupied"""
        for table in self:
            table.is_occupied = bool(table.current_waiting_list_id)
    
    @api.depends('waiting_list_ids', 'waiting_list_ids.status')
    def _compute_waiting_count(self):
        """Count customers waiting for this table"""
        for table in self:
            table.waiting_count = len(table.waiting_list_ids.filtered(
                lambda w: w.status in ['waiting', 'ready', 'called']
            ))
    
    @api.depends('waiting_list_ids', 'waiting_list_ids.status', 'waiting_list_ids.customer_id')
    def _compute_reservation_status(self):
        """Check if table is reserved for a waiting list customer (assigned but not seated)"""
        for table in self:
            reserved = table.waiting_list_ids.filtered(
                lambda w: w.status in ['ready', 'called'] and w.table_id.id == table.id
            )
            if reserved:
                # Take the first one (should only be one)
                reservation = reserved[0]
                table.is_reserved_for_waiting = True
                table.reserved_customer_name = reservation.customer_name
                table.reserved_waiting_list_id = reservation.id
            else:
                table.is_reserved_for_waiting = False
                table.reserved_customer_name = False
                table.reserved_waiting_list_id = False
    
    @api.depends('is_occupied', 'is_reserved_for_waiting')
    def _compute_table_status_combined(self):
        """Compute combined table status"""
        for table in self:
            if table.is_occupied:
                table.table_status = 'occupied'
            elif table.is_reserved_for_waiting:
                table.table_status = 'reserved'
            else:
                table.table_status = 'available'
    
    @api.depends('foodics_status')
    def _compute_foodics_status_text(self):
        """Convert Foodics status code to text"""
        status_mapping = {
            0: 'Inactive',
            1: 'Available',
            2: 'Occupied',
            3: 'Reserved',
        }
        for table in self:
            if table.foodics_status is not False:
                table.foodics_status_text = status_mapping.get(table.foodics_status, f'Unknown ({table.foodics_status})')
            else:
                table.foodics_status_text = 'Not Synced'
    
    def action_view_waiting_list(self):
        """View waiting list entries for this table"""
        self.ensure_one()
        
        return {
            'name': _('Waiting List - Table %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'waiting.list',
            'view_mode': 'tree,form',
            'domain': [('table_id', '=', self.id)],
            'context': {
                'default_table_id': self.id,
                'default_floor_id': self.floor_id.id,
                'default_party_size': self.seats,
            },
        }
    
    def action_assign_to_waiting_customer(self):
        """Quick action to assign table to next waiting customer"""
        self.ensure_one()
        
        if self.is_occupied:
            raise UserError(_('This table is currently occupied.'))
        
        # Find next waiting customer that fits this table
        next_customer = self.env['waiting.list'].search([
            ('status', 'in', ['waiting', 'ready']),
            ('floor_id', '=', self.floor_id.id),
            ('party_size', '<=', self.seats),
            ('table_id', '=', False),
        ], order='priority desc, create_date asc', limit=1)
        
        if not next_customer:
            raise UserError(_('No suitable waiting customers found for this table.'))
        
        next_customer.write({
            'table_id': self.id,
            'table_assigned_time': fields.Datetime.now(),
            'status': 'ready'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Table Assigned'),
                'message': _('Table %s assigned to %s (%d Guests)') % (
                    self.display_name,
                    next_customer.customer_id.name,
                    next_customer.party_size
                ),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_select_for_waiting_list(self):
        """Select this table for a waiting list entry (called from suggestion popup)"""
        self.ensure_one()
        
        # Get the active waiting list entry from context
        active_id = self.env.context.get('active_id')
        if not active_id:
            raise UserError(_('No waiting list entry found in context.'))
        
        waiting_list = self.env['waiting.list'].browse(active_id)
        if not waiting_list.exists():
            raise UserError(_('Waiting list entry not found.'))
        
        # Check if table is reserved for someone else
        warning_message = ''
        if self.is_reserved_for_waiting and self.reserved_waiting_list_id.id != waiting_list.id:
            warning_message = _('⚠️ Warning: This table is already reserved for %s!\\n') % self.reserved_customer_name
        
        # Check if table is occupied
        if self.is_occupied:
            occupied_customer = self.current_waiting_list_id.customer_name if self.current_waiting_list_id else 'another customer'
            warning_message += _('⚠️ Warning: This table is currently occupied by %s!\\n') % occupied_customer
        
        # Assign table
        waiting_list.write({
            'table_id': self.id,
            'floor_id': self.floor_id.id,
            'table_assigned_time': fields.Datetime.now(),
            'status': 'ready',
        })
        
        # Prepare success message
        success_message = _('Table %s (%s) assigned to %s (%d guests)') % (
            self.table_number,
            self.floor_id.name,
            waiting_list.customer_id.name,
            waiting_list.party_size
        )
        
        if warning_message:
            success_message = warning_message + '\\n' + success_message
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Table Assigned') if not warning_message else _('Table Assigned (With Warnings)'),
                'message': success_message,
                'type': 'warning' if warning_message else 'success',
                'sticky': bool(warning_message),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class RestaurantFloor(models.Model):
    """Extend restaurant floor with waiting list analytics"""
    
    _inherit = 'restaurant.floor'
    
    waiting_list_count = fields.Integer(
        string='Waiting Customers',
        compute='_compute_waiting_statistics',
        help='Number of customers waiting for tables on this floor'
    )
    
    occupied_tables_count = fields.Integer(
        string='Occupied Tables',
        compute='_compute_table_statistics',
        help='Number of currently occupied tables'
    )
    
    available_tables_count = fields.Integer(
        string='Available Tables',
        compute='_compute_table_statistics',
        help='Number of available tables'
    )
    
    @api.depends('table_ids', 'table_ids.waiting_list_ids', 'table_ids.waiting_list_ids.status')
    def _compute_waiting_statistics(self):
        """Calculate waiting list statistics for this floor"""
        for floor in self:
            waiting_entries = self.env['waiting.list'].search([
                ('floor_id', '=', floor.id),
                ('status', 'in', ['waiting', 'ready', 'called'])
            ])
            floor.waiting_list_count = len(waiting_entries)
    
    @api.depends('table_ids', 'table_ids.is_occupied')
    def _compute_table_statistics(self):
        """Calculate table statistics for this floor"""
        for floor in self:
            active_tables = floor.table_ids.filtered(lambda t: t.active)
            floor.occupied_tables_count = len(active_tables.filtered(lambda t: t.is_occupied))
            floor.available_tables_count = len(active_tables) - floor.occupied_tables_count
    
    def action_view_waiting_list(self):
        """View all waiting list entries for this floor"""
        self.ensure_one()
        
        return {
            'name': _('Waiting List - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'waiting.list',
            'view_mode': 'tree,kanban,form',
            'domain': [('floor_id', '=', self.id)],
            'context': {
                'default_floor_id': self.id,
            },
        }
