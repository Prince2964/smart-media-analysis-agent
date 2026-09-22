# API-key branch
See the API-key migration section in README.md. API-key mode is active on this laptop. Storage upload/read/delete and the AI services have been live-verified. No az login is needed in this mode. The instructions below also cover the preserved CLI mode.

# Run the project on your computer

The backend automatically loads `backend/.env` on startup. The existing Azure
endpoints and deployment names are already configured on this computer.
Restart the backend after editing this file. Process environment settings take
precedence over the file. The frontend does not receive this configuration.

The saved Foundry agent `smart-media-analysis-agent` has two app roles:
`FOUNDRY_AGENT_VERSION=2` answers only from retrieved media passages;
`FOUNDRY_WEB_AGENT_VERSION=3` has the Web Search tool attached and handles
opted-in web fallback. Open version 3 in Foundry to inspect its tool and instructions.
The app calls that saved version, rather than supplying a web tool on each request.
Only the resolved question is passed to web research. Video citations and web
citations remain separate. On a different project, configure equivalent versions.

## First-time setup for teammates (PowerShell, project root)

Install Python 3.12+, Node.js 20.19+ or 22.12+, and Azure CLI first.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
Copy-Item backend/.env.example backend/.env
az login
Set-Location frontend
npm.cmd ci
Set-Location ..
```

Only copy the example when `backend/.env` does not already exist. It contains
the team's resource endpoints, not secrets. Edit it if using different resources.
In CLI mode, each teammate must sign in with an account granted access to the team's Azure
resources. Service-principal mode instead uses the configured application identity. `.env` does not grant access. Azure firewall rules must also permit
their network. Do not share account passwords or CLI token caches.

## Start each day

First terminal, from the project root:

```powershell
.\start-azure-storage.ps1
```

Alternatively, from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Second terminal:

```powershell
Set-Location frontend
npm.cmd run dev -- --port 5173
```

Open http://127.0.0.1:5173. Keep both terminals running. Run `az login` again
if Azure reports an expired login. The default mode uses Azure CLI authentication. For running without personal login,
see the service-principal and managed-identity setup in README.md. All Azure
integrations use AZURE_AUTH_MODE; arbitrary API key variables are not consumed.

`backend/.env` is ignored by Git; never put secrets in frontend `VITE_*` variables.
Completed reports are saved locally in `.local/jobs`, so different computers do
not automatically share their report libraries. This setup runs a local copy;
a shared public website still requires deployment and access controls.

For an offline fixture-only demo, set `BACKEND_LOAD_ENV=false`,
`PROCESSING_MODE=mock`, `STORAGE_MODE=discard`, and unset `AZURE_SEARCH_ENDPOINT`
in the backend process environment before starting it.
