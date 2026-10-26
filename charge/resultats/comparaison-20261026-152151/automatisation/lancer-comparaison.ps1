$ErrorActionPreference = 'Stop'
$pythonPath = 'C:\Users\souss\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
function Invoke-Measure([string[]]$MeasureArguments) {
    & $pythonPath @MeasureArguments
    if ($LASTEXITCODE -ne 0) { throw 'Étape interrompue : consulter les journaux. Les résultats existants sont conservés.' }
}
Push-Location $PSScriptRoot
try {
    Invoke-Measure -MeasureArguments @('prepare_campaign.py')
    Invoke-Measure -MeasureArguments @('campaign.py','vm','--rep','1','--calibration')
    Invoke-Measure -MeasureArguments @('campaign.py','vm','--rep','2','--calibration')
    Invoke-Measure -MeasureArguments @('campaign.py','vm','--rep','1')
    Invoke-Measure -MeasureArguments @('campaign.py','dk','--rep','1','--calibration')
    Invoke-Measure -MeasureArguments @('campaign.py','dk','--rep','2','--calibration')
    Invoke-Measure -MeasureArguments @('campaign.py','dk','--rep','1')
    Invoke-Measure -MeasureArguments @('campaign.py','dk','--rep','2')
    Invoke-Measure -MeasureArguments @('campaign.py','vm','--rep','2')
    Invoke-Measure -MeasureArguments @('baseline.py','vm')
    Invoke-Measure -MeasureArguments @('baseline.py','dk')
    Invoke-Measure -MeasureArguments @('campaign.py','vm','--rep','2','--prepare-only')
    Invoke-Measure -MeasureArguments @('audit_campaign.py')
    Invoke-Measure -MeasureArguments @('report_campaign.py')
} finally { Pop-Location }
