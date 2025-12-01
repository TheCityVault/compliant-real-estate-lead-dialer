/**
 * @file compliance-gates.js
 * @description Compliance gate logic for the Agent Workspace
 * @version 1.0.0
 * 
 * This module handles three compliance gates:
 * 1. Owner Occupied HARD Gate - Blocks dialing until agent acknowledges disclosure
 * 2. Probate Fiduciary SOFT Gate - Displays fiduciary contact notice for Probate leads
 * 3. Tax Lien Redemption Deadline SOFT Gate - Alerts agents to imminent deadlines
 * 
 * Business Justification:
 * - CFPB Reg X compliance requires isolated, auditable gate logic
 * - Surgical edits for regulatory updates without touching unrelated code
 * - Pillar 1 (Compliance) isolation reduces audit risk
 */

/**
 * ComplianceGates Module
 * Uses IIFE pattern to encapsulate state and expose public API
 * 
 * @param {Object} config - Configuration object
 * @param {string} config.ownerOccupiedStatus - The owner occupied status ('Yes', 'No', 'Unknown')
 * @param {string} config.itemId - The Podio item ID for the current lead
 * @param {string} config.leadType - The lead type (e.g., 'Probate/Estate', 'Tax Lien')
 * @param {Object} config.intelligenceData - Intelligence data containing deadline info
 * @returns {Object} Public API for compliance gates
 */
