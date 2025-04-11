import requests
import re
import os
import base64
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import pystray
from PIL import Image, ImageDraw
import csv
import os
from dotenv import load_dotenv

# -------------------- Configuration --------------------
# Threshold values for evaluation
MALICIOUS_THRESHOLD = 1
SUSPICIOUS_THRESHOLD = 1
UNDETECTED_THRESHOLD = 10
HARMLESS_THRESHOLD = 50
TIMEOUT_THRESHOLD = 1

# API URLs
MICROSOFT_GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"
VIRUSTOTAL_API_URL = "https://www.virustotal.com/api/v3/urls"
VIRUSTOTAL_API_FILE = "https://www.virustotal.com/api/v3/files"

# Global tray icon variable (used by tray functions)
tray_icon = None

# -------------------- API Functions --------------------
def get_emails(access_token):
    headers = {"Authorization": access_token, "Content-Type": "application/json"}
    response = requests.get(MICROSOFT_GRAPH_API_URL, headers=headers)
    return response.json()

def extract_attachments(email, access_token):
    headers = {"Authorization": access_token, "Content-Type": "application/json"}
    attachments_url = f"{MICROSOFT_GRAPH_API_URL}/{email['id']}/attachments"
    attachments = requests.get(attachments_url, headers=headers).json()
    file_paths = []
    for attachment in attachments.get("value", []):
        decoded_content = base64.b64decode(attachment["contentBytes"])
        file_path = attachment["name"]
        with open(file_path, "wb") as file:
            file.write(decoded_content)
        file_paths.append(file_path)
    return attachments.get("value", []), file_paths

def extract_urls(email_body):
    # A simple URL extraction regex
    return re.findall(r"http[s]?://[^\s]+", email_body)

def analyze_file(attachment, api_key):
    files = {"file": (attachment["name"], open(attachment["name"], "rb"), attachment["contentType"])}
    headers = {"accept": "application/json", "x-apikey": api_key}
    response1 = requests.post(VIRUSTOTAL_API_FILE, files=files, headers=headers)
    analyze = response1.json().get("data", {}).get("links", {}).get("self")
    response2 = requests.get(analyze, headers=headers)
    return response2.json()["data"]["attributes"]["stats"]

def analyze_url(url, api_key):
    payload = {"url": url}
    headers = {"accept": "application/json", "x-apikey": api_key, "content-type": "application/x-www-form-urlencoded"}
    response1 = requests.post(VIRUSTOTAL_API_URL, data=payload, headers=headers)
    if response1.status_code != 200:
        return None
    analyze = response1.json().get("data", {}).get("links", {}).get("self")
    if not analyze:
        return None
    response2 = requests.get(analyze, headers={"accept": "application/json", "x-apikey": api_key})
    return response2.json()["data"]["attributes"]["stats"] if response2.status_code == 200 else None

def send_junk(email, access_token):
    url = f"{MICROSOFT_GRAPH_API_URL}/{email['id']}/move"
    headers = {"Authorization": access_token, "Content-Type": "application/json"}
    data = {"destinationId": find_folder("Junk Email", access_token)}
    requests.post(url, headers=headers, json=data)

