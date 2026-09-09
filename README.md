# rihuan.me

个人主页的全部源码。手写静态站，不依赖 Jekyll，不依赖任何外部 CDN。

**一份源码，两个部署目标：**

| | 地址 | 怎么上去 |
| --- | --- | --- |
| GitHub Pages | <https://rihuan.me/> | 推到 `main`，自动发布 `docs/` |
| 学校主页服务 | `https://mypage.cuhk.edu.cn/<账号>/` | 手动上传 `docs/` 里的内容 |

两边跑的是同一棵 `docs/`。全站相对路径，所以根目录部署和子目录部署都成立 ——
这也是当初放弃 AcademicPages 的原因，Jekyll 那套在子路径下要改一堆配置。

## 目录

```
build.py  build.sh          从 src/ 拼装 docs/ 的六个页面
check.py  check.sh          上传前自检，六类检查
subset-fonts.py  .sh        重切思源字体子集
preview.ps1                 本地预览

src/partials/               公用部分，改一次六个页面全跟着变
  header.en/zh              顶栏与导航（{{home}} {{other}} {{cur_misc}} {{cur_ms}} 由 build 填）
  profile.en/zh             侧栏（主）
  profile-ms.en/zh          侧栏（麻薯页）
  banner-full               首页大幅 banner
  banner-slim               子页面窄条（同一份图形，viewBox 开窗到下半部）
  toc.en/zh                 右侧锚点导航
  footer.en/zh              页脚
  scripts.html              锚点高亮脚本（只有带目录的页面会引入）

src/pages/                  每页只剩 front matter + 自己的 <main>

docs/                       ← 发布目录
  六个 .html                **生成产物，改了会被覆盖**
  assets/ images/ files/    直接在这里维护，build 不碰
  CNAME  .nojekyll          GitHub Pages 用
```

## 改完跑什么

```bash
./build.sh        # 生成六个页面
./check.sh        # 自检，第一项就是「docs/ 与 src/ 是否同步」
git add -A && git commit -m "..." && git push
```

`./build.sh --diff` 只对比不写盘，可以先看会改动什么。

**改内容去 `src/`，别改 `docs/*.html`** —— 下次 build 会覆盖。真改错了 `check.sh` 会拦下来。
`docs/` 里的图片、PDF、CSS 不是产物，就地改就行。

