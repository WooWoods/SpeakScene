import random
from dataclasses import dataclass

from app.prompts.templates import LEVEL_PROFILES, build_scenario_generation_prompt
from app.schemas.practice import Alternatives, Feedback, Keyword


@dataclass(frozen=True)
class GeneratedTask:
    level: int
    category: str
    task_name: str
    cn_sentence: str
    context_cn: str
    keywords: list[Keyword]


class AIClient:
    async def generate_task(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedTask:
        raise NotImplementedError

    async def evaluate_answer(self, task: GeneratedTask, user_input: str) -> Feedback:
        raise NotImplementedError

    async def generate_hints(self, task: GeneratedTask) -> tuple[Alternatives, str]:
        raise NotImplementedError


class MockAIClient(AIClient):
    async def generate_task(
        self,
        level: int,
        category: str,
        scenario_name: str | None = None,
    ) -> GeneratedTask:
        profile = LEVEL_PROFILES[level]
        scenario = self._resolve_scenario(profile, category, scenario_name)
        expression = self._expression_for(level, scenario)

        return GeneratedTask(
            level=level,
            category=category,
            task_name=f"{scenario} 情景表达",
            cn_sentence=expression["cn_sentence"],
            context_cn=f"{profile['name']}情景：{expression['context_cn']}",
            keywords=expression["keywords"],
        )

    async def evaluate_answer(self, task: GeneratedTask, user_input: str) -> Feedback:
        lowered = user_input.lower()
        has_polite_marker = any(token in lowered for token in ["could", "would", "please", "may"])
        has_keyword = any(keyword.text.split()[0].lower() in lowered for keyword in task.keywords)
        base_score = 78 + (8 if has_polite_marker else 0) + (8 if has_keyword else 0)
        score = min(base_score, 96)

        corrected = self._corrected_sentence(task)
        feedback_cn = "表达方向正确。可以继续注意语序、关键词完整度，以及场景中的语气自然度。"
        if task.level == 3 and not has_polite_marker:
            feedback_cn = "意思基本清楚，但实战场景建议加入 could/would 等礼貌表达，语气会更自然。"

        return Feedback(
            score=score,
            grammar_score=max(score - 3, 0),
            authenticity_score=max(score - 6, 0),
            politeness_score=score if has_polite_marker else max(score - 12, 0),
            corrected_sentence=corrected,
            feedback_cn=feedback_cn,
            mistakes=[] if score >= 88 else [
                {
                    "type": "tone",
                    "original": user_input,
                    "suggestion": corrected,
                    "explanation_cn": "可以使用更完整、更贴合场景的句式，让表达更自然。",
                }
            ],
            alternatives=Alternatives(
                polite=corrected,
                neutral=self._neutral_sentence(task),
                casual=self._casual_sentence(task),
            ),
        )

    async def generate_hints(self, task: GeneratedTask) -> tuple[Alternatives, str]:
        return (
            Alternatives(
                polite=self._corrected_sentence(task),
                neutral=self._neutral_sentence(task),
                casual=self._casual_sentence(task),
            ),
            "先抓住关键词，再根据关系选择礼貌、自然或随意的说法。",
        )

    def _resolve_scenario(self, profile: dict, category: str, scenario_name: str | None) -> str:
        if scenario_name and scenario_name.strip():
            return scenario_name.strip()

        scenes = profile["scenes"]
        category_matches = [scene for scene in scenes if category.lower() in scene.lower()]
        return random.choice(category_matches or scenes)

    def _build_scenario_generation_prompt(self, level: int, category: str) -> str:
        return build_scenario_generation_prompt(level, category)

    def _expression_for(self, level: int, scenario: str) -> dict:
        if level == 1:
            return {
                "cn_sentence": f"我想要这个{scenario}里的东西。",
                "context_cn": f"你在 {scenario} 场景里，想简单说出自己想要什么。",
                "keywords": [
                    Keyword(text="want", phonetic="/wɑːnt/", meaning_cn="想要", example="I want this one."),
                    Keyword(text="this one", phonetic=None, meaning_cn="这个", example="I want this one."),
                    Keyword(text="please", phonetic="/pliːz/", meaning_cn="请", example="This one, please."),
                ],
            }
        if level == 2:
            return {
                "cn_sentence": f"请问在{scenario}这个场景下，我应该怎么确认时间或要求？",
                "context_cn": f"你需要在 {scenario} 场景里礼貌地询问信息，并说清楚具体需求。",
                "keywords": [
                    Keyword(text="could you", phonetic=None, meaning_cn="你能否", example="Could you tell me the time?"),
                    Keyword(text="need to", phonetic=None, meaning_cn="需要", example="Do I need to bring anything?"),
                    Keyword(text="by", phonetic="/baɪ/", meaning_cn="在……之前", example="Should I finish it by Friday?"),
                ],
            }
        return {
            "cn_sentence": f"在{scenario}场景中，请礼貌地提出你的需求并确认对方是否方便。",
            "context_cn": f"你正在处理真实的 {scenario} 沟通，需要表达清楚、自然、有礼貌。",
            "keywords": [
                Keyword(
                    text="would it be possible",
                    phonetic=None,
                    meaning_cn="是否可以",
                    example="Would it be possible to reschedule?",
                ),
                Keyword(
                    text="I was wondering",
                    phonetic=None,
                    meaning_cn="我想问一下",
                    example="I was wondering if you had a moment.",
                ),
                Keyword(
                    text="confirm",
                    phonetic="/kənˈfɜːrm/",
                    meaning_cn="确认",
                    example="Could you confirm the details?",
                ),
            ],
        }

    def _corrected_sentence(self, task: GeneratedTask) -> str:
        scenario = self._scenario_from_task(task)
        if task.level == 1:
            return f"I want this one in the {scenario}, please."
        if task.level == 2:
            return f"Could you tell me what I need to do for the {scenario}?"
        return f"I was wondering if it would be possible to confirm the details for the {scenario}."

    def _neutral_sentence(self, task: GeneratedTask) -> str:
        scenario = self._scenario_from_task(task)
        if task.level == 1:
            return f"I want this one in the {scenario}."
        if task.level == 2:
            return f"What do I need to do for the {scenario}?"
        return f"Can we confirm the details for the {scenario}?"

    def _casual_sentence(self, task: GeneratedTask) -> str:
        scenario = self._scenario_from_task(task)
        if task.level == 1:
            return "This one, please."
        if task.level == 2:
            return f"What should I do for the {scenario}?"
        return f"Can we check the {scenario} details?"

    def _scenario_from_task(self, task: GeneratedTask) -> str:
        return task.task_name.replace(" 情景表达", "").strip() or task.category


def get_ai_client() -> AIClient:
    return MockAIClient()
