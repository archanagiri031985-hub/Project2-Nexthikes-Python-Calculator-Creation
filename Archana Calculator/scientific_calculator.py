import tkinter as tk
from tkinter import messagebox, ttk
import math
import numpy as np
import ast
import json
from urllib.request import urlopen
from urllib.parse import urlencode
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

reset_display = False
history = []
active_window = None


# ==========================================
# ACTIVE WINDOW MANAGEMENT
# ==========================================

def check_active_window():
    global active_window

    if active_window is not None:
        try:
            if active_window.winfo_exists():
                active_window.lift()
                return False
        except tk.TclError:
            pass

        active_window = None

    return True


def register_feature_window(window):
    global active_window
    active_window = window

    def close_window():
        global active_window
        if active_window == window:
            active_window = None
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", close_window)


def close_feature_window(window):
    global active_window
    if active_window == window:
        active_window = None
    window.destroy()


# ==========================================
# 1. SCIENTIFIC CALCULATOR
# ==========================================

def click(event):
    global reset_display

    current = num1_textbox.get()
    button_text = event.widget.cget("text")

    if button_text == "C":
        num1_textbox.delete(0, tk.END)
        num1_textbox.insert(tk.END, "0")
        reset_display = True

    elif button_text == "=":
        try:
            expression = current.replace("%", "/100")

            # Trigonometric functions use the selected angle mode.
            # Degrees are converted to radians before calling Python's math functions.
            angle_mode = angle_mode_var.get()
            to_radians = math.radians if angle_mode == "Degrees" else (lambda value: value)

            functions = {
                "sin": lambda x: math.sin(to_radians(x)),
                "cos": lambda x: math.cos(to_radians(x)),
                "tan": lambda x: math.tan(to_radians(x)),
                "sqrt": math.sqrt,
                "log10": math.log10,
                "log": math.log,
                "pi": math.pi,
                "e": math.e
            }

            result = eval(expression, {"__builtins__": {}}, functions)

            history.append({
                "expression": current,
                "result": str(result)
            })

            num1_textbox.delete(0, tk.END)
            num1_textbox.insert(tk.END, str(result))
            reset_display = True

        except Exception:
            num1_textbox.delete(0, tk.END)
            num1_textbox.insert(tk.END, "Error!")
            reset_display = True

    else:
        if reset_display:
            num1_textbox.delete(0, tk.END)
            current = ""
            reset_display = False

        special_buttons = {
            "sin": "sin(",
            "cos": "cos(",
            "tan": "tan(",
            "sqrt": "sqrt(",
            "log": "log10(",
            "ln": "log(",
            "x²": "**2",
            "xʸ": "**",
            "π": "pi",
            "e": "e"
        }

        value = special_buttons.get(button_text, button_text)
        num1_textbox.insert(tk.END, value)


# ==========================================
# 2. BMR CALCULATOR
# ==========================================

def open_bmr():
    if not check_active_window():
        return

    bmr_window = tk.Toplevel(root)
    bmr_window.title("BMR Calculator")
    bmr_window.geometry("320x380")
    bmr_window.resizable(False, False)
    register_feature_window(bmr_window)

    tk.Label(bmr_window, text="Weight (kg):").pack(pady=(12, 0))
    weight_entry = tk.Entry(bmr_window, font=("Arial", 12))
    weight_entry.pack(pady=5)

    tk.Label(bmr_window, text="Height (cm):").pack()
    height_entry = tk.Entry(bmr_window, font=("Arial", 12))
    height_entry.pack(pady=5)

    tk.Label(bmr_window, text="Age (years):").pack()
    age_entry = tk.Entry(bmr_window, font=("Arial", 12))
    age_entry.pack(pady=5)

    tk.Label(bmr_window, text="Select Gender:").pack(pady=5)
    category = tk.StringVar(value="Female")
    tk.OptionMenu(bmr_window, category, "Female", "Male").pack()

    result_label = tk.Label(
        bmr_window, text="", font=("Arial", 12, "bold"), fg="blue",
        wraplength=280
    )
    result_label.pack(pady=10)

    def calculate_bmr():
        try:
            weight = float(weight_entry.get())
            height = float(height_entry.get())
            age = int(age_entry.get())

            if weight <= 0 or height <= 0 or age <= 0:
                raise ValueError("Please enter positive values.")

            if age < 18:
                messagebox.showinfo(
                    "Age restriction",
                    "This adult BMR equation is intended for adults aged 18 or above.",
                    parent=bmr_window
                )
                return

            if category.get() == "Male":
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

            result_label.config(text=f"Estimated BMR: {bmr:.2f} kcal/day")

        except ValueError as error:
            messagebox.showerror(
                "Invalid Input",
                str(error) if str(error) else "Please enter valid numeric values.",
                parent=bmr_window
            )

    tk.Button(
        bmr_window, text="Calculate BMR", font=("Arial", 12),
        command=calculate_bmr
    ).pack(pady=10)


