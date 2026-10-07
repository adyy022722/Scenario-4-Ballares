"""
app.py - Campus Snack Bar POS (Scenario 4)
Run with:  python app.py

Screen layout:
  [Sidebar] [Greeting, banner, Menu (food cards)] [Order Menu: cart, total, payment]
  Payment confirmation and receipt appear as pop-up panels over a see-through
  "glass" backdrop.

Design rules used throughout:
  Corner radius - cards 12px, banner/boxes 10px, buttons and input 8px
  Pink is kept for actions (Add, Pay Now) and key information; navy for
  the logo, headings, active navigation and the banner.
"""
import math
import os
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

import database
from logic import Cart, peso, validate_payment, compute_change

# ---------- Color palette ----------
NAVY = "#1e3268"          # logo, headings, active navigation, banner
NAVY_LIGHT = "#2a4180"    # decorative circles on the banner
NAVY_SOFT = "#c9d3ee"     # light text on navy
TEXT = "#172033"          # dark text
MUTED = "#64748b"         # secondary text (slate)
PINK = "#f36f8a"          # actions and important information
PINK_HOVER = "#e85f7b"    # pink on hover
PINK_SOFT = "#fff1f4"     # light pink backgrounds
PINK_LINE = "#f7c2ce"     # pink outline (hover / focus)
PAGE_BG = "#fffcfc"       # main background
WHITE = "#ffffff"
CARD_BORDER = "#f0e5e8"   # subtle card borders and dividers
INPUT_BORDER = "#e6d6db"  # cash input border (normal)
SHADOW = "#f1e8eb"        # soft card shadow
SHADOW_HOVER = "#e9dce1"  # slightly deeper shadow on hover
BTN_SHADOW = "#f9cfd8"    # soft pink shadow under Pay Now on hover
SUCCESS = "#2f855a"
SUCCESS_BG = "#e8f5ee"
ERROR = "#d6455f"
ERROR_BG = "#fff1f4"
OVERLAY_BG = "#fff1f4"    # "glass" color behind pop-up panels
GLASS_ALPHA = 0.55        # glass opacity: 0 = invisible, 1 = solid
KEY_COLOR = "#ff00fe"     # made transparent so pop-up panels get rounded corners
FONT = "Segoe UI"

# Corner radius rules
R_CARD, R_BOX, R_BUTTON = 12, 10, 8

# Product name -> image file (images/ folder, already sized for the app)
IMAGE_KEYS = {
    "Classic Burger": "classic_burger",
    "Cheeseburger": "cheeseburger",
    "Ham Sandwich": "ham_sandwich",
    "French Fries (Regular)": "french_fries",
    "Nachos": "nachos",
    "Soda (Can)": "soda",
}
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


