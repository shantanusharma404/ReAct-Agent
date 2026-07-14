"""
app.py

Main entry point for the ReAct Agent.
"""

from react_agent import ReActAgent


def main():

    print("=" * 60)
    print("        REACT AGENT — MULTI-STEP REASONING")
    print("=" * 60)
    print("Type 'exit' to quit.\n")

    agent = ReActAgent()

    while True:

        question = input("You: ").strip()

        if question.lower() == "exit":
            print("\nGoodbye.")
            break

        if not question:
            continue

        try:
            result = agent.run(question)

            print("\nAssistant:")
            print(result["final_answer"])
            print(f"\n(Reasoning trace saved — {result['iterations']} step(s) taken)")

        except Exception as e:
            print(f"\nError: {e}")

        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