# ==========================================
# 3. CALCULATION HISTORY
# ==========================================

def show_history():
    if not check_active_window():
        return

    history_window = tk.Toplevel(root)
    history_window.title("Calculation History")
    history_window.geometry("430x350")
    history_window.resizable(False, False)
    register_feature_window(history_window)

    history_listbox = tk.Listbox(
        history_window, font=("Arial", 11), width=48, height=13
    )
    history_listbox.pack(padx=10, pady=10)

    for item in reversed(history):
        history_listbox.insert(
            tk.END, f"{item['expression']} = {item['result']}"
        )

    def use_history(event):
        global reset_display
        selection = history_listbox.curselection()

        if selection:
            selected_item = history_listbox.get(selection[0])
            result = selected_item.split(" = ", 1)[1]
            num1_textbox.delete(0, tk.END)
            num1_textbox.insert(tk.END, result)
            reset_display = True
            close_feature_window(history_window)

    history_listbox.bind("<Double-Button-1>", use_history)

    def clear_history():
        history.clear()
        history_listbox.delete(0, tk.END)
        messagebox.showinfo(
            "History", "Calculation history cleared.",
            parent=history_window
        )

    tk.Button(
        history_window, text="Clear History", font=("Arial", 12),
        command=clear_history
    ).pack(pady=8)


# ==========================================
# 4. GRAPH PLOTTER
# ==========================================

