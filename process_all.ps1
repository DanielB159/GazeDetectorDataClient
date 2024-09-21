# Define the path to the "recordings" folder in the current directory
$recordingsPath = Join-Path (Get-Location) "recordings"

# Get all directories inside the "recordings" folder
Get-ChildItem -Path $recordingsPath -Directory | ForEach-Object {
    $dirName = $_.Name
    Write-Host "Processing directory: $dirName"
    
    # Run the Python script with the directory name as an argument
    python frame_processor.py "$dirName"
}
