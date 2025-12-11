from PySide6.QtCore import Qt, QDate, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QPushButton,
    QDateEdit,
    QComboBox,
    QMessageBox
)

from models.entities import SampleRecord
from services.data_manager import DataManager
from ui.dialogs.details_dialog import RecordDetailsDialog

class HistoryPage(QWidget):
    """
    Page for browsing, filtering, and managing historical survey records.
    """
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.records = [] # In-memory storage
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Filtering Group ---
        self.filter_group = QGroupBox()
        filter_layout = QHBoxLayout(self.filter_group)
        
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        
        self.plot_id_filter_combo = QComboBox()
        self.search_button = QPushButton()
        self.search_button.clicked.connect(self.filter_records)
        
        self.label_from = QLabel()
        filter_layout.addWidget(self.label_from)
        filter_layout.addWidget(self.start_date_edit)
        
        self.label_to = QLabel()
        filter_layout.addWidget(self.label_to)
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addSpacing(20)
        
        self.label_plot = QLabel()
        filter_layout.addWidget(self.label_plot)
        filter_layout.addWidget(self.plot_id_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.search_button)

        # --- Records Table ---
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.doubleClicked.connect(self.view_record_details)

        # --- Actions ---
        actions_layout = QHBoxLayout()
        self.view_button = QPushButton()
        self.view_button.clicked.connect(self.view_record_details)
        self.delete_button = QPushButton()
        self.delete_button.clicked.connect(self.delete_selected_record)
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.load_data)
        
        actions_layout.addStretch()
        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.view_button)
        actions_layout.addWidget(self.delete_button)

        layout.addWidget(self.filter_group)
        layout.addWidget(self.history_table)
        layout.addLayout(actions_layout)
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.filter_group.setTitle(self.tr("Filter Records"))
        self.label_from.setText(self.tr("From:"))
        self.label_to.setText(self.tr("To:"))
        self.label_plot.setText(self.tr("Plot ID:"))
        self.search_button.setText(self.tr("Search"))
        
        self.history_table.setHorizontalHeaderLabels([
            self.tr("Time"), 
            self.tr("Plot ID"), 
            self.tr("Cultivar"), 
            self.tr("Mean DS (%)"), 
            self.tr("Severity")
        ])
        
        self.view_button.setText(self.tr("Open Record"))
        self.delete_button.setText(self.tr("Delete Record"))
        self.refresh_button.setText(self.tr("Refresh"))

    def load_data(self):
        self.records = self.data_manager.load_all_records()
        self.refresh_table()
        self.update_filter_options()

    def update_filter_options(self):
        current_plots = set()
        for r in self.records:
            current_plots.add(r.plot_id)
        
        self.plot_id_filter_combo.clear()
        self.plot_id_filter_combo.addItem("All")
        self.plot_id_filter_combo.addItems(sorted(list(current_plots)))

    def add_record(self, record: SampleRecord):
        self.load_data()

    def filter_records(self):
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().addDays(1).toPython()
        selected_plot = self.plot_id_filter_combo.currentText()

        filtered = []
        for r in self.records:
            if start_date <= r.timestamp.date() < end_date:
                if selected_plot == "All" or selected_plot == "" or r.plot_id == selected_plot:
                    filtered.append(r)
        
        self.refresh_table(filtered)

    def refresh_table(self, records=None):
        if records is None:
            records = self.records
            
        self.history_table.setRowCount(0)
        for row, record in enumerate(records):
            self.history_table.insertRow(row)
            
            t_item = QTableWidgetItem(record.timestamp.strftime("%Y-%m-%d %H:%M"))
            t_item.setData(Qt.UserRole, record)
            
            self.history_table.setItem(row, 0, t_item)
            self.history_table.setItem(row, 1, QTableWidgetItem(record.plot_id))
            self.history_table.setItem(row, 2, QTableWidgetItem(record.cultivar))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(record.mean_ds)))
            self.history_table.setItem(row, 4, QTableWidgetItem(record.severity_class))

    def view_record_details(self):
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a record first."))
            return
        
        item = self.history_table.item(selected_rows[0].row(), 0)
        record = item.data(Qt.UserRole)
        
        if record:
             self.show_details_popup(record)

    def show_details_popup(self, record):
         dialog = RecordDetailsDialog(record, self)
         dialog.exec()

    def delete_selected_record(self):
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a record to delete."))
            return

        reply = QMessageBox.question(
            self, self.tr("Confirm Delete"), self.tr("Are you sure you want to delete the selected record? This cannot be undone."),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            item = self.history_table.item(selected_rows[0].row(), 0)
            record = item.data(Qt.UserRole)
            
            if record:
                self.data_manager.delete_record(record.sample_id)
                self.load_data()
                QMessageBox.information(self, self.tr("Deleted"), self.tr("Record deleted."))