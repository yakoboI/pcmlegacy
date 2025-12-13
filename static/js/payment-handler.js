/**
 * Payment Handler - Safe DOM Manipulation
 * Replaces innerHTML with textContent for security
 */

(function() {
    'use strict';

    function safeUpdateElement(element, text, showSpinner) {
        if (!element) return;
        
        // Store original content if not already stored
        if (!element.dataset.originalText) {
            element.dataset.originalText = element.textContent;
        }
        
        if (showSpinner) {
            // Create spinner element safely
            const spinner = document.createElement('span');
            spinner.className = 'icon icon-spinner icon-sm icon-mr';
            spinner.setAttribute('aria-hidden', 'true');
            
            const textNode = document.createTextNode('Processing...');
            
            // Clear and add new content
            element.textContent = '';
            element.appendChild(spinner);
            element.appendChild(textNode);
        } else {
            // Restore original content
            element.textContent = element.dataset.originalText || '';
        }
    }

    function initPaymentButtons() {
        document.addEventListener('click', function(e) {
            const button = e.target.closest('[data-payment-button]');
            if (!button) return;
            
            const action = button.getAttribute('data-payment-action');
            const statusElement = document.getElementById('mpesaPayStatus');
            
            if (action === 'process') {
                safeUpdateElement(button, '', true);
                
                // Simulate payment processing (replace with actual payment logic)
                setTimeout(function() {
                    safeUpdateElement(button, '', false);
                    if (statusElement) {
                        statusElement.textContent = 'Payment processed successfully';
                        statusElement.setAttribute('role', 'alert');
                        statusElement.setAttribute('aria-live', 'polite');
                    }
                }, 2000);
            }
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPaymentButtons);
    } else {
        initPaymentButtons();
    }
})();

