import json


LEVEL_PROFILES = {
    1: {
        "name": "启蒙",
        "tone": "短句、强鼓励、生活化，不要求完整复杂输出",
        "scenes": ["toy store", "ice cream stand", "zoo ticket gate", "family breakfast"],
    },
    2: {
        "name": "进阶",
        "tone": "校园和日常交流，关注基础语法、时态和清晰表达",
        "scenes": ["asking a teacher about homework", "library help desk", "school club signup", "cafeteria order"],
    },
    3: {
        "name": "实战",
        "tone": "商务、旅行和跨文化沟通，关注礼貌度、地道性和场景契合",
        "scenes": ["client meeting", "hotel front desk", "restaurant reservation", "airport check-in"],
    },
}


SCENARIO_PACKAGE_CONTRACT = """
Return strict JSON for a scenario-led English practice session:
- scenario_name: short English scenario name
- scenario_context_cn: one concrete Chinese sentence describing the situation
- starter_en: the first natural English sentence spoken by the system
- starter_cn: Chinese meaning of starter_en
- phrases: 8-12 bilingual common expressions for this scenario

Each phrase must contain:
- en: authentic English expression
- cn: Chinese meaning
- usage_note_cn: short Chinese usage note
- tone: one of polite, neutral, casual, professional
- favorite_candidate: boolean

Rules:
- Do not ask the learner to translate a required Chinese sentence.
- The learner should be able to borrow phrases from the left phrase list.
- Prefer common, reusable expressions over rare vocabulary.
"""


CONVERSATION_CONTINUATION_CONTRACT = """
Return strict JSON with:
- text_en: one natural next system message in English
- text_cn: Chinese meaning of text_en

Rules:
- Stay inside the selected scenario.
- Keep the conversation moving with a clear next prompt or response.
- Keep the sentence short enough for speaking practice.
"""


EVALUATION_CONTRACT = """
Return strict JSON with:
- overall_score, vocabulary_score, grammar_score, authenticity_score, fluency_score
- feedback_cn
- strengths: Chinese bullet strings
- improvements: Chinese bullet strings
- suggested_phrases: 3-5 phrase objects using the same phrase schema

Evaluate the user's turns across the whole conversation, not a single required sentence.
"""


def build_scenario_package_prompt(level: int, category: str, scenario_name: str | None = None) -> str:
    profile = LEVEL_PROFILES[level]
    requested = scenario_name or "choose the most useful concrete scenario"
    examples = ", ".join(profile["scenes"])
    return f"""
{SCENARIO_PACKAGE_CONTRACT}

Level: {level} - {profile["name"]}
Level tone: {profile["tone"]}
Category: {category}
Requested scenario: {requested}
Example scenarios: {examples}
"""


def build_conversation_continuation_prompt(
    *,
    level: int,
    category: str,
    scenario_name: str,
    scenario_context_cn: str,
    phrases: list[dict],
    user_turns_count: int,
    latest_user_text: str,
    conversation_history: list[dict],
) -> str:
    profile = LEVEL_PROFILES[level]
    payload = {
        "level": level,
        "level_name": profile["name"],
        "level_tone": profile["tone"],
        "category": category,
        "scenario_name": scenario_name,
        "scenario_context_cn": scenario_context_cn,
        "phrases": phrases,
        "user_turns_count": user_turns_count,
        "latest_user_text": latest_user_text,
        "conversation_history": conversation_history,
    }
    return f"""
{CONVERSATION_CONTINUATION_CONTRACT}

You are the system-side conversation partner in SpeakScene.
Respond naturally as the role implied by the scenario, not as a teacher explaining the app.
Use Chinese only for text_cn.

Context:
{json.dumps(payload, ensure_ascii=False)}
"""


def build_evaluation_prompt(
    *,
    level: int,
    category: str,
    scenario_name: str,
    scenario_context_cn: str,
    phrases: list[dict],
    user_turns: list[str],
) -> str:
    profile = LEVEL_PROFILES[level]
    payload = {
        "level": level,
        "level_name": profile["name"],
        "level_tone": profile["tone"],
        "category": category,
        "scenario_name": scenario_name,
        "scenario_context_cn": scenario_context_cn,
        "phrases": phrases,
        "user_turns": user_turns,
    }
    return f"""
{EVALUATION_CONTRACT}

You are evaluating a Chinese learner's spoken-English practice.
Give practical Chinese feedback, score fairly, and suggest reusable expressions.

Context:
{json.dumps(payload, ensure_ascii=False)}
"""
