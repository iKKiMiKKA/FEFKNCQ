# FEFKNCQ

给 AI agent 用的 skill：把你的 OC 角色做成 [STOMPGAME](https://ikkimikka.net/stompgame/)
（`?character=custom`）能直接导入的自定义角色图，并自动开始游戏。

仓库：<https://github.com/ikkimikka/FEFKNCQ>

> 仓库原名 `stompgama`，2026-11-10 更名为 `FEFKNCQ`；旧地址会自动重定向。
> skill 内部标识仍为 `stompgama`（小写，符合 skill 命名规范），不影响触发。

## 一句话用法

把下面这句发给支持 skill / 能调用生图的 AI agent（豆包电脑版、百度搭子、workbuddy 等），
附上你的 OC 参考图即可：

```
帮我用 github 上的 FEFKNCQ 制作我的 OC 角色并进行大脚踩踏游戏
```

agent 会：判定素材模式 → 按 `references/prompts.md` 逐格生成 26 张图 → 合成 1024×1024
`custom.png` → 校验 → 打开游戏页面自动上传 → 点击开始。之后可以直接说
"第 3 个表情再凶一点"之类的调整，agent 只重画对应格子。

### 你可以提供的素材（任意一种都行）

| 素材 | 说明 |
|---|---|
| 头像 + 脚 | 最佳，角色最还原 |
| 一张全身图 | 自动裁出头/脚作参考 |
| 头像 + 一张手的图 | 手部图只借用线条/配色/饰物风格，脚的结构按官方示例推导 |

## 这个 skill 保证什么

- **保证**：坐标、尺寸、透明度、UI 装饰像素、帧间无突变、导入即可用。
- **不保证**：AI 画得像不像 OC。画面质量靠与 agent 继续讨论、逐格重画。

核心做法：不让图像模型一次画出整张精灵表，而是**逐格生成 + 脚本按坐标合成**，
并把官方 `generic.png` 的 UI 装饰像素原样保留。

## 快速开始（手动跑一遍）

```bash
# 1. 取官方底板（仓库不打包作者原图）
curl -L -o generic.png https://ikkimikka.net/stompgame/generic.png

# 2. 把逐格生成的图片放到 frames/，命名见 references/prompts.md
#    front_0.png ... front_5.png, back_0..4.png,
#    normal_0..5.png, excite_0..5.png, tired_0.png, tired_1.png, endscreen.png

# 3. 合成 + 校验
python scripts/build_sheet.py --frames frames/ --base generic.png --out custom.png --bg auto
python scripts/validate.py --sheet custom.png --base generic.png --report custom.report.json

# 4. 自动导入并开始（可选依赖）
pip install -r requirements-browser.txt
playwright install chromium
python scripts/import_game.py --image custom.png
```

也可以不装 Playwright：打开 <https://ikkimikka.net/stompgame/?character=custom>，
把 `custom.png` 拖进上传框，再点击画布开始。

## 目录

```
SKILL.md                        agent 主指令
references/layout.md            唯一坐标契约（1024×1024 全部切片）
references/frame-semantics.md   26 格姿态/表情语义 + 防动作突变约束
references/input-profiles.md    三种素材模式的容错与降级
references/prompts.md           逐格生图提示词模板
references/import.md            自动导入、验收清单、故障排查
references/upstream.md          底板来源、SHA256、合规、版本漂移
scripts/layout.py               坐标常量（唯一可改的坐标来源）
scripts/png.py                  零依赖 PNG 读写/去背/缩放/统计
scripts/build_sheet.py          合成
scripts/validate.py             校验（含帧间突变检测）
scripts/import_game.py          Playwright 自动上传参考实现
assets/settings.template.json   ZIP 全定制模板
```

## 依赖

- 核心脚本：Python 3.8+，**仅标准库**（无 Pillow / numpy）。
- 浏览器自动上传：可选 `playwright>=1.44,<2`（见 `requirements-browser.txt`）。
  agent 若自带浏览器工具，可完全跳过。
- 在中文 Windows 上运行 skill-creator 的 `quick_validate.py` / `package_skill.py` 时，
  先设 `$env:PYTHONUTF8='1'`，否则脚本按 GBK 读取中文 `SKILL.md` 会报编码错误。

## 关键事实（踩过的坑）

- `?character=custom` 页面在**未上传**时会隐藏爪与头像，`intro_screen()` 直接返回；只有上传
  文件触发 `custom_loaded=true` 后才恢复。所以"打开链接直接玩"要用 `?giant=` / `?json=` 参数，
  不能带 `character=custom`。
- 切片算法：精灵数组第 7 项 `sp=3` 表示每列 3 帧、向下排满再向右换列。
  左侧 11 个爪格 = 前爪 6 帧 + 后爪 5 帧；右侧 14 个表情格 = 常态 6 + 兴奋 6 + 疲惫 2。
- 头像框、棋盘底、名字条、爪影点阵是 UI 装饰，必须原样保留；`validate.py` 逐像素比对。

## 合规

- 本项目为非官方第三方 skill，与游戏作者 ikkimikka 无关联。
- 仓库**不打包**作者的 `generic.png`，运行时从官方地址下载；出处与 SHA256 见
  `references/upstream.md`。
- OC 素材需由用户自行确认使用权；生成内容请遵守所用生图服务与上游站点条款。
- 游戏为"巨人踩踏小人"的卡通玩法，公开分享时请自行标注受众。
