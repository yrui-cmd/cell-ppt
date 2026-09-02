# Nature PPT

Nature PPT 将 PNG、JPEG、WebP 或 SVG 参考图重建为实际可用的 PowerPoint 内容。它不会把“产生了很多路径”误称为“很好编辑”，而是先判断复杂度，再选择合适的输出方式。

## 0.5.0 的工作方式

```text
参考图 → 复杂度预检 → 本地或可选线上矢量化 → SVG 校验 → 本地 PowerPoint 绘制
                     └→ 照片级素材使用混合分层模式
```

- 原生模式：适合扁平科研图、流程图、机制图和有限色彩图。SVG 路径和文字会转为 PowerPoint 原生对象。
- 混合模式：适合照片、3D 渲染、玻璃、金属、辉光、软阴影和密集渐变。复杂连续色调保留为高清背景，文字和关键科研元素在上层重建为可编辑对象。
- 存档模式：生成最高保真 SVG，但不会强行把百万级路径塞进 PowerPoint。

默认原生对象安全上限为 50,000。超过上限时自动保留 SVG 并改用混合输出，除非用户明确接受大型、缓慢的原生文稿。

## 矢量化后端

本地模式无需 API Key，使用固定并校验哈希的 VTracer 1.0.0-alpha.4。

项目同时提供可选 HTTPS 矢量服务适配器。线上服务并非必需，也不会在未配置时自动上传图片。服务只负责返回 SVG，SVG 会在本地完成规范化、结构校验和 PowerPoint 绘制。接口契约见 Skill 的 `references/remote-backend.md`。

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
使用 $nature-ppt，把这张参考图重建为实际可编辑的 PowerPoint；先判断应该使用原生还是混合模式，并说明哪些部分可编辑。
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

## 透明度说明

“可编辑”必须按层说明。原生模式中的路径和文字可逐个编辑；混合模式中的背景仍是图片，但上层文字、箭头和重建对象可编辑。项目不会把混合结果描述为全原生矢量。
