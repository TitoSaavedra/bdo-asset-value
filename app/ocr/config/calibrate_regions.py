import tkinter as tk
import mss
from PIL import Image, ImageTk
import os

OUTPUT_PATH = "app/ocr/config/regions.py"

REGION_KEYS = {
    "1": ("STORAGE_NAME_REGION", "Nombre del almacén"),
    "2": ("STORAGE_SILVER_REGION", "Valor del almacén"),
    "3": ("MARKET_SILVER_REGION", "Silver del mercado"),
    "4": ("INVENTORY_SILVER_REGION", "Silver del inventario"),
}

regions = {}


def capture_region(region_name, description):

    result = {}

    def on_press(event):
        nonlocal start_x, start_y, rect
        start_x = event.x
        start_y = event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="lime", width=2)

    def on_drag(event):
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_release(event):
        x1, y1 = start_x, start_y
        x2, y2 = event.x, event.y

        result["region"] = {
            "x": min(x1, x2),
            "y": min(y1, y2),
            "width": abs(x2 - x1),
            "height": abs(y2 - y1)
        }

        root.destroy()

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img = Image.frombytes("RGB", img.size, img.rgb)

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.overrideredirect(True)

    bg = ImageTk.PhotoImage(img)

    canvas = tk.Canvas(root, width=img.width, height=img.height, cursor="cross", highlightthickness=0)
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=bg)

    label = tk.Label(
        root,
        text=f"Selecciona: {description}",
        bg="black",
        fg="#00ff9c",
        font=("Segoe UI", 30, "bold"),
        padx=20,
        pady=10
    )

    label.place(relx=0.5, rely=0.05, anchor="n")

    start_x = start_y = 0
    rect = None

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()

    return result.get("region")


def save_regions():

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        for name, region in regions.items():

            f.write(f"{name} = {{\n")

            for k, v in region.items():
                f.write(f'    "{k}": {v},\n')

            f.write("}\n\n")


print("\nCALIBRADOR OCR BDO")
print("------------------")

while True:

    print("\n1 → Nombre almacén")
    print("2 → Valor almacén")
    print("3 → Silver mercado")
    print("4 → Silver inventario")
    print("s → Guardar")
    print("q → Salir")

    cmd = input("\nSelecciona opción: ").strip()

    if cmd in REGION_KEYS:

        name, desc = REGION_KEYS[cmd]

        print(f"\nDibuja la región para: {desc}")

        region = capture_region(name, desc)

        if region:
            regions[name] = region
            print(f"Guardado {name} → {region}")

    elif cmd.lower() == "s":

        save_regions()
        print("\nRegiones guardadas.")

    elif cmd.lower() == "q":

        break
