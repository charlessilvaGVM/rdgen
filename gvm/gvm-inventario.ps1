# GVM Suporte - coletor de inventario (26/10/2026)
# Roda como SYSTEM pela tarefa agendada "GVM Suporte - Inventario" (ao ligar o PC e 1x por dia).
# Junta hardware, sistema, discos, rede, seguranca e programas e manda para o painel:
#   https://gvmsuporte.gvmsistemas.com.br/gvm/api/inventario/enviar
# O servidor confere o ID do GVM Suporte com o MachineGuid deste Windows (o mesmo que o GVM Suporte registra).
# Uso manual (como administrador):
#   powershell -ExecutionPolicy Bypass -File gvm-inventario.ps1            -> coleta e envia
#   powershell -ExecutionPolicy Bypass -File gvm-inventario.ps1 -SoMostrar -> so grava o JSON ao lado do log
#   powershell -ExecutionPolicy Bypass -File gvm-inventario.ps1 -Instalar  -> cria a tarefa agendada apontando para
#       ESTE arquivo (o .msi do GVM Suporte faz isso com o que fica em C:\Program Files\GVM_Suporte) e ja envia
#   powershell -ExecutionPolicy Bypass -File gvm-inventario.ps1 -Remover   -> apaga a tarefa
# Arquivo em ASCII de proposito (o PowerShell 5.1 le .ps1 sem BOM como ANSI).
param([switch]$SoMostrar, [switch]$Forcar, [switch]$Instalar, [switch]$Remover)

$ErrorActionPreference = 'SilentlyContinue'
$Versao = '1.2'
$Url = 'https://gvmsuporte.gvmsistemas.com.br/gvm/api/inventario/enviar'
$Pasta = Join-Path $env:ProgramData 'GVM_Suporte\inventario'
$Log = Join-Path $Pasta 'ultimo.log'
New-Item -ItemType Directory -Force -Path $Pasta | Out-Null

function Escreve($msg) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File -FilePath $Log -Append -Encoding utf8 }
function Dt($d) { if ($d) { try { ([datetime]$d).ToString('yyyy-MM-dd HH:mm') } catch { $null } } }
function Txt($s) { if ($null -eq $s) { '' } else { ([string]$s).Trim() } }

if (Test-Path $Log) { if ((Get-Item $Log).Length -gt 200KB) { Remove-Item $Log -Force } }

# ---------- Tarefa agendada (SYSTEM): 5 min depois de ligar e todo dia 12:00 + ate 2 h aleatorias ----------
$Tarefa = 'GVM Suporte - Inventario'
$schtasks = Join-Path $env:SystemRoot 'System32\schtasks.exe'
if ($Remover) {
  & $schtasks /Delete /TN $Tarefa /F 2>$null | Out-Null
  Escreve 'tarefa removida'
  exit 0
}
if ($Instalar) {
  $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
  $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>GVM Suporte: envia o inventario deste PC (hardware e programas) para o painel.</Description></RegistrationInfo>
  <Triggers>
    <BootTrigger><Enabled>true</Enabled><Delay>PT5M</Delay></BootTrigger>
    <CalendarTrigger><StartBoundary>2026-01-01T12:00:00</StartBoundary><Enabled>true</Enabled><RandomDelay>PT2H</RandomDelay>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger>
  </Triggers>
  <Principals><Principal id="Author"><UserId>S-1-5-18</UserId><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>$ps</Command><Arguments>-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "$PSCommandPath"</Arguments></Exec>
  </Actions>
</Task>
"@
  $arqXml = Join-Path $Pasta 'tarefa.xml'
  [IO.File]::WriteAllText($arqXml, $xml, [Text.Encoding]::Unicode)
  & $schtasks /Create /TN $Tarefa /XML $arqXml /F | Out-Null
  $ok = ($LASTEXITCODE -eq 0)
  Remove-Item $arqXml -Force
  if (-not $ok) { Escreve 'ERRO ao criar a tarefa agendada'; Write-Output 'Nao foi possivel criar a tarefa agendada.'; exit 1 }
  Escreve "tarefa criada -> $PSCommandPath"
  & $schtasks /Run /TN $Tarefa | Out-Null
  Write-Output "Tarefa '$Tarefa' criada; primeiro envio em andamento (log: $Log)."
  exit 0
}

Escreve "inicio (coletor $Versao)"

