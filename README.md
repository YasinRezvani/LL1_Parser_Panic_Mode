# LL(1) Parser with Panic Mode Error Recovery

- **Supervisor:** [Dr. Elias Khajeh Karimi](https://shahroodut.ac.ir/en/as/?id=S1163) <br>
- **Teaching Assistants:** Mr. Mohammad Dehghan, Ms. Sara Khoshmaram <br>
- **Course:** Principles of Compiler Design <br>
- **Organization:** [Shahrood University of Technology](https://www.shahroodut.ac.ir/en/) <br>



## Overview
An interactive **LL(1) parser** that visualises the parsing process step by step.  
It supports two built‑in grammars, handles errors using **panic‑mode recovery**, and draws the resulting **parse tree** in real time.  
The entire tool is implemented in Python using **Tkinter** for the graphical interface.



## Features
- **LL(1) table‑driven parsing** – uses pre‑computed parse tables for each grammar.
- **Panic‑mode error recovery** – graceful handling of syntax errors (sync entries, skipping unexpected input, popping mismatched terminals).
- **Real‑time parse tree** – visual tree expansion and colour‑coding (green for matched terminals, blue for non‑terminals).
- **Step history** – navigate forward/backward through every parsing action.
- **Zoom & pan** – mouse wheel zoom and drag to explore large trees.
- **Configurable grammars** – easily add your own grammar by editing the `grammars` dictionary in the code.



## Built‑in Grammars & Inputs
Two grammars are pre‑loaded to demonstrate correct parsing and panic‑mode recovery.

### Grammar 1
```
A → C B | ε
B → c C B | ε
C → E D
D → a E D | ε
E → b | ( A )
```

**Parse Table**

|   | `c`   | `a`     | `b`  | `(`    | `)` | `$` |
|---|-------|---------|------|--------|-----|-----|
| A | –     | –       | C B  | C B    | ε   | ε   |
| B | c C B | –       | –    | –      | ε   | ε   |
| C | sync  | –       | E D  | E D    | sync| sync|
| D | ε     | a E D   | –    | –      | ε   | ε   |
| E | sync  | sync    | b    | ( A )  | sync| sync|

**Example Inputs** (all valid – used to verify correct table entries):
- `(b)ab`
- `bab`
- `(b)aab`
- `bacb`

### Grammar 2 (classic expression grammar)
```
E  → T E'
E' → + T E' | ε
T  → F T'
T' → * F T' | ε
F  → ( E ) | id
```

**Parse Table**

|    | `+`    | `*`    | `(`    | `)` | `id`  | `$`  |
|----|--------|--------|--------|------|-------|------|
| E  | –      | –      | T E'   | sync | T E'  | sync |
| E' | + T E' | –      | –      | ε    | –     | ε    |
| T  | sync   | –      | F T'   | sync | F T'  | sync |
| T' | ε      | * F T' | –      | ε    | –     | ε    |
| F  | sync   | sync   | ( E )  | sync | id    | sync |

**Example Inputs**
- `id + id * id` – valid
- `id * id + id` – valid
- `) id * + id` – **invalid** (starts with `)`; panic‑mode skips the illegal token and continues)
- `id + * id` – **invalid** (missing operand after `+`; panic‑mode pops `*` and recovers)



## Panic‑Mode Error Recovery
When a parsing error is detected, the algorithm uses the following strategies (implemented through the parse table entries):
1. **Skip current input symbol** – if a non‑terminal has no valid entry for the lookahead, the symbol is discarded.
2. **Sync entries** – when the table contains `"Sync"`, the parser pops the non‑terminal (adding `ε` to the tree) until a synchronising terminal is reached.
3. **Popping unexpected terminals** – if a terminal on top of the stack does not match the input, it is removed.

These actions are logged in the **Parsing Steps** table and reflected in the tree (a leaf labelled `ε` may appear for synced non‑terminals).



## Installation & Usage
1. **Requirements:** Python 3 (Tkinter is included in the standard library).
2. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/LL1-Parser-Panic-Mode.git
   cd LL1-Parser-Panic-Mode
   ```
3. **Run the application:**
   ```bash
   python ll1_parser.py
   ```
4. **Using the GUI:**
   - Select a grammar and an input string from the dropdowns.
   - Click **Next ⇒** to perform one parsing step; click **⇐ Back** to undo.
   - The parse tree is drawn on the left pane – zoom with the mouse wheel, pan by dragging.
   - The **Parsing Steps** table shows the stack and input at each step.



## Adding Custom Grammars
You can add your own grammar by extending the `grammars` dictionary in `ll1_parser.py`.  
A grammar entry requires:
- `start` – the start non‑terminal (e.g., `'E'`).
- `parse_table` – a dictionary mapping each non‑terminal to another dictionary where keys are terminals and values are:
  - A list of symbols (production right‑hand side), e.g., `['T', "E'"]`.
  - `[]` for ε‑production.
  - `None` for no entry (triggers input skipping).
  - `"Sync"` for panic‑mode synchronisation.
- `inputs` – a dictionary of named input sequences (each ending with `'$'`).

**Example snippet:**
```python
'My Grammar': {
    'start': 'S',
    'parse_table': {
        'S': {'a': ['A', 'B'], 'b': None, '$': []},
        'A': {'a': ['a'], 'b': 'Sync', '$': 'Sync'},
        'B': {'a': None, 'b': ['b'], '$': []}
    },
    'inputs': {
        'ab': ['a', 'b', '$'],
        'ba': ['b', 'a', '$']
    }
}
```
After adding the entry, restart the application – the new grammar will appear in the dropdown.



## Project Structure
```
LL1-Parser-Panic-Mode/
├── LL(1) Parser.py       # Main application code (Tkinter GUI + parser logic)
├── LL(1) Parser.exe
└── README.md           
```



## Screenshots
<img width="1918" height="1137" alt="Demo" src="https://github.com/user-attachments/assets/0b65c1e7-f793-4110-ac7a-a37532e0c2d8" />


## Acknowledgements
This project was developed as part of the **Principles of Compiler Design** course at Shahrood University of Technology under the supervision of Dr. Elias Khajeh Karimi, with assistance from Mr. Mohammad Dehghan and Ms. Sara Khoshmaram.
