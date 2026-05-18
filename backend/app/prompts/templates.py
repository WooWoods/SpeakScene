LEVEL_PROFILES = {
    1: {
        "name": "启蒙",
        "tone": "极度鼓励，容错高，关注关键词输出",
        "scenes": [
            "supermarket fruit shelf",
            "toy store",
            "zoo ticket gate",
            "playground slide",
            "classroom colors game",
            "family breakfast",
            "birthday party",
            "pet shop",
            "park picnic",
            "ice cream stand",
            "clothing store",
            "bus stop with parents",
            "school bag packing",
            "bedtime story",
            "doctor checkup",
            "library picture book corner",
            "art class",
            "sports day",
            "farm visit",
            "train station with family",
        ],
    },
    2: {
        "name": "进阶",
        "tone": "关注考试常见语法、时态、介词、单复数",
        "scenes": [
            "asking a teacher about homework",
            "borrowing books at the library",
            "joining a school club",
            "planning a weekend hobby",
            "preparing for an exam",
            "asking for directions on campus",
            "ordering food in the cafeteria",
            "talking about a class project",
            "inviting a classmate to practice",
            "reporting a lost item",
            "making an appointment with a teacher",
            "discussing a group presentation",
            "checking the school timetable",
            "asking about sports practice",
            "buying stationery",
            "talking about vacation plans",
            "describing a favorite movie",
            "asking about a museum visit",
            "joining an online class",
            "asking for help with a math problem",
        ],
    },
    3: {
        "name": "实战",
        "tone": "关注礼貌度、地道性、商务和旅行场景表达",
        "scenes": [
            "client meeting",
            "project kickoff",
            "rescheduling a business call",
            "airport check-in",
            "hotel front desk",
            "restaurant reservation",
            "asking for an invoice",
            "confirming delivery details",
            "negotiating a deadline",
            "giving feedback to a teammate",
            "clarifying data in a meeting",
            "networking at a conference",
            "handling a customer complaint",
            "requesting technical support",
            "booking a taxi",
            "asking about dietary requirements",
            "checking out of a hotel",
            "making a small talk introduction",
            "confirming a contract detail",
            "following up after an interview",
            "explaining a product issue",
            "asking for a refund",
            "arranging a factory visit",
            "discussing budget constraints",
        ],
    },
}


SCENARIO_GENERATION_CONTRACT = """
Generate one realistic English-learning scenario name for the requested level.
Return strict JSON with:
- scenario_name: short English scenario name, 3-8 words
- reason_cn: short Chinese explanation of why it fits the level

Rules:
- Match the learner level profile and category.
- Prefer everyday, concrete situations over broad labels.
- Do not return a dialogue or a full task here; only the scenario.
- Avoid repeating the examples already provided in the prompt.
"""


TASK_GENERATION_CONTRACT = """
Return a JSON object with:
- task_name: short Chinese title
- cn_sentence: Chinese sentence the learner should express in English
- context_cn: one-sentence Chinese context
- keywords: array of 3-4 objects with text, phonetic, meaning_cn, example
"""


FEEDBACK_CONTRACT = """
Return strict JSON with score, grammar_score, authenticity_score, politeness_score,
corrected_sentence, feedback_cn, mistakes, and alternatives.
alternatives must contain polite, neutral, casual English versions.
"""


def build_scenario_generation_prompt(level: int, category: str) -> str:
    profile = LEVEL_PROFILES[level]
    examples = ", ".join(profile["scenes"][:8])
    return f"""
{SCENARIO_GENERATION_CONTRACT}

Level: {level} - {profile["name"]}
Level tone: {profile["tone"]}
Category: {category}
Example scenarios to avoid copying exactly: {examples}
"""
