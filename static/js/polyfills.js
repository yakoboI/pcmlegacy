/**
 * Browser Compatibility Polyfills
 * Ensures the application works across Chrome, Edge, Firefox, Safari, and older browsers
 */

(function() {
    'use strict';

    // Polyfill for IntersectionObserver (for lazy loading images)
    if (!window.IntersectionObserver) {
        window.IntersectionObserver = function(callback, options) {
            this.callback = callback;
            this.options = options || {};
            this.elements = [];
            
            this.observe = function(element) {
                this.elements.push(element);
                this.check();
            };
            
            this.unobserve = function(element) {
                this.elements = this.elements.filter(function(el) {
                    return el !== element;
                });
            };
            
            this.disconnect = function() {
                this.elements = [];
            };
            
            this.check = function() {
                var self = this;
                this.elements.forEach(function(element) {
                    var rect = element.getBoundingClientRect();
                    var isIntersecting = (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                    );
                    
                    if (isIntersecting) {
                        self.callback([{
                            target: element,
                            isIntersecting: true,
                            intersectionRatio: 1
                        }], self);
                    }
                });
            };
            
            // Check on scroll and resize
            var self = this;
            window.addEventListener('scroll', function() {
                self.check();
            });
            window.addEventListener('resize', function() {
                self.check();
            });
            
            // Initial check
            setTimeout(function() {
                self.check();
            }, 100);
        };
    }

    // Polyfill for Promise (for older browsers)
    if (!window.Promise) {
        window.Promise = function(executor) {
            var self = this;
            this.state = 'pending';
            this.value = undefined;
            this.handlers = [];
            
            function resolve(result) {
                if (self.state === 'pending') {
                    self.state = 'fulfilled';
                    self.value = result;
                    self.handlers.forEach(handle);
                }
            }
            
            function reject(error) {
                if (self.state === 'pending') {
                    self.state = 'rejected';
                    self.value = error;
                    self.handlers.forEach(handle);
                }
            }
            
            function handle(handler) {
                if (self.state === 'pending') {
                    self.handlers.push(handler);
                } else {
                    if (self.state === 'fulfilled' && typeof handler.onFulfilled === 'function') {
                        handler.onFulfilled(self.value);
                    }
                    if (self.state === 'rejected' && typeof handler.onRejected === 'function') {
                        handler.onRejected(self.value);
                    }
                }
            }
            
            this.then = function(onFulfilled, onRejected) {
                return new Promise(function(resolve, reject) {
                    handle({
                        onFulfilled: function(result) {
                            try {
                                resolve(onFulfilled ? onFulfilled(result) : result);
                            } catch (ex) {
                                reject(ex);
                            }
                        },
                        onRejected: function(error) {
                            try {
                                resolve(onRejected ? onRejected(error) : error);
                            } catch (ex) {
                                reject(ex);
                            }
                        }
                    });
                });
            };
            
            this.catch = function(onRejected) {
                return this.then(null, onRejected);
            };
            
            try {
                executor(resolve, reject);
            } catch (ex) {
                reject(ex);
            }
        };
        
        Promise.resolve = function(value) {
            return new Promise(function(resolve) {
                resolve(value);
            });
        };
        
        Promise.reject = function(reason) {
            return new Promise(function(resolve, reject) {
                reject(reason);
            });
        };
        
        Promise.all = function(promises) {
            return new Promise(function(resolve, reject) {
                var results = [];
                var completed = 0;
                
                if (promises.length === 0) {
                    resolve(results);
                    return;
                }
                
                promises.forEach(function(promise, index) {
                    Promise.resolve(promise).then(function(result) {
                        results[index] = result;
                        completed++;
                        if (completed === promises.length) {
                            resolve(results);
                        }
                    }, reject);
                });
            });
        };
    }

    // Polyfill for Array.from (for older browsers)
    if (!Array.from) {
        Array.from = function(arrayLike, mapFn, thisArg) {
            var C = this;
            var items = Object(arrayLike);
            if (arrayLike == null) {
                throw new TypeError('Array.from requires an array-like object - not null or undefined');
            }
            var mapFunction = mapFn === undefined ? undefined : mapFn;
            var T;
            if (typeof mapFunction !== 'undefined') {
                if (typeof mapFunction !== 'function') {
                    throw new TypeError('Array.from: when provided, the second argument must be a function');
                }
                if (arguments.length > 2) {
                    T = thisArg;
                }
            }
            var len = parseInt(items.length, 10) || 0;
            var A = typeof C === 'function' ? Object(new C(len)) : new Array(len);
            var k = 0;
            var kValue;
            while (k < len) {
                kValue = items[k];
                if (mapFunction) {
                    A[k] = typeof T === 'undefined' ? mapFunction(kValue, k) : mapFunction.call(T, kValue, k);
                } else {
                    A[k] = kValue;
                }
                k += 1;
            }
            A.length = len;
            return A;
        };
    }

    // Polyfill for Object.assign (for older browsers)
    if (!Object.assign) {
        Object.assign = function(target) {
            if (target == null) {
                throw new TypeError('Cannot convert undefined or null to object');
            }
            var to = Object(target);
            for (var index = 1; index < arguments.length; index++) {
                var nextSource = arguments[index];
                if (nextSource != null) {
                    for (var nextKey in nextSource) {
                        if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                            to[nextKey] = nextSource[nextKey];
                        }
                    }
                }
            }
            return to;
        };
    }

    // Polyfill for String.includes (for older browsers)
    if (!String.prototype.includes) {
        String.prototype.includes = function(search, start) {
            if (typeof start !== 'number') {
                start = 0;
            }
            if (start + search.length > this.length) {
                return false;
            } else {
                return this.indexOf(search, start) !== -1;
            }
        };
    }

    // Polyfill for Array.includes (for older browsers)
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            if (this == null) {
                throw new TypeError('"this" is null or not defined');
            }
            var o = Object(this);
            var len = parseInt(o.length, 10) || 0;
            if (len === 0) {
                return false;
            }
            var n = parseInt(fromIndex, 10) || 0;
            var k = n >= 0 ? n : Math.max(len + n, 0);
            function sameValueZero(x, y) {
                return x === y || (typeof x === 'number' && typeof y === 'number' && isNaN(x) && isNaN(y));
            }
            for (; k < len; k++) {
                if (sameValueZero(o[k], searchElement)) {
                    return true;
                }
            }
            return false;
        };
    }

    // Polyfill for Element.closest (for older browsers)
    if (!Element.prototype.closest) {
        Element.prototype.closest = function(selector) {
            var element = this;
            while (element && element.nodeType === 1) {
                if (element.matches(selector)) {
                    return element;
                }
                element = element.parentElement;
            }
            return null;
        };
    }

    // Polyfill for Element.matches (for older browsers)
    if (!Element.prototype.matches) {
        Element.prototype.matches = 
            Element.prototype.matchesSelector ||
            Element.prototype.mozMatchesSelector ||
            Element.prototype.msMatchesSelector ||
            Element.prototype.oMatchesSelector ||
            Element.prototype.webkitMatchesSelector ||
            function(selector) {
                var matches = (this.document || this.ownerDocument).querySelectorAll(selector);
                var i = matches.length;
                while (--i >= 0 && matches.item(i) !== this) {}
                return i > -1;
            };
    }

    // Polyfill for requestAnimationFrame (for older browsers)
    if (!window.requestAnimationFrame) {
        window.requestAnimationFrame = function(callback) {
            return window.setTimeout(function() {
                callback(Date.now());
            }, 1000 / 60);
        };
    }

    if (!window.cancelAnimationFrame) {
        window.cancelAnimationFrame = function(id) {
            clearTimeout(id);
        };
    }

    // Feature detection and graceful degradation
    window.browserCompatibility = {
        hasServiceWorker: 'serviceWorker' in navigator,
        hasCacheAPI: 'caches' in window,
        hasIntersectionObserver: 'IntersectionObserver' in window,
        hasFetch: 'fetch' in window,
        hasPromise: 'Promise' in window,
        hasLocalStorage: (function() {
            try {
                var test = '__localStorage_test__';
                localStorage.setItem(test, test);
                localStorage.removeItem(test);
                return true;
            } catch (e) {
                return false;
            }
        })(),
        hasSessionStorage: (function() {
            try {
                var test = '__sessionStorage_test__';
                sessionStorage.setItem(test, test);
                sessionStorage.removeItem(test);
                return true;
            } catch (e) {
                return false;
            }
        })()
    };

    // Log browser compatibility info in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Browser Compatibility:', window.browserCompatibility);
    }
})();