def open_graph():
    if not check_active_window():
        return

    graph_window = tk.Toplevel(root)
    graph_window.title("Graph Plotter")
    graph_window.geometry("390x440")
    graph_window.resizable(False, False)
    register_feature_window(graph_window)

    tk.Label(
        graph_window, text="Enter Function (Example: x**2):",
        font=("Arial", 11)
    ).pack(pady=(10, 2))

    function_entry = tk.Entry(graph_window, font=("Arial", 13), width=30)
    function_entry.insert(0, "x**2")
    function_entry.pack(pady=5)

    range_frame = tk.Frame(graph_window)
    range_frame.pack(pady=8)

    tk.Label(range_frame, text="X Minimum:").grid(row=0, column=0)
    min_entry = tk.Entry(range_frame, width=9)
    min_entry.insert(0, "-10")
    min_entry.grid(row=0, column=1, padx=4)

    tk.Label(range_frame, text="X Maximum:").grid(row=0, column=2)
    max_entry = tk.Entry(range_frame, width=9)
    max_entry.insert(0, "10")
    max_entry.grid(row=0, column=3, padx=4)

    figure = Figure(figsize=(4.2, 2.7), dpi=75)
    axes = figure.add_subplot(111)
    axes.set_title("Mathematical Graph")
    axes.set_xlabel("X Axis")
    axes.set_ylabel("Y Axis")
    axes.grid(True)

    canvas = FigureCanvasTkAgg(figure, master=graph_window)
    canvas.get_tk_widget().pack(
        fill=tk.BOTH, expand=False, padx=5, pady=4
    )

    def evaluate_expression(expression, x):
        expression = expression.replace("^", "**")
        tree = ast.parse(expression, mode="eval")

        allowed_functions = {
            "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "sqrt": np.sqrt, "log": np.log, "log10": np.log10,
            "exp": np.exp, "abs": np.abs
        }

        def calculate(node):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value

            elif isinstance(node, ast.Name):
                if node.id == "x":
                    return x
                if node.id == "pi":
                    return np.pi
                if node.id == "e":
                    return np.e
                raise ValueError("Invalid variable")

            elif isinstance(node, ast.BinOp):
                left = calculate(node.left)
                right = calculate(node.right)

                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
                if isinstance(node.op, ast.Pow):
                    return left ** right
                if isinstance(node.op, ast.Mod):
                    return left % right

            elif isinstance(node, ast.UnaryOp):
                value = calculate(node.operand)
                if isinstance(node.op, ast.USub):
                    return -value
                if isinstance(node.op, ast.UAdd):
                    return value

            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise ValueError("Invalid function")

                name = node.func.id
                if name not in allowed_functions:
                    raise ValueError("Unsupported function")
                if len(node.args) != 1 or node.keywords:
                    raise ValueError("Use one function argument")

                return allowed_functions[name](calculate(node.args[0]))

            raise ValueError("Invalid mathematical expression")

        return calculate(tree.body)

    def plot_graph():
        try:
            expression = function_entry.get().strip()
            if not expression:
                raise ValueError("Please enter a mathematical function.")

            x_min = float(min_entry.get())
            x_max = float(max_entry.get())

            if not math.isfinite(x_min) or not math.isfinite(x_max):
                raise ValueError("Enter finite X-axis values.")
            if x_min >= x_max:
                raise ValueError("Maximum must be greater than minimum.")

            x_values = np.linspace(x_min, x_max, 1000)

            with np.errstate(all="ignore"):
                y_values = evaluate_expression(expression, x_values)

            y_values = np.broadcast_to(
                np.asarray(y_values, dtype=float), x_values.shape
            )
            valid = np.isfinite(y_values)

            if not np.any(valid):
                raise ValueError("No valid graph values in this range.")

            axes.clear()
            axes.plot(
                x_values[valid], y_values[valid],
                label="y = " + expression
            )
            axes.set_title("Graph of y = " + expression)
            axes.set_xlabel("X Axis")
            axes.set_ylabel("Y Axis")
            axes.axhline(0, linewidth=0.8)
            axes.axvline(0, linewidth=0.8)
            axes.grid(True)
            axes.legend()
            figure.tight_layout()
            canvas.draw()

        except Exception as error:
            messagebox.showerror(
                "Graph Error", str(error), parent=graph_window
            )

    tk.Button(
        graph_window, text="Plot Graph", font=("Arial", 12, "bold"),
        bg="#b6f2e9", command=plot_graph
    ).pack(pady=7)


# ==========================================
# 5. UNIT AND CURRENCY CONVERTER
# ==========================================

UNIT_FACTORS = {
    "Length": {
        "Meter": 1.0,
        "Kilometer": 1000.0,
        "Centimeter": 0.01,
        "Millimeter": 0.001,
        "Micrometer": 0.000001,
        "Inch": 0.0254,
        "Foot": 0.3048,
        "Yard": 0.9144,
        "Mile": 1609.344
    },
    "Volume": {
        "Liter": 1.0,
        "Milliliter": 0.001,
        "Cubic meter": 1000.0,
        "Cubic centimeter": 0.001,
        "US gallon": 3.785411784,
        "US quart": 0.946352946,
        "US pint": 0.473176473,
        "US cup": 0.2365882365
    },
    "Weight": {
        "Kilogram": 1.0,
        "Gram": 0.001,
        "Milligram": 0.000001,
        "Metric ton": 1000.0,
        "Pound": 0.45359237,
        "Ounce": 0.028349523125,
        "Stone": 6.35029318
    }
}

CURRENCIES = {
    "INR - Indian Rupee": "INR",
    "USD - US Dollar": "USD",
    "EUR - Euro": "EUR",
    "GBP - British Pound": "GBP",
    "AED - UAE Dirham": "AED",
    "JPY - Japanese Yen": "JPY",
    "CAD - Canadian Dollar": "CAD",
    "AUD - Australian Dollar": "AUD",
    "SGD - Singapore Dollar": "SGD",
    "CHF - Swiss Franc": "CHF",
    "CNY - Chinese Yuan": "CNY",
    "SAR - Saudi Riyal": "SAR"
}


