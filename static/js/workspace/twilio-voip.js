/**
 * Twilio VOIP Module
 * 
 * Encapsulates Twilio Voice SDK initialization and call handling logic.
 * Extracted from workspace.html for maintainability and SDK upgrade isolation.
 * 
 * @module TwilioVOIP
 * @version 1.0.0
 * @requires Twilio Voice SDK v2.11.1 (self-hosted)
 * 
 * Business Justification (Pillar 5 - Scalability):
 * Isolating Twilio SDK logic enables easier SDK version upgrades and allows
 * VOIP debugging without touching compliance or form logic.
 */

var TwilioVOIP = (function() {
    'use strict';

    // ==========================================
    // PRIVATE STATE
    // ==========================================
    
    /** @type {Twilio.Device|null} Twilio Device instance */
    let twilioDevice = null;
    
    /** @type {Twilio.Call|null} Current active call/connection */
    let currentConnection = null;
    
    /** @type {string|null} CallSid for the current/last call (used for Podio mapping) */
    let currentCallSid = null;
    
    /** @type {string} Unique agent identity for VOIP registration */
    let agentIdentity = 'agent_' + Math.random().toString(36).substr(2, 9);
    
    /** @type {Object} DOM element references (set during init) */
    let elements = {};
    
    /** @type {Function|null} Callback for updating device status UI */
    let onStatusChange = null;

    // ==========================================
    // PRIVATE FUNCTIONS
    // ==========================================

    /**
     * Wait for Twilio SDK to be loaded (with timeout)
     * @private
     * @returns {Promise<void>} Resolves when SDK is available, rejects after timeout
     */
    function waitForTwilioSDK() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50; // 10 seconds max wait (50 * 200ms)

            const checkTwilio = setInterval(() => {
                attempts++;

                if (typeof Twilio !== 'undefined') {
                    clearInterval(checkTwilio);
                    resolve();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkTwilio);
                    reject(new Error('Twilio SDK failed to load after 10 seconds'));
                }
            }, 200); // Check every 200ms
        });
    }

    /**
     * Update device status display
     * @private
     * @param {string} message - Status message to display
     * @param {string} type - Status type: 'success', 'warning', or 'error'
     */
    function updateDeviceStatus(message, type) {
        const statusEl = document.getElementById('twilio-device-status');
        if (statusEl) {
            statusEl.textContent = message;
            if (type === 'success') {
                statusEl.className = 'ml-1 text-green-600';
            } else if (type === 'warning') {
                statusEl.className = 'ml-1 text-yellow-600';
            } else {
                statusEl.className = 'ml-1 text-red-600';
            }
        }
        
        // Call external callback if registered
        if (typeof onStatusChange === 'function') {
            onStatusChange(message, type);
        }
    }

    /**
     * Initialize the Twilio Voice client
     * @private
     * @returns {Promise<void>}
     */
    async function initializeTwilioClient() {
        try {
            // Wait for Twilio SDK to be loaded
            if (typeof Twilio === 'undefined') {
                console.log('⏳ Waiting for Twilio SDK to load...');
                updateDeviceStatus('Loading SDK...', 'warning');
                await waitForTwilioSDK();
            }

            console.log('✅ Twilio SDK loaded successfully');

            // Fetch access token from backend using the stored identity
            const response = await fetch('/token?identity=' + agentIdentity);
            if (!response.ok) {
                throw new Error('Failed to fetch Twilio token');
            }

            const data = await response.json();
            console.log('Twilio token obtained for identity:', data.identity);

            // Pre-fill the Agent Connection field with the identity used for registration
            if (elements.agentIdField) {
                elements.agentIdField.value = 'client:' + agentIdentity;
                console.log('✅ Agent Connection field pre-populated with:', 'client:' + agentIdentity);
            }

            // Access Device from Twilio SDK v2 (Device is directly on Twilio object in v2.11.1)
            const Device = Twilio.Device;

            // Initialize Twilio Device (v2 API)
            twilioDevice = new Device(data.token, {
                logLevel: 1, // 1 = debug, 0 = trace
                codecPreferences: [Twilio.Call.Codec.Opus, Twilio.Call.Codec.PCMU]
            });

            // Device registered event (v2: 'ready' → 'registered')
            twilioDevice.on('registered', function() {
                console.log('✅ Twilio Device is ready to receive calls');
                updateDeviceStatus('Ready', 'success');
            });

            // Incoming call event (v2: connection → call)
            twilioDevice.on('incoming', function(call) {
                console.log('📞 Incoming call from:', call.parameters.From);
                currentConnection = call;

                // Show disconnect button, hide dial button
                if (elements.dialButton) {
                    elements.dialButton.classList.add('hidden');
                }
                if (elements.disconnectButton) {
                    elements.disconnectButton.classList.remove('hidden');
                }

                // Set up call event handlers BEFORE accepting
                call.on('accept', function() {
                    console.log('✅ Call accepted and connected');
                    updateDeviceStatus('Active Call', 'success');
                });

                call.on('disconnect', function() {
                    console.log('📴 Call ended');
                    currentConnection = null;
                    updateDeviceStatus('Ready', 'success');

                    // Hide disconnect button, show dial button
                    if (elements.disconnectButton) {
                        elements.disconnectButton.classList.add('hidden');
                    }
                    if (elements.dialButton) {
                        elements.dialButton.classList.remove('hidden');
                        elements.dialButton.disabled = false;
                        elements.dialButton.classList.remove('opacity-50', 'cursor-not-allowed');
                    }
                    if (elements.callStatus) {
                        elements.callStatus.classList.add('hidden');
                    }
                });

                call.on('error', function(error) {
                    console.error('❌ Call error:', error);
                    updateDeviceStatus('Call Error', 'error');
                });

                // Auto-accept the incoming call (agent initiated it via "Initiate Call" button)
                call.accept();
                updateDeviceStatus('Accepting...', 'warning');
            });

            // Error handling (v2: error event still exists)
            twilioDevice.on('error', function(error) {
                console.error('❌ Twilio Device error:', error);
                updateDeviceStatus('Error: ' + error.message, 'error');
            });

            // Register the device (v2: must explicitly register)
            await twilioDevice.register();
            console.log('Device registration initiated...');

        } catch (error) {
            console.error('Failed to initialize Twilio Client:', error);
            updateDeviceStatus('SDK Error', 'error');
        }
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    return {
        /**
         * Initialize the Twilio VOIP module
         * @param {Object} config - Configuration options
         * @param {HTMLElement} [config.dialButton] - Dial button element
         * @param {HTMLElement} [config.disconnectButton] - Disconnect button element
         * @param {HTMLElement} [config.callStatus] - Call status indicator element
         * @param {HTMLElement} [config.agentIdField] - Agent ID input field
         * @param {Function} [config.onStatusChange] - Callback for status changes
         * @returns {Promise<void>}
         */
        init: async function(config) {
            if (config) {
                elements.dialButton = config.dialButton || null;
                elements.disconnectButton = config.disconnectButton || null;
                elements.callStatus = config.callStatus || null;
                elements.agentIdField = config.agentIdField || null;
                onStatusChange = config.onStatusChange || null;
            }
            
            await initializeTwilioClient();
        },

        /**
         * Get the current CallSid
         * @returns {string|null} The CallSid of the current/last call
         */
        getCurrentCallSid: function() {
            return currentCallSid;
        },

        /**
         * Set the current CallSid (called after /dial response)
         * @param {string} sid - The CallSid from the dial response
         */
        setCurrentCallSid: function(sid) {
            currentCallSid = sid;
            console.log('TwilioVOIP: CallSid set to:', sid);
        },

        /**
         * Get the current connection/call object
         * @returns {Twilio.Call|null} The current Twilio Call object
         */
        getCurrentConnection: function() {
            return currentConnection;
        },

        /**
         * Get the Twilio Device instance
         * @returns {Twilio.Device|null} The Twilio Device instance
         */
        getDevice: function() {
            return twilioDevice;
        },

        /**
         * Disconnect the current call
         * @returns {boolean} True if a call was disconnected, false otherwise
         */
        disconnect: function() {
            if (currentConnection) {
                currentConnection.disconnect();
                console.log('📴 TwilioVOIP: User manually disconnected call');
                return true;
            }
            return false;
        },

        /**
         * Get the agent identity used for VOIP registration
         * @returns {string} The agent identity string
         */
        getAgentIdentity: function() {
            return agentIdentity;
        },

        /**
         * Check if the device is ready to make/receive calls
         * @returns {boolean} True if device is registered and ready
         */
        isReady: function() {
            return twilioDevice !== null && twilioDevice.state === 'registered';
        },

        /**
         * Check if there is an active call
         * @returns {boolean} True if there is an active connection
         */
        hasActiveCall: function() {
            return currentConnection !== null;
        },

        /**
         * Update the device status display (public wrapper)
         * @param {string} message - Status message
         * @param {string} type - Status type: 'success', 'warning', 'error'
         */
        updateStatus: function(message, type) {
            updateDeviceStatus(message, type);
        }
    };
})();

// Export for module systems (if available)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TwilioVOIP;
}