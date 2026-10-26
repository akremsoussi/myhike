param([string]$LinuxRoot='/home/remi/POLYTECH_INFO/4A/HIKING_APP/myhike', [string]$OutputDirectory=(Join-Path $PSScriptRoot '../docs/preuves-docker/nouvelles-mesures'))
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$repoLinux=$LinuxRoot
$vbox='C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$vmNames=@('vm-donnees','vm-metier','vm-proxy')
$log=Join-Path $OutputDirectory 'progression.txt'
function Write-ProgressLog([string]$Message) { ('{0:o} {1}' -f (Get-Date),$Message) | Add-Content -LiteralPath $log }
function Invoke-Docker([string[]]$DockerArguments) {
    & wsl.exe -d Ubuntu -u root -- docker compose -p refuges-validation --env-file "$repoLinux/.env.docker" -f "$repoLinux/docker/compose.yaml" @DockerArguments 2>&1 | Out-File -Append -LiteralPath (Join-Path $OutputDirectory 'compose.log')
    if ($LASTEXITCODE -ne 0) { throw 'Commande Compose en échec ; voir compose.log.' }
}
function Get-Health {
    try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/api/health' -TimeoutSec 2;return ($r.api -eq 'ok' -and $r.database -eq 'ok') } catch { return $false }
}
function Wait-Health {
    $limit=[Diagnostics.Stopwatch]::StartNew()
    while ($limit.Elapsed.TotalSeconds -lt 240) { if (Get-Health) {return};Start-Sleep -Milliseconds 500 }
    throw 'Le service ne répond pas après 240 secondes.'
}
function Get-Consultation {
    $body=@{email='randonneur@refuges.local';password='refuges123'} | ConvertTo-Json -Compress
    $null=Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8080/api/auth/login' -ContentType 'application/json' -Body $body -SessionVariable apiSession -TimeoutSec 30
    $values=@()
    for ($j=1;$j -le 10;$j++) {
        $watch=[Diagnostics.Stopwatch]::StartNew()
        $answer=Invoke-WebRequest -Uri 'http://127.0.0.1:8080/api/refuges?limit=20' -WebSession $apiSession -TimeoutSec 30
        $watch.Stop();$result=$answer.Content | ConvertFrom-Json
        if ($answer.StatusCode -ne 200 -or $result.total -ne 4652) {throw 'Consultation non valide.'}
        $values+=@{request=$j;elapsed_ms=$watch.Elapsed.TotalMilliseconds;http_status=[int]$answer.StatusCode;total=[int]$result.total}
    }
    return ,$values
}
function Stop-VMs {
    foreach ($vmName in $vmNames) {
        $info=& $vbox showvminfo $vmName --machinereadable
        if ($info -contains 'VMState="running"') { & $vbox controlvm $vmName acpipowerbutton 2>&1 | Out-File -Append (Join-Path $OutputDirectory 'virtualbox.log') }
    }
    $watch=[Diagnostics.Stopwatch]::StartNew()
    do {
        $remaining=@()
        foreach ($vmName in $vmNames) {if ((& $vbox showvminfo $vmName --machinereadable) -notcontains 'VMState="poweroff"') {$remaining+=$vmName}}
        if ($remaining.Count -eq 0){return};Start-Sleep -Seconds 2
    } while ($watch.Elapsed.TotalSeconds -lt 90)
    throw ('Extinction ACPI incomplète : '+($remaining -join ', '))
}
$existing=& $vbox list runningvms
if ($existing) {throw 'Des VM sont déjà en marche ; ne pas interrompre une session existante.'}
$hardware=Get-CimInstance Win32_ComputerSystem
$baseline=@{timestamp=(Get-Date).ToUniversalTime().ToString('o');physical_memory_bytes=$hardware.TotalPhysicalMemory;logical_processors=$hardware.NumberOfLogicalProcessors;wsl_before_bytes=(Get-Process -Name 'vmmemWSL' -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum}
$baseline | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $OutputDirectory 'hote.json')
$measurements=@()
try {
    Invoke-Docker @('stop')
    for ($rep=1;$rep -le 3;$rep++) {
        Write-ProgressLog "Docker répétition $rep : démarrage"
        $watch=[Diagnostics.Stopwatch]::StartNew();Invoke-Docker @('up','-d');Wait-Health;$watch.Stop()
        Start-Sleep -Seconds 8
        $memory=@();for ($sample=1;$sample -le 3;$sample++) { $memory+=(Get-Process -Name 'vmmemWSL' | Measure-Object WorkingSet64 -Sum).Sum;Start-Sleep -Seconds 1 }
        & wsl.exe -d Ubuntu -u root -- docker stats --no-stream --format '{{json .}}' refuges-validation-db-1 refuges-validation-backend-1 refuges-validation-frontend-1 | Set-Content -Encoding utf8 (Join-Path $OutputDirectory "docker-stats-r$rep.jsonl")
        $measurements+=@{deployment='Docker';repetition=$rep;boot_seconds=$watch.Elapsed.TotalSeconds;memory_host_samples_bytes=$memory;memory_scope='vmmemWSL complet, moteur Linux et autres processus WSL inclus';consultation=(Get-Consultation)}
        $measurements | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 (Join-Path $OutputDirectory 'mesures.json')
        Invoke-Docker @('stop');Write-ProgressLog "Docker répétition $rep terminée"
    }
    for ($rep=1;$rep -le 3;$rep++) {
        Write-ProgressLog "VM répétition $rep : démarrage"
        $watch=[Diagnostics.Stopwatch]::StartNew()
        foreach ($vmName in $vmNames) { & $vbox startvm $vmName --type headless 2>&1 | Out-File -Append (Join-Path $OutputDirectory 'virtualbox.log');if ($LASTEXITCODE -ne 0){throw "Démarrage VM en échec : $vmName"} }
        Wait-Health;$watch.Stop();Start-Sleep -Seconds 8
        $memory=@();for ($sample=1;$sample -le 3;$sample++) { $memory+=(Get-Process -Name 'VBoxHeadless','VirtualBoxVM' -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum;Start-Sleep -Seconds 1 }
        $measurements+=@{deployment='VM';repetition=$rep;boot_seconds=$watch.Elapsed.TotalSeconds;memory_host_samples_bytes=$memory;memory_scope='Somme WorkingSet64 des processus VBoxHeadless / VirtualBoxVM';consultation=(Get-Consultation)}
        $measurements | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 (Join-Path $OutputDirectory 'mesures.json')
        Stop-VMs;Write-ProgressLog "VM répétition $rep terminée"
    }
} finally {
    Invoke-Docker @('stop');Stop-VMs
}
Write-ProgressLog 'Mesures terminées ; tous les déploiements sont arrêtés.'
