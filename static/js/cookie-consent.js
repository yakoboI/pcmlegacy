/**
 * Cookie Consent Management
 * GDPR/CCPA Compliant Cookie Consent Handler
 */

(function() {
    'use strict';

    const COOKIE_CONSENT_KEY = 'cookie_consent';
    const COOKIE_CONSENT_VERSION = '1.0';
    const CONSENT_EXPIRY_DAYS = 365;

    // Cookie categories
    const COOKIE_CATEGORIES = {
        essential: 'essential',
        analytics: 'analytics',
        functional: 'functional',
        marketing: 'marketing'
    };

    /**
     * Get cookie consent preferences from localStorage
     */
    function getCookieConsent() {
        try {
            const stored = localStorage.getItem(COOKIE_CONSENT_KEY);
            if (stored) {
                const consent = JSON.parse(stored);
                // Check if consent is still valid (not expired)
                if (consent.version === COOKIE_CONSENT_VERSION && consent.timestamp) {
                    const consentDate = new Date(consent.timestamp);
                    const expiryDate = new Date(consentDate);
                    expiryDate.setDate(expiryDate.getDate() + CONSENT_EXPIRY_DAYS);
                    
                    if (new Date() < expiryDate) {
                        return consent;
                    }
                }
            }
        } catch (e) {
            console.warn('Error reading cookie consent:', e);
        }
        return null;
    }

    /**
     * Save cookie consent preferences to localStorage
     */
    function saveCookieConsent(preferences) {
        try {
            const consent = {
                version: COOKIE_CONSENT_VERSION,
                timestamp: new Date().toISOString(),
                preferences: preferences
            };
            localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(consent));
            return true;
        } catch (e) {
            console.error('Error saving cookie consent:', e);
            return false;
        }
    }

    /**
     * Check if user has given consent
     */
    function hasConsent() {
        const consent = getCookieConsent();
        return consent !== null && consent.preferences && consent.preferences.accepted;
    }

    /**
     * Check if specific category is allowed
     */
    function isCategoryAllowed(category) {
        const consent = getCookieConsent();
        if (!consent || !consent.preferences) {
            return false;
        }
        
        // Essential cookies are always allowed
        if (category === COOKIE_CATEGORIES.essential) {
            return true;
        }
        
        return consent.preferences.categories && consent.preferences.categories[category] === true;
    }

    /**
     * Accept all cookies
     */
    function acceptAll() {
        const preferences = {
            accepted: true,
            categories: {
                essential: true,
                analytics: true,
                functional: true,
                marketing: true
            }
        };
        
        if (saveCookieConsent(preferences)) {
            hideBanner();
            loadAllowedScripts();
            showNotification('Cookie preferences saved. Thank you!', 'success');
        }
    }

    /**
     * Decline non-essential cookies
     */
    function declineNonEssential() {
        const preferences = {
            accepted: true,
            categories: {
                essential: true,
                analytics: false,
                functional: false,
                marketing: false
            }
        };
        
        if (saveCookieConsent(preferences)) {
            hideBanner();
            loadAllowedScripts();
            showNotification('Cookie preferences saved. Only essential cookies will be used.', 'success');
        }
    }

    /**
     * Save custom preferences
     */
    function savePreferences() {
        const preferences = {
            accepted: true,
            categories: {
                essential: true, // Always true
                analytics: document.getElementById('cookie-analytics').checked,
                functional: document.getElementById('cookie-functional').checked,
                marketing: document.getElementById('cookie-marketing').checked
            }
        };
        
        if (saveCookieConsent(preferences)) {
            hideModal();
            loadAllowedScripts();
            showNotification('Cookie preferences saved successfully!', 'success');
        }
    }

    /**
     * Show cookie consent banner
     */
    function showBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.style.display = 'block';
            // Focus management for accessibility
            setTimeout(function() {
                const acceptBtn = document.getElementById('cookie-consent-accept');
                if (acceptBtn) {
                    acceptBtn.focus();
                }
            }, 100);
        }
    }

    /**
     * Hide cookie consent banner
     */
    function hideBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }

    /**
     * Show preferences modal
     */
    function showModal() {
        const modal = document.getElementById('cookie-preferences-modal');
        const consent = getCookieConsent();
        
        if (modal) {
            // Set current preferences
            if (consent && consent.preferences && consent.preferences.categories) {
                document.getElementById('cookie-analytics').checked = consent.preferences.categories.analytics || false;
                document.getElementById('cookie-functional').checked = consent.preferences.categories.functional || false;
                document.getElementById('cookie-marketing').checked = consent.preferences.categories.marketing || false;
            } else {
                // Default: all unchecked except essential
                document.getElementById('cookie-analytics').checked = false;
                document.getElementById('cookie-functional').checked = false;
                document.getElementById('cookie-marketing').checked = false;
            }
            
            modal.style.display = 'flex';
            // Focus management
            const closeBtn = document.getElementById('cookie-preferences-close');
            if (closeBtn) {
                closeBtn.focus();
            }
        }
    }

    /**
     * Hide preferences modal
     */
    function hideModal() {
        const modal = document.getElementById('cookie-preferences-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Load scripts based on consent
     */
    function loadAllowedScripts() {
        const consent = getCookieConsent();
        if (!consent || !consent.preferences) {
            return;
        }

        // Load analytics scripts if allowed
        if (isCategoryAllowed(COOKIE_CATEGORIES.analytics)) {
            // Add analytics scripts here if needed
            // Example: Google Analytics, etc.
        }

        // Load marketing scripts if allowed
        if (isCategoryAllowed(COOKIE_CATEGORIES.marketing)) {
            // Add marketing scripts here if needed
        }
    }

    /**
     * Show notification
     */
    function showNotification(message, type) {
        // Use existing notification system if available
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = `cookie-notification cookie-notification-${type}`;
            notification.textContent = message;
            notification.setAttribute('role', 'alert');
            notification.setAttribute('aria-live', 'polite');
            document.body.appendChild(notification);
            
            setTimeout(function() {
                notification.style.opacity = '0';
                setTimeout(function() {
                    if (notification.parentElement) {
                        notification.parentElement.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
    }

    /**
     * Initialize cookie consent
     */
    function initCookieConsent() {
        // Check if consent already given
        if (hasConsent()) {
            loadAllowedScripts();
            return;
        }

        // Show banner if consent not given
        showBanner();

        // Event listeners
        const acceptBtn = document.getElementById('cookie-consent-accept');
        const declineBtn = document.getElementById('cookie-consent-decline');
        const preferencesBtn = document.getElementById('cookie-consent-preferences');
        const modalCloseBtn = document.getElementById('cookie-preferences-close');
        const saveBtn = document.getElementById('cookie-preferences-save');
        const acceptAllBtn = document.getElementById('cookie-preferences-accept-all');

        if (acceptBtn) {
            acceptBtn.addEventListener('click', acceptAll);
        }

        if (declineBtn) {
            declineBtn.addEventListener('click', declineNonEssential);
        }

        if (preferencesBtn) {
            preferencesBtn.addEventListener('click', showModal);
        }

        if (modalCloseBtn) {
            modalCloseBtn.addEventListener('click', hideModal);
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', savePreferences);
        }

        if (acceptAllBtn) {
            acceptAllBtn.addEventListener('click', function() {
                acceptAll();
                hideModal();
            });
        }

        // Close modal on backdrop click
        const modal = document.getElementById('cookie-preferences-modal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    hideModal();
                }
            });
        }

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const modal = document.getElementById('cookie-preferences-modal');
                if (modal && modal.style.display === 'flex') {
                    hideModal();
                }
            }
        });
    }

    // Export functions for external use
    window.cookieConsent = {
        hasConsent: hasConsent,
        isCategoryAllowed: isCategoryAllowed,
        showPreferences: showModal,
        getConsent: getCookieConsent,
        saveCookieConsent: saveCookieConsent,
        acceptAll: acceptAll
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCookieConsent);
    } else {
        initCookieConsent();
    }
})();

