import logging
import os
import shlex
import tkinter as tk
from tkinter import ttk

from get_token import get_token
from main import MyClient
import threading

class Colors:
    # Define color codes
    BG_COLOR = "#2e2e2e"  # Background color
    FG_COLOR = "#ffffff"  # Foreground color
    WHITE = "#ffffff"  # White
    BLACK = "#000000"  # Black
    ENTRY_BG_COLOR = "#3e3e3e"  # Entry background color
    ENTRY_FG_COLOR = "#cccccc"  # Entry foreground color
    DISABLED_COLOR = "#888888"  # Disabled color


class ToolTip(object):
    def __init__(self, widget, text="widget info"):
        self.waittime = 500  # milliseconds before popup appears
        self.wraplength = 180  # pixels before text wraps
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(
            self.tw,
            text=self.text,
            justify="left",
            background=Colors.WHITE,
            foreground=Colors.BLACK,
            relief="solid",
            borderwidth=1,
            wraplength=self.wraplength,
        )
        label.pack(ipadx=4, ipady=4)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


def get_arguments():
    def center_window(root, width=350, height=475):
        # Get screen width and height
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate position x, y
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        root.geometry("%dx%d+%d+%d" % (width, height, x, y))

    def toggle_token_entry(*args):
        if get_token_var.get():
            # Disable the token entry field if the checkbox is checked
            token_entry.config(state="disabled")
            token_label.configure(foreground=Colors.DISABLED_COLOR)
            submit_button.config(text="Next")

        else:
            # Enable the token entry field and label if the checkbox is unchecked
            token_entry.config(state="normal")
            token_label.configure(foreground=entry_fg_color)
            submit_button.config(text="Submit")

    def on_submit():
        args["sleep_time"] = (
            float(sleep_time_entry.get()) if sleep_time_entry.get() else 2.0
        )
        args["output_verbosity"] = output_verbosity_var.get()
        args["loglevel"] = loglevel_var.get()
        args["print_info"] = print_info_var.get()
        args["write_to_json"] = write_to_json_var.get()
        args["output_path"] = (
            output_path_entry.get() if output_path_entry.get() else "output/"
        )
        args["include_servers"] = (
            shlex.split(include_servers_entry.get())
            if include_servers_entry.get()
            else []
        )
        args["get_token"] = get_token_var.get()

        if not args.get("get_token"):
            args["token"] = token_entry.get()

        root.destroy()

    root = tk.Tk()
    root.title("Discord-Mutual-Servers-and-Friends")
    center_window(root)
    root.minsize(350, 475)
    root.resizable(True, True)

    if tk.TkVersion >= 8.6:
        root.iconphoto(True, tk.PhotoImage(file="icon.png"))  # For Linux
    else:
        root.iconbitmap(default="icon.ico")  # For Windows

    args = {}

    # Create a custom dark theme
    style = ttk.Style()

    # Configure the root window background
    root.configure(bg=Colors.BG_COLOR)  # A lighter shade compared to #1e1e1e
    style.configure("TFrame", background=Colors.BG_COLOR)
    style.configure(
        "TLabel",
        foreground=Colors.FG_COLOR,
        background=Colors.BG_COLOR,
        font=("Helvetica", 12),
    )
    style.configure(
        "TCheckbutton",
        foreground=Colors.BG_COLOR,
        background=Colors.BG_COLOR,
        font=("Helvetica", 12),
    )
    style.configure(
        "TButton",
        foreground=Colors.BLACK,
        background=Colors.ENTRY_BG_COLOR,
        font=("Helvetica", 12),
    )

    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True, fill="both")

    # Spacers for vertical centering
    spacer_top = ttk.Frame(main_frame)
    spacer_top.pack(side="top", fill="both", expand=True)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(pady=5)  # Adjust this value as needed for your layout
    spacer_bottom = ttk.Frame(main_frame)
    spacer_bottom.pack(side="bottom", fill="both", expand=True)

    # Set colors for entry widgets to match Discord's dark theme
    entry_bg_color = Colors.ENTRY_BG_COLOR  # Dark gray
    entry_fg_color = Colors.ENTRY_FG_COLOR  # Light gray for text

    sleep_time_frame = ttk.Frame(content_frame)
    sleep_time_frame.pack(pady=5)
    ttk.Label(
        sleep_time_frame,
        text="Enter sleep time:",
        background=Colors.BG_COLOR,
        foreground=Colors.FG_COLOR,
    ).pack(side="left", padx=5)
    sleep_time_entry = tk.Entry(
        sleep_time_frame,
        bg=entry_bg_color,
        fg=entry_fg_color,
        insertbackground=entry_fg_color,
    )
    sleep_time_entry.insert(0, "2.0")
    sleep_time_entry.pack(side="left", fill="x", padx=(5, 0))
    question_mark_sleep_time = ttk.Label(
        sleep_time_frame,
        text=" ?",
        foreground=Colors.FG_COLOR,
        cursor="hand2",
        background=Colors.BG_COLOR,
    )
    question_mark_sleep_time.pack(side="left")
    ToolTip(
        question_mark_sleep_time,
        "How long to sleep between each member request. With values lower than 2, rate limits tend to be hit, which may lead to a ban. Increase if you hit a rate limit.",
    )

    print_info_frame = ttk.Frame(content_frame)
    print_info_frame.pack(pady=5)
    ttk.Label(print_info_frame, text="Print info:").pack(side="left")
    print_info_var = tk.BooleanVar(value=True)  # Default checked
    ttk.Checkbutton(print_info_frame, text="", variable=print_info_var).pack(
        side="left"
    )
    question_mark_print_info = ttk.Label(
        print_info_frame, text=" ?", foreground=Colors.FG_COLOR, cursor="hand2"
    )
    question_mark_print_info.pack(side="left")
    ToolTip(
        question_mark_print_info,
        "If true, the server info, mutual friends, and mutual servers are printed to the command line.",
    )

    write_to_json_frame = ttk.Frame(content_frame)
    write_to_json_frame.pack(pady=5)
    ttk.Label(write_to_json_frame, text="Write to JSON:").pack(side="left")
    write_to_json_var = tk.BooleanVar(value=True)  # Default checked
    ttk.Checkbutton(write_to_json_frame, text="", variable=write_to_json_var).pack(
        side="left"
    )
    question_mark_write_to_json = ttk.Label(
        write_to_json_frame, text=" ?", foreground=Colors.FG_COLOR, cursor="hand2"
    )
    question_mark_write_to_json.pack(side="left")
    ToolTip(
        question_mark_write_to_json,
        "If true, the server info, mutual friends, and mutual servers are written to json files.",
    )

    output_path_frame = ttk.Frame(content_frame)
    output_path_frame.pack(pady=5)
    ttk.Label(
        output_path_frame,
        text="Enter output path:",
        background=Colors.BG_COLOR,
        foreground=Colors.FG_COLOR,
    ).pack(side="left", padx=5)
    output_path_entry = tk.Entry(
        output_path_frame,
        bg=entry_bg_color,
        fg=entry_fg_color,
        insertbackground=entry_fg_color,
    )
    output_path_entry.pack(side="left", expand=True, fill="x", padx=(5, 0))
    question_mark_output_path = ttk.Label(
        output_path_frame,
        text="?",
        foreground=Colors.FG_COLOR,
        background=Colors.BG_COLOR,
        cursor="hand2",
    )
    question_mark_output_path.pack(side="left", padx=(5, 0))
    ToolTip(
        question_mark_output_path,
        "Specify the directory where output files will be saved.",
    )

    # For "Enter servers to include"
    servers_include_frame = ttk.Frame(content_frame)
    servers_include_frame.pack(pady=5)
    ttk.Label(
        servers_include_frame,
        text="Enter servers to include:",
        background=Colors.BG_COLOR,
        foreground=Colors.FG_COLOR,
    ).pack(side="left", padx=5)
    include_servers_entry = tk.Entry(
        servers_include_frame,
        bg=entry_bg_color,
        fg=entry_fg_color,
        insertbackground=entry_fg_color,
    )
    include_servers_entry.pack(side="left", expand=True, fill="x", padx=(5, 0))
    question_mark_servers_include = ttk.Label(
        servers_include_frame,
        text="?",
        foreground=Colors.FG_COLOR,
        background=Colors.BG_COLOR,
        cursor="hand2",
    )
    question_mark_servers_include.pack(side="left", padx=(5, 0))
    ToolTip(
        question_mark_servers_include,
        "Only process servers whose names are in this list. If not specified, process all servers. Put server names with mutltiple words in quotes.",
    )

    output_verbosity_options = [1, 2, 3]
    verbosity_label_frame = ttk.Frame(content_frame)
    verbosity_label_frame.pack(pady=(5, 0))
    ttk.Label(
        verbosity_label_frame,
        text="Select output verbosity:",
        background=Colors.BG_COLOR,
        foreground=Colors.FG_COLOR,
    ).pack(side="left", padx=(0, 5))
    question_mark_verbosity = ttk.Label(
        verbosity_label_frame,
        text="?",
        foreground=Colors.FG_COLOR,
        background=Colors.BG_COLOR,
        cursor="hand2",
    )
    question_mark_verbosity.pack(side="left")
    ToolTip(
        question_mark_verbosity,
        "How much information to be included in the mutual friends and mutual servers files. 1 means just the member name. 2 means the member name and a count the member's of mutual friends or mutual servers. 3 means the member name and a list of the member's mutual friends or mutual servers.",
    )
    output_verbosity_options = [1, 2, 3]
    output_verbosity_var = tk.IntVar(value=2)  # Default value
    ttk.OptionMenu(content_frame, output_verbosity_var, *output_verbosity_options).pack(
        pady=5
    )

    loglevel_label_frame = ttk.Frame(content_frame)
    loglevel_label_frame.pack(pady=(5, 0))
    ttk.Label(
        loglevel_label_frame,
        text="Select log level:",
        background=Colors.BG_COLOR,
        foreground=Colors.FG_COLOR,
    ).pack(side="left", padx=(0, 5))
    question_mark_loglevel = ttk.Label(
        loglevel_label_frame,
        text="?",
        foreground=Colors.FG_COLOR,
        background=Colors.BG_COLOR,
        cursor="hand2",
    )
    question_mark_loglevel.pack(side="left")
    ToolTip(question_mark_loglevel, "Provide logging level.")
    loglevel_options = ["debug", "info", "warn", "warning", "error", "critical"]
    loglevel_var = tk.StringVar(value="info")  # Default value
    ttk.OptionMenu(content_frame, loglevel_var, *loglevel_options).pack(pady=5)

    get_token_var = tk.BooleanVar()
    get_token_frame = ttk.Frame(content_frame)
    get_token_frame.pack(pady=5)
    ttk.Label(get_token_frame, text="Get Token:").pack(side="left")
    ttk.Checkbutton(
        get_token_frame, text="", variable=get_token_var, command=toggle_token_entry
    ).pack(side="left")
    question_mark_get_token = ttk.Label(
        get_token_frame, text="?", foreground=Colors.FG_COLOR, cursor="hand2"
    )
    question_mark_get_token.pack(side="left")
    ToolTip(
        question_mark_get_token,
        "If set, will run the get_token script to get a token",
    )

    token_label = ttk.Label(content_frame, text="Enter your token")
    token_entry = tk.Entry(
        content_frame,
        bg=entry_bg_color,
        fg=entry_fg_color,
        insertbackground=entry_fg_color,
    )
    style = ttk.Style()
    style.configure(
        "Custom.TButton", foreground=Colors.FG_COLOR, background=Colors.BG_COLOR
    )

    token_label.pack(pady=5)
    token_entry.pack(pady=5)

    submit_button = ttk.Button(
        content_frame,
        text="Submit",
        command=on_submit,
        style="Custom.TButton",
    )

    submit_button.pack(pady=10)

    toggle_token_entry()

    root.mainloop()
    return args

