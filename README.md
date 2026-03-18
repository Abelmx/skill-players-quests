# Skill-Players-Quests

LLM Agent Skills 使用能力评测框架。

评测 LLM 在使用 [Agent Skills (SKILL.md 标准)](https://agentskills.io/specification) 时的能力，包括技能发现、指令遵循、工具编排和端到端任务完成。

## 特性

- **两种激活模式**：Catalog + 按需激活（Mode A）和全量注入（Mode B）
- **多 Provider 支持**：OpenAI / Anthropic / vLLM (OpenAI 兼容)
- **确定性评分**：Oracle 函数客观打分，无人工判断
- **横向对比**：多模型、多维度对比报告
- **真实执行**：所有脚本在真实环境中执行，不使用 mock

## 快速开始

### 1. 初始化环境

一键创建虚拟环境并安装全部依赖（框架 + skills 脚本）：

```bash
bash setup.sh           # 使用系统默认 python3
bash setup.sh 3.12      # 指定 Python 版本（需 uv）
```

`setup.sh` 做了以下事情：
1. 创建 `.venv` 虚拟环境
2. 安装框架核心依赖 + skills 脚本依赖（`pip install -e ".[skills]"`）
3. 安装 Playwright Chromium 浏览器（`web-screenshot` skill 需要）
4. 检查系统工具（curl, dig, gh, jq, tar）

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 API key 等配置
```

### 3. 激活环境

```bash
source activate.sh      # 或使用 alias: spqenv
```

激活脚本会自动加载 `.env` 并检查依赖完整性。

### 4. 运行评测

```bash
# 使用 OpenAI 在 catalog 模式下运行所有任务
python3 -m spq run -p openai -m catalog

# 运行特定任务
python3 -m spq run -p openai -m catalog -t tokyo-weather -t usd-jpy-rate

# 指定输出路径
python3 -m spq run -p openai -o results/my-report.json

# 使用 Anthropic 全量注入模式
python3 -m spq run -p anthropic -m full_inject

# 查看可用 skills 和 tasks
python3 -m spq list-skills
python3 -m spq list-tasks

# 查看历史报告
python3 -m spq report results/report.json
```

## 依赖说明

项目依赖分为三层，在 `pyproject.toml` 中明确标注：

### 框架核心 (`dependencies`)

评测框架本身运行所需，安装 `pip install -e .` 即可：

| 包 | 用途 |
|-----|------|
| openai | OpenAI / vLLM 兼容 API 调用 |
| anthropic | Anthropic Claude API 调用 |
| pydantic | 数据模型验证 |
| pyyaml | YAML 配置解析 |
| click | CLI 框架 |
| python-frontmatter | SKILL.md frontmatter 解析 |
| rich, tabulate | 终端报告格式化 |

### Skills 脚本依赖 (`[skills]`)

各 skill 内嵌脚本运行所需，安装 `pip install -e ".[skills]"` 追加：

| 包 | 对应 Skill | 用途 |
|-----|-----------|------|
| httpx | image-gen | HTTP 请求图像生成 API |
| Pillow | image-gen, qr-code | 图像处理和验证 |
| qrcode | qr-code | QR 码生成 |
| reportlab | pdf-report | PDF 文档生成 |
| playwright | web-screenshot | 浏览器截图（还需 `playwright install chromium`） |

### 系统工具

部分 skill 的 shell 脚本依赖系统工具：

| 工具 | 对应 Skill | 安装方式（Ubuntu/Debian） |
|------|-----------|--------------------------|
| curl | weather, exchange-rate | `apt install curl` |
| dig | dns-lookup | `apt install dnsutils` |
| gh | github | [GitHub CLI](https://cli.github.com/) |
| jq | github | `apt install jq` |
| tar | file-compressor | 通常预装 |

## 评分维度

| 维度 | 说明 |
|------|------|
| task_score | 任务完成正确性（oracle 函数判定） |
| skill_selection_score | 是否选择了正确的 skill（仅 Mode A） |
| instruction_following_score | 是否按 SKILL.md 指令执行 |

## 项目结构

```
skill-players-quests/
├── setup.sh                  # 一键环境初始化
├── activate.sh               # 环境激活 + 依赖检查
├── pyproject.toml             # 依赖管理（框架 / skills / dev 分层）
├── src/spq/                   # 框架核心代码
│   ├── core/                  # 数据模型和配置
│   ├── skills/                # SKILL.md 解析器和注册表
│   ├── providers/             # LLM Provider 抽象层
│   ├── runtime/               # 执行引擎
│   ├── evaluation/            # Oracle 框架和评分
│   └── cli.py                 # CLI 入口
├── skills/                    # 内置 Skills Pool (~15 个)
├── tasks/                     # 评测任务 (10 个)
├── configs/                   # 配置文件
└── .github/workflows/         # CI 模板
```

## 扩展

### 新增 Skill

在 `skills/` 下创建目录，包含 `SKILL.md` 和 `scripts/`，会被自动发现。
如果脚本有额外 Python 依赖，请添加到 `pyproject.toml` 的 `[project.optional-dependencies] skills` 中。

### 新增 Task

在 `tasks/{category}/` 下创建 `task.yaml` + `task_oracle.py`，从 Skills Pool 中选取 `available_skills`。

## GitHub Actions

项目包含 `.github/workflows/evaluate.yaml`，支持在容器中运行评测。通过 Repository Secrets 注入 API Key。
