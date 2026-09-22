# Stitch design review

Project: https://stitch.withgoogle.com/projects/4653372579633965581

Verdict: useful first draft; revisions needed before approval and frontend implementation.

## Review scope
Reviewed the canvas overview and accessible content of all four generated screen compositions: Ingestion Hub & Workspace Home, Pipeline Processing & Verification Audit, Mobile Intelligence & Chat View, and Media Intelligence Report & Grounded Chat. A design-system board is also present. This is a design/content review, not a runtime, full-resolution accessibility, responsive overflow, or click-behavior test. Stitch's claim of a complete responsive suite is not verification.

## What works
- Three media input labels are prominent.
- Desktop report and adjacent chat support the core journey.
- Report includes summary, topics, transcript, moments and extracted information.
- Timestamp citations and an unsupported-question refusal are represented.
- Sample / mock mode and Azure not connected labels are present.
- Neutral surfaces and teal primary actions broadly match the proposed direction.

## Required changes, in priority order

1. Remove invented implementation and reliability claims. The report names Whisper-v3 / ViT-L-14 / Claude-3.5-Sonnet, and processing names text-embedding-3-small. These are not configured project services. Remove fabricated latency, confidence percentages, 100% timestamp grounding, SHA-256 sealing, and deterministic-answer claims. Show plain sample status. Mock labeling does not make these appropriate descriptions of the planned implementation.
2. Separate mutually exclusive states. Processing shows Analysis Pipeline Complete while Stage 3 is at 74% and later stages are pending. Home shows active errors alongside its initial empty state. Mobile displays an unsupported-link error above a completed report without explaining which source failed. Create separate selectable state designs with a clear transition from input to processing to completion or failure.
3. Complete modality coverage. Four compositions do not demonstrate all requested journeys. Add selected video with filename/remove controls, image preview and OCR/object report, and a supported-link success flow. Add a distinct welcoming landing view and processing-failure/retry state. Existing report sections may share a page; 14 separate routes are unnecessary.
4. Correct link support copy. The design promises YouTube/Vimeo and verified university streams, although no adapters have been implemented. Show only explicitly supported demo sources until actual adapters are tested. Remove real-looking invented university URLs and universal closed-caption assumptions.
5. Simplify the product language and navigation. Replace Ingestion Hub, diagnostic media, synchronous verification, provenance safe-mode, tokenization, and fault flags with Upload media, Analyze, Processing, Sources, and clear error messages. Remove unnecessary lab terminal, account controls, vector-store controls and audit infrastructure from the main journey. The product analyzes user media; it is not restricted to academic lecture repositories.
6. Align desktop/mobile content and visual tokens. Use one shared fixture: mobile labels 01:32 both Introduction and Pricing Model Initialization and uses different duration/content from desktop. Remove mobile confidence scores and LIVE STREAM labeling for an uploaded recording. The design board adds a blue tertiary accent and JetBrains Mono rather than the proposed single-teal/Geist Mono system; reconcile tokens before export.
7. Strengthen evidence presentation. Retrieved passages are source evidence, not generated explanations. Avoid classifying an indexed source chunk as Generated explanation in retrieval results. Keep generated explanation attached to the answer, cite the underlying source, and retain the exact fallback: I can't determine that from the provided media.

## Verification after revision/export
Inspect screens at readable size; verify minimum 44px targets, labels beyond placeholders, keyboard focus, contrast, mobile overflow and navigation, actual timestamp seek behavior, input validation, and state transitions. None of these behaviors is proven by the current mockups or Stitch's completion message.