## 预览

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File preview.ps1
```

打开 <http://localhost:8765/huangrihuan/>。子路径是故意的，用来暴露写死的绝对路径 ——
学校那边是子目录部署，GitHub 这边是根目录，两种都得成立。

## GitHub Pages 设置

Settings → Pages：Source `Deploy from a branch`，分支 `main`，目录 **`/docs`**，
Custom domain `rihuan.me`，Enforce HTTPS 勾上。

选 `/docs` 是为了让根目录的脚本和 `src/` 不被当成网页发布出去 ——
`.nojekyll` 会关掉 Jekyll 构建，那样仓库里每个文件都是可访问的。

## 中英双语

**六个页面，中英各三个。** 用独立文件而不是 JS 切换，理由：不引入 `.js`（学校手册
「网页或潜在脚本文件」那条模糊地带继续绕开）、地址栏能看出当前语种、改中文时完全不会碰到英文页。

```
index.html  ←→  index-zh.html
misc.html   ←→  misc-zh.html
ms.html     ←→  ms-zh.html
```

切换按钮在导航栏最左边（About 左侧），英文页上写「中文」，中文页上写「EN」，
**逐页对应** —— 在 misc 页点切换会去 misc-zh，不会跳回首页。

### 怎么填翻译

中文页里所有待翻译的地方都标成了 `〔待译：…〕`，**搜 `〔待译` 就能找到全部**，
填完搜不到就说明没有遗漏。共 110 处：`index-zh` 45、`misc-zh` 27、`ms-zh` 38。

两种形式：

- **`〔待译：原文〕`** —— 纯文本，整段替换掉即可（导航、标题、按钮、图说等）
- **`〔待译〕 原文…`** —— 段落里含链接或 `<br>`，标记只加在**前面**，原文和标签**原样保留**。
  这样 `<a href>` 不会丢，你改中文时可以按中文语序把链接挪到合适位置，改完删掉 `〔待译〕` 就行。

### 故意不加占位的地方

这些按学术惯例保持英文，中文主页上一般也不翻译：

- 论文标题、期刊名、合作者姓名、卷期页码
- 课程代码（`DMS 2030`、`IBA 6305`）
- `PDF` / `SSRN` / `CERT` 这些标签
- 比赛距离标签（`HALF` / `FULL` / `10 KM`）

想翻的话告诉我，我再加一批占位。

### 改英文页之后

英文页改了内容，中文页**不会自动跟着变** —— 两边是独立文件。加了新段落要手动同步过去。

## 页面

- `index.html` —— 一版到底：About / Research / Teaching 三节，右栏锚点导航随滚动高亮
- `misc.html` —— 跑步，独立一页，保留全部完赛证书链接
- `ms.html` —— 麻薯，35 张照片
- `assets/css/site.css` —— 无框架

三页齐了，可以上传。

## 上传到学校

传 `docs/` **里面的**内容，共 **63 个文件、97 MB**，在学校手册的限制内
（≤1200 个文件、<1024 MB）。

其中 `CNAME` 和 `.nojekyll` 只对 GitHub Pages 有意义，传到学校服务器上是惰性的，
留着不影响，想省事也可以不传。

文件类型只有 `jpg 38 / pdf 8 / html 6 / png 1 / jpeg 1 / css 1 / woff2 3` ——
**一个 `.js` 都没有**，手册第十六节「网页或潜在脚本文件」那条模糊地带完全绕开了。

## 麻薯页的两个处理

**轮播改成并排。** 原页用了三个 Bootstrap carousel，去掉 Bootstrap 后没有照搬成
JS 相册，而是改成并排的图组 —— 这三组本来就是两三张一讲的段子
（「Paper submitted / Paper rejected」「Just lost my paws / Lost again」），
铺垫和包袱同屏才好笑，轮播反而把它们拆散了。窄屏下自动堆叠成一列。

**懒加载 + 预留尺寸。** 35 张图全部带 `loading="lazy"`，首屏只加载 5 张；
每张都写了真实的 `width`/`height`，浏览器据此预留纵横比，
滚动时不会因为图片陆续到位而整页跳动。图片本身**一个字节都没改**。

顺带一提 `images/MS/meme.png` 是 50 MB（7251×4708），占整站体积一半以上，
在页面上最宽只显示到约 960 px。你说过不动图片，所以留着了；
真要提速，压这一张就够。

## 中文字体：自带思源，已子集化

Windows 自带的中文字体里，衬线只有 SimSun（宋体），在标题尺寸下又细又旧；
所以中文字体是**自己带的**，不依赖访客机器上有什么。

| 用途 | 字体 | 源文件 | 子集后 |
| --- | --- | --- | --- |
| 标题 | 思源宋体 SourceHanSerifSC SemiBold | 24 MB | **60 KB** |
| 正文 | 思源黑体 SourceHanSansSC Regular | 16 MB | **48 KB** |
| 中文粗体 | 思源黑体 SourceHanSansSC Bold | 16 MB | **48 KB** |

**授权**：思源是 SIL OFL，允许自由分发和网页嵌入。
⚠️ **不能换成微软雅黑、等线这类 Windows 自带字体** —— 它们随系统授权，禁止上传到服务器再分发。

标题用宋体是因为英文标题是 Cambria 这类衬线体，中文配宋体才对得上；
思源宋体是当代重新设计的，和 SimSun 不是一回事。

粗体单独带一个字重，否则中文小标题和图说（600 字重）会被浏览器做「伪粗体」，糊。

`@font-face` 上写了 `unicode-range`，**英文页不会下载宋体**（实测英文页只拉两个黑体子集共 92 KB，
因为导航里的「麻薯」需要）。`font-display: swap` 保证字体没到之前文字先用系统字体显示，不会白屏。

`src` 里带了 `local()`，访客机器上装了完整思源的话直接用本地的，连下载都省了。

### 改了中文内容之后要重切

子集**只包含页面里出现过的字**。新加的字不在子集里会掉回系统字体，
一句话里出现两种字形，非常显眼。所以中文改完跑一次：

```bash
./subset-fonts.sh
```

（在仓库根目录。依赖 `py -m pip install fonttools brotli`，
只在本机跑，**不上传**。上传的只有 `assets/fonts/*.subset.woff2` 三个文件。）

## 字体：不要把 Georgia 加回衬线栈

`--serif` 里**故意没有 Georgia**。Georgia 的 `U+01D4`（ǔ，拼音第三声）会渲染成
「u + 一个悬空抬高的短音符」，标题里的「麻薯(MáShǔ)」就散架了。

排查时踩的坑：用 canvas `measureText` 宽度比较来判断字体是否含某字形是**不可靠的** ——
Georgia 确实含这个字形，只是画得不对；`document.fonts.check()` 对没装的字体也返回 true，
同样不可信。**唯一可靠的办法是把候选字体并排渲染出来用眼睛看。**

实测正确的：Cambria、Constantia、Palatino Linotype、Times New Roman、Segoe UI。
现在的栈是 `"Iowan Old Style", "Palatino Linotype", Palatino, Cambria, Constantia, "Songti SC", serif`。

## 代码里不写注释

`index.html` / `misc.html` / `ms.html` / `site.css` 里**没有中文注释** —— 访客一按
「查看源代码」就全看得见，所以说明一律放在这份 README 里。CSS 里只留了
`/* Masthead */` 这种英文小节标签，那是常规写法。

以下几条是改代码时容易踩回去的坑，都是没有注释兜着的：

| 位置 | 规则 | 不这么写会怎样 |
| --- | --- | --- |
| `.profile__links li` | 必须 `display:flex` | 侧栏第一项「Shenzhen, China」没有 `<a>` 包裹，`.ico` 会撑成整行的米黄色块 |
| `.pub__meta` | 必须 `display:block` | 后面的获奖徽章会跟在 meta 末尾同行流动，不独占一行 |
| `.races li` | 后两列必须固定宽度 | 每个 `li` 是独立 grid，用 `auto` 的话没证书的那行标签会错位 |
| `.mainnav a` | `white-space:nowrap` | 窄屏下「麻薯」会折成两行 |
| `.banner--slim` | 不需要高度规则 | 子页面用的是同一份 SVG，只把 `viewBox` 开窗到下半部（`0 90 1232 190`），高度由那个比例决定 |
| `ms.html` 的 `<img>` | 都要带真实 `width`/`height` | 配合 `loading="lazy"`，浏览器靠这两个属性预留纵横比；漏了会在滚动时整页乱跳 |

`ms.html` 里的 `.strip` 是原来三个 Bootstrap 轮播的替代 —— 那几组本来就是两三张一讲的段子，
并排比轮播好，而且不需要 JS。

## 设计约定

**容器宽度 1280px 贯穿顶栏、banner、正文、页脚**，四者左右边缘严格对齐
（banner 24→1241，左栏起点 24，右栏终点 1241）。内部三栏 220 / 717 / 200，
正文每行约 72 字符。这是 Valtorta 那个模板没做到的地方 —— 它导航通栏、正文只有 960px。

**配色**（都过 WCAG AA）：

| | 值 | 白底对比度 | 用途 |
| --- | --- | --- | --- |
| 橄榄绿 | `#5a6b3b` | 5.84:1 | 正文链接、标题、主色 |
| 深橄榄 | `#414f28` | — | hover、小标题 |
| 米黄 | `#f0e2b8` | 1.33:1 | **只能做背景**，不能承载文字 |
| 陶土红 | `#c6502c` | 4.55:1 | 编号、职称、强调；勉强过线，不用于长正文 |

