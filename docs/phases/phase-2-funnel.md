# Phase 2 — Revenue funnel

**Goal**: people can find the product, share it, and want Pro.
**Prereq**: Phase 1 live.
**Done when**: all `../design.md` success criteria hold, including a share link driving a tracked signup.

## Tasks (in order)

### 1. Landing page (highest leverage)
- [ ] Replace `/` login screen with marketing landing (see `../design.md` UI direction):
      hero + live-looking demo analysis, primary CTA → signup, tier table, Pro waitlist CTA
- [ ] Move login/signup to `/login`; auth'd users hitting `/` redirect to `/dashboard`
- [ ] Basic SEO: metadata, OG image (a gorgeous analysis breakdown), sitemap

### 2. Public share links
- [ ] `GET /api/share/{token}` — public, rate-limited, returns analysis + image URL
- [ ] `/share/[token]` page — magazine-spread rendering of the analysis
      (image, lighting diagram, palette, camera breakdown) + "try your own still free" footer CTA
- [ ] Share button on analysis results (copy link)
- [ ] Source tracking: signups/waitlist entries record `?ref=share` etc.

### 3. Watermarked exports
- [ ] Backend exposes `plan` in the user profile response
- [ ] jsPDF export adds "Made with Director AI — directorai.app" footer for free plan
- [ ] Export screen shows watermark notice → Pro waitlist modal link

### 4. Measure
- [ ] Minimal analytics: signup count, analyses run, quota hits, waitlist entries by source.
      A plausible-free option or even a daily SQL query is fine — no heavy analytics stack.

## Explicitly out of scope
Teams, billing, custom domains for shares, comments — Phase 3.
