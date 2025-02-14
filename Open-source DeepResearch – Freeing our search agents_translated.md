# 开源 DeepResearch - 解放我们的搜索代理

发布于 2025 年 2 月 4 日

[m-ricAymeric Roucher](https://huggingface.co/m-ric), [albertvillanovaAlbert Villanova del Moral](https://huggingface.co/albertvillanova), [merveMerve Noyan](https://huggingface.co/merve), [thomwolfThomas Wolf](https://huggingface.co/thomwolf), [clefourrierClémentine Fourrier](https://huggingface.co/clefourrier)


## TLDR

昨天，OpenAI发布了[Deep Research](https://openai.com/index/introducing-deep-research/)，这是一个可以浏览网页内容并基于总结回答问题的系统。当我们首次尝试时，这个系统的表现令人印象深刻，让我们惊叹不已。

博客文章中的一个主要成果是在[通用AI助手基准测试（GAIA）](https://huggingface.co/gaia-benchmark)上取得了显著的性能提升。这个基准测试我们最近也在研究。他们在单样本测试中平均达到了接近67%的正确答案率，在特别具有挑战性的"第3级"问题上（涉及多步推理和工具使用）达到了47.6%的正确率（关于GAIA的介绍见下文）。

DeepResearch由一个LLM（可以从OpenAI提供的当前LLM列表中选择，如4o、o1、o3等）和一个内部"代理框架"组成，该框架指导LLM使用网络搜索等工具并组织其行动步骤。

虽然现在已经有功能强大的开源LLM可以免费使用（例如[最近发布的DeepSeek R1模型](https://huggingface.co/deepseek-ai/DeepSeek-R1)），但OpenAI并未透露太多关于Deep Research底层代理框架的信息...

所以我们决定开启一个24小时的任务，重现他们的结果，并在此过程中开源所需的框架！

时间就是金钱，让我们开始吧！⏱️


## Agent框架是什么？为什么它们很重要？

> Agent框架是在LLM之上的一个层，使LLM能够执行操作（如浏览网页或阅读PDF文档），并将其操作组织成一系列步骤。如需快速了解agents，请查看[Andrew Ng的这个精彩访谈](https://youtu.be/sal78ACtGTc?feature=shared&t=52)和我们关于smolagents库的[介绍博文](https://huggingface.co/blog/smolagents)。如需深入了解agents，您可以订阅我们即将开始的agents课程：[点击这里](https://huggingface.us17.list-manage.com/subscribe?u=7f57e683fa28b51bfc493d048&id=9ed45a3ef6)。

几乎每个人都已经通过使用聊天机器人体验到了LLM的强大功能。然而，还不是每个人都意识到，将这些LLM整合到agent系统中可以赋予它们真正的超能力！

这里有一个最近的例子，比较了几个前沿LLM在有无agent框架（在这种情况下是简单的[smolagents](https://github.com/huggingface/smolagents)库）下的表现 - 使用agent框架可以将性能提升多达60分！

[![基准测试](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/benchmarks.png)](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/benchmarks.png)

事实上，OpenAI在其[发布博文](https://openai.com/index/introducing-deep-research/)中也强调，Deep Research在知识密集型的"[人类最后的考试](https://huggingface.co/datasets/cais/hle)"基准测试中，表现远超独立的LLM。

那么，当我们将当前最顶级的LLM整合到agent框架中，朝着`open-DeepResearch`的方向发展时，会发生什么呢？

**简要说明：**我们将在相同的GAIA挑战上对结果进行基准测试，但请记住这是一个进行中的工作。DeepResearch是一个重大成就，其开源复现需要时间。特别是，要达到完全对等，需要改进浏览器的使用和交互，就像OpenAI Operator提供的那样，即超出我们在这第一步探索的当前纯文本网页交互。

让我们首先了解GAIA挑战的范围。

## GAIA 基准测试

[GAIA](https://huggingface.co/datasets/gaia-benchmark/GAIA) 可以说是目前最全面的智能体基准测试。它的问题非常困难，涉及了基于 LLM 系统的诸多挑战。以下是一个难度较大的问题示例：

> 在 2008 年的画作《来自乌兹别克斯坦的刺绣》中展示的水果中，哪些曾在后来被用作电影《最后航程》道具的那艘远洋客轮的 1949 年 10 月份早餐菜单上？请以逗号分隔列表的形式列出这些水果，按照它们在画中从 12 点位置开始顺时针排列的顺序，并使用每种水果的复数形式。

你可以看到这个问题涉及了几个挑战：

- 按照特定格式回答，
- 运用多模态能力（从图像中识别水果），
- 收集多个信息点，有些信息之间存在依赖关系：
  - 识别画中的水果
  - 找出哪艘远洋客轮被用作《最后航程》的浮动道具
  - 找出该远洋客轮 1949 年 10 月的早餐菜单
- 按正确顺序串联起问题解决的轨迹。

解决这个问题既需要高层次的规划能力，也需要严谨的执行力，而这恰恰是单独使用 LLM 时的两个薄弱环节。

所以这是测试智能体系统的绝佳题库！

在 GAIA 的[公开排行榜](https://huggingface.co/spaces/gaia-benchmark/leaderboard)上，GPT-4 在没有任何智能体设置的情况下，在验证集上的得分甚至不到 7%。而在另一端，OpenAI 使用 Deep Research 在验证集上达到了 67.36% 的得分，提升了整整一个数量级！（不过我们不知道它们在私有测试集上的实际表现如何。）

让我们看看能否用开源工具做得更好！

## 构建开放的深度研究

### 使用代码智能体

我们要处理的第一个对传统AI智能体系统的改进是使用所谓的"代码智能体"。正如[Wang等人(2024)](https://huggingface.co/papers/2402.01030)所展示的，让智能体用代码表达其行为有几个优势，但最显著的是**代码专门设计用来表达复杂的动作序列**。

考虑Wang等人给出的这个例子：

[![代码智能体](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/code_agent.png)](https://huggingface.co/datasets/huggingface/documentation-images/resolve/6c7ed2035810565043c92b472d5564c3f1fa4d7e/blog/open-deep-research/code_agent.png)

这突出了使用代码的几个优势：

- 代码动作比JSON更简洁。

  - 需要运行4个并行流，每个包含5个连续动作？用JSON的话，你需要在每个单独的步骤中生成20个JSON块；而用代码只需要1个步骤。
  - 平均而言，论文显示代码动作比JSON需要少30%的步骤，这相当于生成的令牌数量也减少了同样比例。由于LLM调用通常是智能体系统的主要成本，这意味着你的智能体系统运行成本降低了约30%。

- 代码能够重用常用库中的工具

- 在基准测试中表现更好，原因有二：

  - 表达动作的方式更直观
  - LLM在训练中大量接触代码

以上优势在我们对[agent_reasoning_benchmark](https://github.com/aymeric-roucher/agent_reasoning_benchmark)的实验中得到了证实。

从构建`smolagents`的经验中，我们还可以提到一个显著的额外优势，就是对状态的更好处理：这对多模态任务特别有用。需要存储图像/音频/其他内容以供后续使用？没问题，只需将其作为变量分配到你的状态中，需要时可以在4步之后重用。而在JSON中，你必须让LLM在字典键中为其命名，并相信LLM之后能理解它仍然可以使用它。


### 制作合适的工具 🛠️

现在我们需要为代理提供一套合适的工具。

**1.** 网页浏览器。虽然像 [Operator](https://openai.com/index/introducing-operator/) 这样功能完备的网页浏览器交互最终是必需的，但目前我们的首个概念验证仅从一个极其简单的基于文本的网页浏览器开始。你可以在[这里](https://github.com/huggingface/smolagents/blob/gaia-submission-r1/examples/open_deep_research/scripts/text_web_browser.py)找到相关代码。

**2.** 一个简单的文本检查器，用于**读取各种文本文件格式**，在[这里](https://github.com/huggingface/smolagents/blob/gaia-submission-r1/examples/open_deep_research/scripts/text_inspector_tool.py)可以找到。

这些工具来自微软研究院优秀的 [Magentic-One](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/) 代理，向他们致敬！我们没有对其做太多改动，因为我们的目标是用最低的复杂度获得尽可能高的性能。

以下是我们认为能真正提升这些工具性能的简短改进路线图（欢迎提交 PR 和贡献！）：

- 扩展可读取的文件格式数量。
- 提供更精细的文件处理方式。
- 将文本浏览器替换为基于视觉的浏览器，我们已经在[这里](https://github.com/huggingface/smolagents/blob/gaia-submission-r1/src/smolagents/vision_web_browser.py)开始着手进行。

## 结果 🏅

在我们24小时以上的复现冲刺中，我们已经看到了我们的代理在GAIA上的性能稳步提升！

我们很快就超越了之前开放框架的最高水平，从Magentic-One的约46%提升到了[目前在验证集上达到55.15%的性能](https://huggingface.co/spaces/gaia-benchmark/leaderboard)。

这个性能提升主要归功于让我们的代理用代码来编写动作！事实上，当切换到使用JSON而不是代码编写动作的标准代理时，相同设置的性能在验证集上立即降至33%的平均水平。

[这里是最终的代理系统。](https://github.com/huggingface/smolagents/tree/gaia-submission-r1/examples/open_deep_research)

我们已经设置了[在线演示](https://m-ric-open-deep-research.hf.space/)供您试用！

<iframe src="https://m-ric-open-deep-research.hf.space/" frameborder="0" width="850" height="450" style="box-sizing: border-box; border-width: 0px; border-style: solid; border-color: rgb(229, 231, 235); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(59 130 246 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; --tw-contain-size: ; --tw-contain-layout: ; --tw-contain-paint: ; --tw-contain-style: ; display: block; vertical-align: middle; margin-top: 2.5rem; margin-bottom: 2.5rem; overflow: hidden; border-radius: 0.5rem;"></iframe>

然而，这仅仅是个开始，还有很多需要改进的地方！我们的开放工具可以做得更好，smolagents框架也可以进行调优，我们也很想探索更好的开放模型来支持代理。

我们欢迎社区加入这项事业，这样我们就可以一起利用开放研究的力量来构建一个出色的开源代理框架！这将使任何人都能在家运行类似DeepResearch的代理，使用他们喜欢的模型，采用完全本地化和定制化的方法！


## 社区复现

在我们专注于开发GAIA的同时，社区中也涌现出了其他优秀的Deep Research开源实现，特别是来自：

- [dzhng](https://x.com/dzhng/status/1886603396578484630)，
- [assafelovic](https://github.com/assafelovic/gpt-researcher)，
- [nickscamara](https://github.com/nickscamara/open-deep-research)，
- [jina-ai](https://github.com/jina-ai/node-DeepResearch) 和
- [mshumer](https://x.com/mattshumer_/status/1886558939434664404)。

这些实现分别使用了不同的库来进行数据索引、网页浏览和大语言模型查询。在本项目中，我们希望**复现OpenAI展示的基准测试（pass@1平均分），对使用开源大语言模型（如DeepSeek R1）进行基准测试，使用视觉大语言模型，并对传统工具调用与代码原生代理进行基准测试和结果记录。**

## 最重要的下一步

OpenAI的深度研究可能得益于他们通过[Operator](https://openai.com/index/introducing-operator/)引入的优秀网页浏览器。

所以这就是我们接下来要解决的问题！更广泛地说：我们将构建GUI代理，即"能够查看您的屏幕并可以直接用鼠标和键盘操作的代理"。如果您对这个项目感到兴奋，并希望通过开源帮助所有人获得这些很酷的功能，我们非常欢迎您的贡献！
