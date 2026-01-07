# Restaurant Waiting List - Base Module

## Transform Your Restaurant Queue Management

Streamline your restaurant's waiting list operations with this comprehensive, professional-grade waiting list management system designed specifically for restaurants. Perfect for restaurants of all sizes, from single locations to multi-branch operations.

## 🌟 Key Features

### 📋 Smart Waiting List Management
- **Real-time Queue Tracking**: Monitor all waiting customers in one intuitive dashboard
- **Automatic Queue Numbers**: Sequential numbering system for organized customer flow
- **Status Management**: Track customers through their journey - Waiting, Ready, Seated, Canceled, or No Show
- **Guest Count Tracking**: Record party size for optimal table allocation
- **Time Tracking**: Automatic logging of wait times and timestamps for every status change
- **Notes & Special Requests**: Capture customer preferences and special requirements

### 🏢 Multi-Branch Operations
- **Branch-Specific Views**: Isolated waiting lists per location
- **Branch-Level Security**: Staff access restricted to their assigned branches
- **Multi-Company Support**: Perfect for restaurant groups and franchises
- **Hostess Assignment**: Track which staff member is handling each customer

### 🍽️ Table Management
- **Table Configuration**: Define tables with capacity and branch assignment
- **Smart Table Assignment**: Match customers to appropriate tables based on party size
- **Table Status Tracking**: Know which tables are available, occupied, or reserved

### 🚨 Allergen Management & Safety Tracking
One of the most critical features for modern restaurant operations:

- **Comprehensive Allergen Database**: Pre-configured with common allergens
- **Customer Allergen Profiles**: Store permanent allergen information per customer
- **Auto-Population**: Allergen information automatically appears when customer returns
- **Visual Safety Alerts**: Prominent warnings when seating customers with allergens
- **Bilingual Support**: Allergen information in both English and Arabic
- **Safety First**: Helps prevent cross-contamination and ensures customer safety

### 👥 Customer Intelligence
- **Customer Database Integration**: Link waiting list entries to customer records
- **Visit History**: Track customer return visits and patterns
- **Customer Categories**: Organize customers into segments
- **Smart Search**: Quickly find customers by name or phone number
- **Repeat Customer Recognition**: Identify and acknowledge returning guests

### 📊 Survey Integration
- **Customer Feedback**: Built-in survey integration for gathering feedback
- **Satisfaction Tracking**: Measure and improve customer experience
- **Customizable Surveys**: Use Odoo's survey module for flexible questionnaires

### 📈 Reporting & Analytics
- **Interactive Dashboard**: Real-time KPIs and metrics at a glance
- **Wait Time Analysis**: Average wait times and service efficiency metrics
- **Cancellation Tracking**: Monitor and analyze no-shows and cancellations
- **Customer Insights**: Understand your customer base and patterns
- **Exportable Reports**: Generate reports for management review

### 🔒 Security & Access Control
- **Role-Based Access**: Three-tier security model
  - **Admin**: Full system access and configuration
  - **Branch Manager**: Branch-specific management
  - **Hostess/Host**: Waiting list operations only
- **Record-Level Security**: Automatic data isolation by branch
- **Audit Trail**: Complete history of all status changes with user and timestamp

### 🌐 Internationalization
- **Multi-Language Ready**: Full support for Arabic and English
- **Bilingual Allergen Data**: Safety information in multiple languages
- **Localized UI**: Seamless experience for international operations

### ⚡ User-Friendly Interface
- **Intuitive Dashboard**: Easy-to-use interface for busy restaurant environments
- **Quick Add Wizard**: Streamlined customer addition workflow
- **Mobile-Responsive**: Works on tablets and mobile devices (requires responsive theme)
- **Color-Coded Status**: Visual indicators for quick status identification
- **Search & Filter**: Find customers quickly with powerful search tools

## 📦 What's Included

### Models
- `waiting.list` - Core waiting list entries with full lifecycle tracking
- `waiting.list.allergen` - Allergen master data and tracking
- `res.partner` - Extended customer profiles with allergen information
- Wizard for quick customer addition

### Views
- Comprehensive dashboard view with KPIs and metrics
- Waiting list management (tree, form, kanban views)
- Table management interface
- Allergen management and configuration
- Customer profile views with allergen display
- Settings configuration panel

