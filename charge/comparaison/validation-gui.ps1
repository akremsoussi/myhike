param([ValidateSet('positif','negatif')][string]$Cas='positif')
$jmeterPath = 'C:\Users\souss\Downloads\apache-jmeter-5.6.3\bin\jmeter.bat'
$planPath = Join-Path $PSScriptRoot "plan-gui-$Cas.jmx"
if (-not (Test-Path -LiteralPath $planPath)) { throw "Plan absent : $planPath" }
& $jmeterPath -t $planPath '-Jhost=127.0.0.1' '-Jport=8080' '-Jutilisateurs=1' '-Jmontee=1' '-Jboucles=1' '-Jduree=60'
