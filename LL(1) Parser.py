import tkinter as tk
from tkinter import ttk

# --------------------------
# Grammar Definitions
# --------------------------
grammars = {
    'Grammar 1': {
        'start': 'A',
        'parse_table': {
            'A': {'c': None, 'a': None, 'b': ['C', 'B'], '(': ['C', 'B'], ')': [], '$': []},
            'B': {'c': ['c', 'C', 'B'], 'a': None, 'b': None, '(': None, ')': [], '$': []},
            'C': {'c': 'Sync', 'a': None, 'b': ['E', 'D'], '(': ['E', 'D'], ')': 'Sync', '$': 'Sync'},
            'D': {'c': [], 'a': ['a', 'E', 'D'], 'b': None, '(': None, ')': [], '$': []},
            'E': {'c': 'Sync', 'a': 'Sync', 'b': ['b'], '(': ['(', 'A', ')'], ')': 'Sync', '$': 'Sync'},
        },
        'inputs': {
            'Input 1: (b)ab': ['(', 'b', ')', 'a', 'b', '$'],
            'Input 2: bab': ['b', 'a', 'b', '$'],
            'Input 3: (b)aab': ['(', 'b', ')', 'a', 'a', 'b', '$'],
            'Input 4: bacb': ['b', 'a', 'c', 'b', '$'],
        }
    },
    'Grammar 2': {
        'start': 'E',
        'parse_table': {
            'E': {'+': None, '*': None, '(': ['T', "E'"], ')': 'Sync', 'id': ['T', "E'"], '$': 'Sync'},
            "E'": {'+': ['+', 'T', "E'"], '*': None, '(': None, ')': [], 'id': None, '$': []},
            'T': {'+': 'Sync', '*': None, '(': ['F', "T'"], ')': 'Sync', 'id': ['F', "T'"], '$': 'Sync'},
            "T'": {'+': [], '*': ['*', 'F', "T'"], '(': None, ')': [], 'id': None, '$': []},
            'F': {'+': 'Sync', '*': 'Sync', '(': ['(', 'E', ')'], ')': 'Sync', 'id': ['id'], '$': 'Sync'},
        },
        'inputs': {
            'Input 1: id + id * id': ['id', '+', 'id', '*', 'id', '$'],
            'Input 2: id * id + id': ['id', '*', 'id', '+', 'id', '$'],
            'Input 3: ) id * + id': [')', 'id', '*', '+', 'id', '$'],
            'Input 4: id + * id': ['id', '+', '*', 'id', '$'],
        }
    }
}


# --------------------------
# Tree Node Definition
# --------------------------
class TreeNode:
    def __init__(self, sym):
        self.sym = sym             # Symbol at this node
        self.children = []         # Child nodes
        self.x = 0                 # x coordinate for drawing
        self.y = 0                 # y coordinate for drawing
        self.matched = False       # Whether this node has been matched
        self.uid = id(self)        # Unique identifier

    def add_children(self, syms):
        """
        Create child nodes for each symbol in 'syms' and attach to self.
        Returns the list of new child nodes.
        """
        new_nodes = []
        for s in syms:
            node = TreeNode(s)
            self.children.append(node)
            new_nodes.append(node)
        return new_nodes


# --------------------------
# Layout Helper Functions
# --------------------------
def count_leaves(node):
    """Count the leaves beneath this node (used for horizontal spacing)."""
    if not node.children:
        node._leaves = 1
    else:
        node._leaves = sum(count_leaves(c) for c in node.children)
    return node._leaves

def assign_x(node, x0, margin=40):
    """
    Recursively assign x-coordinates to each node.
    Leaves get spaced by 'margin'; parents are centered.
    """
    if not node.children:
        node.x = x0 + margin
        return node.x + margin

    cur = x0
    for child in node.children:
        cur = assign_x(child, cur, margin)
    node.x = (node.children[0].x + node.children[-1].x) / 2
    return cur

def assign_y(node, depth=0, level_h=90):
    """Recursively assign y-coordinates based on tree depth."""
    node.y = 20 + depth * level_h
    for child in node.children:
        assign_y(child, depth + 1, level_h)

def layout(root, width):
    """Compute full layout of the parse tree centered in a canvas of given width."""
    count_leaves(root)
    assign_x(root, 0)
    assign_y(root)
    # Center horizontally
    shift = (width / 2) - root.x
    def shift_all(n):
        n.x += shift
        for c in n.children:
            shift_all(c)
    shift_all(root)


