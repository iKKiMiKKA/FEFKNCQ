# FEFKNCQ

给 AI agent 用的 skill：把你的 OC 角色做成 [STOMPGAME](https://ikkimikka.net/stompgame/)
（`?character=custom`）能直接导入的自定义角色图 `custom.png`，同时产出可设置角色名、
描述与结算评级的 `custom.zip`，并自动开始游戏。

仓库：<https://github.com/ikkimikka/FEFKNCQ>


## 合规

- 本项目为非官方第三方 skill，与游戏作者 ikkimikka 无关联。
- 仓库**不打包**作者的 `generic.png`，运行时从官方地址下载；出处与 SHA256 见
  `references/upstream.md`。
- **分发请用 GitHub 仓库 / zipball**：不要用 skill-creator 的 `package_skill.py` 直接打包
  当前工作目录，它会把 `.git/`、`__pycache__/` 以及含上游像素的本地标注图
  `numbered_map.png` 一起打进 zip。含像素产物（`custom.png`、`custom.zip`、标注图）一律
  不提交、输出到仓库外（`.gitignore` 已覆盖常见文件名）。
- OC 素材需由用户自行确认使用权；生成内容请遵守所用生图服务与上游站点条款。
- 游戏为"巨人踩踏小人"的卡通玩法，公开分享时请自行标注受众。
