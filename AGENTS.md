# Instructions for Agents

## 进展记录

- 已检查仓库并梳理核心模块（`chunker.py`、`translator.py`、`summarizer.py`、`reviewer.py`、`advanced_reviewer.py`、`llm_client.py` 等）。
- 已在 `tests/` 目录编写了覆盖主要模块的单元测试，包括 `chunker`、`summarizer`、`translator`、`reviewer`、`advanced_reviewer`、`llm_client`、`markdown_parser` 以及 `main` CLI；测试使用 mock 避免真实的 LLM 调用。
- 运行 `pytest` 后所有测试通过（需先安装 `openai`、`markdown-it-py`、`python-dotenv` 等依赖）。
- 给出了后续重构方向：整理包结构、引入依赖注入、支持异步并发、改进日志与数据结构、统一异常处理以及优化分段策略等。
- 提出了单元测试计划，可持续完善测试覆盖率。

