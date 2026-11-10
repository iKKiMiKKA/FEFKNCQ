# 上游资源与合规

## 官方底板（唯一需要的上游图片）

- 游戏：<https://ikkimikka.net/stompgame/>
- 自定义上传页：<https://ikkimikka.net/stompgame/?character=custom>
- 示例 PNG：<https://ikkimikka.net/stompgame/generic.png>（1024×1024 RGBA）
- 示例 ZIP：<https://ikkimikka.net/stompgame/generic.zip>
  （内含 `settings.json`、`HOW TO MAKE A STOMPGAME CHARACTER!.txt`、`stats.txt`、`background.png`）
- 作者：ikkimikka；站点托管于 Neocities；页面提供 Patreon 链接。
- 本 skill 记录的版本（2026-11-10）SHA256：
  `EF952E7FD566464B54053D1610661C85D34339D5082FB49C2BE73EE5E8050F2D`

## 为什么仓库不打包 generic.png

- 该图是作者提供的示例模板，官方说明鼓励"download ... and toy around"（下载后自行改画），
  但**再分发原图**的授权并不明确；本仓库只保存坐标规格与校验值，运行时从官方地址下载。
- 底板只用于取 UI 装饰像素（头像框、棋盘底、名字条、爪影点阵），不参与角色画面创作。
- 请保留上游出处；本 skill 为非官方第三方工具，与作者无关联。

## 下载底板

PowerShell：

```powershell
curl.exe -L -o generic.png https://ikkimikka.net/stompgame/generic.png
(Get-FileHash generic.png -Algorithm SHA256).Hash
```

curl / bash：

```bash
curl -L -o generic.png https://ikkimikka.net/stompgame/generic.png
sha256sum generic.png
```

Python（标准库）：

```python
python -c "import urllib.request; urllib.request.urlretrieve('https://ikkimikka.net/stompgame/generic.png','generic.png')"
```

`build_sheet.py` 会计算底板哈希并与 `layout.py:BASE_SHA256` 比较；不一致时只警告并继续，
但**必须**重新核对 `references/layout.md` 的坐标表（作者改版会让整套切片失效）。

## 版本漂移处理

1. 重新下载 `generic.png` 与 `generic.zip`。
2. 查看游戏页面源代码中 `front_spr` / `back_spr` / `normal_spr` / `excite_spr` / `exhaust_spr` /
   `frame_spr` / `bg_spr` / `intro_flag_spr` / `end_spr` / `shadow_*_spr` 的定义。
3. 更新 `scripts/layout.py` 的 `CELLS` / `DECOR` / `BLANK_CELLS` 与 `BASE_SHA256`。
4. 更新 `references/layout.md`、`references/prompts.md` 的帧数与坐标描述。
5. 用 `scripts/validate.py` 重新验证一张用新底板合成的图。

## 用户素材

- OC 头像/脚/全身图由用户提供，用户需确认自己有权使用。
- 生成结果由用户自行承担；公开分享请遵守所用图像生成服务与上游站点的条款。
- 游戏题材为"巨人踩踏小人"的卡通玩法；公开仓库与生成内容请自行标注受众。
