/* ═══ AgentLighthouse — Main Application Logic ═══ */

console.log('%c AGENTLIGHTHOUSE v0.3.0 ','background:#ff6b2b;color:#050507;font-size:16px;font-weight:bold;padding:8px 16px');
console.log('%c AI & Agent Readiness Scanner ','color:#ff6b2b;font-size:13px');
console.log('%c You found the console. Nice. ','color:#8b949e;font-size:12px');
console.log('%c → Source: https://github.com/phrixus-ai/agent-lighthouse ','color:#8b949e;font-size:11px');
console.log('');
console.log('%c 🛡 Also check out SkillGuard ','background:#00d992;color:#050507;font-size:13px;font-weight:bold;padding:6px 12px');
console.log('%c AI Skill & Prompt Security Scanner — scan for malware, prompt injection, credential leaks ','color:#00d992;font-size:12px');
console.log('%c → https://skillguard.burakgider.com ','color:#8b949e;font-size:11px');
console.log('');
console.log('%c → Stay curious. Stay secure. ','color:#f2f2f2;font-size:12px;font-weight:bold');

let particleAnim = null;
let scanInterval = null;
let auditRunning = false;
let hasAudited = false;

// ── Scan History (localStorage) ──
const HISTORY_KEY = 'agentlighthouse_history';
const HISTORY_MAX = 8;

function getHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
    catch { return []; }
}

function saveHistory(url, score, level) {
    const h = getHistory().filter(i => i.url !== url);
    h.unshift({ url, score, level, ts: Date.now() });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(0, HISTORY_MAX)));
}

function renderHistory(targetId = 'historyDropdown') {
    const dd = document.getElementById(targetId);
    const h = getHistory();
    if (!h.length) {
        dd.innerHTML = '<div class="history-empty">No recent scans</div>';
        return;
    }
    dd.innerHTML = h.map(i => {
        const levelCls = { excellent: 'pass', good: 'pass', fair: 'warn', poor: 'fail' }[i.level] || 'pass';
        const ago = timeAgo(i.ts);
        return `<div class="history-item" onclick="loadHistoryUrl('${escAttr(i.url)}')">
            <span class="history-score ${levelCls}">${i.score}</span>
            <span class="history-url">${escHtml(i.url.replace(/^https?:\/\//, ''))}</span>
            <span class="history-ago">${ago}</span>
        </div>`;
    }).join('');
}

