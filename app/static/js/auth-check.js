/**
 * Global Authentication Check Module
 * Provides consistent authentication behavior across all pages
 */

// Configuration
const AUTH_CONFIG = {
    tokenKey: 'auth_token',
    checkInterval: 60000, // Check every 60 seconds
    loginUrl: '/login',
    allowGuestMode: false // DISABLED: Always require authentication
};

// Global authentication state
let authCheckInterval = null;
let isCheckingAuth = false;

/**
 * Get authentication token from storage
 */
function getAuthToken() {
    return localStorage.getItem(AUTH_CONFIG.tokenKey) || 
           sessionStorage.getItem(AUTH_CONFIG.tokenKey) || 
           null;
}

/**
 * Clear authentication data
 */
function clearAuthData() {
    localStorage.removeItem(AUTH_CONFIG.tokenKey);
    localStorage.removeItem('user_data');
    sessionStorage.removeItem(AUTH_CONFIG.tokenKey);
    sessionStorage.removeItem('user_data');
}

/**
 * Check if user is authenticated with the server
 * @returns {Promise<Object|null>} User data if authenticated, null otherwise
 */
async function checkAuthentication() {
    if (isCheckingAuth) return null;
    
    const token = getAuthToken();
    if (!token) {
        // No token found - redirect to login if guest mode is disabled
        if (!AUTH_CONFIG.allowGuestMode) {
            handleAuthenticationFailure();
        }
        return null;
    }
    
    isCheckingAuth = true;
    
    try {
        const response = await fetch('/api/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            credentials: 'include'
        });
        
        if (response.ok) {
            const userData = await response.json();
            isCheckingAuth = false;
            return userData;
        } else if (response.status === 401 || response.status === 403) {
            // Token is invalid or expired - clear data and force login
            console.warn('Authentication token is invalid or expired - redirecting to login');
            clearAuthData();
            isCheckingAuth = false;
            handleAuthenticationFailure();
            return null;
        } else {
            console.error('Authentication check failed:', response.status);
            isCheckingAuth = false;
            return null;
        }
    } catch (error) {
        console.error('Error checking authentication:', error);
        isCheckingAuth = false;
        return null;
    }
}

/**
 * Handle authentication failure
 */
function handleAuthenticationFailure() {
    // Clear any auth data
    clearAuthData();
    
    // Redirect to login if not already there
    if (!window.location.pathname.includes('/login')) {
        console.log('Redirecting to login due to authentication failure');
        window.location.href = AUTH_CONFIG.loginUrl + '?redirect=' + encodeURIComponent(window.location.pathname);
    }
}

/**
 * Auto-populate user info in common UI elements if they exist
 * @param {Object} userData - User data from authentication
 */
function autoPopulateUserInfo(userData) {
    if (!userData) return;
    
    // Common element IDs used across pages
    const commonIds = ['userInfo', 'userName', 'user-name'];
    const iconIds = ['userIcon', 'user-icon'];
    
    const displayName = userData.full_name || userData.username || userData.email || 'User';
    
    // Try to populate any userInfo elements
    for (const id of commonIds) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = displayName;
            console.log(`Auto-populated user info in element: ${id}`);
        }
    }
    
    // Try to populate any userIcon elements
    const initials = displayName.split(' ')
        .map(n => n[0])
        .join('')
        .substring(0, 2)
        .toUpperCase();
        
    for (const id of iconIds) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = initials;
            console.log(`Auto-populated user icon in element: ${id}`);
        }
    }
}

/**
 * Initialize periodic authentication check
 */
function startAuthenticationMonitoring() {
    // Clear any existing interval
    if (authCheckInterval) {
        clearInterval(authCheckInterval);
    }
    
    // Check authentication immediately on page load
    checkAuthentication().then(userData => {
        if (!userData) {
            // No valid authentication - redirect to login
            console.log('No valid authentication found - redirecting to login');
            handleAuthenticationFailure();
        } else {
            console.log('User authenticated:', userData.username);
            // Auto-populate user info if elements exist
            autoPopulateUserInfo(userData);
        }
    });
    
    // Set up periodic check
    authCheckInterval = setInterval(async () => {
        const userData = await checkAuthentication();
        if (!userData) {
            // Authentication failed - redirect to login
            handleAuthenticationFailure();
        }
    }, AUTH_CONFIG.checkInterval);
}

/**
 * Stop authentication monitoring
 */
function stopAuthenticationMonitoring() {
    if (authCheckInterval) {
        clearInterval(authCheckInterval);
        authCheckInterval = null;
    }
}

/**
 * Enhanced fetch wrapper that handles authentication errors globally
 */
async function authenticatedFetch(url, options = {}) {
    const token = getAuthToken();
    
    // Add authorization header if token exists
    if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Always include credentials
    options.credentials = 'include';
    
    try {
        const response = await fetch(url, options);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            console.warn('Request returned 401 - clearing auth data');
            clearAuthData();
            
            if (!AUTH_CONFIG.allowGuestMode) {
                handleAuthenticationFailure();
                throw new Error('Authentication required');
            }
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

/**
 * Load and display user information
 * @param {string} userInfoElementId - ID of element to display username
 * @param {string} userIconElementId - ID of element to display user icon
 * @param {string} defaultName - Default name to show if not authenticated (only used if guest mode enabled)
 */
async function loadAndDisplayUserInfo(userInfoElementId, userIconElementId, defaultName = 'User') {
    const userData = await checkAuthentication();
    
    const userInfoEl = document.getElementById(userInfoElementId);
    const userIconEl = document.getElementById(userIconElementId);
    
    if (userData && userInfoEl) {
        const displayName = userData.full_name || userData.username || userData.email || defaultName;
        userInfoEl.textContent = displayName;
        
        if (userIconEl) {
            const initials = displayName.split(' ')
                .map(n => n[0])
                .join('')
                .substring(0, 2)
                .toUpperCase();
            userIconEl.textContent = initials;
        }
    } else if (!AUTH_CONFIG.allowGuestMode) {
        // No valid authentication and guest mode disabled - redirect to login
        handleAuthenticationFailure();
    } else {
        // Guest mode enabled - show default
        if (userInfoEl) userInfoEl.textContent = defaultName;
        if (userIconEl) userIconEl.textContent = defaultName[0].toUpperCase();
    }
}

/**
 * Initialize authentication system
 * Call this on page load
 */
function initAuth(options = {}) {
    // Merge options with defaults
    Object.assign(AUTH_CONFIG, options);
    
    // Start monitoring
    startAuthenticationMonitoring();
    
    // Add beforeunload handler to clean up
    window.addEventListener('beforeunload', () => {
        stopAuthenticationMonitoring();
    });
}

// Export functions for global use
window.AuthManager = {
    init: initAuth,
    check: checkAuthentication,
    getToken: getAuthToken,
    clearAuth: clearAuthData,
    authenticatedFetch: authenticatedFetch,
    loadUserInfo: loadAndDisplayUserInfo,
    handleAuthFailure: handleAuthenticationFailure
};

// Auto-initialize if not login page
if (!window.location.pathname.includes('/login')) {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initAuth();
        });
    } else {
        initAuth();
    }
}
