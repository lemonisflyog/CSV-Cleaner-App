# ===============================
# 1. Imports
# ===============================
import sys                           # Needed to interact with the system (for app exit, args, etc.)
import pandas as pd                  # Data handling library (for CSV, cleaning, analysis)
import matplotlib.pyplot as plt      # Plotting library (for graphs)

# --- Qt Widgets: building blocks of the GUI ---
from PySide6.QtWidgets import (
    QApplication,        # The base application that manages the event loop
    QMainWindow,         # Main window class (provides menubar, status bar, etc.)
    QPushButton,         # Button widget
    QFileDialog,         # File picker dialog (open/save files)
    QMessageBox,         # Pop-up message box (errors, success notifications)
    QVBoxLayout,         # Vertical layout manager (stack widgets vertically)
    QWidget,             # Base widget class (containers for layouts/widgets)
    QTabWidget,          # Widget that allows multiple "tab pages"
    QTextEdit,           # Multi-line text editor (we use it for displaying text)
    QScrollArea,         # Scrollable container (for large text or widgets)
    QTableView           # Table view widget (to show full datasets in rows/columns)
)

from PySide6.QtCore import Qt        # Provides constants (e.g. alignment, etc.)
from PySide6.QtGui import QStandardItemModel, QStandardItem
# QStandardItemModel + QStandardItem are used to fill QTableView with data

# --- Matplotlib integration with Qt ---
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# FigureCanvas lets us take a Matplotlib figure and embed it directly inside the Qt GUI.


