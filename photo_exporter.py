from qgis.core import QgsProject
from qgis.utils import iface
from osgeo import ogr
from PyQt5.QtWidgets import QAction, QDialog
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QVariant
import os
from .photo_exporter_dialog import PhotoExporterDialog

class PhotoExporter:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&Photo Exporter')
        self.toolbar = self.iface.addToolBar(u'Photo Exporter')
        self.toolbar.setObjectName(u'Photo Exporter')

    def tr(self, message):
        return QCoreApplication.translate('PhotoExporter', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/photo_exporter/icon.png'
        self.add_action(icon_path, text=self.tr(u'Export Photos to GeoPackage'), callback=self.run, parent=self.iface.mainWindow())

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Photo Exporter'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        layer = iface.activeLayer()
        if not layer:
            self.iface.messageBar().pushMessage("Error", "No active layer selected", level=3)
            return

        dialog = PhotoExporterDialog(layer)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            output_path = dialog.get_file_path()
            photo_field_names = dialog.get_selected_fields()
            selected_features = layer.selectedFeatures()
            self.create_geopackage_with_photos(output_path, selected_features, photo_field_names)

    def convert_photo_to_blob(self, photo_path):
        with open(photo_path, 'rb') as file:
            blob = file.read()
        return blob
    
    def create_geopackage_with_photos(self, output_path, features, photo_field_names):
        driver = ogr.GetDriverByName('GPKG')
        if driver is None:
            raise RuntimeError("GeoPackage driver not available.")
        data_source = driver.CreateDataSource(output_path)
        if data_source is None:
            raise RuntimeError(f"Failed to create data source at {output_path}.")
        layer = data_source.CreateLayer('test', geom_type=ogr.wkbPoint)
        if layer is None:
            raise RuntimeError("Failed to create layer in GeoPackage.")
        
        for photo_field_name in photo_field_names:
            field_defn = ogr.FieldDefn(photo_field_name, ogr.OFTBinary)
            layer.CreateField(field_defn)

        for feature in features:
            geom = feature.geometry()
            new_feature = ogr.Feature(layer.GetLayerDefn())
            new_feature.SetGeometry(ogr.CreateGeometryFromWkt(geom.asWkt()))
            for photo_field_name in photo_field_names:
                photo_path = feature[photo_field_name]
                if isinstance(photo_path, QVariant):
                    photo_path = str(photo_path)  # Convert QVariant to string
                if len(photo_path) < 5:
                    continue  # Skip NULL values
                photo_blob = self.convert_photo_to_blob(photo_path)
                new_feature.SetField(photo_field_name, photo_blob)
            layer.CreateFeature(new_feature)
        data_source = None