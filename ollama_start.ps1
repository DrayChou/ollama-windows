# 设置输出编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# 检测显卡信息
Write-Output "=== 显卡检测 ==="
try {
    $gpus = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -notlike "*Basic*" -and $_.Name -notlike "*Generic*" }
    foreach ($gpu in $gpus) {
        $memoryGB = [math]::Round($gpu.AdapterRAM / 1GB, 2)
        Write-Output "显卡: $($gpu.Name)"
        Write-Output "  厂商: $($gpu.VideoProcessor)"
        Write-Output "  显存: $memoryGB GB"
        Write-Output "  驱动版本: $($gpu.DriverVersion)"
        
        # 检测是否为 AMD 显卡
        if ($gpu.Name -match "AMD|Radeon|RX|Vega|RDNA") {
            Write-Output "  *** 检测到 AMD 显卡 ***"
            if ($gpu.Name -match "Integrated|APU|Vega [0-9]|Graphics") {
                Write-Output "  类型: 集成显卡（可能需要特殊配置才能被 Ollama 使用）"
                Write-Output "  建议: 考虑设置 HSA_OVERRIDE_GFX_VERSION 环境变量"
            } else {
                Write-Output "  类型: 独立显卡"
                Write-Output "  ROCm 支持: 需要安装 AMD ROCm 驱动"
            }
        } elseif ($gpu.Name -match "NVIDIA|GeForce|RTX|GTX|Quadro") {
            Write-Output "  *** 检测到 NVIDIA 显卡 ***"
            Write-Output "  CUDA 支持: 建议安装 NVIDIA CUDA 驱动"
        } elseif ($gpu.Name -match "Intel|UHD|Iris") {
            Write-Output "  *** 检测到 Intel 显卡 ***"
            Write-Output "  说明: Ollama 通常不支持 Intel 集显"
        }
        Write-Output ""
    }
} catch {
    Write-Output "显卡检测失败: $($_.Exception.Message)"
}
Write-Output "====================="
Write-Output ""

# 删除旧的 ollama-latest.zip 文件
if (Test-Path "ollama-latest.zip") {
    Write-Output "发现本地压缩包文件，检查是否需要更新..."
}

# 检查是否存在 ollama.exe
$ollama_exists = Test-Path ".\ollama.exe"

# 获取最新版本信息
Write-Output "获取最新版本信息..."
$json = Invoke-RestMethod -Uri "https://api.github.com/repos/ollama/ollama/releases/latest"

# 保存 JSON 信息到本地文件
Write-Output "保存版本信息到本地..."
$json | ConvertTo-Json -Depth 10 | Out-File -FilePath ".\ollama.jsonc" -Encoding UTF8

$latest_version = $json.tag_name -replace "^v", ""
$windows_asset = $json.assets | Where-Object { $_.name -eq "ollama-windows-amd64.zip" }
$download_url = $windows_asset.browser_download_url
$remote_size = $windows_asset.size
$remote_updated_at = $windows_asset.updated_at

Write-Output "最新版本: $latest_version"
Write-Output "文件大小: $([math]::Round($remote_size / 1MB, 2)) MB"
Write-Output "更新时间: $remote_updated_at"

if (-Not $ollama_exists) {
    Write-Output "未找到 ollama.exe，正在下载最新版本..."
    $update_required = $true
} else {
    # 获取本地版本号
    $local_version_output = .\ollama.exe --version 2>&1
    
    # 将输出转换为字符串并提取版本号
    $version_string = $local_version_output | Out-String
    if ($version_string -match "ollama version is ([0-9]+\.[0-9]+\.[0-9]+)") {
        $local_version = $matches[1]
    } else {
        Write-Output "无法解析本地版本号，强制更新"
        Write-Output "调试：版本字符串内容 = $version_string"
        $local_version = "0.0.0"
    }

    # 调试输出本地版本号
    Write-Output "本地版本号输出: $local_version_output"
    Write-Output "提取的本地版本号: $local_version"

    # 调试输出最新版本号
    Write-Output "最新版本号: $latest_version"

    # 版本号比较函数
    function Compare-Version($version1, $version2) {
        $v1 = [Version]$version1
        $v2 = [Version]$version2
        return $v1.CompareTo($v2)
    }

    # 比较版本号
    try {
        $comparison = Compare-Version $local_version $latest_version
        if ($comparison -eq 0) {
            Write-Output "当前已经是最新版本: $local_version"
            $update_required = $false
        } elseif ($comparison -lt 0) {
            Write-Output "发现新版本: $latest_version，当前版本: $local_version"
            $update_required = $true
        } else {
            Write-Output "本地版本 $local_version 比远程版本 $latest_version 更新，无需更新"
            $update_required = $false
        }
    } catch {
        Write-Output "版本比较出错，强制更新"
        $update_required = $true
    }
}

