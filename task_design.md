# Agent Task Suite Design

## Overview
5 categories, ~10-20 tasks each, designed to stress different agentic patterns.
All tasks require multi-step reasoning and tool use — not solvable in a single LLM call.

## Tools Available to Agents
Agents will have access to a standardized tool set (10 tools, implemented as Python functions):

### Information Retrieval
- `search(query)` — keyword search over a provided knowledge base
- `web_lookup(topic)` — retrieve a pre-cached document on a topic (simulated web)

### Computation
- `calculator(expression)` — evaluate math expressions
- `python_exec(code)` — execute Python code and return stdout/stderr

### System Interaction
- `shell_exec(command)` — run a shell command in a sandboxed environment (whitelisted commands only)
- `http_request(url, method, headers, body)` — make HTTP calls to a local mock API server

### Structured Data Access
- `database_query(sql)` — execute SQL queries on a pre-populated SQLite database

### File I/O
- `read_file(path)` — read a file from a sandboxed directory
- `write_file(path, content)` — write a file to a sandboxed directory
- `list_files(directory)` — list files in a directory

### Supporting Infrastructure
- **Mock API server** — local FastAPI app serving pre-defined REST endpoints (e.g., /api/products, /api/users, /api/weather) for reproducible http_request calls
- **SQLite database** — pre-populated with synthetic tables (sales, employees, weather, inventory) for database_query tasks
- **Knowledge base** — JSON/text files for search and web_lookup tools

---

## Category 1: Multi-Hop QA (10 tasks)
**Goal:** Answer questions that require chaining 2-5 information lookups.
**Tools:** search, calculator
**What it stresses:** Sequential reasoning depth, information synthesis

### Example Tasks:
1. "What is the combined GDP of the three largest countries by area in South America? Return the answer in billions USD."
   → Requires: search(largest countries by area in SA) → search(GDP of Brazil) → search(GDP of Argentina) → search(GDP of Peru) → calculator(sum)

2. "How many times heavier is the heaviest land mammal than the heaviest bird? Round to the nearest integer."
   → Requires: search(heaviest land mammal) → search(heaviest bird) → calculator(divide)

3. "What is the population density of the country where the longest river in Europe ends?"
   → Requires: search(longest river Europe) → search(where does it end) → search(country population) → search(country area) → calculator(density)

4. "Which Nobel Prize in Physics laureate was born in the same city as the inventor of dynamite?"
   → Requires: search(inventor of dynamite birthplace) → search(Nobel laureates born in Stockholm)

5. "What is the sum of the atomic numbers of elements discovered by Marie Curie?"
   → Requires: search(elements discovered by Marie Curie) → search(atomic number polonium) → search(atomic number radium) → calculator(sum)

6. "What is the elevation difference between the highest capital city and the lowest capital city in the world?"
   → Requires: search(highest capital) → search(lowest capital) → search(elevation La Paz) → search(elevation Baku) → calculator(difference)

7. "How many years apart were the first and last US presidents born in Virginia?"
   → Requires: search(US presidents born in Virginia) → search(birth years) → calculator(difference)

8. "What percentage of the EU's total area does its largest member state occupy?"
   → Requires: search(largest EU member by area) → search(France area) → search(EU total area) → calculator(percentage)

9. "What is the total length in km of the borders between France and all its neighboring countries?"
   → Requires: search(France neighbors) → search(border length) for each → calculator(sum)

10. "Which planet has the most moons, and what is the ratio of its moons to Earth's moons?"
    → Requires: search(planet most moons) → search(Saturn moon count) → calculator(ratio)

**Evaluation:** Exact answer match (numeric with tolerance) or factual correctness.

---

## Category 2: Code Generation + Debugging (15 tasks)
**Goal:** Write code to solve a problem, execute it, and fix errors iteratively.
**Tools:** python_exec, write_file, read_file
**What it stresses:** Reflection loops, retry overhead, error correction

