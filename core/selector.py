import tkinter as tk

def select_region():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.25)
    root.config(bg="black")
    root.overrideredirect(1)
    root.attributes("-topmost", True)
    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    x1 = y1 = x2 = y2 = 0
    rect = None

    def on_press(e):
        nonlocal x1, y1, rect
        x1, y1 = e.x_root, e.y_root
        rect = canvas.create_rectangle(x1, y1, x1, y1, outline="red", width=2)

    def on_drag(e):
        canvas.coords(rect, x1, y1, e.x_root, e.y_root)

    def on_release(e):
        nonlocal x2, y2
        x2, y2 = e.x_root, e.y_root
        root.quit()

    root.bind("<ButtonPress-1>", on_press)
    root.bind("<B1-Motion>", on_drag)
    root.bind("<ButtonRelease-1>", on_release)
    root.mainloop()
    root.destroy()
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)