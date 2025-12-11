
import os
from PySide6.QtCore import QTranslator, QCoreApplication
from PySide6.QtWidgets import QApplication

class I18nManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance.translator = QTranslator()
            cls._instance.current_lang = "en"
            cls._instance.app = None
        return cls._instance

    def install(self, app: QApplication):
        self.app = app
        # Default is English, so no translator needed initially unless we saved state
        # For now, start with English.

    def set_language(self, lang_code: str):
        """
        Switch language.
        lang_code: 'en' or 'zh_CN'
        """
        if self.app is None:
            print("I18nManager not installed.")
            return

        if lang_code == "zh_CN":
            qm_path = os.path.join(os.getcwd(), "translations", "zh_CN.qm")
            if self.translator.load(qm_path):
                self.app.installTranslator(self.translator)
                self.current_lang = "zh_CN"
                print(f"Loaded translation: {qm_path}")
            else:
                print(f"Failed to load translation: {qm_path}")
        else:
            self.app.removeTranslator(self.translator)
            self.current_lang = "en"
            print("Switched to English")
