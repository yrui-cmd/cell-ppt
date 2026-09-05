# Nature PPT

Nature PPT 将 PNG、JPEG、WebP 或 SVG 参考图重建为实际可用的 PowerPoint 内容。它不会把“产生了很多路径”误称为“很好编辑”，而是先判断复杂度，再选择合适的输出方式。

## 0.6.0 的工作方式

```text
参考图 → 复杂度预检 → 简单图直接高保真矢量化 → SVG 校验 → PowerPoint 原生对象
                     └→ 复杂图按对象预算逐档减色、去噪、简化
```

- 原生模式：适合扁平科研图、流程图、机制图和有限色彩图，按最高保真配置直接生成 PowerPoint 原生对象。
- 轻量原生模式：适合照片、3D 渲染、辉光、软阴影和密集渐变。算法在多个颜色、去噪和曲线简化档位中，选择不超过对象预算且细节最多的版本；PPT 中不嵌入背景位图。
- 存档模式：生成最高保真 SVG，但不会强行把超预算路径塞进 PowerPoint。

默认原生对象安全上限为 50,000。超过上限时自动转为轻量原生矢量化，不再生成“高清位图背景 + 上层编辑对象”的分层结果。

## 矢量化后端

本地模式无需 API Key，使用固定并校验哈希的 VTracer 1.0.0-alpha.4。

项目同时提供可选 HTTPS 矢量服务适配器，可接 SuperSVG、AdaVec 或后续更强的引擎。线上服务并非必需，也不会在未配置时自动上传图片。服务只负责返回 SVG，SVG 会在本地完成路径打包、规范化、结构校验和 PowerPoint 绘制；超预算时回退到本地轻量原生算法。接口契约见 Skill 的 `references/remote-backend.md`。

## 安装

Windows：

```powershell
git clone https://github.com/Gerry2024-hub/nature-ppt.git
Set-Location .\nature-ppt
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

macOS：

```bash
git clone https://github.com/Gerry2024-hub/nature-ppt.git
cd nature-ppt
bash ./setup.sh
```

覆盖旧版时增加 `-Force` 或 `--force`。安装器只更新 `nature-ppt`，不会删除或修改其他 Skill，并保留已有运行配置。

## 使用

在 豆包、VScode、deepseek、Claudecode、Codex等中发送：

```text
使用 $nature-ppt，把这张参考图重建为实际可编辑的 PowerPoint；简单图直接原生生成，复杂图使用轻量原生模式，并报告对象数与细节损失。
```

命令行完整流程：

```powershell
python .\plugins\nature-ppt\skills\nature-ppt\scripts\run_pipeline.py `
  --input-image .\reference.png `
  --output-root .\outputs
```

将已经验证的 SVG 绘制到 Windows 当前 PowerPoint：

```powershell
powershell -ExecutionPolicy Bypass -File `
  .\plugins\nature-ppt\skills\nature-ppt\scripts\reconstruct_from_svg.ps1 `
  -InputSvg .\figure.svg -OutputRoot .\outputs -UseActivePresentation
```

## 测试

```powershell
python .\tests\test_nature_ppt.py
python .\tests\test_cross_platform.py
.\tests\test-package.ps1
```

PowerPoint 真机测试只允许在一次性测试文稿中显式运行：

```powershell
.\tests\test-powerpoint-e2e.ps1 -ConfirmDisposablePresentation
```

## 可编辑性说明

两种 PowerPoint 输出都只包含原生路径和文字，不使用栅格背景。复杂图片会通过减少相近颜色、合并细小区域、简化曲线、把同色非重叠区域打包成复合路径，必要时降低追踪分辨率来控制对象数；因此高清缩放边缘与可编辑性可以兼顾，但照片级微纹理和连续渐变会被适度压缩。
