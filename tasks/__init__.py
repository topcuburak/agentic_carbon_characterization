"""
Task definitions for agentic AI benchmarking.
Each module defines tasks for one category.
"""

from tasks.multihop_qa import MULTIHOP_QA_TASKS
from tasks.code_gen import CODE_GEN_TASKS
from tasks.research_summarization import RESEARCH_SUMMARIZATION_TASKS
from tasks.data_analysis import DATA_ANALYSIS_TASKS
from tasks.multi_agent import MULTI_AGENT_TASKS

ALL_TASKS = {
    "multihop_qa": MULTIHOP_QA_TASKS,
    "code_gen": CODE_GEN_TASKS,
    "research_summarization": RESEARCH_SUMMARIZATION_TASKS,
    "data_analysis": DATA_ANALYSIS_TASKS,
    "multi_agent": MULTI_AGENT_TASKS,
}
