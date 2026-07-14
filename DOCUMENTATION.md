# Documentation — T18: ReAct Agent

A short technical walkthrough of the ReAct loop, plus a fully worked example trace.

---

## 1. What is ReAct?

**ReAct** ("Reasoning + Acting") is a prompting pattern where a language model interleaves free-text reasoning with tool use, in a strict repeating format:

```
Thought  → why do I need to act, and what should I do?
Action   → which tool to call
Action Input → what to pass it
Observation  → what the tool returned  (NOT written by the model)
```

The model repeats this cycle — using each `Observation` to inform its next `Thought` — until it's confident enough to stop and write a `Final Answer`. Because every intermediate thought is emitted as plain text, the model's reasoning is directly inspectable, which is the whole point of using ReAct instead of a black-box agent.

This is different from Task 17's **automatic function calling**, where Gemini decides internally when to call a function and the SDK handles the loop for you — fast to build, but the "why" behind each tool call isn't visible in the output.

---

## 2. The loop, step by step (`react_agent.py`)

1. Build a prompt from `prompts/react_prompt.txt`: tool descriptions + the question + the "scratchpad" (everything reasoned so far).
2. Call Gemini with `stop_sequences=["Observation:"]`. This is the key trick — it forces the model to stop the instant it finishes writing `Action Input:`, so it's structurally unable to invent its own observation.
3. Parse the model's output with regex for `Action:` / `Action Input:` / `Final Answer:`.
4. If there's a `Final Answer`, stop and return it.
5. Otherwise, look the action name up in `tools.TOOL_REGISTRY`, call the matching Python function with the action input, and get back an `Observation`.
6. Append `Thought / Action / Action Input / Observation` to the scratchpad and go back to step 1.
7. Give up gracefully after `MAX_ITERATIONS` (default 6) if no final answer is reached.

Every step — including the raw thought, action, input, and observation — is collected into a `trace` list and saved to `traces/` as both Markdown (for humans) and JSON (for programmatic inspection).

---

## 3. Worked example trace

This is the exact output produced (and verified) by running the agent's parsing and tool-dispatch logic against the question:

> "How many IT employees earn more than 90000, and what is 15% of their combined salary?"

```
# Reasoning Trace

**Question:** How many IT employees earn more than 90000, and what is 15% of their combined salary?

**Final Answer:** There are 3 IT employees earning more than 90000 (David Wilson, Grace Lee, James Clark), with a combined salary of 315000. 15% of that combined salary is 47250.

**Steps taken:** 3

---

## Step 1
- **Thought:** I need to find IT employees earning more than 90000.
- **Action:** Database
- **Action Input:** SELECT name, salary FROM employees WHERE department='IT' AND salary > 90000
- **Observation:** name: David Wilson
salary: 125000

name: Grace Lee
salary: 98000

name: James Clark
salary: 92000

## Step 2
- **Thought:** Now I need to sum these salaries and find 15% of the total.
- **Action:** Calculator
- **Action Input:** (125000 + 98000 + 92000) * 0.15
- **Observation:** Calculation Result
Expression : (125000 + 98000 + 92000) * 0.15
Result     : 47250.0

## Step 3
- **Thought:** I now know the final answer.
- **Final Answer:** There are 3 IT employees earning more than 90000 (David Wilson, Grace Lee, James Clark), with a combined salary of 315000. 15% of that combined salary is 47250.
```

Notice how the agent breaks the question into exactly the two sub-tasks it needs (a database lookup, then a calculation) and only calls `Final Answer` once it has both pieces — that hand-off between tools, driven purely by the model's own `Thought` lines, is what ReAct is demonstrating.

---

## 4. Why the stop sequence matters

Without `stop_sequences=["Observation:"]`, a language model asked to produce a Thought/Action/Observation transcript will often just keep writing — including a plausible-looking (but fake) `Observation:` line, followed by a `Final Answer` based on that fabrication. Cutting generation off immediately after `Action Input:` guarantees the observation the model reasons over is always the real tool output, never a guess.

---

## 5. Adding the Weather tool (a worked example of extending the agent)

The Weather tool (`tools/weather.py`) calls the OpenWeatherMap "current weather" endpoint and formats the response. Adding it required exactly three changes, with **no changes to `react_agent.py` or the prompt template**, because both are built dynamically from `TOOL_REGISTRY`:

1. Write `weather(city: str) -> str` in `tools/weather.py`, reading `OPENWEATHER_API_KEY` from the environment.
2. Register it in `tools/__init__.py`:
   ```python
   "Weather": (
       weather,
       "Gets the current real-world weather for a city ... "
       "Input should be a city name, e.g. \"Mumbai\" or \"London,GB\".",
   ),
   ```
3. Add `OPENWEATHER_API_KEY` to `.env.example` and `requests` to `requirements.txt`.

Because `ReActAgent.__init__` builds `tool_names` and `tool_descriptions` straight from `TOOL_REGISTRY`, the model sees the new tool the next time the agent starts — the prompt template's `{tool_descriptions}` / `{tool_names}` placeholders never needed to change.

**Error handling:** the tool distinguishes four failure modes so the agent's `Final Answer` is honest instead of guessing — a missing API key, a city OpenWeatherMap can't find (HTTP 404), a network failure, and an unexpected response shape. Each returns a clear `Weather Error: ...` string as the `Observation`, which the model then has to explain to the user rather than fabricate a temperature.

---

## 6. Known limitations

- Parsing is regex-based against a fixed text format; a model that deviates from the exact `Thought/Action/Action Input` structure will cause that step to be recorded as a parse error rather than retried.
- `MAX_ITERATIONS` is a hard cap — a genuinely complex question that needs more than 6 tool calls will be cut off with an apologetic final message rather than continuing.
- As in Task 17, the Database tool trusts the model to only issue `SELECT` statements; there is no query-level sandboxing beyond the system prompt's instruction.
