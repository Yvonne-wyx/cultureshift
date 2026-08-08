[CmdletBinding()]
param(
    [switch]$SelfTest
)

$ErrorActionPreference = 'Stop'
$maximumTextBytes = 5MB
$textExtensions = @(
    '', '.c', '.config', '.cpp', '.cs', '.css', '.csv', '.env', '.example',
    '.go', '.graphql', '.h', '.html', '.ini', '.java', '.js', '.json', '.jsx',
    '.md', '.mjs', '.properties', '.ps1', '.py', '.rb', '.rs', '.sh', '.sql',
    '.svg', '.toml', '.ts', '.tsx', '.txt', '.xml', '.yaml', '.yml'
)

$contentPatterns = [ordered]@{
    'Private key' = '-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
    'Likely secret assignment' = '(?im)\b(api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|password)\b\s*[:=]\s*["'']?([A-Za-z0-9_./+=-]{12,})'
    'GitHub token' = '\bgh[opusr]_[A-Za-z0-9_]{20,}\b'
    'AWS access key' = '\bAKIA[0-9A-Z]{16}\b'
    'Absolute local path' = '(?i)(?<![A-Za-z0-9_])[A-Z]:\\(?:Users|Desktop|Documents|Downloads)\\[^\s"''<>|]+'
    'Private-document marker' = '(?i)\b(confid(?:ential)\s+(?:document|material|draft)|strictly\s+private|private\s+document|do\s+not\s+distribute|internal\s+only|university\s+application|personal\s+statement|curriculum\s+vitae|application\s+deadline|admissions\s+material|scholarship\s+application)\b'
    'Email-like value' = '(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'
    'Phone-like value' = '(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\(\d{2,4}\)[ .-]?|\d{2,4}[ .-])\d{3,4}[ .-]\d{3,4}(?!\w)'
}

function Test-DisallowedEnvironmentName {
    param([Parameter(Mandatory)][string]$RelativePath)
    $normalized = $RelativePath -replace '\\', '/'
    return ($normalized -match '(^|/)\.env(?:\..+)?$' -and $normalized -notmatch '(^|/)\.env\.example$')
}

function Find-ContentViolations {
    param([Parameter(Mandatory)][string]$Content)
    $findings = [System.Collections.Generic.List[string]]::new()
    foreach ($entry in $contentPatterns.GetEnumerator()) {
        if ($Content -match $entry.Value) { $findings.Add($entry.Key) }
    }
    return @($findings)
}

function Invoke-ScannerSelfTest {
    $cases = @(
        @{ Name = 'harmless public sentence'; Content = 'This public project requires security and privacy review.'; Expected = 0 }
        @{ Name = 'fake secret'; Content = ('api_key=' + 'synthetic_token_123456'); Expected = 1 }
        @{ Name = 'fake personal email'; Content = ('person' + '@example.invalid'); Expected = 1 }
        @{ Name = 'fake absolute local path'; Content = ('C:' + '\Users\Example\Documents\notes.txt'); Expected = 1 }
    )
    foreach ($case in $cases) {
        $actual = @(Find-ContentViolations -Content $case.Content).Count
        if (($case.Expected -eq 0 -and $actual -ne 0) -or ($case.Expected -gt 0 -and $actual -eq 0)) {
            throw "Scanner self-test failed: $($case.Name)."
        }
    }
    if (-not (Test-DisallowedEnvironmentName -RelativePath '.env.local')) {
        throw 'Scanner self-test failed: disallowed .env filename.'
    }
    if (Test-DisallowedEnvironmentName -RelativePath '.env.example') {
        throw 'Scanner self-test failed: .env.example allowance.'
    }
    Write-Output 'Scanner self-tests passed.'
}

try {
    Invoke-ScannerSelfTest
    if ($SelfTest) { exit 0 }

    $repositoryRootText = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $repositoryRootText) { throw 'Not inside a Git repository.' }
    $repositoryRoot = [System.IO.Path]::GetFullPath($repositoryRootText.Trim())
    $rootWithSeparator = $repositoryRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

    $trackedAndPublicUntracked = @(git -C $repositoryRoot ls-files --cached --others --exclude-standard) | Where-Object { $_ }
    if ($LASTEXITCODE -ne 0) { throw 'Git file enumeration failed.' }
    $ignoredEnvironmentFiles = @(
        git -C $repositoryRoot ls-files --others --ignored --exclude-standard -- '.env' '.env.*' ':(glob)**/.env' ':(glob)**/.env.*'
    ) | Where-Object { $_ }
    if ($LASTEXITCODE -ne 0) { throw 'Ignored environment-file enumeration failed.' }
    $relativeFiles = @($trackedAndPublicUntracked + $ignoredEnvironmentFiles | Sort-Object -Unique)
    $violations = [System.Collections.Generic.List[string]]::new()

    foreach ($relativeFile in $relativeFiles) {
        $normalized = $relativeFile -replace '\\', '/'
        if (Test-DisallowedEnvironmentName -RelativePath $normalized) {
            $violations.Add("Disallowed environment file: $normalized")
            continue
        }

        $fullPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $relativeFile))
        if (-not $fullPath.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
            $violations.Add("Path escapes repository: $normalized")
            continue
        }

        $cursor = $fullPath
        $unsafeLink = $false
        while ($cursor.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
            if (Test-Path -LiteralPath $cursor) {
                $item = Get-Item -LiteralPath $cursor -Force
                if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                    $unsafeLink = $true
                    break
                }
            }
            $parent = [System.IO.Path]::GetDirectoryName($cursor)
            if (-not $parent -or $parent -eq $cursor) { break }
            $cursor = $parent
        }
        if ($unsafeLink) {
            $violations.Add("Symlink or reparse point not scanned: $normalized")
            continue
        }
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            $violations.Add("Missing or unreadable repository file: $normalized")
            continue
        }

        $extension = [System.IO.Path]::GetExtension($fullPath).ToLowerInvariant()
        if ($textExtensions -notcontains $extension) { continue }
        $fileInfo = Get-Item -LiteralPath $fullPath -Force
        if ($fileInfo.Length -gt $maximumTextBytes) {
            $violations.Add("Text file exceeds safe scan size: $normalized")
            continue
        }

        try {
            $strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
            $content = [System.IO.File]::ReadAllText($fullPath, $strictUtf8)
        } catch {
            $violations.Add("Text scan failed closed: $normalized")
            continue
        }
        foreach ($finding in @(Find-ContentViolations -Content $content)) {
            $violations.Add("${finding}: $normalized")
        }
    }

    if ($violations.Count -gt 0) {
        [Console]::Error.WriteLine("Public-boundary verification failed:`n - " + ($violations -join "`n - "))
        exit 1
    }
    Write-Output "Public-boundary verification passed for $($relativeFiles.Count) repository file(s)."
    exit 0
} catch {
    Write-Error "Public-boundary verification could not complete safely: $($_.Exception.Message)"
    exit 2
}
