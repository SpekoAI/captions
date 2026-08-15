SPEKO.AI LANDING DESIGN SPEC (extracted 2026-08-15 from live HTML + /_next/static/immutable/chunks/2xt9yrk1iecnh.css; Next.js + Tailwind v4 utilities + a small set of custom tokens/classes)

COLOR TOKENS (light-only; define on :root)
- --paper: #faf9f6 (page bg, warm off-white) ; --paper-2: #f2f2ec (secondary bg: tab rails, band strips, code title bars) ; --card: #fff (panel bg)
- Ink ramp (green-cast neutrals): --ink: #0e1512 (headings/primary) ; --ink-2: #1d2823 ; --body: #4e5b54 (paragraphs) ; --muted: #5d6861 (nav links, secondary) ; --dim: #646e67 (labels, icons)
- Hairlines: --line: #0e151217 (ink @9%) ; --line-2: #0e151229 (ink @16%, the default border)
- Accent (single blue): --brand: #2f6ad1 ; --brand-hi: #2a5ebb (hover) ; --on-brand: #fff ; alphas: --brand-a06: #2f6ad10f, --brand-a12: #2f6ad11f, --brand-a20: #2f6ad133 (ring + ::selection bg)
- Data scale (heatmap, light->dark blue): --s0 #f2f6fb, --s1 #eaf1fd, --s2 #dbe6f4, --s3 #b9d3f2, --s4 #93b6f2, --s5 #82aaee, --s6 #4a7acc, --s7 #2c5498
- Semantic: --up #2c5498, --down/destructive #a8443c, --warn #7c5d27, --ok #3f7a52 (status dot)
- ::selection { background: var(--brand-a20); color: var(--ink) }

FONTS
- Body/UI: Geist (variable 100-900). body { font-feature-settings: "tnum" 1, "cv05" 1; -webkit-font-smoothing: antialiased } — tabular numerals globally.
- Display: Hanken Grotesk (variable) on h1,h2,h3 only, via --font-display: Hanken Grotesk, Geist, system-ui. Base heading rule: h1,h2,h3 { letter-spacing: -.022em; text-wrap: balance }.
- Mono: Geist Mono (code, labels, numbers). .num { font-family: mono; font-variant-numeric: tabular-nums; text-align: right }.
- Weights used: 400 normal, 500 medium (UI/buttons/code keywords), 600 semibold (all headings + wordmark). Nothing bolder.

TYPE SCALE
- H1 hero: clamp(2.6rem,6.4vw,4.6rem), line-height 1.02, 600, tracking -0.032em, --ink; accent phrase inline in --brand with tracking +0.015em.
- Large section H2: clamp(1.85rem,3.6vw,2.9rem), lh 1.06, 600, max-width 20ch.
- Band H2 (Router/Gateway strips): clamp(1.45rem,2.6vw,1.95rem), lh 1, tracking -0.025em.
- Final CTA H2: clamp(1.3rem,5.4vw,2.6rem), lh 1.08, whitespace-nowrap.
- Understated data-section H2: just 15px, 600, leading-none (deliberately tiny titles: "Benchmark coverage by language").
- Hero sub: clamp(1.02rem,1.5vw,1.19rem), lh 1.55, --body, max-w 44ch, centered. Section lede: 16.5px, lh 1.6, --body, max-w 54ch.
- Workhorse UI size: 13.5px (nav links, footer links, band descriptions, table text). Buttons 14.5px (13.5px in nav). Row titles 17px medium tracking -0.01em. Small: 13px meta, 12.5px code/fineprint, 12px, 11px, 10.5px, down to 9px column tags.
- .marker (the label style): mono 11px, uppercase, letter-spacing .14em, color --dim, tabular-nums. Used for table column heads, axis labels ("Accuracy (WER)"), legend ("worse/better"), footer column titles. This replaces eyebrows/badges.
- Mono letterspacing positive: .14em markers, .1em 9px tags, .06em 10.5px "copy" button.

