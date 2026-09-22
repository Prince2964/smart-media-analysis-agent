$azureCliDirectory = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
if (Test-Path -LiteralPath $azureCliDirectory) {
    $env:PATH = $azureCliDirectory + ';' + $env:PATH
}
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000





