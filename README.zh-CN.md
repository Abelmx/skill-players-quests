# Skill-Players-Quests

[English](README.md)

Skill-Players-Quests 是一个用于评测 `(m)LLM` 作为通用智能体使用 [Agent Skills](https://agentskills.io/what-are-skills) 能力的框架。

它面向这样一类 agent：模型本身并不预置大量专用工具，而是需要先从候选 skills 中发现合适能力，再读取对应的 `SKILL.md`、遵循 skill 指令，并最终完成真实任务。当前仓库仍处于持续演进的 MVP 阶段，因此框架本身、任务集和 benchmark 覆盖范围都还会继续更新。

## 这是什么

这个框架评测的是 general agent 把 skill 当作外部能力层来使用的能力，包括：

- 从候选池中选对 skill
- 通过读取 `SKILL.md` 正确激活 skill
- 按照 skill 的说明、脚本和参考资料执行
- 在真实执行环境中完成任务，并接受 oracle 评分

它关注的不是抽象意义上的“会不会调工具”，而是一个通用智能体能否真正使用当前已经被广泛采用的 skill 协议完成任务。

## Features

- 支持多 provider、多 model，并支持并行评测。
- 支持两种 skill 注入方式：
  - 渐进式注入 `catalog`，即先给 skill catalog，模型按需读取完整 skill 内容
  - 全量注入 `full_inject`，即在一开始把相关 skill 内容全部注入 prompt
- 每个 task 都有独立 oracle，分别评测：
  - `skill_selection_score`
  - `instruction_following_score`
  - `task_score`
- 支持本地快速评测，也支持在 GitHub Actions 中以更干净、更隔离的方式运行。
- 输出结构化结果，包括单任务结果、对话 trace、单模型报告和多模型对比报告。

## Quick Start

### 本地使用

先安装完整评测环境。这里安装的不只是框架本身，还包括内置 skills 所需的依赖。

```bash
bash setup.sh
# 或者：bash setup.sh 3.12
```

`setup.sh` 会自动完成：

- 创建 `.venv`
- 安装框架依赖和内置 skill 依赖
- 安装 Playwright Chromium，供截图类 skill 使用
- 检查 `curl`、`dig`、`gh`、`jq`、`tar` 等系统工具

然后配置框架和环境变量。

先查看 `configs/default.yaml`。这个文件定义了：

- 启用哪些 providers
- 每个 provider 下有哪些 models
- 每个 provider 通过 `api_key_env` 从哪个环境变量读取 API key
- 默认运行参数，例如 `activation_mode`、`max_turns`、`bash_timeout`

例如：

```yaml
providers:
  boyue:
    api_key_env: "SPQ_API_KEY"
    base_url: "http://..."
    models:
      - "gpt-5.4"
```

然后从模板创建本地 `.env`，并填写实际需要的 key：

```bash
cp .env.example .env
# 编辑 .env，填写 configs/default.yaml 中引用到的环境变量
source activate.sh
```

实际使用时：

- 如果 `configs/default.yaml` 中写的是 `api_key_env: "SPQ_API_KEY"`，那就在 `.env` 中配置 `SPQ_API_KEY`
- 如果写的是 `api_key_env: "GUIJI_API_KEY"`，那就在 `.env` 中配置 `GUIJI_API_KEY`
- 如果某个 task 依赖额外的 skill 凭证，也需要一并配置，例如 `IMAGE_GEN_API_KEY` 或 `GITHUB_TOKEN`

环境变量优先级高于 `configs/default.yaml`，所以你可以把稳定默认值写在 config 中，再按机器或按运行环境用环境变量覆盖。

常用查看命令：

```bash
python3 -m spq show-config
python3 -m spq list-skills
python3 -m spq list-tasks
```

运行单个模型的完整评测：

```bash
python3 -m spq run -p boyue --model gpt-5.4 -m catalog
```

只运行部分任务：

```bash
python3 -m spq run -p boyue --model gpt-5.4 -m catalog \
  -t tokyo-weather \
  -t usd-jpy-rate
```

使用全量注入模式：

```bash
python3 -m spq run -p boyue --model gpt-5.4 -m full_inject
```

同时评测多个 provider / model，并把输出写入 `results/`：

```bash
python3 -m spq run -p boyue -p guiji -m catalog -j 2
```

### GitHub Actions 沙盒

如果你希望在更安全、更干净的环境里运行评测，可以直接使用 GitHub Actions。当前 workflow 会在容器环境中执行。

运行前需要先：

- 将你的分支推送到 GitHub
- 在仓库 Secrets 中配置 `SPQ_API_KEY`、`GUIJI_API_KEY`、`INTERN_API_KEY`
- 如果某些 skill 依赖额外密钥，也需要一并配置，例如图像生成相关凭证

然后：

1. 打开 GitHub Actions 中的 `SPQ Evaluation` workflow。
2. 按需填写 task IDs、并发度和注入模式。
3. 启动 workflow。
4. 在 workflow 输出或自动创建的 PR 中查看评测结果和 artifacts。

如果你希望尽量避免本地环境污染，或者希望得到更隔离的执行环境，这是推荐方式。

## 推荐使用方式

为了保证评测可复现，推荐使用专门的评测分支，而不是直接在 `main` 上运行。

建议流程：

1. 拉出一个评测分支，并在该分支上固定框架版本、tasks 和配置。
2. 在本地或 GitHub Actions 中运行评测。
3. 将生成的 `results/` 提交回这个评测分支。
4. 将 benchmark 结果与 benchmark 本身的演进分开管理，不影响 `main`。

这样可以把“框架变更”和“评测结果”清晰分离。更完整的 workflow 说明会在后续独立文档中补充。

## 当前 MVP 覆盖范围

当前仓库内置：

- `10` 个 tasks
- `15` 个 skills
- `5` 个任务类别

### Task Categories

| 类别 | 示例任务 |
|------|----------|
| `realtime-data` | `tokyo-weather`, `usd-jpy-rate` |
| `external-api` | `generate-qr-code`, `generate-cyberpunk-image` |
| `service-interaction` | `react-bug-issues`, `npm-express-version` |
| `design-standards` | `accessible-login-form`, `brutalist-product-page` |
| `specialized-tools` | `domain-dns-lookup`, `webpage-screenshot` |

### Included Skills

目前内置的一些代表性 skills 包括：

- `weather`
- `exchange-rate`
- `github`
- `package-registry`
- `dns-lookup`
- `web-screenshot`
- `qr-code`
- `image-gen`
- `frontend-design`
- `code-formatter`
- `calculator`

当前 MVP 主要聚焦在单 skill 任务执行，同时在每个 task 中放入若干干扰 skill 作为候选项。

## 结果产物

每次评测都会在 `results/` 下写出结构化结果：

- `results.jsonl`：每个 task 一条结果记录
- `traces.jsonl`：每个 task 的原始对话和工具调用 trace
- `report.json`：单模型聚合指标
- `report.md`：单模型可读报告
- `eval_*-models.md`：多模型一起评测时生成的横向对比报告

这样既能看最终分数，也能回看 agent 实际是如何激活和使用 skills 的。

## 评分方式

每个 task 都有自己的 oracle 函数。oracle 可以检查最终文本输出、task artifact 目录中的文件，以及完整执行 trace。

核心评分维度包括：

| 指标 | 含义 |
|------|------|
| `task_score` | 任务是否真正完成 |
| `skill_selection_score` | 是否激活了期望的 skill |
| `instruction_following_score` | 是否遵循了该 skill 预期的使用方式 |

## 仓库结构

```text
skill-players-quests/
├── configs/              # 框架配置
├── skills/               # 内置 skills 池
├── tasks/                # 评测任务与 task-specific oracle
├── src/spq/core/         # 配置与数据模型
├── src/spq/skills/       # skill 发现与注册
├── src/spq/providers/    # 模型 provider 适配层
├── src/spq/runtime/      # prompt 构造、对话循环、工具执行
├── src/spq/evaluation/   # oracle helper、指标聚合、报告生成
└── .github/workflows/    # GitHub Actions 沙盒评测工作流
```

## Notes

- 当前仓库仍是 MVP，会持续演进。
- task 定义、skill 池组成、oracle 逻辑和报告格式都可能继续调整。
- 如果你需要稳定可复现的横向对比，请固定使用某个明确的 branch 或 commit。
