// Portfolio Website JavaScript
// Main interactivity and form handling

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    initSmoothScrolling();

    // Mobile menu toggle
    initMobileMenu();

    // Form validation
    initFormValidation();

    // Analytics tracking
    initAnalytics();

    // Scroll animations
    initScrollAnimations();
});

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');

            // Don't prevent default for links that just have # (like toggles)
            if (href === '#') {
                return;
            }

            e.preventDefault();
            const target = document.querySelector(href);

            if (target) {
                const headerOffset = 80; // Account for fixed nav
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Mobile menu toggle
function initMobileMenu() {
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!menuButton.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
}

// Form validation for contact forms
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            let isValid = true;
            const formData = new FormData(form);

            // Basic validation
            const email = formData.get('email');
            const name = formData.get('name');
            const message = formData.get('message');

            if (!name || name.trim() === '') {
                showError(form, 'name', 'Name is required');
                isValid = false;
            }

            if (!email || !isValidEmail(email)) {
                showError(form, 'email', 'Valid email is required');
                isValid = false;
            }

            if (!message || message.trim() === '') {
                showError(form, 'message', 'Message is required');
                isValid = false;
            }

            if (isValid) {
                // Form is valid, submit or process
                handleFormSubmit(form, formData);
            }
        });
    });
}

// Email validation helper
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Show form error
function showError(form, fieldName, message) {
    const field = form.querySelector(`[name="${fieldName}"]`);
    if (field) {
        // Remove existing error
        const existingError = field.parentElement.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-red-500 text-sm mt-1';
        errorDiv.textContent = message;
        field.parentElement.appendChild(errorDiv);

        // Add error styling to field
        field.classList.add('border-red-500');

        // Remove error on input
        field.addEventListener('input', function() {
            field.classList.remove('border-red-500');
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, { once: true });
    }
}

// Handle form submission
function handleFormSubmit(form, formData) {
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Sending...';
    submitButton.disabled = true;

    // In a real implementation, you'd send this to a backend
    // For now, we'll just simulate success
    setTimeout(() => {
        // Reset form
        form.reset();

        // Show success message
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4';
        successDiv.innerHTML = `
            <strong>Success!</strong> Your message has been sent. I'll respond within 24 hours.
        `;
        form.insertBefore(successDiv, form.firstChild);

        // Reset button
        submitButton.textContent = originalText;
        submitButton.disabled = false;

        // Remove success message after 5 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 5000);

        // Track conversion
        trackEvent('form_submission', {
            form_name: form.getAttribute('data-form-name') || 'contact'
        });
    }, 1500);
}

// Analytics tracking
function initAnalytics() {
    // Track page view
    trackPageView();

    // Track CTA clicks
    document.querySelectorAll('.btn-primary, .btn-secondary').forEach(button => {
        button.addEventListener('click', function(e) {
            const text = this.textContent.trim();
            const href = this.getAttribute('href');

            trackEvent('cta_click', {
                button_text: text,
                destination: href
            });
        });
    });

    // Track demo link clicks
    document.querySelectorAll('a[href*="streamlit.app"]').forEach(link => {
        link.addEventListener('click', function() {
            trackEvent('demo_click', {
                source: 'portfolio_website'
            });
        });
    });

    // Track service card interactions
    document.querySelectorAll('.service-card').forEach(card => {
        card.addEventListener('click', function() {
            const title = this.querySelector('h3')?.textContent || 'unknown';
            trackEvent('service_card_click', {
                service: title
            });
        });
    });
}

// Track page view
function trackPageView() {
    trackEvent('page_view', {
        page_title: document.title,
        page_path: window.location.pathname
    });
}

// Generic event tracking
function trackEvent(eventName, eventData) {
    // Google Analytics 4 (if available)
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, eventData);
    }

    // Console log for development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Analytics Event:', eventName, eventData);
    }
}

// Scroll animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements with animation class
    document.querySelectorAll('.card, .stat-box, .service-card').forEach(el => {
        observer.observe(el);
    });
}

// Utility: Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!');
        });
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!');
    }
}

// Show toast notification
function showToast(message, duration = 3000) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-gray-800 text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300';
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

// Scroll to top button
window.addEventListener('scroll', function() {
    const scrollTop = document.getElementById('scroll-top');
    if (scrollTop) {
        if (window.pageYOffset > 300) {
            scrollTop.classList.remove('hidden');
        } else {
            scrollTop.classList.add('hidden');
        }
    }
});

// Add scroll-to-top button dynamically
window.addEventListener('load', function() {
    const scrollTopBtn = document.createElement('button');
    scrollTopBtn.id = 'scroll-top';
    scrollTopBtn.className = 'fixed bottom-8 right-8 bg-purple-600 text-white p-3 rounded-full shadow-lg hover:bg-purple-700 transition hidden z-40';
    scrollTopBtn.innerHTML = `
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
        </svg>
    `;
    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.body.appendChild(scrollTopBtn);
});

// Performance tracking
window.addEventListener('load', function() {
    // Log page load time
    if (window.performance) {
        const perfData = window.performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;

        trackEvent('performance', {
            page_load_time: pageLoadTime,
            page_path: window.location.pathname
        });
    }
});
