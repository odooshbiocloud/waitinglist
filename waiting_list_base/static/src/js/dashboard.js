/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Waiting List Dashboard Widget
 * Provides real-time dashboard for restaurant hostess
 */
export class WaitingListDashboard extends Component {
    static template = "waiting_list_base.Dashboard";
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            waitingList: [],
            tables: [],
            stats: {
                totalWaiting: 0,
                vipWaiting: 0,
                averageWaitTime: 0,
                availableTables: 0,
                tableUtilization: 0
            },
            loading: true,
            selectedCustomer: null,
            selectedTable: null
        });
        
        onMounted(this.loadDashboardData);
        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
        
        // Auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }
    
    /**
     * Load all dashboard data
     */
    async loadDashboardData() {
        try {
            this.state.loading = true;
            
            const [waitingList, tables, stats] = await Promise.all([
                this.loadWaitingList(),
                this.loadTables(),
                this.loadStats()
            ]);
            
            this.state.waitingList = waitingList;
            this.state.tables = tables;
            this.state.stats = stats;
            
        } catch (error) {
            this.notification.add("Error loading dashboard data", { type: "danger" });
            console.error("Dashboard load error:", error);
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Load waiting list entries
     */
    async loadWaitingList() {
        return await this.orm.searchRead(
            "waiting.list",
            [["status", "in", ["waiting", "called"]]],
            [
                "name", "phone", "party_size", "customer_id", "vip_customer",
                "priority_score", "estimated_wait_time", "actual_wait_time",
                "requested_table_id", "status", "special_requests",
                "customer_type", "arrival_time"
            ],
            { order: "priority_score desc, arrival_time asc" }
        );
    }
    
    /**
     * Load table information
     */
    async loadTables() {
        return await this.orm.searchRead(
            "restaurant.table",
            [],
            [
                "name", "seats", "floor_id", "active", "color",
                "position_h", "position_v", "shape",
                "current_utilization", "daily_revenue", "daily_customers"
            ],
            { order: "floor_id, name" }
        );
    }
    
    /**
     * Load dashboard statistics
     */
    async loadStats() {
        const domain = [["status", "in", ["waiting", "called"]]];
        
        const waitingCount = await this.orm.searchCount("waiting.list", domain);
        const vipCount = await this.orm.searchCount("waiting.list", [
            ...domain,
            ["vip_customer", "=", true]
        ]);
        
        const availableTables = await this.orm.searchCount("restaurant.table", [
            ["active", "=", true]
            // Add availability logic here
        ]);
        
        // Calculate average wait time from recent data
        const recentEntries = await this.orm.searchRead(
            "waiting.list",
            [["status", "=", "seated"], ["create_date", ">=", this._getToday()]],
            ["actual_wait_time"]
        );
        
        const avgWaitTime = recentEntries.length > 0 
            ? recentEntries.reduce((sum, entry) => sum + entry.actual_wait_time, 0) / recentEntries.length
            : 0;
        
        return {
            totalWaiting: waitingCount,
            vipWaiting: vipCount,
            averageWaitTime: Math.round(avgWaitTime),
            availableTables: availableTables,
            tableUtilization: 75 // Calculate from table data
        };
    }
    
    /**
     * Get today's date for filtering
     */
    _getToday() {
        return new Date().toISOString().split('T')[0];
    }
    
    /**
     * Seat a customer at a table
     */
    async seatCustomer(customerId, tableId = null) {
        try {
            if (!tableId && this.state.selectedTable) {
                tableId = this.state.selectedTable.id;
            }
            
            await this.orm.call(
                "waiting.list",
                "seat_customer",
                [customerId],
                { table_id: tableId }
            );
            
            this.notification.add("Customer seated successfully", { type: "success" });
            this.loadDashboardData();
            this.clearSelection();
            
        } catch (error) {
            this.notification.add("Error seating customer", { type: "danger" });
            console.error("Seat customer error:", error);
        }
    }
    
    /**
     * Cancel waiting list entry
     */
    async cancelEntry(entryId) {
        try {
            await this.orm.write("waiting.list", [entryId], { status: "cancelled" });
            this.notification.add("Entry cancelled", { type: "success" });
            this.loadDashboardData();
            
        } catch (error) {
            this.notification.add("Error cancelling entry", { type: "danger" });
            console.error("Cancel entry error:", error);
        }
    }
    
    /**
     * Mark customer as no-show
     */
    async markNoShow(entryId) {
        try {
            await this.orm.write("waiting.list", [entryId], { status: "no_show" });
            this.notification.add("Marked as no-show", { type: "success" });
            this.loadDashboardData();
            
        } catch (error) {
            this.notification.add("Error marking no-show", { type: "danger" });
            console.error("No-show error:", error);
        }
    }
    
    /**
     * Send notification to customer
     */
    async notifyCustomer(entryId) {
        try {
            await this.orm.call("waiting.list", "send_notification", [entryId]);
            this.notification.add("Notification sent", { type: "success" });
            
        } catch (error) {
            this.notification.add("Error sending notification", { type: "danger" });
            console.error("Notification error:", error);
        }
    }
    
    /**
     * Open add customer wizard
     */
    async addCustomer() {
        try {
            await this.action.doAction({
                type: "ir.actions.act_window",
                res_model: "add.to.waitlist.wizard",
                view_mode: "form",
                target: "new",
                name: "Add Customer to Waiting List"
            });
        } catch (error) {
            this.notification.add("Error opening add customer form", { type: "danger" });
        }
    }
    
    /**
     * Select customer for seating
     */
    selectCustomer(customer) {
        this.state.selectedCustomer = customer;
        this.state.selectedTable = null;
    }
    
    /**
     * Select table for seating
     */
    selectTable(table) {
        this.state.selectedTable = table;
        
        // If customer is selected, seat them
        if (this.state.selectedCustomer) {
            this.seatCustomer(this.state.selectedCustomer.id, table.id);
        }
    }
    
    /**
     * Clear selections
     */
    clearSelection() {
        this.state.selectedCustomer = null;
        this.state.selectedTable = null;
    }
    
    /**
     * Get status badge class
     */
    getStatusClass(status) {
        const statusClasses = {
            'waiting': 'status_waiting',
            'called': 'status_called',
            'seated': 'status_seated',
            'cancelled': 'status_cancelled',
            'no_show': 'status_no_show'
        };
        return statusClasses[status] || 'status_waiting';
    }
    
    /**
     * Get priority class
     */
    getPriorityClass(priorityScore) {
        if (priorityScore >= 80) return 'priority_high';
        if (priorityScore >= 60) return 'priority_medium';
        return 'priority_low';
    }
    
    /**
     * Get table status class
     */
    getTableStatusClass(table) {
        // Logic to determine table status based on occupancy
        return 'available'; // Default for now
    }
    
    /**
     * Format wait time display
     */
    formatWaitTime(minutes) {
        if (minutes < 60) {
            return `${minutes}m`;
        }
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours}h ${mins}m`;
    }
    
    /**
     * Get VIP customers
     */
    get vipCustomers() {
        return this.state.waitingList.filter(customer => customer.vip_customer);
    }
    
    /**
     * Get regular customers
     */
    get regularCustomers() {
        return this.state.waitingList.filter(customer => !customer.vip_customer);
    }
    
    /**
     * Get available tables
     */
    get availableTables() {
        return this.state.tables.filter(table => this.getTableStatusClass(table) === 'available');
    }
}

// Register the dashboard as a client action
registry.category("actions").add("waiting_list.dashboard_action", {
    component: WaitingListDashboard,
    type: "ir.actions.client",
});
