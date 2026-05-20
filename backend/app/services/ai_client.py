from dataclasses import dataclass
import logging
from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import settings
from app.prompts.templates import (
    LEVEL_PROFILES,
    build_conversation_continuation_prompt,
    build_evaluation_prompt,
    build_scenario_package_prompt,
)
from app.schemas.practice import ConversationEvaluation, ScenarioPhrase


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedScenario:
    level: int
    category: str
    scenario_name: str
    scenario_context_cn: str
    starter_en: str
    starter_cn: str
    phrases: list[ScenarioPhrase]


@dataclass(frozen=True)
class GeneratedTurn:
    text_en: str
    text_cn: str


class AIClient:
    async def generate_scenario(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedScenario:
        raise NotImplementedError

    async def continue_conversation(
        self,
        session: GeneratedScenario,
        user_turns_count: int,
        latest_user_text: str,
        conversation_history: list[dict] | None = None,
    ) -> GeneratedTurn:
        raise NotImplementedError

    async def evaluate_conversation(
        self,
        session: GeneratedScenario,
        user_turns: list[str],
    ) -> ConversationEvaluation:
        raise NotImplementedError


class MockAIClient(AIClient):
    async def generate_scenario(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedScenario:
        self._build_scenario_package_prompt(level, category, scenario_name)
        scenario = scenario_name or self._default_scenario(category, level)
        package = self._scenario_package(category, scenario)
        return GeneratedScenario(
            level=level,
            category=category,
            scenario_name=scenario,
            scenario_context_cn=package["context_cn"],
            starter_en=package["starter_en"],
            starter_cn=package["starter_cn"],
            phrases=package["phrases"],
        )

    async def continue_conversation(
        self,
        session: GeneratedScenario,
        user_turns_count: int,
        latest_user_text: str,
        conversation_history: list[dict] | None = None,
    ) -> GeneratedTurn:
        lowered = latest_user_text.lower()
        if user_turns_count >= 4:
            return GeneratedTurn(
                text_en="Great. Let me summarize what we agreed on before we finish.",
                text_cn="很好。结束前我来总结一下我们刚才确认的内容。",
            )
        if "sorry" in lowered or "problem" in lowered:
            return GeneratedTurn(
                text_en="No problem. Could you tell me what would work better for you?",
                text_cn="没关系。你能告诉我什么安排对你更合适吗？",
            )
        if "could" in lowered or "would" in lowered or "please" in lowered:
            return GeneratedTurn(
                text_en="That sounds reasonable. Could you share one more detail?",
                text_cn="听起来很合理。你能再补充一个细节吗？",
            )
        return GeneratedTurn(
            text_en="I see. Could you say that a little more politely and clearly?",
            text_cn="我明白。你能说得更礼貌、更清楚一点吗？",
        )

    async def evaluate_conversation(
        self,
        session: GeneratedScenario,
        user_turns: list[str],
    ) -> ConversationEvaluation:
        joined = " ".join(user_turns).lower()
        turn_count = len([turn for turn in user_turns if turn.strip()])
        polite = any(token in joined for token in ["could", "would", "please", "may", "thanks"])
        phrase_hits = sum(1 for phrase in session.phrases if phrase.en.split()[0].lower() in joined)

        base = 62 + min(turn_count, 4) * 6 + min(phrase_hits, 3) * 4 + (8 if polite else 0)
        overall = min(base, 96)
        return ConversationEvaluation(
            overall_score=overall,
            vocabulary_score=min(overall + (4 if phrase_hits else -4), 100),
            grammar_score=max(overall - 3, 0),
            authenticity_score=min(overall + (3 if phrase_hits else -6), 100),
            fluency_score=min(70 + turn_count * 6, 95),
            feedback_cn=(
                "你能围绕场景持续回应，已经进入真实对话练习的状态。"
                "下一步重点是多借用左侧地道表达，并把需求说得更具体。"
            ),
            strengths=[
                "能根据系统追问继续推进对话。",
                "表达目标基本清楚，没有停留在单词层面。",
            ],
            improvements=[
                "多使用 could/would/please 等礼貌表达。",
                "每次回答尽量补充一个具体信息，例如时间、数量、原因或偏好。",
            ],
            suggested_phrases=session.phrases[:4],
        )

    def _build_scenario_package_prompt(self, level: int, category: str, scenario_name: str | None) -> str:
        return build_scenario_package_prompt(level, category, scenario_name)

    def _default_scenario(self, category: str, level: int) -> str:
        scenes = {
            "business": "rescheduling a client meeting",
            "travel": "checking in at a hotel",
            "school": "asking a teacher about homework",
            "restaurant": "making a restaurant reservation",
        }
        return scenes.get(category, LEVEL_PROFILES[level]["scenes"][0])

    def _scenario_package(self, category: str, scenario: str) -> dict:
        packages = {
            "business": {
                "context_cn": f"你正在处理 {scenario}，需要礼貌地确认安排并推进下一步。",
                "starter_en": "Hi, thanks for joining. I wanted to check if our meeting time still works for you.",
                "starter_cn": "你好，感谢参加。我想确认一下我们的会议时间是否仍然适合你。",
                "phrases": [
                    self._phrase("Would it be possible to reschedule?", "可以改个时间吗？", "委婉提出改期", "polite"),
                    self._phrase("I wanted to check if this still works for you.", "我想确认这对你是否仍然合适。", "确认安排是否可行", "professional"),
                    self._phrase("Could we move it to later this week?", "我们可以挪到本周晚些时候吗？", "提出新的时间范围", "polite"),
                    self._phrase("Thanks for being flexible.", "谢谢你灵活配合。", "表达感谢", "polite"),
                    self._phrase("Let me confirm the details by email.", "我邮件确认一下细节。", "收尾确认", "professional"),
                    self._phrase("That time works for me.", "那个时间我可以。", "接受安排", "neutral"),
                    self._phrase("I have a conflict at that time.", "那个时间我有冲突。", "说明时间冲突", "professional"),
                    self._phrase("Could you send over the agenda?", "你能把议程发过来吗？", "请求会议信息", "polite"),
                ],
            },
            "travel": {
                "context_cn": f"你在 {scenario}，需要和工作人员确认预订、需求和入住信息。",
                "starter_en": "Welcome. May I have your name and reservation details, please?",
                "starter_cn": "欢迎。请告诉我您的姓名和预订信息好吗？",
                "phrases": [
                    self._phrase("I have a reservation under the name Li.", "我用李这个名字订了房。", "说明预订姓名", "neutral"),
                    self._phrase("Could I check in now?", "我现在可以入住吗？", "询问能否入住", "polite"),
                    self._phrase("Is breakfast included?", "包含早餐吗？", "确认服务内容", "neutral"),
                    self._phrase("Could I have a room on a higher floor?", "可以给我高楼层房间吗？", "提出房间偏好", "polite"),
                    self._phrase("What time is check-out?", "几点退房？", "确认退房时间", "neutral"),
                    self._phrase("Could you help me with my luggage?", "你能帮我拿一下行李吗？", "请求帮助", "polite"),
                    self._phrase("There may be a mistake with my booking.", "我的预订可能有点问题。", "礼貌说明问题", "polite"),
                    self._phrase("Thank you for your help.", "谢谢你的帮助。", "表达感谢", "polite"),
                ],
            },
            "school": {
                "context_cn": f"你在 {scenario}，需要向老师或同学清楚询问信息。",
                "starter_en": "Hi, what would you like to ask about the assignment?",
                "starter_cn": "你好，你想问作业的什么问题？",
                "phrases": [
                    self._phrase("When is the assignment due?", "作业什么时候截止？", "询问截止时间", "neutral"),
                    self._phrase("Could you explain this part again?", "您能再解释一下这部分吗？", "请求重复讲解", "polite"),
                    self._phrase("I am not sure how to start.", "我不太确定怎么开始。", "表达困惑", "neutral"),
                    self._phrase("Do we need to work in groups?", "我们需要小组合作吗？", "确认完成方式", "neutral"),
                    self._phrase("Can I hand it in tomorrow?", "我可以明天交吗？", "询问能否延期", "polite"),
                    self._phrase("I understand the main idea now.", "我现在明白大意了。", "确认理解", "neutral"),
                    self._phrase("Could you give me an example?", "您能给我一个例子吗？", "请求示例", "polite"),
                    self._phrase("Thanks, that helps a lot.", "谢谢，这很有帮助。", "表达感谢", "casual"),
                ],
            },
            "restaurant": {
                "context_cn": f"你在 {scenario}，需要自然地预订、点餐或确认需求。",
                "starter_en": "Good evening. How many people will be dining with us tonight?",
                "starter_cn": "晚上好。今晚有几位用餐？",
                "phrases": [
                    self._phrase("I would like to make a reservation.", "我想预订。", "开场说明需求", "polite"),
                    self._phrase("A table for two, please.", "请给我们两人桌。", "说明人数", "polite"),
                    self._phrase("Do you have any vegetarian options?", "你们有素食选择吗？", "询问饮食需求", "neutral"),
                    self._phrase("Could we sit by the window?", "我们可以坐窗边吗？", "提出座位偏好", "polite"),
                    self._phrase("What do you recommend?", "你推荐什么？", "请求推荐", "neutral"),
                    self._phrase("Could we split the bill?", "我们可以分开付账吗？", "询问付款方式", "polite"),
                    self._phrase("The food was excellent.", "食物很好吃。", "表达评价", "polite"),
                    self._phrase("Could I get this to go?", "这个可以打包吗？", "请求打包", "polite"),
                ],
            },
        }
        return packages.get(category, packages["business"])

    def _phrase(self, en: str, cn: str, note: str, tone: str) -> ScenarioPhrase:
        return ScenarioPhrase(en=en, cn=cn, usage_note_cn=note, tone=tone, favorite_candidate=True)


class LLMPhraseOutput(BaseModel):
    en: str
    cn: str
    usage_note_cn: str
    tone: Literal["polite", "neutral", "casual", "professional"]
    favorite_candidate: bool


class ScenarioPackageOutput(BaseModel):
    scenario_name: str
    scenario_context_cn: str
    starter_en: str
    starter_cn: str
    phrases: list[LLMPhraseOutput] = Field(..., min_length=8, max_length=12)


class ConversationContinuationOutput(BaseModel):
    text_en: str
    text_cn: str


class EvaluationOutput(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    vocabulary_score: int = Field(..., ge=0, le=100)
    grammar_score: int = Field(..., ge=0, le=100)
    authenticity_score: int = Field(..., ge=0, le=100)
    fluency_score: int = Field(..., ge=0, le=100)
    feedback_cn: str
    strengths: list[str]
    improvements: list[str]
    suggested_phrases: list[LLMPhraseOutput] = Field(..., min_length=3, max_length=5)


class OpenAIClient(AIClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate_scenario(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedScenario:
        prompt = build_scenario_package_prompt(level, category, scenario_name)
        parsed = await self._parse(prompt, ScenarioPackageOutput)
        return GeneratedScenario(
            level=level,
            category=category,
            scenario_name=parsed.scenario_name,
            scenario_context_cn=parsed.scenario_context_cn,
            starter_en=parsed.starter_en,
            starter_cn=parsed.starter_cn,
            phrases=[self._phrase_from_output(phrase) for phrase in parsed.phrases],
        )

    async def continue_conversation(
        self,
        session: GeneratedScenario,
        user_turns_count: int,
        latest_user_text: str,
        conversation_history: list[dict] | None = None,
    ) -> GeneratedTurn:
        prompt = build_conversation_continuation_prompt(
            level=session.level,
            category=session.category,
            scenario_name=session.scenario_name,
            scenario_context_cn=session.scenario_context_cn,
            phrases=[phrase.model_dump() for phrase in session.phrases],
            user_turns_count=user_turns_count,
            latest_user_text=latest_user_text,
            conversation_history=conversation_history or [],
        )
        parsed = await self._parse(prompt, ConversationContinuationOutput)
        return GeneratedTurn(text_en=parsed.text_en, text_cn=parsed.text_cn)

    async def evaluate_conversation(
        self,
        session: GeneratedScenario,
        user_turns: list[str],
    ) -> ConversationEvaluation:
        prompt = build_evaluation_prompt(
            level=session.level,
            category=session.category,
            scenario_name=session.scenario_name,
            scenario_context_cn=session.scenario_context_cn,
            phrases=[phrase.model_dump() for phrase in session.phrases],
            user_turns=user_turns,
        )
        parsed = await self._parse(prompt, EvaluationOutput)
        return ConversationEvaluation(
            overall_score=parsed.overall_score,
            vocabulary_score=parsed.vocabulary_score,
            grammar_score=parsed.grammar_score,
            authenticity_score=parsed.authenticity_score,
            fluency_score=parsed.fluency_score,
            feedback_cn=parsed.feedback_cn,
            strengths=parsed.strengths,
            improvements=parsed.improvements,
            suggested_phrases=[self._phrase_from_output(phrase) for phrase in parsed.suggested_phrases],
        )

    def _phrase_from_output(self, phrase: LLMPhraseOutput) -> ScenarioPhrase:
        return ScenarioPhrase(
            en=phrase.en,
            cn=phrase.cn,
            usage_note_cn=phrase.usage_note_cn,
            tone=phrase.tone,
            favorite_candidate=phrase.favorite_candidate,
        )

    async def _parse(self, prompt: str, output_model: type[BaseModel]):
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": (
                        "You are SpeakScene's AI service. Return only data matching the requested "
                        "structured output schema. English should be natural and useful for spoken practice; "
                        "Chinese fields should be clear Simplified Chinese."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text_format=output_model,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("OpenAI response did not include parsed structured output")
        return parsed


class FallbackAIClient(AIClient):
    def __init__(self, primary: AIClient, fallback: AIClient) -> None:
        self.primary = primary
        self.fallback = fallback

    async def generate_scenario(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedScenario:
        try:
            return await self.primary.generate_scenario(level, category, scenario_name)
        except Exception:
            logger.exception("Primary AI provider failed during scenario generation; falling back to mock")
            return await self.fallback.generate_scenario(level, category, scenario_name)

    async def continue_conversation(
        self,
        session: GeneratedScenario,
        user_turns_count: int,
        latest_user_text: str,
        conversation_history: list[dict] | None = None,
    ) -> GeneratedTurn:
        try:
            return await self.primary.continue_conversation(
                session,
                user_turns_count,
                latest_user_text,
                conversation_history,
            )
        except Exception:
            logger.exception("Primary AI provider failed during conversation continuation; falling back to mock")
            return await self.fallback.continue_conversation(
                session,
                user_turns_count,
                latest_user_text,
                conversation_history,
            )

    async def evaluate_conversation(
        self,
        session: GeneratedScenario,
        user_turns: list[str],
    ) -> ConversationEvaluation:
        try:
            return await self.primary.evaluate_conversation(session, user_turns)
        except Exception:
            logger.exception("Primary AI provider failed during evaluation; falling back to mock")
            return await self.fallback.evaluate_conversation(session, user_turns)


def get_ai_client() -> AIClient:
    mock_client = MockAIClient()
    if settings.ai_provider.lower() != "openai":
        return mock_client
    if not settings.openai_api_key:
        return mock_client
    return FallbackAIClient(
        OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model),
        mock_client,
    )
