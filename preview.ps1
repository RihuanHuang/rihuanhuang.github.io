param(
  [string]$Root   = (Join-Path $PSScriptRoot "docs"),
  [int]   $Port   = 8765,
  [string]$Prefix = "/subpath"
)

$mime = @{
  ".html" = "text/html; charset=utf-8"
  ".css"  = "text/css; charset=utf-8"
  ".js"   = "application/javascript; charset=utf-8"
  ".json" = "application/json; charset=utf-8"
  ".jpg"  = "image/jpeg"
  ".jpeg" = "image/jpeg"
  ".png"  = "image/png"
  ".gif"  = "image/gif"
  ".svg"  = "image/svg+xml"
  ".ico"  = "image/x-icon"
  ".pdf"  = "application/pdf"
  ".woff" = "font/woff"
  ".woff2"= "font/woff2"
  ".ttf"  = "font/ttf"
  ".eot"  = "application/vnd.ms-fontobject"
  ".txt"  = "text/plain; charset=utf-8"
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()
Write-Output "serving '$Root'"
Write-Output "open:  http://localhost:$Port$Prefix/"

while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  $req = $ctx.Request
  $res = $ctx.Response

  $path = [System.Uri]::UnescapeDataString($req.Url.AbsolutePath)
  if ($path.StartsWith($Prefix)) { $path = $path.Substring($Prefix.Length) }
  if ($path -eq "" -or $path.EndsWith("/")) { $path = $path + "index.html" }
  $rel  = $path.TrimStart("/").Replace("/", "\")
  $full = Join-Path $Root $rel

  if (Test-Path -LiteralPath $full -PathType Leaf) {
    $ext = [System.IO.Path]::GetExtension($full).ToLower()
    $ct = $mime[$ext]
    if (-not $ct) { $ct = "application/octet-stream" }
    $bytes = [System.IO.File]::ReadAllBytes($full)
    $res.ContentType     = $ct
    $res.StatusCode      = 200
    $res.ContentLength64 = $bytes.Length
    $res.OutputStream.Write($bytes, 0, $bytes.Length)
    Write-Output ("200  {0}" -f $req.Url.AbsolutePath)
  } else {
    $res.StatusCode = 404
    $msg = [System.Text.Encoding]::UTF8.GetBytes("404 not found: $rel")
    $res.ContentType     = "text/plain; charset=utf-8"
    $res.ContentLength64 = $msg.Length
    $res.OutputStream.Write($msg, 0, $msg.Length)
    Write-Output ("404  {0}" -f $req.Url.AbsolutePath)
  }
  $res.OutputStream.Close()
}
