# WhatsApp Integration for Waiting List

This module integrates the Restaurant Waiting List system with WhatsApp, allowing automatic and manual sending of notifications via WhatsApp.

## Features

### 1. **Automatic WhatsApp Notifications**
   - Table Ready notifications
   - Cancellation notices
   - No-show alerts
   - Survey/feedback requests
   - Custom notifications

### 2. **WhatsApp Templates**
   - Pre-configured templates for each notification type
   - Bilingual support (English/Arabic)
   - Customizable message content
   - Variables for dynamic content (customer name, party size, table, etc.)

### 3. **Configuration Settings**
   - Enable/disable WhatsApp per notification type
   - Configure templates in Settings > Waiting List > WhatsApp
   - Template validation for phone fields

### 4. **Integration with Notification Queue**
   - Seamless integration with `waiting.list.notification` model
   - Automatic WhatsApp sending via cron job
   - Manual send button for on-demand notifications
   - Status tracking (pending, sent, failed)

## Installation

1. **Prerequisites:**
   - `whatsapp` module must be installed (Odoo Enterprise)
   - `waiting_list_enterprise` module must be installed
   - WhatsApp Business API configured in Odoo

2. **Install Module:**
   ```bash
   # Via Odoo UI
   Apps > Update Apps List > Search "WhatsApp - Waiting List" > Install
   
   # Via command line
   docker exec odoo18_enterprise odoo-bin -d odoo18_db -u whatsapp_waitinglist --stop-after-init
   ```

## Configuration

### 1. Enable WhatsApp Notifications

Navigate to: **Settings > Waiting List > Configuration > Settings**

1. Enable "Enable WhatsApp for Waiting List"
2. Configure templates for each notification type:
   - **Table Ready Template**: Sent when table is ready
   - **Cancellation Template**: Sent when reservation is cancelled
   - **No-Show Template**: Sent when customer doesn't show up
   - **Survey Template**: Sent for feedback requests
   - **Custom Template**: For other notifications

### 2. Configure WhatsApp Templates

Templates are pre-created during installation. You can customize them:

1. Go to **WhatsApp > Configuration > Templates**
2. Find templates starting with "Waiting List:"
3. Edit template content and variables
4. **Important**: Ensure `phone_field` is set to `customer_mobile`

### 3. Test WhatsApp Integration

1. Create a waiting list entry with a customer that has a mobile number
2. Mark the entry as "Ready"
3. Check the notification queue: Smart button "Notifications" on the waiting list entry
4. Verify WhatsApp was sent successfully

## Usage

### Automatic Notifications

When you perform actions on waiting list entries, notifications are automatically queued:

1. **Mark Ready**: Queues "Table Ready" notification
2. **Cancel**: Queues "Cancellation" notification
3. **Mark No-Show**: Queues "No-Show" notification
4. **Complete (Done)**: Queues "Survey" notification

The cron job runs every 5 minutes to send pending WhatsApp notifications.

### Manual WhatsApp Sending

#### From Waiting List Entry:
1. Open a waiting list entry
2. Click "Send WhatsApp" button (appears if customer has phone)
3. Select template and customize message
4. Click "Send"

#### From Notification Record:
1. Go to Notifications smart button
2. Open a pending notification
3. Click "Send WhatsApp" button

## Technical Details

### Models

- **res.config.settings**: Configuration for WhatsApp templates
- **waiting.list.notification**: Extended with WhatsApp sending methods
- **waiting.list**: Added WhatsApp action and safe fields
- **whatsapp.composer**: Extended to support waiting.list model
- **whatsapp.template**: Added field mapping for waiting.list

### Key Methods

- `action_send_whatsapp()`: Send WhatsApp for a notification
- `_get_whatsapp_template()`: Determine appropriate template based on message content
- `_cron_send_whatsapp_notifications()`: Cron job to process pending notifications
- `_get_whatsapp_safe_fields()`: Define safe fields for template variables

### Cron Jobs

- **Name**: Send Waiting List WhatsApp Notifications
- **Frequency**: Every 5 minutes
- **Model**: waiting.list.notification
- **Method**: _cron_send_whatsapp_notifications

## Troubleshooting

### WhatsApp Not Sending

1. **Check WhatsApp is enabled:**
   - Settings > Waiting List > WhatsApp > Enable WhatsApp for Waiting List

2. **Verify template configuration:**
   - WhatsApp > Configuration > Templates
   - Ensure templates have `phone_field` set
   - Verify template is approved in WhatsApp Business API

3. **Check notification queue:**
   - Open waiting list entry > Notifications smart button
   - Check notification state (pending/sent/failed)
   - Check error_message field if failed

4. **Verify phone number:**
   - Customer must have mobile number
   - Phone number must be in international format (+1234567890)

### Template Variables Not Working

1. Ensure field names match model fields
2. Use dot notation for related fields: `customer_id.name`
3. Check `_get_whatsapp_safe_fields()` for allowed fields

## License

OEEL-1 (Odoo Enterprise Edition License)

## Author

Odoo PS - 3Fils Restaurant Management

## Version

18.0.1.0.0
