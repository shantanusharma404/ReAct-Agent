# T18 – ReAct Agent 🔁🧠

A from-scratch implementation of the **ReAct pattern** (Reasoning + Acting, [Yao et al., 2022](https://arxiv.org/abs/2210.03629)) built on the Google Gemini API — no LangChain, no agent framework, just an explicit prompt loop you can read line by line.

> Part of the **Month 2 – Week 7: Agents & Tool Use** internship deliverables. Follows on from [Task 17 (Function Calling Deep Dive)](../T17_Function_Calling_Deep_Dive).

---

## What makes this different from Task 17?

Task 17 used **automatic function calling** — the Gemini SDK silently decided when to call a tool and looped internally. That's convenient, but it hides *how* the model reasons.

This project does the opposite: the LLM is prompted to think out loud in a strict text format —

```
Thought: ...
Action: ...
Action Input: ...
Observation: ...
```

— and the Python code parses that text itself, runs the matching tool, and feeds the result back in as the next `Observation`. The reasoning is never hidden; it's the actual output.

---

## How it works

```
Question
   │
   ▼
┌─────────────────────────────┐
│  Thought: what do I need?    │
│  Action: pick a tool          │──► Python executes the tool
│  Action Input: tool arguments │
└─────────────────────────────┘
              │
              ▼
        Observation
   (fed back into the prompt)
              │
              ▼
     repeat until the model
     writes "Final Answer:"
```

The loop stops the model right after `Action Input:` using a **stop sequence** (`"Observation:"`), so it can never fabricate a tool result — the observation always comes from the real tool.

---

## Tools available to the agent

Reused from Task 17:

- **Calculator** — safely evaluates math expressions via Python's `ast` module
- **Search** — keyword search over a local knowledge base (`data/documents.txt`)
- **Database** — runs SQL `SELECT` queries against a local SQLite `employees` table

New in this update:

- **Weather** — real-world current weather for a city via the [OpenWeatherMap](https://openweathermap.org/api) API (temperature, condition, humidity, wind speed)

---

## Project Structure

```
T18_ReAct_Agent/
│
├── .env.example
├── .gitignore
├── app.py               # CLI entry point / chat loop
├── react_agent.py        # The ReAct loop itself
├── create_db.py           # Builds the sample SQLite database
├── requirements.txt
├── README.md
├── DOCUMENTATION.md       # Deep dive + sample reasoning trace
│
├── data/
│   └── documents.txt        # Local knowledge base for the Search tool
│
├── tools/
│   ├── __init__.py           # TOOL_REGISTRY (name -> function + description)
│   ├── calculator.py
│   ├── search.py
│   ├── database.py
│   └── weather.py
│
├── prompts/
│   └── react_prompt.txt      # The ReAct instruction template
│
└── traces/                   # Every run is saved here as .md + .json
```

---

## Quick Start

```bash
git clone <your-repo-url>
cd T18_ReAct_Agent
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env          # then add GEMINI_API_KEY and OPENWEATHER_API_KEY

python create_db.py
python app.py
```

Ask something that needs more than one tool, e.g.:

> "How many IT employees earn more than 90000, and what is 15% of their combined salary?"

> "What's the weather in Mumbai, and is it warmer than 25°C?"

The agent will query the database, do the math, and print a final answer — and a full trace of how it got there is saved automatically to `traces/`.

---

## Reasoning Traces

Every call to `agent.run()` is logged as both:

- `traces/trace_<timestamp>.md` — human-readable Thought/Action/Observation steps
- `traces/trace_<timestamp>.json` — the same data, structured, for programmatic analysis

See **[DOCUMENTATION.md](DOCUMENTATION.md)** for a full worked example trace and an explanation of every field.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| LLM | Google Gemini API |
| SDK | `google-genai` |
| Pattern | ReAct (Reasoning + Acting), implemented manually |
| Database | SQLite |
| Config | `python-dotenv` |

---

## Status

🟢 Core ReAct loop implemented and verified against scripted model responses (parsing, tool dispatch, scratchpad accumulation, and trace saving all confirmed working). Pending: a broader set of live test questions once run against the real API.

---

## Author

**Shantanu Sharma**
B.Tech Computer Science & Design · AI Engineering Internship · Month 2 – Week 7 · Task 18
