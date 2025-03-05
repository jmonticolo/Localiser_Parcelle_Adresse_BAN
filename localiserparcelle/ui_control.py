from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QApplication, QDialog, QWidget

from .ui_localise import Ui_Dialog


class ui_control(QDialog, Ui_Dialog):
    def __init__(self, parent: QWidget, fl):
        QDialog.__init__(self, parent, fl)
        self.setupUi()

    def commune_adresse_disable(self, output):
        self.adrin.clear()
        self.adrout.clear()
        self.infracommune.setCurrentIndex(0)
        self.infracommune.setEnabled(False)

    def commune_adresse_enable(self, output):
        self.adrout.clear()
        self.infracommune.setEnabled(True)

    def affiche_adresse(self, output):
        self.adrout.setEnabled(True)
        self.adrout.setText("%s" % output)

    def efface_adresse(self, output):
        self.adrout.clear()

    def set_dialog_busy(self, dialogShouldBeBusy: bool = True):
        """Fonction qui rend l'interface occupée et l'indique à l'utilisateur."""
        # s = QSettings()
        # networkTimeout = s.value( "Qgis/networkAndProxy/networkTimeout", "60000" ) # Par defaut, c'est 60000
        if dialogShouldBeBusy:
            # s.setValue( "Qgis/networkAndProxy/networkTimeout", "10000" ) #  Imposer un délai de 10 secondes
            # Afficher un sablier à la place du curseur :
            self.busyIndicator.setVisible(True)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
        else:
            # s.setValue( "Qgis/networkAndProxy/networkTimeout", networkTimeout ) # Retablir le parametre d'origine
            QApplication.restoreOverrideCursor()  # Retablir le curseur d'origine
            self.busyIndicator.setVisible(False)
