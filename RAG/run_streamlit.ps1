param(
    [int]$Port = 8501
)

# Run Streamlit with project root on PYTHONPATH
Set-Location -Path (Resolve-Path -LiteralPath .) 
$root = (Get-Location).Path
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = $root

Write-Output "Starting Streamlit on port $Port (PYTHONPATH=$env:PYTHONPATH)"
& .\.venv\Scripts\python.exe -m streamlit run src/ui/app.py --server.port $Port --server.headless true