### Example Tasks:
1. "Write a Python function that finds the longest palindromic substring in a given string. Test it with: 'babad', 'cbbd', 'racecarannakayak'. Return results."

2. "Write a Python script that reads a CSV file (provided) containing student names and grades, computes the class average, median, and identifies students below average. Output as formatted table."

3. "Implement a binary search tree with insert, delete, and in-order traversal. Insert [5,3,7,1,4,6,8], delete 3, print traversal."

4. "Write a function to solve the 0/1 knapsack problem using dynamic programming. Test with weights=[2,3,4,5], values=[3,4,5,6], capacity=8."

5. "Create a Python script that generates the first 20 numbers of the Fibonacci sequence using matrix exponentiation. Verify against iterative method."

6. "Write a Python function that validates whether a given string of parentheses, brackets, and braces is balanced. Test with 10 provided test cases." (5 valid, 5 invalid)

7. "Implement Dijkstra's shortest path algorithm. Given an adjacency list (provided), find shortest path from node A to node F."

8. "Write a script that takes a nested JSON (provided) and flattens it into dot-notation keys. Handle arrays by using index notation."

9. "Implement a simple LRU cache class with get() and put() methods. Demonstrate with a sequence of 20 operations."

10. "Write a function that converts a Roman numeral string to an integer and vice versa. Test with: 1994, 58, 3999, 'MCMXCIV', 'LVIII'."

11. "Write a Python script that simulates a simple bank account system with deposit, withdraw, and transfer between accounts. Include overdraft protection. Run provided test scenario."

12. "Implement merge sort and count the number of inversions in an array. Test with [2,4,1,3,5] and [5,4,3,2,1]."

13. "Write a script that parses a simple arithmetic expression string (with +,-,*,/,parentheses) and evaluates it without using eval(). Test with '3+(2*4)-6/(3-1)'."

14. "Implement a trie data structure with insert, search, and prefix-search. Insert a provided list of 20 words, then test search and prefix queries."

15. "Write a function that finds all prime factors of a number using Pollard's rho algorithm. Test with 600851475143."

**Evaluation:** Code executes successfully + output correctness.

**Key metric:** Number of execute→fix cycles per task (directly measures reflection overhead).

---

## Category 3: Research & Summarization (10 tasks)
**Goal:** Gather information from multiple sources and synthesize a structured report.
**Tools:** web_lookup, search, write_file
**What it stresses:** Multi-step planning, information gathering breadth, long context accumulation

### Example Tasks:
1. "Compare renewable energy adoption rates in Germany, China, and the US. Cover solar, wind, and hydroelectric. Write a 300-word summary with key statistics."

2. "Research the causes and effects of the 2008 financial crisis. Identify the 5 most important contributing factors and explain each in 2-3 sentences."

3. "Compare three database systems (PostgreSQL, MongoDB, Cassandra) across: data model, scalability, consistency guarantees, and ideal use cases. Present as a structured comparison."

4. "Summarize the history and current state of quantum computing. Cover: key milestones, current hardware approaches, major players, and practical applications."

5. "Research the environmental impact of cryptocurrency mining. Cover: energy consumption, carbon footprint, comparison to traditional banking, and proposed solutions."

6. "Compare the healthcare systems of the US, UK, and Japan. Cover: cost, coverage, outcomes, and public satisfaction."

7. "Research the development of mRNA vaccine technology. Cover: history, key breakthroughs, COVID-19 application, and future potential."

8. "Analyze the pros and cons of remote work. Cover: productivity, employee wellbeing, environmental impact, and economic effects."

9. "Research the current state of autonomous vehicles. Cover: technology levels (L1-L5), major companies, regulatory challenges, and safety statistics."

10. "Compare three programming paradigms (OOP, functional, procedural). Provide: core principles, strengths, weaknesses, and best-suited problem types."

**Evaluation:** Rubric-based scoring: coverage (did it address all sub-topics?), accuracy, structure, and conciseness.