const ComplianceGates = (function() {
    'use strict';

    // ==========================================
    // PRIVATE STATE
    // ==========================================
    
    /** @type {boolean} Whether the dialer is locked due to Owner Occupied status */
    let _isDialerLocked = false;
    
    /** @type {boolean} Whether the fiduciary notice has been acknowledged */
    let _fiduciaryNoticeAcknowledged = false;
    
    /** @type {boolean} Whether the deadline notice has been acknowledged */
    let _deadlineNoticeAcknowledged = false;
    
    /** @type {string} Current item ID */
    let _itemId = '';
    
    /** @type {string} Current lead type */
    let _leadType = '';
    
    /** @type {Object} Intelligence data */
    let _intelligenceData = {};

    // ==========================================
    // DOM ELEMENT REFERENCES (set during init)
    // ==========================================
    
    let _dialButton = null;
    let _dialButtonText = null;
    let _complianceModal = null;
    let _unlockDialerBtn = null;
    let _cancelComplianceBtn = null;
    let _complianceAcknowledge = null;
    let _fiduciaryTooltip = null;
    let _fiduciaryBadge = null;
    let _deadlineTooltip = null;
    let _deadlineBadge = null;
    let _deadlineBadgeContainer = null;
    let _daysRemainingDisplay = null;

    // ==========================================
    // OWNER OCCUPIED HARD GATE (Phase 1)
    // ==========================================

    /**
     * Updates the dial button state based on lock status
     * When locked, button shows compliance warning; when unlocked, shows normal state
     * 
     * @description HARD GATE: CFPA/Dodd-Frank compliance for owner-occupied properties
     * Prevents dialing until agent explicitly acknowledges Foreclosure Consultant Disclaimer
     */
    function updateDialButtonState() {
        if (!_dialButton || !_dialButtonText) {
            console.warn('ComplianceGates: Dial button elements not initialized');
            return;
        }

        if (_isDialerLocked) {
            _dialButton.classList.add('bg-gray-400', 'cursor-not-allowed');
            _dialButton.classList.remove('bg-primary', 'hover:bg-primary-dark');
            _dialButtonText.textContent = "⚠️ Compliance Check Required";
            // Note: We don't set disabled=true here because we need the click event 
            // to trigger the modal. Instead, we handle the click logic in the handler.
        } else {
            _dialButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
            _dialButton.classList.add('bg-primary', 'hover:bg-primary-dark');
            _dialButtonText.textContent = "Initiate Call";
            _dialButton.disabled = false;
        }
    }

    /**
     * Shows the compliance modal for owner-occupied acknowledgment
     * @private
     */
    function _showComplianceModal() {
        if (_complianceModal) {
            _complianceModal.classList.remove('hidden');
        }
    }

    /**
     * Hides the compliance modal
     * @private
     */
    function _hideComplianceModal() {
        if (_complianceModal) {
            _complianceModal.classList.add('hidden');
        }
        if (_complianceAcknowledge) {
            _complianceAcknowledge.checked = false;
        }
        if (_unlockDialerBtn) {
            _unlockDialerBtn.disabled = true;
        }
    }

    /**
     * Handles unlock dialer button click
     * @private
     */
    function _handleUnlockDialer() {
        _isDialerLocked = false;
        _hideComplianceModal();
        updateDialButtonState();
        
        // Change button text to indicate ready state
        if (_dialButtonText) {
            _dialButtonText.textContent = "Initiate Compliant Call";
        }
        
        console.log("✅ Compliance Gate Unlocked by Agent for lead:", _itemId);
    }

    /**
     * Checks if dialing should be blocked and shows modal if needed
     * 
     * @returns {boolean} True if dial should be blocked, false if allowed
     * @description Called by dial button click handler to enforce HARD gate
     */
    function checkDialerGate() {
        if (_isDialerLocked) {
            _showComplianceModal();
            return true; // Block dial
        }
        return false; // Allow dial
    }

    // ==========================================
    // PROBATE FIDUCIARY SOFT GATE (Phase 2a)
    // ==========================================

    /**
     * Toggles visibility of the fiduciary notice tooltip
     * 
     * @description SOFT GATE: Displays notice when contacting Personal Representative
     * for Probate/Estate leads. The PR is a fiduciary, not the property owner.
     * Required for ethical outreach - owner is deceased.
     */
    function toggleFiduciaryTooltip() {
        if (_fiduciaryTooltip) {
            _fiduciaryTooltip.classList.toggle('visible');
            if (_fiduciaryTooltip.classList.contains('visible')) {
                console.log('SOFT GATE: Fiduciary notice displayed for lead:', _itemId);
            }
        }
    }

    /**
     * Acknowledges the fiduciary notice
     * Hides tooltip and logs acknowledgment
     * 
     * @description Agent confirms understanding of fiduciary contact requirements
     */
    function acknowledgeFiduciaryNotice() {
        _fiduciaryNoticeAcknowledged = true;
        if (_fiduciaryTooltip) {
            _fiduciaryTooltip.classList.remove('visible');
        }
        console.log('✅ Fiduciary notice acknowledged by agent for lead:', _itemId);
    }

    // ==========================================
    // TAX LIEN REDEMPTION DEADLINE SOFT GATE (Phase 2b)
    // ==========================================

    /**
     * Calculates days remaining until a deadline date
     * 
     * @param {string} dateString - Date in YYYY-MM-DD format
     * @returns {number|null} Days until deadline, or null if invalid
     * 
     * @description Used to determine deadline urgency for Tax Lien compliance gate
     */
    function calculateDaysUntilDeadline(dateString) {
        if (!dateString) return null;
        try {
            // Expected format: YYYY-MM-DD
            const deadline = new Date(dateString + 'T00:00:00');
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const diffTime = deadline - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            return diffDays;
        } catch (e) {
            console.error('Error calculating days until deadline:', e);
            return null;
        }
    }

    /**
     * Checks and activates the redemption deadline gate for Tax Lien leads
     * 
     * @description SOFT GATE: Alerts agents to imminent redemption deadlines (≤30 days)
     * Compliance requirement: Avoid undue pressure - present facts neutrally
     */
    function checkRedemptionDeadlineGate() {
        // Only check for Tax Lien lead types
        if (_leadType !== 'Tax Lien') return;
        
        const redemptionDeadline = _intelligenceData.redemption_deadline;
        if (!redemptionDeadline) return;
        
        const daysRemaining = calculateDaysUntilDeadline(redemptionDeadline);
        
        if (daysRemaining !== null && daysRemaining <= 30 && daysRemaining >= 0) {
            // Show the imminent deadline badge
            if (_deadlineBadgeContainer) {
                _deadlineBadgeContainer.style.display = 'inline-block';
            }
            
            // Update days remaining display
            if (_daysRemainingDisplay) {
                if (daysRemaining === 0) {
                    _daysRemainingDisplay.textContent = 'TODAY - Deadline Day!';
                } else if (daysRemaining === 1) {
                    _daysRemainingDisplay.textContent = '1 Day Remaining';
                } else {
                    _daysRemainingDisplay.textContent = `${daysRemaining} Days Remaining`;
                }
            }
            
            console.log(`SOFT GATE: Redemption deadline in ${daysRemaining} days for lead:`, _itemId);
        }
    }

    /**
     * Toggles visibility of the deadline notice tooltip
     * 
     * @description Displays compliance guidance for imminent tax lien deadlines
     */
    function toggleDeadlineTooltip() {
        if (_deadlineTooltip) {
            _deadlineTooltip.classList.toggle('visible');
            if (_deadlineTooltip.classList.contains('visible')) {
                console.log('SOFT GATE: Redemption deadline notice displayed for lead:', _itemId);
            }
        }
    }

    /**
     * Acknowledges the deadline notice
     * Hides tooltip and logs acknowledgment
     * 
     * @description Agent confirms understanding of ethical outreach requirements
     */
    function acknowledgeDeadlineNotice() {
        _deadlineNoticeAcknowledged = true;
        if (_deadlineTooltip) {
            _deadlineTooltip.classList.remove('visible');
        }
        console.log('✅ Redemption deadline notice acknowledged by agent for lead:', _itemId);
    }

    // ==========================================
    // INITIALIZATION
    // ==========================================

    /**
     * Initializes the compliance gates module
     * 
     * @param {Object} config - Configuration object
     * @param {string} config.ownerOccupiedStatus - 'Yes', 'No', or 'Unknown'
     * @param {string} config.itemId - Podio item ID
     * @param {string} config.leadType - Lead type string
     * @param {Object} config.intelligenceData - Object with deadline info
     * @param {Object} config.elements - DOM element references
     */
    function init(config) {
        // Store configuration
        _itemId = config.itemId || '';
        _leadType = config.leadType || '';
        _intelligenceData = config.intelligenceData || {};
        
        // Initialize lock state based on owner occupied status
        const ownerOccupiedStatus = config.ownerOccupiedStatus || '';
        _isDialerLocked = (ownerOccupiedStatus === 'Yes' || ownerOccupiedStatus === 'Unknown');
        
        // Store DOM element references
        const elements = config.elements || {};
        _dialButton = elements.dialButton;
        _dialButtonText = elements.dialButtonText;
        _complianceModal = elements.complianceModal;
        _unlockDialerBtn = elements.unlockDialerBtn;
        _cancelComplianceBtn = elements.cancelComplianceBtn;
        _complianceAcknowledge = elements.complianceAcknowledge;
        _fiduciaryTooltip = elements.fiduciaryTooltip;
        _fiduciaryBadge = elements.fiduciaryBadge;
        _deadlineTooltip = elements.deadlineTooltip;
        _deadlineBadge = elements.deadlineBadge;
        _deadlineBadgeContainer = elements.deadlineBadgeContainer;
        _daysRemainingDisplay = elements.daysRemainingDisplay;
        
        // Set up event listeners for compliance modal
        _setupEventListeners();
        
        // Initialize button state
        updateDialButtonState();
        
        // Check redemption deadline gate for Tax Lien leads
        checkRedemptionDeadlineGate();
        
        console.log('ComplianceGates initialized:', {
            itemId: _itemId,
            isDialerLocked: _isDialerLocked,
            leadType: _leadType
        });
    }

    /**
     * Sets up event listeners for compliance UI elements
     * @private
     */
    function _setupEventListeners() {
        // Compliance acknowledge checkbox
        if (_complianceAcknowledge && _unlockDialerBtn) {
            _complianceAcknowledge.addEventListener('change', function() {
                _unlockDialerBtn.disabled = !this.checked;
            });
        }
        
        // Cancel compliance button
        if (_cancelComplianceBtn) {
            _cancelComplianceBtn.addEventListener('click', _hideComplianceModal);
        }
        
        // Unlock dialer button
        if (_unlockDialerBtn) {
            _unlockDialerBtn.addEventListener('click', _handleUnlockDialer);
        }
        
        // Click outside to close tooltips
        document.addEventListener('click', function(event) {
            // Fiduciary tooltip
            if (_fiduciaryBadge && _fiduciaryTooltip && 
                !_fiduciaryBadge.contains(event.target) && 
                !_fiduciaryTooltip.contains(event.target)) {
                _fiduciaryTooltip.classList.remove('visible');
            }
            // Deadline tooltip
            if (_deadlineBadge && _deadlineTooltip && 
                !_deadlineBadge.contains(event.target) && 
                !_deadlineTooltip.contains(event.target)) {
                _deadlineTooltip.classList.remove('visible');
            }
        });
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    return {
        /**
         * Initialize the compliance gates module
         * @type {Function}
         */
        init: init,
        
        /**
         * Update the dial button visual state based on lock status
         * @type {Function}
         */
        updateDialButtonState: updateDialButtonState,
        
        /**
         * Check if dial should be blocked and show modal if needed
         * @type {Function}
         * @returns {boolean} True if blocked, false if allowed
         */
        checkDialerGate: checkDialerGate,
        
        /**
         * Toggle fiduciary tooltip visibility (Probate leads)
         * @type {Function}
         */
        toggleFiduciaryTooltip: toggleFiduciaryTooltip,
        
        /**
         * Acknowledge fiduciary notice
         * @type {Function}
         */
        acknowledgeFiduciaryNotice: acknowledgeFiduciaryNotice,
        
        /**
         * Calculate days until deadline
         * @type {Function}
         * @param {string} dateString - YYYY-MM-DD format
         * @returns {number|null}
         */
        calculateDaysUntilDeadline: calculateDaysUntilDeadline,
        
        /**
         * Check and activate redemption deadline gate (Tax Lien leads)
         * @type {Function}
         */
        checkRedemptionDeadlineGate: checkRedemptionDeadlineGate,
        
        /**
         * Toggle deadline tooltip visibility (Tax Lien leads)
         * @type {Function}
         */
        toggleDeadlineTooltip: toggleDeadlineTooltip,
        
        /**
         * Acknowledge deadline notice
         * @type {Function}
         */
        acknowledgeDeadlineNotice: acknowledgeDeadlineNotice,
        
        /**
         * Get current dialer lock state
         * @type {Function}
         * @returns {boolean}
         */
        isDialerLocked: function() { return _isDialerLocked; },
        
        /**
         * Get fiduciary notice acknowledgment state
         * @type {Function}
         * @returns {boolean}
         */
        isFiduciaryAcknowledged: function() { return _fiduciaryNoticeAcknowledged; },
        
        /**
         * Get deadline notice acknowledgment state
         * @type {Function}
         * @returns {boolean}
         */
        isDeadlineAcknowledged: function() { return _deadlineNoticeAcknowledged; }
    };
})();

// Export for both browser global and module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComplianceGates;
}