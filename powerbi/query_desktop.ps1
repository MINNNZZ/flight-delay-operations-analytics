param([Parameter(Mandatory=$true)][int]$Port,[Parameter(Mandatory=$true)][string]$QueryPath,[string]$OutputPath='')
$ErrorActionPreference='Stop'
$taskLib='C:\Program Files\Microsoft Power BI Desktop\bin'
[void][Reflection.Assembly]::LoadFrom($taskLib+'\Microsoft.Identity.Client.dll')
[void][Reflection.Assembly]::LoadFrom($taskLib+'\Microsoft.PowerBI.AdomdClient.dll')
$taskConn=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection('Data Source=localhost:'+$Port+';')
try {
    $taskConn.Open()
    $taskCmd=$taskConn.CreateCommand()
    $taskCmd.CommandText=[IO.File]::ReadAllText((Resolve-Path -LiteralPath $QueryPath))
    $taskCmd.CommandTimeout=60
    $taskReader=$taskCmd.ExecuteReader()
    $taskRows=New-Object System.Collections.Generic.List[object]
    while($taskReader.Read()) {
        $taskRow=[ordered]@{}
        for($taskCol=0;$taskCol -lt $taskReader.FieldCount;$taskCol++) {
            $taskVal=$taskReader.GetValue($taskCol)
            if ($taskVal -is [DBNull]) {$taskVal=$null}
            $taskRow[$taskReader.GetName($taskCol)]=$taskVal
        }
        $taskRows.Add([PSCustomObject]$taskRow)
    }
    $taskReader.Close()
    $taskJson=ConvertTo-Json -InputObject @($taskRows.ToArray()) -Depth 8
    if ($OutputPath) { [IO.File]::WriteAllText($OutputPath,$taskJson,(New-Object System.Text.UTF8Encoding($false))) }
    $taskJson
} finally {$taskConn.Close()}