def open_converter():
    if not check_active_window():
        return

    converter_window = tk.Toplevel(root)
    converter_window.title("Unit & Currency Converter")
    converter_window.geometry("440x430")
    converter_window.resizable(False, False)
    register_feature_window(converter_window)

    tk.Label(
        converter_window, text="UNIT & CURRENCY CONVERTER",
        font=("Arial", 15, "bold"), fg="#174c65"
    ).pack(pady=12)

    body = tk.Frame(converter_window)
    body.pack(fill=tk.BOTH, expand=True, padx=18)

    tk.Label(body, text="Conversion category:", font=("Arial", 11)).grid(
        row=0, column=0, sticky="w", pady=7
    )
    category_var = tk.StringVar(value="Length")
    category_box = ttk.Combobox(
        body, textvariable=category_var,
        values=["Length", "Volume", "Weight", "Currency"],
        state="readonly", width=24
    )
    category_box.grid(row=0, column=1, sticky="ew", pady=7)

    tk.Label(body, text="Amount:", font=("Arial", 11)).grid(
        row=1, column=0, sticky="w", pady=7
    )
    amount_entry = tk.Entry(body, font=("Arial", 12), width=27)
    amount_entry.insert(0, "1")
    amount_entry.grid(row=1, column=1, sticky="ew", pady=7)

    tk.Label(body, text="From:", font=("Arial", 11)).grid(
        row=2, column=0, sticky="w", pady=7
    )
    from_var = tk.StringVar()
    from_box = ttk.Combobox(
        body, textvariable=from_var, state="readonly", width=24
    )
    from_box.grid(row=2, column=1, sticky="ew", pady=7)

    tk.Label(body, text="To:", font=("Arial", 11)).grid(
        row=3, column=0, sticky="w", pady=7
    )
    to_var = tk.StringVar()
    to_box = ttk.Combobox(
        body, textvariable=to_var, state="readonly", width=24
    )
    to_box.grid(row=3, column=1, sticky="ew", pady=7)

    result_label = tk.Label(
        body, text="Result will appear here",
        font=("Arial", 13, "bold"), fg="blue",
        wraplength=390, justify="center"
    )
    result_label.grid(row=5, column=0, columnspan=2, pady=18)

    status_label = tk.Label(
        body, text="", font=("Arial", 9), fg="gray",
        wraplength=390, justify="center"
    )
    status_label.grid(row=6, column=0, columnspan=2, pady=2)

    body.columnconfigure(1, weight=1)

    def update_units(event=None):
        category = category_var.get()

        if category == "Currency":
            choices = list(CURRENCIES.keys())
            from_box["values"] = choices
            to_box["values"] = choices
            from_var.set("USD - US Dollar")
            to_var.set("INR - Indian Rupee")
            status_label.config(
                text="Currency conversion retrieves the latest available online rate."
            )
        else:
            choices = list(UNIT_FACTORS[category].keys())
            from_box["values"] = choices
            to_box["values"] = choices

            defaults = {
                "Length": ("Meter", "Kilometer"),
                "Volume": ("Liter", "Milliliter"),
                "Weight": ("Kilogram", "Gram")
            }
            from_var.set(defaults[category][0])
            to_var.set(defaults[category][1])
            status_label.config(text="")

        result_label.config(text="Result will appear here")

    def swap_units():
        old_from = from_var.get()
        old_to = to_var.get()
        from_var.set(old_to)
        to_var.set(old_from)
        result_label.config(text="Result will appear here")

    def convert():
        try:
            amount = float(amount_entry.get())
            if not math.isfinite(amount):
                raise ValueError("Please enter a finite amount.")

            category = category_var.get()
            source = from_var.get()
            target = to_var.get()

            if not source or not target:
                raise ValueError("Please select both units.")

            if category == "Currency":
                from_code = CURRENCIES[source]
                to_code = CURRENCIES[target]

                if from_code == to_code:
                    result = amount
                    rate = 1.0
                else:
                    params = urlencode({
                        "amount": amount,
                        "from": from_code,
                        "to": to_code
                    })
                    url = f"https://api.frankfurter.app/latest?{params}"

                    # The currency rate is fetched online; no API key is required.
                    with urlopen(url, timeout=10) as response:
                        data = json.loads(response.read().decode("utf-8"))

                    rate = data["rates"][to_code] / amount
                    result = data["rates"][to_code]

                result_label.config(
                    text=f"{amount:,.4f} {from_code} = {result:,.4f} {to_code}"
                )
                status_label.config(
                    text=f"Rate used: 1 {from_code} = {rate:,.6f} {to_code} | "
                         "Source: Frankfurter exchange-rate service"
                )

            else:
                factors = UNIT_FACTORS[category]
                result = amount * factors[source] / factors[target]
                result_label.config(
                    text=f"{amount:,.6g} {source} = {result:,.10g} {target}"
                )
                status_label.config(text="")

        except ValueError as error:
            messagebox.showerror(
                "Invalid Input", str(error), parent=converter_window
            )
        except Exception as error:
            messagebox.showerror(
                "Conversion Error",
                "Could not retrieve the currency rate. Check your internet "
                "connection and try again.\n\nDetails: " + str(error),
                parent=converter_window
            )

    category_box.bind("<<ComboboxSelected>>", update_units)

    button_frame = tk.Frame(converter_window)
    button_frame.pack(pady=12)

    tk.Button(
        button_frame, text="Convert", width=12, font=("Arial", 11, "bold"),
        bg="#b6f2e9", command=convert
    ).grid(row=0, column=0, padx=6)

    tk.Button(
        button_frame, text="Swap", width=10, font=("Arial", 11),
        command=swap_units
    ).grid(row=0, column=1, padx=6)

    tk.Button(
        button_frame, text="Close", width=10, font=("Arial", 11),
        command=lambda: close_feature_window(converter_window)
    ).grid(row=0, column=2, padx=6)

    update_units()