# 只有在需要更新时才停止正在运行的 Ollama 实例
if ($update_required) {
    Write-Output "需要更新，检查并停止正在运行的 Ollama 实例..."
    $ollama_list_output = .\ollama.exe list 2>&1
    if ($ollama_list_output -match "NAME\s+ID\s+SIZE\s+MODIFIED") {
        Write-Output "发现正在运行的 Ollama 实例，正在停止..."
        Stop-Process -Name "ollama" -Force
        Start-Sleep -Seconds 2 # 等待实例完全停止
    }
}

# 检查本地压缩包是否已经是最新版本
if ($update_required -and (Test-Path "ollama-latest.zip")) {
    $local_zip_info = Get-Item "ollama-latest.zip"
    $local_size = $local_zip_info.Length
    
    Write-Output "========== 压缩包检查 =========="
    Write-Output "检查本地压缩包..."
    Write-Output "本地文件大小: $([math]::Round($local_size / 1MB, 2)) MB ($local_size 字节)"
    Write-Output "远程文件大小: $([math]::Round($remote_size / 1MB, 2)) MB ($remote_size 字节)"
    
    # 如果文件大小一致，认为是同一个文件，跳过下载
    if ($local_size -eq $remote_size) {
        Write-Output "✓ 本地压缩包已是最新版本，跳过下载"
        $skip_download = $true
    } else {
        Write-Output "✗ 本地压缩包大小不匹配，重新下载"
        Write-Output "  删除不完整的本地文件..."
        Remove-Item -Force "ollama-latest.zip"
        $skip_download = $false
    }
    Write-Output "================================"
} else {
    $skip_download = $false
    if ($update_required) {
        Write-Output "未找到本地压缩包，需要下载"
    }
}

