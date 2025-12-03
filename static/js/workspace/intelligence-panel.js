/**
 * @file intelligence-panel.js
 * @description Dynamic Intelligence Panel rendering for the Agent Workspace
 * @version 1.0.0
 * 
 * This module handles lead-type-specific intelligence panel rendering:
 * - NED Listing: Foreclosure details, compliance & timeline
 * - Foreclosure Auction: Auction details, location & logistics
 * - Probate/Estate: Probate details, estate information
 * - Tax Lien: Lien details, timeline & urgency
 * 
 * Business Justification:
 * - Pillar 2 (Conversion Analytics): Isolating intelligence panel rendering 
 *   enables future A/B testing of field layouts and priority displays
 *   without touching VOIP or compliance code.
 * - Pillar 3 (Data Pipeline): New lead-type bundles (Code Violation, 
 *   Tired Landlord) can be added by modifying only this module.
 * 
 * @requires ComplianceGates - For calculateDaysUntilDeadline() on deadline fields
 */

/**
 * IntelligencePanel Module
 * Uses IIFE pattern to encapsulate configuration and expose public API
 * 
 * @returns {Object} Public API for intelligence panel rendering
 */
var IntelligencePanel = (function() {
    'use strict';

    // ==========================================
    // STATIC CONFIGURATION: FIELD BUNDLES PER LEAD TYPE
    // ==========================================

    /**
     * Field Display Configuration
     * Maps lead types to their section-grouped field bundles
     * 
     * @constant {Object}
     * @description Each lead type defines sections with arrays of field names.
     * New lead types can be added here without modifying rendering logic.
     */
    const FIELD_DISPLAY_CONFIG = {
        "NED Listing": {
            "Foreclosure Details": ["auction_date", "balance_due", "opening_bid"],
            "Compliance & Timeline": ["law_firm_name", "first_publication_date"]
        },
        "Foreclosure Auction": {
            "Auction Details": ["auction_platform", "auction_date", "opening_bid"],
            "Location & Logistics": ["auction_location", "registration_deadline"]
        },
        // V4.0 Phase 2a - Probate/Estate Bundle
        "Probate/Estate": {
            "Probate Details": ["probate_case_number", "probate_filing_date", "court_jurisdiction"],
            "Estate Information": ["executor_name", "decedent_name", "estate_value"]
        },
        // V4.0 Phase 2b/2c - Tax Lien Bundle (including Multi-Year)
        "Tax Lien": {
            "Tax Lien Details": ["lien_type", "tax_debt_amount"],
            "Multi-Year Breakdown": ["tax_delinquency_summary", "delinquent_years_count"],
            "Timeline & Urgency": ["delinquency_start_date", "redemption_deadline"]
        }
    };

    // ==========================================
    // STATIC CONFIGURATION: FIELD METADATA
    // ==========================================

    /**
     * Field Metadata
     * Defines labels and types for all intelligence fields
     * 
     * @constant {Object}
     * @description Types control formatting: 'money', 'date', 'text', 'law_firm',
     * 'fiduciary', 'deadline', 'category'. New field types can be added
     * by extending the renderField() function.
     */
    const FIELD_METADATA = {
        // NED Listing / Foreclosure Auction fields
        "auction_date": { label: "Auction Date", type: "date" },
        "balance_due": { label: "Balance Due", type: "money" },
        "opening_bid": { label: "Opening Bid", type: "money" },
        "law_firm_name": { label: "Law Firm Name", type: "law_firm" },
        "first_publication_date": { label: "First Publication Date", type: "date" },
        "auction_platform": { label: "Auction Platform", type: "text" },
        "auction_location": { label: "Auction Location", type: "text" },
        "registration_deadline": { label: "Registration Deadline", type: "date" },
        // V4.0 Phase 2a - Probate/Estate Fields
        "executor_name": { label: "Personal Representative", type: "fiduciary" },
        "probate_case_number": { label: "Case Number", type: "text" },
        "probate_filing_date": { label: "Filing Date", type: "date" },
        "estate_value": { label: "Estate Value", type: "money" },
        "decedent_name": { label: "Decedent Name", type: "text" },
        "court_jurisdiction": { label: "Court Jurisdiction", type: "text" },
        // V4.0 Phase 2b - Tax Lien Fields
        "tax_debt_amount": { label: "Tax Debt Amount", type: "money" },
        "delinquency_start_date": { label: "Delinquency Start Date", type: "date" },
        "redemption_deadline": { label: "Redemption Deadline", type: "deadline" },
        "lien_type": { label: "Lien Type", type: "category" },
        // V4.0 Phase 2c - Tax Lien Multi-Year Fields
        "tax_delinquency_summary": { label: "Tax Delinquency Summary", type: "multi_year_summary" },
        "delinquent_years_count": { label: "Delinquent Years", type: "years_count" }
    };

    // ==========================================
    // PRIVATE HELPER FUNCTIONS
    // ==========================================

    /**
     * Format a numeric value as USD currency
     * 
     * @param {number|string|null|undefined} value - The value to format
     * @returns {string} Formatted currency string or "N/A"
     * 
     * @example
     * formatMoney(125000) // Returns "$125,000"
     * formatMoney(null)   // Returns "N/A"
     */
    function formatMoney(value) {
        if (value === null || value === undefined || value === "") {
            return "N/A";
        }
        return new Intl.NumberFormat('en-US', { 
            style: 'currency', 
            currency: 'USD', 
            maximumFractionDigits: 0 
        }).format(value);
    }

    /**
     * Format a date string from YYYY-MM-DD to MM/DD/YYYY
     * 
     * @param {string|null|undefined} value - Date string in YYYY-MM-DD format
     * @returns {string} Formatted date string or "Unknown"
     * 
     * @example
     * formatDate("2025-03-15") // Returns "03/15/2025"
     * formatDate(null)         // Returns "Unknown"
     */
    function formatDate(value) {
        if (!value) {
            return "Unknown";
        }
        try {
            // Expecting YYYY-MM-DD
            const parts = value.split('-');
            if (parts.length === 3) {
                return `${parts[1]}/${parts[2]}/${parts[0]}`;
            }
            return value;
        } catch (e) {
            return value;
        }
    }

    /**
     * Render a single field with appropriate formatting and styling
     * 
     * @param {string} fieldName - The field key matching FIELD_METADATA
     * @param {*} value - The field value to render
     * @returns {string} HTML string for the field
     * 
     * @description Handles special rendering for different field types:
     * - money: Currency formatting
     * - date: Date formatting (YYYY-MM-DD → MM/DD/YYYY)
     * - law_firm: Attorney represented warning badge
     * - fiduciary: Fiduciary contact styling for Personal Representative
     * - deadline: Urgency indicator with days remaining (uses ComplianceGates)
     * - category: Badge-style display with color coding
     * - text: Default text display
     * 
     * @requires ComplianceGates.calculateDaysUntilDeadline for deadline fields
     */
    function renderField(fieldName, value) {
        const meta = FIELD_METADATA[fieldName] || { 
            label: fieldName.replace(/_/g, ' '), 
            type: 'text' 
        };
        let displayValue = value;
        let extraHtml = '';
        let valueClass = "text-base font-semibold text-gray-900";

        // Handle null/undefined/empty values
        if (value === null || value === undefined || value === "") {
            displayValue = (meta.type === 'money') ? "N/A" : "Unknown";
            valueClass = "text-base font-semibold text-gray-400";
        } else {
            // Apply type-specific formatting
            if (meta.type === 'money') {
                displayValue = formatMoney(value);
            } else if (meta.type === 'date') {
                displayValue = formatDate(value);
            } else if (meta.type === 'law_firm') {
                valueClass = "text-base font-semibold text-red-700";
                extraHtml = `
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 ml-2">
                        ⚖️ Attorney Represented
                    </span>
                    <p class="text-xs text-red-600 mt-1 w-full">
                        ⚠️ Compliance: Obtain attorney consent before dialing
                    </p>
                `;
            } else if (meta.type === 'fiduciary') {
                // V4.0 Phase 2a: Fiduciary contact styling for Personal Representative
                valueClass = "text-base font-semibold text-orange-700";
                extraHtml = `
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800 ml-2">
                        🔶 Fiduciary
                    </span>
                    <p class="text-xs text-orange-600 mt-1 w-full">
                        ℹ️ This is the Executor/Administrator, not the property owner
                    </p>
                `;
            } else if (meta.type === 'deadline') {
                // V4.0 Phase 2b: Redemption deadline with urgency indicator
                // Cross-module dependency: ComplianceGates provides deadline calculation
                const daysRemaining = (typeof ComplianceGates !== 'undefined') 
                    ? ComplianceGates.calculateDaysUntilDeadline(value) 
                    : null;
                
                displayValue = formatDate(value);
                
                if (daysRemaining !== null && daysRemaining <= 30) {
                    valueClass = "text-base font-bold text-red-700";
                    extraHtml = `
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 ml-2">
                            🔴 ${daysRemaining} days remaining
                        </span>
                        <p class="text-xs text-red-600 mt-1 w-full">
                            ⚠️ Use ethical language - avoid pressure tactics
                        </p>
                    `;
                } else if (daysRemaining !== null && daysRemaining <= 60) {
                    valueClass = "text-base font-semibold text-orange-600";
                    extraHtml = `
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800 ml-2">
                            🟠 ${daysRemaining} days remaining
                        </span>
                    `;
                }
            } else if (meta.type === 'category') {
                // Category fields - display as colored badge
                valueClass = "text-base font-semibold text-gray-900";
                const categoryColors = {
                    'Property Tax': 'bg-green-100 text-green-800',
                    'IRS Federal': 'bg-red-100 text-red-800',
                    'State Tax': 'bg-blue-100 text-blue-800',
                    'HOA/Assessment': 'bg-yellow-100 text-yellow-800',
                    'Municipal/Utility': 'bg-purple-100 text-purple-800',
                    'Multiple': 'bg-pink-100 text-pink-800'
                };
                const colorClass = categoryColors[value] || 'bg-gray-100 text-gray-800';
                displayValue = `<span class="inline-flex items-center px-2 py-1 rounded text-sm font-medium ${colorClass}">${value}</span>`;
            } else if (meta.type === 'multi_year_summary') {
                // V4.0 Phase 2c: Multi-year tax delinquency summary
                // Example: "$12,740 total (2023: $6,501, 2024: $6,239)"
                valueClass = "text-base font-semibold text-gray-900";
                extraHtml = `
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800 ml-2">
                        📊 Multi-Year Data
                    </span>
                `;
            } else if (meta.type === 'years_count') {
                // V4.0 Phase 2c: Number of delinquent years
                const count = parseInt(value);
                if (count >= 3) {
                    valueClass = "text-base font-bold text-red-700";
                    extraHtml = `
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 ml-2">
                            🔴 ${count} Years - High Risk
                        </span>
                    `;
                } else if (count === 2) {
                    valueClass = "text-base font-semibold text-orange-600";
                    extraHtml = `
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800 ml-2">
                            🟠 ${count} Years
                        </span>
                    `;
                } else {
                    displayValue = count + " year" + (count !== 1 ? "s" : "");
                }
            }
        }

        return `
            <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">${meta.label}</label>
                <div class="flex flex-wrap items-center">
                    <p class="${valueClass}">${displayValue}</p>
                    ${extraHtml}
                </div>
            </div>
        `;
    }

    /**
     * Render a section with title and grouped fields
     * 
     * @param {string} title - Section title (uppercase tracking)
     * @param {string[]} fields - Array of field names to render
     * @param {Object} data - Intelligence data object containing field values
     * @returns {string} HTML string for the section
     * 
     * @example
     * renderDynamicSection("Foreclosure Details", ["auction_date", "balance_due"], data)
     */
    function renderDynamicSection(title, fields, data) {
        const fieldsHtml = fields.map(fieldName => {
            const value = data[fieldName];
            return renderField(fieldName, value);
        }).join('');

        return `
            <div class="bg-white rounded-lg p-4 shadow-sm mb-4">
                <h3 class="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
                    ${title}
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${fieldsHtml}
                </div>
            </div>
        `;
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    return {
        /**
         * Render the dynamic intelligence panel into a container
         * 
         * @param {string} containerId - The ID of the container element (without #)
         * @param {Object} leadData - Lead data object containing lead_type
         * @param {Object} intelligenceData - Intelligence data object with field values
         * @returns {void}
         * 
         * @description Renders lead-type-specific sections into the specified container.
         * If the lead type has no configured fields, no sections are rendered.
         * Each section is appended to the container using insertAdjacentHTML.
         * 
         * @example
         * IntelligencePanel.render('dynamic-intelligence-sections', leadData, intelligenceData);
         */
        render: function(containerId, leadData, intelligenceData) {
            const container = document.getElementById(containerId);
            if (!container) {
                console.warn('IntelligencePanel: Container not found:', containerId);
                return;
            }

            // Clear any existing content
            container.innerHTML = '';

            const leadType = leadData.lead_type;
            const config = FIELD_DISPLAY_CONFIG[leadType];

            if (config) {
                Object.entries(config).forEach(([sectionTitle, fields]) => {
                    const sectionHtml = renderDynamicSection(sectionTitle, fields, intelligenceData);
                    container.insertAdjacentHTML('beforeend', sectionHtml);
                });
                console.log('IntelligencePanel: Rendered sections for lead type:', leadType);
            } else {
                console.log('IntelligencePanel: No field config for lead type:', leadType);
            }
        },

        /**
         * Get the field display configuration
         * 
         * @returns {Object} The FIELD_DISPLAY_CONFIG object
         * 
         * @description Returns the mapping of lead types to their section-grouped fields.
         * Useful for inspection or extending field configurations dynamically.
         */
        getFieldConfig: function() {
            return FIELD_DISPLAY_CONFIG;
        },

        /**
         * Get the field metadata
         * 
         * @returns {Object} The FIELD_METADATA object
         * 
         * @description Returns the mapping of field names to their labels and types.
         * Useful for building dynamic forms or validating field names.
         */
        getFieldMetadata: function() {
            return FIELD_METADATA;
        },

        /**
         * Format a money value using the module's formatter
         * 
         * @param {number|string|null|undefined} value - The value to format
         * @returns {string} Formatted currency string or "N/A"
         * 
         * @description Exposed for external use (e.g., by other modules that need
         * consistent currency formatting).
         */
        formatMoney: formatMoney,

        /**
         * Format a date value using the module's formatter
         * 
         * @param {string|null|undefined} value - Date string in YYYY-MM-DD format
         * @returns {string} Formatted date string or "Unknown"
         * 
         * @description Exposed for external use (e.g., by other modules that need
         * consistent date formatting).
         */
        formatDate: formatDate
    };
})();

// Export for both browser global and module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IntelligencePanel;
}