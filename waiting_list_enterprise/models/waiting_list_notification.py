# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class WaitingListNotification(models.Model):
    """Queue for waiting list notifications to be sent via SMS/WhatsApp"""
    
    _name = 'waiting.list.notification'
    _description = 'Waiting List Notification Queue'
    _order = 'create_date desc'
    _rec_name = 'waiting_list_id'
    
    waiting_list_id = fields.Many2one(
        'waiting.list',
        string='Waiting List Entry',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        related='waiting_list_id.customer_id',
        string='Customer',
        store=True,
        readonly=True
    )
    
    notification_type = fields.Selection([
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('sms_whatsapp', 'SMS + WhatsApp'),
        ('call', 'Phone Call'),
    ], string='Notification Type', required=True, index=True)
    
    phone_number = fields.Char(
        string='Phone Number',
        required=True,
        help='Phone number to send notification to'
    )
    
    message = fields.Text(
        string='Message',
        required=True,
        help='Message content to be sent'
    )
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True, index=True)
    
    scheduled_time = fields.Datetime(
        string='Scheduled Time',
        default=fields.Datetime.now,
        help='When this notification should be sent'
    )
    
    sent_time = fields.Datetime(
        string='Sent Time',
        readonly=True,
        help='When the notification was actually sent'
    )
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True,
        help='Error details if sending failed'
    )
    
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        readonly=True,
        help='Number of times sending was attempted'
    )
    
    max_retries = fields.Integer(
        string='Max Retries',
        default=3,
        help='Maximum number of retry attempts'
    )
    
    company_id = fields.Many2one(
        'res.company',
        related='waiting_list_id.company_id',
        string='Company',
        store=True,
        readonly=True
    )
    
    # SMS-specific fields (if using Odoo SMS module)
    sms_id = fields.Many2one(
        'sms.sms',
        string='SMS Record',
        readonly=True,
        help='Link to Odoo SMS record if SMS module is used'
    )
    
    @api.model
    def _prepare_message_content(self, waiting_list):
        """Prepare notification message content based on waiting list entry"""
        table_info = waiting_list.table_id.display_name if waiting_list.table_id else _('your table')
        
        # Get customer's preferred language
        lang = waiting_list.customer_id.lang or self.env.user.lang or 'en_US'
        
        # Arabic message
        if lang.startswith('ar'):
            message = f"""مرحباً {waiting_list.customer_name}،

طاولتك جاهزة الآن!
الطاولة: {table_info}
عدد الضيوف: {waiting_list.party_size}

يرجى التوجه إلى المضيف عند وصولك.

شكراً لانتظاركم - {waiting_list.company_id.name}"""
        else:
            # English message
            message = f"""Hello {waiting_list.customer_name},

Your table is ready!
Table: {table_info}
Number of Guests: {waiting_list.party_size}

Please proceed to the host when you arrive.

Thank you for waiting - {waiting_list.company_id.name}"""
        
        return message
    
    @api.model
    def create_notification(self, waiting_list_id, notification_type=None, scheduled_time=None):
        """Create a new notification for a waiting list entry"""
        waiting_list = self.env['waiting.list'].browse(waiting_list_id)
        
        if not waiting_list.exists():
            raise UserError(_('Waiting list entry not found.'))
        
        # Determine notification type
        if not notification_type:
            notification_type = waiting_list.notification_type or 'sms'
        
        # Get phone number
        phone_number = waiting_list.customer_mobile or waiting_list.customer_phone
        if not phone_number:
            raise UserError(_('Customer has no phone number for notification.'))
        
        # Prepare message
        message = self._prepare_message_content(waiting_list)
        
        # Create notification record
        notification = self.create({
            'waiting_list_id': waiting_list.id,
            'notification_type': notification_type,
            'phone_number': phone_number,
            'message': message,
            'state': 'pending',
            'scheduled_time': scheduled_time or fields.Datetime.now(),
        })
        
        _logger.info(
            'Created %s notification #%d for waiting list %s (customer: %s)',
            notification_type, notification.id, waiting_list.name, waiting_list.customer_name
        )
        
        # Try to send immediately instead of waiting for cron
        try:
            _logger.info('Attempting to send notification #%d immediately', notification.id)
            notification.action_send()
            _logger.info('Notification #%d sent immediately', notification.id)
        except Exception as e:
            _logger.warning('Failed to send notification #%d immediately, will retry via cron: %s', 
                          notification.id, str(e))
            # Leave it in pending state for cron to retry
        
        return notification
    
    def action_send(self):
        """Send the notification immediately"""
        for notification in self:
            if notification.state in ('sent', 'cancelled'):
                continue
            
            notification.write({
                'state': 'processing',
                'retry_count': notification.retry_count + 1
            })
            
            try:
                success = True
                error_messages = []
                
                if notification.notification_type == 'sms':
                    notification._send_sms()
                elif notification.notification_type == 'whatsapp':
                    notification._send_whatsapp()
                elif notification.notification_type == 'sms_whatsapp':
                    # Send both SMS and WhatsApp - try both even if one fails
                    try:
                        notification._send_sms()
                        _logger.info('SMS sent successfully for notification #%d', notification.id)
                    except Exception as e:
                        error_messages.append(f'SMS failed: {str(e)}')
                        _logger.error('SMS failed for notification #%d: %s', notification.id, str(e))
                        success = False
                    
                    try:
                        notification._send_whatsapp()
                        _logger.info('WhatsApp sent successfully for notification #%d', notification.id)
                    except Exception as e:
                        error_messages.append(f'WhatsApp failed: {str(e)}')
                        _logger.error('WhatsApp failed for notification #%d: %s', notification.id, str(e))
                        success = False
                    
                    # If at least one succeeded, mark as sent
                    if len(error_messages) < 2:
                        success = True
                    
                    # If both failed, raise exception
                    if not success:
                        raise UserError(_('Both SMS and WhatsApp failed: %s') % ' | '.join(error_messages))
                        
                elif notification.notification_type == 'call':
                    notification._send_call_notification()
                
                notification.write({
                    'state': 'sent',
                    'sent_time': fields.Datetime.now(),
                    'error_message': ' | '.join(error_messages) if error_messages else False,
                })
                
                _logger.info('Sent %s notification #%d successfully', notification.notification_type, notification.id)
                
            except Exception as e:
                error_msg = str(e)
                _logger.error('Failed to send notification #%d: %s', notification.id, error_msg)
                
                # Check if we should retry
                if notification.retry_count >= notification.max_retries:
                    notification.write({
                        'state': 'failed',
                        'error_message': error_msg,
                    })
                else:
                    # Reset to pending for retry
                    notification.write({
                        'state': 'pending',
                        'error_message': error_msg,
                    })
        
        return True
    
    def _send_sms(self):
        """Send SMS using Odoo SMS module"""
        self.ensure_one()
        
        # Check if SMS module is installed
        if not hasattr(self.env['ir.model'], 'search') or \
           not self.env['ir.model'].search([('model', '=', 'sms.sms')], limit=1):
            # SMS module not installed, just log the message
            _logger.warning(
                'SMS module not installed. Would send SMS to %s: %s',
                self.phone_number, self.message
            )
            # For demo/testing without SMS module, we'll just mark as sent
            return True
        
        # Use Odoo SMS module
        sms = self.env['sms.sms'].create({
            'number': self.phone_number,
            'body': self.message,
            'partner_id': self.customer_id.id if self.customer_id else False,
        })
        
        self.sms_id = sms.id
        sms.send()
        
        return True
    
    def _send_whatsapp(self):
        """Send WhatsApp message using whatsapp_waitinglist module integration"""
        self.ensure_one()
        
        _logger.info('=== _send_whatsapp called for notification #%d ===', self.id)
        _logger.info('Notification type: %s, State: %s, Phone: %s', 
                     self.notification_type, self.state, self.phone_number)
        
        # Check if whatsapp_waitinglist module is installed
        has_method = hasattr(self, 'action_send_whatsapp')
        _logger.info('Has action_send_whatsapp method: %s', has_method)
        
        if has_method:
            # Use the whatsapp_waitinglist module method
            _logger.info('Using whatsapp_waitinglist module to send WhatsApp notification #%d', self.id)
            try:
                result = self.action_send_whatsapp()
                _logger.info('action_send_whatsapp returned: %s', result)
                return result
            except Exception as e:
                _logger.error('action_send_whatsapp failed: %s', str(e), exc_info=True)
                raise
        
        # Fallback to Odoo Enterprise WhatsApp module if whatsapp_waitinglist not installed
        # Check if WhatsApp module is installed
        if not hasattr(self.env, 'whatsapp.message'):
            _logger.warning(
                'WhatsApp module not installed. Would send WhatsApp to %s: %s',
                self.phone_number, self.message
            )
            return True
        
        # Get the default WhatsApp account
        wa_account = self.env['whatsapp.account'].search([], limit=1)
        if not wa_account:
            raise UserError(_('No WhatsApp Business Account configured. Please configure one in Settings > Technical > WhatsApp.'))
        
        # Create WhatsApp message
        try:
            # Format phone number for WhatsApp
            formatted_number = self._format_phone_for_whatsapp(self.phone_number)
            
            # Create mail message first (WhatsApp messages are linked to mail.message)
            mail_message = self.env['mail.message'].create({
                'body': self.message,
                'message_type': 'comment',
                'model': 'waiting.list',
                'res_id': self.waiting_list_id.id,
                'partner_ids': [(4, self.customer_id.id)] if self.customer_id else [],
            })
            
            # Create WhatsApp message
            wa_message = self.env['whatsapp.message'].create({
                'mobile_number': formatted_number,
                'wa_account_id': wa_account.id,
                'mail_message_id': mail_message.id,
                'message_type': 'outbound',
                'state': 'outgoing',
            })
            
            # Send the message
            wa_message._send()
            
            _logger.info(
                'WhatsApp notification sent to %s for waiting list %s',
                self.phone_number, self.waiting_list_id.name
            )
            
            return True
            
        except Exception as e:
            _logger.error('Failed to send WhatsApp message: %s', str(e))
            raise UserError(_('Failed to send WhatsApp message: %s') % str(e))
    
    def _format_phone_for_whatsapp(self, phone_number):
        """Format phone number for WhatsApp (remove spaces, dashes, etc.)"""
        if not phone_number:
            return ''
        
        # Remove common separators
        formatted = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Ensure it starts with +
        if not formatted.startswith('+'):
            # Try to add country code if customer has country
            if self.customer_id and self.customer_id.country_id:
                country_code = self.customer_id.country_id.phone_code
                if country_code and not formatted.startswith(str(country_code)):
                    formatted = f'+{country_code}{formatted}'
                else:
                    formatted = f'+{formatted}'
            else:
                formatted = f'+{formatted}'
        
        return formatted
    
    def _send_call_notification(self):
        """Record phone call notification"""
        self.ensure_one()
        
        # For phone calls, we just log the activity
        # The actual call would be made manually by staff
        
        if self.customer_id:
            self.customer_id.message_post(
                body=_('Phone call notification for table ready: %s') % self.message,
                subject=_('Waiting List - Table Ready'),
            )
        
        _logger.info(
            'Phone call notification logged for %s: %s',
            self.phone_number, self.message
        )
        
        return True
    
    def action_cancel(self):
        """Cancel pending notification"""
        self.filtered(lambda n: n.state in ('pending', 'failed')).write({
            'state': 'cancelled'
        })
        return True
    
    def action_retry(self):
        """Retry failed notification"""
        self.filtered(lambda n: n.state == 'failed').write({
            'state': 'pending',
            'retry_count': 0,
            'error_message': False,
        })
        return True
    
    @api.model
    def _cron_process_pending_notifications(self):
        """Scheduled action to process pending notifications"""
        # Find notifications that should be sent now
        pending_notifications = self.search([
            ('state', '=', 'pending'),
            ('scheduled_time', '<=', fields.Datetime.now()),
        ], limit=100)  # Process in batches of 100
        
        _logger.info('=== Cron: Processing pending notifications ===')
        _logger.info('Found %d pending notifications to process', len(pending_notifications))
        
        if pending_notifications:
            for notif in pending_notifications:
                _logger.info('Processing notification #%d: type=%s, phone=%s', 
                           notif.id, notif.notification_type, notif.phone_number)
            pending_notifications.action_send()
        
        return True
    
    @api.model
    def _cron_cleanup_old_notifications(self):
        """Clean up old sent/cancelled notifications"""
        # Delete notifications older than 30 days
        cutoff_date = fields.Datetime.now() - timedelta(days=30)
        
        old_notifications = self.search([
            ('state', 'in', ('sent', 'cancelled')),
            ('create_date', '<', cutoff_date),
        ])
        
        if old_notifications:
            _logger.info('Cleaning up %d old notifications', len(old_notifications))
            old_notifications.unlink()
        
        return True
