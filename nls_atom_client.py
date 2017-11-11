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

import os

import requests
import zipfile
import StringIO

from PyQt4.QtCore import QTimer

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
        # 7. Add the data as layer(s) (if user wants)
        
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
        
        self.utm10_layer = QgsVectorLayer(os.path.join(self.path, "data/utm10.shp"), "utm10", "ogr")
        if not self.utm10_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 10 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 10 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
        
        self.utm25lr_layer = QgsVectorLayer(os.path.join(self.path, "data/utm25LR.shp"), "utm25lr", "ogr")
        if not self.utm25lr_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 25LR grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 25LR grid layer", level=QgsMessageBar.CRITICAL, duration=5)

        self.utm25_layer = QgsVectorLayer(os.path.join(self.path, "data/utm25.shp"), "utm25", "ogr")
        if not self.utm25_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 25 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 25 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            
        self.utm50_layer = QgsVectorLayer(os.path.join(self.path, "data/utm50.shp"), "utm50", "ogr")
        if not self.utm50_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 50 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 50 grid layer", level=QgsMessageBar.CRITICAL, duration=5)

        self.utm100_layer = QgsVectorLayer(os.path.join(self.path, "data/utm100.shp"), "utm100", "ogr")
        if not self.utm100_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 100 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 100 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            
        self.utm200_layer = QgsVectorLayer(os.path.join(self.path, "data/utm200.shp"), "utm200", "ogr")
        if not self.utm200_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 200 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 200 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            
        self.municipalities_dialog = uic.loadUi(os.path.join(self.path, MUNICIPALITIES_DIALOG_FILE))
        iter = self.municipality_layer.getFeatures()
        for feature in iter:
            self.municipalities_dialog.municipalityListWidget.addItem(feature['NAMEFIN'])
        
        for key, value in self.product_types.items():
            self.municipalities_dialog.productListWidget.addItem(value)

        self.municipalities_dialog.show()
        
        # show the dialog
        #self.dlg.show()
        # Run the dialog event loop
        result = self.municipalities_dialog.exec_()
        # See if OK was pressed
        if result:
            self.mun_utm10_features = []
            self.mun_utm25lr_features = []
            self.mun_utm25_features = []
            self.mun_utm50_features = []
            self.mun_utm100_features = []
            self.mun_utm200_features = []
            
            selected_mun_names = []
            for item in self.municipalities_dialog.municipalityListWidget.selectedItems():
                selected_mun_names.append(item.text())
                
            QgsMessageLog.logMessage(str(selected_mun_names), 'NLSAtomClient', QgsMessageLog.INFO)
            
            for selected_mun_name in selected_mun_names:
                self.mun_utm25lr_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm25lr_layer)
                self.mun_utm25_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm25lr_layer)
                self.mun_utm10_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm10_layer)
                self.mun_utm50_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm50_layer)
                self.mun_utm100_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm100_layer)
                self.mun_utm200_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm200_layer)
            
            product_types = {} # TODO ask from the user via dialog that lists types based on NLS Atom service  

            for selected_prod_title in self.municipalities_dialog.productListWidget.selectedItems():
                for key, value in self.product_types.items():
                    if selected_prod_title.text() == value:
                        product_types[key] = value
                    
            QgsMessageLog.logMessage(str(product_types), 'NLSAtomClient', QgsMessageLog.INFO)
            self.downloadData(product_types)

    def getMunicipalityIntersectingFeatures(self, selected_mun_name, layer):
        intersecting_features = []
        request = QgsFeatureRequest().setFilterExpression( u'"NAMEFIN" = \'' + selected_mun_name + u'\'' )
        #QgsMessageLog.logMessage(municipality_layer.featureCount(request), 'NLSAtomClient', QgsMessageLog.INFO)
        iter = self.municipality_layer.getFeatures( request )
        count = 0
        for feature in iter:
            count += 1
            mun_geom = feature.geometry()
            
            layer_iter = layer.getFeatures()
            for layer_feature in layer_iter:
                layer_geom = layer_feature.geometry()
                if mun_geom.intersects(layer_geom):
                    intersecting_features.append(layer_feature)
            
        QgsMessageLog.logMessage("Municipalities with the name " + selected_mun_name + ": " + str(count), 'NLSAtomClient', QgsMessageLog.INFO)
        QgsMessageLog.logMessage("Count of sheets (features) intersecting with the municipality: " + str(len(intersecting_features)), 'NLSAtomClient', QgsMessageLog.INFO)

        return intersecting_features
    
    def downloadData(self, product_types):
        # TODO show progress to the user
        # TODO show extracted data as layers in the QGIS if preferred by the user
        
        self.all_urls = []
        self.total_download_count = 0
        self.download_count = 0
        
        for product_key, product_title in product_types.items():
            urls = self.createDownloadURLS(product_key, product_title)
            self.all_urls.extend(urls)
            self.total_download_count += len(urls)
            
        percentage = self.download_count / float(self.total_download_count) * 100.0
        percentage_text = "%.2f" % round(percentage, 2)

        self.busy_indicator_dialog = QgsBusyIndicatorDialog("A moment... processed " + percentage_text + "% of the files", self.iface.mainWindow())
        self.busy_indicator_dialog.show()
            
        QTimer.singleShot(10, self.downloadOneFile)

    def createDownloadURLS(self, product_key, product_title):
        
        urls = []
        
        if product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiinteistorekisterikartta/karttalehdittain":
            urls = self.createCadastralIndexMapVectorAllFeaturesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastotietokanta/kaikki":
            urls = self.createTopographicDatabaseDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokarttarasteri_50k_jhs180/painovari":
            urls = createTopographicMapRaster50kDownloadURLS(product_key, product_title)
        
        #QgsMessageLog.logMessage("URL count: " + str(len(urls)), 'NLSAtomClient', QgsMessageLog.INFO)
        return urls
    
    def createCadastralIndexMapVectorAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp/kiinteistorekisterikartta/karttalehdittain", "/tilauslataus/tuotteet/kiinteistorekisterikartta/avoin/karttalehdittain")
    
            url = modified_key + "/tm35fin/shp/" + sn1 + "/" + sheet_name + ".zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createTopographicDatabaseDownloadURLS(self, product_key, product_title):
        
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
            
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs89/shp/" + sn1 + "/" + sn2 + "/" + sheet_name + ".shp.zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls

    def createTopographicMapRaster50kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm50_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/4m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries20kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm50_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/4m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls

    def createBackgroundMapSeries10kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/2m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries5kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/0_5m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createBasicMapRasterPrintingColorNoAntiAliasingDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/1m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createBasicMapRasterBackgroundColorDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/1m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createBasicMapRasterPrintingColorDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/1m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createLaserScanningDataPointCloudDownloadURLS(self, product_key, product_title):
        # TODO
        pass
    
    def createGeneralMapRaster8000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/Yleiskarttarasteri_8milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createGeneralMapRaster4500kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/Yleiskarttarasteri_45milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createGeneralMapRaster2000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/Yleiskarttarasteri_2milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createGeneralMapRaster1000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/kaikki/etrs89/png/Yleiskarttarasteri_1milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries8000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/2048m/etrs89/png/Taustakartta_8milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries4000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/1024m/etrs89/png/Taustakartta_4milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls

    def createBackgroundMapSeries2000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/256m/etrs89/png/Taustakartta_2milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries800kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/128m/etrs89/png/Taustakartta_800.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries320kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/64m/etrs89/png/Taustakartta_320.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createBackgroundMapSeries160kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/32m/etrs89/png/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls


    def createBackgroundMapSeries80kDownloadURLS(self, product_key, product_title):
        pass
    #===========================================================================
    #     urls = []
    #     
    #     for mun_utm_feature in self.mun_utm100_features:
    #         sheet_name = mun_utm_feature['LEHTITUNNU']
    #                     
    #         modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    # 
    #         url = modified_key + "/16m/etrs89/png/" + sheet_name + ".png?api_key="  + self.nls_user_key
    #         #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    # 
    #         urls.append((url, product_title, product_key))
    #         
    #     return urls
    #===========================================================================
    
    def createBackgroundMapSeries40kDownloadURLS(self, product_key, product_title):
        pass
    #===========================================================================
    #     urls = []
    #     
    #     for mun_utm_feature in self.mun_utm100_features:
    #         sheet_name = mun_utm_feature['LEHTITUNNU']
    #         sn1 = sheet_name[:2]
    #         sn2 = sheet_name[:3]
    #                     
    #         modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    # 
    #         url = modified_key + "/8m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + "L.png?api_key="  + self.nls_user_key
    #         url = modified_key + "/8m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + "R.png?api_key="  + self.nls_user_key
    #         #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    # 
    #         urls.append((url, product_title, product_key))
    #         
    #     return urls
    #===========================================================================
    
    def createTopographicMapRaster500kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs89/png/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createTopographicMapRaster250kDownloadURLS(self, product_key, product_title):
        pass
    
    def createTopographicMapRaster100kDownloadURLS(self, product_key, product_title):
        pass
    
    def createControlPointsN2000DownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/KorkeusPisteet_N2000_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createControlPointsN60DownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/KorkeusPisteet_N60_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createControlPointsTM35FINDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/euref_etrs-tm35fin_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createControlPointsEUREFFINDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/Euref_geodeettiset_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createOrthophotoColourInfraDownloadURLS(self, product_key, product_title):
        pass
    
    def createOrthophotoColourDownloadURLS(self, product_key, product_title):
        pass
    
    def createElevationModel2mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createShadedReliefRaster2mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createPlaceNamesMapNames50kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames8000kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames4500kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames500kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames250kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames100kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames2000kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames1000kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesMapNames25kDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesPlacesDownloadURLS(self, product_key, product_title):
        pass
    
    def createPlaceNamesPlaceNamesDownloadURLS(self, product_key, product_title):
        pass
    
    def createTopographicDatabaseRoadsWithAddressesDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs89/shp/" + sheet_name + ".shp.zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls

    
    def createMunicipalDivision100kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_100k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createMunicipalDivision4500kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/KarttakuvaaKuntarajoista_2017_4500k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createMunicipalDivision1000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_1000k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createMunicipalDivision250kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_250k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls

    def createMunicipalDivision10kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_10k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createShadedReliefRaster8mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createShadedReliefRaster512mDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs-tm35fin-n2000/suomi.tif?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createShadedReliefRaster128mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createShadedReliefRaster64mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createShadedReliefRaster32mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createElevationModel10mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createElevationZonesRaster512mDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs-tm35fin-n2000/suomi.tif?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createElevationZonesRaster128mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createElevationZonesRaster64mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createElevationZonesRaster32mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createCadastralIndexMapRasterCadastralIdentifiersDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp/kiinteistorekisterikartta/ktj_kiinteistotunnukset", "/tilauslataus/tuotteet/kiinteistorekisterikartta/avoin/karttalehdittain/tm35fin/png/ktj_kiinteistotunnukset")
    
            url = modified_key + "/" + sn1 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createCadastralIndexMapRasterCadastralUnitsDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp/kiinteistorekisterikartta/ktj_kiinteistorajat", "/tilauslataus/tuotteet/kiinteistorekisterikartta/avoin/karttalehdittain/tm35fin/png/ktj_kiinteistorajat")
    
            url = modified_key + "/" + sn1 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createGeneralMap1000kAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shape/1_milj_Shape_etrs_shape.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createTopographicMap100kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
                
            url = modified_key + "/etrs89/shp/" + sn1 + "/" + sheet_name + ".zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key))
            
        return urls
    
    def createGeneralMap4500kAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shape/4_5_milj_shape_etrs-tm35fin.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createTopographicMap250kDownloadURLS(self, product_key, product_title):
        pass
    
    def createMapSheetGridAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "etrs89/shp/UTM_EUREF_SHP.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls
    
    def createControlPointsLocationDrawingsForControlPointsDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "etrs89/tiff/asemapiirrokset_pakattu.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key))
            
        return urls

    def downloadOneFile(self):
        
        url = self.all_urls[self.download_count][0]
        QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
        r = requests.get(url, stream=True)
        # TODO check r.status_code & r.ok
        
        url_parts = url.split('/')
        file_name = url_parts[-1].split('?')[0]
        
        dir_path = os.path.join(self.path, "data", self.all_urls[self.download_count][1])
        #QgsMessageLog.logMessage(dir_path, 'NLSAtomClient', QgsMessageLog.INFO)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
                else:
                    QgsMessageLog.logMessage(exc.errno, 'NLSAtomClient', QgsMessageLog.CRITICAL)
        if not os.path.exists(dir_path):
            QgsMessageLog.logMessage("dir not created", 'NLSAtomClient', QgsMessageLog.CRITICAL)

        #z = zipfile.ZipFile(StringIO.StringIO(r.content))
        #z.extractall(os.path.join(self.path, "data", value))
        with open(os.path.join(dir_path, file_name), 'wb') as f:
            f.write(r.content)
        
        self.download_count += 1
        percentage = self.download_count / float(self.total_download_count) * 100.0
        percentage_text = "%.2f" % round(percentage, 2)
        
        self.busy_indicator_dialog.setMessage("A moment... processed " + percentage_text + "% of the files")
        #self.iface.messageBar().pushMessage("A moment... processed " + percentage_text + "% of files")
        QgsMessageLog.logMessage("A moment... processed " + percentage_text + "% of the files", 'NLSAtomClient', QgsMessageLog.INFO)
        
        if self.download_count == self.total_download_count:
            QgsMessageLog.logMessage("done downloading data", 'NLSAtomClient', QgsMessageLog.INFO)
            self.busy_indicator_dialog.hide()
        else:
            QTimer.singleShot(10, self.downloadOneFile)
                
    def downloadNLSProductTypes(self):
        products = {}

        url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp?api_key=" + self.nls_user_key
        r = requests.get(url)
        # TODO parse and read the titles and return them as a list
        #QgsMessageLog.logMessage(r.text, 'NLSAtomClient', QgsMessageLog.INFO)
        
        e = xml.etree.ElementTree.fromstring(r.text.encode('utf-8'))
        
        #for child in e:
            #if child.tag
            #QgsMessageLog.logMessage(child.tag, 'NLSAtomClient', QgsMessageLog.INFO)
            #QgsMessageLog.logMessage(child.text, 'NLSAtomClient', QgsMessageLog.INFO)

        for entry in e.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title');
            QgsMessageLog.logMessage(title.text, 'NLSAtomClient', QgsMessageLog.INFO)
            id = entry.find('{http://www.w3.org/2005/Atom}id')
            QgsMessageLog.logMessage(id.text, 'NLSAtomClient', QgsMessageLog.INFO)
            products[id.text] = title.text

        return products
