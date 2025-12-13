/**
 * Global Error Handler
 * Provides error boundaries and better error handling
 */

(function() {
    'use strict';

    // Global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        
        // Show user-friendly error message
        const errorContainer = document.getElementById('error-container');
        if (!errorContainer) {
            const container = document.createElement('div');
            container.id = 'error-container';
            container.className = 'error-boundary';
            container.setAttribute('role', 'alert');
            container.setAttribute('aria-live', 'assertive');
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 1rem; border-radius: 0.5rem; z-index: 10000; max-width: 400px;';
            container.innerHTML = '<p><strong>An error occurred:</strong> ' + (event.message || 'Unknown error') + '</p><button onclick="this.parentElement.remove()" style="margin-top: 0.5rem; padding: 0.25rem 0.5rem;">Dismiss</button>';
            document.body.appendChild(container);
            
            // Auto-dismiss after 10 seconds
            setTimeout(function() {
                if (container.parentElement) {
                    container.remove();
                }
            }, 10000);
        }
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        
        // Prevent default browser error handling
        event.preventDefault();
        
        // Show user-friendly error message
        const errorContainer = document.getElementById('error-container');
        if (!errorContainer) {
            const container = document.createElement('div');
            container.id = 'error-container';
            container.className = 'error-boundary';
            container.setAttribute('role', 'alert');
            container.setAttribute('aria-live', 'assertive');
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 1rem; border-radius: 0.5rem; z-index: 10000; max-width: 400px;';
            const errorMsg = event.reason && event.reason.message ? event.reason.message : 'An unexpected error occurred';
            container.innerHTML = '<p><strong>Error:</strong> ' + errorMsg + '</p><button onclick="this.parentElement.remove()" style="margin-top: 0.5rem; padding: 0.25rem 0.5rem;">Dismiss</button>';
            document.body.appendChild(container);
            
            // Auto-dismiss after 10 seconds
            setTimeout(function() {
                if (container.parentElement) {
                    container.remove();
                }
            }, 10000);
        }
    });

    // Safe function wrapper for error boundaries
    window.safeExecute = function(fn, errorCallback) {
        try {
            return fn();
        } catch (error) {
            console.error('Error in safeExecute:', error);
            if (errorCallback) {
                errorCallback(error);
            }
            return null;
        }
    };

    // Safe async function wrapper
    window.safeAsync = async function(fn, errorCallback) {
        try {
            return await fn();
        } catch (error) {
            console.error('Error in safeAsync:', error);
            if (errorCallback) {
                errorCallback(error);
            }
            return null;
        }
    };
})();

