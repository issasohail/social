param(
  [string]$ProjectPath = "",
  [string]$OutputDir = "",
  [ValidateSet("Ask","Yes","No")][string]$DataMode = "Ask",
  [ValidateSet("Ask","Yes","No")][string]$MediaMode = "Ask",
  [ValidateSet("Ask","Yes","No")][string]$VenvMode = "Ask",
  [string]$LiveContainer = "social_db",
  [string]$DbName = "social_welfare",
  [string]$DbUser = "social_welfare"
)
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest
[int]$KeepLatestBackups=3
function Ask([string]$mode,[string]$prompt,[bool]$default=$false){if($mode-eq"Yes"){return $true};if($mode-eq"No"){return $false};$s=if($default){"[Y/n]"}else{"[y/N]"};while($true){$a=(Read-Host "$prompt $s").Trim().ToLower();if(!$a){return $default};if($a-in@("y","yes")){return $true};if($a-in@("n","no")){return $false}}}
if(!$ProjectPath){$ProjectPath=(git rev-parse --show-toplevel 2>$null).Trim()};if(!$ProjectPath){throw "Run inside the Social Git repository or pass -ProjectPath."};$ProjectPath=(Resolve-Path $ProjectPath).Path
if(!$OutputDir){$OutputDir=Join-Path (Split-Path $ProjectPath -Parent) "Social_Backups"};New-Item -ItemType Directory -Force $OutputDir|Out-Null
$includeData=Ask $DataMode "Include database data?" $true;$includeMedia=Ask $MediaMode "Include uploaded media/photos?" $true;$includeVenv=Ask $VenvMode "Include .venv?" $false
$stamp=Get-Date -Format "yyyy-MM-dd_HH-mm-ss";$commit=(git -C $ProjectPath rev-parse --short HEAD).Trim();$zip=Join-Path $OutputDir ("SOCIAL_{0}_{1}_{2}_{3}_{4}.zip" -f $stamp,$commit,$(if($includeData){"DATA"}else{"NODATA"}),$(if($includeMedia){"MEDIA"}else{"NOMEDIA"}),$(if($includeVenv){"VENV"}else{"NOVENV"}))
$tmp=Join-Path $env:TEMP "social_backup_$stamp";New-Item -ItemType Directory -Force $tmp|Out-Null
try{
  Write-Host "Copying Social source code..." -ForegroundColor Cyan
  $exclude=@(".git","__pycache__","staticfiles","Social_Backups","*.pyc","*.pyo",".env","*.log")
  if(!$includeVenv){$exclude+=".venv"};if(!$includeMedia){$exclude+="media"}
  $args=@($ProjectPath,$tmp,"/E","/R:1","/W:1","/NFL","/NDL","/NJH","/NJS","/NP","/XD")+$exclude.Where({$_ -notlike "*.*"})+@("/XF")+$exclude.Where({$_ -like "*.*"})
  & robocopy @args | Out-Null;if($LASTEXITCODE-ge 8){throw "robocopy failed with exit code $LASTEXITCODE"}
  if($includeData){
    New-Item -ItemType Directory -Force (Join-Path $tmp "_database")|Out-Null
    $sqlite=Join-Path $ProjectPath "db.sqlite3"
    if(Test-Path $sqlite){Copy-Item $sqlite (Join-Path $tmp "_database\db.sqlite3") -Force;Write-Host "Included SQLite database." -ForegroundColor Green}
    else{
      if(!(Get-Command docker -ErrorAction SilentlyContinue)){throw "Docker is required to dump MySQL data."}
      $pwd=& docker exec $LiveContainer sh -c 'printf %s "$MYSQL_PASSWORD"' 2>$null
      if(!$pwd){$pwd=& docker exec $LiveContainer sh -c 'printf %s "$MYSQL_ROOT_PASSWORD"' 2>$null}
      if(!$pwd){throw "Could not read MYSQL_PASSWORD/MYSQL_ROOT_PASSWORD from container '$LiveContainer'. Pass a container with those environment variables."}
      $remote="/tmp/social_backup_$stamp.sql";& docker exec -e "MYSQL_PWD=$pwd" $LiveContainer mysqldump -u $DbUser --default-character-set=utf8mb4 --set-gtid-purged=OFF --no-tablespaces --single-transaction --quick --skip-lock-tables --routines --triggers $DbName -r $remote
      if($LASTEXITCODE-ne 0){throw "mysqldump failed."};& docker cp "${LiveContainer}:$remote" (Join-Path $tmp "_database\social_full.sql")|Out-Null;& docker exec $LiveContainer rm -f $remote|Out-Null
      Write-Host "Included full MySQL schema + data." -ForegroundColor Green
    }
  }
  @("Backup created: $(Get-Date)","Source: $ProjectPath","Commit: $commit","Database included: $includeData","Media included: $includeMedia","Venv included: $includeVenv","NOTE: .env, .git, logs, caches and collected static are intentionally excluded. Database/media may contain confidential personal information; protect this ZIP.") | Set-Content (Join-Path $tmp "BACKUP_README.txt")
  Write-Host "Creating ZIP..." -ForegroundColor Cyan;Compress-Archive -Path (Join-Path $tmp "*") -DestinationPath $zip -CompressionLevel Fastest -Force
  if(!(Test-Path $zip)){throw "ZIP was not created."};Write-Host "Created: $zip" -ForegroundColor Green
  Get-ChildItem $OutputDir -Filter "SOCIAL_*.zip"|Sort-Object LastWriteTime -Descending|Select-Object -Skip $KeepLatestBackups|Remove-Item -Force
}finally{Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue}
