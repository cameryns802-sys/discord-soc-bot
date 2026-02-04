// Main JavaScript for Sentinel SOC Dashboard

// API Configuration
const API_BASE_URL = window.location.origin;

// Dashboard configuration
let dashboardConfig = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛡️ Sentinel SOC Dashboard Initialized');
    
    // Load dashboard configuration first
    loadDashboardConfig().then(() => {
        // Fetch live statistics
        fetchLiveStats();
        
        // Update stats every 30 seconds
        setInterval(fetchLiveStats, 30000);
        
        // Add smooth scrolling
        initSmoothScrolling();
        
        // Add scroll animations
        initScrollAnimations();
        
        // Initialize activity feed updates
        updateActivityFeed();
        setInterval(updateActivityFeed, 60000); // Update every minute
    });
});

// Load dashboard configuration
async function loadDashboardConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard-config`);
        
        if (response.ok) {
            dashboardConfig = await response.json();
            applyConfiguration();
            console.log('✅ Dashboard configuration loaded');
        } else {
            console.log('Using default configuration');
        }
    } catch (error) {
        console.log('Configuration load error, using defaults:', error);
    }
}

// Apply configuration to dashboard
function applyConfiguration() {
    if (!dashboardConfig || Object.keys(dashboardConfig).length === 0) {
        return;
    }
    
    // Apply branding
    if (dashboardConfig.branding) {
        // Update logo text
        document.querySelectorAll('.logo-text').forEach(el => {
            el.textContent = dashboardConfig.branding.name;
        });
        
        // Update logo icon
        document.querySelectorAll('.logo-icon').forEach(el => {
            el.textContent = dashboardConfig.branding.logo_emoji;
        });
        
        // Update hero section
        const heroTitle = document.querySelector('.hero-title');
        if (heroTitle) heroTitle.textContent = dashboardConfig.branding.name;
        
        const heroDescription = document.querySelector('.hero-description');
        if (heroDescription) heroDescription.textContent = dashboardConfig.branding.description;
        
        const heroSubtitle = document.querySelector('.hero-subtitle');
        if (heroSubtitle) heroSubtitle.innerHTML = dashboardConfig.branding.subtitle;
        
        const heroBadge = document.querySelector('.hero-badge');
        if (heroBadge) heroBadge.textContent = dashboardConfig.hero.badge_text;
        
        // Update footer
        const footerDesc = document.querySelector('.footer-description');
        if (footerDesc) footerDesc.textContent = dashboardConfig.footer.description;
        
        const footerCopyright = document.querySelector('.footer-bottom p');
        if (footerCopyright) footerCopyright.textContent = dashboardConfig.footer.copyright;
    }
    
    // Apply links
    if (dashboardConfig.links) {
        // Update Discord invite links
        document.querySelectorAll('a[href*="discord.gg"]').forEach(el => {
            if (el.textContent.includes('Add to Discord') || el.textContent.includes('Discord')) {
                el.href = dashboardConfig.links.discord_invite;
            }
        });
        
        // Update support server links
        document.querySelectorAll('a').forEach(el => {
            if (el.textContent.includes('Support')) {
                el.href = dashboardConfig.links.support_server;
            }
        });
        
        // Update GitHub link
        const githubLink = document.querySelector('a[href*="github"]');
        if (githubLink) githubLink.href = dashboardConfig.links.github;
    }
    
    // Apply colors dynamically
    if (dashboardConfig.colors) {
        const style = document.createElement('style');
        style.id = 'dynamic-theme';
        style.textContent = `
            :root {
                --primary: ${dashboardConfig.colors.primary} !important;
                --primary-dark: ${dashboardConfig.colors.primary_dark} !important;
                --secondary: ${dashboardConfig.colors.secondary} !important;
                --danger: ${dashboardConfig.colors.danger} !important;
                --warning: ${dashboardConfig.colors.warning} !important;
            }
        `;
        
        // Remove old dynamic theme if exists
        const oldStyle = document.getElementById('dynamic-theme');
        if (oldStyle) oldStyle.remove();
        
        document.head.appendChild(style);
    }
    
    // Apply CTA section
    if (dashboardConfig.cta) {
        const ctaTitle = document.querySelector('.cta-title');
        if (ctaTitle) ctaTitle.textContent = dashboardConfig.cta.title;
        
        const ctaSubtitle = document.querySelector('.cta-subtitle');
        if (ctaSubtitle) ctaSubtitle.textContent = dashboardConfig.cta.subtitle;
    }
    
    // Update stats defaults
    if (dashboardConfig.stats && !dashboardConfig.stats.show_live_stats) {
        useDemoData();
    }
}

// Fetch live statistics from API
async function fetchLiveStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        
        if (response.ok) {
            const data = await response.json();
            updateStatsDisplay(data);
        } else {
            // Fallback to demo data if API unavailable
            console.log('Using demo data - API unavailable');
            useDemoData();
        }
    } catch (error) {
        console.log('Fetch error, using demo data:', error);
        useDemoData();
    }
}

// Update statistics display
function updateStatsDisplay(data) {
    // Update server and user counts
    const serverCount = document.getElementById('serverCount');
    const userCount = document.getElementById('userCount');
    
    if (serverCount && data.guilds !== undefined) {
        animateValue(serverCount, parseInt(serverCount.textContent), data.guilds, 1000);
    }
    
    if (userCount && data.users !== undefined) {
        animateValue(userCount, parseInt(userCount.textContent), data.users, 1000);
    }
    
    // Update threat statistics
    const threatsDetected = document.getElementById('threatsDetected');
    const threatsBlocked = document.getElementById('threatsBlocked');
    const responseTime = document.getElementById('responseTime');
    const securityScore = document.getElementById('securityScore');
    
    if (data.security) {
        if (threatsDetected) {
            animateValue(threatsDetected, parseInt(threatsDetected.textContent), data.security.threats_detected || 0, 1000);
        }
        
        if (threatsBlocked) {
            animateValue(threatsBlocked, parseInt(threatsBlocked.textContent), data.security.threats_blocked || 0, 1000);
        }
        
        if (responseTime && data.security.avg_response_time) {
            responseTime.textContent = data.security.avg_response_time + 's';
        }
        
        if (securityScore && data.security.posture_score) {
            animateValue(securityScore, parseInt(securityScore.textContent), data.security.posture_score, 1000);
        }
    }
}

// Use demo data when API is unavailable
function useDemoData() {
    const demoData = {
        guilds: 2,
        users: 13,
        security: {
            threats_detected: Math.floor(Math.random() * 50) + 150,
            threats_blocked: Math.floor(Math.random() * 45) + 140,
            avg_response_time: (Math.random() * 2 + 1).toFixed(1),
            posture_score: Math.floor(Math.random() * 10) + 90
        }
    };
    
    updateStatsDisplay(demoData);
}

// Animate number changes
function animateValue(element, start, end, duration) {
    if (start === end) return;
    
    const range = end - start;
    const increment = range / (duration / 16); // 60 FPS
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        
        element.textContent = Math.round(current);
    }, 16);
}

// Update activity feed
function updateActivityFeed() {
    const activityFeed = document.getElementById('activityFeed');
    if (!activityFeed) return;
    
    // Simulate real-time activity updates
    const activities = [
        { icon: '🔍', text: 'Phishing attempt detected and blocked', time: getRandomTime(1, 5) },
        { icon: '✅', text: 'Security drill completed - Score: 87/100', time: getRandomTime(10, 30) },
        { icon: '🚨', text: 'Raid attempt prevented - 12 users blocked', time: getRandomTime(45, 90) },
        { icon: '📊', text: 'Weekly security report generated', time: getRandomTime(100, 180) },
        { icon: '🛡️', text: 'Malware scan completed - 0 threats found', time: getRandomTime(200, 300) },
        { icon: '⚠️', text: 'Suspicious activity detected in #general', time: getRandomTime(20, 40) }
    ];
    
    // Shuffle and take first 4
    const shuffled = activities.sort(() => Math.random() - 0.5).slice(0, 4);
    
    activityFeed.innerHTML = shuffled.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">${activity.icon}</div>
            <div class="activity-content">
                <div class="activity-text">${activity.text}</div>
                <div class="activity-time">${activity.time}</div>
            </div>
        </div>
    `).join('');
}

