# Professional Waiting List System Implementation Guide

## Overview
This guide organizes requirements and implementation rules for a restaurant waiting list and table management system for Odoo 18 Community/Enterprise. Use this to structure development in `waiting_list_base` (core features) and `waiting_list_enterprise` (advanced features).

---

## waiting_list_base (Core Features)

### 1. Models
- `waiting.list`: Customer name, mobile, guests, status (Waiting, Ready, Seated, Canceled, No Show), timestamps, hostess assignment, branch/table reference.
- `res.partner`: Extend with visit count, spend, last visit, VIP/Regular/Inactive flag.
- `restaurant.table`: Table config, seats, branch, Foodics ID.
- Status logs: Track status changes with timestamp/user.

### 2. Views
- Waiting list form/tree views with status, hostess, branch, table.
- Table management views (add/edit tables, assign to branches).
- Customer analysis: visits, spend, segmentation.

### 3. Security
- Role-based access: Admin (full), Branch Manager (branch only), Hostess (waiting list only).
- Branch-level record rules.

### 4. Integration
- Notification stubs: SMS/WhatsApp triggers on status change.
- **Note**: Foodics integration is now a separate module (`waiting_list_foodics`)

### 5. Reporting & Analytics
- Dashboards: KPIs (wait time, cancellations, table turnover).
- Exportable reports (Excel/PDF).

### 6. Multi-language
- Arabic/English support for UI and templates.

---

## waiting_list_enterprise (Advanced/Enterprise Features)

### 1. Advanced Features
- Advanced table management with floor layouts (pos_restaurant integration).
- **Note**: Foodics integration moved to separate module (`waiting_list_foodics`)

### 2. Notification System
- SMS/WhatsApp integration (Twilio/WhatsApp Business API).
- Editable message templates per branch/language.
- Message logs linked to customer/waiting list.

### 3. Advanced Reporting
- Hostess performance, table utilization, customer insights dashboards.
- KPI widgets: daily customers, wait times, top spenders.

### 4. Inventory Sync
- Odoo inventory as source of truth.
- Foodics sales trigger Odoo stock consumption.
- Variance and low-stock alerts per branch.

### 5. Customer Analysis Page
- CRM + POS data: visit frequency, spend, CLV, engagement rating, loyalty tier.
- Dynamic charts, KPIs, filters (branch, time, VIP).

---

## AI Implementation Rules
- Use Odoo ORM and security best practices.
- Always support multi-branch and multi-language.
- Use Odoo's translation and access control mechanisms.
- Integrate with external APIs using Odoo models and scheduled jobs.
- Log all status changes and communications.
- Keep base features in `waiting_list_base`; put integrations, analytics, and advanced logic in `waiting_list_enterprise`.
- Ensure compatibility with Odoo 18 Community by default.

---

## waiting_list_foodics (Optional Foodics Integration)

### 1. Purpose
- Separate module for Foodics POS integration
- Can be installed independently of `waiting_list_enterprise`
- Both base and enterprise modules work without Foodics

### 2. Features
- Auto-create Foodics orders when customers are seated
- Two-way sync between Odoo and Foodics
- Branch and table mapping configuration
- Real-time order status updates via webhooks
- Customer data synchronization
- Error handling and retry mechanism

### 3. Architecture
- Uses async HTTP client (aiohttp) for API calls
- Webhook controller for real-time updates
- Scheduled actions for retry mechanism
- Comprehensive error logging

### 4. Configuration
- API credentials in Settings
- Branch mappings (Odoo branch ↔ Foodics branch)
- Table mappings (Odoo table ↔ Foodics table)
- Webhook setup in Foodics console

### 5. Dependencies
- `waiting_list_base` (required)
- `div_foodics_with_webhook` (required)
- `aiohttp` Python library (required)

---

_Review and update this guide as requirements evolve. Use it as a checklist for professional, maintainable development._