## Banner

内联 SVG，深圳天际线，**由西向东**排列真实地标：
宝安「湾区之光」摩天轮 → 南山「春笋」华润总部 → 福田平安金融中心 → 罗湖地王大厦。
颜色走 CSS 变量，换配色时自动跟随。摩天轮是全幅唯一的红。

子页面用同一份图形，只把 `viewBox` 开窗到下半部（`0 90 1232 190`），
不是另画一张，所以永远不会和主图不一致。

画的时候踩过的坑，改之前先看一眼：

- **春笋是子弹形，不是三角形**。腰部（y≈208）最宽，往上宽度先保持很长一段再收成针尖，
  中段是**外凸**的。控制点必须压在腰部正上方（`C532 150 541 95 560 60`）；
  放在腰部到尖顶的连线附近，中段只会鼓出不到 2px，画出来就是三角形。
- **平安的顶是八道棱线自身收束成的冠部**，不是"塔身 + 一根天线"。塔身从底到顶连续收分。
- 高度不按真实比例，只保证平安最高。摩天轮按比例只有 59px 会看不清，放大到了 104px。

## 相对旧版退掉的东西

Bootstrap、jQuery、Popper、Font Awesome 全套字体，合计约 3.5 MB → 现在 `index.html` 24 KB
+ `site.css` 16 KB，**零外部请求、零独立 `.js` 文件**（锚点高亮那十几行内联在 HTML 里）。
学校手册里「网页或潜在脚本文件」那条模糊地带也就不用管了。

图标全部是内联 SVG，不再需要字体文件。
