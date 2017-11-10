# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NLSAtomClient
                                 A QGIS plugin
 This plugin makes possible to download NLS.fi open data
                              -------------------
        begin                : 2017-11-09
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Gispo
        email                : erno@gispo.fi
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from nls_atom_client_dialog import NLSAtomClientDialog
import os.path

from qgis.core import *
from qgis.gui import *

from PyQt4 import uic

import xml.etree.ElementTree

import requests
import zipfile
import StringIO

NLS_USER_KEY_DIALOG_FILE = "nls_atom_client_dialog_NLS_user_key.ui"
MUNICIPALITIES_DIALOG_FILE = "nls_atom_client_dialog_municipality_selection.ui"

class NLSAtomClient:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'NLSAtomClient_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&NLS Data Downloader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'NLSAtomClient')
        self.toolbar.setObjectName(u'NLSAtomClient')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('NLSAtomClient', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/NLSAtomClient/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'NLS Data Downloader'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&NLS Data Downloader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        
        #TODO
        # 1. Load the municipality data and the UTM 25LR grid
        # 2. List municipalities to the user (later also show the selection on the map)
        # 3. Prompt the API key from the user and store it (later allow changing via the settings)
        # 4. Let user choose the data sets (later remember selections and allow to create defaults)
        # 5. Download the type of data chosen by the user (later remember selections) 
        # 6. Store the data to the disk (later let user choose the storage format)
        # 7. Add the data as layer(s)
        
        #TODO later:
        # - check if municipality and utm data has been updated and download automatically also letting the user to know
        # - allow user to load new municipality data and the UTM 25LR grid from NLS server
        # - allow user to choose, map sheets intersecting or fully inside a municipality or clip the data according to the municipality borders
        # - store Atom responses locally and just check updates (automatically? / by user request?)
        # - let the user choose the source data type
        
        self.path = os.path.dirname(__file__)
        #QgsMessageLog.logMessage(self.path,
        #                         'NLSAtomClient',
        #                         QgsMessageLog.INFO)
        
        self.nls_user_key = QSettings().value("/NLSAtomClient/userKey", "", type=str)
        if self.nls_user_key == "":
            self.nls_user_key_dialog = uic.loadUi(os.path.join(self.path, NLS_USER_KEY_DIALOG_FILE))
            self.nls_user_key_dialog.show()
            # Run the dialog event loop
            result = self.nls_user_key_dialog.exec_()
            # See if OK was pressed
            if result:
                self.nls_user_key = self.nls_user_key_dialog.userKeyLineEdit.text()
                QSettings().setValue("/NLSAtomClient/userKey", self.nls_user_key)
            else:
                # TODO cannot work without the key, so user needs to be notified
                pass
        
        self.product_types = self.downloadNLSProductTypes()
        
        self.municipality_layer = QgsVectorLayer(os.path.join(self.path, "data/SuomenKuntajako_2017_10k.shp"), "municipalities", "ogr")
        if not self.municipality_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the municipality layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the municipality layer", level=QgsMessageBar.CRITICAL, duration=5)
        self.municipality_layer.setProviderEncoding('ISO-8859-1')
        
        self.utm25lr_layer = QgsVectorLayer(os.path.join(self.path, "data/utm25LR.shp"), "utm25lr", "ogr")
        if not self.municipality_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 25LR grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 25LR grid layer", level=QgsMessageBar.CRITICAL, duration=5)
        
        self.municipalities_dialog = uic.loadUi(os.path.join(self.path, MUNICIPALITIES_DIALOG_FILE))
        iter = self.municipality_layer.getFeatures()
        for feature in iter:
            self.municipalities_dialog.municipalityListWidget.addItem(feature['NAMEFIN'])
        
        self.municipalities_dialog.show()
        
        # show the dialog
        #self.dlg.show()
        # Run the dialog event loop
        result = self.municipalities_dialog.exec_()
        # See if OK was pressed
        if result:
            mun_utm_features = []
            
            selected_mun_names = []
            for item in self.municipalities_dialog.municipalityListWidget.selectedItems():
                selected_mun_names.append(item.text())
                
            QgsMessageLog.logMessage(str(selected_mun_names), 'NLSAtomClient', QgsMessageLog.INFO)
            
            for selected_mun_name in selected_mun_names:
                mun_utm_features = self.getMunicipalityIntersectingUTMFeatures(selected_mun_name)
            
                feature_types = ["maastotietokanta"] # TODO ask from the user via dialog that lists types based on NLS Atom service
                #self.downloadData(mun_utm_features, feature_types)


    def getMunicipalityIntersectingUTMFeatures(self, selected_mun_name):
        mun_utm_features = []
        request = QgsFeatureRequest().setFilterExpression( u'"NAMEFIN" = \'' + selected_mun_name + u'\'' )
        #QgsMessageLog.logMessage(municipality_layer.featureCount(request), 'NLSAtomClient', QgsMessageLog.INFO)
        iter = self.municipality_layer.getFeatures( request )
        count = 0
        for feature in iter:
            count += 1
            mun_geom = feature.geometry()
            
            utm_iter = self.utm25lr_layer.getFeatures()
            for utm_feature in utm_iter:
                utm_geom = utm_feature.geometry()
                if mun_geom.intersects(utm_geom):
                    mun_utm_features.append(utm_feature)
            
        QgsMessageLog.logMessage("Municipalities with the name: " + str(count), 'NLSAtomClient', QgsMessageLog.INFO)
        QgsMessageLog.logMessage("UTM sheets matching the municipality name: " + str(len(mun_utm_features)), 'NLSAtomClient', QgsMessageLog.INFO)

        return mun_utm_features
    
    def downloadData(self, mun_utm_features, feature_types):
        # TODO show progress to the user
        # TODO show extracted data as layers in the QGIS if preferred by the user
        for feature_type in feature_types:
            for mun_utm_feature in mun_utm_features:
                sheet_name = mun_utm_feature['LEHTITUNNU']
                sn1 = sheet_name[:2]
                sn2 = sheet_name[:3]
        
                url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/tilauslataus/tuotteet/" + feature_type + "/kaikki/etrs89/shp/" + sn1 + "/" + sn2 + "/" + sheet_name + ".shp.zip?api_key="  + self.nls_user_key
                #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                r = requests.get(url, stream=True)
                # TODO check r.status_code
                z = zipfile.ZipFile(StringIO.StringIO(r.content))
                z.extractall(os.path.join(self.path, "data", feature_type))
                
    def downloadNLSProductTypes(self):
        url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp?api_key=" + self.nls_user_key
        r = requests.get(url)
        # TODO parse and read the titles and return them as a list
        QgsMessageLog.logMessage(r.text, 'NLSAtomClient', QgsMessageLog.INFO)
        
        e = xml.etree.ElementTree.fromstring(r.text)
        
        
        
        