# 导入游戏：ZIP 默认自动上传，桌面同时给 PNG 与 ZIP

## 交付物（build_sheet.py 默认产出）

| 文件 | 位置 | 用途 |
|---|---|---|
| `custom.png` | 与 `--out` 同目录 + **桌面副本** | 纯图片上传，用户手动选择时用 |
| `custom.zip` | 与 `--out` 同目录 + **桌面副本** | **默认上传对象**：内含图片与根目录 `settings.json` |

ZIP 内的 `settings.json` 来自 `assets/settings.template.json`（可用 `--settings` 换成自定义文件），
`images.giant` 自动指向 ZIP 内图片的文件名，`--name "<OC 名字>"` 会写入 `giant.name`。
模板还含 `giant.description`、`congrats`、`grades`（评级）、`stickers`；要改评级/贴纸时
复制一份 settings.json 用 `--settings` 传入。**不要把文件夹本身压进 ZIP，两个文件都在根。**

模板的 `"stickers": []` 会**清空**游戏默认贴纸（官方贴纸坐标按默认爪图设计，套到 OC 上
容易错位，默认清空更安全）；想保留官方默认贴纸就加 `--keep-default-stickers`，
脚本会省略该键。打包时脚本会校验 settings.json，危险改动写入 report 的 `warnings`。

桌面副本路径记在 `custom.report.json` 的 `desktop_copy`（PNG）与 `desktop_zip`（ZIP），
agent 应把两个路径都告诉用户；同名文件不会被覆盖（改用带时间戳的名字）。

## 主路线（默认）：有浏览器能力的 agent 上传 ZIP

1. 用浏览器打开 `https://ikkimikka.net/stompgame/?character=custom`（有头模式，保持窗口）。
2. 等待运行时注入的 `#upload` 出现（该 input 由 CUSTOM UPLOAD 面板动态写入，不在初始 HTML 里）。
3. 把本地 `custom.zip` 设置到 `#upload`：
   - Playwright：`page.set_input_files("#upload", "/abs/path/custom.zip")`
   - 参考实现：`python scripts/import_game.py`（`--image` 默认就是 `custom.zip`）
   - 其他浏览器工具：等价于给 `input[type=file]` 选择文件；拖放亦可。
4. 等待约 2–3 秒。上传会解析 ZIP 根目录的 `settings.json`，触发
   `textures.set("giant", ...)`、`custom_loaded = true`、`cancelAnimationFrame` 与
   `done_loading()` 重启游戏；此时爪与右上头像 HUD 才恢复显示。
5. 点击画布 `#outcanvas` 任意位置，进入 `CLICK TO BEGIN` → 开始游戏。
6. 保持浏览器窗口打开，把游戏交给用户。

`scripts/import_game.py` 只是参考实现（需 `requirements-browser.txt`）：默认在真实终端里
`input()` 等待回车以保持窗口；agent/CI 的非交互环境 stdin 为 EOF，窗口会随进程退出而关闭
（脚本会打印 NOTE 提示）。**agent 自带浏览器工具时优先用自带工具**，要立即关闭可传 `--no-wait`。

## 备选：用户自己上传（桌面二选一）

桌面同时有 `custom.png` 与 `custom.zip`，用户打开上传页后拖任意一份进上传框即可：
选 PNG 最省事，选 ZIP 会额外应用角色名/描述/评级/贴纸。**两份是同一张图，不要重新生成。**
agent 没有浏览器能力、或用户只想自己上传时走这条路。
用户明确指定了保存位置时脚本加 `--no-desktop`，两个文件都按指定位置输出、不产生桌面副本。

## 上传后的游戏行为（必须知道）

- **上传 ZIP（默认）**：`settings.json` 生效，`giant.name` 为设定名字，`giant.description`、
  `congrats`、`grades`（评级）、`stickers` 按模板/自定义值加载；结算页会显示评级。
- **上传 PNG**：游戏用文件名去 `.png` 当名字（自动命名后会带时间戳/角色名，故**角色名以 ZIP 内 `settings.json` 为准**，优先上传 ZIP），
  `giant.description = ""`，`giant.grades = false`（评级关闭，结算横幅只画单层、无评级抖动残影）；
  **贴纸保持游戏默认**（只有贴纸编辑器模式 `?stickers=true` 才清空）。反之默认 ZIP 模板的
  `"stickers": []` 是整体替换，会清空默认贴纸——这是两种上传方式的观感差异之一。
- 两种情况都只替换 `giant` 纹理；小人、背景、音效仍是默认 `city.png` 与站点资源；
  **所有坐标仍按 `references/layout.md`**。

### 验收清单（导入后逐项确认）

- [ ] 屏幕上有前爪与远景后爪，移动鼠标时前爪跟随
- [ ] 右上角 128×128 头像框内是 OC 的脸，不是白块/错位
- [ ] 抬爪、落下、加压时爪的姿态连续，无突然换脚/换视角
- [ ] 地面有爪影，不是白色方块
- [ ] 结算画面顶部横幅是自定义图
- [ ] **上传 ZIP 时**开场名字条显示设定角色名，结算页出现评级
- [ ] 无白底方块覆盖游戏画面（去背失败的最典型症状）

