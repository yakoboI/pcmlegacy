/**
 * Dashboard Tabs Handler
 * Handles tab switching for user dashboard
 */

(function() {
    'use strict';

    function initDashboardTabs() {
        const tabs = document.querySelectorAll('[data-tab]');
        const tabContents = document.querySelectorAll('.tab-content');

        tabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                
                // Update ARIA attributes
                tabs.forEach(function(t) {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                
                tabContents.forEach(function(content) {
                    content.classList.remove('active');
                });
                
                // Activate selected tab
                this.classList.add('active');
                this.setAttribute('aria-selected', 'true');
                
                const selectedContent = document.getElementById(tabName + '-tab');
                if (selectedContent) {
                    selectedContent.classList.add('active');
                }
            });
        });

        // Refresh downloads handler
        const refreshBtn = document.querySelector('[data-action="refresh-downloads"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                location.reload();
            });
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDashboardTabs);
    } else {
        initDashboardTabs();
    }
})();

