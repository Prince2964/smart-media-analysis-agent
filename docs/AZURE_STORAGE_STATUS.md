# Blob Storage setup checkpoint

User-confirmed configuration:
- Storage account: `mediaanylyzer13`
- Blob endpoint: `https://mediaanylyzer13.blob.core.windows.net/`
- Container: `media-uploads` (private)
- Region: UAE North
- Development identity: user's Microsoft Entra account
- Container role: Storage Blob Data Contributor (confirmed in portal screenshot)
- Portal upload: successful; uploaded image visible using Entra authentication.

Verified on 2026-09-22:
- Azure CLI installed; signed into enabled Azure for Students subscription.
- SDK uploaded a unique test blob, read identical bytes, and deleted that test blob.
- Live API accepted a generated PNG, stored identical bytes, and returned an explicitly mock report.
- The API test blob was removed. User-uploaded files were untouched.
- 22 backend tests, 3 browser tests, and frontend production build passed.

Start the backend with `./start-azure-storage.ps1` from PowerShell (stop any existing
backend on port 8000 first). This configures non-secret environment variables and
Azure CLI PATH. Credentials stay in the Azure CLI credential store.

Storage and processing modes are independent. Default STORAGE_MODE=discard does
not send uploads to Azure. STORAGE_MODE=azure persists validated uploads. Reports
and questions remain fixtures under PROCESSING_MODE=mock. Health reports verified
Blob access separately from the still-unconnected end-to-end AI pipeline.

The server is for local development only. It has no user authentication or ownership
checks. Do not expose it publicly. Blobs persist after server restarts, while job
records are in memory only. No retention job is configured.

The next manual checkpoint is AZURE_CONTENT_UNDERSTANDING_SETUP.md.

Latest verification: after the user saved the updated IP firewall rule, SDK
upload/read/delete passed again. Backend restarted in azure-image mode.
The integrated upload API stored matching image bytes and Content Understanding
returned a non-mock description containing the expected Room 204 text. Real-media
fixture chat was correctly blocked (409). Only the generated test blob was removed.
