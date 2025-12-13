/**
 * Accessibility Enhancements
 * Handles skip navigation, focus management, and ARIA updates
 */

(function() {
    'use strict';

    // Skip Navigation Link Handler
    function initSkipNavigation() {
        const skipLink = document.querySelector('.skip-nav-link');
        if (skipLink) {
            skipLink.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector('#main-content');
                if (target) {
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    // Remove tabindex after focus to restore normal tab order
                    setTimeout(function() {
                        target.removeAttribute('tabindex');
                    }, 1000);
                }
            });
        }
    }

    // Close Alert Button Handler (replaces onclick)
    function initAlertDismiss() {
        document.addEventListener('click', function(e) {
            if (e.target.matches('.btn-close[data-dismiss="alert"]') || 
                e.target.closest('.btn-close[data-dismiss="alert"]')) {
                const button = e.target.matches('.btn-close') ? e.target : e.target.closest('.btn-close');
                const alert = button.closest('.alert');
                if (alert) {
                    alert.style.transition = 'opacity 0.3s ease';
                    alert.style.opacity = '0';
                    setTimeout(function() {
                        if (alert.parentElement) {
                            alert.parentElement.removeChild(alert);
                        }
                    }, 300);
                }
            }
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initSkipNavigation();
            initAlertDismiss();
        });
    } else {
        initSkipNavigation();
        initAlertDismiss();
    }
})();