LAYOUT + SPACING
- Container .shell: width 100%; max-width 1240px (--maxw); padding-inline clamp(20px,5vw,56px) (--gutter); margin-inline auto.
- Section pattern: <section><div class="max-w-[1240px] mx-auto border-t border-line-2"> + node circles + <div class="shell py-20 md:py-28">. Section padding 80px/112px. Rules span the CONTAINER, not the viewport.
- Offsets: --nav-h 64px; sticky panels sit at top: calc(64px + 52px + 1.5rem).
- Radius tokens: 18/12/8/4px (--r-lg/md/sm/xs). In practice: rounded-xl (12px) buttons/pills/chips, rounded-2xl (16px) tab rails, rounded-[26px] nav pill, and MICRO radii for data: 2px heatmap cells, 2.5px flags, 3px code marks. Nothing rounded-full except status dots.
- Motion: --ease: cubic-bezier(.22,1,.36,1); durations --t-press 70ms, --t-tint .12s (all hovers), --t-draw .2s, --t-enter .42s. Hover motion = color/border tints only, plus 1px translate on external-link arrows.

NAV
- header: sticky top-0 z-50 pt-3; inner bar h-52px flex justify-between rounded-[26px], STARTS border-transparent bg-transparent shadow-none; transitions [background,border,shadow,radius,backdrop-filter] 260ms ease(.22,1,.36,1) to a floating pill on scroll.
- Logo: 28px square, rx=12/48 fill brand, white pixel-grid glyph (6px squares on 48 grid); wordmark 17px font-display 600 tracking -0.03em.
- Links 13.5px text-muted hover:text-ink; dropdown "Platform" + external links (Models/Pricing/Docs) each get a 14px lucide arrow-up-right in dim/70 that translates x+1px y-1px and darkens on hover. Right side: ghost "Sign in" + primary "Get API key".

BUTTONS
- Primary: rounded-xl bg-brand px-3 py-1.5 text 13.5-14.5px font-medium white; hover bg-brand-hi. Flat: no shadow, no gradient, compact (not tall CTAs).
- Secondary: rounded-xl border border-line-2 bg-card, same padding, text-ink, hover border-ink/25.
- Ghost: rounded-xl px-3 py-1.5 text-muted hover:bg-ink/[0.04] hover:text-ink.
- Text link: text-brand-hi underline decoration-brand/30 underline-offset-[3px], hover text-brand.

