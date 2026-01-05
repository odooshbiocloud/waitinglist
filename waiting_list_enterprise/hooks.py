# -*- coding: utf-8 -*-

def post_init_hook(env):
    """Create cron jobs after module installation"""
    
    # Check if cron jobs already exist
    cron_process = env.ref('waiting_list_enterprise.ir_cron_process_pending_notifications', raise_if_not_found=False)
    cron_cleanup = env.ref('waiting_list_enterprise.ir_cron_cleanup_old_notifications', raise_if_not_found=False)
    
    # Get the model
    model_notification = env['ir.model'].search([('model', '=', 'waiting.list.notification')], limit=1)
    
    if not model_notification:
        # Model not found, skip cron creation
        return
    
    # Create cron for processing pending notifications if it doesn't exist
    if not cron_process:
        env['ir.cron'].create({
            'name': 'Waiting List: Process Pending Notifications',
            'model_id': model_notification.id,
            'state': 'code',
            'code': 'model._cron_process_pending_notifications()',
            'interval_number': 5,
            'interval_type': 'minutes',
            'active': True,
            'priority': 5,
        })
    
    # Create cron for cleanup if it doesn't exist
    if not cron_cleanup:
        env['ir.cron'].create({
            'name': 'Waiting List: Cleanup Old Notifications',
            'model_id': model_notification.id,
            'state': 'code',
            'code': 'model._cron_cleanup_old_notifications()',
            'interval_number': 1,
            'interval_type': 'days',
            'active': True,
            'priority': 10,
        })
