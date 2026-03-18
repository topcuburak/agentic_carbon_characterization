"""
Data Analysis tasks.
Analyze provided datasets (CSV/SQLite) and answer analytical questions.
"""

from tasks.task_schema import Task

SYSTEM_PROMPT = (
    "You are a data analyst. Use python_exec to write and run Python code for data analysis. "
    "Use read_file to examine CSV files and database_query for SQL queries. "
    "Use the calculator for simple computations. Show your work and print results clearly."
)

DATA_ANALYSIS_TASKS = [
    Task(
        id="da_01",
        category="data_analysis",
        prompt=(
            "Using the database, find the top 3 products by total revenue in each region "
            "from the sales table. Present the results as a formatted table."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,  # Dynamic based on synthetic data
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "queries the sales table correctly",
                "groups by region and product",
                "shows top 3 per region",
                "presents results in a table format",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        min_steps=2,
    ),
    Task(
        id="da_02",
        category="data_analysis",
        prompt=(
            "Read the weather_data.csv file and determine which city has the highest "
            "temperature variance. Compute the variance for each city and report the results."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "reads the CSV correctly",
                "computes variance per city",
                "identifies the city with highest variance",
                "shows numeric results",
            ],
            "min_score": 3,
        },
        tools_required=["python_exec", "read_file"],
        min_steps=2,
    ),
    Task(
        id="da_03",
        category="data_analysis",
        prompt=(
            "Using the employees table in the database, compute the Pearson correlation "
            "between years_experience and performance_score. Report the correlation "
            "coefficient and interpret whether it's statistically significant."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "queries employee data correctly",
                "computes Pearson correlation",
                "reports the coefficient value",
                "provides interpretation",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        min_steps=2,
    ),
    Task(
        id="da_04",
        category="data_analysis",
        prompt=(
            "Using the sales table, identify the month with the highest total revenue. "
            "Then compute what percentage of that month's revenue came from the top-selling product."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "correctly aggregates revenue by month",
                "identifies the top month",
                "finds the top product in that month",
                "computes percentage correctly",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec", "calculator"],
        min_steps=3,
    ),
    Task(
        id="da_05",
        category="data_analysis",
        prompt=(
            "Using weather_data.csv, find all days where temperature exceeded 2 standard "
            "deviations above the city mean. Which city had the most such outlier days? "
            "List the specific dates for that city."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "computes per-city mean and std correctly",
                "identifies outlier days (>2 std above mean)",
                "identifies city with most outliers",
                "lists specific dates",
            ],
            "min_score": 3,
        },
        tools_required=["python_exec", "read_file"],
        min_steps=2,
    ),
    Task(
        id="da_06",
        category="data_analysis",
        prompt=(
            "Using the employees table, compute the mean, median, and standard deviation "
            "of salary for each department. Which department has the largest salary gap "
            "(difference between max and min)?"
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "computes mean salary per department",
                "computes median salary per department",
                "computes std per department",
                "identifies largest salary gap department",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        min_steps=2,
    ),
    Task(
        id="da_07",
        category="data_analysis",
        prompt=(
            "Using the sales table, compute month-over-month revenue growth rate for 2025. "
            "Which month had the largest revenue decline? Show the growth rates for all months."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "aggregates monthly revenue",
                "computes growth rate correctly",
                "identifies largest decline",
                "shows all monthly rates",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        min_steps=2,
    ),
    Task(
        id="da_08",
        category="data_analysis",
        prompt=(
            "Using weather_data.csv, compute the correlation between humidity and "
            "precipitation across all cities. Run a simple linear regression and report "
            "the R² value and regression coefficients."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "loads weather data correctly",
                "computes correlation",
                "runs linear regression",
                "reports R² and coefficients",
            ],
            "min_score": 3,
        },
        tools_required=["python_exec", "read_file"],
        min_steps=2,
    ),
    Task(
        id="da_09",
        category="data_analysis",
        prompt=(
            "Using the employees table, segment employees into performance quartiles "
            "(Q1=bottom 25%, Q4=top 25%). For each quartile, compute the average salary "
            "and average years of experience."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "correctly defines quartile boundaries",
                "assigns employees to quartiles",
                "computes average salary per quartile",
                "computes average experience per quartile",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        min_steps=2,
    ),
    Task(
        id="da_10",
        category="data_analysis",
        prompt=(
            "Using the orders table in the database, find: (1) the total revenue by status, "
            "(2) the customer with the most orders, and (3) the most popular product. "
            "Use both SQL queries and Python for analysis. Present a complete summary."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=None,
        evaluation_type="rubric",
        evaluation_config={
            "criteria": [
                "computes revenue by status",
                "finds customer with most orders",
                "finds most popular product",
                "presents a clear summary",
            ],
            "min_score": 3,
        },
        tools_required=["database_query", "python_exec"],
        min_steps=3,
    ),
]