class LoadingScreen:
    def __init__(self):
        self.root = tk.Tk()  # Changed back to Tk() to make it the primary window
        self.root.title("Loading")
        self.configure_window()
        self.add_loading_message()
        self.root.withdraw()  # Initially hide the window
        self.configure_styles()  # Configure styles for the UI

    def configure_window(self):
        self.root.geometry("350x475")  # Window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (350/2)
        y = (screen_height / 2) - (475/2)
        self.root.geometry(f"+{int(x)}+{int(y)}")
        self.root.configure(bg=Colors.BG_COLOR)  # Set the window background color

    def add_loading_message(self):
        # Store the label in an attribute so it can be updated later
        self.message_label = tk.Label(self.root, text="Loading, please wait...", bg=Colors.BG_COLOR, fg=Colors.FG_COLOR)
        self.message_label.pack(expand=True)

    def configure_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background=Colors.BG_COLOR)
        style.configure("TLabel", foreground=Colors.FG_COLOR, background=Colors.BG_COLOR, font=("Helvetica", 12))
        style.configure("TCheckbutton", foreground=Colors.BG_COLOR, background=Colors.BG_COLOR, font=("Helvetica", 12))
        style.configure("TButton", foreground=Colors.BLACK, background=Colors.ENTRY_BG_COLOR, font=("Helvetica", 12))

    def show(self):
        self.root.deiconify()  # Show the window

    def close(self):
        self.root.destroy()  # Close the windo    
        

    def update_message(self, message, fg_color=Colors.FG_COLOR):
            self.message_label.config(text=message, fg=fg_color)  # Update the label with the new message and foreground color


