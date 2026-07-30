# ==============================================================================
# SCRIPT DE CONFIGURACIÓN Y PRUEBA INMEDIATA PARA GMAIL (SMTP)
# ==============================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   CONFIGURACIÓN DE CORREO DE GMAIL PARA ALERTAS VISA 462" -ForegroundColor Cyan
Write-Host "================================================================"

Write-Host "`nPara enviar correos automáticos desde Gmail, Google requiere una 'Contraseña de aplicación'."
Write-Host "Puedes generarla en: Cuenta de Google -> Seguridad -> Verificación en 2 pasos -> Contraseñas de aplicaciones.`n"

$EmailUser = Read-Host "1. Introduce tu correo de Gmail emisor (ej. maverick6576@gmail.com)"
if ([string]::IsNullOrWhiteSpace($EmailUser)) {
    Write-Host "Error: El correo no puede estar vacío." -ForegroundColor Red
    exit 1
}

Write-Host "`n2. Introduce tu Contraseña de Aplicación de 16 letras (la escritura está oculta por seguridad):" -ForegroundColor Yellow
$SecurePass = Read-Host -AsSecureString
$EmailPass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePass))

if ([string]::IsNullOrWhiteSpace($EmailPass)) {
    Write-Host "Error: La contraseña de aplicación no puede estar vacía." -ForegroundColor Red
    exit 1
}

# Limpiar espacios de la contraseña de aplicación si el usuario la pegó con espacios (ej: "abcd efgh ijkl mnop" -> "abcdefghijklmnop")
$EmailPassClean = $EmailPass.Replace(" ", "")

# Archivo .env
$EnvPath = Join-Path -Path $PSScriptRoot -ChildPath ".env"

if (-not (Test-Path $EnvPath)) {
    Copy-Item (Join-Path -Path $PSScriptRoot -ChildPath ".env.example") -Destination $EnvPath
}

# Actualizar el contenido de .env
$content = Get-Content $EnvPath -Raw
$content = $content -replace "(?m)^EMAIL_ENABLED=.*", "EMAIL_ENABLED=true"
$content = $content -replace "(?m)^EMAIL_TO=.*", "EMAIL_TO=maverick6576@gmail.com"
$content = $content -replace "(?m)^EMAIL_FROM=.*", "EMAIL_FROM=$EmailUser"
$content = $content -replace "(?m)^EMAIL_SMTP_USER=.*", "EMAIL_SMTP_USER=$EmailUser"
$content = $content -replace "(?m)^EMAIL_SMTP_PASSWORD=.*", "EMAIL_SMTP_PASSWORD=$EmailPassClean"

Set-Content -Path $EnvPath -Value $content -Encoding UTF8

Write-Host "`n[SUCCESS] Credenciales de Gmail guardadas de forma segura en .env." -ForegroundColor Green
Write-Host "Enviando un correo de prueba ahora mismo a maverick6576@gmail.com para verificar la conexión...`n" -ForegroundColor Cyan

# Ejecutar prueba inmediata de alerta
python main.py --test-alert

Write-Host "`n================================================================"
Write-Host "Si ves '¡Correo urgente enviado exitosamente!', revisa la bandeja"
Write-Host "de entrada de maverick6576@gmail.com (y la carpeta de Spam por si acaso)."
Write-Host "================================================================" -ForegroundColor Cyan
