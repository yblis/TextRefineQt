import sys
import json
import os
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QLabel,
                            QDialog, QLineEdit, QComboBox, QProgressBar,
                            QMessageBox, QMenu, QFileDialog, QShortcut)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence
import requests

os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['QT_MAC_WANTS_LAYER'] = '1'

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

class HistoryManager:
    def __init__(self):
        self.history_file = data_dir / "history.json"
        self.history = self.load_history()

    def load_history(self):
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def add_entry(self, original_text, reformulated_text, parameters):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'original': original_text,
            'reformulated': reformulated_text,
            'parameters': parameters
        }
        self.history.append(entry)
        self.save_history()

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history[-100:], f, ensure_ascii=False, indent=2)

class TemplateManager:
    def __init__(self):
        self.templates_file = data_dir / "templates.json"
        self.templates = self.load_templates()

    def load_templates(self):
        if self.templates_file.exists():
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "Email professionnel": {
                "tone": "Professionnel",
                "format": "Mail",
                "length": "Moyen"
            },
            "Article blog décontracté": {
                "tone": "Décontracté",
                "format": "Article de blog",
                "length": "Long"
            }
        }

    def save_templates(self):
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

class PromptDialog(QDialog):
    def __init__(self, current_prompt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration du Prompt")
        self.setStyleSheet("""
            QDialog { background-color: #323232; }
            QLabel { color: white; font-size: 13px; }
            QTextEdit {
                background-color: #3d3d3d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        prompt_label = QLabel("Prompt système:")
        layout.addWidget(prompt_label)

        self.prompt_text = QTextEdit()
        self.prompt_text.setMinimumSize(400, 200)
        self.prompt_text.setText(current_prompt)
        layout.addWidget(self.prompt_text)

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

class SettingsDialog(QDialog):
    def __init__(self, current_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration Ollama")
        self.setStyleSheet("""
            QDialog { background-color: #323232; }
            QLabel { color: white; font-size: 13px; }
            QLineEdit {
                background-color: #3d3d3d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        url_label = QLabel("URL d'Ollama:")
        self.url_input = QLineEdit()
        self.url_input.setText(current_url)
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)

        models_label = QLabel("Modèle:")
        self.models_combo = QComboBox()
        layout.addWidget(models_label)
        layout.addWidget(self.models_combo)

        refresh_button = QPushButton("Rafraîchir les modèles")
        refresh_button.clicked.connect(self.refresh_models)
        layout.addWidget(refresh_button)

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        self.setMinimumWidth(400)
        self.refresh_models()

    def refresh_models(self):
        try:
            response = requests.get(f"{self.url_input.text()}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.models_combo.clear()
                for model in data.get('models', []):
                    self.models_combo.addItem(model['name'], model)
        except Exception as e:
            print(f"Erreur lors de la récupération des modèles: {e}")

class TagButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(35)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.updateStyle()

    def updateStyle(self):
        if self.isChecked():
            style = """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 17px;
                    padding: 5px 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: #424242;
                    color: white;
                    border: none;
                    border-radius: 17px;
                    padding: 5px 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #484848;
                }
            """
        self.setStyleSheet(style)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.updateStyle()

class TagSection(QWidget):
    def __init__(self, title, tags, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: #3d3d3d;
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 13px;
                padding: 5px;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        layout.addWidget(title_label)
        
        tags_container = QWidget()
        tags_container.setStyleSheet("background-color: transparent;")
        tags_layout = QHBoxLayout(tags_container)
        tags_layout.setSpacing(8)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        
        self.buttons = []
        for tag in tags:
            btn = TagButton(tag)
            btn.clicked.connect(lambda checked, b=btn: self.handleTagClick(b))
            self.buttons.append(btn)
            tags_layout.addWidget(btn)
        
        tags_layout.addStretch()
        layout.addWidget(tags_container)

        if self.buttons:
            self.buttons[0].setChecked(True)
            self.buttons[0].updateStyle()

    def handleTagClick(self, clicked_button):
        for button in self.buttons:
            if button != clicked_button:
                button.setChecked(False)
                button.updateStyle()
        clicked_button.setChecked(True)
        clicked_button.updateStyle()

    def getSelectedTag(self):
        for button in self.buttons:
            if button.isChecked():
                return button.text()
        return ""

class ExportManager:
    @staticmethod
    def export_text(text, file_path, format_type):
        with open(file_path, 'w', encoding='utf-8') as f:
            if format_type == "markdown":
                f.write(f"# Reformulated Text\n\n{text}")
            elif format_type == "html":
                f.write(f"<html><body><h1>Reformulated Text</h1><p>{text}</p></body></html>")
            else:
                f.write(text)

class ReformulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.history_manager = HistoryManager()
        self.template_manager = TemplateManager()
        self.ollama_url = "http://localhost:11434"
        self.current_model = "qwen2.5:3b"
        self.system_prompt = """Tu es un expert en reformulation. Tu dois reformuler le texte selon les paramètres spécifiés par l'utilisateur: ton, format et longueur. IMPORTANT : retourne UNIQUEMENT le texte reformulé, sans aucune mention des paramètres. 
Respecte scrupuleusement le format demandé, la longueur et le ton. Ne rajoute aucun autre commentaire."""
        
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_autosave()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+R"), self, self.reformulate_text)
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_to_clipboard)
        QShortcut(QKeySequence("Ctrl+S"), self, self.export_text)
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_history)

    def setup_autosave(self):
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.auto_save)
        self.autosave_timer.start(60000)

    def setup_ui(self):
        self.setWindowTitle("Reformulateur")
        self.setStyleSheet("""
            QMainWindow { background-color: #323232; }
            QLabel { color: white; font-size: 13px; }
            QTextEdit {
                background-color: #3d3d3d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
            }
            QPushButton#mainButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                min-height: 45px;
            }
            QPushButton#mainButton:hover {
                background-color: #45a049;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        config_layout = QHBoxLayout()
        settings_button = QPushButton("⚙️ Configuration Ollama")
        settings_button.setObjectName("mainButton")
        settings_button.clicked.connect(self.open_settings)
        
        prompt_button = QPushButton("📝 Configuration Prompt")
        prompt_button.setObjectName("mainButton")
        prompt_button.clicked.connect(self.open_prompt_config)
        
        config_layout.addWidget(settings_button)
        config_layout.addWidget(prompt_button)
        layout.addLayout(config_layout)

        input_label = QLabel("Entre ton texte à reformuler:")
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setMinimumHeight(100)
        self.input_text.setPlaceholderText("Entrez votre texte ici...")
        layout.addWidget(self.input_text)

        self.tone_section = TagSection("Ton:", 
            ["Professionnel", "Informatif", "Décontracté", "Enthousiaste", "Drôle", "Sarcastique"])
        layout.addWidget(self.tone_section)

        self.format_section = TagSection("Format:", 
            ["Mail", "Paragraphe", "Idées", "Article de blog"])
        layout.addWidget(self.format_section)

        self.length_section = TagSection("Longueur:", 
            ["Court", "Moyen", "Long"])
        layout.addWidget(self.length_section)

        self.reformulate_button = QPushButton("Reformuler")
        self.reformulate_button.setObjectName("mainButton")
        self.reformulate_button.clicked.connect(self.reformulate_text)
        layout.addWidget(self.reformulate_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        response_label = QLabel("Réponse:")
        layout.addWidget(response_label)
        
        self.output_text = QTextEdit()
        self.output_text.setMinimumHeight(120)
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        buttons_layout = QHBoxLayout()
        copy_button = QPushButton("Copier")
        copy_button.setObjectName("mainButton")
        clear_button = QPushButton("Effacer")
        clear_button.setObjectName("mainButton")
        
        copy_button.clicked.connect(self.copy_to_clipboard)
        clear_button.clicked.connect(self.clear_output)
        
        buttons_layout.addWidget(copy_button)
        buttons_layout.addWidget(clear_button)
        layout.addLayout(buttons_layout)

        self.setMinimumSize(700, 900)
        self.resize(700, 900)

    def auto_save(self):
        settings = {
            "input_text": self.input_text.toPlainText(),
            "output_text": self.output_text.toPlainText(),
            "tone": self.tone_section.getSelectedTag(),
            "format": self.format_section.getSelectedTag(),
            "length": self.length_section.getSelectedTag()
        }
        with open(data_dir / "settings.json", 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def open_settings(self):
        dialog = SettingsDialog(self.ollama_url, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.ollama_url = dialog.url_input.text()
            if dialog.models_combo.currentData():
                self.current_model = dialog.models_combo.currentData()['name']

    def open_prompt_config(self):
        dialog = PromptDialog(self.system_prompt, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.system_prompt = dialog.prompt_text.toPlainText()

    def show_history(self):
        pass

    def export_text(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Reformulated Text",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;HTML Files (*.html)"
        )
        if file_name:
            format_type = "text"
            if file_name.endswith(".md"):
                format_type = "markdown"
            elif file_name.endswith(".html"):
                format_type = "html"
            ExportManager.export_text(self.output_text.toPlainText(), file_name, format_type)

    def reformulate_text(self):
        if not self.input_text.toPlainText().strip():
            QMessageBox.warning(self, "Warning", "Please enter text to reformulate.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.reformulate_button.setEnabled(False)
        self.reformulate_button.setText("En cours...")

        try:
            prompt = f"""<|im_start|>system
{self.system_prompt}
<|im_end|>
<|im_start|>user
Texte à reformuler: {self.input_text.toPlainText()}
Ton: {self.tone_section.getSelectedTag()}
Format: {self.format_section.getSelectedTag()}
Longueur: {self.length_section.getSelectedTag()}
<|im_end|>
<|im_start|>assistant"""

            self.progress_bar.setValue(30)
            
            response = requests.post(f'{self.ollama_url}/api/generate',
                          json={
                              "model": self.current_model,
                              "prompt": prompt,
                              "stream": False
                          })
            
            self.progress_bar.setValue(70)
            
            if response.status_code == 200:
                result = response.json()
                reformulated_text = result['response']
                
                lines = reformulated_text.split('\n')
                cleaned_lines = [line for line in lines if not any(x in line.lower() for x in 
                               ['paramètre', 'ton:', 'format:', 'longueur:', 'voici', 'reformulation'])]
                cleaned_text = '\n'.join(cleaned_lines).strip()
                
                self.output_text.setText(cleaned_text)
                
                parameters = {
                    "tone": self.tone_section.getSelectedTag(),
                    "format": self.format_section.getSelectedTag(),
                    "length": self.length_section.getSelectedTag()
                }
                self.history_manager.add_entry(
                    self.input_text.toPlainText(),
                    cleaned_text,
                    parameters
                )
            else:
                QMessageBox.critical(self, "Error", "Reformulation failed. Please try again.")
            
            self.progress_bar.setValue(100)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Reformulation failed: {str(e)}")
        finally:
            self.reformulate_button.setEnabled(True)
            self.reformulate_button.setText("Reformuler")
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())

    def clear_output(self):
        self.output_text.clear()

def main():
    app = QApplication(sys.argv)
    window = ReformulatorApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()