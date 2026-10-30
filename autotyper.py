#!/usr/bin/env python3
"""Simple auto typer + mouse mover for testing activity tracking.

- Types random code, one character at a time, into the focused window.
  cfg.text_type picks what: "css" (cfg.lines_per_round lines of rules per round) or
  "js" (one random long Next.js component per round). After each round it
  clears everything (Ctrl+A, Backspace) and starts again, until you quit.
- Moves the mouse ~1 inch in a random direction every 10 seconds.
- DEL toggles start/pause. It starts PAUSED: focus a text editor, then press DEL.
- Ctrl+C in the terminal quits.

Settings live in `cfg` and are read on every use, so a GUI (autotyper_gui.py)
can change them while it runs. Progress goes through `notify`, which prints
by default; the GUI swaps in its own handler.
"""

import math
import random
import threading
import time
from types import SimpleNamespace

from pynput import keyboard, mouse

cfg = SimpleNamespace(
    text_type="js",            # "css" or "js"
    lines_per_round=800,       # css only; a js round is one whole component
    char_delay=0.3,            # seconds per character
    mouse_every=5.0,           # seconds between mouse moves
    inch_px=96,                # 1 inch at standard 96 DPI; adjust for your screen
    editor_auto_indent=True,   # True for Sublime/VS Code (they indent for you); False only for editors that don't auto-indent
)
stats = SimpleNamespace(round=1, lines=0, chars=0)


def notify(kind, message=""):
    """Progress hook. kind is "state", "round" or "log". The GUI replaces this."""
    if message:
        print(message)

running = threading.Event()  # set = typing/moving, clear = paused
restart = threading.Event()  # set by stop(): abandon the current round on the next resume
started = threading.Event()  # clear = stopped: DEL is ignored until start()
kb = keyboard.Controller()
ms = mouse.Controller()

SELECTORS = ["body", "header", "footer", "main", "nav", "section", "article",
             ".card", ".btn", ".container", ".title", ".grid", "#app", "ul li", "a:hover"]
PROPS = {
    "color": lambda: rand_color(),
    "background-color": lambda: rand_color(),
    "margin": lambda: f"{random.randint(0, 40)}px",
    "padding": lambda: f"{random.randint(0, 32)}px {random.randint(0, 32)}px",
    "font-size": lambda: f"{random.choice([12, 14, 16, 18, 20, 24, 32])}px",
    "font-weight": lambda: random.choice(["400", "500", "600", "700"]),
    "border-radius": lambda: f"{random.randint(0, 16)}px",
    "display": lambda: random.choice(["block", "flex", "grid", "inline-block", "none"]),
    "width": lambda: f"{random.randint(10, 100)}%",
    "line-height": lambda: str(random.choice([1.2, 1.4, 1.5, 1.6, 2])),
    "opacity": lambda: str(round(random.uniform(0.3, 1), 2)),
    "border": lambda: f"{random.randint(1, 3)}px solid {rand_color()}",
}


def rand_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


def css_lines():
    """Yield exactly cfg.lines_per_round lines of random CSS rules."""
    count = 0
    while True:
        rule = [f"{random.choice(SELECTORS)} {{"]
        for prop in random.sample(list(PROPS), random.randint(2, 6)):
            rule.append(f"  {prop}: {PROPS[prop]()};")
        rule += ["}", ""]
        for line in rule:
            if count >= cfg.lines_per_round:
                return
            yield line
            count += 1


COMPONENTS = ["Dashboard", "UserProfile", "ProductList", "OrderHistory", "TeamMembers",
              "Analytics", "Inbox", "ProjectBoard", "Billing", "Inventory"]
ENTITIES = ["user", "product", "order", "project", "invoice", "task", "message", "member"]
WORDS = ["Alpha", "Bravo", "Cedar", "Delta", "Ember", "Falcon", "Granite", "Harbor",
         "Indigo", "Juniper", "Kestrel", "Lumen", "Maple", "Nova", "Orbit", "Pine"]
STATUSES = ["active", "pending", "archived", "draft", "paused"]
CARD_CLASSES = ["rounded-lg border bg-white p-4 shadow-sm", "rounded-xl bg-white p-6 shadow",
                "rounded-md border border-gray-200 p-4", "rounded-2xl bg-slate-50 p-5"]
BUTTON_CLASSES = ["rounded bg-blue-600 px-3 py-1 text-white", "rounded-md bg-gray-900 px-4 py-2 text-sm text-white",
                  "rounded border px-3 py-1 text-sm", "rounded-full bg-emerald-500 px-4 py-1 text-white"]