if ($update_required) {    if (-not $skip_download) {
        # 智能下载：尝试多种下载方式
        Write-Output "正在准备下载最新版本..."
        
        # 1. 首先检查并尝试安装 aria2c（最佳选择）
        $aria2c_path = $null
        $aria2c_installed = $false
        
        # 检查系统 PATH 中是否有 aria2c
        try {
            $aria2c_check = Get-Command aria2c -ErrorAction SilentlyContinue
            if ($aria2c_check) {
                $aria2c_path = $aria2c_check.Source
                $aria2c_installed = $true
                Write-Output "✓ 检测到系统已安装 aria2c: $aria2c_path"
            }
        } catch { }
        
        # 如果没有 aria2c，尝试下载便携版
        if (-not $aria2c_installed) {
            Write-Output "未检测到 aria2c，正在下载便携版本..."
            $aria2c_url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
            $aria2c_zip = ".\aria2c.zip"
            
            try {
                # 使用系统自带下载器下载 aria2c（小文件，速度可接受）
                Write-Output "正在下载 aria2c 下载工具..."
                Invoke-WebRequest -Uri $aria2c_url -OutFile $aria2c_zip -UseBasicParsing
                
                # 解压 aria2c
                Write-Output "正在解压 aria2c..."
                Expand-Archive -Path $aria2c_zip -DestinationPath ".\aria2c_temp" -Force
                
                # 查找 aria2c.exe
                $aria2c_exe = Get-ChildItem -Path ".\aria2c_temp" -Recurse -Name "aria2c.exe" | Select-Object -First 1
                if ($aria2c_exe) {
                    $aria2c_path = ".\aria2c_temp\$($aria2c_exe)"
                    $aria2c_installed = $true
                    Write-Output "✓ aria2c 下载工具准备就绪"
                }
                
                # 清理压缩包
                Remove-Item -Force $aria2c_zip -ErrorAction SilentlyContinue
                
            } catch {
                Write-Output "✗ aria2c 下载失败: $($_.Exception.Message)"
            }
        }
        
        # 2. 使用最佳可用方式下载
        $download_success = $false
        
        if ($aria2c_installed -and $aria2c_path) {
            Write-Output "========== 多线程下载 (aria2c) =========="
            Write-Output "使用 aria2c 进行高速下载..."
            Write-Output "文件: $([math]::Round($remote_size / 1MB, 2)) MB"
            
            try {
                # aria2c 参数说明：
                # -x 16: 使用16个连接
                # -s 16: 分割成16段
                # -k 1M: 最小分割大小1MB
                # --file-allocation=none: 不预分配文件空间（Windows推荐）
                # --allow-overwrite=true: 允许覆盖
                # --auto-file-renaming=false: 不自动重命名
                
                $aria2c_args = @(
                    "-x", "16",
                    "-s", "16", 
                    "-k", "1M",
                    "--file-allocation=none",
                    "--allow-overwrite=true",
                    "--auto-file-renaming=false",
                    "--summary-interval=2",
                    "--download-result=hide",
                    "--console-log-level=notice",
                    "-o", "ollama-latest.zip",
                    $download_url
                )
                
                $process = Start-Process -FilePath $aria2c_path -ArgumentList $aria2c_args -Wait -PassThru -NoNewWindow
                
                if ($process.ExitCode -eq 0 -and (Test-Path "ollama-latest.zip")) {
                    $downloaded_size = (Get-Item "ollama-latest.zip").Length
                    Write-Output "✓ aria2c 下载完成！"
                    Write-Output "  下载大小: $([math]::Round($downloaded_size / 1MB, 2)) MB"
                    $download_success = $true
                } else {
                    Write-Output "✗ aria2c 下载失败，退出代码: $($process.ExitCode)"
                }
                
            } catch {
                Write-Output "✗ aria2c 执行出错: $($_.Exception.Message)"
            }
            Write-Output "========================================"
        }
        
        # 3. 备用方案：PowerShell 分块并行下载
        if (-not $download_success) {
            Write-Output "========== 分块并行下载 (PowerShell) =========="
            Write-Output "使用 PowerShell 并行下载..."
            
            try {
                # 分块下载函数
                $downloadChunk = {
                    param($url, $start, $end, $chunkFile)
                    
                    $headers = @{
                        'Range' = "bytes=$start-$end"
                        'User-Agent' = 'PowerShell-DownloadManager/1.0'
                    }
                    
                    try {
                        Invoke-WebRequest -Uri $url -Headers $headers -OutFile $chunkFile -UseBasicParsing
                        return @{Success = $true; File = $chunkFile; Size = (Get-Item $chunkFile).Length}
                    } catch {
                        return @{Success = $false; Error = $_.Exception.Message; File = $chunkFile}
                    }
                }
                
                # 检查服务器是否支持范围请求
                $headRequest = Invoke-WebRequest -Uri $download_url -Method Head -UseBasicParsing
                $acceptRanges = $headRequest.Headers['Accept-Ranges']
                
                if ($acceptRanges -and $acceptRanges -contains 'bytes') {
                    Write-Output "✓ 服务器支持分块下载"
                    
                    # 计算分块
                    $chunkCount = 8  # 8个并行下载
                    $chunkSize = [math]::Ceiling($remote_size / $chunkCount)
                    $jobs = @()
                    $chunkFiles = @()
                    
                    Write-Output "分割为 $chunkCount 个分块，每块约 $([math]::Round($chunkSize / 1MB, 2)) MB"
                    
                    # 启动并行下载任务
                    for ($i = 0; $i -lt $chunkCount; $i++) {
                        $start = $i * $chunkSize
                        $end = [math]::Min(($i + 1) * $chunkSize - 1, $remote_size - 1)
                        $chunkFile = ".\chunk_$i.tmp"
                        $chunkFiles += $chunkFile
                        
                        Write-Output "启动分块 $($i+1): $([math]::Round($start/1MB,1))MB - $([math]::Round($end/1MB,1))MB"
                        
                        $job = Start-Job -ScriptBlock $downloadChunk -ArgumentList $download_url, $start, $end, $chunkFile
                        $jobs += $job
                    }
                    
                    # 等待所有任务完成
                    Write-Output "等待下载完成..."
                    $results = $jobs | Wait-Job | Receive-Job
                    $jobs | Remove-Job
                    
                    # 检查下载结果
                    $allSuccess = $true
                    $totalDownloaded = 0
                    
                    foreach ($result in $results) {
                        if ($result.Success) {
                            $totalDownloaded += $result.Size
                            Write-Output "✓ 分块完成: $($result.File) ($([math]::Round($result.Size/1MB,2)) MB)"
                        } else {
                            Write-Output "✗ 分块失败: $($result.File) - $($result.Error)"
                            $allSuccess = $false
                        }
                    }
                    
                    if ($allSuccess) {
                        # 合并文件
                        Write-Output "正在合并文件..."
                        $outputStream = [System.IO.File]::Create("ollama-latest.zip")
                        
                        try {
                            foreach ($chunkFile in $chunkFiles) {
                                if (Test-Path $chunkFile) {
                                    $chunkData = [System.IO.File]::ReadAllBytes($chunkFile)
                                    $outputStream.Write($chunkData, 0, $chunkData.Length)
                                    Remove-Item $chunkFile -Force
                                }
                            }
                            $outputStream.Close()
                            
                            $finalSize = (Get-Item "ollama-latest.zip").Length
                            Write-Output "✓ 文件合并完成！最终大小: $([math]::Round($finalSize / 1MB, 2)) MB"
                            $download_success = $true
                            
                        } catch {
                            Write-Output "✗ 文件合并失败: $($_.Exception.Message)"
                            $outputStream.Close()
                        }
                    } else {
                        # 清理失败的分块文件
                        foreach ($chunkFile in $chunkFiles) {
                            Remove-Item $chunkFile -Force -ErrorAction SilentlyContinue
                        }
                    }
                    
                } else {
                    Write-Output "✗ 服务器不支持分块下载，降级到单线程"
                }
                
            } catch {
                Write-Output "✗ 并行下载出错: $($_.Exception.Message)"
            }
            Write-Output "============================================"
        }
        
        # 4. 最终备用方案：传统单线程下载
        if (-not $download_success) {
            Write-Output "========== 单线程下载 (备用方案) =========="
            Write-Output "使用传统方式下载..."
            
            try {
                # 使用 WebClient 替代 Invoke-WebRequest，性能更好
                $webClient = New-Object System.Net.WebClient
                $webClient.Headers.Add("User-Agent", "PowerShell-DownloadManager/1.0")
                
                # 添加下载进度回调
                Register-ObjectEvent -InputObject $webClient -EventName DownloadProgressChanged -Action {
                    $progress = $Event.SourceEventArgs.ProgressPercentage
                    $received = $Event.SourceEventArgs.BytesReceived
                    $total = $Event.SourceEventArgs.TotalBytesToReceive
                    
                    if ($total -gt 0) {
                        Write-Progress -Activity "下载 ollama-latest.zip" -Status "$progress% 完成" -PercentComplete $progress -CurrentOperation "$([math]::Round($received/1MB,2)) MB / $([math]::Round($total/1MB,2)) MB"
                    }
                } | Out-Null
                
                $webClient.DownloadFile($download_url, "ollama-latest.zip")
                $webClient.Dispose()
                
                Write-Progress -Activity "下载 ollama-latest.zip" -Completed
                
                if (Test-Path "ollama-latest.zip") {
                    $finalSize = (Get-Item "ollama-latest.zip").Length
                    Write-Output "✓ 单线程下载完成！大小: $([math]::Round($finalSize / 1MB, 2)) MB"
                    $download_success = $true
                }
                
            } catch {
                Write-Output "✗ 单线程下载也失败了: $($_.Exception.Message)"
            }
            Write-Output "============================================"
        }
        
        # 清理临时的 aria2c 文件
        if (Test-Path ".\aria2c_temp") {
            Remove-Item -Recurse -Force ".\aria2c_temp" -ErrorAction SilentlyContinue
        }
        
        if (-not $download_success) {
            Write-Output "❌ 所有下载方式都失败了！请检查网络连接。"
            exit 1
        } else {
            Write-Output "🎉 下载完成！准备解压..."
        }
        
        # 验证下载的文件大小
        if (Test-Path "ollama-latest.zip") {
            $downloaded_size = (Get-Item "ollama-latest.zip").Length
            Write-Output "========== 下载验证 =========="
            Write-Output "下载大小: $([math]::Round($downloaded_size / 1MB, 2)) MB"
            Write-Output "预期大小: $([math]::Round($remote_size / 1MB, 2)) MB"
            
            if ($downloaded_size -eq $remote_size) {
                Write-Output "✓ 文件大小验证通过"
            } else {
                Write-Output "⚠️ 文件大小不匹配，但可能仍然有效"
                Write-Output "  差异: $([math]::Round(($downloaded_size - $remote_size) / 1MB, 2)) MB"
            }
            Write-Output "================================"
        }
    }

    # 解压到临时目录
    Write-Output "正在解压文件..."
    Expand-Archive -Path "ollama-latest.zip" -DestinationPath ".\temp" -Force

    # 替换现有的 ollama.exe
    Write-Output "正在更新 ollama.exe..."
    Move-Item -Force ".\temp\ollama.exe" ".\ollama.exe"

    # 清理临时文件
    Remove-Item -Recurse -Force ".\temp"
    Remove-Item -Force "ollama-latest.zip"
    
    Write-Output "更新完成！"
}

# 设置环境变量： models 目录到当前目录下
$env:OLLAMA_MODELS = "$PWD\models"

# 设置环境变量： 设置 host 0.0.0.0
$env:OLLAMA_HOST = "0.0.0.0"

# 检查是否有 AMD 集显，如果有则设置 HSA_OVERRIDE_GFX_VERSION
$gpus = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -notlike "*Basic*" -and $_.Name -notlike "*Generic*" }
$hasAmdIgpu = $gpus | Where-Object { $_.Name -match "AMD.*Graphics|Radeon.*Graphics|Vega [0-9]" }
if ($hasAmdIgpu) {
    Write-Output "检测到 AMD 集显，设置 HSA_OVERRIDE_GFX_VERSION 环境变量"
    $env:HSA_OVERRIDE_GFX_VERSION = "11.0.0"
}

# 启动 ollama 服务
Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/c .\ollama.exe start"