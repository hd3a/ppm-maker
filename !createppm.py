import tkinter as tk
from tkinter import simpledialog, colorchooser, filedialog

class ColorGridApp:
    def __init__(self, root):
        self.root = root
        self.select_canvas_size()
        
    # --- 横・縦同時ウィンドウでサイズ選択 ---
    def select_canvas_size(self):
        input_win = tk.Toplevel(self.root)
        input_win.title("キャンバスサイズ選択")

        tk.Label(input_win, text="縦のマス数:").grid(row=0, column=0)
        self.rows_var = tk.IntVar(value=18)
        tk.Entry(input_win, textvariable=self.rows_var, width=5).grid(row=0, column=1)

        tk.Label(input_win, text="横のマス数:").grid(row=1, column=0)
        self.cols_var = tk.IntVar(value=18)
        tk.Entry(input_win, textvariable=self.cols_var, width=5).grid(row=1, column=1)

        tk.Button(input_win, text="決定", command=lambda: self.init_canvas(input_win)).grid(row=2, column=0, columnspan=2, pady=5)

    # --- キャンバス初期化 ---
    def init_canvas(self, input_win):
        self.rows = max(1, min(100, self.rows_var.get()))
        self.cols = max(1, min(100, self.cols_var.get()))
        input_win.destroy()

        self.base_px = 360  # 18x18マス時の物理サイズ
        max_cells = max(self.rows, self.cols)
        self.cell_size = max(1, self.base_px // max_cells)  # 正方形セルサイズ

        self.selected_color = "#000000"
        self.color_history = []
        self.colors = [["#FFFFFF" for _ in range(self.cols)] for _ in range(self.rows)]

        # ツール状態
        self.current_tool = tk.StringVar(value="pen")
        self.pen_size = tk.IntVar(value=1)
        self.start_point = None  # 四角ツール用

        # --- キャンバスボタン ---
        self.buttons = []
        for r in range(self.rows):
            row_buttons = []
            for c in range(self.cols):
                btn = tk.Button(self.root, bg="white",
                                width=self.cell_size//10, height=self.cell_size//20,
                                command=lambda r=r, c=c: self.apply_tool(r, c))
                btn.grid(row=r, column=c)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        # PPM出力ボタン
        tk.Button(self.root, text="PPM出力", command=self.export_ppm).grid(row=self.rows, column=0, columnspan=self.cols)

        # ツールウィンドウ
        self.open_tool_window()

    # --- ツール＆カラーピッカーウィンドウ ---
    def open_tool_window(self):
        self.tool_win = tk.Toplevel(self.root)
        self.tool_win.title("ツール & カラーピッカー")

        # 現在の色
        tk.Label(self.tool_win, text="現在の色").pack()
        self.color_label = tk.Label(self.tool_win, bg=self.selected_color, width=20, height=2)
        self.color_label.pack(pady=5)

        def pick_color():
            color_code = colorchooser.askcolor(title="色を選んでね")
            if color_code[1]:
                self.set_selected_color(color_code[1])
        tk.Button(self.tool_win, text="色を選ぶ", command=pick_color).pack(pady=5)

        # 色履歴
        tk.Label(self.tool_win, text="色履歴").pack()
        self.history_frame = tk.Frame(self.tool_win)
        self.history_frame.pack()

        # ツール選択
        tk.Label(self.tool_win, text="ツール").pack()
        tools = [("ペン", "pen"), ("塗りつぶし", "fill"), ("消しゴム", "eraser"),
                 ("スポイト", "eyedropper"), ("四角（塗りつぶし）", "rect_fill"),
                 ("四角（枠のみ）", "rect_outline")]
        for text, tool in tools:
            tk.Radiobutton(self.tool_win, text=text, value=tool, variable=self.current_tool,
                           indicatoron=False, width=20).pack(fill="x")

        # ペン太さ
        tk.Label(self.tool_win, text="ペンの太さ").pack()
        tk.Spinbox(self.tool_win, from_=1, to=10, textvariable=self.pen_size, width=5).pack()

    # --- 色選択 & 履歴管理 ---
    def set_selected_color(self, color):
        self.selected_color = color
        self.color_label.config(bg=color)
        if color in self.color_history:
            self.color_history.remove(color)
        self.color_history.insert(0, color)
        if len(self.color_history) > 10:
            self.color_history.pop()
        self.update_history_buttons()

    def update_history_buttons(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        for col in self.color_history:
            btn = tk.Button(self.history_frame, bg=col, width=4, height=2,
                            command=lambda c=col: self.set_selected_color(c))
            btn.pack(side="left", padx=2, pady=2)

    # --- ツール適用 ---
    def apply_tool(self, r, c):
        tool = self.current_tool.get()
        if tool == "pen":
            self.draw_pen(r, c)
        elif tool == "eraser":
            self.draw_pen(r, c, color="#FFFFFF")
        elif tool == "eyedropper":
            self.set_selected_color(self.colors[r][c])
        elif tool == "fill":
            target_color = self.colors[r][c]
            if target_color != self.selected_color:
                self.flood_fill(r, c, target_color, self.selected_color)
        elif tool in ("rect_fill", "rect_outline"):
            self.handle_rectangle_tool(r, c, tool)

    def draw_pen(self, r, c, color=None):
        color = color or self.selected_color
        size = self.pen_size.get()
        half = size // 2
        for dr in range(-half, half+1):
            for dc in range(-half, half+1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    self.set_color(rr, cc, color)

    # 四角ツール
    def handle_rectangle_tool(self, r, c, tool):
        if self.start_point is None:
            self.start_point = (r, c)
        else:
            r1, c1 = self.start_point
            r2, c2 = r, c
            self.start_point = None
            rmin, rmax = min(r1, r2), max(r1, r2)
            cmin, cmax = min(c1, c2), max(c1, c2)
            if tool == "rect_fill":
                for rr in range(rmin, rmax+1):
                    for cc in range(cmin, cmax+1):
                        self.set_color(rr, cc, self.selected_color)
            else:  # rect_outline
                for rr in range(rmin, rmax+1):
                    self.set_color(rr, cmin, self.selected_color)
                    self.set_color(rr, cmax, self.selected_color)
                for cc in range(cmin, cmax+1):
                    self.set_color(rmin, cc, self.selected_color)
                    self.set_color(rmax, cc, self.selected_color)

    # --- 塗りつぶし（再帰） ---
    def flood_fill(self, r, c, target_color, new_color):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return
        if self.colors[r][c] != target_color:
            return
        self.set_color(r, c, new_color)
        self.flood_fill(r+1, c, target_color, new_color)
        self.flood_fill(r-1, c, target_color, new_color)
        self.flood_fill(r, c+1, target_color, new_color)
        self.flood_fill(r, c-1, target_color, new_color)

    # --- 色設定 ---
    def set_color(self, r, c, color):
        self.colors[r][c] = color
        self.buttons[r][c].configure(bg=color)

    # --- PPM出力 ---
    def export_ppm(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".ppm",
                                                 filetypes=[("PPM files", "*.ppm")])
        if not file_path:
            return
        with open(file_path, "w") as f:
            f.write("P3\n")
            f.write(f"{self.cols} {self.rows}\n255\n")
            for r in range(self.rows):
                for c in range(self.cols):
                    hex_color = self.colors[r][c]
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
                    f.write(f"{rgb[0]} {rgb[1]} {rgb[2]} ")
                f.write("\n")
        print("PPM保存:", file_path)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("フル機能カラーボード")
    app = ColorGridApp(root)
    root.mainloop()
