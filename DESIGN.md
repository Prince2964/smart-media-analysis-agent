# Design System: Smart Media Analysis Agent

Status: user approved the revised Stitch direction for initial implementation on 2026-09-22. See docs/STITCH_STATUS.md for the approved frame set and implementation limitations.

## 1. Visual Theme & Atmosphere
A calm, media-first research workspace for a university AI-103 demonstration. Balanced density (4/10), modest asymmetry (5/10), restrained motion (2/10). Content and its evidence take priority over metrics and decoration. Use a left-aligned home introduction and a larger report workspace beside a narrower grounded-question panel.

## 2. Color Palette & Roles
- Canvas Zinc (#FAFAFA): page background.
- Surface White (#FFFFFF): media viewer and elevated input surface.
- Charcoal Ink (#18181B): primary text and navigation.
- Secondary Zinc (#52525B): secondary text, readable metadata.
- Whisper Zinc (#E4E4E7): dividers and borders.
- Deep Teal (#24766D): sole accent, primary action, active input tab, focus and source links.
- Pale Teal (#EDF6F4): selected surfaces and evidence highlights.
Errors use charcoal text, an alert icon, and a clear border with explicit error wording; never rely on color alone. No neon, pure black, or gradient text.

## 3. Typography Rules
Use Geist for headings and body, Geist Mono for timestamps and source identifiers; sans-serif fallbacks permitted when fonts are unavailable. Desktop title 36px/42px, section heading 24px/32px, body 16px/26px, metadata 14px/20px. Heading tracking -0.025em, weights 500–650. Limit narrative text to 65ch. Responsive titles use clamp(1.75rem, 3vw, 2.25rem). No serif or Inter.

## 4. Component Stylings
- Buttons: minimum 44px tall, 10px radius, primary teal with white text; outline secondary actions. Visible focus outline, disabled labels and restrained 1px press feedback.
- Input selector: three clearly labeled adjacent controls, Upload Video / Upload Image / Paste Link. These are input modes, not decorative feature cards. Wrap vertically on narrow screens.
- Upload area: roomy dashed boundary, file requirements, browse action, selected filename and remove action. Keyboard-accessible file input; drag and drop is supplementary.
- Link input: persistent label, example format, supported-source guidance and validation below the field. Unsupported URLs get an explicit explanation; do not suggest all links work.
- Surfaces: 16px corner radius for media/input panels, 1px borders, shadows only for meaningful elevation. Report sections primarily use whitespace and dividers.
- Report: Summary, Main Topics, Transcript / Extracted Content, Important Moments, Key Information. Keep media preview and source identity visible.
- Evidence: distinguish Direct extraction, Retrieved context, Generated explanation. Citations show source and available timestamp; timestamp buttons seek only when playable media exists.
- Chat: title Ask About Your Media, persistent question label, placeholder Ask a question about this media..., Ask button. Answers include source citations. Unknown answer: I can't determine that from the provided media.
- Loading: static skeleton layout and named processing stages, accessible status text. Never invent a completion percentage.
- Empty state: a clear invitation to select a media input, with optional explicitly labeled sample demonstration.
- Error state: concise cause, retained input where safe, Retry or Choose another file.
- Completion: Processing complete label and direct transition to report and chat.
- Local mode: persistent Sample / mock mode label explaining that fixture output is not analysis of the uploaded media. Azure services must not appear connected.

## 5. Layout Principles
Desktop max-width 1440px; compact navigation rail, flexible report column and approximately 360px question panel. Use CSS Grid, 8px spacing rhythm, 24–32px panel padding. Home uses a left-aligned title and a contextual media/report preview without text overlap. No fabricated usage metrics or analytics charts.
Below 1024px put questions beneath the report. Below 768px collapse all multi-column content to a single column; convert navigation to a compact accessible menu. Minimum 44px touch targets, no horizontal overflow, no fixed-height content clipping. Use min-height: 100dvh when needed.

## 6. Motion & Interaction
User preference overrides the skill's perpetual-animation defaults: no infinite decorative loops, typewriters, floating panels, or staggered content delays. Use 120–180ms opacity/transform transitions only where useful. Respect prefers-reduced-motion. Preserve focus, keyboard navigation, and readable live status updates.

## 7. Anti-Patterns (Banned)
No generic dashboard metrics, equal feature-card triptychs, emoji icons, neon glows, oversized gradient headings, overlapping text, decorative stock photos, custom cursors, invented success statistics, fictitious Azure connection indicators, or unsupported claims that outputs came from real media analysis.

## 8. Required Screen Coverage
1. Landing / Home with one primary Start analyzing action.
2. Main dashboard with immediately visible input modes and empty workspace.
3. Video upload with selected file and validation.
4. Image upload with image preview and validation.
5. Link entry with supported-source guidance.
6. Processing with ordered stages and skeleton report.
7. Media Intelligence Report with all five required sections.
8. Transcript / content view with searchable passages and source markers.
9. Important moments with prominent timestamp controls.
10. Grounded media chat with cited response at 01:32.
11. Retrieval results showing relevant passages and no-results variant.
12. Error state with actionable retry and unsupported-link variant.
13. Empty state before media input.
14. Processing complete with report ready.
Also generate a mobile dashboard/report/chat composition. Use the same shell and components throughout.
