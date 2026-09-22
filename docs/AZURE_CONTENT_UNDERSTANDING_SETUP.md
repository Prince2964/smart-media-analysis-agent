# Next manual checkpoint: Content Understanding

Why: extract actual image/video content rather than returning prepared fixtures.
Content Understanding requires a Microsoft Foundry resource. The agent integration
will be a later step; creating this resource does not connect an agent automatically.

Read-only CLI checks on 2026-09-22 found no existing Cognitive Services accounts in
the selected subscription. Its allowed region policy lists UAE North, Southeast Asia,
Central India, Austria East, and Malaysia West. Southeast Asia is the overlap with
the documented Content Understanding supported region list. Resource deployment and
model quota still need to pass Azure's validation; policy allowance is not a quota guarantee.

Manual steps:
1. In Azure Portal create a Microsoft Foundry resource (not a standalone Azure OpenAI resource).
2. Select Azure for Students and your existing project resource group.
3. Select Southeast Asia. Storage can remain in UAE North.
4. Choose an available resource name and enter it yourself; no resource name or endpoint is assumed.
5. If prompted for a project, choose a project name for this app.
6. Share the creation form if it requests additional options such as pricing or networking,
   so we can verify the actual available settings before you create it.
7. Review + create, then Create after validation succeeds.

After creation, provide only actual resource name, resource group, region, and
service endpoint copied from the portal. No keys, tokens, or connection strings.
Say done. We will then inspect available model deployments/quota and guide the
required Content Understanding model-default configuration and Entra role setup.
Do not fabricate deployments or enable actual analysis before that setup is tested.

References checked 2026-09-22:
- https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/how-to/create-multi-service-resource
- https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/language-region-support
- https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/quickstart/use-rest-api

## Verified resource checkpoint
Read-only Azure inspection confirmed:
- Resource: media-analyzer-13-resource
- Kind: AIServices
- Region: southeastasia
- Resource group: rg-mayank3230.beai24-4125
- Content Understanding endpoint: https://media-analyzer-13-resource.services.ai.azure.com/
- Project name from user's portal screenshot: media-analyzer-13
- Model deployment list: empty.
- Authenticated GET defaults (2025-11-01): DefaultsNotSet.

Next manual action: open Content Understanding Studio settings, Add resource,
select this existing resource, enable autodeployment for required models when no
 defaults exist, then Next/Save. Report quota or deployment errors. After done,
read actual deployments/defaults again and test extraction before marking connected.
No model deployment or default mapping has been created by this agent.

## Image extraction verification
User configured completion aliases to gpt-5-mini via PATCH defaults.
Live test: prebuilt-imageSearch, API 2025-11-01, generated PNG with text
SMART MEDIA TEST / Workshop starts at 10:30 AM. / Room 204.
Result Succeeded; Summary correctly included the time and room number.
Reported model usage: 223 input tokens, 68 output tokens.
Raw generated-test result: .local/cu-image-check.json (ignored by source control).
The first test using prebuilt-image failed with an analyzer fields_schema validation
error; use prebuilt-imageSearch for the tested path.
This verifies only direct image extraction. Frontend reports remain mock; video,
normalization, AI Search retrieval, and Foundry Agent integration are not verified.
