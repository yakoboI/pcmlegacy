/**
 * Loading States Manager
 * Provides visual feedback during async operations
 */

(function() {
    'use strict';

    const LoadingStates = {
        /**
         * Show loading spinner
         */
        showSpinner: function(message) {
            const spinner = document.getElementById('loading-spinner');
            const text = document.getElementById('loading-text');
            
            if (spinner) {
                if (text && message) {
                    text.textContent = message;
                }
                spinner.style.display = 'block';
                spinner.setAttribute('aria-busy', 'true');
            }
        },

        /**
         * Hide loading spinner
         */
        hideSpinner: function() {
            const spinner = document.getElementById('loading-spinner');
            if (spinner) {
                spinner.style.display = 'none';
                spinner.setAttribute('aria-busy', 'false');
            }
        },

        /**
         * Show loading overlay (full page)
         */
        showOverlay: function(message) {
            const overlay = document.getElementById('loading-overlay');
            const text = document.getElementById('loading-overlay-text');
            
            if (overlay) {
                if (text && message) {
                    text.textContent = message;
                }
                overlay.style.display = 'flex';
                overlay.setAttribute('aria-busy', 'true');
                // Prevent body scroll
                document.body.style.overflow = 'hidden';
            }
        },

        /**
         * Hide loading overlay
         */
        hideOverlay: function() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.style.display = 'none';
                overlay.setAttribute('aria-busy', 'false');
                // Restore body scroll
                document.body.style.overflow = '';
            }
        },

        /**
         * Show inline loading indicator
         */
        showInline: function(elementId, message) {
            const inline = document.getElementById('loading-inline');
            if (inline) {
                const text = inline.querySelector('.loading-text-small');
                if (text && message) {
                    text.textContent = message;
                }
                inline.style.display = 'inline-flex';
            }
        },

        /**
         * Hide inline loading indicator
         */
        hideInline: function() {
            const inline = document.getElementById('loading-inline');
            if (inline) {
                inline.style.display = 'none';
            }
        },

        /**
         * Set button loading state
         */
        setButtonLoading: function(button, loading) {
            if (!button) return;
            
            if (loading) {
                button.classList.add('loading');
                button.disabled = true;
                button.setAttribute('aria-busy', 'true');
                // Store original text
                if (!button.dataset.originalText) {
                    button.dataset.originalText = button.textContent;
                }
            } else {
                button.classList.remove('loading');
                button.disabled = false;
                button.removeAttribute('aria-busy');
                // Restore original text
                if (button.dataset.originalText) {
                    button.textContent = button.dataset.originalText;
                }
            }
        },

        /**
         * Set form loading state
         */
        setFormLoading: function(form, loading) {
            if (!form) return;
            
            if (loading) {
                form.classList.add('form-loading');
                const inputs = form.querySelectorAll('input, button, select, textarea');
                inputs.forEach(input => {
                    input.disabled = true;
                });
            } else {
                form.classList.remove('form-loading');
                const inputs = form.querySelectorAll('input, button, select, textarea');
                inputs.forEach(input => {
                    input.disabled = false;
                });
            }
        },

        /**
         * Set table loading state
         */
        setTableLoading: function(table, loading) {
            if (!table) return;
            
            if (loading) {
                table.classList.add('table-loading');
            } else {
                table.classList.remove('table-loading');
            }
        },

        /**
         * Set card loading state
         */
        setCardLoading: function(card, loading) {
            if (!card) return;
            
            if (loading) {
                card.classList.add('card-loading');
            } else {
                card.classList.remove('card-loading');
            }
        }
    };

    // Auto-enhance forms with loading states
    function enhanceForms() {
        const forms = document.querySelectorAll('form[data-loading]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const loadingType = form.dataset.loading || 'form';
                
                if (loadingType === 'overlay') {
                    LoadingStates.showOverlay('Processing your request...');
                } else if (loadingType === 'spinner') {
                    LoadingStates.showSpinner('Processing your request...');
                } else {
                    LoadingStates.setFormLoading(form, true);
                }
                
                // Hide loading after form submission (will be handled by page reload or AJAX)
                // For AJAX forms, loading should be hidden in the success/error handlers
            });
        });
    }

    // Auto-enhance buttons with loading states
    function enhanceButtons() {
        const buttons = document.querySelectorAll('button[data-loading], a[data-loading]');
        buttons.forEach(button => {
            button.addEventListener('click', function(e) {
                const loadingType = button.dataset.loading || 'button';
                
                if (loadingType === 'overlay') {
                    LoadingStates.showOverlay('Processing...');
                } else if (loadingType === 'spinner') {
                    LoadingStates.showSpinner('Processing...');
                } else {
                    LoadingStates.setButtonLoading(button, true);
                }
            });
        });
    }

    // Enhance AJAX requests
    function enhanceAjaxRequests() {
        // Intercept fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            const options = args[1] || {};
            
            // Show loading if not explicitly disabled
            if (!options.noLoading) {
                LoadingStates.showSpinner('Loading...');
            }
            
            return originalFetch.apply(this, args)
                .then(response => {
                    if (!options.noLoading) {
                        LoadingStates.hideSpinner();
                    }
                    return response;
                })
                .catch(error => {
                    if (!options.noLoading) {
                        LoadingStates.hideSpinner();
                    }
                    throw error;
                });
        };
    }

    // Initialize on DOM ready
    function init() {
        enhanceForms();
        enhanceButtons();
        // Optionally enhance AJAX requests
        // enhanceAjaxRequests();
    }

    // Export to global scope
    window.LoadingStates = LoadingStates;

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