**Key metric:** Number of web_lookup/search calls, total tokens accumulated across all calls.

---

## Category 4: Data Analysis (10 tasks)
**Goal:** Analyze provided datasets and answer specific analytical questions.
**Tools:** python_exec, read_file, calculator
**What it stresses:** Tool selection, iterative exploration, computation cycles

### Datasets (synthetic, provided as CSV):
- `sales_data.csv` — 1000 rows: date, product, region, revenue, units_sold
- `weather_data.csv` — 365 rows: date, city, temperature, humidity, precipitation
- `employee_data.csv` — 500 rows: id, department, salary, years_experience, performance_score

### Example Tasks:
1. "Using sales_data.csv: What are the top 3 products by revenue in each region? Show as a table."

2. "Using weather_data.csv: Which city has the highest temperature variance? Plot a histogram of daily temperatures for that city and save as PNG."

3. "Using employee_data.csv: Is there a correlation between years of experience and performance score? Compute Pearson correlation and p-value."

4. "Using sales_data.csv: Identify the month with the highest total revenue. What percentage of that month's revenue came from the top product?"

5. "Using weather_data.csv: Find all days where temperature exceeded 2 standard deviations above the city mean. Which city had the most such outlier days?"

6. "Using employee_data.csv: What is the salary gap between the highest and lowest paid departments? Compute mean, median, and std for each department."

7. "Using sales_data.csv: Compute month-over-month revenue growth rate. Which month had the largest decline?"

8. "Using weather_data.csv: What is the correlation between humidity and precipitation across all cities? Run a linear regression and report R²."

9. "Using employee_data.csv: Segment employees into performance quartiles. What is the average salary and experience for each quartile?"

10. "Using sales_data.csv: Forecast next month's revenue using a simple moving average (window=3). Compare with actual if available."

**Evaluation:** Numeric accuracy of answers + completeness.

**Key metric:** Number of python_exec calls, iterative refinement cycles.

---

## Category 5: Multi-Agent Collaboration (10 tasks)
**Goal:** Tasks that benefit from role specialization and agent-to-agent delegation.
**Tools:** All tools available, agents can delegate sub-tasks
**What it stresses:** Communication overhead, token amplification from inter-agent messages

**Note:** For frameworks that don't natively support multi-agent (or for baselines), these run as single-agent. This measures whether multi-agent overhead is justified.

### Example Tasks:
1. "Plan a 3-day tech conference. Agent roles: venue coordinator (finds venue specs), content planner (designs tracks/sessions), budget analyst (estimates costs). Produce a unified plan."

2. "Conduct a code review pipeline: Developer agent writes a sorting algorithm, Reviewer agent reviews for bugs/efficiency, Developer fixes issues. Iterate until Reviewer approves."

3. "Market analysis: Researcher agent gathers data on 3 competitors, Analyst agent identifies trends and gaps, Strategist agent proposes recommendations. Produce a final report."

4. "Debate: Agent A argues for nuclear energy, Agent B argues against. Moderator agent summarizes key points from both sides and declares which argument was more evidence-based."

5. "Project estimation: Requirements agent breaks down a software project description into tasks, Estimation agent assigns story points, Risk agent identifies potential blockers. Produce a project plan."

6. "Data pipeline: Collector agent reads and validates raw data, Transformer agent cleans and transforms it, Analyst agent runs analysis and reports findings."

7. "Technical documentation: Reader agent examines provided code, Writer agent produces API documentation, Reviewer agent checks for accuracy and completeness."

8. "Bug triage: Reporter agent describes a bug scenario, Investigator agent examines code to identify root cause, Fixer agent proposes and tests a fix."

9. "Content creation: Researcher agent gathers facts on a topic, Writer agent drafts an article, Editor agent refines for clarity and accuracy."

10. "System design: Requirements agent clarifies the problem, Architect agent proposes a design, Critic agent identifies weaknesses, Architect revises."

