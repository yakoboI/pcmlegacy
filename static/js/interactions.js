/**
 * Safe Interaction Handlers
 * Replaces inline onclick handlers with event listeners to prevent XSS
 */

(function() {
    'use strict';

    // Material Card Click Handler
    function initMaterialCards() {
        document.addEventListener('click', function(e) {
            const card = e.target.closest('.material-card[data-material-url]');
            if (card && !e.target.closest('a, button')) {
                const url = card.getAttribute('data-material-url');
                if (url) {
                    window.location.href = url;
                }
            }
        });
    }

    // Category Card Click Handler
    function initCategoryCards() {
        document.addEventListener('click', function(e) {
            const card = e.target.closest('.category-card[data-category-url]');
            if (card) {
                const url = card.getAttribute('data-category-url');
                if (url) {
                    window.location.href = url;
                }
            }
        });
    }

    // Stop Propagation Handler (replaces onclick="event.stopPropagation()")
    function initStopPropagation() {
        document.addEventListener('click', function(e) {
            if (e.target.hasAttribute('data-stop-propagation') || 
                e.target.closest('[data-stop-propagation]')) {
                e.stopPropagation();
            }
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initMaterialCards();
            initCategoryCards();
            initStopPropagation();
        });
    } else {
        initMaterialCards();
        initCategoryCards();
        initStopPropagation();
    }
})();

