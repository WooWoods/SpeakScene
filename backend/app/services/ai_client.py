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


class MinimalFallbackAIClient(AIClient):
    """Minimal fallback for when the primary LLM provider fails."""

    async def generate_scenario(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedScenario:
        scenario = scenario_name or f"{category} conversation practice"
        return GeneratedScenario(
            level=level,
            category=category,
            scenario_name=scenario,
            scenario_context_cn=f"Practice {category} conversation at level {level}.",
            starter_en="Hello. Let's practice this conversation together. Please start when you're ready.",
            starter_cn="你好。让我们一起练习这个对话。准备好了就开始吧。",
            phrases=[
                ScenarioPhrase(en="Could you please repeat that?", cn="请你再说一遍好吗？", usage_note_cn="请求重复", tone="polite", favorite_candidate=True),
                ScenarioPhrase(en="I understand.", cn="我明白了。", usage_note_cn="确认理解", tone="neutral", favorite_candidate=True),
                ScenarioPhrase(en="Could you speak more slowly?", cn="你能说得慢一点吗？", usage_note_cn="请求放慢语速", tone="polite", favorite_candidate=True),
                ScenarioPhrase(en="Thank you for your patience.", cn="谢谢你的耐心。", usage_note_cn="表达感谢", tone="polite", favorite_candidate=True),
            ],
        )

    async def continue_conversation(
        self,
        session: GeneratedScenario,
        user_turns_count: int,
        latest_user_text: str,
        conversation_history: list[dict] | None = None,
    ) -> GeneratedTurn:
        return GeneratedTurn(
            text_en="I see. Could you tell me more about that?",
            text_cn="我明白了。你能告诉我更多吗？",
        )

    async def evaluate_conversation(
        self,
        session: GeneratedScenario,
        user_turns: list[str],
    ) -> ConversationEvaluation:
        turn_count = len([t for t in user_turns if t.strip()])
        overall = min(60 + turn_count * 5, 85)
        return ConversationEvaluation(
            overall_score=overall,
            vocabulary_score=min(overall + 5, 90),
            grammar_score=max(overall - 5, 40),
            authenticity_score=min(overall + 3, 88),
            fluency_score=min(55 + turn_count * 8, 90),
            feedback_cn="请继续练习，注意使用更多的礼貌表达。",
            strengths=["能够完成对话练习。"],
            improvements=["多使用礼貌用语如 could, would, please。", "尝试使用更多场景相关的短语。"],
            suggested_phrases=session.phrases[:3],
        )


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
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

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

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are SpeakScene's AI service. Return only data matching the requested "
                        "structured output schema. English should be natural and useful for spoken practice; "
                        "Chinese fields should be clear Simplified Chinese. Output valid JSON only, "
                        "no markdown, no explanation, no thinking tags. "
                        "IMPORTANT: For phrase objects, use keys: en, cn, usage_note_cn, tone, favorite_candidate"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI response did not include content")
        import json
        # Try multiple extraction strategies to find valid JSON
        json_str = None

        # Strategy 1: Find the last { and last } after it (handles thinking tags at start)
        think_end = content.rfind('<think>')
        if think_end != -1:
            json_start = content.find('{', think_end)
            if json_start != -1:
                # Find matching closing brace - search for } that closes the first {
                depth = 0
                json_end = -1
                for i in range(json_start, len(content)):
                    if content[i] == '{':
                        depth += 1
                    elif content[i] == '}':
                        depth -= 1
                        if depth == 0:
                            json_end = i
                            break
                if json_end != -1:
                    json_str = content[json_start:json_end + 1]

        # Strategy 2: If that failed, find the first { and try to parse from there
        if json_str is None:
            json_start = content.find('{')
            if json_start != -1:
                # Try to find a valid JSON by finding the first } that gives balanced braces
                depth = 0
                json_end = -1
                for i in range(json_start, len(content)):
                    if content[i] == '{':
                        depth += 1
                    elif content[i] == '}':
                        depth -= 1
                        if depth == 0:
                            json_end = i
                            break
                if json_end != -1:
                    json_str = content[json_start:json_end + 1]

        # Strategy 3: Try to extract from markdown code blocks
        if json_str is None:
            import re
            # Look for JSON in code blocks
            code_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if code_blocks:
                # Find the largest/last code block content
                for block in code_blocks:
                    try:
                        json_str = block
                        json.loads(json_str)  # Test if valid
                        break
                    except:
                        continue

        if json_str is None:
            raise ValueError(f"No valid JSON found in response: {content[:200]}")

        # Normalize field names to handle schema differences
        data = json.loads(json_str)

        # Handle suggested_phrases schema mismatch
        if "suggested_phrases" in data and isinstance(data["suggested_phrases"], list):
            normalized_phrases = []
            for phrase in data["suggested_phrases"]:
                if "en" not in phrase and "phrase_en" in phrase:
                    phrase["en"] = phrase.pop("phrase_en")
                if "cn" not in phrase and "phrase_cn" in phrase:
                    phrase["cn"] = phrase.pop("phrase_cn")
                if "usage_note_cn" not in phrase and "note" in phrase:
                    phrase["usage_note_cn"] = phrase.pop("note")
                normalized_phrases.append(phrase)
            data["suggested_phrases"] = normalized_phrases

        try:
            return output_model.model_validate(data)
        except Exception as e:
            logger.warning(f"Validation failed, attempting to normalize data: {e}")
            # Try to normalize common field mismatches for phrases
            for key in ["phrases", "suggested_phrases"]:
                if key in data and isinstance(data[key], list):
                    for phrase in data[key]:
                        if "phrase_en" in phrase and "en" not in phrase:
                            phrase["en"] = phrase.pop("phrase_en")
                        if "phrase_cn" in phrase and "cn" not in phrase:
                            phrase["cn"] = phrase.pop("phrase_cn")
                        if "usage_note" in phrase and "usage_note_cn" not in phrase:
                            phrase["usage_note_cn"] = phrase.pop("usage_note")
                        if "note" in phrase and "usage_note_cn" not in phrase:
                            phrase["usage_note_cn"] = phrase.pop("note")
            return output_model.model_validate(data)


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
    fallback_client = MinimalFallbackAIClient()
    if settings.ai_provider.lower() != "openai":
        return fallback_client
    if not settings.openai_api_key:
        logger.warning("OpenAI provider selected but OPENAI_API_KEY is not set; using minimal fallback")
        return fallback_client
    return FallbackAIClient(
        OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model, base_url=settings.openai_base_url),
        fallback_client,
    )
