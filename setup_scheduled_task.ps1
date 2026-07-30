# ==============================================================================
# SCRIPT POWERSHELL - REGISTRAR TAREA PROGRAMADA EN WINDOWS (CADA 15 MINUTOS)
# ==============================================================================

$TaskName = "AustraliaVisa462Monitor_Spain"
$ScriptDir = $PSScriptRoot
$BatPath = Join-Path -Path $ScriptDir -ChildPath "run_monitor.bat"

Write-Host "Configurando tarea programada: $TaskName" -ForegroundColor Cyan
Write-Host "Directorio del script: $ScriptDir"
Write-Host "Archivo a ejecutar   : $BatPath"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "La tarea '$TaskName' ya existe. Reemplazando con configuración anti-reinicio..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`"" -WorkingDirectory $ScriptDir

# Disparador: Repetir cada 15 minutos indefinidamente desde la hora actual
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)

# Configuración del usuario actual
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Configuración de alta disponibilidad:
# - StartWhenAvailable = True -> Si el PC estaba apagado cuando tocaba ejecutar, ¡lo ejecuta en cuanto enciendas e inicies sesión!
# - DontStopIfGoingOnBatteries & AllowStartIfOnBatteries -> Funciona perfecto en portátiles con batería.
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew

# Registrar la tarea en Windows
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Agente automático de monitoreo para la Visa Work and Holiday (462) Australia para España. Comprueba el cupo cada 15 minutos y se reanuda automáticamente al encender el PC."

Write-Host "`n¡SUCCESS: Tarea '$TaskName' registrada exitosamente con protección contra reinicios!" -ForegroundColor Green
Write-Host "El agente se ejecutará automáticamente cada 15 minutos y reanudará su trabajo inmediatamente tras apagar/encender tu PC." -ForegroundColor Green
