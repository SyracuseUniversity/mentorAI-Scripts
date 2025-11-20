$ErrorActionPreference = 'Stop'

#=== GET API KEY FROM FILE ===
[System.String]$apiKey = (Get-Content -Path "C:\Users\relstad\Apps-SU\Git\mentorAIKey.txt" -Raw).Trim()

#=== BUILD REQUEST HEADERS ===
$headers = @{
    "Content-Type"  = "application/json"
    "Authorization" = "Api-Token $apiKey"
}

[System.String]$orgId = "syracuse"
[System.String]$userId = "relstad" #can also use your FID
[System.String]$url = "https://base.manager.ai.syr.edu/api/ai-index/orgs/$orgId/users/$userId/documents/train/"

[System.String]$pathway = "96324d0e-dfcf-4f25-839e-941ce97e44d0" #You can find this at the end of the URL string when viewing a mentor in a browser. Will be formatted like: 12345678-1234-1234-1234-123456789012

#[System.String]$ingestURL = "https://nullrefexcept.syr.edu/Declartion%20Of%20Independance.txt"

# File to upload
$filePath = "C:\Users\relstad\Apps-SU\Git\LifeCycle\Connectors\ADAccountControl.ps1"

# Read file content
$fileContent = Get-Content -Path $filePath -Raw

    
#file = $fileContent

$body = @{
    pathway = $pathway
    type = "file"
    access = "private"
    file = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($fileContent))
    
} | ConvertTo-Json

#=== CALL THE API ===
try
{
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
}
catch 
{
    Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__
    Write-Host "StatusDescription:" $_.Exception.Response.StatusDescription
    Write-Host $_ | select *
    exit
}

Write-Host $response.message
Write-Host "Task ID:" + $response.task_id
Write-Host "Doc ID: " + $response.document_id