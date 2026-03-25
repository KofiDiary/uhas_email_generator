import customtkinter as ctk
from tkinter import messagebox, simpledialog
import database as db


class MappingManagerWindow(ctk.CTkToplevel):
    # Standalone top-level window for managing schools and their programmes
    # Opened from the main window via a button

    def __init__(self, parent):
        super().__init__(parent)
        self.title("School & Programme Manager")
        self.geometry("900x620")
        self.minsize(800, 550)
        self.resizable(True, True)

        # Keep this window on top of the parent
        self.transient(parent)
        self.grab_set()

        # Track currently selected school
        self._selected_school = None

        self._build_layout()
        self._load_schools()

        # Center window on screen after layout is built
        self.after(50, self._center_window)


    def _center_window(self):
        # Centers the window on the screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")


    # ─── LAYOUT ───

    def _build_layout(self):
        # Main layout: two side-by-side panels inside a content frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        self._build_school_panel(content)
        self._build_programme_panel(content)


    def _build_school_panel(self, parent):
        # Left panel: list of schools with add, rename, delete controls
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        # Panel header
        ctk.CTkLabel(
            panel,
            text="Schools",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        # Scrollable list of schools
        self._school_list_frame = ctk.CTkScrollableFrame(panel, label_text="")
        self._school_list_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._school_list_frame.grid_columnconfigure(0, weight=1)

        # Bottom action buttons
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 12))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Add School",
            width=90,
            command=self._on_add_school
        ).grid(row=0, column=0, padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Rename",
            width=90,
            fg_color="#2E86AB",
            hover_color="#1B6A8A",
            command=self._on_rename_school
        ).grid(row=0, column=1, padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            width=90,
            fg_color="#C0392B",
            hover_color="#A93226",
            command=self._on_delete_school
        ).grid(row=0, column=2, padx=4)


    def _build_programme_panel(self, parent):
        # Right panel: programmes for the selected school
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        # Panel header label (updates when a school is selected)
        self._prog_panel_label = ctk.CTkLabel(
            panel,
            text="Programmes  —  Select a school",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self._prog_panel_label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        # Add programme input row
        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        input_frame.grid_columnconfigure(0, weight=1)

        self._new_prog_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter new programme name...",
            height=36,
        )
        self._new_prog_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            input_frame,
            text="Add Programme",
            width=130,
            command=self._on_add_programme
        ).grid(row=0, column=1)

        # Scrollable programme list
        self._prog_list_frame = ctk.CTkScrollableFrame(panel, label_text="")
        self._prog_list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._prog_list_frame.grid_columnconfigure(0, weight=1)

        # Bottom status label
        self._prog_count_label = ctk.CTkLabel(
            panel,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self._prog_count_label.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 10))


    # ─── SCHOOL LIST RENDERING ───

    def _load_schools(self):
        # Fetches all schools from DB and renders them in the school list panel
        for widget in self._school_list_frame.winfo_children():
            widget.destroy()

        schools = db.get_all_schools()

        if not schools:
            ctk.CTkLabel(
                self._school_list_frame,
                text="No schools found. Add one below.",
                text_color="gray"
            ).grid(row=0, column=0, pady=12)
            return

        for i, school in enumerate(schools):
            self._render_school_row(i, school)

        # If a school was previously selected, try to re-select it
        if self._selected_school:
            still_exists = any(s["id"] == self._selected_school["id"] for s in schools)
            if not still_exists:
                self._selected_school = None
                self._clear_programme_panel()


    def _render_school_row(self, index, school):
        # Renders a single school row as a clickable button in the school list
        is_selected = (
            self._selected_school is not None and
            self._selected_school["id"] == school["id"]
        )

        btn = ctk.CTkButton(
            self._school_list_frame,
            text=f"{school['code'].upper()}  —  {school['name']}",
            anchor="w",
            fg_color="#1F4E79" if is_selected else "transparent",
            text_color="white" if is_selected else ("black", "white"),
            hover_color="#2E6DA4",
            border_width=1,
            border_color="#AAAAAA",
            height=38,
            command=lambda s=school: self._on_select_school(s)
        )
        btn.grid(row=index, column=0, sticky="ew", pady=2, padx=2)


    def _on_select_school(self, school):
        # Handles school selection and loads its programmes
        self._selected_school = school
        self._load_schools()
        self._load_programmes(school)


    # ─── PROGRAMME LIST RENDERING ────

    def _load_programmes(self, school):
        # Fetches and renders all programmes for the selected school
        self._prog_panel_label.configure(
            text=f"Programmes  —  {school['code'].upper()}"
        )

        for widget in self._prog_list_frame.winfo_children():
            widget.destroy()

        programmes = db.get_programmes_for_school(school["id"])
        self._prog_count_label.configure(
            text=f"{len(programmes)} programme(s) registered"
        )

        if not programmes:
            ctk.CTkLabel(
                self._prog_list_frame,
                text="No programmes yet. Add one above.",
                text_color="gray"
            ).grid(row=0, column=0, pady=12)
            return

        for i, prog in enumerate(programmes):
            self._render_programme_row(i, prog)


    def _render_programme_row(self, index, prog):
        # Renders a single programme row with a remove button
        row_frame = ctk.CTkFrame(self._prog_list_frame, fg_color="transparent")
        row_frame.grid(row=index, column=0, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            row_frame,
            text=prog["programme_name"],
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="ew", padx=(4, 8))

        ctk.CTkButton(
            row_frame,
            text="Remove",
            width=70,
            height=28,
            fg_color="#C0392B",
            hover_color="#A93226",
            font=ctk.CTkFont(size=11),
            command=lambda p=prog: self._on_remove_programme(p)
        ).grid(row=0, column=1)


    def _clear_programme_panel(self):
        # Resets the programme panel to its default empty state
        self._prog_panel_label.configure(text="Programmes  —  Select a school")
        for widget in self._prog_list_frame.winfo_children():
            widget.destroy()
        self._prog_count_label.configure(text="")


    # ─── SCHOOL ACTION HANDLERS ───

    def _on_add_school(self):
        # Opens a dialog to collect new school code and name then saves to DB
        dialog = _SchoolDialog(self, title="Add New School")
        self.wait_window(dialog)

        if dialog.result:
            code, name = dialog.result
            success, error = db.add_school(code, name)
            if success:
                self._load_schools()
            else:
                messagebox.showerror("Error", error, parent=self)


    def _on_rename_school(self):
        # Opens a dialog pre-filled with the selected school's details for editing
        if not self._selected_school:
            messagebox.showwarning("No Selection", "Please select a school first.", parent=self)
            return

        dialog = _SchoolDialog(
            self,
            title="Rename School",
            initial_code=self._selected_school["code"],
            initial_name=self._selected_school["name"],
        )
        self.wait_window(dialog)

        if dialog.result:
            code, name = dialog.result
            success, error = db.rename_school(self._selected_school["id"], code, name)
            if success:
                # Update selected school reference to reflect new values
                self._selected_school["code"] = code
                self._selected_school["name"] = name
                self._load_schools()
                if self._selected_school:
                    self._load_programmes(self._selected_school)
            else:
                messagebox.showerror("Error", error, parent=self)


    def _on_delete_school(self):
        # Confirms then deletes the selected school and all its programmes
        if not self._selected_school:
            messagebox.showwarning("No Selection", "Please select a school first.", parent=self)
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete school '{self._selected_school['code'].upper()}' and all its programmes?\n"
            f"This action cannot be undone.",
            parent=self
        )

        if confirmed:
            db.delete_school(self._selected_school["id"])
            self._selected_school = None
            self._clear_programme_panel()
            self._load_schools()


    # ─── PROGRAMME ACTION HANDLERS ───

    def _on_add_programme(self):
        # Reads the entry field and adds a new programme to the selected school
        if not self._selected_school:
            messagebox.showwarning("No Selection", "Please select a school first.", parent=self)
            return

        programme_name = self._new_prog_entry.get().strip()
        if not programme_name:
            messagebox.showwarning("Empty Input", "Please enter a programme name.", parent=self)
            return

        success, error = db.add_programme(self._selected_school["id"], programme_name)
        if success:
            self._new_prog_entry.delete(0, "end")
            self._load_programmes(self._selected_school)
        else:
            messagebox.showerror("Error", error, parent=self)


    def _on_remove_programme(self, prog):
        # Confirms then removes a programme from the selected school
        confirmed = messagebox.askyesno(
            "Confirm Remove",
            f"Remove programme:\n'{prog['programme_name']}'?",
            parent=self
        )
        if confirmed:
            db.remove_programme(prog["id"])
            self._load_programmes(self._selected_school)


