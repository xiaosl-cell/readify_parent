[CmdletBinding()]
param(
    [switch]$SkipInfra,
    [switch]$SkipAgi,
    [switch]$SkipServer,
    [switch]$SkipFrontend,
    [switch]$SkipAdmin,
    [switch]$SkipEval,
    [switch]$RebuildServer
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSCommandPath
Set-Location $repoRoot

function Resolve-DockerCompose {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker) {
        & docker compose version 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ FilePath = "docker"; Prefix = @("compose") }
        }
    }

    $dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
    if ($dockerCompose) {
        return @{ FilePath = "docker-compose"; Prefix = @() }
    }

    return $null
}

function Wait-ForPort {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSec = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-NetConnection -ComputerName $HostName -Port $Port -InformationLevel Quiet) {
            return $true
        }
        Start-Sleep -Seconds 2
    }

    return $false
}

function Get-CondaEnvPython {
    param([string]$EnvName)

    $candidates = @()
    if ($env:CONDA_PREFIX -and (Split-Path -Leaf $env:CONDA_PREFIX) -eq $EnvName) {
        $candidates += (Join-Path $env:CONDA_PREFIX "python.exe")
    }

    if ($env:CONDA_EXE) {
        $condaExe = $env:CONDA_EXE
        $condaRoot = Split-Path -Parent $condaExe
        $condaBase = Split-Path -Parent $condaRoot
        $candidates += (Join-Path $condaBase "envs\$EnvName\python.exe")
    }

    if ($env:USERPROFILE) {
        $candidates += (Join-Path $env:USERPROFILE "miniconda3\envs\$EnvName\python.exe")
        $candidates += (Join-Path $env:USERPROFILE "anaconda3\envs\$EnvName\python.exe")
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Start-CmdWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory
    )

    $fullCommand = "title $Title && $Command"
    if ($WorkingDirectory) {
        Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", $fullCommand) -WorkingDirectory $WorkingDirectory | Out-Null
    } else {
        Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", $fullCommand) | Out-Null
    }
}

function Get-AgiCommand {
    param([string]$Root)

    if ($env:READIFY_AGI_COMMAND) {
        return $env:READIFY_AGI_COMMAND
    }

    $venvPython = Join-Path $Root "readify_agi\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return ('"{0}" main.py' -f $venvPython)
    }

    $condaPython = Get-CondaEnvPython -EnvName "readify_agi"
    if ($condaPython) {
        return ('"{0}" main.py' -f $condaPython)
    }

    return "python main.py"
}

function Get-NpmCommand {
    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmCmd) {
        return $npmCmd.Source
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm -and $npm.CommandType -eq "Application") {
        return $npm.Source
    }

    return "npm"
}

function Get-ServerCommand {
    param(
        [string]$Root,
        [switch]$ForceBuild
    )

    $serverRoot = Join-Path $Root "readify_server"
    $mvnCmd = "mvn"
    $command = ('cd /d "{0}" && ' -f $serverRoot)
    if ($ForceBuild) {
        $command += ('call {0} clean && call {0} package -DskipTests && ' -f $mvnCmd)
    } else {
        $command += ('call {0} package -DskipTests && ' -f $mvnCmd)
    }
    $command += 'java -Dfile.encoding=UTF-8 -jar target\readify-0.0.1-SNAPSHOT.jar'

    return $command
}

function Get-EvalCommand {
    param([string]$Root)

    $evalRoot = Join-Path $Root "readify_eval\backend"

    $venvPython = Join-Path $evalRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return ('cd /d "{0}" && "{1}" run.py' -f $evalRoot, $venvPython)
    }

    $condaPython = Get-CondaEnvPython -EnvName "readify-eval"
    if ($condaPython) {
        return ('cd /d "{0}" && "{1}" run.py' -f $evalRoot, $condaPython)
    }

    return ('cd /d "{0}" && python run.py' -f $evalRoot)
}

Write-Host "Readify one-click starter"

if (-not $SkipInfra) {
    $compose = Resolve-DockerCompose
    if ($compose) {
        Write-Host "Starting infra (nacos/mysql/milvus)..."
        $composeArgs = @()
        $composeArgs += $compose.Prefix
        $composeArgs += @("-f", "infra\docker-compose.yml", "up", "-d")
        & $compose.FilePath @composeArgs

        if (-not (Wait-ForPort -HostName "localhost" -Port 8848 -TimeoutSec 120)) {
            Write-Warning "Nacos port 8848 not ready yet. AGI/Server may fail if config is missing."
        }
    } else {
        Write-Warning "Docker Compose not found. Skipping infra startup."
    }
}

if (-not $SkipAgi) {
    $agiRoot = Join-Path $repoRoot "readify_agi"
    $agiCommand = Get-AgiCommand -Root $repoRoot
    Start-CmdWindow -Title "readify-agi" -Command ('cd /d "' + $agiRoot + '" && ' + $agiCommand)
}

if (-not $SkipServer) {
    $serverCommand = Get-ServerCommand -Root $repoRoot -ForceBuild:$RebuildServer
    Start-CmdWindow -Title "readify-server" -Command $serverCommand
}

if (-not $SkipFrontend) {
    $frontendRoot = Join-Path $repoRoot "readify_frontend"
    $npmCommand = Get-NpmCommand
    $nodeModulesPath = Join-Path $frontendRoot "node_modules"
    if (Test-Path $nodeModulesPath) {
        $frontendCommand = ('call "' + $npmCommand + '" run dev')
    } else {
        $frontendCommand = ('call "' + $npmCommand + '" install && call "' + $npmCommand + '" run dev')
    }
    Start-CmdWindow -Title "readify-frontend" -Command $frontendCommand -WorkingDirectory $frontendRoot
}

if (-not $SkipAdmin) {
    $adminRoot = Join-Path $repoRoot "readify_admin"
    $npmCommand = Get-NpmCommand
    $nodeModulesPath = Join-Path $adminRoot "node_modules"
    if (Test-Path $nodeModulesPath) {
        $adminCommand = ('call "' + $npmCommand + '" run dev')
    } else {
        $adminCommand = ('call "' + $npmCommand + '" install && call "' + $npmCommand + '" run dev')
    }
    Start-CmdWindow -Title "readify_admin" -Command $adminCommand -WorkingDirectory $adminRoot
}

if (-not $SkipEval) {
    $evalCommand = Get-EvalCommand -Root $repoRoot
    Start-CmdWindow -Title "readify-eval-backend" -Command $evalCommand

    # Eval frontend - static HTML served via Python http.server on port 5175
    $evalFrontendRoot = Join-Path $repoRoot "readify_eval\frontend"
    $evalFrontendPython = Get-CondaEnvPython -EnvName "readify-eval"
    if (-not $evalFrontendPython) {
        $evalFrontendPython = "python"
    }
    $evalFrontendCommand = ('cd /d "{0}" && "{1}" -m http.server 5175' -f $evalFrontendRoot, $evalFrontendPython)
    Start-CmdWindow -Title "readify-eval-frontend" -Command $evalFrontendCommand
}

Write-Host "Done. Service windows should be opening now."

