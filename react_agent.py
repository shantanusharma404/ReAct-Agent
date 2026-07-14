"""
react_agent.py

A from-scratch implementation of the ReAct pattern
(Reasoning + Acting — Yao et al., 2022) on top of the Gemini API.

Unlike Task 17's automatic function calling, this agent does NOT let the
SDK decide when to call a tool. Instead, the LLM is prompted to produce an
explicit Thought / Action / Action Input trace in plain text; this code
parses that text, executes the matching local tool, feeds the result back
in as an Observation, and repeats — building up a visible chain of
reasoning until the model emits a Final Answer.

Every step of that trace is captured and can be saved to disk, so the
agent's reasoning is fully auditable.
"""

import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import TOOL_REGISTRY

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"
MAX_ITERATIONS = 6

_BASE_DIR = Path(__file__).parent
_PROMPT_PATH = _BASE_DIR / "prompts" / "react_prompt.txt"
_TRACES_DIR = _BASE_DIR / "traces"

# Matches "Action: X" / "Action Input: Y" / "Final Answer: Z" (all on one line)
_ACTION_RE = re.compile(r"Action:\s*(.+)")
_ACTION_INPUT_RE = re.compile(r"Action Input:\s*(.+)")
_FINAL_ANSWER_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)
_THOUGHT_RE = re.compile(r"Thought:\s*(.+)")


class ReActAgent:
    """
    Runs the Thought -> Action -> Action Input -> Observation loop and
    records a structured trace of every step.

        agent = ReActAgent()
        result = agent.run("How many IT employees earn more than 90000, "
                            "and what is 15% of their combined salary?")
        print(result["final_answer"])
        print(result["trace"])       # list of step dicts
    """

    def __init__(self, model: str = MODEL_NAME, max_iterations: int = MAX_ITERATIONS):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Create a .env file with:\n"
                "GEMINI_API_KEY=YOUR_API_KEY"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_iterations = max_iterations
        self.prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

        tool_descriptions = "\n".join(
            f"- {name}: {desc}" for name, (_, desc) in TOOL_REGISTRY.items()
        )
        self.tool_names = ", ".join(TOOL_REGISTRY.keys())
        self.tool_descriptions = tool_descriptions

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self, question: str, save_trace: bool = True) -> dict:
        """
        Executes the ReAct loop for a single question.

        Returns a dict with:
            question, final_answer, trace (list of step dicts), iterations
        """

        scratchpad = ""
        trace = []

        for step_number in range(1, self.max_iterations + 1):

            prompt = self.prompt_template.format(
                tool_descriptions=self.tool_descriptions,
                tool_names=self.tool_names,
                question=question,
                agent_scratchpad=scratchpad,
            )

            model_output = self._call_model(prompt)

            # Stop as soon as the model commits to a final answer.
            final_match = _FINAL_ANSWER_RE.search(model_output)
            thought_match = _THOUGHT_RE.search(model_output)

            if final_match:
                final_answer = final_match.group(1).strip()

                trace.append({
                    "step": step_number,
                    "thought": thought_match.group(1).strip() if thought_match else None,
                    "action": None,
                    "action_input": None,
                    "observation": None,
                    "final_answer": final_answer,
                })

                result = {
                    "question": question,
                    "final_answer": final_answer,
                    "trace": trace,
                    "iterations": step_number,
                }

                if save_trace:
                    self._save_trace(result)

                return result

            action_match = _ACTION_RE.search(model_output)
            action_input_match = _ACTION_INPUT_RE.search(model_output)

            if not action_match or not action_input_match:
                # The model didn't follow the format. Record what we got
                # and stop rather than looping forever on malformed output.
                trace.append({
                    "step": step_number,
                    "thought": thought_match.group(1).strip() if thought_match else None,
                    "action": None,
                    "action_input": None,
                    "observation": None,
                    "final_answer": None,
                    "raw_output": model_output.strip(),
                    "error": "Could not parse Action / Action Input from model output.",
                })
                break

            action = action_match.group(1).strip()
            action_input = action_input_match.group(1).strip()

            observation = self._execute_tool(action, action_input)

            trace.append({
                "step": step_number,
                "thought": thought_match.group(1).strip() if thought_match else None,
                "action": action,
                "action_input": action_input,
                "observation": observation,
                "final_answer": None,
            })

            # Extend the scratchpad so the next call sees the full history.
            scratchpad += (
                f"\nThought: {thought_match.group(1).strip() if thought_match else ''}"
                f"\nAction: {action}"
                f"\nAction Input: {action_input}"
                f"\nObservation: {observation}"
            )

        # Ran out of iterations without a Final Answer.
        result = {
            "question": question,
            "final_answer": (
                "The agent could not reach a final answer within "
                f"{self.max_iterations} reasoning steps."
            ),
            "trace": trace,
            "iterations": self.max_iterations,
        }

        if save_trace:
            self._save_trace(result)

        return result

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _call_model(self, prompt: str) -> str:
        """
        Calls Gemini with a stop sequence at "Observation:" so the model
        can't hallucinate its own tool result — it must stop right after
        proposing an action and let this code fill the observation in.
        """

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                stop_sequences=["Observation:"],
                temperature=0,
            ),
        )

        return response.text or ""

    def _execute_tool(self, action: str, action_input: str) -> str:

        if action not in TOOL_REGISTRY:
            return (
                f"Error: '{action}' is not a valid tool. "
                f"Valid tools are: {self.tool_names}."
            )

        tool_fn, _ = TOOL_REGISTRY[action]

        try:
            return tool_fn(action_input)
        except Exception as exc:
            return f"Error while running {action}: {exc}"

    def _save_trace(self, result: dict) -> Path:

        _TRACES_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_path = _TRACES_DIR / f"trace_{timestamp}.json"
        md_path = _TRACES_DIR / f"trace_{timestamp}.md"

        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        md_path.write_text(self._trace_to_markdown(result), encoding="utf-8")

        return md_path

    @staticmethod
    def _trace_to_markdown(result: dict) -> str:

        lines = [
            f"# Reasoning Trace",
            "",
            f"**Question:** {result['question']}",
            "",
            f"**Final Answer:** {result['final_answer']}",
            "",
            f"**Steps taken:** {result['iterations']}",
            "",
            "---",
            "",
        ]

        for step in result["trace"]:

            lines.append(f"## Step {step['step']}")

            if step.get("thought"):
                lines.append(f"- **Thought:** {step['thought']}")
            if step.get("action"):
                lines.append(f"- **Action:** {step['action']}")
            if step.get("action_input"):
                lines.append(f"- **Action Input:** {step['action_input']}")
            if step.get("observation"):
                lines.append(f"- **Observation:** {step['observation']}")
            if step.get("final_answer"):
                lines.append(f"- **Final Answer:** {step['final_answer']}")
            if step.get("error"):
                lines.append(f"- **Error:** {step['error']}")

            lines.append("")

        return "\n".join(lines)
