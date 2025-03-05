#!/usr/bin/env python

from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsNetworkAccessManager,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
)
from qgis.gui import QgsMapCanvasItem, QgsVertexMarker
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QObject,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSettings,
    Qt,
    QTranslator,
    pyqtProperty,
)
from qgis.PyQt.QtGui import QColor, QIcon, QPainter
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QSizePolicy
from qgis.utils import iface, pluginMetadata

from .ban_locator_filter import BanLocatorFilter
from .ui_control import ui_control

cePlugin = Path(__file__).parent.name
PluginVersion = pluginMetadata(
    cePlugin,
    "version",
)  ## Pour les changements, voir metadata.txt


class plugin(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        # translation environment
        self.plugin_dir = Path(__file__).parent
        # locale = QSettings().value("locale/userLocale")[0:2]
        locale = "fr"
        localePath = Path(self.plugin_dir) / "i18n" / f"localiseparcelle_{locale}.qm"
        if Path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(str(localePath))
            QCoreApplication.installTranslator(self.translator)

        # locator
        self.locator_filter = BanLocatorFilter(self)
        self.iface.registerLocatorFilter(self.locator_filter)

    def initGui(self):
        self.settings = "Plugin-LocaliserParcelleAdresse/"  # Pour mémoriser les parametres de recherche
        self.manager = QgsNetworkAccessManager.instance()
        self.tmpGeometry = []
        self.lstListes = []  # Les listes déroulantes de l'écran : region, dep, comm...
        icon = str(Path(__file__).parent / "icons" / "icone.png")
        win = iface.mainWindow()
        self.pluginMenu = iface.pluginMenu().addMenu(
            QIcon(icon), "&Localiser Parcelle ou Adresse (Ban)"
        )

        self.action = QAction(QIcon(icon), "&Localiser Parcelle Adresse (Ban)", win)
        iface.mainWindow().setAttribute(Qt.WA_DeleteOnClose)
        self.action.setWhatsThis("Localiser une commune, une parcelle ou une adresse")
        self.action.setStatusTip("Localiser une commune, une parcelle ou une adresse")
        self.action.triggered.connect(self.run)
        iface.addToolBarIcon(self.action)
        # iface.addPluginToMenu("&Localiser Parcelle ou Adresse (Ban)", self.action)
        self.pluginMenu.addAction(self.action)

        self.actionAide = QAction(
            QIcon(str(Path(__file__).parent / "icons" / "help.png")),
            f"A propos du plugin (version {PluginVersion})",
            win,
        )
        self.actionAide.triggered.connect(self.getAbout)
        self.pluginMenu.addAction(self.actionAide)

        self.barInfo = iface.messageBar()
        self.barInfo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.color = QColor(0, 255, 0, 125)

        self.dlg = None
        self.marker = None
        ### Rétablir la dernière valeur du zoom et l'option de marqueur choisies par le user:
        s = QSettings()  # QGIS options settings
        scale = s.value(f"{self.settings}zoom", "100")
        self.scaleZoom = int(scale)
        self.marqueurDyna = s.value(f"{self.settings}marker", False, type=bool)

    def unload(self):
        self.cleanMarker()
        self.pluginMenu.parentWidget().removeAction(
            self.pluginMenu.menuAction(),
        )  # Remove from Extension menu
        # self.iface.removePluginMenu("&Localiser Parcelle ou Adresse (Ban)",self.action)
        iface.removeToolBarIcon(self.action)
        iface.deregisterLocatorFilter(self.locator_filter)
        self.locator_filter = None

    def run(self):
        if self.dlg:  # Si l'écran a deja ete lancé dans cette session
            self.dlg.show()
            self.dlg.activateWindow()
            print("self.dlg.lRegion.count() =", self.dlg.lRegion.count())
            # Si liste des regions vide (soucis reseau ou autre) :
            # if self.dlg.lRegion.count()<2:  self.getListAction(0) # Charger la liste
            return

        win = iface.mainWindow()
        # self.dlg = ui_control(None, Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint )
        self.dlg = ui_control(
            win, Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        # Il faut positionner le dialog MANUELLEMENT, sinon Qt va le repositionner automatiquement à chaque hide -> show :
        self.dlg.setGeometry(
            win.geometry().x() + 50,
            win.geometry().y() + 50,
            200,
            200,
        )  # """

        # fermeture de la fenetre du plugin on deroute sur une fonction interne
        # self.dlg.closeEvent = self.close_Event
        ########################
        # INSERTION DES SIGNAUX #
        ########################
        self.dlg.bInfo.clicked.connect(self.getAbout)
        # self.dlg.lastWindowClosed.connect(self.closeDlg)
        self.dlg.bQuit.clicked.connect(self.closeDlg)
        self.dlg.bErase.clicked.connect(self.cleanSearch)
        self.dlg.lRegion.activated[int].connect(self.getListDepartements)
        self.dlg.bMajReg.released.connect(lambda: self.getListAction(0))

        self.dlg.lDepartement.activated[int].connect(self.getListCommunes)
        self.dlg.bMajDep.released.connect(lambda: self.getListAction(1))
        self.dlg.lCommune.activated[int].connect(self.getListSections)
        # self.dlg.lCommune.editTextChanged.connect(self.getListSectionsByText)
        self.dlg.lCommune.activated[int].connect(self.updateCodecity)
        # self.dlg.lCommune.currentIndexChanged.connect(self.updateCodecity)
        self.dlg.bMajCom.released.connect(lambda: self.getListAction(2))

        self.dlg.lSection.activated[int].connect(self.getListParcelles)
        self.dlg.lParcelle.editTextChanged.connect(self.findParcelleByText)

        self.dlg.bZoom.clicked.connect(self.getLocation)
        self.dlg.adrin.returnPressed.connect(self.getLocationByAdress)
        self.dlg.colorMarker.setColor(self.color)
        self.dlg.colorMarker.colorChanged.connect(self.setColor)
        self.dlg.dynaMarker.setChecked(self.marqueurDyna)  # init dans initGui
        self.dlg.dynaMarker.clicked.connect(self.setMarker)
        self.dlg.scale.setValue(self.scaleZoom)  # init dans initGui
        self.dlg.scale.valueChanged.connect(self.setScale)

        self.dlg.opacityMarker.setOpacity(float(self.color.alpha() / 255))
        self.dlg.opacityMarker.opacityChanged.connect(self.setColor)

        self.dlg.show()
        self.dlg.activateWindow()

        ### VARIABLES D'INITIALISATION
        self.lstListes = [
            self.dlg.lRegion,
            self.dlg.lDepartement,
            self.dlg.lCommune,
            self.dlg.lSection,
            self.dlg.lParcelle,
        ]
        self.lstListes_label = [
            "-- REGION --",
            "-- DEPARTEMENT --",
            "-- COMMUNE --",
            "-- SECTION --",
            "-- PARCELLE --",
        ]
        self.results = [1, 2, 3, 4, 5]
        self.indexPrecedent = -2

        from .http_finder import CartelieFinder

        self.cartelie = CartelieFinder(self.dlg)

        self.getListAction(0, MAJ=False)

        ### Rétablir la dernière région et dernier département choisi par le user:
        s = QSettings()  # QGIS options settings

        region = s.value(f"{self.settings}region", "")
        if region == "":
            return
        region = int(region)
        if region > self.dlg.lRegion.count() - 1:
            return  # Si le nb de regions a changé !
        self.dlg.lRegion.setCurrentIndex(region)

        dep = s.value(
            f"{self.settings}departement",
            "",
        )  # Il faut le faire avant getListDepartements()
        self.getListDepartements()
        if dep == "":
            return
        dep = int(dep)
        if dep > self.lstListes[1].count() - 1:
            return  # Si le nb de dep a changé !
        self.lstListes[1].setCurrentIndex(dep)

        self.getListCommunes()

    def cleanSearch(self):
        # self.dlg.commune_adresse_disable('')
        # for j in range(3, 5): self.lstListes[j].clear() #; self.lstListes[j].addItem(self.lstListes_label[j])
        # self.lstListes[2].setCurrentIndex(0)
        self.cleanMarker()

    def cleanMarker(self):
        # detruire les precedents marqueurs
        for i in range(len(self.tmpGeometry)):
            self.iface.mapCanvas().scene().removeItem(self.tmpGeometry[i])
        self.marker = None
        self.tempGeometry = []

    def closeDlg(self):
        self.dlg.reject()
        # self.cleanMarker();

    def getListDepartements(self, index=0):
        self.getListAction(1, MAJ=False)

    def getListCommunes(self, index=0):
        self.dlg.lCommune.blockSignals(True)
        # self.dlg.lCommune.activated[int].disconnect(self.getListSections) #Eviter req commune
        # self.dlg.lCommune.editTextChanged.disconnect(self.getListSectionsByText)
        self.getListAction(2, MAJ=False)
        # self.dlg.lCommune.activated[int].connect(self.getListSections)
        # self.dlg.lCommune.editTextChanged.connect(self.getListSectionsByText)
        self.dlg.lCommune.blockSignals(False)

    def getListSectionsByText(self, text: str):
        text = self.dlg.lCommune.currentText()
        index = self.dlg.lCommune.findText(text)
        try:
            if index > -1 and index < (self.dlg.lCommune.maxIndex - 1):
                self.dlg.lCommune.setCurrentIndex(index)
                self.getListAction(3)
        except:
            pass

    def getListSections(self, index):
        self.getListAction(3)

    def getListParcelles(self, index):
        self.dlg.lParcelle.blockSignals(True)
        self.getListAction(4)
        self.dlg.lParcelle.blockSignals(False)

    def findParcelleByText(self, text: str):
        # text = self.dlg.lParcelle.currentText()
        # text = text.lstrip("0") #if len(text)>1 :
        if text == "":
            self.dlg.lParcelle.lineEdit().setStyleSheet(
                "QLineEdit{background-color:#ffffff;}",
            )
            return
        index = self.dlg.lParcelle.findText(text)  # , Qt.MatchContains )
        if index < 0 or index > self.dlg.lParcelle.maxIndex - 1:
            self.dlg.lParcelle.lineEdit().setStyleSheet(
                "QLineEdit{background-color:#ff9999}",
            )
            return
        self.dlg.lParcelle.lineEdit().setStyleSheet(
            "QLineEdit{background-color:#ffffff;}",
        )
        try:
            self.dlg.lParcelle.setCurrentIndex(index)
        except:
            pass

    #######################################
    # REINITIALISATION DES LISTES D'APRES #
    #######################################
    def getListAction(self, indexListe, MAJ=True):
        if indexListe == 3:  # Pour eviter les requetes doublons generé par lCommune :
            index = self.lstListes[indexListe - 1].currentIndex()
            if index == self.indexPrecedent:
                return
            else:
                self.indexPrecedent = index

        for j in range(indexListe, 5):
            self.lstListes[
                j
            ].clear()  # ; self.lstListes[j].addItem(self.lstListes_label[j])

        #############################################
        # RECUPERATION des DONNEES SERVICE CARTELIE #
        #############################################
        s = QSettings()
        networkTimeout = s.value(
            "Qgis/networkAndProxy/networkTimeout",
            "60000",
        )  # Sauver le param Timeout
        s.setValue(
            "Qgis/networkAndProxy/networkTimeout",
            "20000",
        )  #  Imposer un délai de 20 secondes

        if indexListe > 0:
            index = self.lstListes[indexListe - 1].currentIndex()  # currentIndex()-1
            if index < 0 or index >= len(self.results[indexListe - 1]):
                return
            code = self.results[indexListe - 1][index]["code"]
            result = self.cartelie.appel(indexListe, code, forcerMAJ=MAJ)
        else:
            result = self.cartelie.appel(indexListe, forcerMAJ=MAJ)

        s.setValue(
            "Qgis/networkAndProxy/networkTimeout",
            networkTimeout,
        )  # Retablir le parametre d'origine

        if not result:
            self.dlg.set_dialog_busy(False)
            QMessageBox.warning(
                self.dlg,
                "Erreur réseau",
                "Serveurs de localisation (Géoref et Cartélie) injoignables :"
                "\n 1. Ces serveurs centraux sont peut-être hors-service."
                "\n 2. Ou bien il y a un problème sur votre réseau"
                " ou celui du ministère.\n\n"
                "Vous pouvez aussi vérifier vos paramètres réseau:"
                "\n   Préférences > Options > Réseau > Proxy",
            )
            return

        self.results[indexListe] = result
        ###################################
        # REMPLISSAGE DE LA LISTE D'APRES #
        ###################################
        n = len(result)
        for i in range(n):
            if indexListe == 1:
                libelle = f'{result[i]["nom"]} ({result[i]["code"]})'
            elif indexListe == 2:
                libelle = f'{result[i]["code"]} - {result[i]["nom"]}'
            else:
                libelle = result[i]["nom"].lstrip("0")
            # elif indexListe==4:	libelle = result[i]["nom"].lstrip("0")
            # else: libelle = result[i]["nom"]
            """if indexListe == 2 :
                libelle = "%s - %s" % (result[i]["code"], result[i]["nom"])
            else :
                libelle = "%s (%s)" % (result[i]["nom"], result[i]["code"]) if indexListe == 1 else result[i]["nom"] #"""
            self.lstListes[indexListe].addItem(libelle)
        try:
            self.lstListes[indexListe].getMaxIndex()
        except:
            pass

        self.lstListes[indexListe].setCurrentIndex(-1)

        ####  Enregistrer parametres de recherche ####
        if indexListe == 0:
            self.dlg.commune_adresse_disable("")
        elif indexListe == 1:  # Enregistre le choix de la région
            self.dlg.commune_adresse_disable("")
            s.setValue(f"{self.settings}region", index)
            s.setValue(f"{self.settings}departement", "")
        elif indexListe == 2:  # enregistre le choix du dép.
            self.dlg.commune_adresse_disable("")
            s.setValue(f"{self.settings}departement", index)
        elif indexListe == 3:
            self.dlg.commune_adresse_enable(self.dlg.lCommune.currentText())
        # FIN de : Enregistrer parametres de recherche

        self.dlg.set_dialog_busy(False)

    def getLocation(self):
        # Si tab Parcelle activer recherche parcelle
        (
            self.getLocationByParcelId()
            if self.dlg.infracommune.currentIndex() == 0
            else self.getLocationByAdress()
        )

    def getLocationByAdress(self):
        # http://api-adresse.data.gouv.fr/search/?q=rue&citycode=2A004&limit=5000
        self.dlg.adrout.clear()
        result = self.dlg.adrin.get_search_result()

        if not result:
            self.dlg.affiche_adresse(
                "<html><body><p align=left color=red><b>"
                "Adresse non trouvée"
                "</p></b></body></html>",
            )
            return

        adresse, score, typeInfo, x, y = result
        self.dlg.affiche_adresse(
            "<html><body><p align=left>"
            f"Trouvé ({typeInfo}):<br>{adresse}<br>correspondance={score} &#37;"
            "</p></body></html>",
        )
        # Transformer les coordonnees du 4326 du Gécodeur Etalab -> Systeme projection projet
        # recuperation CRS projet
        transformer = self.getTransformer(4326)
        point = transformer.transform(
            QgsPointXY(x, y), QgsCoordinateTransform.ForwardTransform
        )
        x, y = point[0], point[1]

        # Zoomer sur le point
        self.zoomTo(x, y, x, y)

    def getLocationByParcelId(self):
        ###################################################
        # RECUPERATION DE LA LISTE ACTIVE ET DE SON INDEX #
        ###################################################
        indexListe = None
        for i in range(4, -1, -1):
            if self.lstListes[i].currentIndex() > -1:  # 0 :
                # RECUPERATION DE L'ID DE LA LISTE
                indexListe = i
                break
        if indexListe is None:
            QMessageBox.information(
                self.iface.mainWindow(),
                "Zoom impossible",
                "Pas si vite! Vous n'avez même pas choisi de région où aller !",
            )
        else:
            index_lActuelle = self.lstListes[indexListe].currentIndex()  # -1

        result = self.results[indexListe][index_lActuelle]

        if not result:
            QMessageBox.warning(
                self.dlg,
                "Message :",
                "(Erreur Url) - Serveur Cartelie injoignable, réessayer plus tard ... !",
            )
            return

        xmin, ymin, xmax, ymax = (
            result["xmin"],
            result["ymin"],
            result["xmax"],
            result["ymax"],
        )
        transformer = self.getTransformer(2154)
        rect = transformer.transformBoundingBox(
            QgsRectangle(xmin, ymin, xmax, ymax),
            QgsCoordinateTransform.ForwardTransform,
        )
        # Zoomer sur le rectangle
        self.zoomTo(rect.xMinimum(), rect.yMaximum(), rect.xMaximum(), rect.yMinimum())

    def getTransformer(self, epsgCode):
        transformer = QgsCoordinateTransform()
        transformer.setSourceCrs(QgsCoordinateReferenceSystem(epsgCode))
        destCrs = QgsProject.instance().crs()
        transformer.setDestinationCrs(destCrs)
        return transformer

    def getMarkerLocationInMapCoordinates(self, marker):
        x, y = marker.x(), marker.y()
        point = marker.toMapCoordinates(QPoint(x, y))
        return point.x(), point.y()

    def setMarker(self):
        self.marqueurDyna = self.dlg.dynaMarker.isChecked()
        QSettings().setValue(
            f"{self.settings}marker",
            self.marqueurDyna,
        )  # Memoriser le parametre "marqueurDyna"
        if self.marker:
            mc = self.iface.mapCanvas()
            x, y = self.getMarkerLocationInMapCoordinates(self.marker)
            self.cleanMarker()
            self.marker = (
                dynaLocationMarker(mc, x, y, self.color)
                if self.marqueurDyna
                else basicLocationMarker(mc, x, y, self.color)
            )
            self.tmpGeometry.append(self.marker)
            mc.refresh()

    def setColor(self):
        alpha = int(self.dlg.opacityMarker.opacity() * 255)
        if self.dlg.sender() == self.dlg.colorMarker:
            self.color.setRgb(self.dlg.colorMarker.color().rgb())
        elif self.dlg.sender() == self.dlg.opacityMarker:
            self.color.setAlpha(alpha)
        if self.marker and not isinstance(self.marker, dynaLocationMarker):
            self.marker.setColor(self.color)

    def setScale(self):
        self.scaleZoom = self.dlg.scale.value()
        QSettings().setValue(
            f"{self.settings}zoom",
            self.scaleZoom,
        )  # Memoriser le parametre "Zoom"

        if self.marker:
            x, y = self.getMarkerLocationInMapCoordinates(self.marker)
            mc = self.iface.mapCanvas()
            # modif 2.2 gestion exception et mis a echelle 0
            try:
                if self.iface.mapCanvas().mapUnits() == 0:
                    scale = self.dlg.scale.value()  # si unités en metres
                else:
                    scale = (
                        0  # pas des metres donc on ne peut pas utiliser ce parametre.
                    )
            except Exception:
                scale = 0
            rect = QgsRectangle(x - scale, y - scale, x + scale, y + scale)
            mc.setExtent(rect)
            mc.refresh()

    def zoomTo(self, x, y, x1, y1):
        # Zoomer sur rectangle englobant
        mc = self.iface.mapCanvas()

        # modif 2.2 gestion exception et mis a echelle 0
        try:
            if self.iface.mapCanvas().mapUnits() == 0:
                scale = self.scaleZoom  # si unités en metres
            else:
                scale = 0  # pas des metres donc on ne peut pas utiliser ce parametre.
        except Exception:
            scale = 0
        rect = QgsRectangle(x - scale, y - scale, x1 + scale, y1 + scale)
        mc.setExtent(rect)

        self.cleanMarker()

        self.marker = (
            dynaLocationMarker(mc, rect.center().x(), rect.center().y(), self.color)
            if self.marqueurDyna
            else basicLocationMarker(
                mc,
                rect.center().x(),
                rect.center().y(),
                self.color,
            )
        )
        # self.marker = dynaLocationMarker(mc, rect.center().x(), rect.center().y(), self.color) if self.dlg.dynaMarker.isChecked() else basicLocationMarker(mc, rect.center().x(), rect.center().y(), self.color)
        self.tmpGeometry.append(self.marker)
        mc.refresh()

    def updateCodecity(self, idx):
        """Mets à jour le citycode pour filtrer la requete par code insee."""
        c = self.results[2][idx]["code"]  # c = self.results[2][idx-1]["code"]
        self.dlg.adrin.set_codecity(c)

    def getAbout(self):
        icon = str(Path(__file__).parent / "icons" / "icone.png")
        icon = icon.replace("\\", "/")
        html = (
            "Ce plugin exploite (par le protocole <b>HTTP</b>):<br>"
            "<ol><li>le service Web du Ministère de la Transition Ecologique et Solidaire"
            " de géolocalisation avec plusieurs échelles administratives"
            " (Région, Département, Commune, Section, Parcelle) ;</li>"
            "<li>le service web de géolocalisation à l'adresse"
            " Etalab.gouv.fr-BAN.</li></ol>"
            "Ces deux web services fonctionnent depuis des postes de travail ayant"
            " un accès internet, en utilisant la configuration réseau de qgis"
            " pour le protocole HTTP et le système de projection courant du projet"
            " pour toute transformation des coordonnées.<br><br>"
            f"<img src='{icon}'> Version {PluginVersion}"
        )
        QMessageBox.information(self.dlg, "A propos", html)


class basicLocationMarker(QgsVertexMarker):
    def __init__(self, canvas, x, y, color):
        super().__init__(canvas)
        self.canvas = canvas
        self.color = color
        self.map_pos = QgsPointXY(x, y)
        self.setCenter(self.map_pos)
        self.setColor(self.color)
        self.setIconSize(10)
        self.setIconType(QgsVertexMarker.ICON_X)  # ICON_BOX ICON_CROSS, ICON_X
        self.setPenWidth(2)


class dynaLocationMarker(QgsMapCanvasItem):

    class aniObject(QObject):
        def __init__(self):
            super().__init__()
            self._size = 0
            self.startsize = 0
            self.maxsize = 32

        @pyqtProperty(int)
        def size(self):
            return self._size

        @size.setter
        def size(self, value):
            self._size = value

    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.color = color
        self.map_pos = QgsPointXY(x, y)
        self.aniObject = self.aniObject()
        QgsMapCanvasItem.__init__(self, canvas)
        self.anim = QPropertyAnimation(self.aniObject, b"size")
        self.anim.setDuration(1000)
        self.anim.setStartValue(self.aniObject.startsize)
        self.anim.setEndValue(self.aniObject.maxsize)
        self.anim.setLoopCount(-1)
        self.anim.valueChanged.connect(self.value_changed)
        self.anim.start()

    @property
    def size(self):
        return self.aniObject.size

    @property
    def halfsize(self):
        return self.aniObject.maxsize / 2.0

    @property
    def maxsize(self):
        return self.aniObject.maxsize

    def value_changed(self, value):
        self.update()

    def paint(self, painter, xxx, xxx2):
        self.setCenter(self.map_pos)
        rect = QRectF(0 - self.halfsize, 0 - self.halfsize, self.size, self.size)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(self.color)
        painter.drawEllipse(QPointF(0, 0), self.size, self.size)

    def boundingRect(self):
        return QRectF(
            self.halfsize * -2.0,
            self.halfsize * -2.0,
            2.0 * self.maxsize,
            2.0 * self.maxsize,
        )

    def setCenter(self, map_pos):
        self.map_pos = map_pos
        self.setPos(self.toCanvasCoordinates(self.map_pos))

    def updatePosition(self):
        self.setCenter(self.map_pos)
