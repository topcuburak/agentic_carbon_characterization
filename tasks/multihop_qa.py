"""
Multi-Hop QA tasks.
Questions requiring 2-5 chained information lookups and computation.
"""

from tasks.task_schema import Task

SYSTEM_PROMPT = (
    "You are a research assistant. Answer questions by searching the knowledge base "
    "and using the calculator for computations. Always use tools to look up facts — "
    "do not rely on your own knowledge. Show your reasoning."
)

MULTIHOP_QA_TASKS = [
    Task(
        id="mhqa_01",
        category="multihop_qa",
        prompt=(
            "What is the combined GDP of the three largest countries by area in South America? "
            "Return the answer in billions USD."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=3019,  # Brazil 2130 + Argentina 621 + Peru 268
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 5},
        tools_required=["search", "calculator"],
        min_steps=4,
    ),
    Task(
        id="mhqa_02",
        category="multihop_qa",
        prompt=(
            "How many times heavier is the heaviest land mammal than the heaviest bird? "
            "Round to the nearest integer."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=46,  # ~6000kg / ~130kg
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 15},
        tools_required=["search", "calculator"],
        min_steps=3,
    ),
    Task(
        id="mhqa_03",
        category="multihop_qa",
        prompt=(
            "What is the population density of the country where the longest river "
            "in Europe ends? Give the answer in people per km²."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=8.4,  # Russia: 144M / 17.1M km²
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 15},
        tools_required=["search", "calculator"],
        min_steps=4,
    ),
    Task(
        id="mhqa_04",
        category="multihop_qa",
        prompt=(
            "Alfred Nobel, the inventor of dynamite, was born in which city? "
            "Name one Nobel Prize in Physics laureate who was also born in that city."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer="Stockholm",  # Factual lookup
        evaluation_type="rubric",
        evaluation_config={"criteria": ["mentions Stockholm", "names a physicist born in Stockholm"]},
        tools_required=["search"],
        min_steps=2,
    ),
    Task(
        id="mhqa_05",
        category="multihop_qa",
        prompt="What is the sum of the atomic numbers of elements discovered by Marie Curie?",
        system_prompt=SYSTEM_PROMPT,
        expected_answer=172,  # Polonium(84) + Radium(88)
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 0},
        tools_required=["search", "calculator"],
        min_steps=3,
    ),
    Task(
        id="mhqa_06",
        category="multihop_qa",
        prompt=(
            "What is the elevation difference in meters between the highest capital city "
            "and the lowest capital city in the world?"
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=3668,  # La Paz ~3640m - Baku ~-28m = 3668m
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 5},
        tools_required=["search", "calculator"],
        min_steps=4,
    ),
    Task(
        id="mhqa_07",
        category="multihop_qa",
        prompt=(
            "How many years apart were the first and last US presidents born in Virginia?"
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=124,  # Washington 1732, Wilson 1856
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 0},
        tools_required=["search", "calculator"],
        min_steps=3,
    ),
    Task(
        id="mhqa_08",
        category="multihop_qa",
        prompt=(
            "What percentage of the EU's total area does its largest member state occupy? "
            "Round to one decimal place."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=15.2,  # France 643801 / EU 4233262 * 100
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 5},
        tools_required=["search", "calculator"],
        min_steps=3,
    ),
    Task(
        id="mhqa_09",
        category="multihop_qa",
        prompt=(
            "What is the approximate total length in km of the borders between France "
            "and all its neighboring countries?"
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=2883,
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 5},
        tools_required=["search", "calculator"],
        min_steps=3,
    ),
    Task(
        id="mhqa_10",
        category="multihop_qa",
        prompt=(
            "Which planet has the most moons, and what is the ratio of its moons "
            "to Earth's moons?"
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=146,  # Saturn: 146 moons, ratio 146:1
        evaluation_type="numeric",
        evaluation_config={"tolerance_pct": 5},
        tools_required=["search", "calculator"],
        min_steps=3,
    ),
]
