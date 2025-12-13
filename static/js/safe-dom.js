/**
 * Safe DOM Manipulation Utilities
 * Provides safe alternatives to innerHTML
 */

(function() {
    'use strict';

    window.safeDOM = {
        /**
         * Safely set HTML content using textContent for simple cases
         * or createElement for complex HTML
         */
        setText: function(element, text) {
            if (!element) return;
            element.textContent = text || '';
        },

        /**
         * Safely create and append elements
         */
        createElement: function(tag, attributes, text) {
            const element = document.createElement(tag);
            
            if (attributes) {
                Object.keys(attributes).forEach(function(key) {
                    if (key === 'className') {
                        element.className = attributes[key];
                    } else if (key === 'classList') {
                        attributes[key].forEach(function(cls) {
                            element.classList.add(cls);
                        });
                    } else {
                        element.setAttribute(key, attributes[key]);
                    }
                });
            }
            
            if (text) {
                element.textContent = text;
            }
            
            return element;
        },

        /**
         * Safely append child elements
         */
        appendChild: function(parent, child) {
            if (parent && child) {
                parent.appendChild(child);
            }
        },

        /**
         * Safely clear element content
         */
        clear: function(element) {
            if (!element) return;
            while (element.firstChild) {
                element.removeChild(element.firstChild);
            }
        },

        /**
         * Safely set error message
         */
        setError: function(element, message, linkUrl, linkText) {
            if (!element) return;
            
            this.clear(element);
            
            const errorDiv = this.createElement('div', { className: 'error-message' });
            const errorP = this.createElement('p', null, message);
            this.appendChild(errorDiv, errorP);
            
            if (linkUrl && linkText) {
                const link = this.createElement('a', { 
                    href: linkUrl,
                    className: 'btn btn-success'
                }, linkText);
                this.appendChild(errorDiv, link);
            }
            
            this.appendChild(element, errorDiv);
        }
    };
})();

