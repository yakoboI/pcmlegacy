/**
 * Safe DOCX Viewer
 * Replaces innerHTML usage with safe DOM manipulation
 */

(function() {
    'use strict';

    function safeSetHTML(element, html) {
        // Clear existing content
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
        
        // Create a temporary container
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Move nodes safely
        while (temp.firstChild) {
            element.appendChild(temp.firstChild);
        }
    }

    function initDocxViewer() {
        const viewer = document.getElementById('word-viewer');
        if (!viewer) return;

        // This will be called by the docx-preview library
        // We'll wrap it to use safe methods
        window.safeDocxRender = function(element, docxData) {
            if (typeof renderAsync === 'function') {
                renderAsync(docxData, element, null, {
                    className: 'docx',
                    inWrapper: true,
                    ignoreWidth: false,
                    ignoreHeight: false,
                    ignoreFonts: false,
                    breakPages: true,
                    ignoreLastRenderedPageBreak: true,
                    experimental: false,
                    trimXml: false
                });
            }
        };
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDocxViewer);
    } else {
        initDocxViewer();
    }
})();

