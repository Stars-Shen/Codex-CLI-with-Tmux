<div align="center">

# Codex CLI with tmux

**让浅色终端里的 Codex 代码差异重新清晰可读。**

Readable Codex diffs in light terminals, including legacy tmux setups.

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Dependencies: stdlib only](https://img.shields.io/badge/dependencies-stdlib_only-2EA44F)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

[快速安装](#快速安装) · [配色展示](#配色展示) · [搭配-tmux-使用](#搭配-tmux-使用) · [恢复原配置](#恢复原配置) · [常见问题](#常见问题)

</div>

## 解决什么问题

在白底终端中运行 Codex CLI 时，旧版 tmux 可能无法回答终端背景颜色查询。Codex 因此采用深色差异背景：`Edited` 下方出现很深的绿色或红色块，行号、注释的对比度也不合适。

这个工具安装一个兼容主题 **`codex-light`**：沿用 Codex 默认浅色方案所使用的 **Catppuccin Latte** 语法配色，固定采用 Codex 的浅色新增、删除背景。无需升级 tmux。

> 这是社区兼容工具，不是 OpenAI 官方发布的独立主题。适用于浅色终端；实际渲染仍受终端调色板和 Codex 版本影响。

## 配色展示

![深色回退与 codex-light 浅色差异块的配色对比](docs/images/comparison.svg)

*上图依据实际验证的 RGB 配色绘制，属于效果示意，并非终端实拍。*

| 内容 | 配色 |
| --- | --- |
| 语法高亮 | Catppuccin Latte |
| 新增行背景 | 浅绿 `#dafbe1` |
| 删除行背景 | 浅红 `#ffebe9` |

<details>
<summary>查看最初遇到的问题截图</summary>

![浅色终端中错误使用深色差异背景的实际截图](docs/images/before.png)

</details>

## 快速安装

需要 **Python ≥ 3.8**，以及支持 `/theme`、自定义 `.tmTheme` 和差异范围背景的 Codex CLI。本工具已在 **Codex CLI 0.162.1 + tmux 3.0a** 上验证；不宣称所有更旧版本均兼容。

```bash
git clone https://github.com/Stars-Shen/Codex-CLI-with-Tmux.git
cd Codex-CLI-with-Tmux
python3 install.py
```

安装器仅使用 Python 标准库。克隆或下载项目后，**安装过程无需联网、sudo 或 pip 依赖**。

安装完成后：

- **Codex 已在运行**：输入 `/theme`，选择 **`codex-light (custom)`**，立即应用。
- **新启动 Codex**：直接运行 `codex` 或 `codex resume`，自动读取已保存的主题配置。

如果当前 shell 设置了禁色变量，先执行：

```bash
unset NO_COLOR
codex
```

### 安装器会修改什么

默认安装到 `~/.codex`；已配置标准变量 `CODEX_HOME` 时，使用该目录。

```text
~/.codex/
├── config.toml                 # 只设置 [tui] 下的 theme
└── themes/
    ├── codex-light.tmTheme
    └── codex-light.LICENSE
```

配置修改为：

```toml
[tui]
theme = "codex-light"
```

已有 `[tui]` 会被复用，其他配置保留。文件发生变化前自动创建同目录的 `.backup-时间戳` 备份，并打印路径；重复安装且内容不变时不写文件、不新增备份。安装器不修改 tmux、shell 初始化文件、登录文件或正在运行的会话。

### 离线复制到其他服务器

复制整个项目目录或下载 GitHub 的源码压缩包，在目标服务器的项目目录运行同一个命令即可：

```bash
python3 install.py
```

## 搭配 tmux 使用

主题可以单独使用。需要“底部标签栏 + 鼠标点击切换窗口”时，仓库另附可选的 [tmux 配置示例](examples/tmux.conf)，安装器不会自动加载它。

检查已有 `~/.tmux.conf` 后，将示例中需要的设置合并进去。例如鼠标、底部栏和真彩色设置：

```tmux
set -g mouse on
set -g status-position bottom
set -g default-terminal "tmux-256color"
set -as terminal-overrides ",xterm-256color:Tc"
```

`tmux-256color` 需要相应 terminfo，可先执行 `infocmp tmux-256color` 检查。上述 `terminal-overrides` 写法用于兼容本项目实测的 tmux 3.0a；外层终端的 `TERM` 不同或不支持真彩色时，需要相应调整。

已有 tmux 服务时加载配置：

```bash
tmux source-file ~/.tmux.conf
```

新建工作会话与窗口：

```bash
tmux new-session -d -s codex -n shell
tmux new-window -d -t codex -n paper
tmux new-window -d -t codex -n code
tmux new-window -d -t codex -n debug
tmux new-window -d -t codex -n experiment
tmux attach -t codex
```

请在 **tmux 外部**执行上述创建命令，并使用尚未存在的会话名。已有会话直接 `tmux attach -t codex`；已经在 tmux 内则可用 `tmux switch-client -t codex`。

采用完整示例配置后，底部标签类似：

```text
[codex] [1:shell] 2:paper 3:code 4:debug 5:experiment
```

每个窗口中可独立运行 `codex`。`Ctrl+b` 后按 `c` 创建窗口，按 `d` 暂时离开会话；重新连接服务器后用 `tmux attach -t codex` 返回。

## 恢复原配置

只想换主题时，在 Codex 中运行 `/theme` 并选择其他内置主题即可。浅色终端可选 `catppuccin-latte`；深色终端可选 `catppuccin-mocha`。旧 tmux 的背景查询限制仍可能影响内置主题的差异背景。

要完整恢复安装前的配置，将安装器打印的备份路径替换到命令中：

```bash
cp '/实际路径/config.toml.backup-时间戳' ~/.codex/config.toml
```

使用 `CODEX_HOME` 时，目标也替换为该目录中的 `config.toml`。**整份恢复会覆盖备份之后对配置的修改**；仅切换主题时优先使用 `/theme`。同名主题文件被替换前也会备份，可以用相同方式恢复。

## 常见问题

**安装后当前窗口为什么没变？**

正在运行的 Codex 不会因配置文件变化自动切换主题。运行 `/theme` 并选择 `codex-light (custom)`，或者退出后重新启动 Codex；无需结束 tmux 会话。

**直接执行 `codex` 仍然没有颜色？**

先检查启动它的 shell 中是否存在 `NO_COLOR`。`env -u NO_COLOR codex` 只影响那一次启动；在原 shell 执行 `unset NO_COLOR` 后，后续启动才不会继续继承该变量。老的 tmux 窗口也可能各自保留旧环境。

**主题和 tmux 的绿色底栏是一回事吗？**

它们是两层独立界面：主题控制 Codex 的语法与差异块；tmux 状态栏由 `~/.tmux.conf` 控制。此工具不重绘 tmux 标签栏。

**状态行有哪些项目？**

在 Codex 中使用 `/statusline` 选择。安装器不改变已有状态行项目。

**配置使用 `tui = { ... }` 或 `tui.theme = ...`？**

安装器支持标准 `[tui]` 表；遇到内联或点号写法会停止且不改动文件。可手动复制主题后通过官方选择器应用：

```bash
mkdir -p ~/.codex/themes
cp codex-light.tmTheme codex-light.LICENSE ~/.codex/themes/
```

然后在 Codex 中运行 `/theme`。使用 `CODEX_HOME` 时，将复制目标改为对应目录的 `themes/`。

**深色终端适合吗？**

本主题固定使用浅色差异背景，主要面向白底、浅色终端。深色终端优先使用内置深色主题。

## 验证安装器

```bash
python3 -m unittest discover -s tests -v
```

测试使用临时目录，覆盖配置保留、主题替换、重复安装、备份恢复和不支持的配置写法，不修改真实 Codex 配置。

## 来源与许可证

- [Codex 官方主题机制](https://learn.chatgpt.com/docs/cli-customization)
- [Codex v0.162.1 默认浅色主题选择](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/tui/src/render/highlight.rs)：浅色终端使用 Catppuccin Latte。
- [Codex v0.162.1 差异背景配色](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/tui/src/diff_render.rs)：采用其浅绿、浅红背景数值。
- [Catppuccin Latte 原始主题](https://github.com/catppuccin/bat/blob/main/themes/Catppuccin%20Latte.tmTheme)。本项目增加 `markup.inserted` / `diff.inserted` 与 `markup.deleted` / `diff.deleted` 的背景覆盖。

安装器、文档和展示素材采用 [MIT License](LICENSE)。Catppuccin 派生主题保留原作者署名及原始 [MIT 许可证](codex-light.LICENSE)。