// Generate random time string
function getRandomTime(minMinutes, maxMinutes) {
    const minutes = Math.floor(Math.random() * (maxMinutes - minMinutes + 1)) + minMinutes;
    
    if (minutes < 60) {
        return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    } else {
        const hours = Math.floor(minutes / 60);
        return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    }
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Scroll animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all cards and sections
    const elements = document.querySelectorAll('.feature-card, .stat-card, .system-category, .team-card');
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Header scroll effect
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.3)';
    } else {
        header.style.boxShadow = 'none';
    }
    
    lastScroll = currentScroll;
});

// Add particle effect to hero section (optional)
function initParticles() {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    
    // Create canvas for particles
    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    
    hero.style.position = 'relative';
    hero.insertBefore(canvas, hero.firstChild);
    
    const ctx = canvas.getContext('2d');
    canvas.width = hero.offsetWidth;
    canvas.height = hero.offsetHeight;
    
    const particles = [];
    const particleCount = 50;
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 1;
            this.speedX = Math.random() * 0.5 - 0.25;
            this.speedY = Math.random() * 0.5 - 0.25;
            this.opacity = Math.random() * 0.5 + 0.2;
        }
        
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            
            if (this.x > canvas.width) this.x = 0;
            if (this.x < 0) this.x = canvas.width;
            if (this.y > canvas.height) this.y = 0;
            if (this.y < 0) this.y = canvas.height;
        }
        
        draw() {
            ctx.fillStyle = `rgba(88, 101, 242, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    function init() {
        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        // Draw connections
        particles.forEach((p1, i) => {
            particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    ctx.strokeStyle = `rgba(88, 101, 242, ${0.2 * (1 - distance / 100)})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(animate);
    }
    
    init();
    animate();
    
    // Resize canvas on window resize
    window.addEventListener('resize', () => {
        canvas.width = hero.offsetWidth;
        canvas.height = hero.offsetHeight;
    });
}

// Initialize particles (optional - can be disabled for performance)
// initParticles();

// Console easter egg
console.log('%c🛡️ Sentinel SOC Bot', 'font-size: 24px; font-weight: bold; color: #5865F2;');
console.log('%cEnterprise-Grade Discord Security', 'font-size: 14px; color: #72767d;');
console.log('%c172 Security Cogs | 100 Commands | AI-Powered', 'font-size: 12px; color: #b9bbbe;');
console.log('%c\nInterested in the code? Visit: https://github.com/your-repo', 'font-size: 12px; color: #57F287;');
