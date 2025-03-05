#!/usr/bin/env python

"""
/***************************************************************************
        Aller sur une parcelle - Zoomer de la région à la parcelle
                             -------------------
 begin     : 10-10-2011
 copyright : (C) 2011 par Mathieu Rajerison
 auteurs   :
  Mathieu RAJERISON, Philippe DESBOEUFS, Frédéric LASSERON, Christophe MASSE, Jean-Daniel LOMENEDE

 ***************************************************************************/
/*  Vous êtes libres d'utilsier les sources de ce script à condition de
/*  mentionner son auteur
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


def classFactory(iface):
    from .localise import plugin

    return plugin(iface)
