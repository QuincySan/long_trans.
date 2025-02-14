# 开源 DeepResearch –解放我们的搜索代理发布日期：2025年2月4日

[m-ric艾梅里克·鲁歇](https://huggingface.co/m-ric), [albertvillanova阿尔伯特·维拉诺瓦·德尔·莫拉尔](https://huggingface.co/albertvillanova), [merve梅尔韦·诺扬](https://huggingface.co/merve), [thomwolf托马斯·沃尔夫](https://huggingface.co/thomwolf), [clefourrier克莱门汀·富里耶](https://huggingface.co/clefourrier)

## 简要说明
昨日，OpenAI发布了 [深度研究](https://openai.com/index/introducing-deep-research/)系统。该系统可通过浏览网页总结内容，并基于总结回答问题。初次试用时，其表现令人震撼。

博客文章中的核心成果是 [通用人工智能助手基准测试（GAIA）](https://huggingface.co/gaia-benchmark)性能的大幅提升。我们最近也在研究这一基准测试——OpenAI在单次尝试（1-shot）中平均正确率达到近67%，而在涉及多步推理和工具使用的「三级」高难度问题上也达到了47.6%的正确率（GAIA的具体介绍见下文）。

DeepResearch由大型语言模型（LLM，可从 OpenAI当前提供的模型列表中选择，如4o、o1、o3等）和一个内部「智能体框架」组成。该框架会引导 LLM使用网络搜索等工具，并分步骤组织其行动。

尽管开源社区现已可自由使用强大的 LLM（例如 [最新的 DeepSeek R1模型](https://huggingface.co/deepseek-ai/DeepSeek-R1)），但 OpenAI并未透露太多关于 Deep Research底层智能体框架的信息……

因此，我们决定开启一项24小时任务：复现他们的成果，并在此过程中开源所需的框架！

倒计时开始！⏱️

## 什么是智能体框架？为何它们如此重要？

>智能体框架是构建在大语言模型（LLM）之上的功能层，旨在让LLM能够执行实际动作（如浏览网页或阅读PDF文档），并通过多步骤流程组织其任务执行。若想快速了解智能体概念，请观看[Andrew Ng的这个精彩访谈](https://youtu.be/sal78ACtGTc?feature=shared&t=52)，并阅读我们关于[smolagents库的介绍博客](https://huggingface.co/blog/smolagents)。如需深入学习智能体知识，可报名参加我们即将开课的智能体系列课程：[点击此处订阅](https://huggingface.us17.list-manage.com/subscribe?u=7f57e683fa28b51bfc493d048&id=9ed45a3ef6)。

通过聊天机器人，几乎所有人都已亲身体验过大语言模型的强大能力。然而，尚未被广泛认知的是：当我们将这些LLM整合到智能体系统中时，它们将获得真正的"超能力"！

最近有个典型案例：比较前沿的LLM在有无智能体框架（此处使用简单的[smolagents库](https://github.com/huggingface/smolagents)）时的表现差异——使用智能体框架可使性能提升最高达60个百分点！

[![基准测试](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/benchmarks.png)](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/benchmarks.png)

事实上，OpenAI在[发布博文](https://openai.com/index/introducing-deep-research/)中也强调，在知识密集型基准测试"[人类终极考试](https://huggingface.co/datasets/cais/hle)"上，DeepResearch的表现显著优于独立运行的LLM。

那么，当我们将当前顶尖的LLM整合到智能体框架中，朝着打造`开源版DeepResearch`的目标迈进时，会发生什么？

**重要说明：**我们将使用相同的GAIA挑战进行基准测试，但请注意这仍是正在进行的工作。DeepResearch是一项重大成就，其开源复现需要时间。特别是要实现完全对等，需要改进浏览器使用和交互方式（例如超越本文探索的纯文本网页交互），就像OpenAI Operator所提供的那样。

让我们先了解GAIA挑战的规模。

## GAIA基准测试

[GAIA](https://huggingface.co/datasets/gaia-benchmark/GAIA)可以说是目前最全面的智能体基准测试。其问题难度极高，涵盖了基于LLM系统的诸多挑战。以下是一个高难度问题的示例：

>在2008年油画《乌兹别克斯坦刺绣》中展示的水果里，有哪些曾出现在某远洋邮轮1949年10月的早餐菜单中？该邮轮后来被用作电影《最后航程》的浮动道具。请以逗号分隔的形式列出这些水果，按画作中从12点方向顺时针排列的顺序呈现。所有水果名称使用复数形式。

这个问题体现了多方面的挑战：
-按约束格式回答-使用多模态能力（从图像中提取水果信息）
-整合多个相互关联的信息片段：
 -识别画作中的水果 -确认被用作《最后航程》浮动道具的邮轮 -查找该邮轮1949年10月的早餐菜单-以正确顺序串联问题解决路径要解决这个问题，既需要高层级的规划能力，又需要严谨的执行力——这正是单独使用LLM时表现最薄弱的两个环节。

因此这是测试智能体系统的绝佳基准！

根据GAIA的[公开排行榜](https://huggingface.co/spaces/gaia-benchmark/leaderboard)，未经智能体框架辅助的GPT-4在验证集上的正确率甚至不足7%。而另一方面，通过深度研究（Deep Research），OpenAI在验证集上达到了67.36%的分数，提升了近一个数量级！（不过我们尚不清楚他们在未公开测试集上的实际表现）

让我们看看是否能用开源工具做得更好！

##构建开放的深度研究生态系统我们正在创建一个协作框架，通过开源工具和共享知识推进深度学习方法的研究与应用。这个生态系统包含：

![开放研究生态系统示意图](https://example.com/research-ecosystem.png)

### 目标

-  **普及先进工具**：让所有背景的研究人员都能使用先进的深度研究工具- **加速可重复性**：通过标准化工作流程降低研究复现成本- **促进创新**：构建模块化组件以支持新型架构的快速实验- **培育协作文化**：创建跨机构的知识共享机制###核心原则1. **开放获取**
- 所有研究成果默认开放源代码 -公开模型权重和训练数据 -采用CC-BY-SA4.0许可证2. **协作基础设施**
- 基于Git的版本控制工作流程 -容器化实验环境（Docker集成）
- 分布式计算支持（Kubernetes编排）

3. **可扩展架构**
 ![系统架构图](https://example.com/system-architecture-v2.png)
    -模块化插件系统 -支持多框架（PyTorch/TensorFlow/JAX）
    -混合精度训练管道###技术组件|模块 |功能 |参考实现 |
    |------|-----|---------|
    |模型库 |预训练模型存储库 | [Hugging Face Transformers库](https://huggingface.co/docs/transformers) |
    |实验跟踪 |超参数版本控制 | [MLflow集成](https://mlflow.org/) |
    |数据分析 |可视化工具包 | Altair + Streamlit仪表盘 |

###当前进展```markdown- [x]核心API规范v0.1- [ ]分布式训练模块- [ ]跨平台模型转换器```

**正在进行中的项目**:
- OpenRDM（研究数据管理平台）[查看路线图](https://roadmap.deepresearch.org)
-协作标注工具套件（预计2024 Q2发布）

###贡献指南欢迎通过以下方式参与：
1.代码贡献 -提交PR到我们的[GitHub仓库](https://github.com/deep-research)
 -完善测试覆盖率2.非代码贡献 -改进文档 -报告研究用例 -参与[社区讨论](https://forum.deepresearch.org)

>注意：所有贡献者需遵守我们的[行为准则](https://conduct.deepresearch.org)和[贡献协议](https://cla.deepresearch.org)

[![开放研究宣言](https://img.shields.io/badge/Open_Research-Manifesto-blue)](https://manifesto.deepresearch.org)

```
构建开放的研究未来，一次一个项目！
```

###使用代码代理（CodeAgent）

我们对传统AI代理系统的首个改进是采用所谓的"代码代理"。正如[Wang等人（2024）](https://huggingface.co/papers/2402.01030)所示，让代理用代码表达其动作具有多个优势，最显著的是**代码本身就是为表达复杂动作序列而专门设计的**。

参考Wang等人给出的这个示例：

[![代码代理](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/code_agent.png)](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/code_agent.png)

这凸显了使用代码的多个优势：

-代码动作比JSON更加简洁 -需要运行包含5个连续动作的4个并行流？使用JSON需要生成20个独立步骤的JSON块；而代码仅需1步 -论文显示，代码动作平均比JSON少30%的步骤，相当于减少等比例的token生成。由于LLM调用通常是代理系统的主要成本，这意味着代理系统运行成本可降低约30%

-代码可以直接复用常见库中的工具-在基准测试中表现更优，原因有二：
 -更直观地表达动作的方式 - LLM训练过程中大量接触过代码我们在[agent_reasoning_benchmark](https://github.com/aymeric-roucher/agent_reasoning_benchmark)上的实验也验证了上述优势。

通过构建`smolagents`，我们还发现一个显著的额外优势：更好地处理状态。这对多模态任务尤其有用。需要临时存储图片/音频/其他数据供后续使用？只需将其赋值给状态变量，四步之后仍可调用。而使用JSON时，必须让LLM在字典键中命名，并指望LLM之后能正确识别该键值。

###选择合适的工具 🛠️现在我们需要为智能体提供合适的工具集。

**1.**网络浏览器。虽然要达到完整性能需要像[操作员](https://openai.com/index/introducing-operator/)这样成熟的网页浏览器交互，但我们目前为第一个概念验证实现了一个极简的基于文本的网页浏览器。代码可在[此处](https://github.com/huggingface/smolagents/blob/gaia-submission-r1/examples/open_deep_research/scripts/text_web_browser.py)找到。

**2.**简单的文本检查器，用于**读取多种文本文件格式**，代码位于[这里](https://github.com/huggingface/smolagents/blob/gaia-submission-r1/examples/open_deep_research/scripts/text_inspector_tool.py)。

这些工具来自微软研究院优秀的[Magentic-One](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/)智能体系统，向他们致敬！我们未做太多修改，因为我们的目标是尽可能以最低复杂度实现最佳性能。

以下是我们认为能显著提升这些工具性能的改进路线图（欢迎提交PR贡献代码！）：

-扩展可读取的文件格式数量-实现更细粒度的文件处理-用基于视觉的网页浏览器替代当前版本，我们已在此[文件](https://github.com/huggingface/smolagents/blob/gaia-submission-r1/src/smolagents/vision_web_browser.py)中开始相关开发

##结果 🏅在我们持续24小时以上的复现冲刺中，已经观察到智能体在 GAIA基准上的性能稳步提升！

我们快速超越了之前开放框架的 SOTA成绩（Magentic-One约46%），达到了[验证集上当前55.15%的性能表现](https://huggingface.co/spaces/gaia-benchmark/leaderboard)。

性能提升的关键在于让智能体使用代码编写动作！当我们将系统切换为使用 JSON格式编写动作的标准智能体时，相同配置在验证集上的平均表现立即下降至33%。

[点击查看最终智能体系统](https://github.com/huggingface/smolagents/tree/gaia-submission-r1/examples/open_deep_research)

我们搭建了[实时演示界面](https://m-ric-open-deep-research.hf.space/)供您体验！

<iframe src="https://m-ric-open-deep-research.hf.space/" frameborder="0" width="850" height="450" style="box-sizing: border-box; border-width:0px; border-style: solid; border-color: rgb(229,231,235); --tw-border-spacing-x:0; --tw-border-spacing-y:0; --tw-translate-x:0; --tw-translate-y:0; --tw-rotate:0; --tw-skew-x:0; --tw-skew-y:0; --tw-scale-x:1; --tw-scale-y:1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width:0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(59130246 / .5); --tw-ring-offset-shadow:00 #0000; --tw-ring-shadow:00 #0000; --tw-shadow:00 #0000; --tw-shadow-colored:00 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; --tw-contain-size: ; --tw-contain-layout: ; --tw-contain-paint: ; --tw-contain-style: ; display: block; vertical-align: middle; margin-top:2.5rem; margin-bottom:2.5rem; overflow: hidden; border-radius:0.5rem;"></iframe>

但这仅仅是开始，仍有大量改进空间！我们的开放工具可以优化，smolagents框架还能调整，我们期待探索更强大的开放模型来支持智能体。

诚邀社区加入我们的征程，让我们共同利用开放研究的力量，打造卓越的开源智能体框架！这将让每个人都能在家运行类 DeepResearch智能体，使用最喜爱的模型，实现完全本地化和定制化的解决方案！

##社区复现成果在我们专注于GAIA研究的同时，社区中也涌现出多个优秀的深度研究开源实现，特别要感谢以下贡献者：

- [dzhng](https://x.com/dzhng/status/1886603396578484630),
- [assafelovic](https://github.com/assafelovic/gpt-researcher),
- [nickscamara](https://github.com/nickscamara/open-deep-research),
- [jina-ai](https://github.com/jina-ai/node-DeepResearch)以及- [mshumer](https://x.com/mattshumer_/status/1886558939434664404)。

这些实现方案在数据索引、网页浏览和LLM查询等环节分别采用了不同的技术栈。本项目旨在**复现OpenAI提出的基准测试（pass@1平均分），通过改用开源大模型（如DeepSeek R1）、融合视觉模型等方案进行性能对比，并系统记录传统工具调用与代码原生智能体的基准测试结果。**

##最重要的后续步骤OpenAI的深度研究很可能通过他们与 [Operator（操作员）](https://openai.com/index/introducing-operator/)共同推出的优秀网页浏览器得到加速。

因此我们接下来要攻克这个方向！更广义的问题上：我们将构建 GUI代理，即"能够查看你的屏幕并通过鼠标键盘直接操作的代理"。如果你对这个项目感到兴奋，并希望通过开源帮助所有人都能使用如此酷炫的能力，我们非常欢迎你的贡献！

我们正在[招聘全职工程师](https://apply.workable.com/huggingface/j/AF1D4E3FEB/)来协助推进这个项目及其他工作，感兴趣请申请 🙂

-要开始使用开放深度研究，请尝试[此处](https://github.com/huggingface/smolagents/tree/gaia-submission-r1/examples/open_deep_research)的示例-查看 [smolagents代码仓库](https://github.com/huggingface/smolagents)
-阅读更多关于 smolagents的[文档](https://huggingface.co/docs/smolagents/index)和[介绍博客](https://huggingface.co/blog/smolagents)