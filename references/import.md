# 导入游戏：本地图片 + 浏览器自动上传

## 主路线（默认，最稳，不依赖外部图床）

目标：生成 `custom.png` 后，让 AI agent 自动把它填进页面的上传控件并开始游戏。

### 给 AI agent 的执行步骤

1. 用浏览器打开 `https://ikkimikka.net/stompgame/?character=custom`（建议有头模式，保持窗口让用户能玩）。
2. 等待运行时注入的 `#upload` 出现（该 input 是 CUSTOM UPLOAD 面板动态写入的，不在初始 HTML 里）。
3. 把本地 `custom.png` 设置到 `#upload`：
   - Playwright：`page.set_input_files("#upload", "/abs/path/custom.png")`
   - 其他浏览器工具：等价于给 `input[type=file]` 选择文件；拖放亦可。
4. 等待约 2–3 秒。上传会触发 `textures.set("giant", ...)`、`custom_loaded = true`、
   `cancelAnimationFrame` 与 `done_loading()` 重启游戏；此时爪与右上头像 HUD 才恢复显示。
5. 点击画布 `#outcanvas` 任意位置，进入 `CLICK TO BEGIN` → 开始游戏。
6. 保持浏览器窗口打开，把游戏交给用户。

参考实现：`scripts/import_game.py --image custom.png`（需 `requirements-browser.txt`）。
若 agent 自带浏览器工具，优先用自带工具按上述步骤操作，不要用脚本的 `--wait` 阻塞会话。

### 手动上传（用户自己来）

`build_sheet.py` 默认会把同一张成品**复制一份到桌面**（`custom.png`，已有同名文件不会被
覆盖），路径记在 `custom.report.json` 的 `desktop_copy`。agent 应把路径告诉用户，用户打开
`https://ikkimikka.net/stompgame/?character=custom` 把桌面那份拖进上传框即可。
agent 没有浏览器能力、或用户只想自己上传时走这条路；桌面副本与自动上传用的是同一张图，
**不要重新生成**。用户明确指定了保存位置时脚本加 `--no-desktop`，不产生桌面副本。

### 上传 PNG 后的游戏行为（必须知道）

- `giant.name = 文件名去 .png`（例如 `custom.png` → `CUSTOM`），`giant.description = ""`。
- `giant.grades = false`：评级系统关闭，结算横幅只画单层、不显示评级抖动残影。
- 默认贴纸被清空；小人、背景、音效仍是默认 `city.png` 与站点资源。
- 只替换了 `giant` 纹理，**所有坐标仍按 `references/layout.md`**。

### 验收清单（导入后逐项确认）

- [ ] 屏幕上有前爪与远景后爪，移动鼠标时前爪跟随
- [ ] 右上角 128×128 头像框内是 OC 的脸，不是白块/错位
- [ ] 抬爪、落下、加压时爪的姿态连续，无突然换脚/换视角
- [ ] 地面有爪影，不是白色方块
- [ ] 结算画面顶部横幅是自定义图
- [ ] 无白底方块覆盖游戏画面（去背失败的最典型症状）

## 备选路线 A：ZIP 全定制

把 `custom.png` 与根目录的 `settings.json` 一起打包（**不要**把文件夹本身压缩进去）。
`settings.json` 可覆盖 `images.giant`、角色名/描述/评级、贴纸、音效、以及所有 `*_spr` 坐标。
模板见 `assets/settings.template.json`。上传 `.zip` 同样走 `#upload`。

注意：ZIP 内的 `settings.json` 必须在根；相对路径资源（如 `custom.png`）会先在 ZIP 内查找。

## 备选路线 B：免上传直达链接（可选，非默认）

- `?giant=<图片URL>`：只换图，`custom=false`，打开即可玩。
- `?json=<URL 编码的 JSON 或 base64>`：可同时设置 `images.giant`、`giant.name/description/grades` 等。
- `?extra=<settings.json 的 URL>`：加载完整配置。

限制与坑：

- **不要**在直达链接里带 `character=custom`：该模式会隐藏爪与头像且跳过开场，等于不能玩。
- 远程图片服务器必须允许跨域（实测 `raw.githubusercontent.com` 返回 `Access-Control-Allow-Origin: *`，
  站点 CSP 也允许跨源 fetch），但**国内网络能否访问该托管源不可控**，所以默认仍用本地上传。
- 直达链接只换 `giant` 纹理，不换 ZIP 里的音效/背景/贴纸等资源。
- 不要把图片塞进 `data:` URL：体积过大，URL 长度不可靠。

## 故障排查

| 症状 | 原因 | 处理 |
|---|---|---|
| 打开页面看不到爪和头像 | 用了 `?character=custom` 但未上传 | 完成上传后再看，或改用 `?giant=` 直达链接 |
| 白色方块盖住画面 | 生成图未去背 | `--bg white` 重新合成，或用 `--bg none` + 已抠好的透明图 |
| 头像框里是错位的图 | 表情格坐标/尺寸不对 | 核对 `layout.md`，重新 `build_sheet.py` |
| 爪影消失 / 变成实色块 | 装饰区被 AI 重画 | `validate.py` 会 FAIL；从官方底板重取装饰区 |
| 上传后游戏没反应 | 文件类型不是 `.png`/`.zip`，或 input 未等到 | 确认扩展名与 `wait_for_selector("#upload")` |
| 无法自动上传 | agent 无浏览器能力 | 生成文件后让用户手动拖入 `?character=custom` 页面 |