# ---------- ID do GVM Suporte e MachineGuid ----------
$exe = $null
$svc = Get-CimInstance Win32_Service -Filter "Name='GVM_Suporte'"
if ($svc -and $svc.PathName -match '"([^"]+\.exe)"') { $exe = $Matches[1] }
if (-not $exe) { $exe = Join-Path $env:ProgramFiles 'GVM_Suporte\GVM_Suporte.exe' }
$id = ''
if (Test-Path $exe) { $id = (& $exe --get-id 2>$null | Out-String).Trim() }
if ($id -notmatch '^\d{6,12}$') { Escreve "ID do GVM Suporte nao encontrado ($exe): '$id'"; exit 1 }
$hklm64 = [Microsoft.Win32.RegistryKey]::OpenBaseKey('LocalMachine', 'Registry64')
$guid = $hklm64.OpenSubKey('SOFTWARE\Microsoft\Cryptography').GetValue('MachineGuid')

# ---------- Sistema ----------
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$cv = $hklm64.OpenSubKey('SOFTWARE\Microsoft\Windows NT\CurrentVersion')
$ativado = $null
$lic = Get-CimInstance SoftwareLicensingProduct -Filter "ApplicationID='55c92734-d682-4d71-983e-d6ec3f16059f' AND PartialProductKey IS NOT NULL" | Select-Object -First 1
if ($lic) { $ativado = ($lic.LicenseStatus -eq 1) }
$sistema = [ordered]@{
  hostname        = $env:COMPUTERNAME
  nome            = Txt $os.Caption
  versao          = Txt $os.Version
  build           = "$($os.BuildNumber).$($cv.GetValue('UBR'))"
  versao_exibicao = Txt ($(if ($cv.GetValue('DisplayVersion')) { $cv.GetValue('DisplayVersion') } else { $cv.GetValue('ReleaseId') }))
  arquitetura     = Txt $os.OSArchitecture
  instalado_em    = Dt $os.InstallDate
  ultimo_boot     = Dt $os.LastBootUpTime
  usuario_logado  = Txt $cs.UserName
  dominio         = Txt $cs.Domain
  em_dominio      = [bool]$cs.PartOfDomain
  ativado         = $ativado
  fuso            = Txt (Get-CimInstance Win32_TimeZone).Caption
}

# ---------- Hardware ----------
$bios = Get-CimInstance Win32_BIOS
$placa = Get-CimInstance Win32_BaseBoard
$chassi = @((Get-CimInstance Win32_SystemEnclosure).ChassisTypes)
$tipo = 'Desktop'
if ($cs.Model -match 'Virtual|VMware|KVM|QEMU|HVM|Xen|VirtualBox' -or $cs.Manufacturer -match 'QEMU|Xen|innotek|VMware') { $tipo = 'Maquina virtual' }
elseif ($chassi | Where-Object { $_ -in 8, 9, 10, 11, 14, 30, 31, 32 }) { $tipo = 'Notebook' }
elseif (($chassi | Where-Object { $_ -in 17, 23, 28 }) -or $os.ProductType -ne 1) { $tipo = 'Servidor' }
$cpus = @(Get-CimInstance Win32_Processor)
$mem = @(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
  [ordered]@{ slot = Txt $_.DeviceLocator; capacidade = [int64]$_.Capacity; velocidade = $_.Speed; fabricante = Txt $_.Manufacturer; peca = Txt $_.PartNumber } })
$slots = (Get-CimInstance Win32_PhysicalMemoryArray | Measure-Object -Property MemoryDevices -Sum).Sum
$video = @(Get-CimInstance Win32_VideoController | ForEach-Object {
  [ordered]@{ nome = Txt $_.Name; memoria = [int64]$_.AdapterRAM; driver = Txt $_.DriverVersion } })
function Dec($a) { if ($a) { (($a | Where-Object { $_ -ne 0 } | ForEach-Object { [char]$_ }) -join '').Trim() } else { '' } }
$monitores = @(Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID | ForEach-Object {
  [ordered]@{ fabricante = Dec $_.ManufacturerName; modelo = Dec $_.UserFriendlyName; serial = Dec $_.SerialNumberID } })