# ===============================
# 2. Main Application Window
# ===============================
class CSVApp(QMainWindow):   # Subclass QMainWindow → our custom app window
    def __init__(self):
        super().__init__()   # Initialize parent QMainWindow class

        # --- Window settings ---
        self.setWindowTitle("CSV Cleaner App")  # Title shown in window bar
        self.setGeometry(200, 200, 1200, 800)   # Window position (x=200, y=200), size (width=1200, height=800)

        # --- Tab manager ---
        self.tabs = QTabWidget()          # Create a tab container (like browser tabs)
        self.setCentralWidget(self.tabs)  # Place the tabs widget as the main content of the window

        # --- Data storage ---
        self.df = None  # Placeholder for our pandas DataFrame (the CSV file once loaded)

        # --------------------------------------------------------
        # Tab 1: Home (Upload & Export)
        # --------------------------------------------------------
        self.home_tab = QWidget()           # A blank container for the Home tab
        self.home_layout = QVBoxLayout()    # Vertical layout inside this tab

        # Upload button
        self.upload_btn = QPushButton("Upload CSV")   # Create button
        self.upload_btn.clicked.connect(self.load_csv) # Connect click → load_csv method
        self.home_layout.addWidget(self.upload_btn)    # Add button to layout

        # Export button
        self.export_btn = QPushButton("Export Cleaned CSV")
        self.export_btn.clicked.connect(self.export_csv)   # Connect click → export_csv method
        self.export_btn.setEnabled(False)  # Disabled until CSV is loaded (avoid exporting nothing)
        self.home_layout.addWidget(self.export_btn)

        self.home_tab.setLayout(self.home_layout)      # Assign layout to tab
        self.tabs.addTab(self.home_tab, "Home")        # Add tab to main tabs widget

        # --------------------------------------------------------
        # Tab 2: Data Preview (Scrollable table)
        # --------------------------------------------------------
        self.preview_tab = QWidget()
        self.preview_layout = QVBoxLayout()

        self.table_view = QTableView()      # QTableView allows large table scrolling
        self.preview_layout.addWidget(self.table_view)

        self.preview_tab.setLayout(self.preview_layout)
        self.tabs.addTab(self.preview_tab, "Data Preview")

        # --------------------------------------------------------
        # Tab 3: Duplicates (Scrollable text)
        # --------------------------------------------------------
        self.duplicates_tab = QWidget()
        self.duplicates_layout = QVBoxLayout()

        self.duplicates_text = QTextEdit()     # Multi-line text widget
        self.duplicates_text.setReadOnly(True) # User can’t edit this text

        # Wrap inside a scrollable container → handles overflow text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)        # Scrollbars appear automatically
        scroll.setWidget(self.duplicates_text)

        self.duplicates_layout.addWidget(scroll)
        self.duplicates_tab.setLayout(self.duplicates_layout)
        self.tabs.addTab(self.duplicates_tab, "Duplicates")

        # --------------------------------------------------------
        # Tab 4 & 5: Graphs (each graph gets its own tab)
        # --------------------------------------------------------
        # Tab for monthly subscriptions graph
        self.graph_month_tab = QWidget()
        self.graph_month_layout = QVBoxLayout()
        self.graph_month_tab.setLayout(self.graph_month_layout)
        self.tabs.addTab(self.graph_month_tab, "Subscriptions per Month")

        # Tab for yearly subscriptions graph
        self.graph_year_tab = QWidget()
        self.graph_year_layout = QVBoxLayout()
        self.graph_year_tab.setLayout(self.graph_year_layout)
        self.tabs.addTab(self.graph_year_tab, "Subscriptions per Year")

    # ============================================================
    # 3. Load and Clean CSV
    # ============================================================
    def load_csv(self):
        # --- Open file picker ---
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:  # If user cancels → stop
            return

        try:
            # --- Load CSV into DataFrame ---
            self.df = pd.read_csv(file_path)

            # --- Clean Website URLs ---
            if "Website" in self.df.columns:
                self.df["Cleaned Website"] = (
                    self.df["Website"]
                    .str.replace(r"^https?:\/\/", "", regex=True) # Remove http:// or https://
                    .str.replace(r"^www\.", "", regex=True)       # Remove www.
                    .str.rstrip("/")                              # Remove trailing slash
                )

            # --- Clean Subscription Dates ---
            if "Subscription Date" in self.df.columns:
                # Convert to datetime objects
                self.df["Subscription Date"] = pd.to_datetime(
                    self.df["Subscription Date"], errors="coerce"
                )
                # Sort dataset by date (earliest first)
                self.df = self.df.sort_values(by="Subscription Date", ascending=True)

            # Enable export button now that we have valid data
            self.export_btn.setEnabled(True)

            # Update all UI sections with new data
            self.show_preview()     # Fill Data Preview tab
            self.find_duplicates()  # Fill Duplicates tab
            self.plot_graphs()      # Draw graphs

            # Show success popup
            QMessageBox.information(self, "Success", "CSV loaded and processed!")

        except Exception as e:
            # Show error popup if loading fails
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    # ============================================================
    # 4. Data Preview Tab
    # ============================================================
    def show_preview(self):
        if self.df is not None:
            # Create a model to feed into QTableView
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(self.df.columns.tolist())  # Set column names

            # Loop through each row of DataFrame
            for row in self.df.itertuples(index=False):  # index=False → don’t include DataFrame index
                items = [QStandardItem(str(field)) for field in row]  # Convert row values to QStandardItem
                model.appendRow(items)  # Add row to model

            # Attach model to table view
            self.table_view.setModel(model)
            self.table_view.resizeColumnsToContents()  # Resize columns so content fits

    # ============================================================
    # 5. Duplicates Tab
    # ============================================================
    def find_duplicates(self):
        if self.df is not None:
            text_output = ""  # String buffer to collect results

            # --- Duplicate Companies ---
            if "Company" in self.df.columns:
                company_counts = self.df["Company"].value_counts()
                duplicates = company_counts[company_counts > 1]  # Only keep duplicates
                if not duplicates.empty:
                    text_output += "🏢 Duplicate Companies:\n"
                    text_output += str(duplicates) + "\n\n"

                    # Show details of customers in those companies
                    dup_customers = self.df[self.df["Company"].isin(duplicates.index)]
                    text_output += str(
                        dup_customers[["Company", "First Name", "Last Name", "City"]]
                    ) + "\n\n"
                else:
                    text_output += "✅ No duplicate companies found.\n\n"

            # --- Duplicate Cities ---
            if "City" in self.df.columns:
                city_counts = self.df["City"].value_counts()
                duplicates = city_counts[city_counts > 1]
                if not duplicates.empty:
                    text_output += "🌆 Duplicate Cities:\n"
                    text_output += str(duplicates) + "\n\n"
                else:
                    text_output += "✅ No duplicate cities found.\n\n"

            # Write to text widget
            self.duplicates_text.setText(text_output)

    # ============================================================
    # 6. Graph Tabs
    # ============================================================
    def plot_graphs(self):
        if self.df is not None and "Subscription Date" in self.df.columns:
            # --- Clear old graphs (avoid stacking if user reloads CSV) ---
            for layout in [self.graph_month_layout, self.graph_year_layout]:
                for i in reversed(range(layout.count())):
                    widget = layout.itemAt(i).widget()
                    if widget:
                        widget.setParent(None)  # Remove widget from layout

            # --- Subscriptions per Month ---
            monthly = (
                self.df["Subscription Date"].dt.to_period("M")
                .value_counts()
                .sort_index()
            )
            fig1, ax1 = plt.subplots(figsize=(7, 5))
            monthly.plot(kind="bar", ax=ax1, title="Subscriptions per Month")
            canvas1 = FigureCanvas(fig1)   # Embed plot in Qt
            self.graph_month_layout.addWidget(canvas1)

            # --- Subscriptions per Year ---
            yearly = (
                self.df["Subscription Date"].dt.to_period("Y")
                .value_counts()
                .sort_index()
            )
            fig2, ax2 = plt.subplots(figsize=(7, 5))
            yearly.plot(kind="bar", ax=ax2, title="Subscriptions per Year")
            canvas2 = FigureCanvas(fig2)
            self.graph_year_layout.addWidget(canvas2)

    # ============================================================
    # 7. Export Cleaned CSV
    # ============================================================
    def export_csv(self):
        if self.df is not None:
            # Ask user where to save file
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save CSV", "", "CSV Files (*.csv)"
            )
            if save_path:
                self.df.to_csv(save_path, index=False)  # Write DataFrame to CSV
                QMessageBox.information(
                    self, "Exported", f"CSV saved to:\n{save_path}"
                )


# ===============================
# 8. Application Entry Point
# ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)  # Create the app instance
    window = CSVApp()             # Create our main window
    window.show()                 # Show it
    sys.exit(app.exec())          # Start the event loop (waits for user actions)
