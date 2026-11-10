# STOMPGAME 自定义图布局规格（唯一坐标契约）

游戏页面：`https://ikkimikka.net/stompgame/`（内联 JS 约 3839 行，无构建产物）。
自定义角色图是一张 **1024×1024 的 RGBA PNG**，游戏只按固定坐标切片，不读文件名、不识别内容。
坐标均为 `(x, y, w, h)`，原点左上，X 向右、Y 向下。

## 1. 切片数组与翻页算法

精灵数组：`["giant", x, y, w, h, 向下?, 每列帧数]`。源码 `sprite()` 计算
`fy = f % sp`、`fx = floor(f / sp)`：当 `sp = 3` 时，**每列 3 帧，先向下排 3 行，再向右换一列**。

- `front_spr = ["giant", 0, 0, 160, 256, true, 3]`
- `back_spr  = ["giant", 320, 0, 160, 256, true, 3]`
- `normal_spr = ["giant", 768, 0, 128, 128, true]`（无 sp，单列向下）
- `excite_spr = ["giant", 896, 0, 128, 128, true]`
- `exhaust_spr = ["giant", 768, 896, 128, 128]`（无向下标志，帧 0/1 向右取两格）
- `frame_spr = ["giant", 640, 0, 128, 128]`
- `bg_spr = ["giant", 640, 128, 128, 128]`
- `intro_flag_spr = ["giant", 640, 256, 128, 32]`
- `end_spr = ["giant", 0, 768, 256, 128]`
- `shadow_end_spr = ["giant", 745, 998, 8, 21]`
- `shadow_mid_spr = ["giant", 751, 998, 4, 21]`

## 2. 可重画单元格（26 格）

| 名称 | 坐标 | 尺寸 | 帧 / 用途 |
|---|---|---|---|
| `front_0` | (0, 0) | 160×256 | 前爪帧 0：`paw_state=0`，爪在屏幕上半，最高抬起 |
| `front_1` | (0, 256) | 160×256 | 前爪帧 1：`paw_state=1`，`paw_y > h/2` |
| `front_2` | (0, 512) | 160×256 | 前爪帧 2：`paw_state=2`，`paw_y > h*0.75` |
| `front_3` | (160, 0) | 160×256 | 前爪帧 3：`paw_state=3`，刚触地，压力≈0 |
| `front_4` | (160, 256) | 160×256 | 前爪帧 4：触地 + `stomp_frame=1`（约 `pressure 0.3–0.5`），或爪被顶住时的特殊帧 |
| `front_5` | (160, 512) | 160×256 | 前爪帧 5：触地 + `stomp_frame=2`（约 `pressure > 0.5`），最深压力 |
| `back_0` | (320, 0) | 160×256 | 后爪帧 0：`round(pressure*4)=0` |
| `back_1` | (320, 256) | 160×256 | 后爪帧 1 |
| `back_2` | (320, 512) | 160×256 | 后爪帧 2 |
| `back_3` | (480, 0) | 160×256 | 后爪帧 3 |
| `back_4` | (480, 256) | 160×256 | 后爪帧 4（最大压力） |
| `normal_0..5` | (768, 0/128/256/384/512/640) | 128×128 | 常态头像，帧 = `ego_level = floor(ego_climb/1000)`，0→5 ego 渐高 |
| `excite_0..5` | (896, 0/128/256/384/512/640) | 128×128 | 兴奋头像：ego 增加后 0.5 秒内，或 `finished` 时 |
| `tired_0` | (768, 896) | 128×128 | 疲惫动画帧 0：`exhausted`（体力耗尽 / WIPEOUT） |
| `tired_1` | (896, 896) | 128×128 | 疲惫动画帧 1，与上一格交替 |
| `endscreen` | (0, 768) | 256×128 | 结算画面顶部横幅 |

## 3. 禁止重画区域（UI 装饰）

| 名称 | 坐标 | 说明 |
|---|---|---|
| `portrait_frame` | (640, 0, 128, 128) | 白色圆角边框，盖在头像最上层 |
| `portrait_bg` | (640, 128, 128, 128) | 棋盘格底 + 右下灰色斜角 |
| `intro_flag` | (640, 256, 128, 32) | 开场画面角色名底条 |
| `shadow_end` | (745, 998, 8, 21) | 爪影端头（点阵） |
| `shadow_mid` | (751, 998, 4, 21) | 爪影中段（平铺） |

官方说明明确要求："the paw shadow … is best left unmodified unless you know what you're doing"。
`build_sheet.py` 从官方底板原样复制这些像素；`validate.py` 逐像素比对，改动即判失败。

## 4. 保留空白格

`(480,512,160,256)`、`(768,768,128,128)`、`(896,768,128,128)` 默认不被采样，必须留空。

## 5. 屏幕位置（内部逻辑画布 400×240，显示放大 2 倍到 800×480）

- 前爪：`paw_x - 80`，脚底对齐 `paw_y`，水平跟随鼠标；地面 `floor_y = 228`。
- 后爪：固定 `(160, 204)` 底边对齐，属远景脚；压力越大越淡。
- 头像 HUD：右上角 `(272..400, 0..128)`；绘制顺序 `bg → 表情 → frame`。
- 开场名字条：屏幕左上 `(0, 18)`，角色名文字叠在其上。
- 结算横幅：顶部居中 `(72..328, 8..136)`。
- 爪影：地面 `y ≈ 224`，横向拼接。

## 6. 页面参数（导入相关）

- `?character=custom`：**仅进入上传面板**。此时 `hide_paws = hide_cam = true`、`intro_screen()` 提前 return，爪/头像/名字条全部隐藏，游戏不能玩。上传文件后 `custom_loaded = true` 才重启为正常游戏。
- `?giant=<URL>`：直接把 `images.giant` 换成该图片（`custom=false`，可正常开玩）。
- `?json=<JSON 或 base64>`：`apply_settings()` 可一次覆盖 `images`、`giant`（名字/描述/评级）、`paw`、`ego` 等。
- `?extra=<settings.json URL>`：从 URL 加载完整配置。
- 上传入口：运行时注入的 `<input id="upload" type="file" accept=".png, .zip">`，只有 `change` 事件；拖放是浏览器对 file input 的原生行为。
- 站点 CSP 允许跨源 fetch，但远程图片服务器必须返回 CORS 头；`raw.githubusercontent.com` 返回 `Access-Control-Allow-Origin: *`。

## 7. 依据与版本

- 页面内联源码：定义 135、178、223、262–264、296–304 行；绘制 2445–2479、2660–2700、3409–3414、3692、3754–3756 行；隐藏条件 3038–3040、3321–3322 行。
- `generic.zip` 内 `HOW TO MAKE A STOMPGAME CHARACTER!.txt` 与 `settings.json`（后者原样重列全部坐标）。
- 对 `generic.png` 的逐格像素统计确认上述占用与空白格。
- 底板 SHA256：`EF952E7FD566464B54053D1610661C85D34339D5082FB49C2BE73EE5E8050F2D`。
  若哈希不符，说明作者改过模板，**必须重新核对本表**再生成，不要盲目沿用。
