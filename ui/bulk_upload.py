import customtkinter as ctk
from tkinter import messagebox, filedialog
import pandas as pd
import database as db


class BulkUploadWindow(ctk.CTkToplevel):
    # Modal window for bulk uploading schools and programmes from an Excel file
    # Expected file format: two columns - School Code | Programme Names (comma-separated)

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Bulk Upload Schools & Programmes")
        self.geometry("780x580")
        self.minsize(700, 500)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Holds the parsed DataFrame before committing to DB
        self._preview_df = None

        self._build_layout()
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
        # Main scrollable container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(3, weight=1)

        self._build_instructions(content)
        self._build_file_section(content)
        self._build_mode_section(content)
        self._build_preview_section(content)
        self._build_action_buttons(content)


    def _build_instructions(self, parent):
        # Instruction card at the top of the window
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="How to prepare your file",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        instructions = (
            "Your Excel or CSV file must have exactly two columns:\n"
            "  \u2022  School Code  \u2014  short code for the school, e.g.  som,  sph,  sahs\n"
            "  \u2022  Programme Names  \u2014  comma-separated list of programmes in one cell\n\n"
            "Example row:   som   |   Bachelor of Dental Surgery, Bachelor of Medicine, Bachelor of Surgery"
        )

        ctk.CTkLabel(
            card,
            text=instructions,
            font=ctk.CTkFont(size=12),
            justify="left",
            anchor="w",
            wraplength=680,
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))


    def _build_file_section(self, parent):
        # File picker row
        file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_frame,
            text="File:",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=50,
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self._file_path_label = ctk.CTkLabel(
            file_frame,
            text="No file selected",
            anchor="w",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self._file_path_label.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ctk.CTkButton(
            file_frame,
            text="Browse File",
            width=120,
            command=self._on_browse_file
        ).grid(row=0, column=2)


    def _build_mode_section(self, parent):
        # Upload mode selector: merge or replace
        mode_frame = ctk.CTkFrame(parent, corner_radius=8)
        mode_frame.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        mode_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mode_frame,
            text="Upload Mode",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        self._upload_mode = ctk.StringVar(value="merge")

        merge_desc = (
            "Merge  \u2014  Keep existing schools and programmes. "
            "Only new entries from the file will be added."
        )
        replace_desc = (
            "Replace  \u2014  Delete all existing schools and programmes, "
            "then insert everything from the file."
        )

        ctk.CTkRadioButton(
            mode_frame,
            text=merge_desc,
            variable=self._upload_mode,
            value="merge",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=14, pady=4)

        ctk.CTkRadioButton(
            mode_frame,
            text=replace_desc,
            variable=self._upload_mode,
            value="replace",
            font=ctk.CTkFont(size=12),
            text_color="#C0392B",
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(4, 12))


    def _build_preview_section(self, parent):
        # Preview area showing parsed file contents before import
        preview_label = ctk.CTkLabel(
            parent,
            text="File Preview",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        preview_label.grid(row=3, column=0, sticky="w", pady=(0, 6))

        # Scrollable frame acting as a table preview
        self._preview_frame = ctk.CTkScrollableFrame(parent, label_text="")
        self._preview_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 14))
        self._preview_frame.grid_columnconfigure(0, weight=1)
        self._preview_frame.grid_columnconfigure(1, weight=3)

        parent.grid_rowconfigure(4, weight=1)

        self._preview_status_label = ctk.CTkLabel(
            parent,
            text="No file loaded.",
            text_color="gray",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self._preview_status_label.grid(row=5, column=0, sticky="w", pady=(0, 10))


    def _build_action_buttons(self, parent):
        # Bottom action row with Import and Cancel buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=6, column=0, sticky="e")

        self._import_btn = ctk.CTkButton(
            btn_frame,
            text="Import to Database",
            width=160,
            state="disabled",
            command=self._on_import
        )
        self._import_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color="gray",
            hover_color="#555555",
            command=self.destroy
        ).pack(side="left")


    # ─── FILE HANDLING ───

    def _on_browse_file(self):
        # Opens a file dialog and loads the selected file for preview
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Schools & Programmes File",
            filetypes=[
                ("Excel & CSV files", "*.xlsx *.xls *.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
            ]
        )

        if not file_path:
            return

        self._file_path_label.configure(text=file_path, text_color=("black", "white"))
        self._load_preview(file_path)


    def _load_preview(self, file_path):
        # Parses the selected file and renders a preview table
        self._preview_df = None
        self._import_btn.configure(state="disabled")
        self._clear_preview()

        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path, dtype=str)
            else:
                df = pd.read_excel(file_path, dtype=str)

            # Normalize column names for validation
            df.columns = [str(c).strip() for c in df.columns]

            # Validate required columns exist
            required = {"school code", "programme names"}
            actual = {c.lower() for c in df.columns}
            missing = required - actual

            if missing:
                self._preview_status_label.configure(
                    text=f"Error: Missing columns: {', '.join(missing)}. "
                         f"Found: {', '.join(df.columns)}",
                    text_color="#C0392B"
                )
                return

            # Drop fully empty rows
            df.dropna(how="all", inplace=True)
            df.reset_index(drop=True, inplace=True)

            if df.empty:
                self._preview_status_label.configure(
                    text="File is empty after removing blank rows.",
                    text_color="#C0392B"
                )
                return

            self._preview_df = df
            self._render_preview(df)
            self._import_btn.configure(state="normal")

            self._preview_status_label.configure(
                text=f"{len(df)} school row(s) ready to import.",
                text_color="#27AE60"
            )

        except Exception as e:
            self._preview_status_label.configure(
                text=f"Failed to read file: {str(e)}",
                text_color="#C0392B"
            )


    def _render_preview(self, df):
        # Renders the parsed DataFrame as a simple two-column table in the preview frame
        self._clear_preview()

        # Find actual column names (case-insensitive match)
        col_map = {c.lower(): c for c in df.columns}
        code_col = col_map.get("school code", df.columns[0])
        prog_col = col_map.get("programme names", df.columns[1])

        # Header row
        header_kwargs = {
            "font": ctk.CTkFont(size=12, weight="bold"),
            "anchor": "w",
            "fg_color": "#1F4E79",
            "text_color": "white",
            "corner_radius": 4,
            "height": 30,
        }

        ctk.CTkLabel(
            self._preview_frame,
            text="  School Code",
            **header_kwargs
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 4))

        ctk.CTkLabel(
            self._preview_frame,
            text="  Programme Names",
            **header_kwargs
        ).grid(row=0, column=1, sticky="ew", pady=(0, 4))

        # Data rows
        for i, row in df.iterrows():
            bg = "#EAF2FB" if i % 2 == 0 else "transparent"

            code_val = str(row[code_col]).strip() if pd.notna(row[code_col]) else ""
            prog_val = str(row[prog_col]).strip() if pd.notna(row[prog_col]) else ""

            ctk.CTkLabel(
                self._preview_frame,
                text=f"  {code_val.upper()}",
                anchor="w",
                font=ctk.CTkFont(size=12),
                fg_color=bg,
                corner_radius=4,
                height=28,
            ).grid(row=i + 1, column=0, sticky="ew", padx=(0, 4), pady=1)

            ctk.CTkLabel(
                self._preview_frame,
                text=f"  {prog_val}",
                anchor="w",
                font=ctk.CTkFont(size=12),
                fg_color=bg,
                corner_radius=4,
                height=28,
                wraplength=400,
            ).grid(row=i + 1, column=1, sticky="ew", pady=1)


    def _clear_preview(self):
        # Removes all widgets from the preview frame
        for widget in self._preview_frame.winfo_children():
            widget.destroy()


    # ─── IMPORT HANDLER ───

    def _on_import(self):
        # Validates mode and calls the database bulk upload function
        if self._preview_df is None:
            messagebox.showwarning("No Data", "Please load a valid file first.", parent=self)
            return

        mode = self._upload_mode.get()

        # Warn before replacing all existing data
        if mode == "replace":
            confirmed = messagebox.askyesno(
                "Confirm Replace",
                "This will permanently delete all existing schools and programmes "
                "and replace them with the contents of this file.\n\n"
                "This action cannot be undone. Continue?",
                parent=self,
                icon="warning"
            )
            if not confirmed:
                return

        merge = mode == "merge"

        success_count, errors = db.bulk_upload_from_dataframe(self._preview_df, merge=merge)

        # Build result message
        if errors:
            error_summary = "\n".join(errors[:10])
            if len(errors) > 10:
                error_summary += f"\n... and {len(errors) - 10} more issue(s)."

            messagebox.showwarning(
                "Import Completed with Warnings",
                f"{success_count} programme(s) imported successfully.\n\n"
                f"The following issues were encountered:\n{error_summary}",
                parent=self
            )
        else:
            messagebox.showinfo(
                "Import Successful",
                f"{success_count} programme(s) imported successfully.",
                parent=self
            )

        # Close the window after a successful import
        self.destroy()