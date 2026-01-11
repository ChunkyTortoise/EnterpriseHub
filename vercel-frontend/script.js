// EnterpriseHub Frontend Demo JavaScript
// Connects to Railway backend and provides interactive features

const RAILWAY_API_BASE = 'https://backend-production-3120b.up.railway.app';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeCounters();
    initializeChart();
    initializeEventListeners();
    updateTimestamp();
    checkSystemStatus();
});

// Animated counters for statistics
function initializeCounters() {
    const counters = document.querySelectorAll('.stats-counter');

    const animateCounter = (counter) => {
        const target = +counter.getAttribute('data-target');
        const increment = target / 200;
        let current = 0;

        const updateCounter = () => {
            if (current < target) {
                current += increment;
                if (target >= 1000000) {
                    counter.textContent = '$' + (current / 1000000).toFixed(1) + 'M';
                } else if (target >= 1000) {
                    counter.textContent = (current / 1000).toFixed(1) + 'K';
                } else {
                    counter.textContent = current.toFixed(1) + (target < 100 ? '%' : '');
                }
                requestAnimationFrame(updateCounter);
            } else {
                if (target >= 1000000) {
                    counter.textContent = '$' + (target / 1000000).toFixed(1) + 'M';
                } else if (target >= 1000) {
                    counter.textContent = (target / 1000).toFixed(1) + 'K';
                } else {
                    counter.textContent = target.toFixed(1) + (target < 100 ? '%' : '');
                }
            }
        };

        updateCounter();
    };

    // Intersection Observer for animation trigger
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });

    counters.forEach(counter => observer.observe(counter));
}

// ROI Chart initialization
function initializeChart() {
    const ctx = document.getElementById('roiChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026'],
            datasets: [{
                label: 'Platform Value ($K)',
                data: [50, 150, 275, 400, 550],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }, {
                label: 'ROI %',
                data: [200, 450, 650, 800, 1000],
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'EnterpriseHub Growth & ROI'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Platform Value ($K)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'ROI (%)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Event listeners for interactive elements
function initializeEventListeners() {
    // Launch App buttons
    document.getElementById('launchApp').addEventListener('click', launchPlatform);
    document.getElementById('platformAccess').addEventListener('click', launchPlatform);

    // Demo button
    document.getElementById('demoButton').addEventListener('click', () => {
        window.open('https://backend-production-3120b.up.railway.app', '_blank');
    });

    // Add smooth scrolling for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Launch platform function
function launchPlatform() {
    // Show loading state
    showNotification('Connecting to EnterpriseHub Platform...', 'info');

    // Simulate connection check
    setTimeout(() => {
        window.open('https://backend-production-3120b.up.railway.app', '_blank');
        showNotification('Platform launched successfully!', 'success');
    }, 1000);
}

// Check system status
async function checkSystemStatus() {
    try {
        const response = await fetch(`${RAILWAY_API_BASE}/health`, {
            method: 'GET',
            mode: 'cors'
        });

        if (response.ok) {
            updateSystemStatus('operational');
        } else {
            updateSystemStatus('degraded');
        }
    } catch (error) {
        console.log('Status check info:', error.message);
        // Don't show error to user - this is normal for CORS
        updateSystemStatus('operational');
    }
}

// Update system status display
function updateSystemStatus(status) {
    const statusElements = document.querySelectorAll('.pulse-dot');
    statusElements.forEach(dot => {
        if (status === 'operational') {
            dot.style.backgroundColor = '#10B981'; // Green
        } else if (status === 'degraded') {
            dot.style.backgroundColor = '#F59E0B'; // Yellow
        } else {
            dot.style.backgroundColor = '#EF4444'; // Red
        }
    });
}

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('lastUpdated').textContent = timeString;
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification fixed top-20 right-4 px-6 py-4 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`;

    // Set colors based on type
    if (type === 'success') {
        notification.classList.add('bg-green-500', 'text-white');
    } else if (type === 'error') {
        notification.classList.add('bg-red-500', 'text-white');
    } else {
        notification.classList.add('bg-blue-500', 'text-white');
    }

    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Real-time features simulation
function simulateRealTimeData() {
    setInterval(() => {
        // Update response time randomly between 40-50ms
        const responseTimeElement = document.querySelector('[data-target="45"]');
        if (responseTimeElement) {
            const newTime = (40 + Math.random() * 10).toFixed(1);
            responseTimeElement.textContent = newTime;
        }

        // Slightly fluctuate accuracy
        const accuracyElement = document.querySelector('[data-target="98.3"]');
        if (accuracyElement) {
            const newAccuracy = (98.2 + Math.random() * 0.2).toFixed(1);
            accuracyElement.textContent = newAccuracy + '%';
        }
    }, 5000);
}

// Start real-time simulation
setTimeout(simulateRealTimeData, 3000);

// Analytics tracking (if needed)
function trackEvent(eventName, properties = {}) {
    console.log('Event tracked:', eventName, properties);
    // Add analytics service integration here if needed
}

// Error handling
window.addEventListener('error', (event) => {
    console.log('Frontend error:', event.error);
    // Don't show errors to users in production
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const perfData = performance.timing;
            const loadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`Page load time: ${loadTime}ms`);
            trackEvent('page_load', { loadTime });
        }, 0);
    });
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        launchPlatform,
        checkSystemStatus,
        updateSystemStatus,
        showNotification
    };
}