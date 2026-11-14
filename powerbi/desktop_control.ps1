param(
    [ValidateSet('Inspect','Invoke','Click','Keys','Paste','Value','Screenshot')][string]$Action='Inspect',
    [string]$Name='',
    [string]$AutomationId='',
    [string]$Value='',
    [string]$Keys='',
    [string]$OutputPath='',
    [int]$ProcessId=0
)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class PbiWindowNative {
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr handle);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr handle,int command);
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr handle);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr handle,out uint pid);
 [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
 [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint first,uint second,bool attach);
 [DllImport("user32.dll")] public static extern void keybd_event(byte key,byte scan,uint flags,UIntPtr extra);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint x,uint y,uint data,UIntPtr extra);
}
'@
[void][PbiWindowNative]::SetProcessDPIAware()
$taskProcesses=@(Get-Process PBIDesktop -ErrorAction SilentlyContinue)
if ($ProcessId) { $taskProcesses=@($taskProcesses | Where-Object { $_.Id -eq $ProcessId }) }
$taskPids=@($taskProcesses | ForEach-Object { $_.Id })
$taskRoot=[System.Windows.Automation.AutomationElement]::RootElement
$taskAllWindows=$taskRoot.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
$taskPbiWindows=@($taskAllWindows | Where-Object { $_.Current.ProcessId -in $taskPids })
if ($taskPbiWindows.Count -eq 0) { throw 'No accessible Power BI Desktop window.' }
$taskMain=@($taskPbiWindows | Where-Object { $_.Current.Name -match 'Power BI Desktop' }) | Select-Object -First 1
if (-not $taskMain) { $taskMain=$taskPbiWindows[0] }
function Set-PbiForeground {
    $taskHandle=[IntPtr]$taskMain.Current.NativeWindowHandle
    [uint32]$taskForegroundPid=0
    $taskForegroundThread=[PbiWindowNative]::GetWindowThreadProcessId([PbiWindowNative]::GetForegroundWindow(),[ref]$taskForegroundPid)
    if ($taskForegroundPid -in $taskPids) { return }
    if ([PbiWindowNative]::IsIconic($taskHandle)) { [void][PbiWindowNative]::ShowWindow($taskHandle,9) }
    [PbiWindowNative]::keybd_event(18,0,0,[UIntPtr]::Zero)
    [PbiWindowNative]::keybd_event(18,0,2,[UIntPtr]::Zero)
    $taskCurrentThread=[PbiWindowNative]::GetCurrentThreadId()
    [void][PbiWindowNative]::AttachThreadInput($taskCurrentThread,$taskForegroundThread,$true)
    [void][PbiWindowNative]::SetForegroundWindow($taskHandle)
    [void][PbiWindowNative]::AttachThreadInput($taskCurrentThread,$taskForegroundThread,$false)
    Start-Sleep -Milliseconds 200
}
if ($Action -eq 'Inspect') {
    foreach ($taskWindow in $taskPbiWindows) {
        'WINDOW: '+$taskWindow.Current.Name
        $taskElements=$taskWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
        $taskElements | Where-Object { ($_.Current.Name -or $_.Current.AutomationId) -and (-not $Name -or $_.Current.Name -match $Name) } | Select-Object -First 230 | ForEach-Object {
            [PSCustomObject]@{Name=$_.Current.Name;Type=$_.Current.ControlType.ProgrammaticName;Id=$_.Current.AutomationId;Enabled=$_.Current.IsEnabled} | ConvertTo-Json -Compress
        }
    }
    exit
}
if ($Action -eq 'Screenshot') {
    Set-PbiForeground
    Start-Sleep -Milliseconds 400
    $taskRect=$taskMain.Current.BoundingRectangle
    if ($taskRect.Width -le 0 -or $taskRect.Height -le 0) { throw 'Power BI window has no visible bounds.' }
    $taskBitmap=New-Object System.Drawing.Bitmap([int]$taskRect.Width,[int]$taskRect.Height)
    $taskGraphics=[System.Drawing.Graphics]::FromImage($taskBitmap)
    $taskGraphics.CopyFromScreen([int]$taskRect.X,[int]$taskRect.Y,0,0,$taskBitmap.Size)
    $taskBitmap.Save($OutputPath,[System.Drawing.Imaging.ImageFormat]::Png)
    $taskGraphics.Dispose();$taskBitmap.Dispose()
    'Saved '+$OutputPath
    exit
}
Set-PbiForeground
if ($Action -in @('Keys','Paste')) {
    $taskShell=New-Object -ComObject WScript.Shell
    Start-Sleep -Milliseconds 150
    if ($Action -eq 'Paste') {
        [System.Windows.Forms.Clipboard]::SetText($Value)
        $taskShell.SendKeys('^v')
    } else { $taskShell.SendKeys($Keys) }
    exit
}
$taskProperty=[System.Windows.Automation.AutomationElement]::NameProperty
$taskMatch=$Name
if ($AutomationId) { $taskProperty=[System.Windows.Automation.AutomationElement]::AutomationIdProperty;$taskMatch=$AutomationId }
$taskCondition=New-Object System.Windows.Automation.PropertyCondition($taskProperty,$taskMatch)
$taskTarget=$null
foreach ($taskWindow in $taskPbiWindows) {
    $taskTarget=$taskWindow.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$taskCondition)
    if ($taskTarget) { break }
}
if (-not $taskTarget) { throw ('Power BI control not found: '+$taskMatch) }
if ($Action -eq 'Value') {
    $taskTarget.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Value)
    exit
}
$taskPattern=$null
if ($Action -ne 'Click' -and $taskTarget.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$taskPattern)) { $taskPattern.Invoke() }
elseif ($Action -ne 'Click' -and $taskTarget.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$taskPattern)) { $taskPattern.Select() }
else {
    $taskRect=$taskTarget.Current.BoundingRectangle
    [void][PbiWindowNative]::SetCursorPos([int]($taskRect.X+$taskRect.Width/2),[int]($taskRect.Y+$taskRect.Height/2))
    [PbiWindowNative]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
    [PbiWindowNative]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
