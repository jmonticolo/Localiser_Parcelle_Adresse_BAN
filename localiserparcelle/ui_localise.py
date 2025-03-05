import time
from pathlib import Path

from qgis.core import QgsApplication
from qgis.gui import (
    QgsBusyIndicatorDialog,
    QgsCollapsibleGroupBox,
    QgsColorButton,
    QgsFilterLineEdit,
    QgsOpacityWidget,
)
from qgis.PyQt.QtCore import (
    QMetaObject,
    QModelIndex,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QTimer,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .http_finder import AdresseBanFinder

try:
    _encoding = QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)

except AttributeError:

    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class Ui_Dialog:
    def setupUi(self):
        self.setObjectName("Dialog")
        self.resize(380, 380)
        icon = Path.parent(__file__) / "icons" / "icone.png"
        self.setWindowIcon(QIcon(icon))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.gridLayout = QGridLayout(self)
        self.gridLayout.setMargin(5)
        self.gridLayout.setObjectName("gridLayout")

        self.GroupBox = QGroupBox(self)
        self.GroupBox.setObjectName("GroupBox")
        self.GroupBox.setTitle("")

        self.gridLayout_2 = QGridLayout(self.GroupBox)
        self.gridLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.gridLayout_2.setMargin(10)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.lRegion = QComboBox(self.GroupBox)
        self.lRegion.setObjectName("lRegion")
        self.lRegion.setLayoutDirection(Qt.LeftToRight)
        # self.lRegion.setSizeAdjustPolicy( QComboBox.AdjustToContentsOnFirstShow )
        self.lRegion.setEditable(True)
        self.lRegion.setInsertPolicy(QComboBox.NoInsert)
        self.lRegion.lineEdit().setPlaceholderText("Choisir la région")
        self.gridLayout_2.addWidget(self.lRegion, 0, 1, 1, 3)
        # --
        self.bMajReg = QPushButton(
            QgsApplication.getThemeIcon("/mActionRefresh.svg"),
            "",
        )  # 'Rafraichir')
        self.bMajReg.setToolTip("Mettre à jour la liste des régions")
        self.bMajReg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gridLayout_2.addWidget(self.bMajReg, 0, 4, 1, 1)

        self.lDepartement = QComboBox(self.GroupBox)
        self.lDepartement.setObjectName("lDepartement")
        # self.lDepartement.setSizeAdjustPolicy( QComboBox.AdjustToContentsOnFirstShow )
        self.lDepartement.setEditable(True)
        self.lDepartement.setInsertPolicy(QComboBox.NoInsert)
        self.lDepartement.lineEdit().setPlaceholderText("Choisir le département")
        self.gridLayout_2.addWidget(self.lDepartement, 1, 1, 1, 3)
        # --
        self.bMajDep = QPushButton(
            QgsApplication.getThemeIcon("/mActionRefresh.svg"), ""
        )
        self.bMajDep.setToolTip("Mettre à jour la liste des départements")
        self.bMajDep.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gridLayout_2.addWidget(self.bMajDep, 1, 4, 1, 1)

        self.lCommune = filteredComboBox(self.GroupBox)
        self.lCommune.setObjectName("lCommune")
        self.lCommune.setToolTip(
            "Choisir la commune dans la liste ou saisir son code INSEE"
            " ou les premiers caractères de son nom",
        )
        # self.lCommune.setSizeAdjustPolicy( QComboBox.AdjustToContentsOnFirstShow )
        self.lCommune.setEditable(True)
        self.lCommune.setInsertPolicy(QComboBox.NoInsert)
        self.lCommune.lineEdit().setPlaceholderText("Choisir la commune")
        self.gridLayout_2.addWidget(self.lCommune, 2, 1, 1, 3)
        # --
        self.bMajCom = QPushButton(
            QgsApplication.getThemeIcon("/mActionRefresh.svg"),
            "",
        )
        self.bMajCom.setToolTip("Mettre à jour la liste des communes")
        self.bMajCom.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gridLayout_2.addWidget(self.bMajCom, 2, 4, 1, 1)

        self.infracommune = QTabWidget(self.GroupBox)
        self.infracommune.setObjectName("infracommune")
        self.infracommune.setEnabled(True)
        self.infracommune.setMinimumSize(QSize(320, 120))
        self.infracommune.setLayoutDirection(Qt.LeftToRight)
        self.infracommune.setAutoFillBackground(False)
        self.infracommune.setElideMode(Qt.ElideNone)
        self.infracommune.setUsesScrollButtons(False)
        self.infracommune.setDocumentMode(False)
        self.infracommune.setTabsClosable(False)
        self.infracommune.setMovable(False)

        self.parcelle = QWidget()
        self.parcelle.setObjectName("parcelle")

        self.lSection = QComboBox(self.parcelle)
        self.lSection.setGeometry(20, 10, 160, 25)
        self.lSection.setObjectName("lSection")
        # self.lSection.addItem("")
        self.lSection.setEditable(True)
        self.lSection.setInsertPolicy(QComboBox.NoInsert)
        self.lSection.lineEdit().setPlaceholderText("Choisir la section")

        self.lParcelle = filteredComboBox(self.parcelle)  # QComboBox(self.parcelle) #
        self.lParcelle.setEditable(True)
        self.lParcelle.setInsertPolicy(QComboBox.NoInsert)
        self.lParcelle.lineEdit().setPlaceholderText("Choisir la parcelle")
        # self.lParcelle.setModelColumn(0)
        self.lParcelle.setGeometry(20, 50, 160, 25)
        self.lParcelle.setObjectName("lParcelle")
        # self.lParcelle.addItem("")

        icon = Path.parent(__file__) / "icons" / "parcelle.png"
        self.infracommune.addTab(self.parcelle, QIcon(icon), "")
        self.adresse = QWidget()
        self.adresse.setMinimumSize(QSize(294, 0))
        self.adresse.setObjectName("adresse")

        self.adrin = AutocompleteBanLineEdit(self.adresse)
        self.adrin.setEnabled(True)
        self.adrin.setInputMethodHints(Qt.ImhPreferUppercase | Qt.ImhUppercaseOnly)
        self.adrin.setObjectName("adrin")
        self.ladrin = QLabel(self.adresse)
        self.ladrin.setEnabled(True)
        self.ladrin.setGeometry(14, 0, 270, 23)
        self.ladrin.setObjectName("ladrin")

        self.adrout = QLabel(self.adresse)
        self.adrout.setEnabled(False)
        self.adrout.setGeometry(5, 49, 301, 71)
        self.adrout.setFrameShape(QFrame.NoFrame)
        self.adrout.setText("")
        self.adrout.setObjectName("adrout")

        icon = Path.parent(__file__) / "icons" / "adresse.png"
        self.infracommune.addTab(self.adresse, QIcon(icon), "")
        self.gridLayout_2.addWidget(self.infracommune, 3, 1, 1, 4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(7)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout_2.addLayout(self.horizontalLayout, 4, 1, 1, 4)
        # --
        self.bZoom = QPushButton(self.GroupBox)
        self.bZoom.setDefault(True)
        self.bZoom.setObjectName("bZoom")
        self.bZoom.setStyleSheet("QPushButton { padding:3px 50px; font-weight:bold; }")
        # self.bZoom.setStyleSheet("QPushButton { padding:2px 60px; background-color:#00eeee; border:1px solid #888; border-radius:3px; border-style:outset; font-size:12pt; font-weight:bold; color:#090909; }")
        self.horizontalLayout.addWidget(self.bZoom)
        # --
        self.bErase = QPushButton(self.GroupBox)
        self.bErase.setAutoDefault(False)
        self.bErase.setObjectName("bErase")
        self.horizontalLayout.addWidget(self.bErase)
        # --
        self.busyIndicator = QgsBusyIndicatorDialog(
            "",
            self,
            fl=Qt.WindowFlags(),
        )  # Widget)
        self.busyIndicator.setVisible(False)
        self.busyIndicator.setMinimumSize(50, 10)
        try:  # Pour reduire sa largeur :
            self.busyIndicator.children()[0].setContentsMargins(0, 0, 0, 0)
            self.busyIndicator.children()[0].setSpacing(0)
            self.busyIndicator.children()[1].setVisible(False)
            self.busyIndicator.children()[2].setTextVisible(False)
        except:
            pass
        self.horizontalLayout.addWidget(self.busyIndicator)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.optionGroupBox = QgsCollapsibleGroupBox(self.GroupBox)
        self.optionGroupBox.setObjectName("optionGroupBox")
        self.optionGroupBox.setMinimumSize(QSize(320, 110))

        self.gridLayout_2.addWidget(self.optionGroupBox, 6, 1, 1, 4)

        optionsVLayout = QVBoxLayout()
        optionsVLayout.setSpacing(2)
        optionsVLayout.setContentsMargins(10, 10, 10, 10)
        self.optionGroupBox.setLayout(optionsVLayout)

        zoomHLayout = QHBoxLayout()
        optionsVLayout.addLayout(zoomHLayout)

        self.lblScale = QLabel()  # self.optionGroupBox)
        self.lblScale.setObjectName("lblScale")
        self.lblScale.setAlignment(Qt.AlignLeft)
        # self.lblScale.setGeometry(10, 20, 160, 25)
        zoomHLayout.addWidget(self.lblScale)

        self.scale = QSpinBox()  # self.optionGroupBox)
        self.scale.setMinimum(10)
        self.scale.setMaximum(5000)
        self.scale.setSingleStep(10)
        self.scale.setProperty("value", 50)
        self.scale.setObjectName("scale")
        # self.scale.setGeometry(175, 15, 50, 25)
        zoomHLayout.addWidget(self.scale)

        self.dynaMarker = QCheckBox(self.optionGroupBox)
        self.dynaMarker.setObjectName("scale")
        # self.dynaMarker.setGeometry(10, 40, 125, 25)
        optionsVLayout.addWidget(self.dynaMarker)

        colorHLayout = QHBoxLayout()
        optionsVLayout.addLayout(colorHLayout)

        self.lblColorOpacity = QLabel(self.optionGroupBox)
        self.lblColorOpacity.setObjectName("lblColorOpacity")
        self.lblColorOpacity.setAlignment(Qt.AlignLeft)
        # self.lblColorOpacity.setGeometry(10, 75, 120, 25)
        colorHLayout.addWidget(self.lblColorOpacity)

        # self.colorMarker.setGeometry(120, 70, 80, 25)
        self.colorMarker = QgsColorButton(self.optionGroupBox, "", None)
        colorHLayout.addWidget(self.colorMarker)
        self.opacityMarker = QgsOpacityWidget(self.optionGroupBox)
        spinBoxOpa = self.opacityMarker.layout().itemAt(1).widget()
        spinBoxOpa.setShowClearButton(False)
        spinBoxOpa.setMinimumSize(QSize(0, 0))
        spinBoxOpa.setDecimals(0)
        # self.opacityMarker.setGeometry(210, 70, 200, 25)
        colorHLayout.addWidget(self.opacityMarker)

        self.gridLayout_2.addLayout(self.horizontalLayout_2, 10, 1, 1, 1)
        self.gridLayout.addWidget(self.GroupBox, 0, 0, 1, 1)

        self.horizontalLayoutBottom = QHBoxLayout()
        self.horizontalLayoutBottom.setSpacing(7)
        self.horizontalLayoutBottom.setObjectName("horizontalLayoutBottom")

        self.bInfo = QPushButton(self.GroupBox)
        self.bInfo.setObjectName("bInfo")

        self.bQuit = QPushButton(self.GroupBox)
        self.bQuit.setObjectName("bQuit")
        self.bQuit.setAutoDefault(False)

        self.horizontalLayoutBottom.addWidget(self.bInfo)
        self.horizontalLayoutBottom.addWidget(self.bQuit)
        self.gridLayout_2.addLayout(self.horizontalLayoutBottom, 8, 1, 1, 1)

        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.bErase.setSizePolicy(sizePolicy)
        self.bZoom.setSizePolicy(sizePolicy)
        self.scale.setSizePolicy(sizePolicy)
        self.bInfo.setSizePolicy(sizePolicy)
        self.bQuit.setSizePolicy(sizePolicy)

        self.retranslateUi()
        self.infracommune.setCurrentIndex(1)
        QMetaObject.connectSlotsByName(self)
        self.lCommune.setFocus()
        self.setTabOrder(self.lRegion, self.lDepartement)
        self.setTabOrder(self.lDepartement, self.lCommune)
        self.setTabOrder(self.lCommune, self.lSection)
        self.setTabOrder(self.lSection, self.lParcelle)
        self.setTabOrder(self.lParcelle, self.bZoom)
        self.setTabOrder(self.bZoom, self.bInfo)

    def resizeEvent(self, event):
        self.adrin.setGeometry(5, 23, self.width() - 60, 26)

    def retranslateUi(self):
        self.setWindowTitle(
            _translate(
                "Dialog", "Localiser une commune, une parcelle ou une adresse", None,
            ),
        )
        self.bInfo.setText(_translate("Dialog", "à propos", None))
        self.lCommune.setItemText(0, _translate("Dialog", "-- COMMUNE --", None))
        self.lDepartement.setItemText(
            0, _translate("Dialog", "-- DEPARTEMENT --", None)
        )
        self.lRegion.setItemText(0, _translate("Dialog", "-- REGION --", None))
        self.lSection.setItemText(0, _translate("Dialog", "-- SECTION --", None))
        self.lParcelle.setItemText(0, _translate("Dialog", "-- PARCELLE --", None))
        self.infracommune.setTabText(
            self.infracommune.indexOf(self.parcelle),
            _translate("Dialog", "Parcelle", None),
        )
        self.ladrin.setText(_translate("Dialog", "N° et /ou voie :", None))
        self.infracommune.setTabText(
            self.infracommune.indexOf(self.adresse),
            _translate("Dialog", "Adresse", None),
        )
        self.bZoom.setText(_translate("Dialog", "Localiser", None))
        self.bErase.setText(_translate("Dialog", "Effacer le marqueur", None))
        self.bQuit.setText(_translate("Dialog", "Fermer", None))
        self.optionGroupBox.setTitle(
            f"{_translate("Dialog", "Options du marqueur", None)} :",
        )
        self.lblScale.setText(
            f"{_translate("Dialog", "Zoom élément trouvé  (m)", None)} :",
        )
        self.lblColorOpacity.setText(
            f"{_translate("Dialog", "Couleur et opacité", None)} :",
        )
        self.dynaMarker.setText(_translate("Dialog", "Marqueur animé", None))


class filteredComboBox(QComboBox):

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)

        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        self.completer = QCompleter(self.pFilterModel, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        def filter(text: str):
            self.pFilterModel.setFilterFixedString(text)

        def keyPress():
            if self.count() > self.maxIndex:
                self.removeItem(self.count() - 1)
                self.setCurrentIndex(0)

        self.lineEdit().textEdited.connect(filter)
        self.lineEdit().returnPressed.connect(keyPress)
        self.completer.activated.connect(self.on_completer_activated)

    def getMaxIndex(self):
        self.maxIndex = self.count()

    def on_completer_activated(self, text: str):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            # fix bug
            self.activated[int].emit(index)

    def setModel(self, model):
        super().setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super().setModelColumn(column)


class AutocompleteBanLineEdit(QgsFilterLineEdit):
    """mosty from discovery plugin."""

    def __init__(self, parent: QWidget = None):
        # Variables pour faciliter la gestion des requêtes
        super().__init__(parent)
        self.timer = QTimer()
        self.line_edit_timer = QTimer()
        self.line_edit_timer.setSingleShot(True)
        self.line_edit_timer.timeout.connect(self.reset_line_edit_after_move)
        self.next_query_time = None
        self.last_query_time = time.time()
        self.search_delay = 0.5  # s
        self.query_text = None
        self.codecity = None

        self.search_results = []
        self.search_result = None
        self.completer = None

        # Texte pour inviter l'utilisateur à entrer une adresse
        self.setPlaceholderText("Rechecher une adresse...")

        # Initialisation du ompleter
        self.completer = QCompleter([])  # Initialise with en empty list
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setMaxVisibleItems(1000)
        # On laisse le tri à l'api BAN
        self.completer.setModelSorting(QCompleter.UnsortedModel)
        # Montre toutes les possibilité
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.activated[QModelIndex].connect(self.on_result_selected)
        self.completer.highlighted[QModelIndex].connect(self.on_result_highlighted)
        self.setCompleter(self.completer)

        # Signaux
        self.textEdited.connect(self.on_search_text_changed)

        # Résultats de la recherches
        self.search_results = []

        # Initialisation du timer pour faire des recherches périodiques
        self.timer.timeout.connect(self.do_search)
        self.timer.start(100)

    def clear_suggestions(self):
        model = self.completer.model()
        model.setStringList([])

    def on_search_text_changed(self, new_search_text: str):

        self.query_text = new_search_text

        if len(new_search_text.strip()) < 3:
            # Suppression de l'ensemble des suggestion
            # si l'utilisateur supprime sa recherche
            self.clear_suggestions()
            return
        self.schedule_search(self.query_text)

    def do_search(self):
        if self.next_query_time is not None and self.next_query_time < time.time():
            # Lancement de la requête
            self.next_query_time = None  # Préviens la requête d'être répétée
            self.last_query_time = time.time()
            self.perform_search()

    def perform_search(self):
        self.search_results = []
        suggestions = []
        adresse_ban_finder = AdresseBanFinder(
            search=self.query_text, codecity=self.codecity, parent=self.parent()
        )
        suggestions = adresse_ban_finder.get_suggestions()
        self.search_results = adresse_ban_finder.get_search_results()
        model = self.completer.model()
        model.setStringList(suggestions)
        self.completer.complete()

    def schedule_search(self, query_text: str):
        # Mise à jour de la recherche à lancer et du temps pour que la requête s'exécute
        self.query_text = query_text
        self.next_query_time = time.time() + self.search_delay

    def set_codecity(self, codecity):
        self.codecity = str(codecity)

    # Sélection faite, stockage du résultat dans la search_result
    def on_result_selected(self, result_index):
        if result_index.row() >= len(self.search_results):
            return  # Si user clique trop vite sur liste non maj apres saisie
        self.search_result = self.search_results[result_index.row()]
        self.clear_suggestions()

    def select_result(self, result_data):
        self.line_edit_timer.start(0)

    def on_result_highlighted(self, result_idx):
        self.line_edit_timer.start(0)

    def reset_line_edit_after_move(self):
        self.setText(self.query_text)

    def get_search_result(self):
        """Renvoie le résultat de la requête."""
        return self.search_result