# ─── SCHOOL DIALOG ───

class _SchoolDialog(ctk.CTkToplevel):
    # Modal dialog for adding or renaming a school
    # result is set to (code, name) tuple on confirm, or None on cancel

    def __init__(self, parent, title, initial_code="", initial_name=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        self._build(initial_code, initial_name)
        self.after(50, self._center_on_parent, parent)


    def _center_on_parent(self, parent):
        # Centers this dialog over its parent window
        self.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w  = self.winfo_width()
        h  = self.winfo_height()
        x  = px + (pw // 2) - (w // 2)
        y  = py + (ph // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")


    def _build(self, initial_code, initial_name):
        # Builds the dialog layout with two input fields and confirm/cancel buttons
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="School Code:").grid(
            row=0, column=0, sticky="w", pady=6
        )
        self._code_entry = ctk.CTkEntry(frame, placeholder_text="e.g. som")
        self._code_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=6)
        if initial_code:
            self._code_entry.insert(0, initial_code)

        ctk.CTkLabel(frame, text="School Name:").grid(
            row=1, column=0, sticky="w", pady=6
        )
        self._name_entry = ctk.CTkEntry(frame, placeholder_text="e.g. School of Medicine")
        self._name_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=6)
        if initial_name:
            self._name_entry.insert(0, initial_name)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(16, 0))

        ctk.CTkButton(
            btn_frame,
            text="Confirm",
            width=110,
            command=self._on_confirm
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=110,
            fg_color="gray",
            hover_color="#555555",
            command=self.destroy
        ).pack(side="left", padx=8)

        # Allow Enter key to confirm
        self.bind("<Return>", lambda e: self._on_confirm())
        self.bind("<Escape>", lambda e: self.destroy())


    def _on_confirm(self):
        # Validates inputs and sets result before closing
        code = self._code_entry.get().strip()
        name = self._name_entry.get().strip()

        if not code:
            messagebox.showwarning("Missing Input", "School code is required.", parent=self)
            return
        if not name:
            messagebox.showwarning("Missing Input", "School name is required.", parent=self)
            return

        self.result = (code, name)
        self.destroy()