"""
Code Generation + Debugging tasks.
Write code, execute, fix errors iteratively.
"""

from tasks.task_schema import Task

SYSTEM_PROMPT = (
    "You are a Python programmer. Write code to solve the given problem, "
    "execute it to verify correctness, and fix any errors. "
    "Use the python_exec tool to run code and the write_file/read_file tools for file I/O."
)

CODE_GEN_TASKS = [
    Task(
        id="code_01",
        category="code_gen",
        prompt=(
            "Write a Python function that finds the longest palindromic substring in a string. "
            "Test it with inputs: 'babad', 'cbbd', 'racecarannakayak'. "
            "Print each input and its longest palindromic substring."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"babad": "bab", "cbbd": "bb", "racecarannakayak": "racecar"},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_02",
        category="code_gen",
        prompt=(
            "Write a Python script that reads 'student_grades.csv' (columns: name, grade) "
            "from the current directory. First create the file with this data:\n"
            "name,grade\nAlice,92\nBob,78\nCharlie,95\nDiana,63\nEve,88\nFrank,71\nGrace,85\n"
            "Then compute: class average, median, and list students below average. "
            "Print results as a formatted table."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"average": 81.71, "median": 85.0},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True, "tolerance": 0.1},
        tools_required=["python_exec", "write_file", "read_file"],
        min_steps=3,
    ),
    Task(
        id="code_03",
        category="code_gen",
        prompt=(
            "Implement a binary search tree in Python with insert, delete, and in-order traversal. "
            "Insert values [5, 3, 7, 1, 4, 6, 8], delete 3, then print the in-order traversal."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=[1, 4, 5, 6, 7, 8],
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_04",
        category="code_gen",
        prompt=(
            "Write a function to solve the 0/1 knapsack problem using dynamic programming. "
            "Test with weights=[2,3,4,5], values=[3,4,5,6], capacity=8. "
            "Print the maximum value and the selected items."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"max_value": 12},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_05",
        category="code_gen",
        prompt=(
            "Create a Python script that generates the first 20 Fibonacci numbers using "
            "matrix exponentiation. Verify the results match the iterative method. "
            "Print both sequences and confirm they match."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer="match",
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_06",
        category="code_gen",
        prompt=(
            "Write a Python function that validates whether a string of parentheses, "
            "brackets, and braces is balanced. Test with these 10 cases:\n"
            "Valid: '()', '()[]{}', '{[()]}', '([{}])', '((()))\n"
            "Invalid: '(]', '([)]', '{[}', '(()', ')('"
            "\nPrint each test case and whether it's valid or invalid."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=[True, True, True, True, True, False, False, False, False, False],
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_07",
        category="code_gen",
        prompt=(
            "Implement Dijkstra's shortest path algorithm in Python. "
            "Use this graph (adjacency list with weights):\n"
            "A: [(B,4), (C,2)]\nB: [(D,3), (E,1)]\nC: [(B,1), (D,5)]\n"
            "D: [(E,2), (F,3)]\nE: [(F,4)]\nF: []\n"
            "Find the shortest path from A to F and print the path and its total weight."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"path": ["A", "C", "B", "E", "D", "F"], "weight": 11},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_08",
        category="code_gen",
        prompt=(
            "Write a Python script that flattens a nested JSON object into dot-notation keys. "
            "Handle arrays by using index notation (e.g., 'items.0.name'). "
            "Test with: {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}, 'f': [1, {'g': 4}]}\n"
            "Print the flattened result."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"a": 1, "b.c": 2, "b.d.e": 3, "f.0": 1, "f.1.g": 4},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_09",
        category="code_gen",
        prompt=(
            "Implement an LRU cache class in Python with get(key) and put(key, value) methods. "
            "Capacity = 3. Run this sequence and print the state after each operation:\n"
            "put(1,'a'), put(2,'b'), put(3,'c'), get(1), put(4,'d'), get(2), put(5,'e'), get(3), get(4), get(5)"
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"get_2": -1, "get_3": -1},  # 2 and 3 evicted
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_10",
        category="code_gen",
        prompt=(
            "Write Python functions to convert Roman numerals to integers and vice versa. "
            "Test with: 1994, 58, 3999, 'MCMXCIV', 'LVIII', 'MMMCMXCIX'. "
            "Print each conversion."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"1994": "MCMXCIV", "58": "LVIII", "3999": "MMMCMXCIX"},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_11",
        category="code_gen",
        prompt=(
            "Write a Python script simulating a bank account system with deposit, withdraw, "
            "and transfer methods. Include overdraft protection (reject if insufficient funds). "
            "Create accounts A(balance=1000) and B(balance=500). Run:\n"
            "1. A deposits 200\n2. B withdraws 600 (should fail)\n"
            "3. A transfers 300 to B\n4. B withdraws 600 (should succeed now)\n"
            "Print balance after each operation."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"A_final": 900, "B_final": 200},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_12",
        category="code_gen",
        prompt=(
            "Implement merge sort in Python that also counts the number of inversions. "
            "An inversion is a pair (i,j) where i < j but arr[i] > arr[j]. "
            "Test with [2,4,1,3,5] and [5,4,3,2,1]. Print sorted arrays and inversion counts."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"inversions_1": 3, "inversions_2": 10},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_13",
        category="code_gen",
        prompt=(
            "Write a Python script that parses and evaluates simple arithmetic expressions "
            "(+, -, *, /, parentheses) WITHOUT using eval(). Implement a recursive descent parser. "
            "Test with: '3+(2*4)-6/(3-1)', '(1+2)*(3+4)', '10-2*3+1'. Print results."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"expr1": 8.0, "expr2": 21.0, "expr3": 5.0},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True, "tolerance": 0.01},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_14",
        category="code_gen",
        prompt=(
            "Implement a trie data structure in Python with insert, search (exact), and "
            "prefix_search (all words with prefix). Insert these words: "
            "'apple', 'app', 'application', 'banana', 'band', 'bandana', 'bat', 'bath', "
            "'can', 'candy', 'cane', 'car', 'card', 'care', 'cart', 'cat', 'catch', 'category', 'cave', 'cell'. "
            "Then: search('app') -> True, search('ap') -> False, prefix_search('ban') -> list. Print all results."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer={"search_app": True, "search_ap": False, "prefix_ban": ["banana", "band", "bandana"]},
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
    Task(
        id="code_15",
        category="code_gen",
        prompt=(
            "Write a Python function that finds all prime factors of a number. "
            "Use trial division for small factors and Pollard's rho for large factors. "
            "Test with: 600851475143. Print the complete prime factorization."
        ),
        system_prompt=SYSTEM_PROMPT,
        expected_answer=[71, 839, 1471, 6857],
        evaluation_type="code_exec",
        evaluation_config={"check_outputs": True},
        tools_required=["python_exec"],
        min_steps=2,
    ),
]