def js_lines():
    """Return the lines of one random Next.js client component.

    Every line ends in punctuation (never a bare word), so Enter can't accept an
    editor autocomplete suggestion instead of inserting a newline.
    """
    name = random.choice(COMPONENTS)
    entity = random.choice(ENTITIES)
    title = f"{entity.capitalize()}s"
    data = f"INITIAL_{entity.upper()}S"
    card, button = random.choice(CARD_CLASSES), random.choice(BUTTON_CLASSES)
    out = []

    def add(level=0, text=""):
        out.append("  " * level + text if text else "")

    add(0, '"use client";')
    add()
    add(0, 'import { useState, useEffect, useMemo } from "react";')
    add(0, 'import Link from "next/link";')
    add()
    add(0, f"const {data} = [")
    for i in range(random.randint(4, 9)):
        add(1, f'{{ id: {i + 1}, name: "{random.choice(WORDS)} {random.choice(WORDS)}", '
               f'status: "{random.choice(STATUSES)}", amount: {random.randint(10, 999)} }},')
    add(0, "];")
    add()
    add(0, f"export default function {name}() {{")
    add(1, f"const [items, setItems] = useState({data});")
    add(1, 'const [query, setQuery] = useState("");')
    add(1, "const [loading, setLoading] = useState(false);")
    add(1, "const [selected, setSelected] = useState(null);")
    add(1, "const [page, setPage] = useState(1);")
    add(1, 'const [sortBy, setSortBy] = useState("name");')
    add()

    if random.random() < 0.8:
        add(1, "useEffect(() => {")
        add(2, "async function load() {")
        add(3, "setLoading(true);")
        add(3, f'const res = await fetch("/api/{entity}s?page=" + page);')
        add(3, "const data = await res.json();")
        add(3, "setItems(data);")
        add(3, "setLoading(false);")
        add(2, "}")
        add(2, "load();")
        add(1, "}, [page]);")
        add()

    add(1, "const filtered = useMemo(() => {")
    add(2, "const q = query.toLowerCase();")
    add(2, "const result = items.filter((item) => item.name.toLowerCase().includes(q));")
    add(2, "return [...result].sort((a, b) => (a[sortBy] > b[sortBy] ? 1 : -1));")
    add(1, "}, [items, query, sortBy]);")
    add()
    add(1, "const total = useMemo(() => filtered.reduce((sum, item) => sum + item.amount, 0), [filtered]);")
    add()

    handlers = [
        ["function handleDelete(id) {",
         "  setItems((prev) => prev.filter((item) => item.id !== id));",
         "  if (selected?.id === id) setSelected(null);", "}"],
        ["function handleArchive(id) {",
         '  setItems((prev) => prev.map((item) => (item.id === id ? { ...item, status: "archived" } : item)));', "}"],
        ["function handleSelect(item) {",
         "  setSelected((current) => (current?.id === item.id ? null : item));", "}"],
        ["function handleAdd() {",
         "  const id = Math.max(0, ...items.map((item) => item.id)) + 1;",
         f'  setItems((prev) => [...prev, {{ id, name: "New {entity} " + id, status: "draft", amount: 0 }}]);', "}"],
        ["async function handleSave(item) {",
         f'  await fetch("/api/{entity}s/" + item.id, {{',
         '    method: "PUT",',
         '    headers: { "Content-Type": "application/json" },',
         "    body: JSON.stringify(item),",
         "  });", "}"],
    ]
    for handler in random.sample(handlers, random.randint(3, len(handlers))):
        for line in handler:
            add(1, line)
        add()

    add(1, "return (")
    add(2, '<main className="mx-auto max-w-5xl space-y-6 p-8">')
    add(3, '<header className="flex items-center justify-between">')
    add(4, f'<h1 className="text-2xl font-bold">{title}</h1>')
    add(4, f'<Link href="/{entity}s/new" className="{button}">New {entity}</Link>')
    add(3, "</header>")
    add()
    add(3, '<div className="flex gap-3">')
    add(4, f'<input value={{query}} onChange={{(e) => setQuery(e.target.value)}} placeholder="Search {entity}s..." className="flex-1 rounded border px-3 py-2" />')
    add(4, '<select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="rounded border px-2">')
    add(5, '<option value="name">Name</option>')
    add(5, '<option value="amount">Amount</option>')
    add(5, '<option value="status">Status</option>')
    add(4, "</select>")
    add(3, "</div>")
    add()

    if random.random() < 0.7:
        add(3, '<section className="grid grid-cols-3 gap-4">')
        for label, expr in random.sample([("Total", "items.length"), ("Showing", "filtered.length"),
                                          ("Amount", "total"), ("Page", "page")], 3):
            add(4, f'<div className="{card}">')
            add(5, f'<p className="text-sm text-gray-500">{label}</p>')
            add(5, f'<p className="text-xl font-semibold">{{{expr}}}</p>')
            add(4, "</div>")
        add(3, "</section>")
        add()

    add(3, '{loading && <p className="text-gray-500">Loading...</p>}')
    add()
    add(3, '<ul className="space-y-2">')
    add(4, "{filtered.map((item) => (")
    add(5, f'<li key={{item.id}} className="{card} flex items-center justify-between">')
    add(6, '<button onClick={() => setSelected(item)} className="text-left">')
    add(7, '<span className="font-medium">{item.name}</span>')
    add(7, '<span className="ml-2 text-xs text-gray-400">{item.status}</span>')
    add(6, "</button>")
    add(6, '<span className="text-sm">${item.amount}</span>')
    add(5, "</li>")
    add(4, "))}")
    add(3, "</ul>")
    add()

    if random.random() < 0.7:
        add(3, "{selected && (")
        add(4, '<aside className="fixed inset-y-0 right-0 w-80 bg-white p-6 shadow-xl">')
        add(5, '<h2 className="text-lg font-semibold">{selected.name}</h2>')
        add(5, '<p className="mt-2 text-sm text-gray-500">Status: {selected.status}</p>')
        add(5, '<p className="text-sm text-gray-500">Amount: ${selected.amount}</p>')
        add(5, f'<button onClick={{() => setSelected(null)}} className="{button} mt-4">Close</button>')
        add(4, "</aside>")
        add(3, ")}")
        add()

    add(3, '<footer className="flex justify-between">')
    add(4, f'<button disabled={{page === 1}} onClick={{() => setPage((p) => p - 1)}} className="{button}">Previous</button>')
    add(4, f'<button onClick={{() => setPage((p) => p + 1)}} className="{button}">Next</button>')
    add(3, "</footer>")
    add(2, "</main>")
    add(1, ");")
    add(0, "}")
    return out


