from PySide6.QtCore import Qt, QSettings, Signal, Slot, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QComboBox,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QTabWidget,
    QListWidget,
    QLineEdit,
    QInputDialog,
    QApplication,
    QSizePolicy
)
from services.data_manager import DataManager
from services.i18n_manager import I18nManager

class OptionManagerWidget(QWidget):
    """
    A helper widget to manage a list of strings (Add/Remove).
    """
    options_changed = Signal()

    def __init__(self, title, settings_key, default_values):
        super().__init__()
        self.title_text = title
        self.settings_key = settings_key
        self.default_values = default_values
        self.settings = QSettings("RBNet", "FieldSurvey")
        self.init_ui()
        self.load_options()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.group = QGroupBox(self.title_text)
        group_layout = QVBoxLayout(self.group)

        self.list_widget = QListWidget()
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton()
        self.add_btn.clicked.connect(self.add_option)
        self.remove_btn = QPushButton()
        self.remove_btn.clicked.connect(self.remove_option)
        self.reset_btn = QPushButton()
        self.reset_btn.clicked.connect(self.reset_options)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.reset_btn)

        group_layout.addWidget(self.list_widget)
        group_layout.addLayout(btn_layout)
        layout.addWidget(self.group)
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.group.setTitle(self.tr(self.title_text)) # Note: title_text might need to be translated by parent or passed as key
        self.add_btn.setText(self.tr("Add"))
        self.remove_btn.setText(self.tr("Remove"))
        self.reset_btn.setText(self.tr("Reset"))

    def load_options(self):
        self.list_widget.clear()
        options = self.settings.value(self.settings_key, self.default_values)
        if isinstance(options, str):
             options = [options]
        if not isinstance(options, list):
             options = self.default_values

        for opt in options:
            self.list_widget.addItem(str(opt))

    def save_options(self):
        options = []
        for i in range(self.list_widget.count()):
            options.append(self.list_widget.item(i).text())
        self.settings.setValue(self.settings_key, options)
        self.options_changed.emit()

    def add_option(self):
        text, ok = QInputDialog.getText(self, self.tr("Add Option"), self.tr("New Option:"))
        if ok and text:
            self.list_widget.addItem(text)
            self.save_options()

    def remove_option(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            self.save_options()
        else:
             QMessageBox.warning(self, self.tr("Tip"), self.tr("Please select an item first"))

    def reset_options(self):
        if QMessageBox.question(self, self.tr("Reset"), self.tr("Are you sure you want to reset to defaults?")) == QMessageBox.Yes:
            self.settings.setValue(self.settings_key, self.default_values)
            self.load_options()
            self.options_changed.emit()

class SettingsPage(QWidget):
    """
    Page for configuring application settings.
    """
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("RBNet", "FieldSurvey")
        self.data_manager = DataManager()
        self.i18n_manager = I18nManager()
        self._is_loading_settings = False
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Tab 1: General Settings ---
        self.general_tab = QWidget()
        self.init_general_tab()
        self.tabs.addTab(self.general_tab, "") # Set in retranslateUi

        # --- Tab 2: Metadata Options ---
        self.options_tab = QWidget()
        self.init_options_tab()
        self.tabs.addTab(self.options_tab, "") # Set in retranslateUi
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.tabs.setTabText(0, self.tr("General Settings"))
        self.tabs.setTabText(1, self.tr("Metadata Options"))
        
        # General Tab
        self.lang_group.setTitle(self.tr("Language"))
        self.ds_group.setTitle(self.tr("DS Thresholds"))
        self.camera_group.setTitle(self.tr("Camera Settings"))
        self.system_group.setTitle(self.tr("Data & System"))
        self.clear_data_button.setText(self.tr("Clear All Local Records"))
        
        # DS threshold row labels
        self.label_mild.setText(self.tr("Mild Symptoms: "))
        self.label_mod.setText(self.tr("Moderate Symptoms: "))
        self.label_sev.setText(self.tr("Severe Symptoms: "))
        
        self.label_res.setText(self.tr("Resolution:"))
        self.label_rot.setText(self.tr("Rotation:"))

    def init_general_tab(self):
        layout = QVBoxLayout(self.general_tab)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)

        # --- Language ---
        self.lang_group = QGroupBox()
        lang_layout = QFormLayout(self.lang_group)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("中文", "zh_CN")
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addRow(self.tr("Language:"), self.lang_combo)
        layout.addWidget(self.lang_group)

        # --- DS Thresholds ---
        self.ds_group = QGroupBox()
        ds_layout = QFormLayout(self.ds_group)
        ds_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        ds_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ds_layout.setFormAlignment(Qt.AlignTop)
        ds_layout.setHorizontalSpacing(10)
        ds_layout.setVerticalSpacing(6)
        
        # Mild Symptoms: 0% ~ mild_threshold
        self.min_mild = QLabel("0%")
        self.min_mild.setFixedWidth(50)
        self.min_mild.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sep_mild = QLabel("~")
        self.sep_mild.setFixedWidth(14)
        self.sep_mild.setAlignment(Qt.AlignCenter)
        self.mild_threshold = QSpinBox()
        self.mild_threshold.setRange(1, 100)
        self.mild_threshold.setSuffix(" %")
        self.mild_threshold.valueChanged.connect(self.save_settings)

        self.mild_row = QWidget()
        mild_row_layout = QHBoxLayout(self.mild_row)
        mild_row_layout.setContentsMargins(0, 0, 0, 0)
        mild_row_layout.setSpacing(6)
        mild_row_layout.addWidget(self.min_mild)
        mild_row_layout.addWidget(self.sep_mild)
        mild_row_layout.addWidget(self.mild_threshold)

        # Moderate Symptoms: mild_threshold % ~ moderate_threshold
        self.min_mod = QLabel()
        self.min_mod.setFixedWidth(50)
        self.min_mod.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sep_mod = QLabel("~")
        self.sep_mod.setFixedWidth(14)
        self.sep_mod.setAlignment(Qt.AlignCenter)
        self.moderate_threshold = QSpinBox()
        self.moderate_threshold.setRange(1, 100)
        self.moderate_threshold.setSuffix(" %")
        self.moderate_threshold.valueChanged.connect(self.save_settings)

        self.mod_row = QWidget()
        mod_row_layout = QHBoxLayout(self.mod_row)
        mod_row_layout.setContentsMargins(0, 0, 0, 0)
        mod_row_layout.setSpacing(6)
        mod_row_layout.addWidget(self.min_mod)
        mod_row_layout.addWidget(self.sep_mod)
        mod_row_layout.addWidget(self.moderate_threshold)

        # Severe Symptoms: moderate_threshold % ~ 100%
        self.min_sev = QLabel()
        self.min_sev.setFixedWidth(50)
        self.min_sev.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sep_sev = QLabel("~")
        self.sep_sev.setFixedWidth(14)
        self.sep_sev.setAlignment(Qt.AlignCenter)
        self.max_sev = QLabel("100%")
        self.max_sev.setFixedWidth(50)
        self.max_sev.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.sev_row = QWidget()
        self.sev_row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sev_row_layout = QHBoxLayout(self.sev_row)
        sev_row_layout.setContentsMargins(0, 0, 0, 0)
        sev_row_layout.setSpacing(6)
        sev_row_layout.addWidget(self.min_sev)
        sev_row_layout.addWidget(self.sep_sev)
        sev_row_layout.addWidget(self.max_sev)
        sev_row_layout.addStretch(1)

        self.label_mild = QLabel()
        ds_layout.addRow(self.label_mild, self.mild_row)
        
        self.label_mod = QLabel()
        ds_layout.addRow(self.label_mod, self.mod_row)

        self.label_sev = QLabel()
        ds_layout.addRow(self.label_sev, self.sev_row)

        # --- Camera Settings ---
        self.camera_group = QGroupBox()
        camera_layout = QFormLayout(self.camera_group)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1024x768", "1920x1440"])
        self.resolution_combo.currentTextChanged.connect(self.save_settings)
        
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["0°", "90°", "180°", "270°"])
        self.rotation_combo.currentTextChanged.connect(self.save_settings)

        self.label_res = QLabel()
        camera_layout.addRow(self.label_res, self.resolution_combo)
        
        self.label_rot = QLabel()
        camera_layout.addRow(self.label_rot, self.rotation_combo)

        # --- Data & System ---
        self.system_group = QGroupBox()
        system_layout = QFormLayout(self.system_group)
        
        self.clear_data_button = QPushButton()
        self.clear_data_button.setStyleSheet("background-color: #dc3545; color: white;")
        self.clear_data_button.clicked.connect(self.confirm_clear_data)
        
        system_layout.addRow(self.clear_data_button)

        layout.addWidget(self.ds_group)
        layout.addWidget(self.camera_group)
        layout.addWidget(self.system_group)
        layout.addStretch()

        self._update_ds_range_labels()

    def init_options_tab(self):
        layout = QHBoxLayout(self.options_tab)
        
        # Plot IDs
        default_plots = [f"PLOT-{i:03}" for i in range(1, 11)]
        self.plot_manager = OptionManagerWidget("Plot IDs", "options/plots", default_plots)
        self.plot_manager.options_changed.connect(self.notify_settings_change)
        
        # Cultivars
        default_cultivars = ["Cultivar-A", "Cultivar-B", "IR64", "Minghui 63"]
        self.cultivar_manager = OptionManagerWidget("Cultivars", "options/cultivars", default_cultivars)
        self.cultivar_manager.options_changed.connect(self.notify_settings_change)

        # Growth Stages
        default_stages = ["Tillering", "Stem Elongation", "Booting", "Heading/Flowering"]
        self.stage_manager = OptionManagerWidget("Growth Stages", "options/stages", default_stages)
        self.stage_manager.options_changed.connect(self.notify_settings_change)

        layout.addWidget(self.plot_manager)
        layout.addWidget(self.cultivar_manager)
        layout.addWidget(self.stage_manager)

    def load_settings(self):
        self._is_loading_settings = True
        self.mild_threshold.blockSignals(True)
        self.moderate_threshold.blockSignals(True)
        self.resolution_combo.blockSignals(True)
        self.rotation_combo.blockSignals(True)
        # Thresholds
        # Defaults: 0-5, 5-15, 15-100
        if not self.settings.contains("thresholds/mild"):
            self.settings.setValue("thresholds/mild", 5)
        if not self.settings.contains("thresholds/moderate"):
            self.settings.setValue("thresholds/moderate", 15)

        self.mild_threshold.setValue(int(self.settings.value("thresholds/mild", 5)))
        self.moderate_threshold.setValue(int(self.settings.value("thresholds/moderate", 15)))
        self._enforce_threshold_constraints()
        self._update_ds_range_labels()
        
        # Camera
        res = self.settings.value("camera/resolution", "1024x768")
        rot = self.settings.value("camera/rotation", "0°")
        self.resolution_combo.setCurrentText(str(res))
        self.rotation_combo.setCurrentText(str(rot))

        self.mild_threshold.blockSignals(False)
        self.moderate_threshold.blockSignals(False)
        self.resolution_combo.blockSignals(False)
        self.rotation_combo.blockSignals(False)
        self._is_loading_settings = False

    def change_language(self, index):
        lang_code = self.lang_combo.itemData(index)
        self.i18n_manager.set_language(lang_code)

    def save_settings(self):
        if getattr(self, "_is_loading_settings", False):
            return
        self._enforce_threshold_constraints()
        self._update_ds_range_labels()
        self.settings.setValue("thresholds/mild", self.mild_threshold.value())
        self.settings.setValue("thresholds/moderate", self.moderate_threshold.value())
        self.settings.setValue("camera/resolution", self.resolution_combo.currentText())
        self.settings.setValue("camera/rotation", self.rotation_combo.currentText())
        self.notify_settings_change()

    def _enforce_threshold_constraints(self):
        """Keep thresholds consistent: mild_max <= moderate_max.

        Per requirement: moderate min equals mild max.
        We allow equality, and auto-correct when user crosses values.
        """
        mild_value = int(self.mild_threshold.value())
        moderate_value = int(self.moderate_threshold.value())

        if mild_value > moderate_value:
            self.moderate_threshold.blockSignals(True)
            self.moderate_threshold.setValue(mild_value)
            self.moderate_threshold.blockSignals(False)

        # Keep spinbox limits aligned (allow equality)
        self.mild_threshold.blockSignals(True)
        self.moderate_threshold.blockSignals(True)
        self.mild_threshold.setMaximum(self.moderate_threshold.value())
        self.moderate_threshold.setMinimum(self.mild_threshold.value())
        self.mild_threshold.blockSignals(False)
        self.moderate_threshold.blockSignals(False)

    def _update_ds_range_labels(self):
        mild_max = int(self.mild_threshold.value())
        moderate_max = int(self.moderate_threshold.value())
        self.min_mod.setText(f"{mild_max}%")
        self.min_sev.setText(f"{moderate_max}%")

    def notify_settings_change(self):
        self.settings_changed.emit({
            "thresholds": {
                "mild": self.mild_threshold.value(),
                "moderate": self.moderate_threshold.value()
            },
            "camera": {
                "resolution": self.resolution_combo.currentText(),
                "rotation": self.rotation_combo.currentText()
            },
            "options_updated": True 
        })

    def confirm_clear_data(self):
        reply = QMessageBox.warning(
            self,
            self.tr("Confirm"),
            self.tr("This will delete all local records and cannot be undone.\nContinue?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.data_manager.clear_all_data()
                QMessageBox.information(self, self.tr("Done"), self.tr("All local data cleared."))
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to clear data')}: {e}")