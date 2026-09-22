# Smart Media Analyzer: today's demonstration

## Before presenting

- Keep the local frontend and backend running, and keep the existing report tab open. A browser refresh does not currently offer a report-history screen.
- Prepare a short, non-sensitive video under the app's 100 MB limit. Complete one analysis before the presentation; analysis can take several minutes.
- Keep the original video selected in the report tab if you want to demonstrate timestamp playback.
- The `Try sample` buttons show prepared demonstrations, not newly analyzed uploads. Label them honestly if used.

## Five-minute walkthrough

1. **Purpose:** “This application turns uploaded media into a searchable report, then answers questions using extracted evidence.”
2. **Upload:** Show video upload. “The backend saves the upload in Azure Blob Storage and sends the media to Azure Content Understanding.” If processing is slow, show the previously completed report; do not describe it as the new upload's result.
3. **Report:** Show the concise summary, topics, timestamps and expandable Hinglish transcript. “Recognition errors can remain; original extracted content is available for inspection.”
4. **Media questions:** With web search off, ask “What does the video say about ANC?” Show the supporting passages and timestamp citations. This question fits the saved AirPods report; adapt it for another video.
5. **Related web question:** Enable the checkbox and ask “What is dB?” Explain that, when media evidence is insufficient, Azure Foundry's web-search tool retrieves public-web information through Bing. Web answers have separate labels and source links.
6. **Scope control:** Ask “Give me a cake recipe.” For the headphone report, the app should explain that the question is unrelated and skip web search. Relevance checking is model-based, not a guarantee of perfect classification.

## Explain the architecture

React interface → local FastAPI backend → Azure Blob Storage / Azure Content Understanding → Azure AI Search → Azure Foundry agent.

The app resolves follow-up questions and checks topic relevance using the deployed Azure model. Media answers use retrieved passages. Optional web answers use a separate Foundry Responses request, not a change to the saved media agent.

## State the current limitations

- Local prototype; per-user sign-in and ownership enforcement are not implemented. Do not present it as a public multi-user service.
- External ID tenant creation is blocked by the subscription's region policy.
- Processing and web answers can take time. Uploads currently have a 100 MB limit.
- Search is keyword-based. Model answers and extracted transcripts can contain errors.
- Completed reports persist locally, but there is no user-facing report-history screen yet.

## Checks performed before this walkthrough

The running health endpoint reported verified Blob access and the Foundry agent configured. Three browser checks passed: saved-report rendering and desktop/mobile chat scrolling. Chat-control tests use simulated responses; these checks do not constitute a fresh end-to-end Azure analysis run.
