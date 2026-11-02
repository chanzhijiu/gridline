# GRIDLINE — 赛车 × 电竞一站式看板

一个纯静态单页看板，把 **Formula 1、Formula E、英雄联盟（S16 全球总决赛 + LPL）、VCT、KPL、IVL** 放进同一张时间表。深色仪表盘风格，中英双语界面，按系列切换主题色。

**在线地址：<https://chanzhijiu.github.io/gridline/>**

![views](https://img.shields.io/badge/views-F1%20%C2%B7%20FE%20%C2%B7%20LoL%20%C2%B7%20VCT%20%C2%B7%20KPL%20%C2%B7%20IVL-ff3b30)

## 快速打开

直接双击 `index.html` 即可。数据已内嵌在 `data.js` 里，不需要本地服务器；核心内容离线可看，队徽与在线字体在联网时显示更完整（加载失败会自动回退）。

如果浏览器对 `file://` 有限制，可以在本目录起一个静态服务器：

```bash
python -m http.server 8080
# 打开 http://127.0.0.1:8080/
```

### 手机 / 局域网访问

当前已在 `8765` 端口起了静态服务器。手机和电脑连同一个 Wi-Fi 后，手机浏览器打开：

```text
http://192.168.0.116:8765/
```

电脑本机访问 `http://127.0.0.1:8765/`。如果手机打不开，依次检查：是否同一 Wi-Fi、Windows 防火墙是否放行 Python、电脑 IP 是否变化（`ipconfig` 查看 WLAN 的 IPv4 地址）。

重新启动服务器的命令：

```bash
cd E:\dsh-workspace\racehub
python -m http.server 8765 --bind 0.0.0.0
```

手机浏览器可“添加到主屏幕”，获得接近 App 的全屏入口。

### 公网访问

这是纯静态站，不需要后端。推荐用 GitHub Pages：仓库已带 GitHub Actions 工作流，推到 `main` 会自动构建并发布；之后每天北京时间 09:17 自动刷新一次数据快照。

首次部署：

1. 在 GitHub 新建仓库（例如 `gridline`），不要勾选 “Add a README”；
2. 把本目录推到仓库的 `main` 分支；
3. 打开仓库 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**；
4. 等 Actions 里的 “Build and deploy GRIDLINE” 跑完，公开地址是 `https://<用户名>.github.io/gridline/`。

也可以手动触发：**Actions → Build and deploy GRIDLINE → Run workflow**。

其他选择：把整个目录拖到 [Netlify Drop](https://app.netlify.com/drop)，或在 Vercel / Cloudflare Pages 里把构建命令留空、输出目录填根目录。

公网地址生成后，手机和电脑都能直接访问；数据由 Action 每日更新，不必本地重新部署。

## 页面内容

| 板块 | 内容 |
| --- | --- |
| **F1** | 下一站倒计时、车手 / 车队积分榜、上一站领奖台与最快圈、2026 全 23 站赛历（含冲刺周末） |
| **Formula E** | 第 13 赛季 21 站赛历，按比赛周末分组，开幕站倒计时 |
| **英雄联盟** | S16 全球总决赛瑞士轮 16 队积分与本周赛程；LPL 第三赛段登峰组 / 涅槃组积分 |
| **VCT** | VLR.GG 世界排名 5 个主赛区（中国 / 亚太 / 欧洲 / 北美 / 韩国）+ 其他赛区折叠；近期赛程与赛果 |
| **KPL** | 2026 年度总决赛赛段进程、擂台赛大师组 / 精英组积分、全部 54 场赛程赛果（可筛选） |
| **IVL** | 2026 秋季赛全部 90 场赛程赛果（可筛选），下一场倒计时 |

所有时间统一显示为 **北京时间（UTC+8）**。各板块标题区的“完整赛历 / 赛程赛果”按钮会定位到当前板块内对应段落，并保留在地址栏（如 `#kpl-schedule`），可以直接分享该定位。

### 可点击详情

页面里的车手、车队、赛历卡、比赛、战队、赛区、赛段等条目都支持点击 / 键盘回车打开详情面板：

- **F1**：车手档案与逐站成绩、车队积分与胜场、每个分站的完整 22 车手结果；
- **Formula E**：比赛周末的场次、日期与倒计时；
- **LoL**：Worlds 战队瑞士轮战绩、每场对阵，LPL 战队分组积分；
- **VCT**：赛区排名、战队积分、比赛对阵；
- **KPL**：赛段统计与分组排名、战队战绩、比赛结果；
- **IVL**：战队战绩、比赛对阵。

详情面板保留原页面上下文，支持遮罩、右上角关闭、`Esc` 和键盘操作；移动端自动全宽。

### 中英切换、动态与音乐

- 右上角 **中 / EN** 切换界面语言，选择会写入 `localStorage`，刷新后保持。
- 页面包含滚动进度条、hero 聚光与视差、表格错峰入场、倒计时秒位跳动等动效；系统开启“减少动态效果”时会自动关闭。
- 右下角 **电台** 打开 GRIDLINE RADIO：公开电台（Radio Paradise Main / Mellow / Rock），无需登录即可收听。
- 电台面板底部的 Spotify / Apple Music / QQ音乐 / 网易云 按钮会打开各自官方站点，供用户在自己的账号中登录。

> **关于“登录音乐账号”**：纯静态站点无法直接取得任意音乐平台的登录授权。每个平台都需要自己的 OAuth 应用 / 开发者凭据；本项目没有把任何平台的登录流程伪装成站内授权。**QQ音乐与网易云音乐目前都没有面向第三方网页的公开 OAuth 登录入口**，因此不能在这两个平台之间做“站内登录”。若需要真正的站内播放/登录，必须选定一个提供开放平台能力的服务并提供应用凭据；否则只能使用公开电台或跳转到官方 App。

### 开场动画与影像

- 首次打开站点会播放约 3 秒的 GRIDLINE 开场动画；右下角可跳过，`Esc` 也可关闭。动画只在一个浏览器会话内播放一次（`sessionStorage`），系统开启“减少动态效果”时直接跳过。
- 六个板块末尾都有“现场与影像 / Media & moments”区块：两张大图 + 一个官方视频。图片可打开原图，视频点击后才加载 Bilibili 播放器，避免拖慢首屏。
- 影像缩略图来自 Bilibili 官方赛事账号（F1世界锦标赛、FE电动方程式、哔哩哔哩英雄联盟赛事、无畏契约赛事、哔哩哔哩王者荣耀赛事、第五人格赛事）的公开封面；版权归原权利人，卡片保留来源链接。
- 影像属于**官方内容嵌入**，不表示本站与赛事方有合作关系；若原视频下架，卡片会保留图片、视频区域会提示加载失败。


## 数据刷新

数据快照由 `build_data.py` 生成：

```bash
python build_data.py
```

脚本会重新抓取公开数据源，输出：

- `data.json` — 结构化快照，便于二次开发
- `data.js` — `window.RACEHUB_DATA = {...};`，供 `file://` 直接加载

依赖：Python 3.10+、`lxml`。除 KPL 官方接口为 POST 且按官方要求带 `Origin/Referer` 外，其余数据源均为公开 GET；不需要登录或 API key。

### 数据源

| 数据 | 来源 | 说明 |
| --- | --- | --- |
| F1 | [Jolpica / Ergast API](https://api.jolpi.ca/ergast/f1/current/) | 赛历、车手 / 车队积分、全部已完赛分站结果 |
| Formula E | [FIA Formula E 官方日历](https://www.fiaformulae.com/en/calendar) | 页面内嵌 `application/ld+json` 日历 |
| 英雄联盟 | [ScoreGG](https://www.scoregg.com/) | S16 全球总决赛瑞士轮、LPL 第三赛段积分 |
| VCT | [VLR.GG](https://www.vlr.gg/) | 世界排名、近期赛程与赛果 |
| KPL | [KPL 官方赛事接口](https://kpl.qq.com/) | 2026 年度总决赛赛程与擂台赛积分 |
| IVL | [IVL 官方赛事接口](https://ivl.163.com/) | 2026 秋季赛赛程赛果 |

## 目录结构

```
racehub/
├─ index.html          # 页面骨架、导航、页脚
├─ manifest.webmanifest # PWA 清单（手机添加到主屏幕）
├─ .github/workflows/pages.yml  # GitHub Pages 构建 + 每日数据刷新
├─ assets/
│  ├─ styles.css       # 深色仪表盘主题、响应式布局
│  ├─ app.js           # 渲染、hash 路由、倒计时、赛程筛选
│  ├─ icon.svg         # 矢量图标
│  ├─ icon-*.png       # 180 / 192 / 512 图标
│  ├─ qr.png           # 局域网访问二维码
│  └─ media/           # 六个板块的官方影像缩略图（本地化）
├─ build_data.py       # 抓取 + 归一化，生成 data.json / data.js
├─ requirements.txt    # 构建依赖（lxml）
├─ data.json           # 数据快照
└─ data.js             # 同上，挂到 window.RACEHUB_DATA
```

## 说明与边界

- 本项目是**非官方粉丝项目**，赛程、积分与排名最终以各赛事官方公告为准。
- 页面读取的是**生成时刻的快照**；F1 等数据会随后续比赛变化，重新运行 `build_data.py` 即可更新。
- 部分数据源没有稳定公开 API，脚本按页面结构解析；若源站改版，可能需要同步调整 `build_data.py` 中的选择器。
- LPL 展示的是第三赛段常规赛最终积分；Worlds 展示的是当前瑞士轮阶段数据。
- VCT 排名来自 VLR.GG 的世界排名页，覆盖 13 个赛区，页面主区域展示 5 个主要赛区。
- KPL 淘汰赛阶段部分对阵在快照时仍为“待定”，页面会原样显示。
- 已通过 HTML/CSS 静态校验、`node --check` 语法检查、DOM shim 六视图渲染检查，以及桌面 1440px / 手机 390px 的 CDP 截图与真实点击验收。

## 自定义

- 主题色：`assets/styles.css` 顶部 `body[data-view="f1"]` 等规则里的 `--accent`。
- 新增赛事：在 `index.html` 加导航按钮与 `<section class="view" id="view-xxx">`，在 `app.js` 里加 `renderXXX()` 并在底部调用，再在 `build_data.py` 里补数据。
- 想换视觉风格：主要改 `--bg`、`--panel`、`--line`、`--accent` 与字体变量。
