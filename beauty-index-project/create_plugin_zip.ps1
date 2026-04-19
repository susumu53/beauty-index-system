$pluginName = "beauty-index-generator"
$files = @(
    "beauty-index-generator.php"
)

# テンポラリフォルダの作成
$tempDir = Join-Path $PSScriptRoot $pluginName
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# ファイルのコピー
foreach ($file in $files) {
    $sourcePath = Join-Path $PSScriptRoot $file
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $tempDir
        Write-Host "Copied $file"
    } else {
        Write-Host "Warning: $file not found!" -ForegroundColor Yellow
    }
}

# ZIPフアイルの作成 (上書き)
$zipPath = Join-Path $PSScriptRoot "$pluginName.zip"
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}
Compress-Archive -Path $tempDir -DestinationPath $zipPath

# テンポラリフォルダの削除
Remove-Item -Recurse -Force $tempDir

Write-Host "Plugin packaged successfully at: $zipPath" -ForegroundColor Green