# ==========================================
# 6. MAIN CALCULATOR WINDOW
# ==========================================

root = tk.Tk()
root.title("Advance Calculator")
root.geometry("500x570")
root.resizable(False, False)
root.configure(bg="#F0F0F0")

# Angle mode selector for sin(), cos() and tan().
angle_mode_var = tk.StringVar(value="Degrees")

angle_frame = tk.Frame(root, bg="#F0F0F0")
angle_frame.pack(anchor="e", padx=18, pady=(4, 0))

tk.Label(
    angle_frame, text="Angle Mode:",
    font=("Arial", 10, "bold"), bg="#F0F0F0"
).pack(side=tk.LEFT, padx=(0, 6))

angle_mode_menu = tk.OptionMenu(
    angle_frame, angle_mode_var, "Degrees", "Radians"
)
angle_mode_menu.config(font=("Arial", 10), width=9, bg="#b6f2e9")
angle_mode_menu.pack(side=tk.LEFT)

num1_textbox = tk.Entry(
    root, bd=5, font=("Arial", 20), justify="right",
    width=30, bg="#b6f2e9"
)
num1_textbox.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(padx=10, pady=10)

buttons = [
    ["C", "(", ")", "/", "sin", "cos"],
    ["7", "8", "9", "*", "tan", "sqrt"],
    ["4", "5", "6", "-", "log", "ln"],
    ["1", "2", "3", "+", "x²", "xʸ"],
    [".", "0", "%", "=", "π", "e"]
]

for i in range(len(buttons)):
    for j in range(len(buttons[i])):
        btn = tk.Button(
            btn_frame, text=buttons[i][j],
            font=("Arial", 14), width=5, height=2
        )
        btn.grid(row=i, column=j, padx=4, pady=7)
        btn.bind("<Button-1>", click)


# ==========================================
# 7. FEATURE BUTTONS - HORIZONTAL LAYOUT
# ==========================================

feature_frame = tk.Frame(root, bg="#F0F0F0")
feature_frame.pack(pady=12)

feature_buttons = [
    ("BMR", open_bmr),
    ("History", show_history),
    ("Graph", open_graph),
    ("Converter", open_converter)
]

for column, (label, command) in enumerate(feature_buttons):
    tk.Button(
        feature_frame, text=label,
        font=("Arial", 9, "bold"),
        width=9, height=2, bg="#b6f2e9",
        command=command
    ).grid(row=0, column=column, padx=2)


# ==========================================
# 8. START APPLICATION
# ==========================================

root.mainloop()
