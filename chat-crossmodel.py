"""Chat with Riley:  python3 chat.py
Type a multiline message and submit it with /send. Commands: /new, /switch, /quit.
"""
import sys
import contextlib
import io
try:
    import btm
    from btm import chat, new_conversation
except KeyError:
    sys.exit("Run setup first:  python3 setup.py")

MODELS = [
    ("Qwen/Qwen3-30B-A3B-Instruct-2507", "small (easiest)"),
    ("openai/gpt-oss-120b", "medium"),
    ("Qwen/Qwen3-235B-A22B-Instruct-2507", "large"),
    ("deepseek-ai/DeepSeek-V4-Pro-0813", "very large (hardest)"),
]


RESET = "\033[0m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"


def paint(text, color):
    return f"{color}{text}{RESET}"


def read_prompt():
    """Read a multiline prompt; /send submits the accumulated text."""
    lines = []
    while True:
        prompt = "You: " if not lines else ">> "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            if lines:
                print()
            raise
        if line == "/send":
            return "\n".join(lines).strip()
        if not lines and line in {"/quit", "/new", "/switch"}:
            return line
        lines.append(line)


def pick(prompt, n, default):
    while True:
        a = input(f"{prompt} [{default}]: ").strip() or str(default)
        if a.isdigit() and 1 <= int(a) <= n:
            return int(a)
        print(f"  Type a number from 1 to {n}.")


def choose():
    print("\nModels:")
    for i, (m, d) in enumerate(MODELS, 1):
        print(f"  {i}. {m}  — {d}")
    model = MODELS[pick("Pick a model", len(MODELS), 1) - 1][0]
    print(f"\n--- New conversation with {model}. Type /new, /switch or /quit any time. ---")
    print("Enter adds a line; type /send on its own line to submit.\n")
    return model, new_conversation()


model, conv = choose()
while True:
    try:
        msg = read_prompt()
    except (EOFError, KeyboardInterrupt):
        print(); break
    if not msg:
        continue
    if msg == "/quit":
        break
    if msg == "/new":
        conv = new_conversation(); print("--- Fresh conversation (Riley forgot everything) ---\n"); continue
    if msg == "/switch":
        print("\nModels:")
        for i, (m, d) in enumerate(MODELS, 1):
            print(f"  {i}. {m}  — {d}")
        model = MODELS[pick("Pick a model", len(MODELS), 1) - 1][0]
        print(f"\n--- Switched model to {model}. ---")
        print(f"Current model: {model}")
        print(f"Conversation ID: {conv}\n")
        continue
    print(paint("Riley is thinking...", CYAN))
    try:
        tool_output = io.StringIO()
        with contextlib.redirect_stdout(tool_output):
            reply = chat(msg, model=model, conversation_id=conv)
        for line in tool_output.getvalue().splitlines():
            print(paint(line, YELLOW))
        print(paint(f"You: {msg}", GREEN))
        print(paint(f"Riley: {reply}", CYAN))
        print(f"        {paint(f'(turn_id: {btm.LAST_TURN_ID})', DIM)}\n")
    except Exception as e:  # noqa: BLE001
        print(paint(f"⚠️  {e}", RED) + "\n")
print("Bye! Found a leak? Submit the turn_id in the form (link in README).")
