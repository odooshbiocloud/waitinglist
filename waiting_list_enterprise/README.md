# Waiting List Enterprise - POS Restaurant Integration

## Overview

This module extends `waiting_list_base` with full POS Restaurant integration for Odoo 18 Enterprise. It provides advanced table management, floor-based organization, and VIP customer prioritization.

## Features

### 🏢 Restaurant Floor Integration
- **Floor Selection**: Assign waiting customers to specific restaurant floors
- **Floor Overview Dashboard**: See waiting list statistics per floor
- **Real-time Availability**: Track occupied and available tables per floor

### 🪑 Smart Table Assignment
- **Automatic Suggestions**: System suggests tables based on party size
- **Capacity Validation**: Ensures table can accommodate the party
- **Occupancy Tracking**: See which tables are occupied in real-time
- **One-Click Assignment**: Quickly assign next waiting customer to available table

### ⭐ VIP & Priority Management
- **Automatic VIP Detection**: Based on customer categories from base module
- **Priority Queueing**: Higher priority customers served first
- **Smart Ordering**: Combines priority and arrival time (FIFO within priority)

### 📊 Enhanced Views & Dashboards
- **Floor-based Kanban**: Visual management of waiting list by floor
- **Table Assignment View**: Dedicated view for assigning tables
- **Enhanced Customer Forms**: Shows table, floor, and POS config information
- **Restaurant Table Views**: See waiting list directly from table records

### 🔔 Notification System (Ready for Integration)
- **Notification Tracking**: Track when customers were notified
- **Multiple Methods**: Support for SMS, WhatsApp, Phone Call
- **Integration Points**: Ready for SMS/WhatsApp service integration

### ⏱️ Wait Time Estimation
- **Smart Estimates**: Calculates wait time based on queue and table availability
- **Party Size Adjustment**: Larger parties get longer estimates
- **Priority Awareness**: Considers priority when estimating wait

## Installation

### Prerequisites
1. Odoo 18 Enterprise Edition
2. `waiting_list_base` module installed
3. `pos_restaurant` module installed and configured

### Steps

#### Method 1: Using Installation Script
```powershell
# From workspace root
python install_waiting_list_enterprise.py

# Then restart Odoo
docker-compose restart odoo18_enterprise
```

#### Method 2: Manual Installation
1. Update Apps List in Odoo
2. Search for "Restaurant Waiting List - Enterprise"
3. Click Install

#### Method 3: Docker Container
```powershell
# Restart container to detect new module
docker-compose restart odoo18_enterprise

# Access Odoo at http://localhost:8019
# Go to Apps → Update Apps List → Install module
```

## Configuration

### 1. POS Configuration
1. Go to **Point of Sale → Configuration → Point of Sale**
2. Ensure Restaurant features are enabled
3. Configure floors and tables

### 2. Restaurant Floors
1. Go to **Waiting List → Floor Overview**
2. Floors from POS Restaurant will be automatically available
3. Tables are linked to their respective floors

### 3. Customer Categories
The module uses VIP category from base module:
- VIP customers automatically get priority = 10
- Regular customers have priority = 0
- You can manually adjust priority as needed

## Usage

### Adding Customers to Waiting List

1. **Navigate**: Waiting List → Waiting List → Create
2. **Fill Details**:
   - Customer information
   - Party size
   - POS Configuration (optional)
   - Floor selection
   - Preferred seating (optional)

3. **System Actions**:
   - VIP customers automatically prioritized
   - Estimated wait time calculated
   - Queue position determined

### Assigning Tables

#### Option 1: From Waiting List Entry
1. Open waiting list entry
2. Select Floor
3. Click "Suggest Tables" to see available tables
4. Or manually select a table
5. Click "Assign Table"

#### Option 2: From Table Record
1. Go to Floor Overview
2. Click on a table
3. Click "Assign to Next Customer"
4. System automatically assigns highest priority customer

#### Option 3: Bulk Assignment View
1. Go to **Waiting List → Table Assignment**
2. See all customers waiting for tables
3. Assign tables in bulk

### Customer Flow

```
1. Customer Arrives → Create Waiting List Entry (Status: Waiting)
                    ↓
2. Table Available → Assign Table (Status: Ready)
                    ↓
3. Notify Customer → Send Notification (Status: Called)
                    ↓
4. Customer Ready → Seat Customer (Status: Seated)
```

### Notifying Customers

1. Open waiting list entry with assigned table
2. Ensure customer has phone/mobile number
3. Click "Notify Customer"
4. Customer status changes to "Called"
5. Integration point ready for SMS/WhatsApp services

## Views & Dashboards

### Main Views

1. **By Floor** (`menu_waiting_list_by_floor`)
   - Kanban view grouped by floor
   - See all waiting customers per floor
   - Visual priority indicators

