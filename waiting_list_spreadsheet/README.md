# Waiting List Spreadsheet Analytics

**Version:** 18.0.1.0.0  
**Author:** Odoo PS  
**License:** OEEL-1 (Odoo Enterprise Edition License)

---

## 📊 Overview

Advanced spreadsheet-based analytics dashboard for the **Waiting List Enterprise** system. Provides comprehensive historical trend analysis, performance metrics, and actionable insights for restaurant managers.

### Key Features

✅ **Historical Analytics** - Track performance over 7 days, 30 days, or custom periods  
✅ **Interactive Charts** - 6+ pre-built charts with drill-down capabilities  
✅ **Multi-Company Support** - Unified view with branch/company filters  
✅ **VIP Tracking** - Filter by VIP customer status  
✅ **Manager-Only Access** - Secured for management-level users  
✅ **Auto-Refresh** - Hourly automatic data updates  
✅ **Export to Excel** - Download charts and data for offline analysis  

---

## 📈 Included Analytics

### Charts & Visualizations

1. **Status Distribution** (Pie Chart)
   - Breakdown: Waiting, Ready, Called, Seated, Done, Cancelled, No-Show
   - Shows current state of all entries

2. **Hourly Entry Trends** (Bar Chart)
   - Peak hours identification
   - Entry patterns throughout the day
   - Helps optimize staffing levels

3. **Wait Time Analysis** (Line Chart)
   - Average wait time trends over selected period
   - Daily/weekly comparisons
   - Performance benchmarking

4. **Table Utilization** (Bar Chart)
   - Most/least used tables
   - Table turnover rates
   - Space optimization insights

5. **Party Size Distribution** (Pie Chart)
   - Group size patterns (1-2, 3-4, 5-6, 7+ guests)
   - Helps with table configuration

6. **Customer Satisfaction** (Bar Chart)
   - Satisfaction score distribution (1-5 stars)
   - Trends over time
   - Quality monitoring

### Key Performance Indicators (KPIs)

- **Total Entries** - Count of all waiting list entries in period
- **Average Wait Time** - Mean wait time for seated customers
- **No-Show Rate (%)** - Percentage of no-shows vs. total entries
- **Cancellation Rate (%)** - Percentage of cancellations
- **Satisfaction Score** - Average customer satisfaction (1-5)
- **VIP Count** - Number of VIP customers served
- **Allergen Alerts** - Customers with allergen restrictions

---

## 🔧 Installation

### Prerequisites

- **Odoo 18 Enterprise Edition** or **Odoo.sh**
- **waiting_list_base** module installed
- **waiting_list_enterprise** module installed
- **spreadsheet_dashboard** module (included in Enterprise)

### Installation Steps

#### Via Odoo UI

1. Navigate to **Apps** menu
2. Remove **Apps** filter
3. Search for `waiting_list_spreadsheet`
4. Click **Install**

#### Via PowerShell Script (Local Development)

```powershell
# Save this as install_waiting_list_spreadsheet.ps1

$ErrorActionPreference = "Stop"

# Database connection details
$DB_NAME = "odoo18_db"
$DB_USER = "odoo"
$DB_PASSWORD = "odoo"
$DB_HOST = "localhost"
$DB_PORT = "5432"

Write-Host "Installing Waiting List Spreadsheet module..." -ForegroundColor Green

# Install via Python script
$pythonScript = @"
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        dbname='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD',
        host='$DB_HOST',
        port='$DB_PORT'
    )
    cursor = conn.cursor()
    
    # Check if module exists
    cursor.execute(\"\"\"
        SELECT id, state FROM ir_module_module 
        WHERE name = 'waiting_list_spreadsheet'
    \"\"\")
    
    result = cursor.fetchone()
    
    if result:
        module_id, state = result
        
        if state == 'installed':
            print('Module already installed. Upgrading...')
            cursor.execute(\"\"\"
                UPDATE ir_module_module 
                SET state = 'to upgrade' 
                WHERE name = 'waiting_list_spreadsheet'
            \"\"\")
        else:
            print('Installing module...')
            cursor.execute(\"\"\"
                UPDATE ir_module_module 
                SET state = 'to install' 
                WHERE name = 'waiting_list_spreadsheet'
            \"\"\")
        
        conn.commit()
        print('✅ Module marked for installation. Restart Odoo to complete.')
    else:
        print('❌ Module not found. Update app list first.')
        sys.exit(1)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {str(e)}')
    sys.exit(1)
"@

$pythonScript | python

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Installation initiated successfully!" -ForegroundColor Green
    Write-Host "Next step: Restart Odoo container" -ForegroundColor Yellow
    Write-Host "Run: docker-compose restart odoo18_enterprise" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Installation failed!" -ForegroundColor Red
}
```

#### Via Docker (Recommended)

```powershell
# Update module list
docker-compose restart odoo18_enterprise

# Or install directly
docker exec -it odoo-docker-odoo18_enterprise-1 odoo -d odoo18_db -i waiting_list_spreadsheet --stop-after-init
```

---

## 📖 Usage Guide

### Accessing the Dashboard

1. Navigate to **Waiting List → Performance Dashboard**
2. Click **Open Dashboard** to view interactive spreadsheet
3. Use built-in filters to drill down:
   - Date Range (Today, Last 7 Days, Last 30 Days, Custom)
   - Company/Branch
   - VIP Status
   - Floor
   - Table
   - Entry Status

### Refreshing Data

**Auto-Refresh:** Dashboard updates every hour automatically

**Manual Refresh:**
1. Go to **Waiting List → Analytics Dashboard**
2. Open any dashboard record
3. Click **Refresh Data** button

### Exporting Reports

1. Open the dashboard
2. Click **Export** button (top-right)
3. Choose format: **Excel** or **PDF**
4. Download file

