# -----------------------------------------------------------
# Mostly from
# QGIS Quick Finder Plugin
# Copyright (C) 2014 Denis Rouzaud, Arnaud Morvan
#               2018 JDL
#
# -----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------

import codecs
import json
import os

from PyQt5.QtCore import (
    QDir,
    QEventLoop,
    QFile,
    QObject,
    QSettings,
    QUrl,
    QUrlQuery,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QApplication
from qgis.core import Qgis, QgsLogger, QgsMessageLog, QgsNetworkAccessManager
from qgis.utils import iface


class HttpFinder(QObject):

    finished = pyqtSignal(QObject)
    message = pyqtSignal(str, Qgis.MessageLevel)

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.asynchonous = False
        self.reply = None
        self.data = None
        self.message.connect(self.display_message)

    def send_request(self, url, params, headers={}):
        url = QUrl(url)
        q = QUrlQuery(url)
        for key, value in params.items():
            q.addQueryItem(key, value)
        url.setQuery(q)
        # QgsLogger.debug('Request: {}'.format(url.toEncoded()))
        request = QNetworkRequest(url)
        for key, value in headers.items():
            request.setRawHeader(key, value)

        if self.asynchonous:
            if self.reply is not None:
                self.reply.finished.disconnect(self.reply_finished)
                self.reply.abort()
                self.reply = None

            self.reply = QgsNetworkAccessManager.instance().get(request)
            self.reply.finished.connect(self.reply_finished)

        else:
            try:
                self.parent().set_dialog_busy(True)
            except AttributeError:
                pass
            self.reply = QgsNetworkAccessManager.instance().get(request)
            self.reply.deleteLater()
            evloop = QEventLoop()
            self.reply.finished.connect(evloop.quit)
            evloop.exec_(QEventLoop.AllEvents)
            self.reply_finished()

    def _finish(self):
        self.finished.emit(self)
        try:
            self.parent().set_dialog_busy(False)
        except AttributeError:
            pass

    def stop(self):
        if self.reply:
            self.reply.abort()
            self.reply = None
        self._finish()

    def reply_finished(self):
        self.erreurs = ""
        error = self.reply.error()
        if error == QNetworkReply.NoError:
            self.dataText = self.reply.readAll().data().decode("utf-8", "ignore")
            # QgsLogger.debug('Response: {}'.format(self.dataText))
            try:
                self.data = json.loads(self.dataText)
                self.load_data(self.data)
            except ValueError:
                self.message.emit(
                    self.tr(
                        "The service did not reply properly. Please check service definition."
                    ),
                    Qgis.Warning,
                )
        else:
            self.erreurs = self.get_error_message(error)
            self.message.emit(self.erreurs, Qgis.Warning)
            # QgsMessageLog.logMessage("Erreur HttpFinder pour {}: {}".format(self.reply.url().toString(), self.erreurs),"LocaliserParcelleAdresse",Qgis.Warning,False)
        self._finish()
        self.reply.deleteLater()
        self.reply = None

    def tr(self, sourceText):
        """surchage de tr à cause du bug avec PyQt5
        http://pyqt.sourceforge.net/Docs/PyQt5/i18n.html"""
        return QApplication.translate("HttpFinder", sourceText, None)

    @pyqtSlot(str, Qgis.MessageLevel)
    def display_message(self, message, level):
        iface.messageBar().pushMessage("Localiser parcelle adresse", message, level)

    def get_error_message(self, error):
        if error == QNetworkReply.NoError:
            # No error condition.
            # Note: When the HTTP protocol returns a redirect no error will be reported.
            # You can check if there is a redirect with the
            # QNetworkRequest::RedirectionTargetAttribute attribute.
            return ""

        if error == QNetworkReply.ConnectionRefusedError:
            return self.tr(
                "The remote server refused the connection"
                " (the server is not accepting requests)"
            )

        if error == QNetworkReply.RemoteHostClosedError:
            return self.tr(
                "The remote server closed the connection prematurely,"
                " before the entire reply was received and processed"
            )

        if error == QNetworkReply.HostNotFoundError:
            return self.tr("The remote host name was not found (invalid hostname)")

        if error == QNetworkReply.TimeoutError:
            return self.tr("The connection to the remote server timed out")

        if error == QNetworkReply.OperationCanceledError:
            return self.tr(
                "The operation was canceled via calls to abort()"
                " or close() before it was finished."
            )

        if error == QNetworkReply.SslHandshakeFailedError:
            return self.tr(
                "The SSL/TLS handshake failed"
                " and the encrypted channel could not be established."
                " The sslErrors() signal should have been emitted."
            )

        if error == QNetworkReply.TemporaryNetworkFailureError:
            return self.tr(
                "The connection was broken"
                " due to disconnection from the network,"
                " however the system has initiated roaming"
                " to another access point."
                " The request should be resubmitted and will be processed"
                " as soon as the connection is re-established."
            )

        if error == QNetworkReply.ProxyConnectionRefusedError:
            return self.tr(
                "The connection to the proxy server was refused"
                " (the proxy server is not accepting requests)"
            )

        if error == QNetworkReply.ProxyConnectionClosedError:
            return self.tr(
                "The proxy server closed the connection prematurely,"
                " before the entire reply was received and processed"
            )

        if error == QNetworkReply.ProxyNotFoundError:
            return self.tr("The proxy host name was not found (invalid proxy hostname)")

        if error == QNetworkReply.ProxyTimeoutError:
            return self.tr(
                "The connection to the proxy timed out"
                " or the proxy did not reply in time to the request sent"
            )

        if error == QNetworkReply.ProxyAuthenticationRequiredError:
            return self.tr(
                "The proxy requires authentication"
                " in order to honour the request"
                " but did not accept any credentials offered (if any)"
            )

        if error == QNetworkReply.ContentAccessDenied:
            return (
                self.tr(
                    "The access to the remote content was denied"
                    " (similar to HTTP error 401)"
                ),
            )
        if error == QNetworkReply.ContentOperationNotPermittedError:
            return self.tr(
                "The operation requested on the remote content is not permitted"
            )

        if error == QNetworkReply.ContentNotFoundError:
            return self.tr(
                "The remote content was not found at the server"
                " (similar to HTTP error 404)"
            )
        if error == QNetworkReply.AuthenticationRequiredError:
            return self.tr(
                "The remote server requires authentication to serve the content"
                " but the credentials provided were not accepted (if any)"
            )

        if error == QNetworkReply.ContentReSendError:
            return self.tr(
                "The request needed to be sent again, but this failed"
                " for example because the upload data could not be read a second time."
            )

        if error == QNetworkReply.ProtocolUnknownError:
            return self.tr(
                "The Network Access API cannot honor the request"
                " because the protocol is not known"
            )

        if error == QNetworkReply.ProtocolInvalidOperationError:
            return self.tr("the requested operation is invalid for this protocol")

        if error == QNetworkReply.UnknownNetworkError:
            return self.tr("An unknown network-related error was detected")

        if error == QNetworkReply.UnknownProxyError:
            return self.tr("An unknown proxy-related error was detected")

        if error == QNetworkReply.UnknownContentError:
            return self.tr(
                "An unknown error related to the remote content was detected"
            )

        if error == QNetworkReply.ProtocolFailure:
            return self.tr(
                "A breakdown in protocol was detected"
                " (parsing error, invalid or unexpected responses, etc.)"
            )

        return self.tr("An unknown network-related error was detected")


class AdresseBanFinder(HttpFinder):
    def __init__(self, search, limit="10", codecity=None, parent=None):
        HttpFinder.__init__(self, parent)
        self.URL = "https://api-adresse.data.gouv.fr/search/"
        self.search = search
        self.limit = limit
        self.params = {"q": self.search, "limit": self.limit}
        if codecity is not None:
            self.params["citycode"] = codecity
        self.search_results = []
        self.suggestions = []
        self.send_request(self.URL, self.params)

    def load_data(self, data):
        self.suggestions = []
        self.search_results = []
        for feature in data["features"]:
            adresse = feature["properties"]["label"]
            score = round(float(feature["properties"]["score"]) * 100, 2)
            x = float(feature["geometry"]["coordinates"][0])
            y = float(feature["geometry"]["coordinates"][1])
            type_info = feature["properties"]["type"].lower()
            if type_info == "housenumber":
                type_info = "Plaque adresse"
            elif type_info == "street":
                type_info = "Voie"
            elif type_info == "municipality":
                type_info = "Commune"
            else:
                type_info = ""
            self.suggestions.append(adresse)
            self.search_results.append((adresse, score, type_info, x, y))

    def get_suggestions(self):
        return self.suggestions

    def get_search_results(self):
        return self.search_results


class CartelieFinder(HttpFinder):
    def __init__(self, parent=None):  # , indexListe, code=None, parent=None):
        HttpFinder.__init__(self, parent)
        self.URL = "https://georef.application.developpement-durable.gouv.fr/geoservices/api/v1/localize?"
        self.URL2 = "http://cartelie.application.developpement-durable.gouv.fr/cartelie/localize?"
        self.params = {"niveauBase": "0", "niveau": "0", "projection": "EPSG_2154"}

        ## Dossier où enregistrer les datas web en cache pour limiter les requetes
        dossierCache = "plugin_LocaliserParcelle"
        self.cheminCache = None
        iniFic = QSettings().fileName()
        if QFile.exists(iniFic):  # Si la config QGIS est stockee dans QGIS/QGIS3.ini
            iniDir = os.path.dirname(iniFic)
            if QDir(iniDir + os.sep + dossierCache).exists() or QDir(iniDir).mkdir(
                dossierCache
            ):
                self.cheminCache = os.path.abspath(iniDir + os.sep + dossierCache)

    def appel(
        self, indexListe, code=None, parent=None, forcerMAJ=False
    ):  ## Interroger API ou cache
        """Interroger API (url+param) ou bien 1 fichier cache "nomCache.json"
        Si nomCache est défini :
         # On cherche le fichier: self.cheminCache +os.sep +nomCache +'.json'
         # S'il existe on le lit (pas de requête http)
         # S'il n'existe pas : requête http  puis  enregistrer le résultat dans fichier.
        """
        self.data = False

        if (
            indexListe < 3 and self.cheminCache
        ):  ## Lire fichier nomCache si déjà en cache
            if indexListe == 0:
                nomCache = "regions"
            elif indexListe == 1:
                nomCache = "departements" + str(code)
            else:
                nomCache = "communes" + str(code)
            ficCache = self.cheminCache + os.sep + nomCache + ".json"
            if not forcerMAJ and QFile.exists(
                ficCache
            ):  # Lire fichier nomCache sauf si c'est une MAJ
                with codecs.open(ficCache, "r", "utf-8", "ignore") as F:
                    self.data = F.read()
                if self.data:
                    # print('# Liste "'+nomCache+'" lue depuis: ' +ficCache )
                    return json.loads(self.data)
        else:
            ficCache = False

        self.params["niveau"] = str(indexListe)
        if indexListe == 0:
            if "parent" in self.params:
                del self.params["parent"]
        else:
            self.params["parent"] = str(code)
        self.search_results = []
        self.send_request(self.URL, self.params)

        if not self.data or self.data == []:
            print(
                "Erreur réseau : ", self.URL, self.erreurs
            )  # self.log("Erreur réseau: "+ self.erreurs, 'erreur')
            # self.erreurs += "Erreur réseau: {}\n {} \n {}".format(self.erreurs,self.URL,str(self.params))
            # self.messageBar.pushMessage('Erreur réseau', 'URL injoignable : '+self.URL, Qgis.Warning, 10)
            ## Tester avec la 2è URL (serveur cartelie) :
            print("Tester la requete avec URL2 :", self.URL2)
            self.send_request(self.URL2, self.params)
            if not self.data or self.data == []:
                return False
        # if self.data==[]:
        # 	print("Aucune donnée reçue : ", self.URL, self.params)
        # 	#self.messageBar.pushMessage('Aucune donnée reçue', 'URL : '+self.URL, Qgis.Warning, 5)
        # 	return False

        if ficCache:  ## Si chemin ficCache défini, sauvegarder self.data en cache:
            with codecs.open(ficCache, "w", "utf-8", "ignore") as F:
                F.write(self.dataText)

        return self.data

    def load_data(self, data):
        pass

    def get_data(self):
        return self.data