function loadHistoryUrl(url) {
    const clean = url.replace(/^https?:\/\//, '');
    const barVisible = document.getElementById('headerSearch').classList.contains('visible');
    if (barVisible) {
        document.getElementById('urlInputBar').value = clean;
        closeHistory();
        runAudit(true);
    } else {
        document.getElementById('urlInput').value = clean;
        closeHistory();
        runAudit(false);
    }
}

function toggleHistory(fromBar = false) {
    const targetId = fromBar ? 'historyDropdownBar' : 'historyDropdown';
    const dd = document.getElementById(targetId);
    const open = dd.classList.contains('open');
    document.querySelectorAll('.history-dropdown').forEach(d => d.classList.remove('open'));
    if (!open) {
        renderHistory(targetId);
        dd.classList.add('open');
    }
}

function closeHistory() {
    document.querySelectorAll('.history-dropdown').forEach(d => d.classList.remove('open'));
}

function timeAgo(ts) {
    const s = Math.floor((Date.now() - ts) / 1000);
    if (s < 60) return 'just now';
    if (s < 3600) return Math.floor(s / 60) + 'm ago';
    if (s < 86400) return Math.floor(s / 3600) + 'h ago';
    return Math.floor(s / 86400) + 'd ago';
}

function escAttr(str) {
    return str.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

// ── Favicon helpers ──
const GLOBE_SVG = `<svg width="14" height="14" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1"/>
    <path d="M1.5 8h13M8 1.5c-2 2-2 9 0 13M8 1.5c2 2 2 9 0 13" stroke="currentColor" stroke-width="1"/>
</svg>`;

function debounce(fn, ms) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

function setFaviconPrefix(prefixEl, domain) {
    if (!domain) {
        prefixEl.innerHTML = GLOBE_SVG;
        return;
    }
    // Helper: create img, add to DOM first, then load
    function loadImg(src, onSuccess, onFail) {
        const img = document.createElement('img');
        img.width = 14;
        img.height = 14;
        img.style.borderRadius = '2px';
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.2s';
        img.onload = () => { if (onSuccess) onSuccess(img); };
        img.onerror = () => { if (onFail) onFail(); };
        prefixEl.innerHTML = '';
        prefixEl.appendChild(img);
        img.src = src;
    }
    // Chain: .ico → .svg → DuckDuckGo → Globe
    function trySvg() {
        loadImg(
            `https://${encodeURIComponent(domain)}/favicon.svg`,
            (img) => { img.style.opacity = '1'; },
            () => tryDuckDuckGo()
        );
    }
    function tryDuckDuckGo() {
        loadImg(
            `https://icons.duckduckgo.com/ip3/${encodeURIComponent(domain)}.ico`,
            (img) => { if (img.naturalWidth >= 14) img.style.opacity = '1'; else prefixEl.innerHTML = GLOBE_SVG; },
            () => { prefixEl.innerHTML = GLOBE_SVG; }
        );
    }
    // Try .ico first, then .svg, then DuckDuckGo
    loadImg(
        `https://${encodeURIComponent(domain)}/favicon.ico`,
        (img) => { img.style.opacity = '1'; },
        () => trySvg()
    );
}

function bindFaviconInput(inputEl, prefixEl) {
    const update = debounce((val) => {
        const domain = val.trim().replace(/^https?:\/\//, '').split('/')[0];
        setFaviconPrefix(prefixEl, domain);
    }, 300);

    inputEl.addEventListener('input', (e) => update(e.target.value));
    inputEl.addEventListener('paste', () => setTimeout(() => update(inputEl.value), 0));
    inputEl.addEventListener('blur', () => {
        if (!inputEl.value.trim()) setFaviconPrefix(prefixEl, '');
    });
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('heroCanvas');
    if (canvas) particleAnim = new TerminalRain(canvas);

    const urlInput = document.getElementById('urlInput');
    const heroPrefix = urlInput.closest('.url-wrap').querySelector('.url-prefix');
    bindFaviconInput(urlInput, heroPrefix);

    urlInput.addEventListener('paste', (e) => {
        e.preventDefault();
        let text = (e.clipboardData || window.clipboardData).getData('text');
        text = text.replace(/^https?:\/\//, '');
        urlInput.value = text;
        setFaviconPrefix(heroPrefix, text.split('/')[0]);
    });

    urlInput.addEventListener('blur', () => {
        urlInput.value = urlInput.value.replace(/^https?:\/\//, '');
    });

    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') runAudit();
    });

    // History toggle (hero)
    document.getElementById('historyBtn').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleHistory();
    });

    // Audit buttons
    document.getElementById('auditBtn').addEventListener('click', () => runAudit(false));
    document.getElementById('auditBtnBar').addEventListener('click', () => runAudit(true));

    // Export JSON button
    document.getElementById('exportJsonBtn').addEventListener('click', downloadJSON);

    // Close history on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#historyBtn') && !e.target.closest('#historyDropdown') &&
            !e.target.closest('#historyBtnBar') && !e.target.closest('#historyDropdownBar')) {
            closeHistory();
        }
    });

    // ── Bar input (header search) ──
    const urlInputBar = document.getElementById('urlInputBar');
    const barPrefix = urlInputBar.closest('.url-wrap').querySelector('.url-prefix');
    bindFaviconInput(urlInputBar, barPrefix);

    urlInputBar.addEventListener('paste', (e) => {
        e.preventDefault();
        let text = (e.clipboardData || window.clipboardData).getData('text');
        text = text.replace(/^https?:\/\//, '');
        urlInputBar.value = text;
        setFaviconPrefix(barPrefix, text.split('/')[0]);
    });
    urlInputBar.addEventListener('blur', () => {
        urlInputBar.value = urlInputBar.value.replace(/^https?:\/\//, '');
    });
    urlInputBar.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') runAudit(true);
    });
    document.getElementById('historyBtnBar').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleHistory(true);
    });

    initScrollTop();

    // ── Restore last audit on refresh ──
    try {
        const last = JSON.parse(localStorage.getItem('agentlighthouse_last'));
        if (last && last.data && last.ts) {
            const age = Date.now() - last.ts;
            const MAX_AGE = 30 * 60 * 1000; // 30 minutes
            if (age < MAX_AGE) {
                document.getElementById('hero').classList.add('hidden');
                if (particleAnim) particleAnim.stop();
                hasAudited = true;
                document.getElementById('headerSearch').classList.add('visible');
                document.getElementById('headerRight').style.display = 'none';
                document.getElementById('urlInputBar').value = last.url;
                const domain = last.url.replace(/^https?:\/\//, '').split('/')[0];
                const barPrefixEl = document.getElementById('urlInputBar').closest('.url-wrap').querySelector('.url-prefix');
                if (barPrefixEl) setFaviconPrefix(barPrefixEl, domain);
                renderResults(last.data);
                window._lastAuditData = last.data;
                document.getElementById('reportButtons').style.display = 'flex';
            } else {
                localStorage.removeItem('agentlighthouse_last');
            }
        }
    } catch(e) {}
});