$hardware = [ordered]@{
  fabricante = Txt $cs.Manufacturer
  modelo     = Txt $cs.Model
  serial     = Txt $bios.SerialNumber
  tipo       = $tipo
  bios       = [ordered]@{ versao = Txt $bios.SMBIOSBIOSVersion; data = Dt $bios.ReleaseDate; fabricante = Txt $bios.Manufacturer }
  placa_mae  = [ordered]@{ fabricante = Txt $placa.Manufacturer; modelo = Txt $placa.Product; serial = Txt $placa.SerialNumber }
  cpu        = [ordered]@{ nome = Txt $cpus[0].Name; qtd = $cpus.Count; nucleos = ($cpus | Measure-Object NumberOfCores -Sum).Sum
                           threads = ($cpus | Measure-Object NumberOfLogicalProcessors -Sum).Sum; mhz = $cpus[0].MaxClockSpeed }
  ram_total  = [int64]$cs.TotalPhysicalMemory
  ram_slots  = $slots
  memorias   = $mem
  video      = $video
  monitores  = $monitores
}

# ---------- Discos e volumes ----------
$falha = @{}
Get-CimInstance -Namespace root\wmi -ClassName MSStorageDriver_FailurePredictStatus | ForEach-Object { $falha[$_.InstanceName] = $_.PredictFailure }
$prevFalha = [bool]($falha.Values | Where-Object { $_ })
$discos = @()
$pd = @(Get-PhysicalDisk)
if ($pd.Count) {
  $discos = @($pd | ForEach-Object {
    $mt = switch ([string]$_.MediaType) { '3' { 'HDD' } '4' { 'SSD' } 'HDD' { 'HDD' } 'SSD' { 'SSD' } default { '' } }
    [ordered]@{ nome = Txt $_.FriendlyName; tipo = $mt; barramento = Txt $_.BusType; tamanho = [int64]$_.Size
                saude = Txt $_.HealthStatus; serial = Txt $_.SerialNumber } })
} else {
  $discos = @(Get-CimInstance Win32_DiskDrive | ForEach-Object {
    [ordered]@{ nome = Txt $_.Model; tipo = ''; barramento = Txt $_.InterfaceType; tamanho = [int64]$_.Size; saude = Txt $_.Status; serial = Txt $_.SerialNumber } })
}
$volumes = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
  [ordered]@{ letra = Txt $_.DeviceID; rotulo = Txt $_.VolumeName; fs = Txt $_.FileSystem; tamanho = [int64]$_.Size; livre = [int64]$_.FreeSpace } })

