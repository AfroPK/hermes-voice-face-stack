# setup.ps1 - generate a random API key and print the env lines (no secrets stored)
# Prints a fresh key so the operator can configure Hermes. Safe to re-run.
$rand = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Output ""
Write-Output "=== One-time Hermes API key (store it yourself) ==="
Write-Output "API_SERVER_KEY=$rand"
Write-Output ""
Write-Output "Add the following to your Hermes environment (.env / service env / launcher),"
Write-Output "then restart the Hermes gateway:"
Write-Output ""
Write-Output "API_SERVER_KEY=$rand"
Write-Output "API_SERVER_PORT=8642"
Write-Output "API_SERVER_HOST=127.0.0.1"
Write-Output ""
Write-Output "Then set these for the backtalk user so it can reach Hermes:"
Write-Output "$env:HERMES_API_URL = 'http://127.0.0.1:8642/v1'"
Write-Output "$env:HERMES_API_KEY = '$rand'"