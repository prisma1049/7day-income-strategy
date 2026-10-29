# 7-Day Revenue Sprint - Day 2: Channel Selection & Tracking Setup

## ✅ Selected Channel: Affiliate Marketing

### Rationale (Highest ROI for ARM64 Device)
| Channel | Pros | Cons | Verdict |
|---------|------|------|---------|
| **Affiliate Marketing** ✅ | Content ready (7 articles), zero production cost, 30-50% recurring commissions, no inventory/support, fits 479MB RAM | Depends on traffic | **SELECTED** |
| Digital Product | High margin, full control | Weeks to create, needs payment processing, support | Too slow |
| Service/Consulting | Immediate revenue | Time-for-money, doesn't scale, manual | Not automated |
| Content Monetization (ads) | Passive | Needs massive traffic (10k+ views), low RPM | Too slow for 7 days |

### Affiliate Programs Configured
1. **Mixo** - 50% commission, 90-day cookie (AI Website Builder)
2. **ElevenLabs** - 50% recurring commission (AI Voice/TTS)
3. **RunPod** - 20% recurring (GPU Cloud for developers)
4. **Surfer SEO** - 30% recurring (SEO Content Optimization)
5. **Carrd** - 30% commission (Simple Sites)
6. **Vast.ai** - 10% commission (GPU Marketplace)

### Assets Ready (from Day 1 Audit)
- 7 review/comparison articles in `/root/7day-income-site/`
- Content framework & editorial calendar
- Publishing pipeline (`publish.py`) with GitHub Pages deploy + Twitter threads
- Git repo initialized locally

---

## ✅ Tracking Infrastructure Deployed

### 1. SQLite Tracking Database (`tracking.db`)
- **clicks table**: timestamp, affiliate_program, article_slug, UTM params, ip_hash, user_agent, referrer
- **conversions table**: timestamp, program, click_id, amount_eur, commission_eur, status
- **daily_stats table**: aggregated daily KPIs (views, visitors, clicks, conversions, revenue)

### 2. Lightweight Tracking Server (`server.py`)
- **Affiliate Redirects**: `/go/<program>/<article_slug>?utm_*` → 302 to affiliate URL with tracking
- **Dashboard API**: `/api/dashboard` - JSON with totals, per-program stats, recent clicks/conversions
- **Dashboard UI**: `/dashboard` - Visual dashboard with auto-refresh
- **Static File Serving**: Serves all HTML articles from `/root/7day-income-site/`
- **Memory Efficient**: Pure Python stdlib, ~10MB RAM on ARM64

### 3. Tracked Affiliate Links in All Articles
Every article now has CTA buttons with tracked URLs:
- `/go/mixo/mixo-review` → redirects to `https://mixo.io?ref=7day_sprint&utm_source=organic&utm_medium=article&utm_campaign=7day_sprint&utm_content=mixo-review`
- Clicks automatically logged with UTM attribution

### 4. Testing Verified
- ✅ Click logging works (2 test clicks recorded)
- ✅ Conversion logging works (€14.50 commission tracked)
- ✅ Redirect endpoint works (302 with proper UTM params)
- ✅ Dashboard API returns correct JSON
- ✅ Dashboard UI renders with real data
- ✅ Static articles serve with tracked CTA buttons

---

## 📊 KPI Tracking Targets (for 7-day sprint)
| Metric | Target | Tracking Method |
|--------|--------|-----------------|
| Revenue | €50+ | Conversion table + affiliate dashboards |
| Views | 1,000+ | Daily stats (page_views) + server logs |
| Followers/Subs | 50+ | Twitter Analytics + newsletter signups (if added) |
| Affiliate Clicks | 100+ | Clicks table filtered by program |
| Conversions | 3+ | Conversions table with confirmed status |

---

## 🚀 Deployment Commands

### Start Tracking Server (background)
```bash
cd /root/7day-income-site
nohup python3 server.py > server.log 2>&1 &
```

### Deploy to GitHub Pages (public URL)
```bash
cd /root/7day-income-site
git add .
git commit -m "Day 2: Tracking + affiliate links"
git push origin main
# Enable GitHub Pages in repo settings → serves at https://<user>.github.io/7day-income-strategy/
```

### Test Affiliate Links Locally
```bash
curl -v "http://localhost:8080/go/mixo/mixo-review?utm_source=twitter&utm_medium=social"
curl "http://localhost:8080/api/dashboard"
open "http://localhost:8080/dashboard"
```

---

## 📋 Next Steps (Day 3)
1. Deploy site publicly (GitHub Pages + custom domain optional)
2. Produce 2-3 new comparison articles per editorial calendar
3. Launch traffic acquisition: X/Twitter threads, Reddit, Indie Hackers, HN
4. Monitor dashboard for first organic clicks

---

## 📁 Files Created/Modified
- `/root/7day-income-site/tracking.py` - Core tracking library
- `/root/7day-income-site/server.py` - Tracking redirect server + dashboard
- `/root/7day-income-site/update_links.py` - Link update utility
- `/root/7day-income-site/add_cta.py` - CTA button injector
- `/root/7day-income-site/tracking.db` - SQLite database (auto-created)
- All 7 HTML articles updated with tracked CTA buttons
- `index.html` updated