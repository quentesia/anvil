from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Label, Button
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual import on
from typing import List, Dict, Set

class DependencyDashboard(App[List[str]]):
    """
    Interactive Dependency Dashboard.
    Allows users to select packages for upgrade analysis.
    """
    
    CSS = """
    DataTable {
        height: 1fr;
    }
    Label {
        padding: 1;
        background: $boost;
        width: 100%;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("n", "next", "Next (Run Analysis)", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("space", "toggle", "Toggle Selection", show=True),
    ]

    def __init__(self, dependencies: List[Dict]):
        super().__init__()
        self.dependencies = dependencies
        self.selected_packages: Set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Select packages to analyze (Click or Press Space). Press 'N' to Proceed.")
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Add columns with explicit keys for reference
        table.add_column("Select", key="select")
        table.add_column("Package", key="package")
        table.add_column("Range", key="range")
        table.add_column("Installed", key="installed")
        table.add_column("Latest", key="latest")
        table.add_column("Status", key="status")
        
        # Add rows
        for dep in self.dependencies:
            key = dep["name"]
            
            # Default state: Unselected
            icon = "⬜"
            
            table.add_row(
                icon,
                dep["name"],
                dep["range"],
                dep["installed"],
                dep["latest"],
                dep["status"],
                key=key
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle click selection."""
        # Fix: Ensure we use the row key, not the index if that was the issue.
        # But event.row_key.value is correct if we set key=key in add_row.
        self.toggle_selection(event.row_key.value)

    def action_toggle(self) -> None:
        """Handle spacebar toggle."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
             # Get the key of the row at the cursor
             # In recent Textual, coordinate_to_cell_key might help, or get_row_at
             # But let's try getting row key by iteration or cursor_coordinate logic if needed.
             # Actually, table.get_row_at(table.cursor_row) returns data, but keys?
             
             # Robust way: get the row key from the 'cursor_coordinate'
             # The cursor might be on a specific cell.
             # table.coordinate_to_cell_key(table.cursor_coordinate) returns CellKey(row_key, col_key)
             
             try:
                 # Textual 0.50+
                 cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
                 self.toggle_selection(cell_key.row_key.value)
             except:
                 # Fallback if API differs slightly or no cursor
                 pass

    def toggle_selection(self, key: str) -> None:
        table = self.query_one(DataTable)
        
        if key in self.selected_packages:
            self.selected_packages.remove(key)
            icon = "⬜"
        else:
            self.selected_packages.add(key)
            icon = "✅"
            
        # Update the first cell using the explicit key "select"
        table.update_cell(key, "select", icon)
        
    def action_next(self) -> None:
        """Exit with the selected packages."""
        if not self.selected_packages:
            self.notify("Please select at least one package.", severity="warning")
            return
        self.exit(result=list(self.selected_packages))

if __name__ == "__main__":
    deps = [
        {"name": "requests", "range": "any", "installed": "2.31.0", "latest": "2.32.0", "status": "⬆️"},
        {"name": "numpy", "range": "any", "installed": "1.26.0", "latest": "1.26.0", "status": "✅"},
    ]
    app = DependencyDashboard(deps)
    result = app.run()
    print(f"User selected: {result}")
