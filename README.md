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

agent 会：判定素材模式 → **首版只生成 8 张必生图**（`front_0` / `front_3` / `front_5` /
`back_0` / `normal_1` / `normal_3` / `normal_5` / `endscreen`）→ 其余 18 格由脚本自动
复用同组基准帧 → 合成 1024×1024 `custom.png` → 校验 → 打开游戏页面自动上传 → 点击开始。
生成时**默认尝试并发**；通道不支持并发或结果串图时只回退为逐格串行，其余流程不变。

**如果你没有指定图片放在哪里**，脚本会额外把成品**复制一份到桌面**（`custom.png`，
同名文件不会被覆盖），可以直接拖进上传框自己上传；agent 会把桌面路径告诉你。
若你指定了保存位置，agent 会改用 `--no-desktop`，不再额外复制。

**跑通能玩后 agent 会主动询问是否补画更多细节**（兴奋表情、疲惫两帧、抬爪中间帧等），
用户确认前不会自行加图。补细节只需往 `frames/` 多放几张 `<帧名>.png` 重新合成，
单格文件会自动覆盖该格的复用，无需改配置。之后也可以直接说
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

# 2. 首版只放 8 张图到 frames/（命名见 references/prompts.md）
#    front_0.png / front_3.png / front_5.png / back_0.png
#    normal_1.png / normal_3.png / normal_5.png / endscreen.png
#    其余 18 格由 build_sheet.py 按 REUSE_MAP 自动复制，不必生成

# 2b. 需要编号对照图时（含上游像素，仅本地查看，不要提交）
python scripts/make_numbered_map.py --base generic.png --out numbered_map.png

# 3. 合成 + 校验（默认另复制一份到桌面，路径见 custom.report.json 的 desktop_copy）
python scripts/build_sheet.py --frames frames/ --base generic.png --out custom.png --bg auto
python scripts/validate.py --sheet custom.png --base generic.png --report custom.report.json

# 3b. 已指定保存位置、不想要桌面副本时
python scripts/build_sheet.py --frames frames/ --base generic.png --out D:/pic/my.png --no-desktop

# 4. 自动导入并开始（可选依赖）
pip install -r requirements-browser.txt
playwright install chromium
python scripts/import_game.py --image custom.png
```

也可以不装 Playwright：打开 <https://ikkimikka.net/stompgame/?character=custom>，
把桌面上那份 `custom.png` 拖进上传框，再点击画布开始。

## 目录

```
SKILL.md                        agent 主指令
references/layout.md            唯一坐标契约（1024×1024 全部切片）
references/frame-semantics.md   26 格姿态/表情语义 + 防动作突变约束
references/input-profiles.md    三种素材模式的容错与降级
references/numbering.md         34 个格位编号、出现时机与频率
references/prompts.md           首版 8 格提示词 + 复用映射 + 补细节优先级
references/import.md            自动导入、验收清单、故障排查
references/upstream.md          底板来源、SHA256、合规、版本漂移
scripts/layout.py               坐标常量 + MUST_GENERATE / REUSE_MAP / NUMBERED_CELLS
scripts/png.py                  零依赖 PNG 读写/去背/缩放/统计
scripts/build_sheet.py          合成、复用未生成格、默认复制一份到桌面
scripts/validate.py             校验（含帧间突变检测）
scripts/import_game.py          Playwright 自动上传参考实现
scripts/make_numbered_map.py    生成带编号的标注图（本地产出）
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
- 编号是**图位顺序**，不是动画顺序：前爪为 `P01→P05→P09→P02→P06→P10`。
  `F09–F12`（高 ego）、`F13/F14`（疲惫）、`P08/P10`（高压）出现频率低，`X01–X03`
  默认永不采样——这是首版敢复用 18 格的依据，详见 `references/numbering.md`。
- 桌面副本由 `build_sheet.py` 用标准库探测：Windows 先问 shell API（兼容 OneDrive 重定向），
  其余平台依次尝试 `~/Desktop`、`~/桌面`、`~/OneDrive*/Desktop`；可用 `STOMP_DESKTOP_DIR`
  或 `--desktop-dir` 覆盖。桌面已有 `custom.png` 时改存带时间戳的文件名，绝不覆盖。
- **脚必须贴格子底边**：游戏按爪格底边对齐 `paw_y`（碰撞只看 `paw_y` 与 `floor_y=228`，
  不读图片内容），官方底板触地帧脚底留白为 0px。若脚底离格底约 50px，显示放大 2 倍后
  就是约 100px 的"悬空"，小人却已被判定踩死。`build_sheet.py` 现在会对爪格自动裁剪透明边
  并底对齐，`validate.py` 的 `ground:*` 会拦截超过 6px 的留白。

## 合规

- 本项目为非官方第三方 skill，与游戏作者 ikkimikka 无关联。
- 仓库**不打包**作者的 `generic.png`，运行时从官方地址下载；出处与 SHA256 见
  `references/upstream.md`。
- OC 素材需由用户自行确认使用权；生成内容请遵守所用生图服务与上游站点条款。
- 游戏为"巨人踩踏小人"的卡通玩法，公开分享时请自行标注受众。
