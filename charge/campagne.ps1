[CmdletBinding()]
param(
    [ValidateSet('Check', 'Calibration', 'Campaign')][string]$Mode = 'Campaign',
    [string]$Jmeter = "$env:USERPROFILE\Downloads\apache-jmeter-5.6.3\bin\jmeter.bat",
    [string]$Python = '',
    [string]$TargetHost = '127.0.0.1',
    [ValidateRange(1,65535)][int]$Port = 8080,
    [ValidateRange(1,600)][int]$RampSeconds = 10,
    [ValidateRange(60,3600)][int]$SteadySeconds = 60,
    [ValidateRange(1,5)][int]$Repetitions = 2,
    [ValidateRange(0,120)][int]$PauseSeconds = 10,
    [Alias('Users')][ValidateSet(1,5,10,25,50,100)][int[]]$UserLevels = @(1,5,10,25,50,100),
    [int[]]$CalibrationUsers = @(20,100),
    [string]$ResultsDirectory = '',
    [switch]$ResetDatabase,
    [switch]$OtherDeploymentStopped
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$compose = @('compose', '--env-file', (Join-Path $root '.env.docker'), '-f', (Join-Path $root 'docker/compose.yaml'))
if (-not $Python) {
    $bundled = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { $Python = $bundled } else { $Python = 'python' }
}
if (-not $ResultsDirectory) { $ResultsDirectory = Join-Path $PSScriptRoot 'resultats' }
$ResultsDirectory = [IO.Path]::GetFullPath($ResultsDirectory)
$Jmeter = [IO.Path]::GetFullPath($Jmeter)
if (-not (Test-Path -LiteralPath $Jmeter)) { throw "JMeter introuvable : $Jmeter" }
if ($Jmeter -match '["&|<>^%]') { throw 'Chemin JMeter contenant des caracteres shell non pris en charge.' }
& $Python --version
if ($LASTEXITCODE -ne 0) { throw 'Python est necessaire pour les statistiques.' }
if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    $javaFolders = @(Get-ChildItem -LiteralPath "$env:ProgramFiles\Java" -Directory -ErrorAction SilentlyContinue)
    $javaHome = $javaFolders | Where-Object { Test-Path (Join-Path $_.FullName 'bin/java.exe') } | Select-Object -First 1
    if (-not $javaHome) { throw 'Java introuvable : installer Java ou configurer JAVA_HOME.' }
    $env:JAVA_HOME = $javaHome.FullName
    $env:Path = (Join-Path $javaHome.FullName 'bin') + ';' + $env:Path
}
& java -version
if ($LASTEXITCODE -ne 0) { throw 'Java introuvable.' }
$accounts = Join-Path $PSScriptRoot 'comptes.csv'
$plan = Join-Path $PSScriptRoot 'plan.jmx'
$calibration = Join-Path $PSScriptRoot 'plan_etalonnage.jmx'
foreach ($file in @($accounts, $plan, $calibration)) {
    if (-not (Test-Path -LiteralPath $file)) { throw "Fichier manquant : $file" }
}
if (@(Import-Csv $accounts).Count -lt 20) { throw 'Au moins 20 comptes distincts sont requis.' }
foreach ($file in @($plan, $calibration)) { [xml]$null = Get-Content -LiteralPath $file -Raw }
if ($Mode -eq 'Check') { Write-Host 'Configuration et fichiers valides. Aucune charge ni reinitialisation.'; return }
if (-not $OtherDeploymentStopped) { throw 'Arreter les VMs, puis ajouter -OtherDeploymentStopped.' }
$vmProcesses = @(Get-Process VBoxHeadless,VirtualBoxVM,vmware-vmx,qemu-system-x86_64 -ErrorAction SilentlyContinue)
if ($vmProcesses.Count -gt 0) { throw 'Un processus VM est actif. Arreter les VMs avant de mesurer.' }
$runningJmeter = @(Get-CimInstance Win32_Process -Filter "Name='java.exe'" | Where-Object { $_.CommandLine -match 'ApacheJMeter' })
if ($runningJmeter.Count -gt 0) { throw 'Un autre JMeter est actif. Le fermer avant de mesurer.' }
if ($Mode -eq 'Campaign' -and -not $ResetDatabase) {
    throw 'Le protocole impose une base reinitialisee. Ajouter -ResetDatabase (sauvegarde automatique).'
}
New-Item -ItemType Directory -Force $ResultsDirectory | Out-Null
$id = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$levels = if ($Mode -eq 'Calibration') { $CalibrationUsers } else { $UserLevels }
if (@($levels | Where-Object { $_ -lt 1 -or $_ -gt 1000 }).Count -gt 0) { throw 'Palier d etalonnage invalide.' }
$prefix = if ($Mode -eq 'Calibration') { 'etalonnage-dk' } else { 'dk' }
$session = Join-Path $ResultsDirectory "$prefix-$id"
New-Item -ItemType Directory -Path $session | Out-Null
$gitCommit = (& git -C $root rev-parse HEAD) -join ''
$cpuCount = [Environment]::ProcessorCount
$manifest = [ordered]@{
    started_utc = [DateTime]::UtcNow.ToString('o'); mode = $Mode; deployment = 'docker'
    target = "http://${TargetHost}:$Port"; git_commit = $gitCommit
    users = @($levels); ramp_seconds = $RampSeconds
    steady_seconds = $SteadySeconds; run_seconds = $RampSeconds + $SteadySeconds + 2
    repetitions = $Repetitions; logical_processors = $cpuCount
    db_reset = [bool]$ResetDatabase; other_deployment_stopped_declared = [bool]$OtherDeploymentStopped
    hashes = @{}; completion = 'running'
}
foreach ($file in @($plan,$calibration,$accounts,(Join-Path $root 'donnees/schema.sql'),(Join-Path $root 'donnees/peuplement.sql'))) {
    $manifest.hashes[[IO.Path]::GetFileName($file)] = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
}
$manifestPath = Join-Path $session 'configuration.json'
function Save-Manifest { $manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $manifestPath }
Save-Manifest
function Docker-Checked([string[]]$DockerArguments) {
    & docker @DockerArguments
    if ($LASTEXITCODE -ne 0) { throw "Docker a echoue : $($DockerArguments[0..([Math]::Min(2,$DockerArguments.Length-1))] -join ' ')" }
}
function Reset-TestDatabase([int]$Repetition) {
    # Backups are intentionally outside versioned measurement results: they may contain private data.
    $backupDirectory = Join-Path $root '.charge-backups'
    New-Item -ItemType Directory -Force $backupDirectory | Out-Null
    $backupPath = Join-Path $backupDirectory "avant-$id-r$Repetition.sql"
    Docker-Checked ($compose + @('exec','-T','db','sh','-c','MYSQL_PWD=$MYSQL_PASSWORD mysqldump --no-tablespaces --single-transaction --default-character-set=utf8mb4 --user=$MYSQL_USER $MYSQL_DATABASE > /tmp/charge-before-reset.sql'))
    Docker-Checked ($compose + @('cp','db:/tmp/charge-before-reset.sql',$backupPath))
    if ((Get-Item $backupPath).Length -lt 100) { throw 'Sauvegarde SQL vide ou incomplete.' }
    Docker-Checked ($compose + @('stop','frontend','backend','db'))
    Docker-Checked ($compose + @('rm','-f','db'))
    # Exact Compose volume; uploads is never removed.
    Docker-Checked -DockerArguments @('volume','rm','refuges_mysql_data')
    $boot = [Diagnostics.Stopwatch]::StartNew()
    Docker-Checked ($compose + @('up','-d','--wait'))
    $boot.Stop()
    [ordered]@{ repetition=$Repetition; boot_seconds=$boot.Elapsed.TotalSeconds; backup=$backupPath } |
        ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $session "demarrage-r$Repetition.json")
}
function Run-Jmeter([string[]]$JmeterArguments, [string]$LogPrefix, [int]$TimeoutSeconds) {
    foreach ($argument in $JmeterArguments) {
        if ($argument -match '["&|<>^%\r\n]') { throw "Argument shell non pris en charge : $argument" }
    }
    $quoted = ($JmeterArguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $commandLine = '/d /s /c ""' + $Jmeter + '" ' + $quoted + '"'
    $process = Start-Process -FilePath $env:ComSpec -ArgumentList $commandLine -PassThru -WindowStyle Hidden -RedirectStandardOutput "$LogPrefix.stdout.log" -RedirectStandardError "$LogPrefix.stderr.log"
    # Keep the OS handle open: Windows PowerShell otherwise loses ExitCode on fast exits.
    $null = $process.Handle
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        & taskkill /PID $process.Id /T /F | Out-Null
        throw "JMeter a depasse le delai de securite. Voir $LogPrefix.stdout.log"
    }
    if ($process.ExitCode -ne 0) {
        Get-Content "$LogPrefix.stdout.log" -Tail 15 | Write-Host
        Get-Content "$LogPrefix.stderr.log" -Tail 15 | Write-Host
        throw "JMeter a echoue (code $($process.ExitCode))."
    }
}
function Start-Monitor([string]$Destination, [string]$StopFile) {
    $ids = @(& docker @compose ps -q)
    if ($LASTEXITCODE -ne 0 -or $ids.Count -ne 3) { throw 'Les trois conteneurs doivent etre demarres.' }
    $dbId = (& docker @compose ps -q db) -join ''
    Start-Job -ArgumentList $Destination,$StopFile,$ids,$dbId,$cpuCount -ScriptBlock {
        param($destination,$stopFile,$containerIds,$dbId,$cpuCount)
        $lastCpu = $null; $lastTime = $null
        while (-not (Test-Path -LiteralPath $stopFile)) {
            $now = [DateTime]::UtcNow
            $java = @(Get-Process java -ErrorAction SilentlyContinue)
            $cpu = ($java | Measure-Object -Property CPU -Sum).Sum
            $memory = ($java | Measure-Object -Property WorkingSet64 -Sum).Sum
            $cpuPercent = $null
            if ($null -ne $lastTime -and $null -ne $cpu -and $cpu -ge $lastCpu) {
                $cpuPercent = 100 * ($cpu-$lastCpu) / ($now-$lastTime).TotalSeconds / $cpuCount
            }
            $stats = @(& docker stats --no-stream --format '{{json .}}' @containerIds 2>&1 | ForEach-Object { "$_" })
            $statsExit = $LASTEXITCODE
            $sql = 'SHOW GLOBAL STATUS WHERE Variable_name IN (''Threads_connected'',''Threads_running'',''Innodb_data_reads'',''Innodb_data_writes'',''Innodb_data_read'',''Innodb_data_written'');'
            $db = @($sql | & docker exec -i $dbId sh -c 'MYSQL_PWD=$MYSQL_PASSWORD mysql --batch --skip-column-names --user=$MYSQL_USER $MYSQL_DATABASE' 2>&1 | ForEach-Object { "$_" })
            $dbExit = $LASTEXITCODE
            [ordered]@{
                timestamp_utc=$now.ToString('o'); java_cpu_percent_host=$cpuPercent
                java_working_set_bytes=$memory; java_process_count=$java.Count
                docker_stats_exit=$statsExit; docker_stats=$stats
                mysql_status_exit=$dbExit; mysql_status=$db
            } | ConvertTo-Json -Compress -Depth 5 | Add-Content -Encoding UTF8 $destination
            $lastCpu = $cpu; $lastTime = $now
            Start-Sleep -Seconds 3
        }
    }
}
try {
    $versionLog = Join-Path $session 'jmeter-version'
    Run-Jmeter -JmeterArguments @('-v') -LogPrefix $versionLog -TimeoutSeconds 40
    & docker version --format '{{.Server.Version}}' | Set-Content (Join-Path $session 'docker-version.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Docker indisponible.' }
    $sourcePlan = if ($Mode -eq 'Calibration') { $calibration } else { $plan }
    $executionPlan = Join-Path $session 'plan-execute.jmx'
    & $Python (Join-Path $PSScriptRoot 'prepare_plan.py') $sourcePlan $executionPlan
    if ($LASTEXITCODE -ne 0) { throw 'Preparation du plan impossible.' }
    $manifest.hashes['plan-execute.jmx'] = (Get-FileHash $executionPlan -Algorithm SHA256).Hash
    Save-Manifest
    for ($repeat=1; $repeat -le $Repetitions; $repeat++) {
        if ($Mode -eq 'Campaign') { Reset-TestDatabase $repeat }
        $health = Invoke-RestMethod "http://${TargetHost}:$Port/api/health" -TimeoutSec 10
        if ($health.api -ne 'ok' -or $health.database -ne 'ok') { throw 'API ou base indisponible.' }
        & docker stats --no-stream --format '{{json .}}' @(& docker @compose ps -q) |
            Set-Content -Encoding UTF8 (Join-Path $session "repos-r$repeat.jsonl")
        if ($Mode -eq 'Campaign') {
            # Positive and negative controls detect a broken scenario before load is injected.
            foreach ($negative in @($false,$true)) {
                $control = if ($negative) { 'negatif' } else { 'positif' }
                $controlAccounts = $accounts
                if ($negative) {
                    $first = Import-Csv $accounts | Select-Object -First 1
                    $controlAccounts = Join-Path $session 'compte-invalide.csv'
                    @('email,password', ($first.email + ',INVALID_TEST_PASSWORD')) | Set-Content -Encoding ASCII $controlAccounts
                }
                $controlRaw = Join-Path $session "validation-$control-r$repeat.csv"
                Run-Jmeter -JmeterArguments @('-n','-t',$executionPlan,"-Jcomptes=$($controlAccounts.Replace('\','/'))","-Jhost=$TargetHost","-Jport=$Port",'-Jutilisateurs=1','-Jmontee=1','-Jboucles=1','-Jduree=60','-Jjmeter.save.saveservice.output_format=csv','-Jjmeter.save.saveservice.timestamp_format=ms','-l',$controlRaw,'-j',"$controlRaw.jmeter.log") -LogPrefix "$controlRaw.console" -TimeoutSeconds 90
                $requests = @(Import-Csv $controlRaw | Where-Object label -ne '__measurement_origin')
                $failures = @($requests | Where-Object success -ne 'true')
                if (-not $negative -and ($requests.Count -ne 2 -or $failures.Count -ne 0)) { throw 'Le controle nominal doit reussir 2/2.' }
                if ($negative -and @($failures | Where-Object label -eq '01 - Connexion').Count -eq 0) { throw 'Le controle negatif ne detecte pas le mauvais mot de passe.' }
            }
        }
        foreach ($users in $levels) {
            $stem = "$prefix-$users-r$repeat-$id"
            $raw = Join-Path $ResultsDirectory "$stem.csv"
            $steady = Join-Path $session "$stem-plateau.csv"
            $summary = Join-Path $session "$stem-statistiques.csv"
            $stopFile = Join-Path $session "$stem.stop"
            $palierStartUtc = [DateTime]::UtcNow.ToString('o')
            $monitor = Start-Monitor (Join-Path $session "$stem-serveur.jsonl") $stopFile
            Write-Host "[$repeat/$Repetitions] $users utilisateurs : $RampSeconds s de montee, $SteadySeconds s mesurees (hors montee)."
            try {
                $duration = $RampSeconds + $SteadySeconds + 2
                $arguments = @('-n','-t',$executionPlan,"-Jcomptes=$($accounts.Replace('\','/'))","-Jhost=$TargetHost","-Jport=$Port","-Jutilisateurs=$users","-Jmontee=$RampSeconds",'-Jboucles=-1',"-Jduree=$duration",'-Jpath=/index.html','-Jjmeter.save.saveservice.output_format=csv','-Jjmeter.save.saveservice.timestamp_format=ms','-Jjmeter.save.saveservice.print_field_names=true','-Jjmeter.save.saveservice.thread_counts=true','-l',$raw,'-j',(Join-Path $session "$stem.jmeter.log"))
                Run-Jmeter $arguments (Join-Path $session $stem) ($duration+90)
            } finally {
                New-Item -ItemType File -Force $stopFile | Out-Null
                $finished = Wait-Job $monitor -Timeout 20
                if (-not $finished) { Stop-Job $monitor }
                Receive-Job $monitor -ErrorAction Continue | Out-File (Join-Path $session "$stem-monitor.log")
                Remove-Job $monitor
            }
            & $Python (Join-Path $PSScriptRoot 'summarize.py') $raw $steady --ramp $RampSeconds --plateau $SteadySeconds --users $users --summary $summary
            if ($LASTEXITCODE -ne 0) { throw 'Extraction du plateau impossible.' }
            if (Select-String -LiteralPath $raw -SimpleMatch 'java.net.BindException' -Quiet) {
                throw 'Ports TCP de l injecteur epuises : mesure invalide. Attendre leur liberation et verifier le keep-alive.'
            }
            & $Python (Join-Path $PSScriptRoot 'server_summary.py') (Join-Path $session "$stem-serveur.jsonl") $summary (Join-Path $session "$stem-serveur-synthese.json")
            if ($LASTEXITCODE -ne 0) { throw 'Collecte serveur incomplete : voir les releves JSONL.' }
            & docker @compose logs --no-color --since $palierStartUtc backend | Set-Content -Encoding UTF8 (Join-Path $session "backend-$users-r$repeat.txt")
            Run-Jmeter -JmeterArguments @('-g',$steady,'-o',(Join-Path $session "rapport-$users-r$repeat"),'-j',(Join-Path $session "$stem-report.log")) -LogPrefix (Join-Path $session "$stem-report") -TimeoutSeconds 180
            Start-Sleep -Seconds $PauseSeconds
        }
    }
    $all = @(Get-ChildItem $session -Filter '*-statistiques.csv' | ForEach-Object { Import-Csv $_.FullName })
    $all | Export-Csv (Join-Path $session 'synthese.csv') -NoTypeInformation -Encoding UTF8
    & $Python (Join-Path $PSScriptRoot 'repeatability.py') $session
    if ($LASTEXITCODE -ne 0) { throw 'Calcul de repetabilite impossible.' }
    $manifest.completion = 'complete'
    $manifest.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-Manifest
    if ($Mode -eq 'Campaign') {
        & $Python (Join-Path $PSScriptRoot 'rapport_docker.py') $session
        if ($LASTEXITCODE -ne 0) { throw 'Generation du rapport de campagne impossible.' }
    }
    Write-Host "Campagne terminee : $session"
} catch {
    $manifest.completion = 'failed'
    $manifest.error = $_.Exception.Message
    throw
} finally { Save-Manifest }
