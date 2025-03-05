# Discovery Plugin
#
# Copyright (C) 2017 Lutra Consulting
# info@lutraconsulting.co.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from qgis.core import (
    QgsCoordinateTransform,
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsMessageLog,
    QgsPointXY,
)

from .http_finder import AdresseBanFinder


class BanLocatorFilter(QgsLocatorFilter):
    def __init__(self, plugin):
        QgsLocatorFilter.__init__(self, None)
        self.plugin = plugin

    def clone(self):
        return BanLocatorFilter(self.plugin)

    def name(self):
        return "recherche adresse ban"

    def displayName(self):
        return "Recherche adresse BAN"

    def prefix(self):
        return "ban"

    def fetchResults(self, text, context, feedback):

        if len(text) < 3:
            return

        adresse_ban_finder = AdresseBanFinder(search=text, codecity=None, parent=None)

        if feedback.isCanceled():
            return

        search_results = adresse_ban_finder.get_search_results()
        for search_result in sorted(search_results, key=lambda x: (x[2], x[1])):
            (adresse, score, type_info, x, y) = search_result
            res = QgsLocatorResult(self, adresse, (score, type_info, x, y))
            res.score = score
            QgsMessageLog.logMessage(
                "adresse => {} score => {} type_info ==> {}".format(
                    adresse, score, type_info
                )
            )
            res.group = type_info
            self.resultFetched.emit(res)

    def triggerResult(self, result):
        try:  # new PyQt
            score, type_info, x, y = result.getUserData()
        except:
            score, type_info, x, y = result.userData
        transformer = self.plugin.getTransformer(4326)
        point = transformer.transform(
            QgsPointXY(x, y), QgsCoordinateTransform.ForwardTransform
        )
        x, y = point[0], point[1]
        self.plugin.zoomTo(x, y, x, y)

    def hasConfigWidget(self):
        return False

    def openConfigWidget(self, parent):
        pass
