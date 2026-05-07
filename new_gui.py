import math
import tkinter as tk
from tkinter import ttk


class BitcoinNewsAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Bitcoin News Analyzer")
        self.geometry("1180x640")
        self.minsize(980, 560)
        self.configure(bg="#060a14")

        self.colors = {
            "bg": "#060a14",
            "header": "#09111f",
            "panel": "#0d1525",
            "panel_soft": "#101d30",
            "panel_alt": "#192640",
            "border": "#1f3050",
            "border_soft": "#142140",
            "muted": "#8fa5c0",
            "muted_2": "#5a6e88",
            "text": "#e8f0fc",
            "orange": "#ff8c2a",
            "green": "#00e894",
            "red": "#ff4a52",
            "gray": "#607080",
            "scroll": "#8a9aaa",
            "scroll_track": "#141e2d",
            "accent": "#3b82f6",
        }

        self.sources = ["All"]
        self.active_source = tk.StringVar(value="All")
        self.trend = []
        self.bar_data = []
        self.news = []
        self.pie_data = (0, 0, 0)
        self.is_loading = True

        self._configure_style()
        self._build_layout()
        self.after(500, self._fetch_news)

    def _fetch_news(self):
        self.is_loading = True
        self._refresh_news()
        self._draw_trend()
        self._draw_pie()
        self._draw_bars()
        
        import threading
        import queue
        if not hasattr(self, 'data_queue'):
            self.data_queue = queue.Queue()
            
        def task(q):
            try:
                from news import NewsData
                data_fetcher = NewsData()
                compound, pos, neu, neg, text, news_items = data_fetcher.run()
                q.put(("success", (compound, pos, neu, neg, news_items)))
            except Exception as e:
                q.put(("error", e))
                print("Veri çekme hatası:", e)
                
        threading.Thread(target=task, args=(self.data_queue,), daemon=True).start()
        self._check_queue()

    def _check_queue(self):
        import queue
        try:
            msg, data = self.data_queue.get_nowait()
            if msg == "success":
                compound, pos, neu, neg, news_items = data
                self._on_data_fetched(compound, pos, neu, neg, news_items)
            elif msg == "error":
                self.is_loading = False
                self._refresh_news()
        except queue.Empty:
            self.after(100, self._check_queue)

    def _on_data_fetched(self, compound, pos, neu, neg, news_items):
        self.is_loading = False
        self.news = news_items
        
        total = pos + neg + neu
        if total > 0:
            p = int(pos/total*100)
            n = int(neg/total*100)
            u = int(neu/total*100)
            diff = 100 - (p + n + u)
            if p >= n and p >= u:
                p += diff
            elif n >= p and n >= u:
                n += diff
            else:
                u += diff
            self.pie_data = (p, n, u)
        else:
            self.pie_data = (33, 33, 34)
            
        source_counts = {}
        unique_sources = ["All"]
        for item in news_items:
            src = item["source"]
            source_counts[src] = source_counts.get(src, 0) + 1
            if src not in unique_sources:
                unique_sources.append(src)
                
        self.sources = unique_sources
        self.bar_data = [(src, count) for src, count in source_counts.items()]
        
        self._rebuild_filter_buttons()
        
        recent_scores = [item["compound"] for item in news_items[-7:]]
        while len(recent_scores) < 7:
            recent_scores.insert(0, 0)
        self.trend = [int((score + 1) / 2 * 80) for score in recent_scores]
        
        self._refresh_filters()
        self._refresh_news()
        self._draw_trend()
        self._draw_pie()
        self._draw_bars()

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.colors["bg"], borderwidth=0)
        style.configure("Side.TFrame", background=self.colors["panel"], borderwidth=0)
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=self.colors["scroll"],
            troughcolor=self.colors["scroll_track"],
            bordercolor=self.colors["scroll_track"],
            arrowcolor="#a7a7a7",
            lightcolor=self.colors["scroll"],
            darkcolor=self.colors["scroll"],
            width=15,
        )

    def _build_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_body()

    def _build_header(self):
        header = tk.Frame(self, bg=self.colors["header"], height=67)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        icon = tk.Canvas(header, width=26, height=26, bg=self.colors["header"], highlightthickness=0)
        icon.grid(row=0, column=0, rowspan=2, padx=(22, 7), pady=(20, 0), sticky="n")
        icon.create_line(3, 19, 9, 12, 14, 16, 23, 7, fill=self.colors["orange"], width=2)
        icon.create_line(23, 7, 23, 14, fill=self.colors["orange"], width=2)
        icon.create_line(23, 7, 16, 7, fill=self.colors["orange"], width=2)

        tk.Label(
            header,
            text="Bitcoin News Analyzer",
            bg=self.colors["header"],
            fg=self.colors["text"],
            font=("Segoe UI", 17, "bold"),
        ).grid(row=0, column=1, padx=0, pady=(15, 0), sticky="sw")
        tk.Label(
            header,
            text="Real-time sentiment analysis & news tracking",
            bg=self.colors["header"],
            fg=self.colors["muted"],
            font=("Segoe UI", 8),
        ).grid(row=1, column=1, padx=1, pady=(0, 11), sticky="nw")
        tk.Frame(header, bg=self.colors["border"], height=1).grid(
            row=2, column=0, columnspan=2, sticky="ew"
        )

    def _build_body(self):
        body = ttk.Frame(self, style="App.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=20)
        body.grid_columnconfigure(2, minsize=282)
        body.grid_rowconfigure(0, weight=1)

        main = ttk.Frame(body, style="App.TFrame")
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, minsize=0)
        main.grid_rowconfigure(1, minsize=56)
        main.grid_rowconfigure(2, weight=1, minsize=200)
        main.grid_rowconfigure(3, weight=1, minsize=198)

        self._build_center_scroll(body)
        self._build_sentiment(main)
        self._build_news_sidebar(body)

    def _build_featured_card(self, parent):
        shell = tk.Frame(parent, bg=self.colors["bg"], height=74)
        shell.grid(row=0, column=0, columnspan=2, sticky="ew")
        shell.grid_propagate(False)
        shell.grid_columnconfigure(0, weight=1)

        card = tk.Canvas(shell, height=55, bg=self.colors["bg"], highlightthickness=0)
        card.grid(row=0, column=0, sticky="ew", padx=(106, 100), pady=(18, 0))
        card.bind("<Configure>", lambda event: self._draw_featured(card))

    def _draw_featured(self, canvas):
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 40:
            return
        self._rounded_rect(canvas, 1, 1, w - 1, h - 1, 7, fill="#031312", outline="#00a667", width=1)
        self._pill(canvas, 19, 19, 65, 37, "Reddit", self.colors["panel_alt"], self.colors["text"])
        canvas.create_text(78, 28, text="♧", fill=self.colors["green"], font=("Segoe UI", 11, "bold"))
        canvas.create_text(w - 20, 28, anchor="e", text="2 saat önce", fill="#c5d2e2", font=("Segoe UI", 8))

    def _build_center_scroll(self, parent):
        holder = tk.Frame(parent, bg=self.colors["bg"])
        holder.grid(row=0, column=1, sticky="ns")
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)
        canvas = tk.Canvas(holder, width=20, bg=self.colors["bg"], highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="ns")
        canvas.bind("<Configure>", self._draw_center_scroll)

    def _draw_center_scroll(self, event):
        canvas = event.widget
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        canvas.create_rectangle(0, 0, w, h, fill=self.colors["bg"], outline="")
        canvas.create_rectangle(0, 0, w, 74, fill=self.colors["panel_soft"], outline="")
        canvas.create_polygon(w / 2, 7, w / 2 - 6, 16, w / 2 + 6, 16, fill="#9b9b9b")
        canvas.create_polygon(w / 2, 68, w / 2 - 6, 58, w / 2 + 6, 58, fill="#9b9b9b")
        self._rounded_rect(canvas, 5, 23, 15, 44, 5, fill="#9b9b9b", outline="")

    def _build_sentiment(self, parent):
        title = tk.Frame(parent, bg=self.colors["bg"], height=56)
        title.grid(row=1, column=0, columnspan=2, sticky="ew")
        title.grid_propagate(False)

        icon = tk.Canvas(title, width=23, height=23, bg=self.colors["bg"], highlightthickness=0)
        icon.pack(side="left", padx=(22, 0), pady=(20, 0))
        icon.create_line(4, 18, 19, 18, fill=self.colors["orange"], width=2)
        for x, y in [(6, 9), (11, 5), (16, 13)]:
            icon.create_rectangle(x - 2, y, x + 1, 18, fill=self.colors["orange"], outline="")

        tk.Label(
            title,
            text="Sentiment Analysis",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=(6, 0), pady=(17, 0))

        trend_panel = self._panel(parent)
        trend_panel.grid(row=2, column=0, sticky="nsew", padx=(22, 8), pady=(0, 18))
        pie_panel = self._panel(parent)
        pie_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 18), pady=(0, 18))
        bar_panel = self._panel(parent)
        bar_panel.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=22, pady=(0, 18))

        self.trend_canvas = self._chart_canvas(trend_panel)
        self.pie_canvas = self._chart_canvas(pie_panel)
        self.bar_canvas = self._chart_canvas(bar_panel)
        self.trend_canvas.bind("<Configure>", self._draw_trend)
        self.pie_canvas.bind("<Configure>", self._draw_pie)
        self.bar_canvas.bind("<Configure>", self._draw_bars)

    def _build_news_sidebar(self, parent):
        sidebar = ttk.Frame(parent, style="Side.TFrame")
        sidebar.grid(row=0, column=2, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(2, weight=1)

        tk.Frame(sidebar, bg=self.colors["border"], width=1).place(x=0, y=0, relheight=1)
        header = tk.Frame(sidebar, bg=self.colors["panel"])
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(15, 10))

        icon = tk.Canvas(header, width=18, height=18, bg=self.colors["panel"], highlightthickness=0)
        icon.pack(side="left")
        icon.create_oval(3, 3, 14, 14, outline=self.colors["orange"], width=2)
        icon.create_line(5, 14, 1, 18, fill=self.colors["orange"], width=2)

        tk.Label(
            header,
            text="News Sources",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(7, 0))

        self.filters_frame = tk.Frame(sidebar, bg=self.colors["panel"])
        self.filters_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(3, 12))

        self.filter_buttons = {}
        for index, source in enumerate(self.sources):
            btn = tk.Button(
                self.filters_frame,
                text=source,
                width=10,
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 7, "bold"),
                pady=5,
                padx=4,
                command=lambda value=source: self._set_source(value),
            )
            btn.grid(row=index // 4, column=index % 4, padx=(0, 1), pady=(0, 1), sticky="ew")
            self.filter_buttons[source] = btn

        list_holder = tk.Frame(sidebar, bg=self.colors["panel"])
        list_holder.grid(row=2, column=0, sticky="nsew")
        list_holder.grid_columnconfigure(0, weight=1)
        list_holder.grid_rowconfigure(0, weight=1)

        self.news_canvas = tk.Canvas(list_holder, bg=self.colors["panel"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(
            list_holder,
            orient="vertical",
            command=self.news_canvas.yview,
            style="Vertical.TScrollbar",
        )
        self.news_list = tk.Frame(self.news_canvas, bg=self.colors["panel"])

        self.news_canvas.configure(yscrollcommand=scrollbar.set)
        self.news_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        window_id = self.news_canvas.create_window((0, 0), window=self.news_list, anchor="nw")
        self.news_list.bind(
            "<Configure>",
            lambda event: self.news_canvas.configure(scrollregion=self.news_canvas.bbox("all")),
        )
        self.news_canvas.bind(
            "<Configure>",
            lambda event: self.news_canvas.itemconfigure(window_id, width=event.width),
        )
        self._refresh_filters()
        self._refresh_news()

    def _panel(self, parent):
        frame = tk.Frame(
            parent,
            bg=self.colors["panel"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        frame.grid_propagate(False)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _chart_canvas(self, parent):
        canvas = tk.Canvas(parent, bg=self.colors["panel"], highlightthickness=0, bd=0)
        canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
        return canvas

    def _set_source(self, source):
        self.active_source.set(source)
        self._refresh_filters()
        self._refresh_news()

    def _rebuild_filter_buttons(self):
        for widget in self.filters_frame.winfo_children():
            widget.destroy()
        self.filter_buttons = {}
        for index, source in enumerate(self.sources):
            btn = tk.Button(
                self.filters_frame,
                text=source,
                width=10,
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 7, "bold"),
                pady=5,
                padx=4,
                command=lambda value=source: self._set_source(value),
            )
            btn.grid(row=index // 4, column=index % 4, padx=(0, 1), pady=(0, 1), sticky="ew")
            self.filter_buttons[source] = btn
        self._refresh_filters()

    def _refresh_filters(self):
        for source, btn in self.filter_buttons.items():
            active = source == self.active_source.get()
            btn.configure(
                bg=self.colors["orange"] if active else self.colors["panel_alt"],
                fg=self.colors["text"] if active else self.colors["muted"],
                activebackground="#ff8a32" if active else "#243044",
                activeforeground=self.colors["text"],
            )

    def _refresh_news(self):
        for child in self.news_list.winfo_children():
            child.destroy()

        if hasattr(self, 'is_loading') and self.is_loading:
            tk.Label(
                self.news_list, 
                text="Loading data...", 
                bg=self.colors["panel"], 
                fg=self.colors["muted"], 
                font=("Segoe UI", 12)
            ).pack(pady=40)
            return

        source = self.active_source.get()
        visible = [
            item
            for item in self.news
            if source == "All" or item["source"] == source
        ]
        for item in visible:
            self._news_card(self.news_list, item).pack(fill="x")

    def _news_card(self, parent, item):
        card = tk.Frame(parent, bg=self.colors["panel_soft"], padx=12, pady=12)
        card.bind("<Enter>", lambda event: self._set_card_bg(card, "#1d2638"))
        card.bind("<Leave>", lambda event: self._set_card_bg(card, self.colors["panel_soft"]))

        top = tk.Frame(card, bg=card["bg"])
        top.pack(fill="x")
        tk.Label(
            top,
            text=item["source"],
            bg=top["bg"],
            fg=self.colors["orange"],
            font=("Segoe UI", 7, "bold"),
        ).pack(side="left")

        symbol = {"positive": "♧", "negative": "♤", "neutral": "−"}[item["sentiment"]]
        color = {
            "positive": self.colors["green"],
            "negative": self.colors["red"],
            "neutral": self.colors["gray"],
        }[item["sentiment"]]
        tk.Label(
            top,
            text=symbol,
            bg=top["bg"],
            fg=color,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right")

        tk.Label(
            card,
            text=item["title"],
            bg=card["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
            wraplength=230,
            justify="left",
        ).pack(anchor="w", pady=(8, 4))
        tk.Label(
            card,
            text=item["body"],
            bg=card["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 8, "bold"),
            wraplength=240,
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            card,
            text=item["time"],
            bg=card["bg"],
            fg=self.colors["muted_2"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(8, 0))

        tk.Frame(parent, bg=self.colors["border_soft"], height=1).pack(fill="x")
        return card

    def _set_card_bg(self, card, color):
        card.configure(bg=color)
        for child in card.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=color)
                for sub in child.winfo_children():
                    sub.configure(bg=color)
            else:
                child.configure(bg=color)

    def _draw_trend(self, event=None):
        canvas = self.trend_canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 80 or h < 80:
            return

        canvas.create_text(
            0, 12, anchor="nw", text="Recent News Sentiment Trend",
            fill=self.colors["text"], font=("Segoe UI", 8, "bold")
        )
        
        if hasattr(self, 'is_loading') and self.is_loading:
            canvas.create_text(w/2, h/2, text="Loading...", fill=self.colors["muted"], font=("Segoe UI", 10))
            return
            
        left, top, right, bottom = 48, 42, w - 8, h - 44
        self._draw_grid(canvas, left, top, right, bottom, 4, 6)

        for value in [0, 20, 40, 60, 80]:
            y = bottom - (value / 80) * (bottom - top)
            canvas.create_text(left - 8, y, anchor="e", text=str(value), fill=self.colors["muted"], font=("Segoe UI", 8))

        points = []
        if self.trend:
            for index, value in enumerate(self.trend):
                x = left + (index / (len(self.trend) - 1)) * (right - left)
                y = bottom - (value / 80) * (bottom - top)
                points.extend([x, y])
            if len(points) >= 4:
                canvas.create_line(*points, fill="#b7aebc", width=2, smooth=True)
            for index, value in enumerate(self.trend):
                x = left + (index / (len(self.trend) - 1)) * (right - left)
                y = bottom - (value / 80) * (bottom - top)
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#cfc8d4", outline="#ffffff")

        for index, label in enumerate(["1", "2", "3", "4", "5", "6", "7"]):
            x = left + (index / 6) * (right - left)
            canvas.create_text(x, bottom + 14, text=label, fill=self.colors["muted"], font=("Segoe UI", 8))
        self._legend(canvas, w / 2 - 72, h - 18)

    def _draw_pie(self, event=None):
        canvas = self.pie_canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 120 or h < 90:
            return

        canvas.create_text(
            0, 12, anchor="nw", text="Sentiment Distribution",
            fill=self.colors["text"], font=("Segoe UI", 8, "bold")
        )
        
        if hasattr(self, 'is_loading') and self.is_loading:
            canvas.create_text(w/2, h/2, text="Loading...", fill=self.colors["muted"], font=("Segoe UI", 10))
            return
            
        size = min(w, h) * 0.54
        x0 = w / 2 - size / 2
        y0 = h / 2 - size / 2 + 10
        x1, y1 = x0 + size, y0 + size
        data = [
            (f"Positive: {self.pie_data[0]}%", self.pie_data[0], self.colors["green"]),
            (f"Negative: {self.pie_data[1]}%", self.pie_data[1], self.colors["red"]),
            (f"Neutral: {self.pie_data[2]}%", self.pie_data[2], self.colors["gray"]),
        ]
        start = 0
        for _, value, color in data:
            extent = 360 * value / 100
            canvas.create_arc(x0, y0, x1, y1, start=start, extent=extent, fill=color, outline="#d8dee8", width=1)
            start += extent

        positions = [(w / 2 - 76, y0 - 10), (w / 2 - 76, y1 + 8), (x1 + 38, h / 2 + 32)]
        for (label, _, color), (x, y) in zip(data, positions):
            canvas.create_text(x, y, text=label, fill=color, font=("Segoe UI", 9))

    def _draw_bars(self, event=None):
        canvas = self.bar_canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 180 or h < 120:
            return

        canvas.create_text(
            0, 14, anchor="nw", text="Source Article Distribution",
            fill=self.colors["text"], font=("Segoe UI", 8, "bold")
        )
        
        if hasattr(self, 'is_loading') and self.is_loading:
            canvas.create_text(w/2, h/2, text="Loading...", fill=self.colors["muted"], font=("Segoe UI", 10))
            return

        left, top, right, bottom = 52, 44, w - 16, h - 30
        self._draw_grid(canvas, left, top, right, bottom, 4, 5)

        if not self.bar_data:
            return

        max_count = max(v for _, v in self.bar_data)
        if max_count == 0: max_count = 1
        max_val = int(max_count * 1.4)
        if max_val == 0: max_val = 10

        for value in [0, max_val//4, max_val//2, max_val*3//4, max_val]:
            y = bottom - (value / max_val) * (bottom - top)
            canvas.create_text(left - 8, y, anchor="e", text=str(value), fill=self.colors["muted"], font=("Segoe UI", 8))

        n = len(self.bar_data)
        xs = [left + (i / max(n - 1, 1)) * (right - left) for i in range(n)]
        ys = [bottom - (v / max_val) * (bottom - top) for _, v in self.bar_data]

        # Filled area under the curve
        if n == 1:
            fill_pts = [xs[0] - 2, bottom, xs[0] - 2, ys[0], xs[0] + 2, ys[0], xs[0] + 2, bottom]
        else:
            fill_pts = [left, bottom]
            for i in range(n - 1):
                x0, y0 = xs[i], ys[i]
                x1, y1 = xs[i + 1], ys[i + 1]
                cx = (x0 + x1) / 2
                fill_pts += [x0, y0, cx, y0, cx, y1]
            fill_pts += [xs[-1], ys[-1], right, bottom]
        canvas.create_polygon(fill_pts, fill="#1a3a60", outline="", smooth=False)

        # Smooth line on top
        if n >= 2:
            line_pts = []
            for i in range(n - 1):
                x0, y0 = xs[i], ys[i]
                x1, y1 = xs[i + 1], ys[i + 1]
                cx = (x0 + x1) / 2
                line_pts += [x0, y0, cx, y0, cx, y1]
            line_pts += [xs[-1], ys[-1]]
            canvas.create_line(line_pts, fill=self.colors["accent"], width=2, smooth=False)
        elif n == 1:
            canvas.create_line(xs[0] - 2, ys[0], xs[0] + 2, ys[0], fill=self.colors["accent"], width=2)

        # Glowing dots at data points
        for i, ((label, value), x, y) in enumerate(zip(self.bar_data, xs, ys)):
            canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=self.colors["panel"], outline=self.colors["accent"], width=2)
            canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=self.colors["accent"], outline="")
            canvas.create_text(x, bottom + 14, text=label, fill=self.colors["muted"], font=("Segoe UI", 7))
            canvas.create_text(x, y - 12, text=str(value), fill=self.colors["accent"], font=("Segoe UI", 7, "bold"))

    def _draw_grid(self, canvas, left, top, right, bottom, rows, cols):
        for row in range(rows + 1):
            y = top + row * (bottom - top) / rows
            canvas.create_line(left, y, right, y, fill=self.colors["border"], dash=(2, 3))
        for col in range(cols + 1):
            x = left + col * (right - left) / cols
            canvas.create_line(x, top, x, bottom, fill=self.colors["border"], dash=(2, 3))
        canvas.create_line(left, bottom, right, bottom, fill=self.colors["muted_2"])
        canvas.create_line(left, top, left, bottom, fill=self.colors["muted_2"])

    def _legend(self, canvas, x, y):
        items = [
            ("Positive", self.colors["green"]),
            ("Negative", self.colors["red"]),
            ("Neutral", self.colors["gray"]),
        ]
        offset = 0
        for label, color in items:
            canvas.create_line(x + offset, y, x + offset + 10, y, fill=color, width=2)
            canvas.create_oval(x + offset + 4, y - 2, x + offset + 8, y + 2, fill=color, outline="")
            canvas.create_text(x + offset + 34, y, text=label, fill=color, font=("Segoe UI", 8))
            offset += 74

    def _pill(self, canvas, x0, y0, x1, y1, text, fill, color):
        self._rounded_rect(canvas, x0, y0, x1, y1, 9, fill=fill, outline="")
        canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=text, fill=color, font=("Segoe UI", 7, "bold"))

    def _rounded_rect(self, canvas, x0, y0, x1, y1, radius, **kwargs):
        points = [
            x0 + radius, y0,
            x1 - radius, y0,
            x1, y0,
            x1, y0 + radius,
            x1, y1 - radius,
            x1, y1,
            x1 - radius, y1,
            x0 + radius, y1,
            x0, y1,
            x0, y1 - radius,
            x0, y0 + radius,
            x0, y0,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)


if __name__ == "__main__":
    app = BitcoinNewsAnalysisApp()
    app.mainloop()
