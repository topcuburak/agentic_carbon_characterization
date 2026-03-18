"""
Research & Summarization tasks.
Gather information from multiple sources and synthesize structured reports.
"""

from tasks.task_schema import Task

SYSTEM_PROMPT = (
    "You are a research analyst. Gather information using web_lookup and search tools, "
    "then synthesize your findings into a clear, structured report. "
    "Always use tools to look up facts — do not rely on your own knowledge. "
    "Cite which lookups you used."
)

RESEARCH_SUMMARIZATION_TASKS = [
    Task(
        id="res_01",
        category="research_summarization",
        prompt=(
            "Compare renewable energy adoption rates in Germany, China, and the US. "
            "Cover solar, wind, and hydroelectric. Write a 300-word summary with key statistics."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "covers Germany solar, wind, hydroelectric with numbers",
                "covers China solar, wind, hydroelectric with numbers",
                "covers US solar, wind, hydroelectric with numbers",
                "comparative analysis across countries",
                "approximately 300 words",
            ],
            "min_score": 3,  # out of 5
        },
        tools_required=["web_lookup", "search"],
        min_steps=3,
    ),
    Task(
        id="res_02",
        category="research_summarization",
        prompt=(
            "Research the causes and effects of the 2008 financial crisis. "
            "Identify the 5 most important contributing factors and explain each in 2-3 sentences."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "identifies 5 distinct contributing factors",
                "mentions subprime mortgages",
                "mentions securitization/CDOs",
                "mentions regulatory failures",
                "each factor explained in 2-3 sentences",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=2,
    ),
    Task(
        id="res_03",
        category="research_summarization",
        prompt=(
            "Compare three database systems (PostgreSQL, MongoDB, Cassandra) across: "
            "data model, scalability, consistency guarantees, and ideal use cases. "
            "Present as a structured comparison table or sections."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "covers all three databases",
                "discusses data model for each",
                "discusses scalability for each",
                "discusses consistency for each",
                "identifies ideal use cases for each",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=3,
    ),
    Task(
        id="res_04",
        category="research_summarization",
        prompt=(
            "Summarize the history and current state of quantum computing. "
            "Cover: key milestones, current hardware approaches, major players, "
            "and practical applications."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "mentions key milestones (Feynman, Shor, quantum supremacy)",
                "covers hardware approaches (superconducting, trapped ions, etc.)",
                "names major players (IBM, Google, etc.)",
                "discusses practical applications",
                "coherent narrative structure",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=2,
    ),
    Task(
        id="res_05",
        category="research_summarization",
        prompt=(
            "Research the environmental impact of cryptocurrency mining. "
            "Cover: energy consumption, carbon footprint, comparison to traditional banking, "
            "and proposed solutions."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "provides energy consumption numbers",
                "provides carbon footprint estimates",
                "compares to traditional banking",
                "discusses proposed solutions",
                "balanced presentation",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=2,
    ),
    Task(
        id="res_06",
        category="research_summarization",
        prompt=(
            "Compare the healthcare systems of the US, UK, and Japan. "
            "Cover: cost, coverage, outcomes (life expectancy), and public satisfaction."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "covers all three countries",
                "includes cost/spending data",
                "discusses coverage",
                "includes life expectancy or outcome data",
                "mentions satisfaction or quality assessment",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=3,
    ),
    Task(
        id="res_07",
        category="research_summarization",
        prompt=(
            "Research the development of mRNA vaccine technology. "
            "Cover: history, key breakthroughs, COVID-19 application, and future potential."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "covers history (1990s origins)",
                "mentions Karikó and Weissman's breakthrough",
                "covers COVID-19 vaccine development",
                "discusses future applications",
                "includes specific data points",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=2,
    ),
    Task(
        id="res_08",
        category="research_summarization",
        prompt=(
            "Analyze the pros and cons of remote work. "
            "Cover: productivity, employee wellbeing, environmental impact, and economic effects."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "discusses productivity impact with data",
                "covers employee wellbeing (positive and negative)",
                "mentions environmental effects",
                "discusses economic implications",
                "balanced analysis",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=2,
    ),
    Task(
        id="res_09",
        category="research_summarization",
        prompt=(
            "Research the current state of autonomous vehicles. "
            "Cover: SAE levels (L1-L5), major companies, regulatory challenges, and safety statistics."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "explains SAE levels",
                "names major companies with specifics",
                "discusses regulatory landscape",
                "includes safety data",
                "current state (not just future predictions)",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=2,
    ),
    Task(
        id="res_10",
        category="research_summarization",
        prompt=(
            "Compare three programming paradigms (OOP, functional, procedural). "
            "For each provide: core principles, strengths, weaknesses, and best-suited problem types."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "covers all three paradigms",
                "describes core principles for each",
                "identifies strengths for each",
                "identifies weaknesses for each",
                "recommends problem types for each",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search"],
        min_steps=3,
    ),
]
