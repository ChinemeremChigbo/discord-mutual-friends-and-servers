import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import tkinter as tk
from tkinter import ttk

import subprocess
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_username_password():
    def center_window(root, width=350, height=475):
        # Get screen width and height
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate position x, y
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        root.geometry("%dx%d+%d+%d" % (width, height, x, y))

    def go_back():
        # Adjust the path to ui.py if necessary using resource_path
        ui_path = resource_path("ui.py")
        # Run ui.py and close the current window
        subprocess.Popen(['python', ui_path])
        sys.exit()  # Exit the script

    def submit():
        # Retrieve entered values
        username_var.set(username_entry.get())
        password_var.set(password_entry.get())
        # Signal the main loop to continue and close the window
        root.destroy()

    # Initialize the main window
    root = tk.Tk()
    root.title("Get Token")

    center_window(root)  # Set the size of the window

    # Set minimum size
    root.minsize(350, 475)

    root.resizable(True, True)

    if tk.TkVersion >= 8.6:
        icon_path = resource_path("icon.png")  # Use resource_path to get the correct path
        root.iconphoto(True, tk.PhotoImage(file=icon_path))  # For Linux and newer versions of Windows
    else:
        icon_path = resource_path("icon.ico")  # Use resource_path to get the correct path
        root.iconbitmap(default=icon_path)  # For older versions of Windows

    # Apply lighter Discord theme colors
    style = ttk.Style()
    root.configure(bg="#2e2e2e")  # Discord-like background color
    style.configure("TFrame", background="#2e2e2e")
    style.configure(
        "TLabel", foreground="#FFFFFF", background="#2e2e2e", font=("Helvetica", 12)
    )
    style.configure(
        "TCheckbutton",
        foreground="#FFFFFF",
        background="#2e2e2e",
        font=("Helvetica", 12),
    )
    style.configure(
        "TButton", foreground="#000000", background="#4e4e4e", font=("Helvetica", 12)
    )

    # Main frame for content
    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True, fill="both")

    # Spacers for vertical centering
    spacer_top = ttk.Frame(main_frame)
    spacer_top.pack(side="top", fill="both", expand=True)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(pady=20)  # This frame holds the actual content
    spacer_bottom = ttk.Frame(main_frame)
    spacer_bottom.pack(side="bottom", fill="both", expand=True)

    # Variables to hold credentials
    username_var = tk.StringVar()
    password_var = tk.StringVar()

    ttk.Label(
        content_frame, text="Email:", background="#2e2e2e", foreground="#FFFFFF"
    ).pack()
    username_entry = ttk.Entry(
        content_frame,
        background="#3e3e3e",
        foreground="#cccccc",
        # insertbackground="#cccccc",
        width=40,
    )
    username_entry.pack(pady=(5, 10), padx=5)

    ttk.Label(
        content_frame, text="Password:", background="#2e2e2e", foreground="#FFFFFF"
    ).pack()
    password_entry = ttk.Entry(
        content_frame,
        show="*",
        background="#3e3e3e",
        foreground="#cccccc",
        # insertbackground="#cccccc",
        width=40,
    )
    password_entry.pack(pady=(5, 10), padx=5)

    style = ttk.Style()
    style.configure("Custom.TButton", foreground="#FFFFFF", background="#2e2e2e")

    submit_btn = ttk.Button(
        content_frame,
        text="Submit",
        command=submit,
        style="Custom.TButton",
    )

    submit_btn.pack()

    # Add a "Back" button
    back_btn = ttk.Button(
        content_frame,
        text="Back",
        command=go_back,  # Bind the go_back function to the button
        style="Custom.TButton",
    )
    back_btn.pack(pady=(0, 20))

    root.mainloop()

    # After the window is closed, check if the variables were set
    if username_var.get() and password_var.get():
        return username_var.get(), password_var.get()
    else:
        # If the function reaches this point without valid inputs,
        # it means the user closed the window without entering credentials.
        # You can handle this case as needed, for example:
        print("No credentials entered. Exiting...")
        exit()  # Exit the script


def get_token():
    username, password = get_username_password()

    chrome_options = webdriver.ChromeOptions()

    # Initialize the Chrome driver with the options
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://discord.com/login")
    time.sleep(3)

    username_input = driver.find_element(By.NAME, "email")
    username_input.send_keys(username)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)

    # click login button
    driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
    time.sleep(15)
    token = ""

    try:
        # Trigger the JavaScript command that opens the alert
        driver.execute_script(
            "alert((webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken())"
        )

        # Wait for the alert to be present
        WebDriverWait(driver, 10).until(EC.alert_is_present())

        # Switch to the alert
        alert = driver.switch_to.alert

        # Get the text from the alert
        token = alert.text
        

        # You can now accept the alert to close it
        alert.accept()

    except Exception as e:
        print("An error occurred: ", e)

    driver.close()
    return token