def run_client(args, loading_screen):
    try:
        client = MyClient(
            sleep_time=args["sleep_time"],
            output_verbosity=args["output_verbosity"],
            print_info=args["print_info"],
            write_to_json=args["write_to_json"],
            output_path=args["output_path"],
            include_servers=args["include_servers"],
        )
        client.run(args["token"])
    except Exception as e:
        loading_screen.update_message("Token validation failed.", Colors.FG_COLOR)
        # Optionally log the exception or perform other error handling here
        print(f"Error running client: {e}")
    finally:
        # Ensure the loading screen is closed only if the client runs successfully
        loading_screen.close()  # Close the loading screen
        

def on_client_complete():
    # Now, initiate the JSON viewer window
    json_viewer_root = tk.Tk()  # Start a new Tkinter instance for the JSON viewer
    json_files = [os.path.join(output_path, f) for f in os.listdir(output_path) if f.endswith('.json')]
    JsonViewer(json_viewer_root, json_files)
    json_viewer_root.mainloop()  # Start the Tkinter loop for the JSON viewer

class JsonViewer:
    def __init__(self, master, files):
        self.master = master
        self.master.title("JSON File Viewer")
        self.files = files
        self.configure_window()
        self.create_widgets()
        self.configure_styles()
    
    def configure_window(self):
        # Similar geometry and background configuration as LoadingScreen
        self.master.geometry("350x475")  # Adjust the size as needed
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width / 2) - (350/2)  # Adjust the offset as needed
        y = (screen_height / 2) - (475/2)  # Adjust the offset as needed
        self.master.geometry(f"+{int(x)}+{int(y)}")
        self.master.configure(bg=Colors.BG_COLOR)  # Use the same background color
    
    def configure_styles(self):
        # Apply similar styles for consistency
        style = ttk.Style()
        style.configure("TFrame", background=Colors.BG_COLOR)
        style.configure("TLabel", foreground=Colors.FG_COLOR, background=Colors.BG_COLOR, font=("Helvetica", 12))
        style.configure("TButton", foreground=Colors.BLACK, background=Colors.ENTRY_BG_COLOR, font=("Helvetica", 12))
        # For Text widget, which doesn't use ttk.Style, configure directly
        self.text.config(bg=Colors.BG_COLOR, fg=Colors.FG_COLOR, font=("Helvetica", 12))

    def create_widgets(self):
        # Create a frame to contain the text widget and scrollbars
        text_frame = tk.Frame(self.master, bg=Colors.BG_COLOR)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Create the text widget with scrollbars inside the frame
        self.text = tk.Text(text_frame, wrap=tk.NONE, width=80, height=20, 
                            bg=Colors.BG_COLOR, fg=Colors.FG_COLOR, font=("Helvetica", 12),
                            xscrollcommand=lambda *args: h_scrollbar.set(*args),
                            yscrollcommand=lambda *args: v_scrollbar.set(*args))
        self.text.grid(row=0, column=0, sticky='nsew')  # Use grid for better control

        # Vertical scrollbar
        v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text.yview)
        v_scrollbar.grid(row=0, column=1, sticky='ns')

        # Horizontal scrollbar
        h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text.xview)
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid row/column weights in the frame
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Insert JSON file content
        for file_path in self.files:
            with open(file_path, 'r') as file:
                content = file.read()
                self.text.insert(tk.END, f"File: {file_path}\n{content}\n\n")

if __name__ == "__main__":
    # Set the default output path and initialize logging
    output_path = os.path.dirname(os.path.realpath(__file__)) + "/output/"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    args = get_arguments()  # This needs to be adjusted to actually return args from the UI
    if args.get("get_token", False):
        args["token"] = get_token()
    logging.basicConfig(level=args["loglevel"].upper())
    if "TOKEN" in os.environ:
        del os.environ["TOKEN"]

    # Show the loading screen
    loading_screen = LoadingScreen()
    loading_screen.show()

    # Start the client in a background thread
    client_thread = threading.Thread(target=run_client, args=(args, loading_screen))
    client_thread.start()

    # Start the Tkinter loop for the loading screen
    loading_screen.root.mainloop()
    on_client_complete()
