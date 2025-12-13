document.addEventListener('DOMContentLoaded', function() {
    try {
        initMobileNavigation();
        initSearch();
        initLazyLoading();
        initPerformanceOptimizations();
        initFlashMessages();
    } catch (error) {
        console.error('Error initializing main functions:', error);
    }
});

function initMobileNavigation() {
    try {
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');
        
        if (!navToggle || !navMenu) {
            
            
            return;
        }
        
        
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.setAttribute('aria-controls', 'navMenu');
        navToggle.setAttribute('aria-label', 'Toggle navigation menu');
        navMenu.setAttribute('id', 'navMenu');
        
        function openMobileMenu() {
            navMenu.classList.add('active');
            navToggle.setAttribute('aria-expanded', 'true');
            
            
            document.body.style.overflow = 'hidden';
            
            
            const firstLink = navMenu.querySelector('a');
            if (firstLink) {
                setTimeout(() => firstLink.focus(), 100);
            }
        }
        
        function closeMobileMenu() {
            navMenu.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
            
            
            document.body.style.overflow = '';
            
            
            navToggle.focus();
        }
        
        
        navToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const isExpanded = navMenu.classList.contains('active');
            
            if (isExpanded) {
                closeMobileMenu();
            } else {
                openMobileMenu();
            }
        });
        
        
        document.addEventListener('click', function(event) {
            if (navMenu.classList.contains('active') && 
                !navToggle.contains(event.target) && 
                !navMenu.contains(event.target)) {
                closeMobileMenu();
            }
        });
        
        
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('active')) {
                closeMobileMenu();
            }
        });
        
        
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768 && navMenu.classList.contains('active')) {
                closeMobileMenu();
            }
        });
        
        
        navMenu.addEventListener('click', function(event) {
            if (event.target.tagName === 'A') {
                
                setTimeout(() => {
                    closeMobileMenu();
                }, 100);
            }
        });
    } catch (error) {
        console.error('Error in initMobileNavigation:', error);
    }
}

function initSearch() {
    try {
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
        document.addEventListener('keydown', function(event) {
            if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                event.preventDefault();
                searchInput.focus();
            }
        });
    }
    } catch (error) {
        console.error('Error in initSearch:', error);
    }
}

function initLazyLoading() {
    try {
        // Use IntersectionObserver if available, otherwise fallback to immediate loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            observer.unobserve(img);
                        }
                    }
                });
            }, {
                rootMargin: '50px' // Start loading images 50px before they come into view
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // Fallback for browsers without IntersectionObserver (polyfill or immediate load)
            document.querySelectorAll('img[data-src]').forEach(img => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                }
            });
        }
    } catch (error) {
        console.error('Error in initLazyLoading:', error);
        // Fallback: load all images immediately on error
        document.querySelectorAll('img[data-src]').forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
                img.classList.remove('lazy');
            }
        });
    }
}

function initPerformanceOptimizations() {
    try {
        preloadCriticalResources();
        optimizeScrollPerformance();
        initServiceWorker();
    } catch (error) {
        console.error('Error in initPerformanceOptimizations:', error);
    }
}

function initFlashMessages() {
    try {
        const flashMessages = document.querySelectorAll('.alert');
        flashMessages.forEach(alert => {
        
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => {
                    if (alert.parentElement) {
                        alert.parentElement.remove();
                    }
                }, 300);
            }
        }, 2000);
    });
    } catch (error) {
        console.error('Error in initFlashMessages:', error);
    }
}

function preloadCriticalResources() {
    // Only prefetch if user is authenticated (check for user session)
    // Skip prefetching protected routes to avoid unnecessary requests
    try {
        // Only prefetch public pages
        const publicPages = ['/subscriptions'];
        publicPages.forEach(page => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = page;
            document.head.appendChild(link);
        });
    } catch (error) {
        console.error('Error in preloadCriticalResources:', error);
    }
}

function optimizeScrollPerformance() {
    let ticking = false;
    
    function updateScrollPosition() {
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateScrollPosition);
            ticking = true;
        }
    });
}

function initServiceWorker() {
    // Check for service worker support with feature detection
    if ('serviceWorker' in navigator && window.browserCompatibility && window.browserCompatibility.hasServiceWorker) {
        window.addEventListener('load', function() {
            // Use Promise.resolve for better browser compatibility
            var registrationPromise = navigator.serviceWorker.register('/static/js/sw.js');
            
            if (registrationPromise && typeof registrationPromise.then === 'function') {
                registrationPromise
                    .then(function(registration) {
                        // Service worker registered successfully
                        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                            console.log('Service Worker registered:', registration);
                        }
                    })
                    .catch(function(error) {
                        // Silently handle registration failures
                        // This can happen when tracking prevention blocks storage access
                        // The app will still function normally without service worker caching
                        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                            console.warn('Service Worker registration failed:', error);
                        }
                    });
            }
        });
    }
}

function showNotification(message, type = 'info') {
    try {
        
        if (!document.body) {
            console.warn('Document body not available for notification');
            return;
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#2563eb'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification && notification.style) {
                notification.style.transform = 'translateX(0)';
            }
        }, 100);
        
        setTimeout(() => {
            if (notification && notification.style) {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (notification && notification.parentElement) {
                        document.body.removeChild(notification);
                    }
                }, 300);
            }
        }, 3000);
    } catch (error) {
        console.error('Error showing notification:', error);
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateCardNumber(cardNumber) {
    const cleaned = cardNumber.replace(/\s/g, '');
    return /^\d{13,19}$/.test(cleaned);
}

function validateExpiryDate(expiryDate) {
    const re = /^(0[1-9]|1[0-2])\/\d{2}$/;
    if (!re.test(expiryDate)) return false;
    
    const [month, year] = expiryDate.split('/');
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear() % 100;
    const currentMonth = currentDate.getMonth() + 1;
    
    if (parseInt(year) < currentYear) return false;
    if (parseInt(year) === currentYear && parseInt(month) < currentMonth) return false;
    
    return true;
}

function validateCVV(cvv) {
    return /^\d{3,4}$/.test(cvv);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

function handleMaterialAction(action, materialId, quantity = 1) {
    switch (action) {
        case 'download':
            return downloadMaterial(materialId);
        default:
            throw new Error(`Unknown action: ${action}`);
    }
}

function downloadMaterial(materialId) {
    window.location.href = `/download/${materialId}`;
    return Promise.resolve({ success: true });
}

window.handleMaterialAction = handleMaterialAction;
window.showNotification = showNotification;