async function runAudit(fromBar = false) {
    if (auditRunning) return;
    auditRunning = true;

    const urlInput = document.getElementById(fromBar ? 'urlInputBar' : 'urlInput');
    const rawUrl = urlInput.value.trim();
    const errorEl = document.getElementById('errorMsg');
    const results = document.getElementById('results');

    if (!rawUrl) { auditRunning = false; showError('Please enter a URL'); return; }

    // Disable BOTH buttons
    document.getElementById('auditBtn').disabled = true;
    document.getElementById('auditBtnBar').disabled = true;
    errorEl.classList.remove('active');
    results.classList.remove('active');

    const domain = rawUrl.replace(/^https?:\/\//, '').replace(/\/.*$/, '');

    // ── Open dialog ──
    const dialog = document.getElementById('auditDialog');
    const dialogUrl = document.getElementById('dialogUrl');
    const termCmd = document.getElementById('termCmd');
    const termBody = document.getElementById('termBody');
    dialogUrl.textContent = `> agentlighthouse ${domain}`;
    termCmd.textContent = '';
    termBody.innerHTML = '';
    dialog.showModal();

    // ── Terminal animation lines ──
    const TERM_LINES = [
        { text: 'DNS lookup ...', delay: 300, exitAfter: 900 },
        { text: `TCP handshake ${domain}:443`, delay: 600, exitAfter: 1100 },
        { text: 'TLS negotiation ...', delay: 900, exitAfter: 1400 },
        { text: 'GET / HEADERS 200 OK', delay: 1200, exitAfter: 1700 },
        { text: 'parsing <meta>, <link>, <script>', delay: 1500, exitAfter: 2000 },
        { text: 'robots.txt / sitemap.xml', delay: 1800, exitAfter: 2300 },
        { text: 'OG / JSON-LD / structured data', delay: 2100, exitAfter: 2600 },
        { text: 'Lighthouse signals ...', delay: 2400, exitAfter: 2900 },
        { text: 'scoring ...', delay: 2700, exitAfter: 3200 },
        { text: 'done.', delay: 3000, exitAfter: 3500 },
    ];
    const timers = [];
    TERM_LINES.forEach(line => {
        const t1 = setTimeout(() => {
            const el = document.createElement('div');
            el.className = 'term-line step';
            el.textContent = line.text;
            termBody.querySelectorAll('.cursor').forEach(c => c.remove());
            const cursor = document.createElement('span');
            cursor.className = 'cursor';
            el.appendChild(cursor);
            termBody.appendChild(el);
            if (line.exitAfter) {
                const t2 = setTimeout(() => {
                    el.classList.add('exit');
                    setTimeout(() => el.remove(), 800);
                }, line.exitAfter - line.delay);
                timers.push(t2);
            }
        }, line.delay);
        timers.push(t1);
    });
    scanInterval = { timers };

    try {
        const url = rawUrl.startsWith('http') ? rawUrl : 'https://' + rawUrl;
        const resp = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        let data;
        try {
            data = await resp.json();
        } catch (parseErr) {
            console.error('JSON parse error:', parseErr, 'Response status:', resp.status);
            showError('Server returned an invalid response');
            dialog.close();
            return;
        }
        if (!resp.ok) { showError(data.error || 'Audit failed'); dialog.close(); return; }

        // Ensure scan animation shows for at least 3 seconds
        await new Promise(r => setTimeout(r, 3000));

        // ── Dialog done — transition to results ──
        dialog.close();

        if (!hasAudited) {
            // First audit: hide hero, show header search
            document.getElementById('hero').classList.add('hidden');
            if (particleAnim) particleAnim.stop();
            hasAudited = true;
        }

        document.getElementById('headerSearch').classList.add('visible');
        document.getElementById('headerRight').style.display = 'none';
        document.getElementById('urlInputBar').value = rawUrl;
        // Update favicon for header search input
        const barPrefixEl = document.getElementById('urlInputBar').closest('.url-wrap').querySelector('.url-prefix');
        if (barPrefixEl) setFaviconPrefix(barPrefixEl, domain);

        renderResults(data);
        saveHistory(data.url, data.score, data.level);
        // Show report buttons
        document.getElementById('reportButtons').style.display = 'flex';
        // Store last audit data for JSON download
        window._lastAuditData = data;
        // Persist full audit data for refresh restore
        try {
            localStorage.setItem('agentlighthouse_last', JSON.stringify({ url: rawUrl, ts: Date.now(), data }));
        } catch(e) { /* quota exceeded — ignore */ }
    } catch (e) {
        console.error('Audit error:', e);
        showError('Network error: ' + (e.message || 'could not reach the server'));
        dialog.close();
    } finally {
        document.getElementById('auditBtn').disabled = false;
        document.getElementById('auditBtnBar').disabled = false;
        auditRunning = false;
        if (scanInterval && scanInterval.timers) {
            scanInterval.timers.forEach(t => clearTimeout(t));
            scanInterval = null;
        }
    }
}

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = msg;
    el.classList.add('active');
}

