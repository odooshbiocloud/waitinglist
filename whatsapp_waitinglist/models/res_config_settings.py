# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # WhatsApp Templates for Waiting List
    waitinglist_whatsapp_enabled = fields.Boolean(
        string='Enable WhatsApp for Waiting List',
        config_parameter='whatsapp_waitinglist.enabled',
        help='Enable WhatsApp notifications for waiting list updates'
    )
    
    waitinglist_queue_template_id = fields.Many2one(
        'whatsapp.template',
        string='Queue Added Template',
        config_parameter='whatsapp_waitinglist.queue_template_id',
        domain=[('model_id.model', '=', 'waiting.list')],
        help='WhatsApp template for when customer is added to waiting list'
    )
    
    waitinglist_ready_template_id = fields.Many2one(
        'whatsapp.template',
        string='Table Ready Template',
        config_parameter='whatsapp_waitinglist.ready_template_id',
        domain=[('model_id.model', '=', 'waiting.list')],
        help='WhatsApp template for table ready notifications'
    )
    
    waitinglist_cancel_template_id = fields.Many2one(
        'whatsapp.template',
        string='Cancellation Template',
        config_parameter='whatsapp_waitinglist.cancel_template_id',
        domain=[('model_id.model', '=', 'waiting.list')],
        help='WhatsApp template for cancellation notifications'
    )
    
    waitinglist_noshow_template_id = fields.Many2one(
        'whatsapp.template',
        string='No-Show Template',
        config_parameter='whatsapp_waitinglist.noshow_template_id',
        domain=[('model_id.model', '=', 'waiting.list')],
        help='WhatsApp template for no-show notifications'
    )
    
    waitinglist_survey_template_id = fields.Many2one(
        'whatsapp.template',
        string='Survey/Feedback Template',
        config_parameter='whatsapp_waitinglist.survey_template_id',
        domain=[('model_id.model', '=', 'waiting.list')],
        help='WhatsApp template for survey/feedback requests'
    )
    
    waitinglist_custom_template_id = fields.Many2one(
        'whatsapp.template',
        string='Custom Notification Template',
        config_parameter='whatsapp_waitinglist.custom_template_id',
        domain=[('model_id.model', '=', 'waiting.list')],
        help='WhatsApp template for custom notifications'
    )

    @api.constrains('waitinglist_queue_template_id', 'waitinglist_ready_template_id', 
                    'waitinglist_cancel_template_id', 'waitinglist_noshow_template_id', 
                    'waitinglist_survey_template_id', 'waitinglist_custom_template_id')
    def _check_whatsapp_templates(self):
        """Validate that WhatsApp templates have proper phone field configuration"""
        for record in self:
            templates = [
                record.waitinglist_queue_template_id,
                record.waitinglist_ready_template_id,
                record.waitinglist_cancel_template_id,
                record.waitinglist_noshow_template_id,
                record.waitinglist_survey_template_id,
                record.waitinglist_custom_template_id,
            ]
            for template in templates:
                if template and not template.phone_field:
                    raise ValidationError(
                        _("WhatsApp template '%s' must have a phone field configured.") % template.name
                    )
