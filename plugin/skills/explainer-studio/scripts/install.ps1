# Install or update the explainer-studio command for this user to the latest release, then install what videos need
# (explainer-studio setup). Safe to run again. Never needs administrator rights.
#
#   powershell -ExecutionPolicy Bypass -File install.ps1      (from the skill folder)
#   irm <url>/install.ps1 | iex
#
# $env:EXPLAINER_STUDIO_SOURCE overrides where the package comes from, for example a local checkout during
# development. $env:UV_NO_MODIFY_PATH = 1 leaves the user PATH alone.

$Repo = 'heptameta/heptabase-explainer-studio'  # written by scripts/release.py
$DefaultSource = ''  # empty: the latest release; a dev build's snapshot writes its folder here
$script:Problem = $null

function Stop-Install([string] $Message) { $script:Problem = $Message }

function Install-ExplainerStudio {
    $source = if ($env:EXPLAINER_STUDIO_SOURCE) { $env:EXPLAINER_STUDIO_SOURCE } else { $DefaultSource }

    Write-Host "`n== uv (Python tool manager)"
    $candidates = @("$env:USERPROFILE\.local\bin\uv.exe", "$env:USERPROFILE\.cargo\bin\uv.exe")
    $uv = (Get-Command uv -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if (-not $uv) { $uv = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1 }
    if (-not $uv) {
        Write-Host 'installing uv into your user profile (astral.sh/uv)'
        # in a child shell: the uv installer may end the session that runs it
        $shell = (Get-Process -Id $PID).Path
        & $shell -NoProfile -ExecutionPolicy Bypass -Command 'irm https://astral.sh/uv/install.ps1 | iex'
        if ($LASTEXITCODE -ne 0) { return Stop-Install 'the uv installer failed (see the messages above)' }
        $uv = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
        if (-not $uv) { return Stop-Install 'uv was installed but cannot be found; open a new terminal and run this script again' }
    }
    Write-Host "uv: $uv ($(& $uv --version))"

    Write-Host "`n== git"
    # ManimGL (and the default package source) are fetched with git
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return Stop-Install ('git is missing. Install it without administrator rights with ' +
            '"winget install --id Git.Git -e --scope user" (or from https://git-scm.com/download/win), ' +
            'then open a new terminal and run this script again')
    }
    Write-Host "git: $(git --version)"

    if (-not $source) {
        Write-Host "`n== the latest release"
        # the highest v<major>.<minor>.<patch> tag
        $env:GIT_TERMINAL_PROMPT = '0'
        $latest = git ls-remote --tags --refs "https://github.com/$Repo.git" 'v*' 2>$null |
            ForEach-Object { if ($_ -match 'refs/tags/v(\d+\.\d+\.\d+)$') { [version] $Matches[1] } } |
            Sort-Object | Select-Object -Last 1
        if (-not $latest) { return Stop-Install "cannot read the releases of github.com/$Repo; check the network and run this script again" }
        Write-Host "explainer-studio $latest"
        $source = "git+https://github.com/$Repo@v$latest"
    }

    Write-Host "`n== explainer-studio"
    if (Test-Path -LiteralPath $source -PathType Container) {
        # a local checkout: rebuild it every time, since its version number does not change between edits
        $uri = [System.Uri]::new((Resolve-Path -LiteralPath $source).Path).AbsoluteUri
        & $uv tool install --python 3.13 --force --reinstall-package explainer-studio "explainer-studio @ $uri"
    } else {
        & $uv tool install --python 3.13 --force "explainer-studio @ $source"
    }
    if ($LASTEXITCODE -ne 0) { return Stop-Install 'uv could not install explainer-studio (see the messages above)' }
    $bin = (& $uv tool dir --bin | Out-String).Trim()
    # explainer-studio.exe on Windows; the plain name lets PowerShell on macOS and Linux run this script too
    $studio = @('explainer-studio.exe', 'explainer-studio') | ForEach-Object { Join-Path $bin $_ } |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $studio) { return Stop-Install "the install finished but explainer-studio is missing from $bin" }
    $separator = [System.IO.Path]::PathSeparator
    if (($env:Path -split $separator) -notcontains $bin) {
        if (-not $env:UV_NO_MODIFY_PATH) {
            & $uv tool update-shell | Out-Null
            Write-Host "added $bin to your user PATH; new terminals find explainer-studio"
        }
        $env:Path = "$bin$separator$env:Path"
    }

    Write-Host "`n== explainer-studio setup (ffmpeg, LaTeX, fonts, map data, a test render)"
    & $studio setup
    if ($LASTEXITCODE -ne 0) { return Stop-Install "setup did not finish: fix the problems above, then run: $studio setup" }
    Write-Host "`ninstalled: $(& $studio --version) at $studio"
}

# the function's output (the native commands' progress) goes straight to the screen
Install-ExplainerStudio | Out-Host
if ($script:Problem) {
    Write-Host "error: $script:Problem" -ForegroundColor Red
    # `exit` would close the window of someone who ran `irm ... | iex`; only a script file reports an exit code
    if ($PSCommandPath) { exit 1 }
}
