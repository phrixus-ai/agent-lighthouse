/* ═══ Hero — Terminal Rain + Scan Line Animation ═══ */

class TerminalRain {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d', { willReadFrequently: true });
        this.columns = [];
        this.scanY = 0;
        this.running = true;
        this.mouseX = -1000;
        this.mouseY = -1000;
        this.fontSize = 14;
        this.bind();
        this.resize();
        this.initColumns();
        this.animate();
    }

    resize() {
        const dpr = Math.min(window.devicePixelRatio, 2);
        const w = this.canvas.offsetWidth || this.canvas.parentElement?.offsetWidth || window.innerWidth;
        const h = this.canvas.offsetHeight || this.canvas.parentElement?.offsetHeight || window.innerHeight;
        this.w = w;
        this.h = h;
        this.canvas.width = w * dpr;
        this.canvas.height = h * dpr;
        this.ctx.scale(dpr, dpr);
        this.fontSize = Math.max(14, Math.round(this.w / 80));
        this.colCount = Math.floor(this.w / this.fontSize);
    }

    /* Audit-relevant tokens that rain down — real check names, not random chars */
    initColumns() {
        const tokens = [
            'robots.txt', 'meta title', 'og:image', 'JSON-LD',
            'HSTS', 'CORS', 'SSL/TLS', 'sitemap.xml',
            'canonical', 'llms.txt', 'alt text', 'viewport',
            'headers', 'DNS', 'CDN', 'A11y',
            '<meta>', '<link>', 'status 200', 'GA4',
            'noindex', 'crawl', 'schema', 'UA',
            'X-Frame', 'CSP', 'lighthouse', 'perfscore',
            'clarity', 'semantics', 'aria', 'fetch()',
            'HEAD', 'GET', '404', '301',
            'DNSSEC', 'CAA', 'TLS 1.3', 'HTTPS'
        ];
        this.columns = [];
        for (let i = 0; i < this.colCount; i++) {
            const streamLen = Math.floor(Math.random() * 8) + 4;
            const chars = [];
            for (let j = 0; j < streamLen; j++) {
                chars.push(tokens[Math.floor(Math.random() * tokens.length)]);
            }
            this.columns.push({
                x: i * this.fontSize,
                y: Math.random() * this.h * -1 - 50,
                speed: Math.random() * 0.6 + 0.3,
                chars,
                len: streamLen,
                opacity: Math.random() * 0.3 + 0.08
            });
        }
    }

    bind() {
        const ro = new ResizeObserver(() => {
            this.resize();
            this.initColumns();
        });
        ro.observe(this.canvas.parentElement || document.body);
        window.addEventListener('resize', () => {
            this.resize();
            this.initColumns();
        });
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouseX = e.clientX - rect.left;
            this.mouseY = e.clientY - rect.top;
        });
        this.canvas.addEventListener('mouseleave', () => {
            this.mouseX = -1000;
            this.mouseY = -1000;
        });
    }

    stop() {
        this.running = false;
    }

    /* Horizontal CRT scan line that sweeps top→bottom */
    drawScanLine() {
        this.scanY += 0.4;
        if (this.scanY > this.h + 20) this.scanY = -10;

        const grad = this.ctx.createLinearGradient(0, this.scanY - 6, 0, this.scanY + 6);
        grad.addColorStop(0, 'rgba(255,107,43,0)');
        grad.addColorStop(0.5, 'rgba(255,107,43,0.06)');
        grad.addColorStop(1, 'rgba(255,107,43,0)');
        this.ctx.fillStyle = grad;
        this.ctx.fillRect(0, this.scanY - 6, this.w, 12);
    }

    /* Subtle film grain overlay */
    drawGrain() {
        const imgData = this.ctx.getImageData(0, 0, 1, 1);
        // Minimal — just a few random dots, not full-screen
        this.ctx.fillStyle = 'rgba(255,107,43,0.02)';
        for (let i = 0; i < 15; i++) {
            const gx = Math.random() * this.w;
            const gy = Math.random() * this.h;
            this.ctx.fillRect(gx, gy, 1, 1);
        }
    }

    animate() {
        if (!this.running) {
            this.ctx.clearRect(0, 0, this.w, this.h);
            return;
        }
        requestAnimationFrame(() => this.animate());

        this.ctx.clearRect(0, 0, this.w, this.h);
        this.ctx.font = `${this.fontSize}px 'JetBrains Mono', ui-monospace, monospace`;

        // Draw each column stream
        for (const col of this.columns) {
            col.y += col.speed;

            for (let i = 0; i < col.len; i++) {
                const charY = col.y + i * this.fontSize;
                if (charY < -20 || charY > this.h + 20) continue;

                // Fade: head is brightest, tail fades out
                const fadeFromHead = (col.len - i) / col.len;
                const alpha = col.opacity * fadeFromHead;

                // Head character is bright amber, rest is dimmer
                // Mouse hover: nearby chars glow brighter
                const dx = col.x - this.mouseX;
                const dy = charY - this.mouseY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const hoverBoost = Math.max(0, 1 - dist / 120) * 0.6;

                if (i === col.len - 1) {
                    this.ctx.fillStyle = `rgba(255,107,43,${Math.min(alpha + 0.3 + hoverBoost, 0.9)})`;
                } else {
                    this.ctx.fillStyle = `rgba(255,107,43,${Math.min(alpha + hoverBoost, 0.8)})`;
                }

                this.ctx.fillText(col.chars[i % col.chars.length], col.x, charY);
            }

            // Reset column when it goes fully off screen
            if (col.y - col.len * this.fontSize > this.h) {
                col.y = Math.random() * -200 - 100;
                col.speed = Math.random() * 0.6 + 0.3;
                col.opacity = Math.random() * 0.3 + 0.08;
            }
        }

        this.drawScanLine();
        this.drawGrain();
    }
}