# ---------- Rede ----------
$rede = @(Get-CimInstance Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=TRUE' | ForEach-Object {
  [ordered]@{ descricao = Txt $_.Description; mac = Txt $_.MACAddress; dhcp = [bool]$_.DHCPEnabled
              ipv4 = @($_.IPAddress | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' -and $_ -notlike '169.254.*' })
              gateway = @($_.DefaultIPGateway | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' })
              dns = @($_.DNSServerSearchOrder) } })

# ---------- Seguranca ----------
$antivirus = @(Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object {
  $st = [int]$_.productState
  [ordered]@{ nome = Txt $_.displayName; ativo = ((($st -shr 12) -band 0xF) -eq 1); atualizado = ((($st -shr 4) -band 0xF) -eq 0) } })
if (-not $antivirus.Count) {  # Windows Server nao tem o SecurityCenter2: olha o Defender
  $mp = Get-MpComputerStatus
  if ($mp) { $antivirus = @([ordered]@{ nome = 'Microsoft Defender'; ativo = [bool]$mp.RealTimeProtectionEnabled
                                         atualizado = ($mp.AntivirusSignatureAge -le 7) }) }
}
$firewall = @(Get-NetFirewallProfile | ForEach-Object { [ordered]@{ perfil = Txt $_.Name; ativo = [bool]$_.Enabled } })
$bitlocker = @(Get-CimInstance -Namespace root\cimv2\Security\MicrosoftVolumeEncryption -ClassName Win32_EncryptableVolume | ForEach-Object {
  [ordered]@{ letra = Txt $_.DriveLetter; protegido = ($_.ProtectionStatus -eq 1) } })
$hf = @(Get-HotFix | Where-Object { $_.InstalledOn } | Sort-Object InstalledOn -Descending)
$atualizacoes = [ordered]@{ total = $hf.Count; ultima = Dt ($hf | Select-Object -First 1).InstalledOn
  recentes = @($hf | Select-Object -First 20 | ForEach-Object { [ordered]@{ id = Txt $_.HotFixID; data = Dt $_.InstalledOn } }) }

# ---------- Programas ----------
$chaves = @(
  @{ base = $hklm64; caminho = 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'; usuario = '' }
  @{ base = $hklm64; caminho = 'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'; usuario = '' }
)
$hku = [Microsoft.Win32.RegistryKey]::OpenBaseKey('Users', 'Registry64')
foreach ($sid in $hku.GetSubKeyNames() | Where-Object { $_ -match '^S-1-5-21-[\d-]+$' }) {
  $nomeUsr = ''
  try { $nomeUsr = (New-Object System.Security.Principal.SecurityIdentifier($sid)).Translate([System.Security.Principal.NTAccount]).Value } catch { $nomeUsr = $sid }
  $chaves += @{ base = $hku; caminho = "$sid\Software\Microsoft\Windows\CurrentVersion\Uninstall"; usuario = $nomeUsr }
}
$vistos = @{}
$programas = New-Object System.Collections.ArrayList
foreach ($c in $chaves) {
  $k = $c.base.OpenSubKey($c.caminho)
  if (-not $k) { continue }
  foreach ($n in $k.GetSubKeyNames()) {
    $p = $k.OpenSubKey($n)
    if (-not $p) { continue }
    $nome = Txt $p.GetValue('DisplayName')
    if (-not $nome -or $p.GetValue('SystemComponent') -eq 1 -or $p.GetValue('ParentKeyName') -or
        (Txt $p.GetValue('ReleaseType')) -match 'Update|Hotfix') { continue }
    $ver = Txt $p.GetValue('DisplayVersion')
    $chave = "$nome|$ver".ToLower()
    if ($vistos.ContainsKey($chave)) { continue }
    $vistos[$chave] = 1
    $inst = Txt $p.GetValue('InstallDate')
    if ($inst -match '^(\d{4})(\d{2})(\d{2})$') { $inst = "$($Matches[1])-$($Matches[2])-$($Matches[3])" } else { $inst = '' }
    $tam = $p.GetValue('EstimatedSize')
    [void]$programas.Add([ordered]@{ nome = $nome; versao = $ver; fabricante = Txt $p.GetValue('Publisher'); instalado = $inst
                                     tamanho_mb = $(if ($tam) { [math]::Round([double]$tam / 1024, 1) } else { $null }); usuario = $c.usuario })
  }
}
$programas = @($programas | Sort-Object { $_.nome })

# ---------- Monta e envia ----------
$dados = [ordered]@{
  id = $id; machine_guid = $guid; coletor = $Versao; coletado = (Get-Date).ToString('yyyy-MM-dd HH:mm'); forcar = [bool]$Forcar
  sistema = $sistema; hardware = $hardware; discos = $discos; disco_alerta_smart = $prevFalha; volumes = $volumes; rede = $rede
  antivirus = $antivirus; firewall = $firewall; bitlocker = $bitlocker; atualizacoes = $atualizacoes; programas = $programas
}
$json = $dados | ConvertTo-Json -Depth 6 -Compress
$bytes = [Text.Encoding]::UTF8.GetBytes($json)
if ($SoMostrar) {
  $saida = Join-Path $Pasta 'inventario.json'
  [IO.File]::WriteAllBytes($saida, $bytes)
  Escreve "gravado em $saida ($($bytes.Length) bytes, $($programas.Count) programas)"
  Write-Output "gravado em $saida"
  exit 0
}
try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
  # sem isso o PowerShell 5.1 manda "Expect: 100-continue" e o Apache/painel ficam esperando: tempo esgotado
  [Net.ServicePointManager]::Expect100Continue = $false
  $r = Invoke-WebRequest -Uri $Url -Method Post -Body $bytes -ContentType 'application/json; charset=utf-8' -UseBasicParsing -TimeoutSec 90
  Escreve "enviado: ID $id, $($bytes.Length) bytes, $($programas.Count) programas -> $($r.StatusCode) $($r.Content)"
  Write-Output "enviado: $($r.Content)"
} catch {
  $resp = ''
  try { $resp = (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() } catch {}
  Escreve "ERRO ao enviar: $($_.Exception.Message) $resp"
  Write-Output "ERRO ao enviar: $($_.Exception.Message) $resp"
  exit 2
}