function animateNumber(elId, target, duration) {
    const el = document.getElementById(elId);
    if (!el) return;
    const start = performance.now();
    function update(now) {
        const p = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * eased);
        if (p < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function renderResults(data) {
    const circumference = 2 * Math.PI * 55;
    const progress = document.getElementById('scoreProgress');
    const offset = circumference - (data.score / 100) * circumference;
    progress.style.strokeDasharray = circumference;
    progress.style.strokeDashoffset = offset;
    progress.className = 'progress ' + data.level;

    animateNumber('scoreNumber', data.score, 1200);

    const levelTexts = { excellent: 'Excellent', good: 'Good', fair: 'Fair', poor: 'Poor' };
    const label = document.getElementById('scoreLabel');
    label.textContent = levelTexts[data.level] || '—';
    label.className = 'score-label ' + data.level;

    document.getElementById('scannedUrl').textContent = data.url;
    document.getElementById('passCount').textContent = data.summary.passed;
    document.getElementById('warnCount').textContent = data.summary.warnings;
    document.getElementById('failCount').textContent = data.summary.failed;

    renderScoreExtras(data);

    const groups = {};
    data.checks.forEach(c => {
        const cat = c.category || 'general';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(c);
    });

    const sortedCats = Object.keys(groups).sort((a, b) => CAT_ORDER.indexOf(a) - CAT_ORDER.indexOf(b));

    const container = document.getElementById('categoryDetails');
    container.innerHTML = '';

    sortedCats.forEach((cat, idx) => {
        const name = CAT_NAMES[cat] || cat;
        const icon = CAT_ICONS[cat] || CAT_ICONS.general;
        const checks = groups[cat].sort((a, b) => {
            const o = { fail: 0, warning: 1, pass: 2 };
            return o[a.status] - o[b.status];
        });

        const hasFail = checks.some(c => c.status === 'fail');
        const hasWarn = checks.some(c => c.status === 'warning');
        const worst = hasFail ? 'fail' : hasWarn ? 'warn' : 'pass';
        const passCount = checks.filter(c => c.status === 'pass' || c.status === 'info').length;
        const statusClass = hasFail ? 'has-fail' : hasWarn ? 'has-warn' : '';

        const section = document.createElement('details');
        section.className = 'accordion-section ' + statusClass;
        section.id = 'acc-' + cat;
        section.open = (idx === 0);

        section.innerHTML = `
            <summary data-cat="${cat}">
                <span class="acc-status-dot"></span>
                <span class="acc-icon">${icon}</span>
                <span class="acc-name">${name}</span>
                <span class="acc-badge ${worst}">${passCount}/${checks.length}</span>
                <span class="acc-toggle">${section.open ? MINUS_ICON : PLUS_ICON}</span>
            </summary>
            <div class="accordion-body">
                ${checks.map((check, ci) => {
                    const isFull = check.score === check.max_score;
                    const delay = (idx * 15) + (ci * 30);
                    const tooltip = check.status === 'pass'
                        ? ' title="' + escAttr(check.value || check.name + ': OK') + '"'
                        : '';
                    return `
                        <div class="check-item" style="animation-delay:${delay}ms"${tooltip}>
                            <div class="check-icon ${check.status}">${STATUS_ICONS[check.status]}</div>
                            <div class="check-body">
                                <div class="check-name">${check.name}</div>
                                ${check.status !== 'pass' ? '<div class="check-value">' + escHtml(check.value || '—') + '</div>' : ''}
                                ${check.recommendation ? '<div class="check-rec">\\u2192 ' + escHtml(check.recommendation) + '</div>' : ''}
                            </div>
                            <div class="check-score ${isFull ? 'full' : ''}">${check.score}/${check.max_score}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        container.appendChild(section);
    });

    document.getElementById('results').classList.add('active');

    document.querySelectorAll('.accordion-section').forEach(section => {
        section.addEventListener('toggle', () => {
            const icon = section.querySelector('.acc-toggle');
            if (!icon) return;
            icon.innerHTML = section.open ? MINUS_ICON : PLUS_ICON;
        });
    });
}

function renderScoreExtras(data) {
    const container = document.getElementById('scoreExtras');
    if (!container) return;

    let html = '';

    if (data.ssl_days_left !== undefined) {
        const cls = data.ssl_days_left > 30 ? 'ok' : data.ssl_days_left > 0 ? 'warn' : 'bad';
        const label = data.ssl_days_left > 0 ? data.ssl_days_left + ' days' : 'Expired';
        html += `<div class="extra-item">
            <span class="extra-label">SSL</span>
            <span class="extra-value ${cls}">${label}</span>
        </div>`;
    }

    if (data.domain_days_left !== undefined) {
        const cls = data.domain_days_left > 60 ? 'ok' : data.domain_days_left > 30 ? 'warn' : 'bad';
        html += `<div class="extra-item">
            <span class="extra-label">Domain</span>
            <span class="extra-value ${cls}">${data.domain_days_left} days</span>
        </div>`;
    }

    const rtCheck = (data.checks || []).find(c => c.name === 'Response Time');
    if (rtCheck) {
        html += `<div class="extra-item">
            <span class="extra-label">Speed</span>
            <span class="extra-value ${rtCheck.status === 'pass' ? 'ok' : 'warn'}">${rtCheck.value}</span>
        </div>`;
    }

    container.innerHTML = html;
}

function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── Scroll to Top ──
function initScrollTop() {
    const btn = document.getElementById('scrollTop');
    window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// ── Report Download ──
function downloadJSON() {
    const data = window._lastAuditData;
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const domain = (data.url || 'audit').replace(/^https?:\/\//, '').split('/')[0];
    a.href = url;
    a.download = `agentlighthouse-${domain}-${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
}