**Evaluation:** Quality rubric (completeness, coherence, correctness of final output) + tracking of inter-agent messages.

**Key metric:** Total tokens exchanged between agents, number of delegation rounds, ratio of "overhead tokens" (agent coordination) to "useful tokens" (actual task work).

---

## Power Measurement Methodology

### Goals
Break down energy consumption into **CPU** and **GPU** components per run, and further attribute energy to distinct **execution phases** within each agentic run.

### Execution Phases
Each agentic run is decomposed into the following phases, logged with timestamps:

| Phase | Description | Expected Dominant Resource |
|-------|-------------|--------------------------|
| `inference_prefill` | Processing the prompt (input tokens) | GPU |
| `inference_decode` | Generating output tokens | GPU |
| `tool_execution` | Running a tool (python_exec, search, etc.) | CPU |
| `orchestration` | Framework overhead — prompt assembly, routing, state updates, parsing | CPU |
| `idle` | Gaps between phases (e.g., waiting, scheduling) | Both (low) |

### Hardware Counters

| Resource | Method | Sampling Rate |
|----------|--------|---------------|
| **GPU power (W)** | NVML (`pynvml`) per-GPU | 100ms |
| **CPU power (W)** | Intel RAPL `/sys/class/powercap/intel-rapl:*/energy_uj` — delta-based | 100ms |
| **DRAM power (W)** | Intel RAPL DRAM domain (if available) | 100ms |

### Phase Attribution
The benchmarking harness instruments the agent execution loop with **phase markers**:
- Before/after each LLM call → `inference` phase
- Before/after each tool invocation → `tool_execution` phase
- Everything else → `orchestration` phase

Power samples are aligned with phase timestamps to compute:
- `E_gpu_inference` — GPU energy during inference phases (Wh)
- `E_gpu_tool` — GPU energy during tool execution (mostly idle power)
- `E_cpu_inference` — CPU energy during inference phases (mostly idle power)
- `E_cpu_tool` — CPU energy during tool execution phases (Wh)
- `E_cpu_orchestration` — CPU energy during orchestration (Wh)
- `E_total` — Total energy = sum of all components

### Derived Metrics

| Metric | Formula | What it reveals |
|--------|---------|-----------------|
| **Token amplification factor** | `total_tokens_agentic / total_tokens_single_shot` | How much more "work" the agent does |
| **Energy amplification factor** | `E_total_agentic / E_total_single_shot` | True energy overhead of agentic execution |
| **GPU energy fraction** | `E_gpu / E_total` | How GPU-dominant the workload is |
| **Orchestration overhead ratio** | `E_orchestration / E_total` | Framework tax |
| **Energy per correct answer** | `E_total / correctness_score` | Efficiency-adjusted energy cost |

### Power Trace Visualization
Each run produces a time-series CSV:
```
timestamp_ms, phase, gpu0_power_w, gpu1_power_w, cpu_pkg_power_w, dram_power_w
0, orchestration, 45.2, 44.8, 28.1, 5.2
100, inference_prefill, 285.3, 280.1, 35.4, 8.1
200, inference_decode, 250.1, 248.7, 32.0, 7.5
...
```
This enables per-run **stacked area plots** (GPU vs CPU vs DRAM power over time, colored by phase).

---

## Experimental Controls

### Baseline: Single-Shot (Non-Agentic)
For each task, also run a **single-shot prompt** — feed the full task description to the LLM in one call with no tools, no iteration. This provides the baseline for computing **token amplification factor**.

### Repetitions
Each task × framework × model combination runs **3 times** to capture variance (LLM non-determinism, different agent paths).

### Total Experiment Scale
- 5 categories × ~10-15 tasks = 55 tasks
- × 5 frameworks = 275 framework-task pairs
- × 2 models = 550 model-framework-task combinations
- × 3 repetitions = 1,650 runs
- + 55 tasks × 2 models × 3 reps = 330 single-shot baseline runs
- **Total: ~1,980 runs**