def find_folder(foldername, access_token):
    url = "https://graph.microsoft.com/v1.0/me/mailFolders"
    headers = {"Authorization": access_token, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    folders = response.json().get("value", [])
    for folder in folders:
        if folder.get("displayName") == foldername:
            return folder.get("id")
    return None

def eval_result(result):
    if result is None:
        return True
    return not (result["malicious"] > MALICIOUS_THRESHOLD or
                result["suspicious"] > SUSPICIOUS_THRESHOLD)

# -------------------- Tray Icon Functions --------------------
def create_image():
    image = Image.new("RGB", (64, 64), color="black")
    dc = ImageDraw.Draw(image)
    dc.rectangle((10, 10, 54, 54), fill="white")
    return image

def show_window(icon, item):
    global tray_icon
    if tray_icon:
        tray_icon.stop()
    root.event_generate("<<ShowWindow>>", when="tail")

def quit_app(icon, item):
    global tray_icon
    if tray_icon:
        tray_icon.stop()
    root.event_generate("<<QuitApp>>", when="tail")

def run_tray():
    try:
        tray_icon.run()
    except OSError as e:
        print("Tray icon error:", e)

# -------------------- GUI Classes --------------------
class LoginWindow:
    def __init__(self, win, on_login_success):
        self.win = win
        self.win.title("Login to Email Scanner")
        self.win.geometry("400x200")
        self.on_login_success = on_login_success

        tk.Label(win, text="VirusTotal API Key:").pack(pady=5)
        self.api_key_entry = tk.Entry(win, show="*")
        self.api_key_entry.pack(pady=5)

        tk.Label(win, text="Microsoft Graph Access Token:").pack(pady=5)
        self.access_token_entry = tk.Entry(win, show="*")
        self.access_token_entry.pack(pady=5)

        tk.Button(win, text="Login", command=self.login).pack(pady=10)

    def login(self):
        load_dotenv()
        api_key = os.getenv('VIRUSTOTAL_API_KEY')
        access_token = os.getenv('MICROSOFT_ACCESS_TOKEN')
    

        if not api_key:
            api_key = self.api_key_entry.get().strip()
        if not access_token:
            access_token = self.access_token_entry.get().strip()        
        if not api_key or not access_token:
            messagebox.showerror("Error", "Please enter both API Key and Access Token")
            return
        self.win.destroy()
        self.on_login_success(api_key, access_token)

class EmailScannerApp:
    def __init__(self, win, api_key, access_token):
        self.win = win
        self.api_key = api_key
        self.access_token = access_token
        self.win.title("Email Scanner")
        self.win.geometry("1200x750")

        # Buttons frame at the top
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=5, fill="x")
        self.scan_button = tk.Button(btn_frame, text="Scan Emails", command=self.start_scan)
        self.scan_button.pack(side="left", padx=5)
        self.export_button = tk.Button(btn_frame, text="Export to CSV", command=self.save_to_csv)
        self.export_button.pack(side="left", padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(win, mode="indeterminate")
        self.progress.pack(pady=5, fill="x")

        # Table for email results
        self.tree = ttk.Treeview(win, columns=("Email ID", "Email Link", "Sender", "Subject", "Detected URL", "Safety Status", "Action Taken"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(pady=10, fill="both", expand=True)

        # Create a figure with two subplots: bar chart and pie chart
        self.fig, (self.ax_bar, self.ax_pie) = plt.subplots(1, 2, figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=win)
        self.canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

        self.schedule_scan(initial=True)

    def schedule_scan(self, initial=False):
        delay = 0 if initial else 300000  # 300,000 ms = 5 minutes
        self.win.after(delay, self.start_scan)

    def start_scan(self):
        self.progress.start(10)
        threading.Thread(target=self.scan_emails, daemon=True).start()

    def scan_emails(self):
        try:
            self.win.after(0, lambda: self.tree.delete(*self.tree.get_children()))
            self.win.after(0, self.ax_bar.clear)
            self.win.after(0, self.ax_pie.clear)

            emails = get_emails(self.access_token)
            safety_counts = {"Safe": 0, "Unsafe": 0, "Pending": 0}

            for email in emails.get("value", []):
                dangerous = False
                detected_url = None
                result = None
                action = "No Action"

                sender = email.get("sender", {}).get("emailAddress", {}).get("name", "N/A")
                subject = email.get("subject", "N/A")

                if email.get("hasAttachments", False):
                    attachments, file_paths = extract_attachments(email, self.access_token)
                    for attachment in attachments:
                        result = analyze_file(attachment, self.api_key)
                        if not eval_result(result):
                            dangerous = True
                            action = "Moved to Junk Folder"
                            break
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            os.remove(file_path)

                urls = extract_urls(email.get("body", {}).get("content", ""))
                for url in urls:
                    detected_url = url
                    result = analyze_url(url, self.api_key)
                    if not eval_result(result):
                        dangerous = True
                        action = "Moved to Junk Folder"
                        break

                status = "Unsafe" if result is not None and not eval_result(result) else "Safe" if result else "Pending"
                if result is None and urls:
                    action = "Analysis Interrupted"

                short_id = email["id"][:40] + "..." if len(email["id"]) > 40 else email["id"]
                # Insert into the table; use default lambda parameters to capture values properly
                self.win.after(0, lambda e=short_id, l=email.get("webLink", "N/A"), s=sender, su=subject,
                                       du=detected_url or "None", st=status, a=action:
                               self.tree.insert("", "end", values=(e, l, s, su, du, st, a)))

                if dangerous:
                    send_junk(email, self.access_token)

                if status == "Safe":
                    safety_counts["Safe"] += 1
                elif status == "Unsafe":
                    safety_counts["Unsafe"] += 1
                else:
                    safety_counts["Pending"] += 1

            def update_chart():
                self.ax_bar.clear()
                self.ax_pie.clear()

                labels = list(safety_counts.keys())
                values = list(safety_counts.values())
                colors = ["green", "red", "gray"]

                # Bar Chart with legend
                bars = self.ax_bar.bar(labels, values, color=colors)
                # Add legend using the labels
                self.ax_bar.legend(bars, labels)
                self.ax_bar.set_title("Bar Chart - Email Safety")
                self.ax_bar.set_xlabel("Status")
                self.ax_bar.set_ylabel("Count")

                # Pie Chart
                self.ax_pie.pie(values, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
                self.ax_pie.set_title("Pie Chart - Email Safety")

                self.fig.tight_layout()  # Adjust layout to prevent cropping
                self.canvas.draw()

            self.win.after(0, update_chart)
        finally:
            self.win.after(0, self.progress.stop)
            self.schedule_scan(initial=False)

    def save_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        with open(file_path, "w", newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Email ID", "Email Link", "Sender", "Subject", "Detected URL", "Safety Status", "Action Taken"])
            for child in self.tree.get_children():
                writer.writerow(self.tree.item(child)["values"])
        messagebox.showinfo("Export Successful", f"Data saved to {file_path}")

# -------------------- Main Execution --------------------
def start_app(api_key, access_token):
    global tray_icon
    # Create the main scanning window AFTER login
    root = tk.Tk()

    def on_closing():
        global tray_icon
        if root.state() == "withdrawn":
            return
        root.withdraw()
        tray_icon = pystray.Icon(
            "EmailScanner",
            create_image(),
            "Email Scanner",
            menu=pystray.Menu(
                pystray.MenuItem("Show", lambda icon, item: root.event_generate("<<ShowWindow>>")),
                pystray.MenuItem("Quit", lambda icon, item: root.event_generate("<<QuitApp>>"))
            )
        )
        threading.Thread(target=tray_icon.run, daemon=True).start()

    root.bind("<<ShowWindow>>", lambda e: root.deiconify())
    root.bind("<<QuitApp>>", lambda e: root.destroy())
    root.protocol("WM_DELETE_WINDOW", on_closing)

    EmailScannerApp(root, api_key, access_token)
    root.mainloop()

if __name__ == "__main__":
    # Start with only the login window
    login_root = tk.Tk()
    LoginWindow(login_root, start_app)
    login_root.mainloop()
