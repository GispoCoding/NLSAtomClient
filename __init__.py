# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NLSAtomClient
                                 A QGIS plugin
 This plugin makes possible to download NLS.fi open data
                             -------------------
        begin                : 2017-11-09
        copyright            : (C) 2017 by Gispo
        email                : erno@gispo.fi
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NLSAtomClient class from file NLSAtomClient.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .nls_atom_client import NLSAtomClient
    return NLSAtomClient(iface)