# --------------------------
# Serialize / Deserialize
# --------------------------
def serialize(node):
    """Convert a tree to a tuple for history snapshots."""
    return (node.sym, [serialize(c) for c in node.children], node.matched, node.uid)

def deserialize(data):
    """Reconstruct a TreeNode from serialized data."""
    node = TreeNode(data[0])
    node.matched, node.uid = data[2], data[3]
    node.children = [deserialize(c) for c in data[1]]
    return node


# --------------------------
# Tree Traversal Utility
# --------------------------
def find_leftmost(node, sym):
    """
    Find the first unmatched leaf node with symbol 'sym'.
    Returns the node or None if not found.
    """
    if node.sym == sym and not node.children and not node.matched:
        return node
    for c in node.children:
        found = find_leftmost(c, sym)
        if found:
            return found
    return None


# --------------------------
# Main Application Class
# --------------------------
class LL1ParserApp:
    def __init__(self, master):
        self.master = master
        self.history = []      # List of parsing snapshots
        self.hp = -1           # History pointer
        self.accepted = False
        self.scale = 1.0       # Zoom scale
        self.pan_x = 0         # Pan offsets
        self.pan_y = 0
        self._build_ui()
        self._load_grammar('Grammar 1')

    def _build_ui(self):
        """Construct all GUI elements and styles."""
        self.master.title("LL(1) Parser")
        self.master.state('zoomed')

        # Overall container
        main = tk.Frame(self.master, bg="#f5f6fa")
        main.pack(fill='both', expand=True, padx=10, pady=10)

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview.Heading", font=('Segoe UI', 12, 'bold'), padding=5)
        style.configure("Treeview", rowheight=40, font=('Segoe UI', 11), bordercolor="#ccc", relief="flat")
        style.configure("Header.TLabelframe.Label", font=('Segoe UI', 18, 'bold'), foreground="#072336")
        style.configure("Header.TLabelframe", borderwidth=2, relief="solid", background="#f5f6fa")
        style.configure("Accent.TButton", font=('Segoe UI', 11, 'bold'), padding=6,
                        background="#045f9b", foreground="white")
        style.map("Accent.TButton", background=[('active', '#005fa3')])

        # Left pane: parse tree and status
        left = ttk.LabelFrame(main, text="Parse Tree", style="Header.TLabelframe")
        left.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # Canvas for tree
        self.canvas = tk.Canvas(left, bg='white', highlightthickness=1, highlightbackground="#ccc")
        self.canvas.pack(fill='both', expand=True, padx=5, pady=(5, 10))
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<MouseWheel>', self._on_zoom)
        self.canvas.bind('<Double-Button-1>', self._reset_view)

        # Status message
        sf = ttk.LabelFrame(left, text="Status", style="Header.TLabelframe")
        sf.pack(fill='x', padx=5, pady=(0, 5))
        self.msg_label = tk.Label(sf, text="", font=("Segoe UI", 17, 'bold'),
                                  anchor='center', justify='center', wraplength=600,
                                  height=3, bg="#ffffff", fg="#2f3640")
        self.msg_label.pack(fill='both', padx=10, pady=8)

        # Right pane: steps table & controls
        right = tk.Frame(main, bg="#ffffff")
        right.pack(side='right', fill='y', padx=5, pady=5)

        # Parsing Steps table
        tf = ttk.LabelFrame(right, text="Parsing Steps", style="Header.TLabelframe")
        tf.pack(pady=5, fill='both', expand=True)
        cols = ('Stack', 'Input', 'Action')
        self.table = ttk.Treeview(tf, columns=cols, show='headings', selectmode="browse")
        for c in cols:
            width = 120 if c != 'Action' else 360
            self.table.heading(c, text=c)
            self.table.column(c, width=width, stretch=True, anchor='center')
        v_scroll = ttk.Scrollbar(tf, orient='vertical', command=self.table.yview)
        h_scroll = ttk.Scrollbar(tf, orient='horizontal', command=self.table.xview)
        self.table.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')
        self.table.pack(fill='both', expand=True, padx=5, pady=5)

        # Controls (grammar & input selectors, next/back)
        cf = ttk.LabelFrame(right, text="Controls", style="Header.TLabelframe")
        cf.pack(pady=5, fill='x', padx=5)
        grid = tk.Frame(cf, bg="#ffffff")
        grid.pack(fill='x', padx=10, pady=8)

        tk.Label(grid, text="Grammar:", font=("Segoe UI", 12), bg="#ffffff")\
            .grid(row=0, column=0, sticky='w', padx=5, pady=6)
        self.grammar_cb = ttk.Combobox(grid, values=list(grammars.keys()),
                                       state='readonly', font=("Segoe UI", 12), width=30)
        self.grammar_cb['height'] = 10
        self.grammar_cb.grid(row=0, column=1, sticky='ew', padx=5, pady=6)
        self.grammar_cb.current(0)

        tk.Label(grid, text="Input:", font=("Segoe UI", 12), bg="#ffffff")\
            .grid(row=1, column=0, sticky='w', padx=5, pady=6)
        self.input_cb = ttk.Combobox(grid, state='readonly', font=("Segoe UI", 12), width=30)
        self.input_cb['height'] = 10
        self.input_cb.grid(row=1, column=1, sticky='ew', padx=5, pady=6)

        btnf = tk.Frame(grid, bg="#ffffff")
        btnf.grid(row=2, column=0, columnspan=3, pady=10)
        self.btn_back = ttk.Button(btnf, text="⇐ Back", command=self._back,
                                   style="Accent.TButton", width=13)
        self.btn_next = ttk.Button(btnf, text="Next ⇒", command=self._next,
                                   style="Accent.TButton", width=13)
        self.btn_back.pack(side='left', padx=6)
        self.btn_next.pack(side='left', padx=6)
        grid.columnconfigure(1, weight=1)

        # Event bindings
        self.grammar_cb.bind('<<ComboboxSelected>>', self._on_grammar_change)
        self.input_cb.bind('<<ComboboxSelected>>', self._on_input_change)

    # --------------------------
    # Grammar & Input Loading
    # --------------------------
    def _load_grammar(self, name):
        cfg = grammars[name]
        self.parse_table = cfg['parse_table']
        # collect all terminal symbols
        self.terminals = {sym for row in self.parse_table.values() for sym in row}
        self.terminals.add('$')
        self.start = cfg['start']
        inputs = list(cfg['inputs'].keys())
        self.input_cb['values'] = inputs
        self.input_cb.current(0)
        self._reset_parser()

    def _on_grammar_change(self, event):
        self._load_grammar(self.grammar_cb.get())

    def _on_input_change(self, event):
        self._reset_parser()

    # --------------------------
    # Parser State Management
    # --------------------------
    def _reset_parser(self):
        """Initialize stacks, buffers, tree, and UI for a fresh parse."""
        inp = grammars[self.grammar_cb.get()]['inputs'][self.input_cb.get()].copy()
        self.init_input = inp
        self.history.clear()
        self.hp = -1
        self.accepted = False
        self.stack = ['$', self.start]
        self.input_buf = self.init_input.copy()
        self.root = TreeNode(self.start)
        # record initial snapshot
        self._snapshot('Start')
        # clear UI
        self.table.delete(*self.table.get_children())
        self.canvas.delete('all')
        self.msg_label.config(text="Click 'Next' to begin parsing", fg='black')

    def _snapshot(self, action):
        """Save current parser state and action into history."""
        snap = {
            'stack': self.stack.copy(),
            'input': self.input_buf.copy(),
            'tree': serialize(self.root),
            'action': action,
            'accepted': self.accepted
        }
        # truncate future history if stepping backward
        self.history = self.history[:self.hp + 1] + [snap]
        self.hp += 1

    def _restore(self, index):
        """Restore parser state from history[index] and update the UI."""
        snap = self.history[index]
        self.stack = snap['stack'].copy()
        self.input_buf = snap['input'].copy()
        self.root = deserialize(snap['tree'])
        self.accepted = snap['accepted']
        self.scale = 1.0  # reset zoom

        # redraw tree
        self.canvas.delete('all')
        layout(self.root, self.canvas.winfo_width())
        self._draw_node(self.root)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # update table
        self.table.delete(*self.table.get_children())
        for idx, h in enumerate(self.history):
            stack_str = ' '.join(h['stack'][::-1]) if h['action'] != 'ACCEPT' else ''
            input_str = ' '.join(h['input']) if h['action'] != 'ACCEPT' else ''
            self.table.insert('', 'end', values=(stack_str, input_str, h['action']))
        sel = self.table.get_children()[index]
        self.table.selection_set(sel)
        self.table.see(sel)

        # update status message color
        action = snap['action']
        if action.startswith('Error'):
            self.msg_label.config(text=action, fg='red')
        elif action == 'ACCEPT':
            self.msg_label.config(text='Parsing successful.', fg='green')
        else:
            self.msg_label.config(text=action, fg='black')

    # --------------------------
    # Drawing the Tree
    # --------------------------
    def _draw_node(self, node):
        """Recursively draw nodes and edges on the canvas."""
        for child in node.children:
            # draw edge
            self.canvas.create_line(
                node.x * self.scale, node.y * self.scale,
                child.x * self.scale, child.y * self.scale
            )
            self._draw_node(child)

        # node appearance
        fill_color = 'lightgreen' if node.matched and not node.children else '#def'
        self.canvas.create_oval(
            (node.x - 20) * self.scale, (node.y - 20) * self.scale,
            (node.x + 20) * self.scale, (node.y + 20) * self.scale,
            fill=fill_color
        )
        self.canvas.create_text(
            node.x * self.scale, node.y * self.scale,
            text=node.sym, font=('Arial', 16)
        )

    # --------------------------
    # Parsing Step Logic
    # --------------------------
    def _next(self):
        """Advance one parsing action (or step through history)."""
        # if not at end of history, just restore next
        if self.hp < len(self.history) - 1:
            self.hp += 1
            self._restore(self.hp)
            return

        # already accepted
        if self.accepted:
            self.msg_label.config(text='Error: already accepted', fg='red')
            return

        # accept condition
        if self.stack[-1] == '$' and self.input_buf[0] == '$':
            self.accepted = True
            self._snapshot('ACCEPT')
            self._restore(self.hp)
            return

        # pop top of stack
        top = self.stack.pop()
        node = find_leftmost(self.root, top)

        # empty input buffer error
        if not self.input_buf:
            self._snapshot('Error: buffer empty')
            self._restore(self.hp)
            return

        a = self.input_buf[0]

        # 1) Terminal match
        if top == a:
            self.input_buf.pop(0)
            node.matched = True
            self._snapshot(f"match '{a}'")
            self._restore(self.hp)
            return

        # 2) Table lookup
        prod = self.parse_table.get(top, {}).get(a)

        # Panic-mode Case 1: skip input if NT and table entry None
        if prod is None and top not in self.terminals:
            self.stack.append(top)
            skipped = self.input_buf.pop(0)
            self._snapshot(f"Error: skipping input '{skipped}'")
            self._restore(self.hp)
            return

        # Panic-mode Case 2: Sync entry
        if prod == "Sync":
            if top == self.start:
                # do not lose start symbol
                self.stack.append(top)
                skipped = self.input_buf.pop(0)
                self._snapshot(f"Error: skipping input '{skipped}' (sync-start)")
            else:
                # pop NT and show ε-production in tree
                node.add_children(['ε'])
                self._snapshot(f"Error: sync on nonterminal '{top}', {top} → ε (sync-pop)")
            self._restore(self.hp)
            return

        # Panic-mode Case 3: unexpected terminal on stack
        if prod is None and top in self.terminals:
            if top != '$':
                self._snapshot(f"Error: popping unexpected terminal '{top}'")
            else:
                skipped = self.input_buf.pop(0)
                self._snapshot(f"Error: skipping input '{skipped}' (at end-marker)")
            self._restore(self.hp)
            return

        # Epsilon-production
        if prod == []:
            node.add_children(['ε'])
            self._snapshot(f"{top} → ε")
            self._restore(self.hp)
            return

        # Normal expansion
        node.add_children(prod)
        for sym in reversed(prod):
            self.stack.append(sym)
        self._snapshot(f"{top} → {' '.join(prod)}")
        self._restore(self.hp)

    def _back(self):
        """Step backward in history."""
        if self.hp > 0:
            self.hp -= 1
            self._restore(self.hp)

    # --------------------------
    # Mouse Pan/Zoom Handlers
    # --------------------------
    def _reset_view(self, event=None):
        """Reset zoom and pan."""
        self.scale = 1.0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.canvas.scale('all', 0, 0, 1, 1)

    def _on_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_zoom(self, event):
        """Zoom in/out around mouse pointer."""
        factor = 1.001 ** event.delta
        self.scale = max(0.5, min(3.0, self.scale * factor))
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale('all', x, y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))


# --------------------------
# Entry Point
# --------------------------
if __name__ == '__main__':
    root = tk.Tk()
    LL1ParserApp(root)
    root.mainloop()
