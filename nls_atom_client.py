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

from PyQt4.QtGui import QMessageBox

import xml.etree.ElementTree

import os

import requests
import zipfile
import StringIO

from PyQt4.QtCore import QTimer
from future.backports.xmlrpc.client import boolean

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

        self.initWithNLSData()

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
            text=self.tr(u'&Download NLS Open Data'),
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
        
        # Functionality
        # 1. Load the municipality data and the UTM grids
        # 2. List municipalities to the user (later also show the selection on the map)
        # 3. Prompt the API key from the user and store it (later allow changing via the settings)
        # 4. Let user choose the data sets (later remember selections and allow to create defaults)
        # 5. Download the type of data chosen by the user (later remember selections) 
        # 6. Store the data to the disk (later let user choose the storage format)
        # 7. Add the data as layer(s) (if user wants)
        
        #TODO later:
        # - check if municipality and utm data has been updated and download automatically also letting the user to know
        # - allow user to load new municipality data and the UTM grids from NLS server
        # - allow user to choose, map sheets intersecting or fully inside a municipality or clip the data according to the municipality borders
        # - store Atom responses locally and just check updates (automatically? / by user request?)
        # - let the user choose the source data type
        # - allow to choose download locations
        
        #QgsMessageLog.logMessage(self.path,
        #                         'NLSAtomClient',
        #                         QgsMessageLog.INFO)
        
        self.nls_user_key = QSettings().value("/NLSAtomClient/userKey", "", type=str)
        self.data_download_dir = QSettings().value("/NLSAtomClient/dataDownloadDir", "", type=str)
        self.addDownloadedDataAsLayer = QSettings().value("/NLSAtomClient/addDownloadedDataAsLayer", True, type=bool)
        self.showMunicipalitiesAsLayer = QSettings().value("/NLSAtomClient/showMunicipalitiesAsLayer", True, type=bool)
        self.showUTMGridsAsLayer = QSettings().value("/NLSAtomClient/showUTMGridsAsLayer", False, type=bool)
        
        
        if self.nls_user_key == "":
            self.showSettingsDialog()
        
        self.product_types = self.downloadNLSProductTypes()

        self.municipality_layer = QgsVectorLayer(os.path.join(self.path, "data/SuomenKuntajako_2017_10k.shp"), "municipalities", "ogr")
        if not self.municipality_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the municipality layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the municipality layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.municipality_layer.setProviderEncoding('ISO-8859-1')
        
        self.utm5_layer = QgsVectorLayer(os.path.join(self.path, "data/utm5.shp"), "utm5", "ogr")
        if not self.utm5_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 5 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 5 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.utm10_layer = QgsVectorLayer(os.path.join(self.path, "data/utm10.shp"), "utm10", "ogr")
        if not self.utm10_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 10 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 10 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.utm25lr_layer = QgsVectorLayer(os.path.join(self.path, "data/utm25LR.shp"), "utm25lr", "ogr")
        if not self.utm25lr_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 25LR grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 25LR grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.utm25_layer = QgsVectorLayer(os.path.join(self.path, "data/utm25.shp"), "utm25", "ogr")
        if not self.utm25_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 25 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 25 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.utm50_layer = QgsVectorLayer(os.path.join(self.path, "data/utm50.shp"), "utm50", "ogr")
        if not self.utm50_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 50 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 50 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.utm100_layer = QgsVectorLayer(os.path.join(self.path, "data/utm100.shp"), "utm100", "ogr")
        if not self.utm100_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 100 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 100 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.utm200_layer = QgsVectorLayer(os.path.join(self.path, "data/utm200.shp"), "utm200", "ogr")
        if not self.utm200_layer.isValid():
            QgsMessageLog.logMessage('Failed to load the UTM 200 grid layer', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", "Failed to load the UTM 200 grid layer", level=QgsMessageBar.CRITICAL, duration=5)
            return
        
        if self.showUTMGridsAsLayer:
            found_utm5_layer = False
            found_utm10_layer = False
            found_utm25lr_layer = False
            found_utm25_layer = False
            found_utm50_layer = False
            found_utm100_layer = False
            found_utm200_layer = False
            current_layers = self.iface.legendInterface().layers()
            for current_layer in current_layers:
                if current_layer.name() == "utm5":
                    found_utm5_layer = True
                if current_layer.name() == "utm10":
                    found_utm10_layer = True
                if current_layer.name() == "utm25lr":
                    found_utm25lr_layer = True
                if current_layer.name() == "utm25":
                    found_utm25_layer = True
                if current_layer.name() == "utm50":
                    found_utm50_layer = True
                if current_layer.name() == "utm100":
                    found_utm100_layer = True
                if current_layer.name() == "utm200":
                    found_utm200_layer = True
            if not found_utm200_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm200_layer])
            if not found_utm100_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm100_layer])
            if not found_utm50_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm50_layer])
            if not found_utm25_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm25_layer])
            if not found_utm25lr_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm25lr_layer])
            if not found_utm10_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm10_layer])
            if not found_utm5_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.utm5_layer])
                
        if self.showMunicipalitiesAsLayer:
            found_layer = False
            current_layers = self.iface.legendInterface().layers()
            for current_layer in current_layers:
                if current_layer.name() == "municipalities":
                    found_layer = True
                    break
            if not found_layer:
                QgsMapLayerRegistry.instance().addMapLayers([self.municipality_layer])
        
        self.municipalities_dialog = uic.loadUi(os.path.join(self.path, MUNICIPALITIES_DIALOG_FILE))
        self.municipalities_dialog.settingsPushButton.clicked.connect(self.showSettingsDialog)
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
            self.mun_utm5_features = []
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
            
            product_types = {} # TODO ask from the user via dialog that lists types based on NLS Atom service  

            for selected_prod_title in self.municipalities_dialog.productListWidget.selectedItems():
                for key, value in self.product_types.items():
                    if selected_prod_title.text() == value:
                        product_types[key] = value
                    
            QgsMessageLog.logMessage(str(product_types), 'NLSAtomClient', QgsMessageLog.INFO)
            
            if len(selected_mun_names) > 0 and len(product_types) > 0:
                for selected_mun_name in selected_mun_names:
                    if 'https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/laser/etrs-tm35fin-n2000' in product_types or \
                        'https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/orto/vaaravari_ortokuva' in product_types or \
                        'https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/orto/ortokuva' in product_types:
                        self.mun_utm5_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm5_layer)
                    self.mun_utm10_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm10_layer)
                    self.mun_utm25lr_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm25lr_layer)
                    self.mun_utm25_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm25_layer)
                    self.mun_utm50_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm50_layer)
                    self.mun_utm100_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm100_layer)
                    self.mun_utm200_features = self.getMunicipalityIntersectingFeatures(selected_mun_name, self.utm200_layer)
                
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
        QgsMessageLog.logMessage("Count of " + layer.name() + " sheets (features) intersecting with the municipality: " + str(len(intersecting_features)), 'NLSAtomClient', QgsMessageLog.INFO)

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

        self.busy_indicator_dialog = QgsBusyIndicatorDialog("A moment... processed " + percentage_text + "% of the files ", self.iface.mainWindow())
        self.busy_indicator_dialog.show()
        QgsMessageLog.logMessage("A moment... processed " + percentage_text + "% of the files", 'NLSAtomClient', QgsMessageLog.INFO)
        #QgsMessageLog.logMessage(str(self.total_download_count), 'NLSAtomClient', QgsMessageLog.INFO)
            
        QTimer.singleShot(1000, self.downloadOneFile)

    def createDownloadURLS(self, product_key, product_title):
        
        urls = []
        
        if product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiinteistorekisterikartta/karttalehdittain":
            urls = self.createCadastralIndexMapVectorAllFeaturesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastotietokanta/kaikki":
            urls = self.createTopographicDatabaseDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokarttarasteri_50k_jhs180/painovari":
            urls = self.createTopographicMapRaster50kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_20k":
            urls = self.createBackgroundMapSeries20kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_10k":
            urls = self.createBackgroundMapSeries10kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_5k":
            urls = self.createBackgroundMapSeries5kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/peruskarttarasteri_jhs180/painovari_ei_pehmennysta":
            urls = self.createBasicMapRasterPrintingColorNoAntiAliasingDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/peruskarttarasteri_jhs180/taustavari_korkeuskayrilla":
            urls = self.createBasicMapRasterBackgroundColorDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/peruskarttarasteri_jhs180/painovari":
            urls = self.createBasicMapRasterPrintingColorDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/laser/etrs-tm35fin-n2000":
            urls = self.createLaserScanningDataPointCloudDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/yleiskarttarasteri_8000k_jhs180/kaikki":
            urls = self.createGeneralMapRaster8000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/yleiskarttarasteri_4500k_jhs180/kaikki":
            urls = self.createGeneralMapRaster4500kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/yleiskarttarasteri_2000k_jhs180/kaikki":
            urls = self.createGeneralMapRaster2000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/yleiskarttarasteri_1000k_jhs180/kaikki":
            urls = self.createGeneralMapRaster1000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_8m":
            urls = self.createBackgroundMapSeries8000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_4m":
            urls = self.createBackgroundMapSeries4000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_2m":
            urls = self.createBackgroundMapSeries2000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_800k":
            urls = self.createBackgroundMapSeries800kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_320k":
            urls = self.createBackgroundMapSeries320kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_160k":
            urls = self.createBackgroundMapSeries160kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_80k":
            urls = self.createBackgroundMapSeries80kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/taustakarttasarja_jhs180/taustakartta_40k":
            urls = self.createBackgroundMapSeries40kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokarttarasteri_500k_jhs180/kaikki":
            urls = self.createTopographicMapRaster500kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokarttarasteri_250k_jhs180/kaikki":
            urls = self.createTopographicMapRaster250kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokarttarasteri_100k_jhs180/kaikki":
            urls = self.createTopographicMapRaster100kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiintopisterekisteri/korkeuskiintopisteet_n2000":
            urls = self.createControlPointsN2000DownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiintopisterekisteri/korkeuskiintopisteet_n60":
            urls = self.createControlPointsN60DownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiintopisterekisteri/tasokiintopisteet_etrs_tm35fin":
            urls = self.createControlPointsTM35FINDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiintopisterekisteri/maantieteelliset_euref_fin":
            urls = self.createControlPointsEUREFFINDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/orto/vaaravari_ortokuva":
            urls = self.createOrthophotoColourInfraDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/orto/ortokuva":
            urls = self.createOrthophotoColourDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/korkeusmalli/hila_2m":
            urls = self.createElevationModel2mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/vinovalovarjoste/hila_2m":
            urls = self.createShadedReliefRaster2mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_50":
            urls = self.createPlaceNamesMapNames50kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_8000":
            urls = self.createPlaceNamesMapNames8000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_4500":
            urls = self.createPlaceNamesMapNames4500kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_500":
            urls = self.createPlaceNamesMapNames500kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_250":
            urls = self.createPlaceNamesMapNames250kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_100":
            urls = self.createPlaceNamesMapNames100kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_2000":
            urls = self.createPlaceNamesMapNames2000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_1000":
            urls = self.createPlaceNamesMapNames1000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_25":
            urls = self.createPlaceNamesMapNames25kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/paikat":
            urls = self.createPlaceNamesPlacesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/paikannimet_kaikki":
            urls = self.createPlaceNamesPlaceNamesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastotietokanta/tiesto_osoitteilla":
            urls = self.createTopographicDatabaseRoadsWithAddressesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kuntajako/kuntajako_100k":
            urls = self.createMunicipalDivision100kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kuntajako/kuntajako_4500k":
            urls = self.createMunicipalDivision4500kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kuntajako/kuntajako_1000k":
            urls = self.createMunicipalDivision1000kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kuntajako/kuntajako_250k":
            urls = self.createMunicipalDivision250kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kuntajako/kuntajako_10k":
            urls = self.createMunicipalDivision10kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/vinovalovarjoste/hila_8m":
            urls = self.createShadedReliefRaster8mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/vinovalovarjoste/hila_512m":
            urls = self.createShadedReliefRaster512mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/vinovalovarjoste/hila_128m":
            urls = self.createShadedReliefRaster128mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/vinovalovarjoste/hila_64m":
            urls = self.createShadedReliefRaster64mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/vinovalovarjoste/hila_32m":
            urls = self.createShadedReliefRaster32mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/korkeusmalli/hila_10m":
            urls = self.createElevationModel10mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/korkeusvyohyke/hila_512m":
            urls = self.createElevationZonesRaster512mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/korkeusvyohyke/hila_128m":
            urls = self.createElevationZonesRaster128mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/korkeusvyohyke/hila_64m":
            urls = self.createElevationZonesRaster64mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/korkeusvyohyke/hila_32m":
            urls = self.createElevationZonesRaster32mDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiinteistorekisterikartta/ktj_kiinteistotunnukset":
            urls = self.createCadastralIndexMapRasterCadastralIdentifiersDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiinteistorekisterikartta/ktj_kiinteistorajat":
            urls = self.createCadastralIndexMapRasterCadastralUnitsDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/yleiskartta_1000k/kaikki":
            urls = self.createGeneralMap1000kAllFeaturesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokartta_100k/kaikki":
            urls = self.createTopographicMap100kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/yleiskartta_4500k/kaikki":
            urls = self.createGeneralMap4500kAllFeaturesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastokartta_250k/kaikki":
            urls = self.createTopographicMap250kDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/karttalehtijako_ruudukko/kaikki":
            urls = self.createMapSheetGridAllFeaturesDownloadURLS(product_key, product_title)
        elif product_key == "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kiintopisterekisteri/sijaintipiirrokset":
            urls = self.createControlPointsLocationDrawingsForControlPointsDownloadURLS(product_key, product_title)
        else:
            QgsMessageLog.logMessage('Unknown product ' + product_title +  ', please send error report to the author', 'NLSAtomClient', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage('Unknown product ' + product_title +  ', please send error report to the author', level=QgsMessageBar.CRITICAL, duration=10)
            
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
    
            urls.append((url, product_title, product_key, "shp"))
            
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
    
            urls.append((url, product_title, product_key, "shp"))
            
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
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries20kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm50_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/4m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls

    def createBackgroundMapSeries10kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/2m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries5kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/0_5m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBasicMapRasterPrintingColorNoAntiAliasingDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/1m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBasicMapRasterBackgroundColorDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/1m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBasicMapRasterPrintingColorDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25lr_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/1m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
 
    def createLaserScanningDataPointCloudDownloadURLS(self, product_key, product_title):
        urls = []
        
        limit = 100
        offset = 0
        
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/laser/etrs-tm35fin-n2000?" + "limit=" + str(limit) + "&offset=" + str(offset) + "&api_key=" + self.nls_user_key
        QgsMessageLog.logMessage(product_url, 'NLSAtomClient', QgsMessageLog.INFO)
        
        while product_url is not "":
            r = requests.get(product_url)
            #QgsMessageLog.logMessage(r.text, 'NLSAtomClient', QgsMessageLog.INFO)
            
            e = xml.etree.ElementTree.fromstring(r.text.encode('utf-8'))
    
            for entry in e.findall('{http://www.w3.org/2005/Atom}entry'):
                link = entry.find('{http://www.w3.org/2005/Atom}link')
                url = link.attrib["href"]
                #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                
                for mun_utm_feature in self.mun_utm5_features:
                    sheet_name = mun_utm_feature['LEHTITUNNU']
                
                    if sheet_name in url:
                        urls.append((url, product_title, product_key, "laz"))
                        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                
            next_link = e.find('{http://www.w3.org/2005/Atom}link[@rel="next"]')
            #QgsMessageLog.logMessage(str(next_link), 'NLSAtomClient', QgsMessageLog.INFO)
            if next_link is not None:
                next_link_href = next_link.attrib["href"]
                #QgsMessageLog.logMessage(next_link_href, 'NLSAtomClient', QgsMessageLog.INFO)
                product_url = next_link_href
                QgsMessageLog.logMessage(product_url, 'NLSAtomClient', QgsMessageLog.INFO)
            else:
                product_url = ""
                #QgsMessageLog.logMessage("did not find link with rel next", 'NLSAtomClient', QgsMessageLog.INFO)
            
        return urls
    
    def createGeneralMapRaster8000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/Yleiskarttarasteri_8milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createGeneralMapRaster4500kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/Yleiskarttarasteri_45milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createGeneralMapRaster2000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/Yleiskarttarasteri_2milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createGeneralMapRaster1000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/kaikki/etrs89/png/Yleiskarttarasteri_1milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries8000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/2048m/etrs89/png/Taustakartta_8milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries4000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/1024m/etrs89/png/Taustakartta_4milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls

    def createBackgroundMapSeries2000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/256m/etrs89/png/Taustakartta_2milj.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries800kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/128m/etrs89/png/Taustakartta_800.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries320kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/64m/etrs89/png/Taustakartta_320.png?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createBackgroundMapSeries160kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/32m/etrs89/png/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls


    def createBackgroundMapSeries80kDownloadURLS(self, product_key, product_title):
        urls = []
         
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                         
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
     
            url = modified_key + "/16m/etrs89/png/" + sheet_name + "L.png?api_key="  + self.nls_user_key
            urls.append((url, product_title, product_key, "png"))
            url = modified_key + "/16m/etrs89/png/" + sheet_name + "R.png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)     
            urls.append((url, product_title, product_key, "png"))
             
        return urls
    
    def createBackgroundMapSeries40kDownloadURLS(self, product_key, product_title):
        urls = []
         
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                         
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
     
            url = modified_key + "/8m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + "L.png?api_key="  + self.nls_user_key
            urls.append((url, product_title, product_key, "png"))
            url = modified_key + "/8m/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + "R.png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
            urls.append((url, product_title, product_key, "png"))
             
        return urls
    
    def createTopographicMapRaster500kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs89/png/" + sheet_name + ".png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createTopographicMapRaster250kDownloadURLS(self, product_key, product_title):
        urls = []
         
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
                         
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
     
            url = modified_key + "/etrs89/png/" + sn1 + "/" + sn1 + "L/" + sheet_name + "L.png?api_key="  + self.nls_user_key
            urls.append((url, product_title, product_key, "png"))
            url = modified_key + "/etrs89/png/" + sn1 + "/" + sn1 + "R/" + sheet_name + "R.png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)     
            urls.append((url, product_title, product_key, "png"))
             
        return urls

    def createTopographicMapRaster100kDownloadURLS(self, product_key, product_title):
        urls = []
         
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                         
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
     
            url = modified_key + "/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + "L.png?api_key="  + self.nls_user_key
            urls.append((url, product_title, product_key, "png"))
            url = modified_key + "/etrs89/png/" + sn1 + "/" + sn2 + "/" + sheet_name + "R.png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
            urls.append((url, product_title, product_key, "png"))
             
        return urls
    
    def createControlPointsN2000DownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/KorkeusPisteet_N2000_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "gml"))
            
        return urls
    
    def createControlPointsN60DownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/KorkeusPisteet_N60_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "gml"))
            
        return urls
    
    def createControlPointsTM35FINDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/euref_etrs-tm35fin_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "gml"))
            
        return urls
    
    def createControlPointsEUREFFINDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/csv/Euref_geodeettiset_x.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "gml"))
            
        return urls
    
    def createOrthophotoColourInfraDownloadURLS(self, product_key, product_title):
        urls = []
        
        limit = 100
        offset = 0
        
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/orto/vaaravari_ortokuva?" + "limit=" + str(limit) + "&offset=" + str(offset) + "&api_key=" + self.nls_user_key
        QgsMessageLog.logMessage(product_url, 'NLSAtomClient', QgsMessageLog.INFO)
        
        while product_url is not "":
            r = requests.get(product_url)
            #QgsMessageLog.logMessage(r.text, 'NLSAtomClient', QgsMessageLog.INFO)
            
            e = xml.etree.ElementTree.fromstring(r.text.encode('utf-8'))
    
            for entry in e.findall('{http://www.w3.org/2005/Atom}entry'):
                link = entry.find('{http://www.w3.org/2005/Atom}link')
                url = link.attrib["href"]
                #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                
                for mun_utm_feature in self.mun_utm5_features:
                    sheet_name = mun_utm_feature['LEHTITUNNU']
                
                    if sheet_name in url:
                        urls.append((url, product_title, product_key, "jpeg2000"))
                        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                
            next_link = e.find('{http://www.w3.org/2005/Atom}link[@rel="next"]')
            #QgsMessageLog.logMessage(str(next_link), 'NLSAtomClient', QgsMessageLog.INFO)
            if next_link is not None:
                next_link_href = next_link.attrib["href"]
                #QgsMessageLog.logMessage(next_link_href, 'NLSAtomClient', QgsMessageLog.INFO)
                product_url = next_link_href
                QgsMessageLog.logMessage(product_url, 'NLSAtomClient', QgsMessageLog.INFO)
            else:
                product_url = ""
                #QgsMessageLog.logMessage("did not find link with rel next", 'NLSAtomClient', QgsMessageLog.INFO)
            
        return urls
    
    def createOrthophotoColourDownloadURLS(self, product_key, product_title):
        urls = []
        
        limit = 100
        offset = 0
        
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/orto/ortokuva?" + "limit=" + str(limit) + "&offset=" + str(offset) + "&api_key=" + self.nls_user_key
        QgsMessageLog.logMessage(product_url, 'NLSAtomClient', QgsMessageLog.INFO)
        
        while product_url is not "":
            r = requests.get(product_url)
            #QgsMessageLog.logMessage(r.text, 'NLSAtomClient', QgsMessageLog.INFO)
            
            e = xml.etree.ElementTree.fromstring(r.text.encode('utf-8'))
    
            for entry in e.findall('{http://www.w3.org/2005/Atom}entry'):
                link = entry.find('{http://www.w3.org/2005/Atom}link')
                url = link.attrib["href"]
                #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                
                for mun_utm_feature in self.mun_utm5_features:
                    sheet_name = mun_utm_feature['LEHTITUNNU']
                
                    if sheet_name in url:
                        urls.append((url, product_title, product_key, "jpeg2000"))
                        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
                
            next_link = e.find('{http://www.w3.org/2005/Atom}link[@rel="next"]')
            #QgsMessageLog.logMessage(str(next_link), 'NLSAtomClient', QgsMessageLog.INFO)
            if next_link is not None:
                next_link_href = next_link.attrib["href"]
                #QgsMessageLog.logMessage(next_link_href, 'NLSAtomClient', QgsMessageLog.INFO)
                product_url = next_link_href
                QgsMessageLog.logMessage(product_url, 'NLSAtomClient', QgsMessageLog.INFO)
            else:
                product_url = ""
                #QgsMessageLog.logMessage("did not find link with rel next", 'NLSAtomClient', QgsMessageLog.INFO)
            
        return urls
    
    def createElevationModel2mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
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
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createPlaceNamesDownloadURLS(self, product_url, product_key, product_title):
        urls = []
        
        r = requests.get(product_url)
        #QgsMessageLog.logMessage(r.text, 'NLSAtomClient', QgsMessageLog.INFO)
        
        e = xml.etree.ElementTree.fromstring(r.text.encode('utf-8'))

        for entry in e.findall('{http://www.w3.org/2005/Atom}entry'):
            link = entry.find('{http://www.w3.org/2005/Atom}link')
            url = link.attrib["href"]
            QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
            urls.append((url, product_title, product_key, "gml"))
            
        return urls
    
    def createPlaceNamesMapNames50kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_50?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames8000kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_8000?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames4500kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_4500?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames500kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_500?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames250kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_250?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames100kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_100?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames2000kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_2000?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames1000kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_1000?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesMapNames25kDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/karttanimet_25?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesPlacesDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/paikat?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createPlaceNamesPlaceNamesDownloadURLS(self, product_key, product_title):
        product_url = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/nimisto/paikannimet_kaikki?api_key=" + self.nls_user_key
        return self.createPlaceNamesDownloadURLS(product_url, product_key, product_title)
    
    def createTopographicDatabaseRoadsWithAddressesDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs89/shp/" + sheet_name + ".shp.zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "shp"))
            
        return urls

    
    def createMunicipalDivision100kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_100k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createMunicipalDivision4500kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/png/KarttakuvaaKuntarajoista_2017_4500k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "png"))
            
        return urls
    
    def createMunicipalDivision1000kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_1000k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createMunicipalDivision250kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_250k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls

    def createMunicipalDivision10kDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shp/TietoaKuntajaosta_2017_10k.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createShadedReliefRaster8mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createShadedReliefRaster512mDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs-tm35fin-n2000/suomi.tif?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createShadedReliefRaster128mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createShadedReliefRaster64mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createShadedReliefRaster32mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createElevationModel10mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm25_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
            sn2 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sn1 + "/" + sn2 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createElevationZonesRaster512mDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs-tm35fin-n2000/suomi.tif?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createElevationZonesRaster128mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createElevationZonesRaster64mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createElevationZonesRaster32mDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
            url = modified_key + "/etrs-tm35fin-n2000/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createCadastralIndexMapRasterCadastralIdentifiersDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp/kiinteistorekisterikartta/ktj_kiinteistotunnukset", "/tilauslataus/tuotteet/kiinteistorekisterikartta/avoin/karttalehdittain/tm35fin/png/ktj_kiinteistotunnukset")
    
            url = modified_key + "/" + sn1 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createCadastralIndexMapRasterCadastralUnitsDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm10_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:3]
                        
            modified_key = product_key.replace("/feed/mtp/kiinteistorekisterikartta/ktj_kiinteistorajat", "/tilauslataus/tuotteet/kiinteistorekisterikartta/avoin/karttalehdittain/tm35fin/png/ktj_kiinteistorajat")
    
            url = modified_key + "/" + sn1 + "/" + sheet_name + ".tif?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "geotiff"))
            
        return urls
    
    def createGeneralMap1000kAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shape/1_milj_Shape_etrs_shape.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createTopographicMap100kDownloadURLS(self, product_key, product_title):
        urls = []
        
        for mun_utm_feature in self.mun_utm100_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
                        
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
                
            url = modified_key + "/etrs89/shp/" + sn1 + "/" + sheet_name + ".zip?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
            urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createGeneralMap4500kAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "/etrs89/shape/4_5_milj_shape_etrs-tm35fin.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createTopographicMap250kDownloadURLS(self, product_key, product_title):
        urls = []
         
        for mun_utm_feature in self.mun_utm200_features:
            sheet_name = mun_utm_feature['LEHTITUNNU']
            sn1 = sheet_name[:2]
                         
            modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
     
            url = modified_key + "/etrs89/shp/" + "/" + sn1 + "/" + sheet_name + "L.png?api_key="  + self.nls_user_key
            urls.append((url, product_title, product_key, "shp"))
            url = modified_key + "/etrs89/shp/" + "/" + sn1 + "/" + sheet_name + "R.png?api_key="  + self.nls_user_key
            #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)     
            urls.append((url, product_title, product_key, "shp"))
             
        return urls
    
    def createMapSheetGridAllFeaturesDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "etrs89/shp/UTM_EUREF_SHP.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "shp"))
            
        return urls
    
    def createControlPointsLocationDrawingsForControlPointsDownloadURLS(self, product_key, product_title):
        urls = []
        
        modified_key = product_key.replace("/feed/mtp", "/tilauslataus/tuotteet")
    
        url = modified_key + "etrs89/tiff/asemapiirrokset_pakattu.zip?api_key="  + self.nls_user_key
        #QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
    
        urls.append((url, product_title, product_key, "geotiff"))
            
        return urls

    def downloadOneFile(self):
   
        if self.download_count == self.total_download_count or self.download_count >= len(self.all_urls):
            QgsMessageLog.logMessage("Should not be possible to be here", 'NLSAtomClient', QgsMessageLog.CRITICAL)
            QgsMessageLog.logMessage("self.download_count: " + str(self.download_count), 'NLSAtomClient', QgsMessageLog.INFO)
            QgsMessageLog.logMessage("Total download count: " + str(self.total_download_count), 'NLSAtomClient', QgsMessageLog.INFO)
            self.busy_indicator_dialog.hide()
            return
        
        url = self.all_urls[self.download_count][0]
        QgsMessageLog.logMessage(url, 'NLSAtomClient', QgsMessageLog.INFO)
        r = requests.get(url, stream=True)
        # TODO check r.status_code & r.ok
        
        url_parts = url.split('/')
        file_name = url_parts[-1].split('?')[0]
        
        dir_path = os.path.join(self.data_download_dir, self.all_urls[self.download_count][1])
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
        #z.extractall(os.path.join(self.data_download_dir, value))
        with open(os.path.join(dir_path, file_name), 'wb') as f:
            f.write(r.content)
            
        if self.addDownloadedDataAsLayer:
            if "zip" in file_name:
                dir_path = os.path.join(dir_path, file_name.split('.')[0])
                z = zipfile.ZipFile(StringIO.StringIO(r.content))
                z.extractall(dir_path)
                
            data_type = self.all_urls[self.download_count][3]
                
            for listed_file_name in os.listdir(dir_path):
                if (data_type == "shp" and listed_file_name.endswith(".shp")) or \
                    (data_type == "gml" and listed_file_name.endswith(".xml")):
                    found_layer = False
                    current_layers = self.iface.legendInterface().layers()
                    for current_layer in current_layers:
                        if current_layer.name() == "file":
                            found_layer = True
                            break
                    if not found_layer:
                        new_layer = QgsVectorLayer(os.path.join(dir_path, listed_file_name), listed_file_name, "ogr")
                        if new_layer.isValid():
                            QgsMapLayerRegistry.instance().addMapLayers([new_layer])
                if (data_type == "png" and listed_file_name.endswith(".png")) or \
                    (data_type == "geotiff" and listed_file_name.endswith(".tif")) or \
                    (data_type == "jpeg2000" and listed_file_name.endswith(".jp2")):
                    found_layer = False
                    current_layers = self.iface.legendInterface().layers()
                    for current_layer in current_layers:
                        if current_layer.name() == "file":
                            found_layer = True
                            break
                    if not found_layer:
                        new_layer = QgsRasterLayer(os.path.join(dir_path, listed_file_name), listed_file_name)
                        if new_layer.isValid():
                            QgsMapLayerRegistry.instance().addMapLayers([new_layer])
                
            #QgsMapLayerRegistry.instance().addMapLayers([self.municipality_layer])
        
        self.download_count += 1
        percentage = self.download_count / float(self.total_download_count) * 100.0
        percentage_text = "%.2f" % round(percentage, 2)
        
        self.busy_indicator_dialog.setMessage("A moment... processed " + percentage_text + "% of the files ")
        #self.iface.messageBar().pushMessage("A moment... processed " + percentage_text + "% of files")
        QgsMessageLog.logMessage("A moment... processed " + percentage_text + "% of the files", 'NLSAtomClient', QgsMessageLog.INFO)
        
        if self.download_count == self.total_download_count:
            QgsMessageLog.logMessage("done downloading data", 'NLSAtomClient', QgsMessageLog.INFO)
            self.busy_indicator_dialog.hide()
            self.iface.messageBar().pushMessage("Download finished", "NLS data download finished. Data located under " + self.data_download_dir, level=QgsMessageBar.SUCCESS)#, duration=10)
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

    def showSettingsDialog(self):
        self.nls_user_key_dialog.userKeyLineEdit.setText(self.nls_user_key)
        self.nls_user_key_dialog.dataLocationQgsFileWidget.setFilePath(os.path.join(self.path, "data"))
        self.nls_user_key_dialog.addDownloadedDataAsLayerCheckBox.setChecked(self.addDownloadedDataAsLayer)
        self.nls_user_key_dialog.showMunicipalitiesAsLayerCheckBox.setChecked(self.showMunicipalitiesAsLayer)
        self.nls_user_key_dialog.showUTMGridsAsLayerCheckBox.setChecked(self.showUTMGridsAsLayer)
        
        #self.addDownloadedDataAsLayer = QSettings().value("/NLSAtomClient/addDownloadedDataAsLayer", True, type=bool)
        #self.showMunicipalitiesAsLayer = QSettings().value("/NLSAtomClient/showMunicipalitiesAsLayer", True, type=bool)
        #self.showUTMGridsAsLayer = QSettings().value("/NLSAtomClient/showUTMGridsAsLayer", False, type=bool)
        
        #addDownloadedDataAsLayerCheckBox
        #showMunicipalitiesAsLayerCheckBox
        #showUTMGridsAsLayerCheckBox
        
        
        self.nls_user_key_dialog.show()
        # Run the dialog event loop
        result = self.nls_user_key_dialog.exec_()
        # See if OK was pressed
        if result:
            self.nls_user_key = self.nls_user_key_dialog.userKeyLineEdit.text()
            if self.nls_user_key == "":
                # cannot work without the key, so user needs to be notified
                QMessageBox.critical(self.iface.mainWindow(), "User-key is needed", "Data cannot be downloaded without the NLS key") 
                return
            self.data_download_dir = self.nls_user_key_dialog.dataLocationQgsFileWidget.filePath()
            self.addDownloadedDataAsLayer = self.nls_user_key_dialog.addDownloadedDataAsLayerCheckBox.isChecked()
            self.showMunicipalitiesAsLayer = self.nls_user_key_dialog.showMunicipalitiesAsLayerCheckBox.isChecked()
            self.showUTMGridsAsLayer = self.nls_user_key_dialog.showUTMGridsAsLayerCheckBox.isChecked()
            
            QSettings().setValue("/NLSAtomClient/userKey", self.nls_user_key)
            QSettings().setValue("/NLSAtomClient/dataDownloadDir", self.data_download_dir)
            QSettings().setValue("/NLSAtomClient/addDownloadedDataAsLayer", self.addDownloadedDataAsLayer)
            QSettings().setValue("/NLSAtomClient/showMunicipalitiesAsLayer", self.showMunicipalitiesAsLayer)
            QSettings().setValue("/NLSAtomClient/showUTMGridsAsLayer", self.showUTMGridsAsLayer)
        else:
            if self.nls_user_key == "":
                # cannot work without the key, so user needs to be notified
                QMessageBox.critical(self.iface.mainWindow(), "User-key is needed", "Data cannot be downloaded without the NLS key") 
                return

    def initWithNLSData(self):
        self.path = os.path.dirname(__file__)
        self.data_download_dir = self.path
        
        self.nls_user_key_dialog = uic.loadUi(os.path.join(self.path, NLS_USER_KEY_DIALOG_FILE))
        
        #=======================================================================
        # first_run = False
        # 
        # dir_path = os.path.join(self.path, "data")
        # #QgsMessageLog.logMessage(dir_path, 'NLSAtomClient', QgsMessageLog.INFO)
        # if not os.path.exists(dir_path):
        #     first_run = True
        #     try:
        #         os.makedirs(dir_path)
        #     except OSError as exc: # Guard against race condition
        #         if exc.errno != errno.EEXIST:
        #             raise
        #         else:
        #             QgsMessageLog.logMessage(exc.errno, 'NLSAtomClient', QgsMessageLog.CRITICAL)
        # if not os.path.exists(dir_path):
        #     QgsMessageLog.logMessage("Directory " + dir_path + "could not be created", 'NLSAtomClient', QgsMessageLog.CRITICAL)
        #     
        # if first_run:
        #     utm_urls = self.createMapSheetGridAllFeaturesDownloadURLS('https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/karttalehtijako_ruudukko/kaikki', '')
        #     utm_zip_url = utm_urls[0][0]
        #     
        #     r = requests.get(utm_zip_url, stream=True)
        #     z = zipfile.ZipFile(StringIO.StringIO(r.content))
        #     z.extractall(os.path.join(self.path, "data"))
        #     
        #     municipalities_urls = self.createMunicipalDivision10kDownloadURLS('https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/kuntajako/kuntajako_10k', '')
        #     municipalities_zip_url = municipalities_urls[0][0]
        # 
        #     r = requests.get(municipalities_zip_url, stream=True)
        #     z = zipfile.ZipFile(StringIO.StringIO(r.content))
        #     z.extractall(os.path.join(self.path, "data"))
        #=======================================================================
        
        
        
        