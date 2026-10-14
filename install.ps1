# MASK installer for Windows.
#
#   $install = (Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.ps1').Content
#   Invoke-Expression $install
#
# It clones ManageAgentSkills (or fast-forwards an existing clone), then runs the program's own
# `self install` to write the `mask.cmd` launcher. Nothing is elevated, your PATH is not edited, and
# neither Python nor Git is installed for you. Running it again updates in place. MASK links skills
# with directory symlinks, so Windows needs Developer Mode or the symlink privilege.
#
#   MASK_INSTALL_DIR  where the program clone lives   (default: %LOCALAPPDATA%\mask\program)
#   MASK_BIN_DIR      where the launcher is written   (default: %LOCALAPPDATA%\mask\bin)
#   MASK_REPO         Git URL/path to clone           (default: public HTTPS Git URL)
#   MASK_CLONE_WITH_GH  1 to use an existing authenticated gh session instead
#   MASK_PYTHON       Python 3.11+ interpreter to use (default: py -3, then python)
#
# The whole script is one function called on the last line, so a download that is cut short runs nothing.
$ErrorActionPreference = 'Stop'

function Install-Mask {
    $repo = if ($env:MASK_REPO) { $env:MASK_REPO } else { 'https://github.com/MikeMarcin/ManageAgentSkills.git' }
    $dir = if ($env:MASK_INSTALL_DIR) { $env:MASK_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'mask\program' }
    $bin = if ($env:MASK_BIN_DIR) { $env:MASK_BIN_DIR } else { Join-Path $env:LOCALAPPDATA 'mask\bin' }
    $check = 'import sys; sys.exit(sys.version_info < (3, 11))'

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required. Install Git, then run this again.' }
    $python = $null
    $candidates = @()
    if ($env:MASK_PYTHON) { $candidates += , @($env:MASK_PYTHON) } else { $candidates += , @('py', '-3'); $candidates += , @('python') }
    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $rest = @($candidate | Select-Object -Skip 1)
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            & $exe @rest -c $check 2>$null
            if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
        }
    }
    if (-not $python) { throw 'Python 3.11 or newer is required (looked for py -3 and python). Set MASK_PYTHON to choose one.' }
    $exe = $python[0]
    $rest = @($python | Select-Object -Skip 1)

    if (Test-Path (Join-Path $dir '.git')) {
        $verb = 'Updated'
        $before = (git -C $dir rev-parse --short HEAD)
        Write-Host "Updating MASK in $dir"
        # Only a clean fast-forward: local work in the clone is never discarded.
        git -C $dir pull --quiet --ff-only
        if ($LASTEXITCODE -ne 0) { throw "Could not fast-forward $dir. Resolve it with Git, or remove the directory and run this again." }
    } elseif (Test-Path $dir) {
        throw "$dir exists and is not a MASK clone. Move it away, or set MASK_INSTALL_DIR."
    } else {
        $verb = 'Installed'
        $before = $null
        Write-Host "Installing MASK into $dir"
        New-Item -ItemType Directory -Force -Path (Split-Path $dir) | Out-Null
        if ($env:MASK_CLONE_WITH_GH -ne '1') {
            git clone --quiet $repo $dir
            if ($LASTEXITCODE -ne 0) { throw "Could not clone $repo. Check its address and your Git credentials." }
        } else {
            if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
                throw "GitHub CLI is required for the authenticated MASK checkout. Install gh and run 'gh auth login', or set MASK_REPO."
            }
            gh repo clone MikeMarcin/ManageAgentSkills $dir -- --quiet
            if ($LASTEXITCODE -ne 0) { throw "Could not clone the authenticated MASK checkout. Run 'gh auth status', or set MASK_REPO." }
        }
    }

    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    & $exe @rest (Join-Path $dir 'mask.py') self install --bin-dir $bin | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "The launcher could not be written to $bin." }
    $launcher = Join-Path $bin 'mask.cmd'
    $after = (git -C $dir rev-parse --short HEAD)
    if ($verb -eq 'Updated' -and $before -eq $after) {
        Write-Host "Already up to date: $(& $launcher --version) ($after) at $launcher"
    } else {
        $span = if ($before) { "$before -> $after" } else { $after }
        Write-Host "$verb $(& $launcher --version) ($span) at $launcher"
    }

    $mask = $launcher
    if (($env:PATH -split ';') -contains $bin) {
        $mask = 'mask'
    } else {
        Write-Host ''
        Write-Host "$bin is not on your PATH. To add it for your user:"
        Write-Host "  [Environment]::SetEnvironmentVariable('PATH', `"$bin;`" + [Environment]::GetEnvironmentVariable('PATH', 'User'), 'User')"
    }
    Write-Host ''
    Write-Host 'Next:'
    Write-Host "  $mask tap agentskills https://github.com/MikeMarcin/AgentSkills.git       # approve a tap"
    Write-Host "  cd your-project; $mask install implement-rfc                              # add a skill"
    Write-Host "  $mask update                                                              # later: update MASK and fetch taps"
    Write-Host "  $mask self uninstall                                                      # remove the launcher and see what else to delete"
}

Install-Mask
