$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Run-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Step $Name
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name"
    }
}

function Tool-Exists {
    param([string]$ToolName)
    return $null -ne (Get-Command $ToolName -ErrorAction SilentlyContinue)
}

Write-Host "Starting fix + validation pipeline..." -ForegroundColor Green

# -----------------------------
# Auto-fix section
# -----------------------------

if (Tool-Exists "ruff") {
    Run-Step "Formatting Python with ruff format" {
        ruff format .
    }

    Run-Step "Auto-fixing Python issues with ruff check --fix" {
        ruff check . --fix
    }
}
else {
    Write-Warning "ruff not found. Skipping Python format/lint auto-fix."
}

if (Tool-Exists "djlint") {
    Run-Step "Reformatting HTML/Jinja with djlint" {
        djlint . --reformat
    }
}
else {
    Write-Warning "djlint not found. Skipping HTML/Jinja reformat."
}

if (Tool-Exists "npx") {
    Run-Step "Auto-fixing CSS with stylelint" {
        npx stylelint "**/*.css" --fix
    }
}
else {
    Write-Warning "npx not found. Skipping CSS auto-fix."
}

# -----------------------------
# Validation section
# -----------------------------

if (Tool-Exists "ruff") {
    Run-Step "Validating Python lint with ruff check" {
        ruff check .
    }
}

if (Tool-Exists "djlint") {
    Run-Step "Validating HTML/Jinja with djlint" {
        djlint .
    }
}

if (Tool-Exists "npx") {
    Run-Step "Validating CSS with stylelint" {
        npx stylelint "**/*.css"
    }
}

if (Tool-Exists "mypy") {
    Run-Step "Running mypy type checks" {
        mypy --exclude 'migrations|tests' .
    }
}
else {
    Write-Warning "mypy not found. Skipping type checks."
}

if (Tool-Exists "pytest") {
    Run-Step "Running pytest" {
        pytest
    }
}
else {
    Write-Warning "pytest not found. Skipping tests."
}

Write-Host ""
Write-Host "All auto-fixable steps and validations completed successfully." -ForegroundColor Green