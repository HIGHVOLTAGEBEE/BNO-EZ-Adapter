import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import time
import math

# ================= GLOBALS =================
ser = None
connected = False
data = []
status_text = "Nicht verbunden"
current_port = None
read_thread = None

# ================= SERIAL =================
def list_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

def connect():
    global ser, connected, current_port, read_thread
    
    port = port_combo.get()
    if not port:
        status_text = "Kein Port ausgewählt!"
        label.config(text=status_text)
        return
    
    try:
        baud = int(baud_entry.get())
        ser = serial.Serial(port, baud, timeout=1)
        connected = True
        current_port = port
        
        # Thread starten
        read_thread = threading.Thread(target=read_serial, daemon=True)
        read_thread.start()
        
        status_text = f"Verbunden mit {port}"
        connect_btn.config(text="DISCONNECT", command=disconnect)
        port_combo.config(state="disabled")
        
    except Exception as e:
        status_text = f"Fehler: {str(e)}"
    
    label.config(text=status_text)

def disconnect():
    global ser, connected
    connected = False
    if ser:
        ser.close()
        ser = None
    status_text = "Getrennt"
    label.config(text=status_text)
    connect_btn.config(text="CONNECT", command=connect)
    port_combo.config(state="readonly")

def refresh_ports():
    ports = list_ports()
    port_combo['values'] = ports
    if ports and not connected:
        port_combo.set(ports[0])

def read_serial():
    global status_text
    while connected and ser:
        try:
            line = ser.readline().decode(errors='ignore').strip()
            if line.startswith("H:"):
                parts = line.split()
                h = int(parts[0].split(":")[1])
                r = float(parts[1].split(":")[1])
                z = float(parts[2].split(":")[1])
                s = parts[3].split(":")[1]
                
                data.append(h)
                if len(data) > 200:
                    data.pop(0)
                
                status_text = f"Heading: {h}° | Raw: {r:.1f} | Zero: {z:.1f} | Status: {s}"
        except:
            pass

# ================= ZERO / RESET =================
def send_zero():
    if connected and ser:
        ser.write(b"0\n")

def send_reset():
    if connected and ser:
        ser.write(b"r\n")

# ================= UI =================
root = tk.Tk()
root.title("ESP32 BNO085 Kompass Dashboard")
root.geometry("900x650")
root.configure(bg="#f0f0f0")

# --- Port Auswahl ---
port_frame = tk.Frame(root, bg="#f0f0f0")
port_frame.pack(pady=10)

tk.Label(port_frame, text="Port:", bg="#f0f0f0", font=("Arial", 12)).grid(row=0, column=0, padx=5)
port_combo = ttk.Combobox(port_frame, values=list_ports(), width=15, state="readonly")
port_combo.grid(row=0, column=1, padx=5)
if list_ports():
    port_combo.set(list_ports()[0])

tk.Label(port_frame, text="Baud:", bg="#f0f0f0", font=("Arial", 12)).grid(row=0, column=2, padx=5)
baud_entry = tk.Entry(port_frame, width=10, font=("Arial", 12))
baud_entry.grid(row=0, column=3, padx=5)
baud_entry.insert(0, "1000000")

connect_btn = ttk.Button(port_frame, text="CONNECT", command=connect)
connect_btn.grid(row=0, column=4, padx=10)

refresh_btn = ttk.Button(port_frame, text="↻", width=3, command=refresh_ports)
refresh_btn.grid(row=0, column=5, padx=5)

# --- Status ---
label = tk.Label(root, text=status_text, font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#333")
label.pack(pady=10)

# --- Buttons ---
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=5)

btn_zero = ttk.Button(btn_frame, text="ZERO SETZEN", command=send_zero)
btn_zero.grid(row=0, column=0, padx=10)

btn_reset = ttk.Button(btn_frame, text="RESET ZERO", command=send_reset)
btn_reset.grid(row=0, column=1, padx=10)

# ================= KOMPASS (Canvas) =================
compass_canvas = tk.Canvas(root, width=300, height=300, bg="white", highlightthickness=2, highlightbackground="#ccc")
compass_canvas.pack(pady=10)

def draw_compass():
    compass_canvas.delete("all")
    w, h = 300, 300
    cx, cy = w//2, h//2
    radius = 120
    
    # Kreis
    compass_canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, 
                               outline="black", width=3)
    
    # Himmelsrichtungen
    for angle, text in [(0, "N"), (90, "O"), (180, "S"), (270, "W")]:
        rad = math.radians(angle)
        x = cx + (radius-20) * math.sin(rad)
        y = cy - (radius-20) * math.cos(rad)
        compass_canvas.create_text(x, y, text=text, font=("Arial", 16, "bold"))
    
    # Skala (alle 30°)
    for i in range(0, 360, 30):
        rad = math.radians(i)
        x1 = cx + radius * math.sin(rad)
        y1 = cy - radius * math.cos(rad)
        x2 = cx + (radius-10) * math.sin(rad)
        y2 = cy - (radius-10) * math.cos(rad)
        compass_canvas.create_line(x1, y1, x2, y2, width=2)
    
    # Nadel
    if data:
        heading = data[-1]
        rad = math.radians(heading)
        # Nadelspitze (rot)
        x_tip = cx + (radius-30) * math.sin(rad)
        y_tip = cy - (radius-30) * math.cos(rad)
        # Nadelende (grau)
        x_end = cx - (radius-30) * math.sin(rad) * 0.3
        y_end = cy + (radius-30) * math.cos(rad) * 0.3
        
        compass_canvas.create_line(cx, cy, x_tip, y_tip, fill="red", width=4, arrow=tk.LAST)
        compass_canvas.create_line(cx, cy, x_end, y_end, fill="gray", width=2)
        
        # Heading-Text in Mitte
        compass_canvas.create_text(cx, cy+40, text=f"{heading}°", font=("Arial", 20, "bold"), fill="red")

# ================= GRAPH (Canvas) =================
graph_canvas = tk.Canvas(root, width=760, height=200, bg="white", highlightthickness=1)
graph_canvas.pack(pady=10)

def draw_graph():
    graph_canvas.delete("all")
    if len(data) < 2:
        return
    
    w, h = 760, 200
    padding = 30
    
    # Achsen
    graph_canvas.create_line(padding, h-padding, w-padding, h-padding, fill="black", width=2)
    graph_canvas.create_line(padding, padding, padding, h-padding, fill="black", width=2)
    
    # Labels
    graph_canvas.create_text(w//2, h-10, text="Zeit →", font=("Arial", 10))
    graph_canvas.create_text(15, h//2, text="°", font=("Arial", 10), angle=90)
    
    # Grid
    for y in range(0, 361, 90):
        py = h - padding - (y / 360) * (h - 2*padding)
        graph_canvas.create_line(padding, py, w-padding, py, fill="#ddd", dash=(2,2))
        graph_canvas.create_text(padding-15, py, text=str(y), font=("Arial", 9), anchor="e")
    
    # Datenlinie
    step = (w - 2*padding) / max(len(data), 1)
    for i in range(len(data)-1):
        x1 = padding + i * step
        y1 = h - padding - (data[i] / 360) * (h - 2*padding)
        x2 = padding + (i+1) * step
        y2 = h - padding - (data[i+1] / 360) * (h - 2*padding)
        graph_canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)

# ================= UPDATE LOOP =================
def update():
    label.config(text=status_text)
    draw_compass()
    draw_graph()
    root.after(50, update)

update()
root.mainloop()