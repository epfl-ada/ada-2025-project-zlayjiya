/**
 * YouNiverse Data Story - Main JavaScript
 * Handles animations, scroll effects, and interactive visualizations
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Smooth scroll for navigation links
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
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.background = 'rgba(10, 10, 26, 0.95)';
        } else {
            navbar.style.background = 'rgba(10, 10, 26, 0.9)';
        }
        
        lastScroll = currentScroll;
    });
    /*
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Observe all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
    */
    // Add visible class styles
    const style = document.createElement('style');
    style.textContent = `
        .section.visible {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
    
    // Animate stats on scroll
    const animateValue = (element, start, end, duration, suffix = '') => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = progress * (end - start) + start;
            
            // Format based on suffix
            if (suffix === 'M+') {
                element.textContent = (value / 1000000).toFixed(1) + 'M+';
            } else if (suffix === 'K+') {
                element.textContent = Math.floor(value / 1000) + 'K+';
            } else if (suffix === '%') {
                element.textContent = Math.floor(value) + '%';
            } else if (suffix === 'decimal') {
                element.textContent = value.toFixed(3);
            } else {
                element.textContent = Math.floor(value);
            }
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };
    
    // Observe stat cards
    const statObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statNumber = entry.target.querySelector('.stat-number');
                if (statNumber && !statNumber.classList.contains('animated')) {
                    statNumber.classList.add('animated');
                    const text = statNumber.textContent.trim();
                    
                    // Check for decimal with M suffix (like 72.0M+)
                    const decimalMMatch = text.match(/(\d+\.\d+)M\+/);
                    if (decimalMMatch) {
                        const num = parseFloat(decimalMMatch[1]);
                        animateValue(statNumber, 0, num * 1000000, 2000, 'M+');
                    }
                    // Check for decimal with K suffix (like 136.5K+)
                    else if (text.match(/(\d+\.\d+)K\+/)) {
                        const num = parseFloat(text.match(/(\d+\.\d+)/)[1]);
                        animateValue(statNumber, 0, num * 1000, 2000, 'K+');
                    }
                    // Check for plain decimal (like 0.655)
                    else if (text.match(/^\d+\.\d+$/)) {
                        const num = parseFloat(text);
                        animateValue(statNumber, 0, num, 1500, 'decimal');
                    }
                    // Integer with K suffix
                    else if (text.includes('K+')) {
                        const match = text.match(/(\d+)/);
                        if (match) {
                            const num = parseInt(match[1]);
                            animateValue(statNumber, 0, num * 1000, 2000, 'K+');
                        }
                    }
                    // Integer with M suffix
                    else if (text.includes('M+')) {
                        const match = text.match(/(\d+)/);
                        if (match) {
                            const num = parseInt(match[1]);
                            animateValue(statNumber, 0, num * 1000000, 2000, 'M+');
                        }
                    }
                    // Percentage
                    else if (text.includes('%')) {
                        const match = text.match(/(\d+)/);
                        if (match) {
                            const num = parseInt(match[1]);
                            animateValue(statNumber, 0, num, 1500, '%');
                        }
                    }
                    // Plain integer
                    else {
                        const match = text.match(/(\d+)/);
                        if (match) {
                            const num = parseInt(match[1]);
                            animateValue(statNumber, 0, num, 1500);
                        }
                    }
                }
            }
        });
    }, { threshold: 0.5 });
    
    document.querySelectorAll('.stat-card').forEach(card => {
        statObserver.observe(card);
    });
    
    console.log('🌌 YouNiverse Data Story loaded!');
});

/**
 * Helper function to create Plotly charts
 * Call this from your visualization code
 */
function createChart(containerId, data, layout) {
    const defaultLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            family: 'Inter, sans-serif',
            color: '#a0a0c0'
        },
        margin: { t: 40, r: 20, b: 40, l: 60 },
        ...layout
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(containerId, data, defaultLayout, config);
}

/**
 * Example: Create a sample power law distribution chart
 * Replace this with your actual data
 */
function createPowerLawChart() {
    // Sample data - replace with actual data
    const x = Array.from({length: 100}, (_, i) => i + 1);
    const y = x.map(xi => 1000000 / Math.pow(xi, 1.5));
    
    const trace = {
        x: x,
        y: y,
        type: 'scatter',
        mode: 'lines',
        line: {
            color: '#8b5cf6',
            width: 2
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(139, 92, 246, 0.2)'
    };
    
    const layout = {
        title: '',
        xaxis: { 
            title: 'Channel Rank',
            gridcolor: 'rgba(139, 92, 246, 0.1)'
        },
        yaxis: { 
            title: 'Views',
            type: 'log',
            gridcolor: 'rgba(139, 92, 246, 0.1)'
        }
    };
    
    createChart('power-law-chart', [trace], layout);
}
