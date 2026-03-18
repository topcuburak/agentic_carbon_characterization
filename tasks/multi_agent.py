"""
Multi-Agent Collaboration tasks.
Tasks requiring role specialization and agent-to-agent delegation.
For frameworks without native multi-agent support, these run as single-agent.
"""

from tasks.task_schema import Task

SYSTEM_PROMPT = (
    "You are coordinating a team of specialists to complete a complex task. "
    "Break the task into sub-tasks, delegate to the appropriate roles, "
    "and synthesize the results into a cohesive final output. "
    "Use all available tools as needed."
)

MULTI_AGENT_TASKS = [
    Task(
        id="ma_01",
        category="multi_agent",
        prompt=(
            "Plan a 3-day tech conference.\n"
            "Step 1 (Venue Coordinator): Search for venue requirements and capacity needs.\n"
            "Step 2 (Content Planner): Design 3 tracks (AI, Cloud, Security) with 4 sessions each.\n"
            "Step 3 (Budget Analyst): Estimate costs for venue, speakers, catering, and AV equipment.\n"
            "Produce a unified conference plan with schedule, venue specs, and budget breakdown."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "includes venue specifications",
                "has 3 tracks with sessions",
                "provides budget breakdown",
                "coherent unified plan",
                "feasible and realistic",
            ],
            "min_score": 3,
        },
        tools_required=["search", "calculator", "write_file"],
        difficulty="hard",
        min_steps=5,
    ),
    Task(
        id="ma_02",
        category="multi_agent",
        prompt=(
            "Code review pipeline:\n"
            "1. Developer: Write a Python function to sort a list of dictionaries by multiple keys.\n"
            "2. Reviewer: Execute the code, check for bugs, edge cases, and efficiency.\n"
            "3. Developer: Fix any issues found by the reviewer.\n"
            "4. Reviewer: Verify the fixes and approve.\n"
            "Show the complete review cycle with all iterations."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "initial code is written",
                "review identifies specific issues",
                "code is revised based on feedback",
                "final version is verified",
                "working code produced",
            ],
            "min_score": 3,
        },
        tools_required=["python_exec", "write_file", "read_file"],
        difficulty="hard",
        min_steps=4,
    ),
    Task(
        id="ma_03",
        category="multi_agent",
        prompt=(
            "Market analysis report:\n"
            "1. Researcher: Use http_request to fetch product data from the mock API (/api/products). "
            "Also look up competitor information.\n"
            "2. Analyst: Analyze the product catalog — compute average prices by category, "
            "identify pricing gaps.\n"
            "3. Strategist: Based on the analysis, propose 3 strategic recommendations.\n"
            "Produce a complete market analysis report."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "fetches data from API",
                "analyzes pricing by category",
                "identifies market gaps",
                "proposes 3 recommendations",
                "coherent final report",
            ],
            "min_score": 3,
        },
        tools_required=["http_request", "search", "calculator", "python_exec"],
        difficulty="hard",
        min_steps=5,
    ),
    Task(
        id="ma_04",
        category="multi_agent",
        prompt=(
            "Debate on nuclear energy:\n"
            "1. Proponent: Search for evidence supporting nuclear energy (low carbon, reliability, etc.)\n"
            "2. Opponent: Search for evidence against nuclear energy (cost, waste, safety, etc.)\n"
            "3. Moderator: Summarize both positions and evaluate which argument was more evidence-based.\n"
            "Present the full debate with citations."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "pro arguments with evidence",
                "con arguments with evidence",
                "balanced moderator summary",
                "specific data points cited",
                "clear final assessment",
            ],
            "min_score": 3,
        },
        tools_required=["search", "web_lookup"],
        difficulty="medium",
        min_steps=4,
    ),
    Task(
        id="ma_05",
        category="multi_agent",
        prompt=(
            "Project estimation:\n"
            "1. Requirements Agent: Break down this project into tasks: "
            "'Build a REST API for a to-do list app with user auth, CRUD operations, "
            "and a PostgreSQL database.'\n"
            "2. Estimation Agent: Assign story points (1-13 Fibonacci scale) to each task.\n"
            "3. Risk Agent: Identify potential blockers and risks for each task.\n"
            "Produce a project plan with tasks, estimates, and risk assessment."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "breaks project into specific tasks",
                "assigns story points to each",
                "identifies risks/blockers",
                "total estimate is reasonable",
                "complete project plan format",
            ],
            "min_score": 3,
        },
        tools_required=["search", "write_file"],
        difficulty="medium",
        min_steps=4,
    ),
    Task(
        id="ma_06",
        category="multi_agent",
        prompt=(
            "Data pipeline:\n"
            "1. Collector: Read the sales_data.csv file and validate the data "
            "(check for missing values, invalid dates, negative revenues).\n"
            "2. Transformer: Clean the data — remove invalid rows, normalize date formats, "
            "add a 'quarter' column.\n"
            "3. Analyst: Compute quarterly revenue trends and identify the best-performing product.\n"
            "Show the complete pipeline output."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "reads and validates CSV data",
                "cleaning/transformation performed",
                "quarter column added",
                "quarterly trends computed",
                "best product identified",
            ],
            "min_score": 3,
        },
        tools_required=["read_file", "python_exec", "write_file"],
        difficulty="medium",
        min_steps=4,
    ),
    Task(
        id="ma_07",
        category="multi_agent",
        prompt=(
            "Technical documentation:\n"
            "1. Reader: Examine the mock API endpoints by making http_requests to "
            "/api/products, /api/users, /api/orders, and /api/weather.\n"
            "2. Writer: Produce API documentation for each endpoint including URL, "
            "method, parameters, and example response.\n"
            "3. Reviewer: Check the documentation for accuracy and completeness.\n"
            "Write the final documentation to a file."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "explores all 4 API endpoints",
                "documents URL and method for each",
                "includes example responses",
                "review/accuracy check performed",
                "documentation written to file",
            ],
            "min_score": 3,
        },
        tools_required=["http_request", "write_file"],
        difficulty="medium",
        min_steps=5,
    ),
    Task(
        id="ma_08",
        category="multi_agent",
        prompt=(
            "Bug triage:\n"
            "1. Reporter: Describe this bug: 'The inventory system shows negative quantities "
            "for some items after processing returns.'\n"
            "2. Investigator: Query the inventory table in the database to find items with "
            "quantity <= 0. Analyze what might cause negative quantities.\n"
            "3. Fixer: Write a SQL query to fix negative quantities (set to 0) and a Python "
            "validation function to prevent it in the future.\n"
            "Document the complete triage process."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "bug clearly documented",
                "investigation queries the database",
                "root cause analysis provided",
                "fix implemented (SQL and/or Python)",
                "prevention strategy included",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        difficulty="medium",
        min_steps=4,
    ),
    Task(
        id="ma_09",
        category="multi_agent",
        prompt=(
            "Content creation:\n"
            "1. Researcher: Look up information about the environmental impact of "
            "cryptocurrency mining.\n"
            "2. Writer: Draft a 200-word article on the topic, using the researched facts.\n"
            "3. Editor: Review the article for factual accuracy, clarity, and flow. "
            "Suggest and apply improvements.\n"
            "Save the final article to a file."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "research phase gathers relevant facts",
                "draft article is ~200 words",
                "article uses factual data",
                "editing improves the draft",
                "final article saved to file",
            ],
            "min_score": 3,
        },
        tools_required=["web_lookup", "search", "write_file"],
        difficulty="medium",
        min_steps=4,
    ),
    Task(
        id="ma_10",
        category="multi_agent",
        prompt=(
            "System design:\n"
            "1. Requirements Agent: Clarify requirements for: 'A URL shortener service "
            "that handles 10M URLs/day, with analytics on click counts by region.'\n"
            "2. Architect: Propose a system design (components, database choice, API design, "
            "caching strategy).\n"
            "3. Critic: Identify 3 weaknesses or potential failure points in the design.\n"
            "4. Architect: Revise the design to address the criticism.\n"
            "Present the final design document."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "requirements clearly stated",
                "initial design covers key components",
                "criticism identifies real issues",
                "design is revised to address criticism",
                "final design is coherent and complete",
            ],
            "min_score": 3,
        },
        tools_required=["search", "write_file"],
        difficulty="hard",
        min_steps=5,
    ),
]