2. **Table Assignment** (`menu_waiting_list_table_assignment`)
   - List of customers needing table assignment
   - Quick access to assign tables

3. **Floor Overview** (`menu_restaurant_floor_overview`)
   - Kanban cards showing floor statistics
   - Waiting count, occupied/available tables
   - One-click access to floor waiting list

### Enhanced Fields

#### Waiting List Entry
- `pos_config_id`: POS configuration
- `floor_id`: Restaurant floor
- `table_id`: Assigned table
- `priority`: Queue priority (0-∞)
- `is_vip`: Automatic VIP detection
- `preferred_seating`: Seating preference
- `estimated_wait_time`: Calculated wait time
- `table_assigned_time`: When table was assigned
- `notification_sent`: Notification status
- `notification_type`: SMS/WhatsApp/Call
- `table_capacity`: Table seat capacity

#### Restaurant Table
- `waiting_list_ids`: All waiting list entries for table
- `current_waiting_list_id`: Currently seated customer
- `is_occupied`: Occupancy status
- `waiting_count`: Customers waiting for this table

#### Restaurant Floor
- `waiting_list_count`: Total waiting customers
- `occupied_tables_count`: Occupied tables
- `available_tables_count`: Available tables

## Security

Uses security groups from `waiting_list_base`:
- **Hostess**: Can view and assign tables, seat customers
- **Manager**: Full access including table management
- **Admin**: Complete system administration

Access to POS Restaurant models (tables, floors) is read-only for Hostess role.

## API Methods

### Waiting List Model

```python
# Assign table to customer
record.action_assign_table()

# Suggest available tables
record.action_suggest_tables()

# Send notification
record.action_send_notification()

# Seat customer at table
record.action_seat_at_table()
```

### Restaurant Table Model

```python
# View waiting list for table
table.action_view_waiting_list()

# Assign table to next customer
table.action_assign_to_waiting_customer()
```

### Restaurant Floor Model

```python
# View floor waiting list
floor.action_view_waiting_list()
```

## Integration Points

### SMS/WhatsApp Integration
The module has notification tracking ready. To integrate actual SMS/WhatsApp:

1. Extend `action_send_notification()` in `waiting_list.py`
2. Add your SMS provider (Twilio, etc.)
3. Use `notification_type` field to determine channel
4. Message template example:
   ```
   Hi {customer_name},
   Your table ({table_number}) is ready at {floor_name}.
   Please proceed to the restaurant.
   ```

### Foodics Integration
See `IMPLEMENTATION_GUIDE.md` for Foodics POS integration plans.

## Troubleshooting

### Module Not Appearing
```powershell
# Update module list
docker-compose restart odoo18_enterprise
# Then in Odoo: Apps → Update Apps List
```

### Tables Not Showing
- Ensure `pos_restaurant` is installed
- Configure floors in Point of Sale settings
- Add tables to floors

### VIP Not Auto-Detecting
- Check customer has VIP category tag
- Category must match `waiting_list_base.customer_category_vip`

### Priority Not Working
- Check list is sorted by `priority desc, create_date asc`
- Manually adjust priority if needed
- VIP customers should auto-set to priority=10

## Development

### File Structure
```
waiting_list_enterprise/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── waiting_list.py          # Enterprise extensions
│   └── restaurant_table.py       # Table/Floor integration
├── views/
│   ├── waiting_list_views.xml    # Enhanced views
│   ├── restaurant_views.xml      # Table/Floor views
│   └── menu_actions.xml          # Menu structure
├── security/
│   └── ir.model.access.csv       # Access rights
└── static/
    └── src/
        └── js/
            └── enterprise_dashboard.js
```

### Extending the Module

To add custom features:

1. **Inherit waiting.list model**:
   ```python
   class WaitingListCustom(models.Model):
       _inherit = 'waiting.list'
       
       custom_field = fields.Char('Custom Field')
   ```

2. **Add views**: Inherit existing views
3. **Update manifest**: Add data files

## Roadmap

- [ ] Real-time dashboard updates
- [ ] Floor plan visualization
- [ ] SMS/WhatsApp integration
- [ ] Advanced analytics and reporting
- [ ] Foodics POS synchronization
- [ ] Customer loyalty integration
- [ ] Multi-language message templates

## Support

For issues or questions:
1. Check IMPLEMENTATION_GUIDE.md
2. Review Odoo logs: `docker-compose logs -f odoo18_enterprise`
3. Verify module dependencies installed

## License

OEEL-1 (Odoo Enterprise Edition License)

---

**Version**: 18.0.1.0.0  
**Author**: Odoo PS  
**Depends**: waiting_list_base, pos_restaurant