# ======================================================================
# Small drawing helpers (Tkinter has no rounded corners, so we draw them)
# ======================================================================
def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a canvas (a smoothed polygon)."""
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kw)


class RoundButton(tk.Canvas):
    """
    A rounded button drawn on a canvas.
    style: 'primary' (pink, for Pay Now and main actions), 'outline',
           'soft' (light pink, for the + add buttons), 'qty' (small - / +),
           'nav' (navy active navigation item)
    """
    STYLES = {
        "primary": dict(fill=PINK, hover=PINK_HOVER, fg=WHITE, hover_fg=WHITE, border=""),
        "outline": dict(fill=WHITE, hover=PINK_SOFT, fg=NAVY, hover_fg=NAVY, border=INPUT_BORDER),
        "soft": dict(fill=PINK_SOFT, hover=PINK, fg=PINK, hover_fg=WHITE, border=""),
        "qty": dict(fill=PINK_SOFT, hover="#ffe1e8", fg=NAVY, hover_fg=NAVY, border=""),
        "nav": dict(fill=NAVY, hover=NAVY, fg=WHITE, hover_fg=WHITE, border=""),
    }

    def __init__(self, parent, text, command=None, style="primary", width=None, height=40,
                 radius=R_BUTTON, font=(FONT, 10, "bold"), anchor="center", bg=None):
        self.style = self.STYLES[style]
        self.lift_effect = style == "primary"          # shadow + subtle grow on hover
        self.extra = 3 if self.lift_effect else 0       # room for the shadow
        if width is None:
            width = tkfont.Font(font=font).measure(text) + 36
        super().__init__(parent, width=width, height=height + self.extra,
                         bg=bg or parent["bg"], highlightthickness=0, bd=0,
                         cursor="hand2" if command else "arrow")
        self.text, self.command, self.radius = text, command, radius
        self.font, self.anchor = font, anchor
        self.hovering = self.pressed = self.disabled = False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<ButtonPress-1>", lambda e: self._press(True))
        self.bind("<ButtonRelease-1>", self._release)

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height() - self.extra
        if w < 4:
            return
        s = self.style
        active = self.hovering and not self.disabled and self.command
        fill = s["hover"] if active else s["fill"]
        fg = s["hover_fg"] if active else s["fg"]
        grow = 1 if (active and self.lift_effect and not self.pressed) else 0
        if active and self.lift_effect:
            rounded_rect(self, 2, 3, w - 3, h + 2, self.radius, fill=BTN_SHADOW, outline="")
        rounded_rect(self, 1 - grow, 1 - grow, w - 2 + grow, h - 2 + grow, self.radius,
                     fill=fill, outline=s["border"] or fill)
        if self.anchor == "w":
            self.create_text(16, h / 2, text=self.text, fill=fg, font=self.font, anchor="w")
        else:
            self.create_text(w / 2, h / 2, text=self.text, fill=fg, font=self.font)

    def _hover(self, on):
        self.hovering = on
        if not on:
            self.pressed = False
        self.draw()

    def _press(self, on):
        self.pressed = on
        self.draw()

    def _release(self, event):
        was_pressed = self.pressed
        self._press(False)
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        if was_pressed and inside:
            self.invoke()

    def invoke(self):
        if self.command and not self.disabled:
            self.command()

    def set_text(self, text):
        self.text = text
        self.draw()


class RoundedPanel(tk.Canvas):
    """
    A rounded box with an optional border and soft shadow.
    Put widgets inside panel.inner. With stretch=True the panel fills the
    width it is given (pack fill="x" / grid sticky="ew").
    """

    def __init__(self, parent, fill=WHITE, radius=R_CARD, border="", shadow=False,
                 pad=16, stretch=False, bg=None):
        self.shadow = 4 if shadow else 0
        super().__init__(parent, bg=bg or parent["bg"], highlightthickness=0, bd=0)
        self.fill, self.radius, self.border, self.pad, self.stretch = fill, radius, border, pad, stretch
        self.inner = tk.Frame(self, bg=fill)
        self.window = self.create_window(pad, pad, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._fit)
        self.bind("<Configure>", lambda e: self.draw())

    def _fit(self, _=None):
        iw, ih = self.inner.winfo_reqwidth(), self.inner.winfo_reqheight()
        self.config(height=ih + 2 * self.pad + self.shadow)
        if not self.stretch:
            self.config(width=iw + 2 * self.pad)

    def set_border(self, color):
        self.border = color
        self.draw()

    def draw(self):
        self.delete("box")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        bottom = h - 1 - self.shadow
        if self.shadow:
            rounded_rect(self, 1, 4, w - 2, h - 1, self.radius, fill=SHADOW, outline="", tags="box")
        rounded_rect(self, 0, 0, w - 1, bottom, self.radius, fill=self.fill,
                     outline=self.border or self.fill, tags="box")
        self.tag_lower("box")
        if self.stretch:
            self.itemconfig(self.window, width=max(w - 2 * self.pad, 1))


# ======================================================================
# The application
# ======================================================================
class SnackBarPOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Campus Snack Bar POS")
        self.geometry("1366x740")
        self.minsize(1280, 700)
        self.configure(bg=PAGE_BG)
        try:
            self.state("zoomed")        # start maximized on Windows
        except tk.TclError:
            pass

        database.init_db()
        self.products = database.get_products()   # [(id, name, price), ...]
        self.cart = Cart()
        self.paid = False            # True after a successful payment (cart is locked)
        self.last_receipt = None     # data of the last receipt, to show it again
        self.toast_job = None
        self.overlay = None          # the glass backdrop of the open pop-up panel (if any)
        self.overlay_card = None     # the pop-up panel window itself
        self.overlay_bind = None
        self.images = {}             # keeps PhotoImage objects alive
        self.load_images()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.build_sidebar()
        self.build_center()
        self.build_order_panel()
        self.refresh_cart()

    # ---------- images ----------
    def load_images(self):
        """Load product photos. If a file is missing, the app still works (no photo)."""
        names = list(IMAGE_KEYS.values())
        files = names + [n + "_thumb" for n in names] + ["banner_burger"]
        for name in files:
            try:
                self.images[name] = tk.PhotoImage(file=os.path.join(IMAGE_DIR, name + ".png"))
            except tk.TclError:
                self.images[name] = None

    def product_image(self, name, thumb=False):
        key = IMAGE_KEYS.get(name)
        return self.images.get(key + ("_thumb" if thumb else "")) if key else None

    # ---------- sidebar ----------
    def build_sidebar(self):
        side = tk.Frame(self, bg=WHITE, width=220)
        side.grid(row=0, column=0, sticky="ns")
        side.pack_propagate(False)

        brand = tk.Frame(side, bg=WHITE)
        brand.pack(anchor="w", padx=26, pady=(30, 34))
        tk.Label(brand, text="SnackBar", bg=WHITE, fg=NAVY,
                 font=(FONT, 20, "bold")).pack(side="left")
        tk.Label(brand, text=".", bg=WHITE, fg=PINK,
                 font=(FONT, 20, "bold")).pack(side="left")

        RoundButton(side, "\U0001F354   Menu", style="nav", height=42, anchor="w",
                    font=(FONT, 11, "bold")).pack(fill="x", padx=20)
        RoundButton(side, "+   New Transaction", self.new_transaction, style="outline",
                    height=42, anchor="w", font=(FONT, 10, "bold")).pack(fill="x", padx=20, pady=(10, 0))

        tip = RoundedPanel(side, fill=PINK_SOFT, radius=R_BOX, pad=16, stretch=True)
        tip.pack(side="bottom", fill="x", padx=20, pady=26)
        tk.Label(tip.inner, text="Campus Snack Bar", bg=PINK_SOFT, fg=NAVY, anchor="w",
                 font=(FONT, 11, "bold")).pack(fill="x", pady=(0, 4))
        tk.Label(tip.inner, text="Use − and + in the Order Menu to change quantities.",
                 bg=PINK_SOFT, fg=MUTED, anchor="w", justify="left", wraplength=148,
                 font=(FONT, 9)).pack(fill="x")

    # ---------- center: greeting, banner, food cards ----------
    def build_center(self):
        center = tk.Frame(self, bg=PAGE_BG)
        center.grid(row=0, column=1, sticky="nsew", padx=28, pady=(20, 16))

        top = tk.Frame(center, bg=PAGE_BG)
        top.pack(fill="x")
        greet = tk.Frame(top, bg=PAGE_BG)
        greet.pack(side="left")
        hour = datetime.now().hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        tk.Label(greet, text=f"Good {part}, Cashier", bg=PAGE_BG, fg=NAVY,
                 font=(FONT, 18, "bold")).pack(anchor="w")
        tk.Label(greet, text=datetime.now().strftime("%A, %B %d, %Y"), bg=PAGE_BG, fg=MUTED,
                 font=(FONT, 10)).pack(anchor="w")
        # Toast: short feedback message for actions (item added, errors, etc.)
        self.toast = tk.Canvas(top, bg=PAGE_BG, height=36, width=10, highlightthickness=0)
        self.toast.pack(side="right")
        self.toast_text = ""

        self.build_banner(center)

        title = tk.Frame(center, bg=PAGE_BG)
        title.pack(fill="x", pady=(18, 10))
        tk.Label(title, text="Menu", bg=PAGE_BG, fg=NAVY,
                 font=(FONT, 15, "bold")).pack(side="left")
        tk.Label(title, text=f"{len(self.products)} items", bg=PAGE_BG, fg=MUTED,
                 font=(FONT, 10)).pack(side="left", padx=10, pady=(4, 0))

        grid = tk.Frame(center, bg=PAGE_BG)
        grid.pack(anchor="w")
        for i, (pid, name, price) in enumerate(self.products):
            card = self.product_card(grid, pid, name, price)
            card.grid(row=i // 3, column=i % 3, padx=(0, 14), pady=(0, 10))

    def build_banner(self, parent):
        """Navy banner; the text is the main focus, the burger floats gently."""
        banner = tk.Canvas(parent, bg=PAGE_BG, height=118, highlightthickness=0)
        banner.pack(fill="x", pady=(14, 0))
        self.banner = banner

        def draw(_=None):
            banner.delete("all")
            w = banner.winfo_width()
            rounded_rect(banner, 0, 0, w - 1, 117, R_BOX, fill=NAVY, outline=NAVY)
            banner.create_oval(w - 166, 3, w - 54, 115, fill=NAVY_LIGHT, outline="")   # soft halo
            banner.create_text(30, 44, text="Fresh & Hot Snacks", fill=WHITE, anchor="w",
                               font=(FONT, 21, "bold"))
            banner.create_text(30, 76, anchor="w", fill=NAVY_SOFT, font=(FONT, 10),
                               text="Burgers, sandwiches, fries and more — made fresh at the counter.")
            if self.images.get("banner_burger"):
                banner.create_image(w - 110, 59, image=self.images["banner_burger"], tags="burger")

        banner.bind("<Configure>", draw)
        self.float_burger()

    def float_burger(self, step=0):
        """Move the banner burger up and down by about 3px (one cycle every 3 seconds)."""
        if not self.banner.winfo_exists():
            return
        items = self.banner.find_withtag("burger")
        if items:
            x = self.banner.winfo_width() - 110
            self.banner.coords(items[0], x, 59 + 3 * math.sin(step * 2 * math.pi / 50))
        self.after(60, self.float_burger, step + 1)

    def product_card(self, parent, pid, name, price):
        """Food card: large photo on top; name, price and + button below."""
        W, IMG_H, H, SH = 218, 128, 194, 4
        card = tk.Canvas(parent, width=W, height=H + SH, bg=PAGE_BG,
                         highlightthickness=0, cursor="hand2")
        shadow = rounded_rect(card, 1, SH, W - 2, H + SH - 1, R_CARD, fill=SHADOW, outline="")
        rounded_rect(card, 0, 0, W - 1, H - 1, R_CARD, fill=WHITE, outline="")
        img = self.product_image(name)
        if img:
            card.create_image(0, 0, image=img, anchor="nw")
        else:
            card.create_text(W / 2, IMG_H / 2, text="\U0001F37D", font=(FONT, 28), fill=PINK)
        card.create_line(1, IMG_H, W - 2, IMG_H, fill=CARD_BORDER)
        border = rounded_rect(card, 0, 0, W - 1, H - 1, R_CARD, fill="", outline=CARD_BORDER)
        card.create_text(16, IMG_H + 22, text=name, anchor="w", fill=TEXT, font=(FONT, 10, "bold"))
        card.create_text(16, IMG_H + 46, text=peso(price), anchor="w", fill=NAVY,
                         font=(FONT, 13, "bold"))
        add = RoundButton(card, "+", lambda: self.add_to_cart(pid, name, price), style="soft",
                          width=36, height=36, font=(FONT, 14, "bold"), bg=WHITE)
        card.create_window(W - 14, IMG_H + 34, window=add, anchor="e")

        def hover(on):
            card.itemconfig(border, outline=PINK_LINE if on else CARD_BORDER)
            card.itemconfig(shadow, fill=SHADOW_HOVER if on else SHADOW)

        card.bind("<Button-1>", lambda e: self.add_to_cart(pid, name, price))
        card.bind("<Enter>", lambda e: hover(True))
        card.bind("<Leave>", lambda e: hover(False))
        return card

    # ---------- right: order menu (cart), total, payment ----------
    def build_order_panel(self):
        panel = tk.Frame(self, bg=WHITE, width=390)
        panel.grid(row=0, column=2, sticky="ns")
        panel.pack_propagate(False)
        inner = tk.Frame(panel, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=24, pady=(26, 20))

        tk.Label(inner, text="Order Menu", bg=WHITE, fg=NAVY,
                 font=(FONT, 15, "bold")).pack(anchor="w")
        self.count_label = tk.Label(inner, text="", bg=WHITE, fg=MUTED, font=(FONT, 10))
        self.count_label.pack(anchor="w")

        # Bottom part first (packed from the bottom) so it always stays visible
        bottom = tk.Frame(inner, bg=WHITE)
        bottom.pack(side="bottom", fill="x")

        tk.Frame(bottom, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 12))
        total_row = tk.Frame(bottom, bg=WHITE)
        total_row.pack(fill="x")
        tk.Label(total_row, text="Total", bg=WHITE, fg=TEXT,
                 font=(FONT, 12, "bold")).pack(side="left")
        self.total_label = tk.Label(total_row, text="₱0.00", bg=WHITE, fg=NAVY,
                                    font=(FONT, 22, "bold"))
        self.total_label.pack(side="right")

        tk.Label(bottom, text="Cash Received (₱)", bg=WHITE, fg=MUTED,
                 font=(FONT, 10)).pack(anchor="w", pady=(10, 4))
        self.entry_box = RoundedPanel(bottom, fill=WHITE, radius=R_BUTTON, border=INPUT_BORDER,
                                      pad=8, stretch=True)
        self.entry_box.pack(fill="x")
        self.pay_entry = tk.Entry(self.entry_box.inner, font=(FONT, 15), justify="right",
                                  relief="flat", bd=0, fg=TEXT, bg=WHITE,
                                  disabledbackground=WHITE, disabledforeground=MUTED,
                                  insertbackground=PINK, highlightthickness=0)
        self.pay_entry.pack(fill="x", padx=6, pady=1)
        self.pay_entry.bind("<Return>", lambda e: self.pay_button.invoke())
        self.pay_entry.bind("<FocusIn>", lambda e: self.entry_box.set_border(PINK_LINE))
        self.pay_entry.bind("<FocusOut>", lambda e: self.entry_box.set_border(INPUT_BORDER))

        self.pay_message = tk.Label(bottom, text="", bg=WHITE, fg=MUTED, font=(FONT, 9, "bold"),
                                    wraplength=330, justify="left", anchor="w")
        self.pay_message.pack(fill="x", pady=(6, 8))

        # Pay Now: the strongest action on the screen
        self.pay_button = RoundButton(bottom, "Pay Now", self.process_payment, height=48,
                                      font=(FONT, 12, "bold"))
        self.pay_button.pack(fill="x")

        # Cart rows go in the middle area
        self.rows_frame = tk.Frame(inner, bg=WHITE)
        self.rows_frame.pack(fill="both", expand=True, pady=(12, 10))

    def cart_row(self, line, first):
        """One item: photo | name, subtotal | - qty +  x unit price, Remove."""
        pid = line["id"]
        if not first:
            tk.Frame(self.rows_frame, bg=CARD_BORDER, height=1).pack(fill="x")
        row = tk.Frame(self.rows_frame, bg=WHITE)
        row.pack(fill="x", pady=9)
        row.columnconfigure(1, weight=1)

        img = self.product_image(line["name"], thumb=True)
        if img:
            tk.Label(row, image=img, bg=WHITE).grid(row=0, column=0, rowspan=2, padx=(0, 12))

        tk.Label(row, text=line["name"], bg=WHITE, fg=TEXT, anchor="w",
                 font=(FONT, 10, "bold")).grid(row=0, column=1, sticky="w")
        tk.Label(row, text=peso(line["subtotal"]), bg=WHITE, fg=TEXT, anchor="e",
                 font=(FONT, 11, "bold")).grid(row=0, column=2, sticky="e")

        qty = tk.Frame(row, bg=WHITE)
        qty.grid(row=1, column=1, sticky="w", pady=(6, 0))
        RoundButton(qty, "−", lambda: self.decrease_item(pid), style="qty",
                    width=26, height=26, radius=6, font=(FONT, 11, "bold")).pack(side="left")
        tk.Label(qty, text=str(line["qty"]), bg=WHITE, fg=TEXT, width=3,
                 font=(FONT, 10, "bold")).pack(side="left")
        RoundButton(qty, "+", lambda: self.increase_item(pid), style="qty",
                    width=26, height=26, radius=6, font=(FONT, 11, "bold")).pack(side="left")
        tk.Label(qty, text=f"   × {peso(line['price'])}", bg=WHITE, fg=MUTED,
                 font=(FONT, 9)).pack(side="left")

        remove = tk.Label(row, text="Remove", bg=WHITE, fg=MUTED, cursor="hand2", font=(FONT, 9))
        remove.grid(row=1, column=2, sticky="e", pady=(6, 0))
        remove.bind("<Button-1>", lambda e: self.remove_item(pid))
        remove.bind("<Enter>", lambda e: remove.config(fg=ERROR, font=(FONT, 9, "underline")))
        remove.bind("<Leave>", lambda e: remove.config(fg=MUTED, font=(FONT, 9)))

    # ---------- feedback ----------
    def show_status(self, text, ok=True):
        """Show a short rounded toast message at the top right, then hide it after 3 seconds."""
        text = ("✔  " if ok else "⚠  ") + text
        self.toast_text = text
        font = (FONT, 10, "bold")
        w = tkfont.Font(font=font).measure(text) + 30
        self.toast.config(width=w)
        self.toast.delete("all")
        rounded_rect(self.toast, 0, 0, w - 1, 35, R_BUTTON,
                     fill=SUCCESS_BG if ok else ERROR_BG, outline="")
        self.toast.create_text(15, 18, text=text, anchor="w", font=font,
                               fill=SUCCESS if ok else ERROR)
        if self.toast_job:
            self.after_cancel(self.toast_job)
        self.toast_job = self.after(3000, self.hide_toast)

    def hide_toast(self):
        self.toast.delete("all")
        self.toast_text = ""
        self.toast_job = None

    def cart_locked(self):
        if self.paid:
            self.show_status("Order already paid. Click 'New Transaction' to start again.", ok=False)
            return True
        return False

    # ---------- cart actions ----------
    def add_to_cart(self, pid, name, price):
        if self.cart_locked():
            return
        self.cart.add(pid, name, price)
        self.refresh_cart()
        self.show_status(f"Added 1 x {name}")

    def increase_item(self, pid):
        if self.cart_locked():
            return
        self.cart.increase(pid)
        self.refresh_cart()
        self.show_status("Quantity increased")

    def decrease_item(self, pid):
        if self.cart_locked():
            return
        self.cart.decrease(pid)      # at quantity 1, this removes the item
        self.refresh_cart()
        self.show_status("Quantity decreased")

    def remove_item(self, pid):
        if self.cart_locked():
            return
        name = self.cart.items[pid]["name"]
        self.cart.remove(pid)
        self.refresh_cart()
        self.show_status(f"Removed {name}")

    def refresh_cart(self):
        """Redraw the order summary and recompute the total (runs on every cart change)."""
        for child in self.rows_frame.winfo_children():
            child.destroy()
        lines = self.cart.lines()
        if not lines:
            tk.Label(self.rows_frame, text="\U0001F6D2\n\nYour order is empty.\nClick + on a product to add it.",
                     bg=WHITE, fg=MUTED, font=(FONT, 10), justify="center").pack(expand=True)
        for i, line in enumerate(lines):
            self.cart_row(line, first=(i == 0))
        count = sum(line["qty"] for line in lines)
        self.count_label.config(text=f"{count} item{'s' if count != 1 else ''}")
        self.total_label.config(text=peso(self.cart.total()))

    # ---------- payment ----------
    def process_payment(self):
        if self.paid:                    # after payment, this button re-opens the receipt
            self.show_receipt_panel()
            return
        if self.cart.is_empty():
            self.pay_message.config(text="⚠  The cart is empty. Add a product first.", fg=ERROR)
            return

        total = self.cart.total()
        ok, result = validate_payment(self.pay_entry.get(), total)
        if not ok:
            self.pay_message.config(text="⚠  " + result, fg=ERROR)
            self.entry_box.set_border(ERROR)
            self.show_status(result, ok=False)
            return

        amount_paid = result
        change = compute_change(amount_paid, total)
        lines = self.cart.lines()
        reference, timestamp = database.save_transaction(lines, total, amount_paid, change)
        self.last_receipt = (lines, total, amount_paid, change, reference, timestamp)

        self.paid = True
        self.pay_entry.config(state="disabled")
        self.entry_box.set_border(INPUT_BORDER)
        self.pay_message.config(
            text=f"✔  Payment successful!  Change: {peso(change)}  •  {reference}",
            fg=SUCCESS)
        self.pay_button.set_text("View Receipt")
        self.show_status(f"Payment successful • {reference}")
        self.show_confirmation_panel()

    # ---------- pop-up panels over a glass backdrop ----------
    def open_overlay(self, build_card):
        """
        Show a pop-up panel over a see-through "glass" backdrop.

        Tkinter cannot make part of a window transparent, so two small borderless
        windows are placed exactly over the app:
          1. backdrop - a light-pink window at ~55% opacity (the glass), so the
                        app (title, banner, burger photos) shows through it
          2. card     - the rounded panel itself, centered on top
        Clicking the glass or pressing Esc closes the panel.
        """
        self.close_overlay()
        self.update_idletasks()

        backdrop = tk.Toplevel(self)
        backdrop.overrideredirect(True)          # no title bar or border
        backdrop.configure(bg=OVERLAY_BG)
        backdrop.transient(self)

        card_win = tk.Toplevel(self)
        card_win.overrideredirect(True)
        card_win.transient(self)
        try:                                     # rounded corners: make the key color invisible
            card_win.attributes("-transparentcolor", KEY_COLOR)
            corner = KEY_COLOR
        except tk.TclError:
            corner = OVERLAY_BG
        card_win.configure(bg=corner)
        panel = RoundedPanel(card_win, fill=WHITE, radius=14, border=CARD_BORDER,
                             pad=28, bg=corner)
        panel.pack()
        build_card(panel.inner)

        self.overlay, self.overlay_card = backdrop, card_win

        def set_alpha(win, value):
            try:
                win.attributes("-alpha", value)
            except tk.TclError:
                pass                             # transparency not supported: stays solid

        def position(offset=0):
            """Keep the glass over the app and the card centered on it."""
            if self.overlay is not backdrop:
                return
            x, y = self.winfo_rootx(), self.winfo_rooty()
            w, h = self.winfo_width(), self.winfo_height()
            backdrop.geometry(f"{w}x{h}+{x}+{y}")
            card_win.update_idletasks()
            cw, ch = card_win.winfo_reqwidth(), card_win.winfo_reqheight()
            card_win.geometry(f"+{x + (w - cw) // 2}+{y + (h - ch) // 2 + offset}")

        set_alpha(backdrop, 0.0)
        set_alpha(card_win, 0.0)
        position(24)
        backdrop.lift()
        card_win.lift()

        # Fade the glass in and slide the card up gently (fast and subtle)
        steps = [(0.12, 0.2, 18), (0.25, 0.45, 12), (0.38, 0.7, 7),
                 (0.48, 0.9, 3), (GLASS_ALPHA, 1.0, 0)]
        for i, (glass, card_a, offset) in enumerate(steps):
            self.after((i + 1) * 18, lambda g=glass, c=card_a, o=offset: (
                self.overlay is backdrop and (set_alpha(backdrop, g), set_alpha(card_win, c),
                                              position(o))))

        # Follow the main window if it is moved or resized
        self.overlay_bind = self.bind("<Configure>", lambda e: position(), add="+")

        for win in (backdrop, card_win, self):
            win.bind("<Escape>", lambda e: self.close_overlay())
        backdrop.bind("<Button-1>", lambda e: self.close_overlay())   # click the glass to close
        card_win.focus_force()

    def close_overlay(self):
        if self.overlay is not None:
            self.overlay.destroy()
            self.overlay_card.destroy()
            self.overlay = self.overlay_card = None
            self.unbind("<Configure>", self.overlay_bind)
            self.unbind("<Escape>")
            self.focus_force()

    def detail_row(self, parent, label, value, big=False):
        row = tk.Frame(parent, bg=PAGE_BG)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=PAGE_BG, fg=MUTED, font=(FONT, 10)).pack(side="left")
        tk.Label(row, text=value, bg=PAGE_BG, fg=PINK if big else TEXT,
                 font=(FONT, 16 if big else 10, "bold")).pack(side="right")

    def two_buttons(self, parent, left_text, left_cmd, right_text, right_cmd, right_weight=1):
        btns = tk.Frame(parent, bg=WHITE)
        btns.pack(fill="x")
        same = "b" if right_weight == 1 else None
        btns.columnconfigure(0, weight=1, uniform=same)
        btns.columnconfigure(1, weight=right_weight, uniform=same)
        RoundButton(btns, left_text, left_cmd, style="outline", height=44, width=100).grid(
            row=0, column=0, sticky="ew", padx=(0, 6))
        RoundButton(btns, right_text, right_cmd, height=44, width=100,
                    font=(FONT, 11, "bold")).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def show_confirmation_panel(self):
        """Step 6: payment confirmation with the transaction details."""
        lines, total, paid, change, reference, timestamp = self.last_receipt

        def build(card):
            icon = tk.Canvas(card, width=76, height=76, bg=WHITE, highlightthickness=0)
            icon.create_oval(2, 2, 74, 74, fill=SUCCESS_BG, outline="")
            icon.create_text(38, 39, text="✔", fill=SUCCESS, font=(FONT, 28, "bold"))
            icon.pack()
            tk.Label(card, text="Payment Successful", bg=WHITE, fg=NAVY,
                     font=(FONT, 18, "bold")).pack(pady=(12, 2))
            tk.Label(card, text="The order has been paid and saved.", bg=WHITE, fg=MUTED,
                     font=(FONT, 10)).pack()

            details = RoundedPanel(card, fill=PAGE_BG, radius=R_BOX, border=CARD_BORDER,
                                   pad=16, stretch=True)
            details.pack(fill="x", pady=(18, 20))
            box = details.inner
            tk.Frame(box, bg=PAGE_BG, width=290).pack()          # sets the panel width
            self.detail_row(box, "Transaction No.", reference)
            self.detail_row(box, "Date / Time", timestamp)
            self.detail_row(box, "Total Amount", peso(total))
            self.detail_row(box, "Amount Paid (Cash)", peso(paid))
            tk.Frame(box, bg=CARD_BORDER, height=1).pack(fill="x", pady=6)
            self.detail_row(box, "Change", peso(change), big=True)

            self.two_buttons(card, "Close", self.close_overlay, "View Receipt", self.show_receipt_panel)

        self.open_overlay(build)

    # ---------- receipt ----------
    def receipt_text(self, lines, total, paid, change, reference, timestamp):
        w = 44
        out = ["CAMPUS SNACK BAR".center(w), "Official Receipt".center(w), "=" * w,
               f"Transaction No.: {reference}", f"Date/Time:       {timestamp}", "-" * w,
               f"{'Item':<22}{'Qty':>4}{'Price':>8}{'Subtotal':>10}", "-" * w]
        for line in lines:
            out.append(f"{line['name'][:22]:<22}{line['qty']:>4}"
                       f"{line['price']:>8.2f}{line['subtotal']:>10.2f}")
        out += ["-" * w,
                f"{'TOTAL AMOUNT DUE:':<26}{peso(total):>18}",
                f"{'Amount Paid (Cash):':<26}{peso(paid):>18}",
                f"{'Change:':<26}{peso(change):>18}",
                "=" * w, "Thank you! Come again.".center(w)]
        return "\n".join(out)

    def show_receipt_panel(self):
        """Step 7: digital receipt, with a button to start a new transaction."""
        if not self.last_receipt:
            return
        lines, total, paid, change, reference, timestamp = self.last_receipt

        def build(card):
            head = RoundedPanel(card, fill=NAVY, radius=R_BOX, pad=14, stretch=True)
            head.pack(fill="x")
            tk.Label(head.inner, text="\U0001F9FE  Receipt", bg=NAVY, fg=WHITE,
                     font=(FONT, 14, "bold")).pack(side="left", padx=4)
            tk.Label(head.inner, text=reference, bg=NAVY, fg=NAVY_SOFT,
                     font=(FONT, 10)).pack(side="right", padx=4)

            paper = RoundedPanel(card, fill=PAGE_BG, radius=R_BOX, border=CARD_BORDER, pad=14)
            paper.pack(pady=16)
            text = tk.Text(paper.inner, font=("Consolas", 10), bg=PAGE_BG, fg=TEXT,
                           relief="flat", bd=0, highlightthickness=0,
                           width=44, height=len(lines) + 14)
            text.insert("1.0", self.receipt_text(*self.last_receipt))
            text.config(state="disabled")
            text.pack()

            self.two_buttons(card, "Close", self.close_overlay,
                             "Start New Transaction", self.new_transaction, right_weight=2)

        self.open_overlay(build)

    # ---------- new transaction ----------
    def new_transaction(self):
        """Clear the cart, payment amount, and receipt."""
        self.close_overlay()
        self.cart.clear()
        self.paid = False
        self.last_receipt = None
        self.refresh_cart()
        self.pay_entry.config(state="normal")
        self.pay_entry.delete(0, "end")
        self.entry_box.set_border(INPUT_BORDER)
        self.pay_button.set_text("Pay Now")
        self.pay_message.config(text="", fg=MUTED)
        self.show_status("New transaction started")


if __name__ == "__main__":
    SnackBarPOS().mainloop()
