# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class WaitingListNotification(models.Model):
    _inherit = 'waiting.list.notification'

    # WhatsApp Template
    wa_template_id = fields.Many2one(
        'whatsapp.template',
        string='WhatsApp Template',
        help='WhatsApp template to use for this notification'
    )
    
    template_type = fields.Selection([
        ('queue_added', 'Queue Added'),
        ('ready', 'Table Ready'),
        ('cancel', 'Cancellation'),
        ('no_show', 'No Show'),
        ('survey', 'Survey'),
        ('custom', 'Custom'),
    ], string='Template Type', help='Type of notification to determine WhatsApp template')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically use WhatsApp if enabled"""
        ICP = self.env['ir.config_parameter'].sudo()
        whatsapp_enabled = ICP.get_param('whatsapp_waitinglist.enabled')
        
        if whatsapp_enabled:
            for vals in vals_list:
                # Convert SMS notifications to WhatsApp if enabled
                if vals.get('notification_type') in ['sms', False]:
                    vals['notification_type'] = 'whatsapp'
                elif vals.get('notification_type') == 'sms_whatsapp':
                    # Keep sms_whatsapp as it is 
                    pass
                
                # Auto-select WhatsApp template if not already set
                if not vals.get('wa_template_id') and vals.get('notification_type') in ['whatsapp', 'sms_whatsapp']:
                    template_type = vals.get('template_type', 'custom')
                    _logger.info('Auto-selecting WhatsApp template for template_type: %s', template_type)
                    template_id = self._get_template_by_type(template_type)
                    if template_id:
                        vals['wa_template_id'] = template_id
                        _logger.info('Selected WhatsApp template ID: %s for template_type: %s', template_id, template_type)
                    else:
                        _logger.warning('No WhatsApp template found for template_type: %s', template_type)
        
        return super().create(vals_list)
    
    @api.model
    def _get_template_by_type(self, template_type):
        """Get WhatsApp template ID based on explicit template type"""
        ICP = self.env['ir.config_parameter'].sudo()
        
        template_map = {
            'queue_added': 'whatsapp_waitinglist.queue_template_id',
            'ready': 'whatsapp_waitinglist.ready_template_id',
            'cancel': 'whatsapp_waitinglist.cancel_template_id',
            'no_show': 'whatsapp_waitinglist.noshow_template_id',
            'survey': 'whatsapp_waitinglist.survey_template_id',
            'custom': 'whatsapp_waitinglist.custom_template_id',
        }
        
        param_name = template_map.get(template_type, 'whatsapp_waitinglist.custom_template_id')
        template_id = ICP.get_param(param_name)
        
        _logger.info('Looking up WhatsApp template for type "%s" using param "%s": found ID %s', 
                    template_type, param_name, template_id or 'None')
        
        if template_id:
            # Verify template exists
            template = self.env['whatsapp.template'].sudo().browse(int(template_id))
            if template.exists():
                _logger.info('Template verified: %s (ID: %s, Status: %s)', 
                           template.name, template.id, template.status)
                return int(template_id)
            else:
                _logger.warning('Template ID %s does not exist in system', template_id)
                return False
        
        return False

    def action_send_whatsapp(self):
        """Send WhatsApp notification for waiting list entry"""
        self.ensure_one()
        
        _logger.info('=== action_send_whatsapp called for notification #%d ===', self.id)
        _logger.info('Notification type: %s, State: %s, Template Type: %s', 
                    self.notification_type, self.state, self.template_type or 'Not Set')
        
        if self.notification_type not in ['whatsapp', 'sms_whatsapp']:
            _logger.warning("Notification %s is not configured for WhatsApp (type: %s)", 
                          self.id, self.notification_type)
            return False
        
        if self.state not in ['pending', 'processing']:
            _logger.warning("Notification %s is not in pending/processing state (current: %s)", 
                          self.id, self.state)
            return False
        
        # Prepare phone number
        phone = self.phone_number
        if not phone:
            _logger.warning("No phone number for notification %s", self.id)
            self.write({'state': 'failed', 'error_message': 'No phone number provided'})
            raise UserError(_('No phone number provided'))
        
        try:
            # Update state to processing
            self.write({'state': 'processing'})
            
            # Get WhatsApp account
            wa_account = self.env['whatsapp.account'].search([], limit=1)
            if not wa_account:
                raise UserError(_('No WhatsApp Business Account configured. Please configure one in Settings > Technical > WhatsApp.'))
            
            # Format phone number for WhatsApp
            formatted_number = self._format_phone_for_whatsapp(phone)
            
            # Get WhatsApp template from notification record
            if not self.wa_template_id:
                # Try to auto-select based on template_type
                if self.template_type:
                    _logger.info('No template assigned, attempting auto-selection for template_type: %s', self.template_type)
                    template_id = self._get_template_by_type(self.template_type)
                    if template_id:
                        self.write({'wa_template_id': template_id})
                        _logger.info('Auto-assigned template ID: %s', template_id)
                    else:
                        raise UserError(_('No WhatsApp template configured for template type "%s". Please configure it in Settings > Technical > Parameters.') % self.template_type)
                else:
                    raise UserError(_('No WhatsApp template configured for this notification and no template_type specified.'))
            
            _logger.info('Using WhatsApp template: %s (ID: %s) for template_type: %s', 
                        self.wa_template_id.name, self.wa_template_id.id, self.template_type or 'Not Set')
            
            # Create composer and send template message
            composer = self.env['whatsapp.composer'].create({
                'res_model': 'waiting.list',
                'res_ids': str([self.waiting_list_id.id]),
                'wa_template_id': self.wa_template_id.id,
                'phone': formatted_number,
            })
            
            # Send the message
            composer._send_whatsapp_template()
            
            _logger.info('WhatsApp template sent to %s', formatted_number)
            
            self.write({
                'state': 'sent',
                'sent_time': fields.Datetime.now(),
                'error_message': False,
            })
            _logger.info("WhatsApp sent successfully for notification %s to %s", self.id, formatted_number)
            return True
            
        except Exception as e:
            error_msg = str(e)
            _logger.error("Failed to send WhatsApp for notification %s: %s", self.id, error_msg)
            self.write({
                'state': 'failed',
                'error_message': error_msg,
            })
            raise UserError(_('Failed to send WhatsApp message: %s') % error_msg)
    
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

    @api.model
    def _cron_send_whatsapp_notifications(self):
        """Cron job to send pending WhatsApp notifications"""
        pending_notifications = self.search([
            ('state', '=', 'pending'),
            ('notification_type', 'in', ['whatsapp', 'sms_whatsapp']),
        ], limit=50)  # Process in batches
        
        _logger.info("Processing %s pending WhatsApp notifications", len(pending_notifications))
        
        success_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                result = notification.action_send_whatsapp()
                if result:
                    success_count += 1
                    _logger.info("Notification %s sent successfully", notification.id)
                else:
                    failed_count += 1
                    _logger.warning("Notification %s failed to send", notification.id)
            except Exception as e:
                failed_count += 1
                _logger.error("Error processing notification %s: %s", notification.id, str(e))
                # Mark as failed if not already updated
                if notification.state == 'pending':
                    notification.write({
                        'state': 'failed',
                        'error_message': str(e),
                    })
                continue
        
        _logger.info("WhatsApp notification cron completed: %s sent, %s failed", success_count, failed_count)
        return True
