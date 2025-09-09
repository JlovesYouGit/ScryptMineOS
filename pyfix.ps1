# PowerShell function for "kill-the-chaos" Python workflow
# Add this to your PowerShell profile: $PROFILE

function pyfix {
    param(
        [string]$folder = ".",
        [switch]$SecurityOnly,
        [switch]$FormatOnly,
        [switch]$Quiet
    )
    
    $ErrorActionPreference = "Continue"
    
    if ($SecurityOnly) {
        Write-Host "🛡️  SECURITY-ONLY MODE" -ForegroundColor Cyan
        python pyfix.py $folder --security-only $(if ($Quiet) { "--quiet" })
    }
    elseif ($FormatOnly) {
        Write-Host "🧽  FORMAT-ONLY MODE" -ForegroundColor Cyan  
        python pyfix.py $folder --format-only $(if ($Quiet) { "--quiet" })
    }
    else {
        Write-Host "🚀  FULL WORKFLOW MODE" -ForegroundColor Cyan
        python pyfix.py $folder $(if ($Quiet) { "--quiet" })
    }
}

# Alternative batch-style function
function pyfix-batch {
    param([string]$folder = ".")
    
    Write-Host "🧽  FORMAT  $folder" -ForegroundColor Green
    ruff format $folder
    ruff check --fix $folder
    
    Write-Host "🔍  LINT    $folder" -ForegroundColor Yellow
    ruff check $folder
    
    Write-Host "🛡️   SECURITY" -ForegroundColor Red
    bandit -r $folder -f txt
    
    Write-Host "📦  DEPENDENCY-AUDIT" -ForegroundColor Blue
    pip-audit --desc --format=json
    
    Write-Host "🗑️   CACHE-CLEAN" -ForegroundColor Magenta
    pyclean -v $folder
    
    Write-Host "✅  DONE" -ForegroundColor Green
}

# Quick aliases
Set-Alias -Name pf -Value pyfix
Set-Alias -Name pfix -Value pyfix

Write-Host "🚀 Python Code Quality Functions Loaded!" -ForegroundColor Green
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  pyfix [folder]           # Full workflow" -ForegroundColor White
Write-Host "  pyfix -SecurityOnly      # Security only" -ForegroundColor White
Write-Host "  pyfix -FormatOnly        # Format only" -ForegroundColor White
Write-Host "  pyfix-batch [folder]     # Batch mode" -ForegroundColor White
Write-Host "  pf [folder]              # Alias for pyfix" -ForegroundColor White