GENERATORS = {"css": css_lines, "js": js_lines}


def wait_running():
    running.wait()


def clear_all():
    with kb.pressed(keyboard.Key.ctrl):
        kb.tap("a")
    time.sleep(0.2)
    kb.tap(keyboard.Key.backspace)


def press_enter():
    # select any closers the editor auto-inserted after the cursor
    # (e.g. "}" or "))}"), so Enter replaces them
    with kb.pressed(keyboard.Key.shift):
        kb.tap(keyboard.Key.end)
    kb.tap(keyboard.Key.enter)


def reset_stats():
    stats.round, stats.lines, stats.chars = 1, 0, 0


def type_loop():
    while True:
        restart.clear()
        count = typed = 0
        text_type = cfg.text_type  # a change takes effect from the next round
        for line in GENERATORS[text_type]():
            if cfg.editor_auto_indent:
                line = line.lstrip()
            for ch in line + "\n":
                wait_running()
                if restart.is_set():
                    break
                if ch == "\n":
                    press_enter()
                else:
                    kb.type(ch)
                stats.chars += 1
                typed += 1
                time.sleep(cfg.char_delay)
            if restart.is_set():
                break
            count += 1
            stats.lines += 1
        if not restart.is_set():
            wait_running()
        if restart.is_set():
            # stopped mid-round: drop the rest, start fresh on a new line
            # (only once resumed, so the Enter lands in the editor, not the GUI)
            wait_running()
            reset_stats()
            if typed:
                press_enter()
            continue
        clear_all()
        notify("round", f"Round {stats.round} done: {count} lines of {text_type} typed, cleared")
        stats.round += 1
        time.sleep(cfg.char_delay)


def mouse_loop():
    while True:
        time.sleep(cfg.mouse_every)
        wait_running()
        angle = random.uniform(0, 2 * math.pi)
        ms.move(round(cfg.inch_px * math.cos(angle)), round(cfg.inch_px * math.sin(angle)))


def set_running(on):
    if on:
        running.set()
        notify("state", "Running (press DEL to pause)")
    else:
        running.clear()
        notify("state", "Paused (press DEL to resume)")


def start():
    """Turn the typer on, paused. DEL then starts/pauses typing."""
    started.set()
    notify("state", "Started: focus your editor and press DEL to type")


def stop():
    """Turn the typer off: stop typing, ignore DEL, drop the round, reset the stats.

    Doesn't clear the editor: whatever has focus when Stop is clicked (the GUI
    itself) would get the Ctrl+A/Backspace. The next start begins a fresh round.
    """
    started.clear()
    running.clear()
    restart.set()
    reset_stats()
    notify("state", "Stopped: DEL does nothing until you press Start")


def on_press(key):
    if key == keyboard.Key.delete and started.is_set():
        set_running(not running.is_set())


def start_workers():
    """Start the DEL listener and the typing/mouse threads (stopped until start()). Returns the typer thread."""
    if cfg.text_type not in GENERATORS:
        raise SystemExit(f"text_type must be one of {list(GENERATORS)}, got {cfg.text_type!r}")
    keyboard.Listener(on_press=on_press, daemon=True).start()
    threading.Thread(target=mouse_loop, daemon=True).start()
    typer = threading.Thread(target=type_loop, daemon=True)
    typer.start()
    return typer


def main():
    print("Ready. Focus a text editor and press DEL to start/pause. Ctrl+C to quit.")
    typer = start_workers()
    started.set()
    try:
        while typer.is_alive():
            typer.join(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
