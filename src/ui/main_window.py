import sys
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from data_manager import DataManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        
        self.setWindowTitle("Gekisou Arena - Gestionnaire de Collection")
        self.resize(1000, 700)
        
        # Activation du Drag & Drop sur la fenêtre
        self.setAcceptDrops(True)
        
        # Widget central et layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        
        # Message d'accueil / instructions pour le Drag & Drop (qui ne bouge plus !)
        self.info_label = QLabel(
            "Glissez et déposez votre fichier <b>save.json</b> ici\n"
            "pour générer ou mettre à jour votre collection !"
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 16px; color: #888; border: 2px dashed #444; border-radius: 10px; padding: 40px;")
        
        self.layout.addWidget(self.info_label)
        self.setCentralWidget(self.central_widget)

        # --- Notification Toast (Discrète, coin inférieur droit) ---
        self.toast_label = QLabel(self)
        self.toast_label.setStyleSheet("""
            background-color: #2e7d32;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 12px 18px;
            font-size: 13px;
        """)
        self.toast_label.hide()
        
        # Timer pour masquer automatiquement le toast après 3 secondes
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast_label.hide)

    def show_toast(self, message):
        """Affiche une popup toast dans le coin inférieur droit pendant 3 secondes."""
        self.toast_label.setText(f"✅ {message}")
        self.toast_label.adjustSize()
        
        # Calcul de la position (Coin inférieur droit avec 20px de marge)
        margin = 20
        x = self.width() - self.toast_label.width() - margin
        y = self.height() - self.toast_label.height() - margin
        self.toast_label.move(x, y)
        
        self.toast_label.show()
        self.toast_label.raise_()
        self.toast_timer.start(3000) # 3000 ms = 3 secondes

    def resizeEvent(self, event):
        """Permet de repositionner le toast si on redimensionne la fenêtre."""
        super().resizeEvent(event)
        if self.toast_label.isVisible():
            margin = 20
            x = self.width() - self.toast_label.width() - margin
            y = self.height() - self.toast_label.height() - margin
            self.toast_label.move(x, y)

    def dragEnterEvent(self, event):
        """Vérifie si le fichier glissé est bien un JSON."""
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.toLocalFile().endswith(".json"):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        """Gère l'action de lâcher le fichier dans la fenêtre."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            try:
                # Récupération des stats de mise à jour
                total_cards, added_count, has_changed = self.data_manager.build_or_update_collection(file_path)
                
                # Gestion dynamique du message Toast selon les changements
                if not has_changed:
                    self.show_toast("Aucun changement détecté dans la sauvegarde.")
                else:
                    msg = f"Mise à jour réussie ! ({total_cards} cartes"
                    if added_count > 0:
                        msg += f" • {added_count} nouvelle(s))"
                    else:
                        msg += " • Niveaux/Stats mis à jour)"
                    self.show_toast(msg)
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors du parsing :\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())