/* ═══ AgentLighthouse SVG Icons ═══ */

const CAT_ICONS = {
    ai: '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.4"/><circle cx="6" cy="6.5" r="1" fill="currentColor"/><circle cx="10" cy="6.5" r="1" fill="currentColor"/><path d="M5.5 10a2.5 2.5 0 0 0 5 0" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    crawling: '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="3.5" r="2.2" stroke="currentColor" stroke-width="1.2"/><path d="M8 5.7v3.5M5.2 7.5l2.8 2 2.8-2M4.5 13.5h7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    structured: '<svg viewBox="0 0 16 16" fill="none"><rect x="1.5" y="1.5" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/><rect x="9.5" y="1.5" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/><rect x="1.5" y="9.5" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/></svg>',
    api: '<svg viewBox="0 0 16 16" fill="none"><path d="M2 8h3M11 8h3M5 8a3 3 0 1 0 6 0 3 3 0 0 0-6 0z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M8 5V2M8 14v-3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    meta: '<svg viewBox="0 0 16 16" fill="none"><path d="M2 12V4.5h2.5a2 2 0 0 1 0 4H2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M7 4l2 4-2 4M10 4l2 4-2 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    social: '<svg viewBox="0 0 16 16" fill="none"><circle cx="5" cy="8" r="2.8" stroke="currentColor" stroke-width="1.2"/><circle cx="11" cy="8" r="2.8" stroke="currentColor" stroke-width="1.2"/><path d="M7.5 6.5v3" stroke="currentColor" stroke-width="1.2"/></svg>',
    seo: '<svg viewBox="0 0 16 16" fill="none"><circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" stroke-width="1.2"/><path d="M10 10l4 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    content: '<svg viewBox="0 0 16 16" fill="none"><path d="M3 2h10v12H3z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><path d="M5.5 5h5M5.5 7.5h5M5.5 10h3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>',
    security: '<svg viewBox="0 0 16 16" fill="none"><path d="M8 1.5L3 4v4c0 3.5 2.5 5.5 5 6.5 2.5-1 5-3 5-6.5V4L8 1.5z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><path d="M6 8l1.5 1.5L10 6.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    accessibility: '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="3.5" r="1.8" stroke="currentColor" stroke-width="1"/><path d="M4 6.5h8M8 6.5v3.5M5.5 14l2.5-3.5L10.5 14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    mobile: '<svg viewBox="0 0 16 16" fill="none"><rect x="4" y="1.5" width="8" height="13" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M7 12h2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    performance: '<svg viewBox="0 0 16 16" fill="none"><path d="M2 12l3-4 2.5 2L14 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    modern_web: '<svg viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h8M2 12h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M12 7l2 2-2 2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    general: '<svg viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.2"/><path d="M5.5 5h5M5.5 8h3.5M5.5 11h2" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>'
};

const STATUS_ICONS = {
    pass: '<svg viewBox="0 0 12 12" fill="none"><path d="M2.5 6l3 3 4.5-5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    warning: '<svg viewBox="0 0 12 12" fill="none"><path d="M6 3.5v3.5M6 9v.01" stroke-width="1.5" stroke-linecap="round"/></svg>',
    fail: '<svg viewBox="0 0 12 12" fill="none"><path d="M3.5 3.5l5 5M8.5 3.5l-5 5" stroke-width="1.5" stroke-linecap="round"/></svg>',
    info: '<svg viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="4" stroke-width="1.3"/><path d="M6 5.5v3" stroke-width="1.3" stroke-linecap="round"/><circle cx="6" cy="4" r="0.6" fill="currentColor"/></svg>'
};

const PLUS_ICON = '<svg viewBox="0 0 12 12" fill="none"><path d="M2 6h8M6 2v8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>';
const MINUS_ICON = '<svg viewBox="0 0 12 12" fill="none"><path d="M2 6h8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>';

const CAT_NAMES = {
    ai: "AI Readiness",
    crawling: "Crawler Access",
    structured: "Structured Data",
    api: "API & Headers",
    meta: "Meta Tags",
    social: "Social & Sharing",
    seo: "SEO",
    content: "Content",
    security: "Security",
    accessibility: "Accessibility",
    mobile: "Mobile",
    performance: "Performance",
    modern_web: "Modern Web",
    general: "General"
};

const CAT_ORDER = ["ai", "crawling", "structured", "modern_web", "api", "meta", "social", "seo", "content", "security", "accessibility", "mobile", "performance", "general"];

const SCAN_MESSAGES = [
    "Connecting to server...",
    "Checking SSL certificate...",
    "Analyzing HTML structure...",
    "Scanning meta tags...",
    "Testing AI crawler access...",
    "Checking markdown for agents...",
    "Evaluating structured data...",
    "Calculating readiness score..."
];
