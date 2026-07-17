# Product & Design

## Positioning

**Director AI is the AI Director of Photography for small production teams.**
Upload any film still → get the lighting setup, camera settings, and color palette —
then turn that into shot lists and print-ready call sheets your crew actually uses.

- **Paying customer (target)**: small production houses / videography agencies ($50–200/mo, Phase 3).
- **Funnel**: indie filmmakers & film students on a free tier; they bring the tool into paid productions.
- **Hook vs. moat**: AI analysis is the hook (impressive, shareable). Workflow
  (projects → scenes → shots → call sheets) is the moat — that's what teams pay for.

## Monetization: free + waitlisted Pro

No billing code at launch. Validate first.

| | Free | Pro (waitlist) |
|---|---|---|
| AI analyses | 5 / month | Unlimited |
| Projects | 2 | Unlimited |
| PDF call-sheet export | Watermarked ("Made with Director AI") | Clean |
| Share links | Yes (they're the growth loop — never gate) | Yes |
| Team features | — | Phase 3, driven by waitlist demand |

Upgrade triggers surface at the exact moment of friction: hitting the analysis quota,
the 3rd project attempt, or exporting a watermarked PDF. Each shows the Pro modal →
email capture → `waitlist` table. When the waitlist proves demand, Phase 3 adds billing
(likely Razorpay; decision deferred).

## Growth loop (Phase 2)

1. Filmmaker analyzes a still from a film they admire.
2. One click → public share link (`/share/{token}`): the image, lighting diagram,
   palette, camera breakdown — beautifully rendered, no login required.
3. Page footer: "Analyzed with Director AI — try your own still free."
4. Film-Twitter/Reddit/Discord native content → new signups.

## UI design direction

Keep the existing premium dark glassmorphism system — it fits the film audience.
Refinements, not a redesign:

- **Landing page** (replaces the bare login at `/`): hero with a real
  before/after analysis demo (a famous-style still + its breakdown), one primary CTA
  ("Analyze your first still — free"), tier comparison, waitlist CTA for Pro.
  Cinematic dark theme, film-set accent color (amber/tungsten warmth over pure neon).
- **Share page**: the analysis presented like a cinematography magazine spread —
  this page IS the marketing, it must look better than the app.
- **Quota UI**: subtle usage meter in the navbar ("3/5 analyses this month");
  friendly limit modal, never a dead-end error.
- **Existing app screens**: unchanged except where quota/upgrade states are added.

## Success criteria

Phase 1–2 are successful when, without manual intervention:
- A stranger can sign up, analyze a still, build a shot list, and export a PDF on the live URL.
- Free limits enforce themselves and funnel to the waitlist.
- A share link renders publicly and drives a measurable signup (source tracking on waitlist/signup).

Decision gate for Phase 3: **≥25 waitlist emails or 3 direct "can I pay you" requests.**
