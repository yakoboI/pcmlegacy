/**
 * Form Validation and Accessibility
 * Handles client-side form validation with proper ARIA attributes
 */

(function() {
    'use strict';

    // Password strength and match validation
    function initPasswordValidation() {
        const passwordInput = document.querySelector('input[name="password"]');
        const password2Input = document.querySelector('input[name="password2"]');
        const newPasswordInput = document.querySelector('input[name="new_password"]');
        const newPassword2Input = document.querySelector('input[name="new_password2"]');

        function checkPasswordMatch(input1, input2) {
            if (!input1 || !input2) return;
            
            function validate() {
                if (input2.value && input1.value !== input2.value) {
                    input2.setCustomValidity('Passwords do not match');
                    input2.setAttribute('aria-invalid', 'true');
                    const errorMsg = input2.parentElement.querySelector('.password-match-error');
                    if (!errorMsg) {
                        const error = document.createElement('span');
                        error.className = 'password-match-error form-error';
                        error.setAttribute('role', 'alert');
                        error.setAttribute('aria-live', 'polite');
                        error.textContent = 'Passwords do not match';
                        input2.parentElement.appendChild(error);
                    }
                } else {
                    input2.setCustomValidity('');
                    input2.setAttribute('aria-invalid', 'false');
                    const errorMsg = input2.parentElement.querySelector('.password-match-error');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            }

            input1.addEventListener('input', validate);
            input2.addEventListener('input', validate);
        }

        if (passwordInput && password2Input) {
            checkPasswordMatch(passwordInput, password2Input);
        }
        if (newPasswordInput && newPassword2Input) {
            checkPasswordMatch(newPasswordInput, newPassword2Input);
        }
    }

    // Add ARIA attributes to form fields
    function enhanceFormAccessibility() {
        // Add aria-required to required fields
        document.querySelectorAll('input[required], select[required], textarea[required]').forEach(function(field) {
            if (!field.hasAttribute('aria-required')) {
                field.setAttribute('aria-required', 'true');
            }
        });

        // Add aria-describedby for error messages
        document.querySelectorAll('.form-group').forEach(function(group) {
            const input = group.querySelector('input, select, textarea');
            const errorContainer = group.querySelector('.form-errors, .form-error');
            
            if (input && errorContainer) {
                const errorId = 'error-' + Math.random().toString(36).substr(2, 9);
                errorContainer.id = errorId;
                input.setAttribute('aria-describedby', errorId);
                input.setAttribute('aria-invalid', errorContainer.textContent.trim() !== '' ? 'true' : 'false');
            }
        });

        // Update aria-invalid on input
        document.querySelectorAll('input, select, textarea').forEach(function(field) {
            field.addEventListener('invalid', function() {
                this.setAttribute('aria-invalid', 'true');
            });
            field.addEventListener('input', function() {
                if (this.validity.valid) {
                    this.setAttribute('aria-invalid', 'false');
                }
            });
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initPasswordValidation();
            enhanceFormAccessibility();
        });
    } else {
        initPasswordValidation();
        enhanceFormAccessibility();
    }
})();