### Creating Custom Dashboards

1. Go to **Waiting List → Analytics Dashboard**
2. Click **Create**
3. Set date range and filters
4. Click **Open Dashboard**
5. Customize charts using spreadsheet tools

---

## 🔒 Security & Access Control

### Access Levels

- **Manager Group Only:** `waiting_list_enterprise.group_waiting_list_manager`
- Hostess role **cannot** access analytics (operational focus)
- Admins have full access by default

### Multi-Company Rules

- Dashboards respect company context
- Users see data from their assigned companies only
- Global managers can view all companies

---

## 🛠️ Configuration

### System Parameters

Access via **Settings → Technical → System Parameters**:

- `waiting_list_spreadsheet.auto_refresh_interval` - Refresh interval (default: 1 hour)
- `waiting_list_spreadsheet.default_period` - Default date range (default: 30 days)
- `waiting_list_spreadsheet.enable_export` - Allow Excel/PDF export (default: True)

### Scheduled Actions

**Cron Job:** `Waiting List: Refresh Spreadsheet Analytics`
- **Interval:** Every 1 hour
- **Action:** Recalculate KPIs and update dashboards
- Can be disabled if manual refresh preferred

---

## 📊 Chart Details

### Status Distribution (Pie Chart)

**Purpose:** Visualize current state of all entries  
**Data Source:** `waiting.list` model grouped by `status`  
**Measures:** Count of entries  
**Filters:** Date range, company, VIP  

### Hourly Entry Trends (Bar Chart)

**Purpose:** Identify peak hours and staffing needs  
**Data Source:** `waiting.list` grouped by hour of `create_date`  
**Measures:** Count of entries per hour  
**Insight:** Shows when most customers join waitlist  

### Wait Time Analysis (Line Chart)

**Purpose:** Track wait time performance over time  
**Data Source:** `waiting.list` where `status` in (seated, done)  
**Measures:** Average `actual_wait_time`  
**Grouping:** By day  
**Insight:** Identifies trends and anomalies  

### Table Utilization (Bar Chart)

**Purpose:** Optimize table allocation  
**Data Source:** `waiting.list` with `table_id`  
**Measures:** Count per table  
**Grouping:** By table  
**Insight:** Shows most/least popular tables  

### Party Size Distribution (Pie Chart)

**Purpose:** Understand group size patterns  
**Data Source:** `waiting.list` grouped by `party_size`  
**Measures:** Count per size category  
**Categories:** 1-2, 3-4, 5-6, 7+  
**Insight:** Helps optimize table configuration  

### Customer Satisfaction (Bar Chart)

**Purpose:** Track service quality  
**Data Source:** `waiting.list` where `customer_satisfaction` is set  
**Measures:** Count per satisfaction level (1-5)  
**Insight:** Quality monitoring and trend analysis  

---

## 🔍 Troubleshooting

### Dashboard Not Showing Data

1. Check date range filters (ensure data exists in period)
2. Verify company context (switch companies if multi-company)
3. Click **Refresh Data** to reload
4. Check if waiting list entries exist for selected period

### Charts Not Displaying

1. Clear browser cache
2. Check if `spreadsheet_dashboard` module is installed
3. Verify Enterprise license is active
4. Check browser console for JavaScript errors

### Access Denied Errors

1. Verify user is in **Waiting List Manager** group
2. Check multi-company access rights
3. Contact administrator for permission updates

### Auto-Refresh Not Working

1. Go to **Settings → Technical → Scheduled Actions**
2. Find "Waiting List: Refresh Spreadsheet Analytics"
3. Ensure **Active** is checked
4. Check **Next Execution Date**
5. Click **Run Manually** to test

---

## 🧪 Testing

### Verify Installation

```python
# In Odoo shell or script
dashboard = env['waiting.list.spreadsheet'].search([], limit=1)
print(f"Dashboard: {dashboard.name}")
print(f"Total Entries: {dashboard.total_entries}")
print(f"Avg Wait Time: {dashboard.avg_wait_time} min")
```

### Generate Test Data

```python
# Create sample waiting list entries for testing
WaitingList = env['waiting.list']
Partner = env['res.partner']

for i in range(50):
    partner = Partner.create({'name': f'Test Customer {i}'})
    WaitingList.create({
        'customer_id': partner.id,
        'party_size': (i % 8) + 1,
        'status': ['waiting', 'seated', 'done', 'cancelled'][i % 4],
        'waiting_type': 'waitlist',
    })

print("✅ Created 50 test entries")
```

---

## 📚 API Reference

### Methods

#### `get_performance_summary(date_from=None, date_to=None)`

Returns performance summary dict:
```python
{
    'total_entries': int,
    'status_breakdown': dict,
    'avg_wait_time': float,
    'avg_party_size': float,
    'vip_count': int,
    'allergen_count': int,
}
```

#### `action_open_dashboard()`

Opens spreadsheet dashboard in client action

#### `action_refresh_data()`

Manually refreshes computed analytics fields

---

## 🔄 Upgrade Notes

### From v1.0.0 to v1.1.0 (Future)

- Backup database before upgrading
- Run upgrade via Apps menu or CLI
- Check scheduled actions after upgrade

---

## 🆘 Support

- **Documentation:** See module README
- **Issues:** Contact Odoo PS support
- **Community:** Odoo forums

---

## 📜 License

**OEEL-1** - Odoo Enterprise Edition License v1.0

This module requires a valid Odoo Enterprise license.

---

## ✨ Credits

**Developed by:** Odoo Professional Services  
**For:** PSAE 3Fils Restaurant Group  
**Odoo Version:** 18.0 Enterprise  

---

**Enjoy your analytics! 📊🚀**
