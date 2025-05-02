/**
 * StockSim - Chart Setup and Configuration
 * Utility functions for setting up and configuring charts
 */

// Common chart configuration options
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        tooltip: {
            callbacks: {
                label: function(context) {
                    return '₹' + context.raw.toLocaleString('en-IN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
            }
        },
        legend: {
            position: 'top',
        }
    },
    scales: {
        y: {
            beginAtZero: false,
            ticks: {
                callback: function(value) {
                    return '₹' + value.toLocaleString('en-IN', {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                    });
                }
            }
        }
    }
};

/**
 * Create a portfolio line chart
 * @param {string} elementId - Canvas element ID
 * @param {array} data - Array of portfolio history objects with date and value
 */
function createPortfolioChart(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const labels = data.map(item => item.date);
    const values = data.map(item => item.value);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value (₹)',
                data: values,
                backgroundColor: 'rgba(0, 71, 171, 0.2)',
                borderColor: 'rgba(0, 71, 171, 1)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 3
            }]
        },
        options: chartDefaults
    });
}

/**
 * Create a holdings pie chart
 * @param {string} elementId - Canvas element ID
 * @param {array} holdings - Array of stock holding objects
 */
function createHoldingsChart(elementId, holdings) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const labels = holdings.map(holding => holding.symbol);
    const values = holdings.map(holding => holding.value);
    
    // Generate colors - one for each holding
    const colors = generateColors(holdings.length);
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return label + ': ₹' + value.toLocaleString('en-IN', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            }) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a stock price chart
 * @param {string} elementId - Canvas element ID
 * @param {array} dates - Array of date strings
 * @param {array} prices - Array of price values
 * @param {boolean} isPositive - Whether the stock is trending positive
 */
function createStockPriceChart(elementId, dates, prices, isPositive) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const color = isPositive ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)';
    const backgroundColor = isPositive ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)';
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Price (₹)',
                data: prices,
                borderColor: color,
                backgroundColor: backgroundColor,
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: chartDefaults
    });
}

/**
 * Generate an array of colors for charts
 * @param {number} count - Number of colors needed
 * @returns {array} Array of color strings
 */
function generateColors(count) {
    const baseColors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)',
        'rgba(83, 102, 255, 0.7)',
        'rgba(40, 159, 64, 0.7)',
        'rgba(210, 199, 199, 0.7)'
    ];
    
    // If we need more colors than in our base array, generate more
    if (count <= baseColors.length) {
        return baseColors.slice(0, count);
    }
    
    // Generate additional colors
    const colors = [...baseColors];
    for (let i = baseColors.length; i < count; i++) {
        const r = Math.floor(Math.random() * 255);
        const g = Math.floor(Math.random() * 255);
        const b = Math.floor(Math.random() * 255);
        colors.push(`rgba(${r}, ${g}, ${b}, 0.7)`);
    }
    
    return colors;
}
