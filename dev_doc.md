# SpeakScene 产品与开发文档

## 1. 产品定位

SpeakScene 是面向中文母语者的 AI 情景英语陪练。核心不是让用户把指定中文句子翻译成英文，而是在一个真实场景中先获得常用表达，再由系统主动发起对话，帮助用户用语音或键入的方式完成一段可持续的英语互动。

目标用户通常知道一些单词，但不知道真实场景里该怎么自然开口。产品要降低“凭空输出完整句子”的压力，让用户可以参考场景短语，在对话中逐步形成表达习惯。

## 2. 核心体验

页面以一个具体场景为中心，桌面端分为三列：

- 左列：场景信息和 LLM 生成的常用表达，使用中英对照展示。每条表达包含英文、中文、使用说明、语气标签，并可收藏。
- 中列：AI 对话区。系统先发起对话，页面打印英文 starter，并通过浏览器 TTS 朗读。用户可通过语音或键入回复。所有轮次都保存为对话记录。
- 右列：完成对话后的 AI 评分、最近对话、按场景分类的收藏表达。

用户不需要先“会写完整句子”才能练习。左侧表达是脚手架，中间对话是实践场，右侧反馈是复盘。

## 3. MVP 功能范围

- 场景启动：选择等级和类别后，后端生成场景名、中文情境说明、系统开场白和 8-12 条高频表达。
- 对话推进：用户每发送一次回复，后端保存用户轮次并生成下一句系统回复。
- 浏览器语音能力：使用 Web Speech API 做 TTS 和可用浏览器上的 speech recognition；不可用时自动回退到文本输入。
- 语音输入策略：MVP 阶段继续使用浏览器 `SpeechRecognition/webkitSpeechRecognition` 作为低成本语音转文本方案；用户可在提交前查看和编辑识别结果。后续在语音体验需要更稳定、跨浏览器支持更一致时，再接入后端 STT 服务。
- 完成评分：对整段用户对话评分，包括 vocabulary、grammar、authenticity、fluency 和 overall score。
- 收藏系统：用户可收藏真实常用表达，收藏按 scenario category 分组展示。
- 本地开发：默认使用 mock AI client，不需要付费 API key 即可运行完整流程。

## 4. 技术架构

- 前端：React + Vite + Tailwind CSS。主界面是密集型三列工作台，移动端按列堆叠。
- 后端：FastAPI + Pydantic + SQLAlchemy。
- 数据库：SQLite MVP；后续可迁移 PostgreSQL。
- AI 层：当前提供 deterministic mock client；真实 LLM/STT/TTS provider 后续接入 `backend/app/services/ai_client.py`。
- 语音：MVP 使用浏览器 `speechSynthesis` 和 `SpeechRecognition/webkitSpeechRecognition`，不经过后端。
- 后端 STT 规划：后续增加 `POST /api/stt/transcribe`，由前端录制用户音频并提交给后端，后端调用 OpenAI Whisper、ElevenLabs STT、Deepgram 或 AssemblyAI 等 provider，返回 transcript 文本供用户复核、编辑和提交。

## 5. 后端数据模型

MVP 使用以下核心概念：

- ScenarioSession：一次场景练习，包含等级、分类、场景名、中文情境、系统开场白、常用表达、状态、评估结果和完成时间。
- ConversationTurn：一轮对话，包含 speaker、英文文本、可选中文解释、输入方式和时间。
- FavoriteExpression：收藏表达，包含分类、场景名、英文、中文和使用说明。
- User：保留轻量用户字段，认证暂不在本阶段实现。

旧的 PracticeTask / PracticeAttempt / ReviewQueue 模型不再代表当前产品方向。

## 6. API 设计

- `POST /api/scenarios/start`：创建场景会话，返回场景信息、常用表达和系统开场轮次。
- `GET /api/sessions/{session_id}`：获取会话详情和所有轮次。
- `POST /api/sessions/{session_id}/turns`：追加用户回复，返回用户轮次、系统下一轮回复和更新后的会话。
- `POST /api/sessions/{session_id}/complete`：完成对话并返回整段表现评分。
- `GET /api/history`：获取最近场景会话。
- `GET /api/favorites`：按分类获取收藏表达。
- `POST /api/favorites`：收藏表达。
- `DELETE /api/favorites/{favorite_id}`：删除收藏。

## 7. 后续路线

1. 接入真实 LLM：替换 mock scenario generation、conversation continuation 和 evaluation。
2. 语音服务升级：第一阶段保留浏览器 STT；第二阶段接入后端 STT/TTS，并保留浏览器 STT 作为 fallback；第三阶段基于原始音频增加口音、发音、停顿、语速、置信度和 fluency 评估。
3. 增加账号系统：JWT、微信登录、用户学习历史和跨设备收藏。
4. 增加复习系统：把收藏表达和对话弱项组织成场景闪卡。
5. 增加商业化：Pro 场景包、深度评估、无限历史和自定义场景。

## 8. 验收标准

- 首屏就是可练习的三列产品界面，不是营销页。
- 用户进入一个场景后，不需要翻译指定句子，而是参考短语进行真实对话。
- 系统开场白会显示并可朗读。
- 用户至少可以通过文本输入完成对话；支持的浏览器可使用语音识别。
- 后续接入后端 STT 后，即使 provider 不可用，语音输入也应能回退到浏览器识别或文本输入，保证练习流程不中断。
- 完成对话后能看到多维度评分和建议表达。
- 收藏表达能按场景分类展示，并可删除。