### Data
- Pre-configured allergen database
- Customer category templates
- Automated sequence generation
- Sample configurations for quick start

### Security
- Complete security groups and access rights
- Record rules for multi-branch isolation
- Role-based menu access

## 🎯 Perfect For

- ✅ Fine Dining Restaurants
- ✅ Casual Dining Establishments
- ✅ Multi-Branch Restaurant Groups
- ✅ Restaurant Chains and Franchises
- ✅ Hotels with Multiple Dining Outlets
- ✅ Food Courts and Food Halls
- ✅ Any business with customer waiting queues

## 💡 Why Choose This Module?

1. **Safety First**: Comprehensive allergen tracking protects your customers and your business
2. **Community Compatible**: Works with Odoo Community Edition - no Enterprise license required
3. **Professional Grade**: Built following Odoo best practices and coding standards
4. **Scalable**: Grows with your business from single location to multi-branch operations
5. **Easy to Use**: Intuitive interface designed for busy restaurant environments
6. **Well Documented**: Comprehensive guides and clear code structure
7. **Actively Maintained**: Regular updates and compatibility with latest Odoo versions

## 🚀 Quick Start

1. **Install the Module**: Install from Apps menu
2. **Configure Settings**: Set up branches and basic configuration in Settings > Waiting List
3. **Add Tables**: Configure your tables and seating capacity
4. **Configure Allergens**: Review and customize allergen list if needed
5. **Start Using**: Open Waiting List menu and start adding customers to queue

## 📋 Technical Details

- **Version**: 19.0.1.0.0
- **Odoo Version**: 19.0
- **License**: LGPL-3
- **Dependencies**: base, mail, survey
- **Module Type**: Base/Core module
- **Category**: Sales

## 🔄 Compatibility

- ✅ Odoo Community Edition 19.0
- ✅ Odoo Enterprise Edition 19.0
- ✅ Multi-company environments
- ✅ Multi-currency (through Odoo core)

## 📚 Additional Modules

For advanced features, consider these companion modules:

- **pos_waiting_list_enterprise**: Advanced table layouts with pos_restaurant integration, VIP priority, enhanced analytics
- **waiting_list_foodics**: Foodics POS integration for seamless order management
- **pos_waiting_list_spreadsheet**: Advanced reporting with Odoo Spreadsheet integration
- **pos_whatsapp_waitinglist**: WhatsApp notification integration

## 🛠️ Configuration

### Initial Setup
1. Navigate to **Settings > Waiting List Configuration**
2. Configure your branches and locations
3. Set up tables with capacity and branch assignment
4. Review allergen database and customize if needed
5. Configure customer categories
6. Set up user access rights and roles

### Survey Integration (Optional)
1. Create customer satisfaction surveys in Survey app
2. Link surveys in waiting list settings
3. Automatically collect feedback when customers are seated

## 📞 Support & Documentation

- Comprehensive in-app help and tooltips
- Implementation guide included
- Sample data for testing and training
- Clean, well-documented code for customization

## 🏆 Benefits

### For Restaurant Managers
- Better control over customer flow
- Reduced wait time complaints
- Improved table utilization
- Data-driven decision making
- Enhanced customer safety with allergen tracking

### For Staff
- Simplified queue management
- Clear customer information at a glance
- Easy status updates
- Quick customer search and retrieval
- Safety alerts for allergen awareness

### For Customers
- Organized, fair queuing system
- Clear communication of wait times
- Recognition of allergen concerns
- Better overall dining experience
- Consistent service quality

## 🔐 Security Features

- Branch-level data isolation
- User role-based permissions
- Audit trail for all operations
- Secure customer data handling
- Compliance-ready structure

## 🎨 Customization

Built with customization in mind:
- Modular architecture for easy extension
- Well-structured code following Odoo guidelines
- Extensible models with proper inheritance
- Custom views that can be inherited
- API-ready for third-party integrations

## ⚙️ System Requirements

- Odoo 19.0 (Community or Enterprise)
- Python 3.10+
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## 📄 License

This module is licensed under LGPL-3. See LICENSE file for details.

---

**Ready to revolutionize your restaurant's waiting list management?**

Install now and experience professional-grade queue management with safety-first allergen tracking!

---

*Developed by Odoo PS | For support and customization inquiries, contact through Odoo App Store*
