import os
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from ui.mapping_manager import MappingManagerWindow
from ui.bulk_upload import BulkUploadWindow
import file_handler as fh


# ─── COLOUR & FONT CONSTANTS ───

PRIMARY_BLUE    = "#1F4E79"
ACCENT_BLUE     = "#2E86AB"
SUCCESS_GREEN   = "#27AE60"
WARNING_ORANGE  = "#E67E22"
ERROR_RED       = "#C0392B"
LIGHT_BG        = "#F0F4F8"


class MainWindow(ctk.CTk):
    # Root application window for the UHAS Email Generator

    def __init__(self):
        super().__init__()
        self.title("UHAS Student Email Generator")
        self.geometry("1020x720")
        self.minsize(900, 640)
        self.resizable(True, True)

        # Apply consistent appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Internal state
        self._uploaded_file_path   = None
        self._uploaded_file_ext    = None
        self._pipeline_result      = None
        self._processing           = False

        self._build_layout()
        self._center_window()


    def _center_window(self):
        # Centers the main window on the screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")


    # ─── LAYOUT ───

    def _build_layout(self):
        # Root grid: header row + body row
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()


    def _build_header(self):
        # Top banner with app title and management action buttons
        header = ctk.CTkFrame(self, fg_color=PRIMARY_BLUE, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="  UHAS Student Email Generator",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=14)

        # Right-side header buttons
        btn_area = ctk.CTkFrame(header, fg_color="transparent")
        btn_area.grid(row=0, column=2, sticky="e", padx=16)

        ctk.CTkButton(
            btn_area,
            text="Manage Schools & Programmes",
            width=210,
            height=34,
            fg_color=ACCENT_BLUE,
            hover_color="#1B6A8A",
            font=ctk.CTkFont(size=12),
            command=self._open_mapping_manager,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_area,
            text="Bulk Upload Programmes",
            width=180,
            height=34,
            fg_color="#5D6D7E",
            hover_color="#4A5568",
            font=ctk.CTkFont(size=12),
            command=self._open_bulk_upload,
        ).pack(side="left")


    def _build_body(self):
        # Main content area split into left config panel and right results panel
        body = ctk.CTkFrame(self, fg_color=LIGHT_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_config_panel(body)
        self._build_results_panel(body)


    # ─── LEFT CONFIG PANEL ───

    def _build_config_panel(self, parent):
        # Left panel containing file upload, options, and process controls
        panel = ctk.CTkFrame(parent, width=320, corner_radius=0, fg_color="white")
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)

        # Section: File Upload
        self._build_section_label(panel, "1.  Upload Student File", row=0)
        self._build_file_upload_section(panel, row=1)

        # Section: Options
        self._build_section_label(panel, "2.  Configure Options", row=2)
        self._build_options_section(panel, row=3)

        # Section: Process
        self._build_section_label(panel, "3.  Generate Emails", row=4)
        self._build_process_section(panel, row=5)

        # Push everything to top by filling remaining space
        spacer = ctk.CTkFrame(panel, fg_color="transparent")
        spacer.grid(row=6, column=0, sticky="nsew")
        panel.grid_rowconfigure(6, weight=1)


    def _build_section_label(self, parent, text, row):
        # Renders a styled section heading in the config panel
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=PRIMARY_BLUE,
            anchor="w",
        ).grid(row=row, column=0, sticky="ew", padx=16, pady=(18, 4))


    def _build_file_upload_section(self, parent, row):
        # File picker area with drag-hint and selected file display
        frame = ctk.CTkFrame(parent, fg_color=LIGHT_BG, corner_radius=8)
        frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 4))
        frame.grid_columnconfigure(0, weight=1)

        # Drop zone hint button
        self._upload_zone = ctk.CTkButton(
            frame,
            text="Click to Browse File\n(.xlsx  or  .csv)",
            height=72,
            fg_color="white",
            text_color="gray",
            hover_color="#E8EEF4",
            border_width=2,
            border_color="#AABDD0",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._on_browse_file,
        )
        self._upload_zone.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Selected file name display
        self._file_name_label = ctk.CTkLabel(
            frame,
            text="No file selected",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            wraplength=270,
        )
        self._file_name_label.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))


    def _build_options_section(self, parent, row):
        # Student type and other processing options
        frame = ctk.CTkFrame(parent, fg_color=LIGHT_BG, corner_radius=8)
        frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 4))
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="Student Type:",
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        self._student_type_var = ctk.StringVar(value="Regular")
        self._student_type_menu = ctk.CTkOptionMenu(
            frame,
            variable=self._student_type_var,
            values=["Regular", "Sandwich"],
            width=150,
            font=ctk.CTkFont(size=12),
        )
        self._student_type_menu.grid(row=0, column=1, sticky="w", padx=12, pady=(12, 4))

        # Sandwich note
        self._sandwich_note = ctk.CTkLabel(
            frame,
            text="Sandwich students will have 'sw' appended\nto their email username.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left",
            anchor="w",
            wraplength=260,
        )
        self._sandwich_note.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 12))

        # Update note visibility when type changes
        self._student_type_var.trace_add("write", self._on_student_type_change)
        self._on_student_type_change()


    def _on_student_type_change(self, *args):
        # Shows or hides the sandwich note based on selected student type
        if self._student_type_var.get() == "Sandwich":
            self._sandwich_note.configure(text_color=WARNING_ORANGE)
        else:
            self._sandwich_note.configure(text_color="gray")


    def _build_process_section(self, parent, row):
        # Process button, progress bar, and status label
        frame = ctk.CTkFrame(parent, fg_color=LIGHT_BG, corner_radius=8)
        frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 4))
        frame.grid_columnconfigure(0, weight=1)

        self._process_btn = ctk.CTkButton(
            frame,
            text="Generate Emails",
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=PRIMARY_BLUE,
            hover_color=ACCENT_BLUE,
            state="disabled",
            command=self._on_process,
        )
        self._process_btn.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

        self._progress_bar = ctk.CTkProgressBar(frame, mode="indeterminate", height=6)
        self._progress_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        self._progress_bar.set(0)

        self._status_label = ctk.CTkLabel(
            frame,
            text="Upload a file to get started.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            wraplength=270,
        )
        self._status_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 12))


    # ─── RIGHT RESULTS PANEL ───

    def _build_results_panel(self, parent):
        # Right panel with tabs: Preview, Errors, Download
        panel = ctk.CTkFrame(parent, fg_color="white", corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        # Tab bar
        self._tab_view = ctk.CTkTabview(panel, anchor="nw")
        self._tab_view.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        panel.grid_rowconfigure(0, weight=1)

        self._tab_preview  = self._tab_view.add("Preview")
        self._tab_errors   = self._tab_view.add("Errors / Warnings")
        self._tab_download = self._tab_view.add("Download")

        self._tab_preview.grid_columnconfigure(0, weight=1)
        self._tab_preview.grid_rowconfigure(1, weight=1)

        self._tab_errors.grid_columnconfigure(0, weight=1)
        self._tab_errors.grid_rowconfigure(1, weight=1)

        self._tab_download.grid_columnconfigure(0, weight=1)

        self._build_preview_tab()
        self._build_errors_tab()
        self._build_download_tab()


    # ─── PREVIEW TAB ───

    def _build_preview_tab(self):
        # Stats summary row + scrollable preview table
        stats_frame = ctk.CTkFrame(self._tab_preview, fg_color=LIGHT_BG, corner_radius=8)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._stat_total   = self._make_stat_card(stats_frame, "Total Rows",  "—", col=0)
        self._stat_success = self._make_stat_card(stats_frame, "Generated",   "—", col=1, color=SUCCESS_GREEN)
        self._stat_skipped = self._make_stat_card(stats_frame, "Skipped",     "—", col=2, color=ERROR_RED)

        # Scrollable preview table
        self._preview_table_frame = ctk.CTkScrollableFrame(
            self._tab_preview,
            label_text=""
        )
        self._preview_table_frame.grid(row=1, column=0, sticky="nsew")
        self._preview_table_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._render_preview_placeholder()


    def _make_stat_card(self, parent, label, value, col, color=None):
        # Creates a small stat card widget and returns the value label for later updates
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color="white")
        card.grid(row=0, column=col, sticky="ew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=0, column=0, pady=(8, 0))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=color or PRIMARY_BLUE,
        )
        value_label.grid(row=1, column=0, pady=(0, 8))
        return value_label


    def _render_preview_placeholder(self):
        # Shows a placeholder message when no data has been processed yet
        for widget in self._preview_table_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self._preview_table_frame,
            text="No data to preview yet.\nUpload a file and click Generate Emails.",
            text_color="gray",
            font=ctk.CTkFont(size=13),
            justify="center",
        ).grid(row=0, column=0, pady=40)


    def _render_preview_table(self, output_df):
        # Renders a paginated preview of the output DataFrame
        for widget in self._preview_table_frame.winfo_children():
            widget.destroy()

        # Only show key columns in preview for readability
        preview_cols = [
            "Username", "First name", "Last name",
            "Display name", "DEPARTMENT", "Fax Number"
        ]
        cols_to_show = [c for c in preview_cols if c in output_df.columns]

        # Header row
        for col_idx, col_name in enumerate(cols_to_show):
            ctk.CTkLabel(
                self._preview_table_frame,
                text=col_name,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=PRIMARY_BLUE,
                text_color="white",
                corner_radius=4,
                anchor="w",
                height=28,
            ).grid(row=0, column=col_idx, sticky="ew", padx=2, pady=(0, 4))

        # Data rows - show up to 200 rows in preview
        max_preview_rows = 200
        df_slice = output_df.head(max_preview_rows)

        for row_idx, (_, row) in enumerate(df_slice.iterrows(), start=1):
            bg = "#EAF2FB" if row_idx % 2 == 0 else "white"
            for col_idx, col_name in enumerate(cols_to_show):
                val = str(row.get(col_name, ""))
                ctk.CTkLabel(
                    self._preview_table_frame,
                    text=f"  {val}",
                    font=ctk.CTkFont(size=11),
                    fg_color=bg,
                    anchor="w",
                    height=26,
                    corner_radius=2,
                ).grid(row=row_idx, column=col_idx, sticky="ew", padx=2, pady=1)

        if len(output_df) > max_preview_rows:
            ctk.CTkLabel(
                self._preview_table_frame,
                text=f"Showing first {max_preview_rows} of {len(output_df)} rows. "
                     f"Download the file to see all.",
                text_color="gray",
                font=ctk.CTkFont(size=11),
            ).grid(
                row=max_preview_rows + 1,
                column=0,
                columnspan=len(cols_to_show),
                pady=8
            )


    # ─── ERRORS TAB ───

    def _build_errors_tab(self):
        # Header label + scrollable error table
        self._errors_summary_label = ctk.CTkLabel(
            self._tab_errors,
            text="No issues found.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._errors_summary_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self._errors_table_frame = ctk.CTkScrollableFrame(
            self._tab_errors,
            label_text=""
        )
        self._errors_table_frame.grid(row=1, column=0, sticky="nsew")
        self._errors_table_frame.grid_columnconfigure((0, 1, 2), weight=1)


    def _render_errors_table(self, error_report):
        # Renders the error report rows in the Errors tab
        for widget in self._errors_table_frame.winfo_children():
            widget.destroy()

        if not error_report:
            self._errors_summary_label.configure(
                text="No issues found. All rows processed successfully.",
                text_color=SUCCESS_GREEN,
            )
            ctk.CTkLabel(
                self._errors_table_frame,
                text="All rows were processed without errors.",
                text_color=SUCCESS_GREEN,
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, pady=30)
            return

        self._errors_summary_label.configure(
            text=f"{len(error_report)} row(s) had issues:",
            text_color=ERROR_RED,
        )

        headers = ["Row", "Student ID", "Issue"]
        for col_idx, h in enumerate(headers):
            ctk.CTkLabel(
                self._errors_table_frame,
                text=h,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=ERROR_RED,
                text_color="white",
                corner_radius=4,
                anchor="w",
                height=28,
            ).grid(row=0, column=col_idx, sticky="ew", padx=2, pady=(0, 4))

        for row_idx, err in enumerate(error_report, start=1):
            bg = "#FDEDEC" if row_idx % 2 == 0 else "white"
            for col_idx, key in enumerate(["Row", "Student ID", "Issue"]):
                ctk.CTkLabel(
                    self._errors_table_frame,
                    text=f"  {err.get(key, '')}",
                    font=ctk.CTkFont(size=11),
                    fg_color=bg,
                    anchor="w",
                    height=26,
                    corner_radius=2,
                ).grid(row=row_idx, column=col_idx, sticky="ew", padx=2, pady=1)


    # ─── DOWNLOAD TAB ───

    def _build_download_tab(self):
        # Download options for Excel and CSV
        frame = ctk.CTkFrame(self._tab_download, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", pady=20)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Download Generated File",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=PRIMARY_BLUE,
        ).grid(row=0, column=0, pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text="Choose a format to download the output file with all generated emails.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).grid(row=1, column=0, pady=(0, 24))

        # Excel download card
        self._build_download_card(
            frame,
            row=2,
            icon_text="Excel (.xlsx)",
            description="Formatted spreadsheet with styled headers,\nalternating rows and frozen panes.",
            button_text="Download Excel",
            button_color=SUCCESS_GREEN,
            button_hover="#1E8449",
            command=self._on_download_excel,
            attr="_excel_btn",
        )

        ctk.CTkLabel(frame, text="— or —", text_color="gray").grid(row=3, column=0, pady=10)

        # CSV download card
        self._build_download_card(
            frame,
            row=4,
            icon_text="CSV (.csv)",
            description="Plain comma-separated file.\nCompatible with all spreadsheet applications.",
            button_text="Download CSV",
            button_color=ACCENT_BLUE,
            button_hover="#1B6A8A",
            command=self._on_download_csv,
            attr="_csv_btn",
        )

        self._tab_download.grid_rowconfigure(0, weight=1)


    def _build_download_card(self, parent, row, icon_text, description,
                              button_text, button_color, button_hover, command, attr):
        # Renders a styled download option card
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=LIGHT_BG)
        card.grid(row=row, column=0, sticky="ew", padx=60, pady=4)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=icon_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=PRIMARY_BLUE,
        ).grid(row=0, column=0, pady=(14, 4))

        ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center",
        ).grid(row=1, column=0, pady=(0, 10))

        btn = ctk.CTkButton(
            card,
            text=button_text,
            width=180,
            height=38,
            fg_color=button_color,
            hover_color=button_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            command=command,
        )
        btn.grid(row=2, column=0, pady=(0, 16))
        setattr(self, attr, btn)


    # ─── FILE BROWSE HANDLER ───

    def _on_browse_file(self):
        # Opens a file dialog and stores the selected file path
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Student Data File",
            filetypes=[
                ("Excel & CSV files", "*.xlsx *.xls *.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
            ]
        )

        if not file_path:
            return

        self._uploaded_file_path = file_path
        self._uploaded_file_ext  = os.path.splitext(file_path)[1].lower()

        # Update UI to show selected file name
        file_name = os.path.basename(file_path)
        self._file_name_label.configure(
            text=file_name,
            text_color=SUCCESS_GREEN,
        )
        self._upload_zone.configure(
            text=f"File selected\nClick to change",
            text_color=SUCCESS_GREEN,
        )

        # Enable the process button
        self._process_btn.configure(state="normal")
        self._set_status("File loaded. Click Generate Emails to proceed.", "gray")

        # Reset results from any previous run
        self._reset_results()


    # ─── PROCESS HANDLER ────

    def _on_process(self):
        # Validates state then launches the processing pipeline in a background thread
        if not self._uploaded_file_path:
            messagebox.showwarning("No File", "Please upload a file first.", parent=self)
            return

        if self._processing:
            return

        self._processing = True
        self._process_btn.configure(state="disabled", text="Processing...")
        self._progress_bar.start()
        self._set_status("Processing file...", "gray")
        self._reset_results()

        student_type = self._student_type_var.get()

        # Run pipeline in a background thread to keep UI responsive
        thread = threading.Thread(
            target=self._run_pipeline_thread,
            args=(self._uploaded_file_path, self._uploaded_file_ext, student_type),
            daemon=True,
        )
        thread.start()


    def _run_pipeline_thread(self, file_path, file_ext, student_type):
        # Background thread target - runs the full processing pipeline
        # Posts results back to the main thread via after()
        try:
            with open(file_path, "rb") as f:
                result = fh.run_pipeline(f, file_ext, student_type)
            self.after(0, self._on_pipeline_success, result)
        except ValueError as e:
            self.after(0, self._on_pipeline_error, str(e))
        except Exception as e:
            self.after(0, self._on_pipeline_error, f"Unexpected error: {str(e)}")


    def _on_pipeline_success(self, result):
        # Called on the main thread after successful pipeline completion
        self._pipeline_result = result
        self._processing = False

        self._progress_bar.stop()
        self._progress_bar.set(1)
        self._process_btn.configure(state="normal", text="Generate Emails")

        total   = result["total_rows"]
        success = result["success_count"]
        skipped = result["skipped_count"]

        # Update stat cards
        self._stat_total.configure(text=str(total))
        self._stat_success.configure(text=str(success))
        self._stat_skipped.configure(text=str(skipped))

        # Render preview table
        self._render_preview_table(result["output_df"])

        # Render error report
        self._render_errors_table(result["error_report"])

        # Enable download buttons
        self._excel_btn.configure(state="normal")
        self._csv_btn.configure(state="normal")

        # Switch to preview tab
        self._tab_view.set("Preview")

        status_text = f"Done. {success} email(s) generated."
        if skipped > 0:
            status_text += f" {skipped} row(s) skipped."
        self._set_status(status_text, SUCCESS_GREEN if skipped == 0 else WARNING_ORANGE)


    def _on_pipeline_error(self, error_message):
        # Called on the main thread when the pipeline raises an exception
        self._processing = False
        self._progress_bar.stop()
        self._progress_bar.set(0)
        self._process_btn.configure(state="normal", text="Generate Emails")
        self._set_status(f"Error: {error_message}", ERROR_RED)
        messagebox.showerror("Processing Error", error_message, parent=self)


    # ─── DOWNLOAD HANDLERS ───

    def _on_download_excel(self):
        # Prompts user to save the Excel output file
        if not self._pipeline_result:
            return

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="UHAS_Emails.xlsx",
        )

        if not save_path:
            return

        try:
            buffer = self._pipeline_result["excel_buffer"]
            buffer.seek(0)
            with open(save_path, "wb") as f:
                f.write(buffer.read())
            messagebox.showinfo(
                "Download Complete",
                f"Excel file saved to:\n{save_path}",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self)


    def _on_download_csv(self):
        # Prompts user to save the CSV output file
        if not self._pipeline_result:
            return

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="UHAS_Emails.csv",
        )

        if not save_path:
            return

        try:
            buffer = self._pipeline_result["csv_buffer"]
            buffer.seek(0)
            with open(save_path, "wb") as f:
                f.write(buffer.read())
            messagebox.showinfo(
                "Download Complete",
                f"CSV file saved to:\n{save_path}",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self)


    # ─── MANAGEMENT WINDOW LAUNCHERS ────

    def _open_mapping_manager(self):
        # Opens the school and programme management window
        win = MappingManagerWindow(self)
        self.wait_window(win)


    def _open_bulk_upload(self):
        # Opens the bulk upload window
        win = BulkUploadWindow(self)
        self.wait_window(win)


    # ─── HELPERS ───

    def _set_status(self, message, color):
        # Updates the status label in the process section
        self._status_label.configure(text=message, text_color=color)


    def _reset_results(self):
        # Clears all results panels back to their placeholder states
        self._stat_total.configure(text="—")
        self._stat_success.configure(text="—")
        self._stat_skipped.configure(text="—")
        self._render_preview_placeholder()
        for widget in self._errors_table_frame.winfo_children():
            widget.destroy()
        self._errors_summary_label.configure(
            text="No issues found.", text_color="gray"
        )
        self._excel_btn.configure(state="disabled")
        self._csv_btn.configure(state="disabled")
        self._pipeline_result = None
        self._progress_bar.set(0)