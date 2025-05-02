/**
 * StockSim - Market Functionality
 * JavaScript for enhancing user experience in the StockSim application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add "active" class to current nav item based on URL
    highlightCurrentNavItem();
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Setup trade functionality
    setupTradeForm();
    
    // Setup challenge form validation
    setupChallengeForm();
    
    // Auto-dismiss alerts after 5 seconds
    setupAlertDismissal();
});

/**
 * Highlight the current navigation item based on URL
 */
function highlightCurrentNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // Check if the current path starts with the link's href
        // This handles sub-paths like /stock/RELIANCE.NS/ matching with /stock/
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

/**
 * Setup trade form functionality
 */
function setupTradeForm() {
    const quantityInput = document.getElementById('quantity');
    const totalAmountElement = document.getElementById('totalAmount');
    const stockPriceElement = document.querySelector('input[value].stock-price');
    
    if (quantityInput && totalAmountElement && stockPriceElement) {
        const stockPrice = parseFloat(stockPriceElement.value);
        
        quantityInput.addEventListener('input', function() {
            const quantity = parseInt(this.value) || 0;
            const totalAmount = (quantity * stockPrice).toFixed(2);
            totalAmountElement.value = totalAmount;
        });
    }
}

/**
 * Setup challenge form validation
 */
function setupChallengeForm() {
    const challengeForm = document.getElementById('challengeForm');
    
    if (challengeForm) {
        challengeForm.addEventListener('submit', function(event) {
            const startDate = new Date(document.getElementById('start_date').value);
            const endDate = new Date(document.getElementById('end_date').value);
            
            // Validate dates
            if (startDate >= endDate) {
                event.preventDefault();
                alert('End date must be after start date.');
                return false;
            }
            
            if (startDate < new Date()) {
                event.preventDefault();
                alert('Start date cannot be in the past.');
                return false;
            }
            
            return true;
        });
    }
}

/**
 * Auto-dismiss alerts after 5 seconds
 */
function setupAlertDismissal() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            // Check if the alert still exists in the DOM
            if (alert && alert.parentNode) {
                // Create a bootstrap alert instance and call the close method
                if (typeof bootstrap !== 'undefined') {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                } else {
                    // Fallback for when Bootstrap is not available
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        if (alert.parentNode) {
                            alert.parentNode.removeChild(alert);
                        }
                    }, 500);
                }
            }
        }, 5000);
    });
}

/**
 * Format currency amounts with ₹ symbol
 * @param {number} amount - The amount to format
 * @returns {string} Formatted amount with ₹ symbol
 */
function formatCurrency(amount) {
    return '₹' + amount.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Calculate and display transaction total
 * @param {number} quantity - Number of shares
 * @param {number} price - Price per share
 * @param {string} outputId - ID of element to display total
 */
function calculateTransactionTotal(quantity, price, outputId) {
    const total = quantity * price;
    document.getElementById(outputId).value = formatCurrency(total);
}

/**
 * Search stocks API call
 * @param {string} query - Search query
 * @param {function} callback - Callback function to handle results
 */
function searchStocks(query, callback) {
    if (!query || query.length < 2) {
        callback([]);
        return;
    }
    
    fetch(`/api/search-stock/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            callback(data.results);
        })
        .catch(error => {
            console.error('Error searching stocks:', error);
            callback([]);
        });
}