## 进阶：自定义 settings.json

复制 `assets/settings.template.json` 改好后用 `--settings my.json` 传给 `build_sheet.py`，
脚本会重新打包并校验。**ZIP 内 `settings.json` 必须在根**；任何带 `url` 的属性都能写
ZIP 内相对路径（加载时先在包内找，再回退站点 URL），所以自定义背景图/音效可直接放进包里。

游戏 `apply_settings()` 只认 11 个顶层字段，分两种语义：

| 语义 | 字段 | 常用可设内容 |
|---|---|---|
| **浅合并**（不写即用游戏默认） | `giant` | `name`、`description`（开场多行介绍）、`congrats`、`grades` |
| | `images` | `giant`（脚本自动写包内图片名）、`env`（背景图） |
| | `set` | `tiny_name*`、`bg_color`、`day_night_cycle`、`phrase_changes`、`closed_walls`、`starter_bugs`、`show_*` HUD 开关、`ambience_url` |
| | `bug` | 小人动画/物理、`fits` 替代小人、`special_kill` |
| | `paw` | 爪手感、`steamroller`、`wetness`、体力参数 |
| | `ego` | 开关、增减倍率、`step` |
| | `stain` | 污渍数量 |
| **整体替换**（写了就全量覆盖） | `sound_urls` | `[URL, tag]` 列表；**必须列全想要的音效**，省略该键才用默认 |
| | `stickers` | 61 条爪上贴纸坐标；`[]` 即清空 |
| | `demographics` | 小人分布权重 |
| | `ego_tiers` | 6 档 ego 阈值 |

评级 `grades` 每条是 `[stat tag, 操作符, 数值, hint]`（可用 stat 见官方
`generic.zip/stats.txt`，操作符为 `< > <= >= = !=` 六种）；`grades: null` 关闭评级并直接显示
`congrats`；默认 5 条对应 6 个 rank，超过需重定义 `set.grade_spr`；条件按难度**从难到易**排序，
结算显示最后一个未满足条件的 hint。名字/描述/台词由 canvas 的 `VT323` 等宽像素字体绘制，
**建议短英文**：中文会字体回退，且宽度按 6px/字符估算容易溢出。

**不要改的字段**：任何 `*_spr` 坐标（`front_spr` / `normal_spr` / `end_spr` / `grade_spr` 等）、
`ego.levels`、`paw.width`、`paw.stomp_masks`、`ego_tiers` 的长度——它们与 1024×1024 的
26 格切片契约绑定，改了会让整套图错位或表情帧数不匹配。脚本对这类字段、`grades` 结构、
未知顶层 key、`sound_urls` 全量替换都会打印 WARN，交付前逐条确认。

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
| 上传 ZIP 后名字/评级没生效 | `settings.json` 不在 ZIP 根，或 `images.giant` 指向了别的文件名 | 用 `build_sheet.py` 重新打包（脚本自动处理），或 `python -m zipfile -l custom.zip` 检查 |
| 白色方块盖住画面 | 生成图未去背 | 保持默认 `--bg auto` 重新合成（必要时显式 `--bg white`）；`validate.py` 的 `plate:*` 会判 FAIL |
| 头像框里是错位的图 | 表情格坐标/尺寸不对 | 核对 `layout.md`，重新 `build_sheet.py` |
| 爪影消失 / 变成实色块 | 装饰区被 AI 重画 | `validate.py` 会 FAIL；从官方底板重取装饰区 |
| 上传后游戏没反应 | 文件类型不是 `.png`/`.zip`，或 input 未等到 | 确认扩展名与 `wait_for_selector("#upload")` |
| 脚还悬在空中，小人却已被踩死 | 爪格脚底离格子底边留了透明空隙（游戏按格底边对齐 `paw_y`，不看图片内容） | 重跑 `build_sheet.py`：爪格会自动裁剪透明边并底对齐；`validate.py` 的 `ground:*` 会拦截 >6px 的留白 |
| ZIP 上传后没声音 | `sound_urls` 是整体替换，只写了部分标签 | 补全想要的标签，或整个删掉该键使用默认音效 |
| 爪上看不到残留小人/贴纸 | 模板 `"stickers": []` 清空了默认贴纸 | 加 `--keep-default-stickers` 重新打包；需目检官方坐标是否贴合 OC 爪形 |
| 角色名/评级台词显示不全 | 文本用 `VT323` 等宽字体按 6px/字符排版 | 改用短英文，缩短 `name` / `description` / `congrats` / hint |
| `settings.json` 有 WARN | 改了坐标类字段或评级结构 | 按 `custom.report.json` 的 warnings 逐条修，详见上文「不要改的字段」 |
| 无法自动上传 | agent 无浏览器能力 | 把桌面两份路径告诉用户，让用户手动拖入 `?character=custom` 页面 |