CARDS / PANELS / TABS
- Default panel: bg-card + 1px border-line-2 + rounded-12px, NO shadow. Elevation is hairline-led.
- The one hero-shadow exception (final CTA terminal): rounded-xl border-line-2 bg-card shadow-[0_1px_2px_#0e15121a,0_10px_24px_-14px_#0e151233,0_44px_80px_-36px_#0e15124d]; title bar bg-paper-2 border-b border-line px-3.5 py-2.5 with three 9px HOLLOW dots (rounded-full ring-1 ring-ink/20 — monochrome, not mac traffic lights) + mono 12.5px tab toggle (MCP/curl) + ghost copy icon. Body: pre mono 13-13.5px leading-6, "$" prompt in dim.
- Code panels: border-line-2 bg-card rounded-12px; pre px-4 py-4 mono 12.5px lh 1.75 text-body; keywords = text-ink font-medium, strings = brand-hi; key params highlighted with <mark class="rounded-[3px] bg-[--brand-a12] px-1 text-brand-hi">'auto'</mark>; hover-reveal "copy" chip: border-line-2 bg-paper mono 10.5px uppercase tracking .06em text-dim.
- Tab rail: inline-flex rounded-2xl bg-paper-2 p-1; tabs rounded-xl px-3.5 py-1.5 13.5px; active gets bg-card + shadow-[0_1px_2px_#0e15121a,0_1px_1px_#0e15120f] text-ink; inactive text-muted. Width reserved with an invisible duplicate medium-weight span (no shift). Tab icons = 15px pixel-grid SVGs (2px squares).
- Product band divider (Router/Gateway): full-container strip border border-line-2 bg-paper-2 with an animated <canvas> dot grid behind (--pitch: 7px); h2 + max-w-[52ch] 13.5px muted description laid over it, each wrapped in a highlight span: background matching the band, padding 3px 7px, margin -3px, border-radius 3px, box-decoration-break: clone (text stays legible over texture).
- Selector list (integrations): rows divided by border-t border-line (last also border-b), py-5 pl-5; every row has a 2px full-height left bar (bg-line; active = bg-brand); title 17px medium, right meta 13px with 15px language icon; active row expands a 14.5px muted description; paired with a sticky code panel on the right (grid 1fr / 1.35fr, gap 56px).

DATA / MEDIA FRAMING
- Media = live data viz + real code, NOT screenshots in browser mockups.
- Heatmap matrix: grid-template-columns clamp(8.5rem,34vw,15rem) repeat(9,44px), column-gap 3px; cells 44px tall rounded-[2px] filled s1-s7; each cell is a <button> with a full aria-label ("Nova-3, English: 9.8% WER / batch, rank 13") and transition-[transform,box-shadow]. Column heads: 20x15px flag images rounded-[2.5px] with inset ring-ink/15 + 9px mono country code. Legend row uses .marker "worse/better" + min/max values ("$0.0010", "2.0%").
- Hero background: bottom-anchored decorative bar chart — SVG rect columns filled with vertical brand-blue gradients (#255498 -> #2f6ad1 -> transparent), feGaussianBlur stdDeviation=13, entrance = scaleY from 0 (transform-origin bottom), clipped inside the 1240px container. Content sits z-10 above; hero min-h calc(79svh - 64px), pb clamp(140px,19vh,235px).
- Numbers always mono + tabular, right-aligned.

FOOTER
- Container border-t border-line-2 with node circles; shell pt-20/24 pb-10; 4-col grid (gap-x-10 gap-y-12), column titles = .marker, links 13.5px text-body hover:text-brand-hi with 12px arrow-up-right in dim/45.
- Bottom row 1: status chip (ghost pill, pulsing 8px --ok dot via animate-ping) "All systems operational"; "Backed by Y Combinator" chip whose border/dot-pattern/text is revealed by a sweeping mask (--s var animates; dot pattern = radial-gradient(circle, brand 1.15px, transparent 1.45px) at 3.2px pitch, bg-clip-text over duplicate text layers); SOC2/HIPAA/GDPR badge images.
- Bottom row 2: 12.5px muted: (c) 2026 Speko <pipe in text-line-2> tagline.

SIGNATURE TOUCHES
1. Blueprint hairlines with NODE CIRCLES: every section rule gets 17x17 SVG circles (r=4.5, fill --paper, stroke ink @32%, 1px) centered on the line at both container edges (xl+ only).
2. Pixel/dot-grid motif system-wide: logo glyph, tab icons, YC-chip dot matrix, band canvas dots.
3. Box-decoration-break highlight spans behind text on textured surfaces.
4. Invisible-duplicate spans to reserve bold width in toggles.
5. Understated section titles: data sections titled with a bare 15px h2, no eyebrow, no subtitle.
6. mark-highlighting the one load-bearing token in code samples ('auto').

WHAT IT DOES NOT DO
- No dark mode (color-scheme: light; zero prefers-color-scheme rules).
- No decorative gradients: no gradient buttons, no gradient text, no mesh/aurora bgs (the only gradients are the hero bar fills and shimmer masks). No glassmorphism; backdrop-filter only on the scrolled nav pill.
- No card shadows by default; shadow appears exactly twice (CTA terminal, active tab).
- No pill badges/eyebrows above headings, no "NEW" tags, no rule-of-three feature cards, no icon-topped feature grids.
- No photos/illustrations/mascots; no browser-chrome screenshot frames; no colored traffic-light dots.
- No rounded-full buttons, no large CTAs, no all-caps display text, no italics, no serif, no font-weight above 600.
- One accent color total; semantic colors confined to data and the status dot.
- Centered layout only in hero + final CTA; all content sections left-aligned.