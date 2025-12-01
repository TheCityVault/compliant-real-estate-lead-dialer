/**
 * Disposition Form Module
 * 
 * Encapsulates form validation, conditional field logic, and submission handling
 * for the Call Disposition Form in the Agent Workspace.
 * 
 * Extracted from workspace.html for maintainability and future enhancements.
 * 
 * @module DispositionForm
 * @version 1.0.0
 * 
 * Business Justification (Pillar 4 - Disposition Funnel):
 * Isolating form logic enables future enhancements like disposition-specific
 * follow-up prompts, integration with task automation, and analytics on
 * agent workflow patterns.
 */

var DispositionForm = (function() {
    'use strict';

    // ==========================================
    // PRIVATE STATE
    // ==========================================
    
    /** @type {string|null} Current Podio item ID */
    let _itemId = null;
    
    /** @type {Object} DOM element references (set during init) */
    let _elements = {};
    
    /** @type {Function|null} Callback to get current CallSid from TwilioVOIP */
    let _getCallSid = null;
    
    /** @type {Function|null} Callback for successful form submission */
    let _onSubmitSuccess = null;
    
    /** @type {Object} Template data for contact info (owner phone, name, addresses) */
    let _templateData = {};

    // ==========================================
    // DISPOSITIONS THAT REQUIRE NEXT ACTION DATE
    // ==========================================
    
    /** @type {Array<string>} Dispositions requiring a next action date */
    const DISPOSITIONS_REQUIRING_DATE = ['Appointment Set', 'Callback Scheduled'];

    // ==========================================
    // PRIVATE FUNCTIONS
    // ==========================================

    /**
     * Validates the disposition form
     * Checks if required fields are filled and enables/disables submit button
     * 
     * @private
     * @returns {boolean} True if form is valid, false otherwise
     * @description Validates disposition code selection and conditional next action date
     */
    function validateForm() {
        if (!_elements.dispositionCodeSelect || !_elements.submitButton) {
            console.warn('DispositionForm: Required elements not initialized');
            return false;
        }

        const dispositionSelected = _elements.dispositionCodeSelect.value !== '';
        const disposition = _elements.dispositionCodeSelect.value;
        const requiresNextAction = DISPOSITIONS_REQUIRING_DATE.includes(disposition);
        const nextActionFilled = _elements.nextActionDateInput && _elements.nextActionDateInput.value !== '';

        // Enable submit button only if disposition is selected
        // AND if next action is required, it must be filled
        const isValid = dispositionSelected && (!requiresNextAction || nextActionFilled);

        _elements.submitButton.disabled = !isValid;

        if (isValid) {
            _elements.submitButton.classList.remove('bg-secondary', 'hover:bg-gray-600');
            _elements.submitButton.classList.add('bg-success', 'hover:bg-green-600');
            if (_elements.formValidationMessage) {
                _elements.formValidationMessage.classList.add('hidden');
            }
        } else {
            _elements.submitButton.classList.add('bg-secondary', 'hover:bg-gray-600');
            _elements.submitButton.classList.remove('bg-success', 'hover:bg-green-600');

            if (_elements.formValidationMessage) {
                if (dispositionSelected && requiresNextAction && !nextActionFilled) {
                    _elements.formValidationMessage.classList.remove('hidden');
                    _elements.formValidationMessage.textContent =
                        'Next Action Date is required for this disposition';
                } else if (!dispositionSelected) {
                    _elements.formValidationMessage.classList.remove('hidden');
                    _elements.formValidationMessage.textContent =
                        'Please select a Disposition Code to continue';
                }
            }
        }

        return isValid;
    }

    /**
     * Handles disposition code change
     * Updates conditional field requirements and validates form
     * 
     * @private
     * @description Updates next action date requirement based on disposition selection
     */
    function handleDispositionChange() {
        validateForm();

        const disposition = _elements.dispositionCodeSelect.value;
        const requiresNextAction = DISPOSITIONS_REQUIRING_DATE.includes(disposition);

        if (requiresNextAction) {
            if (_elements.nextActionRequired) {
                _elements.nextActionRequired.classList.remove('hidden');
            }
            if (_elements.nextActionHint) {
                _elements.nextActionHint.classList.add('hidden');
            }
            if (_elements.nextActionRequiredHint) {
                _elements.nextActionRequiredHint.classList.remove('hidden');
            }
            if (_elements.nextActionDateInput) {
                _elements.nextActionDateInput.required = true;
            }
        } else {
            if (_elements.nextActionRequired) {
                _elements.nextActionRequired.classList.add('hidden');
            }
            if (_elements.nextActionHint) {
                _elements.nextActionHint.classList.remove('hidden');
            }
            if (_elements.nextActionRequiredHint) {
                _elements.nextActionRequiredHint.classList.add('hidden');
            }
            if (_elements.nextActionDateInput) {
                _elements.nextActionDateInput.required = false;
            }
        }
    }

    /**
     * Handles form submission
     * Validates form, prepares data, and submits via AJAX
     * 
     * @private
     * @param {Event} e - Form submit event
     * @description Submits call disposition data to /submit_call_data endpoint
     */
    async function handleFormSubmit(e) {
        e.preventDefault();

        if (!_elements.submitButton || !_elements.dispositionForm) {
            console.error('DispositionForm: Required elements not available for submission');
            return;
        }

        // Disable submit button during submission
        _elements.submitButton.disabled = true;
        _elements.submitButton.innerHTML = `
            <svg class="animate-spin h-5 w-5 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Submitting...
        `;

        try {
            // Get CallSid from TwilioVOIP module via callback
            const callSid = typeof _getCallSid === 'function' ? _getCallSid() : null;
            
            // Prepare form data
            const formData = {
                item_id: _itemId,
                call_sid: callSid,
                disposition_code: _elements.dispositionCodeSelect.value,
                agent_notes: _elements.agentNotes ? _elements.agentNotes.value : '',
                motivation_level: _elements.motivationLevel ? _elements.motivationLevel.value : '',
                next_action_date: _elements.nextActionDateInput ? _elements.nextActionDateInput.value : '',
                asking_price: _elements.askingPrice ? _elements.askingPrice.value : ''
            };

            console.log('Submitting form data with CallSid:', callSid);

            // Submit to backend
            const response = await fetch('/submit_call_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to submit call data');
            }

            // Show success message
            if (_elements.dispositionForm) {
                _elements.dispositionForm.classList.add('hidden');
            }
            if (_elements.successMessage) {
                _elements.successMessage.classList.remove('hidden');
                _elements.successMessage.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }

            // Call success callback if provided
            if (typeof _onSubmitSuccess === 'function') {
                _onSubmitSuccess(formData);
            }

        } catch (error) {
            console.error('Error submitting call data:', error);
            showError('Failed to submit call data: ' + error.message);

            // Re-enable submit button
            _elements.submitButton.disabled = false;
            _elements.submitButton.innerHTML = `
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Submit Call Data
            `;
        }
    }

    /**
     * Displays an error message to the user
     * 
     * @param {string} message - Error message to display
     * @description Shows error message banner and scrolls it into view
     */
    function showError(message) {
        if (_elements.errorMessageText) {
            _elements.errorMessageText.textContent = message;
        }
        if (_elements.errorMessage) {
            _elements.errorMessage.classList.remove('hidden');
            _elements.errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * Copies text to clipboard with fallback for older browsers
     * 
     * @param {string} text - Text to copy to clipboard
     * @description Utility function for copying phone numbers and other data
     */
    function copyToClipboard(text) {
        navigator.clipboard
            .writeText(text)
            .then(() => {
                alert('📋 Phone number copied: ' + text);
            })
            .catch((err) => {
                console.error('Failed to copy:', err);
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                alert('📋 Phone number copied: ' + text);
            });
    }

    /**
     * Checks if mailing address row should be hidden
     * Hides the row if mailing address is same as property address
     * 
     * @description Contract v1.1.3: Hide redundant mailing address info
     */
    function checkMailingAddress() {
        const mailingAddr = _templateData.ownerMailingAddress || '';
        const propertyAddr = _templateData.validatedMailingAddress || '';

        if (
            mailingAddr === propertyAddr ||
            !mailingAddr ||
            mailingAddr === 'Same as property'
        ) {
            if (_elements.mailingAddressRow) {
                _elements.mailingAddressRow.style.display = 'none';
            }
        }
    }

    /**
     * Auto-populates dialer with owner phone if available
     * 
     * @description Initializes dialer fields from lead/contact data
     */
    function initializeDialer() {
        const ownerPhone = _templateData.ownerPhone || '';
        const ownerName = _templateData.ownerName || '';

        if (ownerPhone) {
            console.log('✅ Dialer auto-populated with owner phone:', ownerPhone);

            // Auto-fill contact name in lead name field (if owner name exists)
            if (_elements.leadNameEl && ownerName) {
                _elements.leadNameEl.textContent = ownerName;
            }
        } else {
            console.warn('⚠️ No owner phone available for auto-populate');
        }
    }

    /**
     * Sets up event listeners for form elements
     * @private
     */
    function setupEventListeners() {
        // Disposition code change handler
        if (_elements.dispositionCodeSelect) {
            _elements.dispositionCodeSelect.addEventListener('change', handleDispositionChange);
        }

        // Next action date change handler
        if (_elements.nextActionDateInput) {
            _elements.nextActionDateInput.addEventListener('change', validateForm);
        }

        // Form submission handler
        if (_elements.dispositionForm) {
            _elements.dispositionForm.addEventListener('submit', handleFormSubmit);
        }
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    return {
        /**
         * Initialize the Disposition Form module
         * 
         * @param {Object} config - Configuration options
         * @param {string} config.itemId - Podio item ID for the current lead
         * @param {Object} config.elements - DOM element references
         * @param {HTMLSelectElement} config.elements.dispositionCodeSelect - Disposition code dropdown
         * @param {HTMLInputElement} config.elements.nextActionDateInput - Next action date input
         * @param {HTMLElement} config.elements.nextActionRequired - Required indicator span
         * @param {HTMLElement} config.elements.nextActionHint - Optional hint text
         * @param {HTMLElement} config.elements.nextActionRequiredHint - Required hint text
         * @param {HTMLButtonElement} config.elements.submitButton - Submit button
         * @param {HTMLFormElement} config.elements.dispositionForm - Form element
         * @param {HTMLElement} config.elements.formValidationMessage - Validation message element
         * @param {HTMLElement} config.elements.successMessage - Success message element
         * @param {HTMLElement} config.elements.errorMessage - Error message container
         * @param {HTMLElement} config.elements.errorMessageText - Error message text element
         * @param {HTMLElement} config.elements.agentNotes - Agent notes textarea
         * @param {HTMLElement} config.elements.motivationLevel - Motivation level select
         * @param {HTMLElement} config.elements.askingPrice - Asking price input
         * @param {HTMLElement} config.elements.mailingAddressRow - Mailing address row element
         * @param {HTMLElement} config.elements.leadNameEl - Lead name display element
         * @param {Function} [config.getCallSid] - Callback to get current CallSid from TwilioVOIP
         * @param {Function} [config.onSubmitSuccess] - Callback for successful submission
         * @param {Object} [config.templateData] - Template data for contact info
         * @param {string} [config.templateData.ownerPhone] - Owner phone number
         * @param {string} [config.templateData.ownerName] - Owner name
         * @param {string} [config.templateData.ownerMailingAddress] - Owner mailing address
         * @param {string} [config.templateData.validatedMailingAddress] - Property address
         */
        init: function(config) {
            if (!config) {
                console.error('DispositionForm: Configuration object required');
                return;
            }

            // Store configuration
            _itemId = config.itemId || null;
            _getCallSid = config.getCallSid || null;
            _onSubmitSuccess = config.onSubmitSuccess || null;
            _templateData = config.templateData || {};

            // Store DOM element references
            _elements = config.elements || {};

            // Set up event listeners
            setupEventListeners();

            // Initialize form validation state
            validateForm();

            // Initialize contact info helpers
            checkMailingAddress();
            initializeDialer();

            console.log('DispositionForm initialized:', {
                itemId: _itemId,
                hasCallSidCallback: typeof _getCallSid === 'function'
            });
        },

        /**
         * Validate the form and update UI state
         * 
         * @returns {boolean} True if form is valid
         * @description Public wrapper for form validation
         */
        validate: function() {
            return validateForm();
        },

        /**
         * Display an error message to the user
         * 
         * @param {string} message - Error message to display
         */
        showError: showError,

        /**
         * Copy text to clipboard
         * 
         * @param {string} text - Text to copy
         * @description Utility for copying phone numbers and other data
         */
        copyToClipboard: copyToClipboard,

        /**
         * Check and hide mailing address row if redundant
         * 
         * @description Contract v1.1.3 compliance
         */
        checkMailingAddress: checkMailingAddress,

        /**
         * Initialize dialer with owner phone data
         */
        initializeDialer: initializeDialer,

        /**
         * Get the list of dispositions that require a next action date
         * 
         * @returns {Array<string>} Disposition codes requiring dates
         */
        getDispositionsRequiringDate: function() {
            return [...DISPOSITIONS_REQUIRING_DATE];
        },

        /**
         * Check if a disposition requires a next action date
         * 
         * @param {string} disposition - Disposition code to check
         * @returns {boolean} True if date is required
         */
        requiresNextActionDate: function(disposition) {
            return DISPOSITIONS_REQUIRING_DATE.includes(disposition);
        },

        /**
         * Reset the form to its initial state
         * 
         * @description Clears form fields and resets validation state
         */
        reset: function() {
            if (_elements.dispositionForm) {
                _elements.dispositionForm.reset();
            }
            validateForm();
            
            // Reset conditional field visibility
            if (_elements.nextActionRequired) {
                _elements.nextActionRequired.classList.add('hidden');
            }
            if (_elements.nextActionHint) {
                _elements.nextActionHint.classList.remove('hidden');
            }
            if (_elements.nextActionRequiredHint) {
                _elements.nextActionRequiredHint.classList.add('hidden');
            }
        },

        /**
         * Get the current item ID
         * 
         * @returns {string|null} The current Podio item ID
         */
        getItemId: function() {
            return _itemId;
        },

        /**
         * Set the item ID (useful for dynamic lead switching)
         * 
         * @param {string} itemId - New Podio item ID
         */
        setItemId: function(itemId) {
            _itemId = itemId;
        }
    };
})();

// Export for module systems (if available)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DispositionForm;
}