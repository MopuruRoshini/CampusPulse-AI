$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
if (!(Test-Path (Join-Path $backend '.env'))) { Copy-Item (Join-Path $backend '.env.example') (Join-Path $backend '.env') }
if (!(Test-Path (Join-Path $backend '.venv'))) { py -3.11 -m venv (Join-Path $backend '.venv') }
$python = Join-Path $backend '.venv\Scripts\python.exe'
& $python -m pip install -r (Join-Path $backend 'requirements.txt')
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$backend'; & '$python' run.py"
Set-Location $frontend
npm install
npm run dev
