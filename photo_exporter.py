from qgis.core import QgsProject, QgsPathResolver, QgsDataSourceUri
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
            self.create_geopackage_with_photos(output_path, selected_features, photo_field_names, layer)

    def convert_photo_to_blob(self, photo_path):
        try:  # Add a try-except block to handle potential file errors
            with open(photo_path, 'rb') as file:
                blob = file.read()
            return blob
        except FileNotFoundError:
            self.iface.messageBar().pushMessage("Error", f"Photo file not found: {photo_path}", level=2)
            return None
        except OSError as e: # Catch other potential OS errors
            self.iface.messageBar().pushMessage("Error", f"Error reading photo file: {photo_path} - {e}", level=2)
            return None


    def create_geopackage_with_photos(self, output_path, features, photo_field_names, layer):
        driver = ogr.GetDriverByName('GPKG')
        if driver is None:
            raise RuntimeError("GeoPackage driver not available.")
        data_source = driver.CreateDataSource(output_path)
        if data_source is None:
            raise RuntimeError(f"Failed to create data source at {output_path}.")
        layer_name = layer.name()  # Use the original layer's name
        
        # Get the geometry type from the original layer
        geometry_type = layer.geometryType()
        
        # Map QGIS geometry types to OGR geometry types
        if geometry_type == 0:  # Point
            ogr_geom_type = ogr.wkbPoint
        elif geometry_type == 1:  # LineString
            ogr_geom_type = ogr.wkbLineString
        elif geometry_type == 2:  # Polygon
            ogr_geom_type = ogr.wkbPolygon
        else:
            self.iface.messageBar().pushMessage("Error", "Unsupported geometry type.", level=3)
            return
        
        
        gpkg_layer = data_source.CreateLayer(layer_name, geom_type=ogr_geom_type) # Use the determined OGR geometry type
        if gpkg_layer is None:
            raise RuntimeError("Failed to create layer in GeoPackage.")

        # Create fields from the original layer (excluding photo fields, and geometry)
        #  Do this *before* creating the photo fields
        layer_defn = layer.dataProvider().fields()
        for i in range(layer_defn.count()):
            field = layer_defn.field(i)
            if field.name() not in photo_field_names:
                ogr_field_type = ogr.OFTString  # Default to String
                if field.typeName() == 'Integer':
                    ogr_field_type = ogr.OFTInteger
                elif field.typeName() == 'Integer64':  # Handle Integer64
                    ogr_field_type = ogr.OFTInteger64
                elif field.typeName() == 'Real':
                    ogr_field_type = ogr.OFTReal
                elif field.typeName() == 'Date':
                    ogr_field_type = ogr.OFTDate  # Handle Date
                elif field.typeName() == 'DateTime':
                     ogr_field_type = ogr.OFTDateTime # Handle DateTime
                # Add more type conversions as needed
                field_defn = ogr.FieldDefn(field.name(), ogr_field_type)
                # Corrected: Use SetPrecision (capitalized)
                if ogr_field_type == ogr.OFTReal:  # Only set precision for Real fields
                    field_defn.SetPrecision(field.precision()) # Keep the precision
                field_defn.SetWidth(field.length())         # Keep the length
                gpkg_layer.CreateField(field_defn)
        
        # Create fields for photo blobs *after* other fields
        for photo_field_name in photo_field_names:
            field_defn = ogr.FieldDefn(photo_field_name, ogr.OFTBinary)
            gpkg_layer.CreateField(field_defn)



        for feature in features:
            geom = feature.geometry()
            new_feature = ogr.Feature(gpkg_layer.GetLayerDefn())
            new_feature.SetGeometry(ogr.CreateGeometryFromWkt(geom.asWkt()))

            # Set attribute values (excluding photo fields)
            for i in range(layer_defn.count()):
                field = layer_defn.field(i)
                if field.name() not in photo_field_names:
                    # Get the value and handle potential QVariant conversion
                    value = feature[field.name()]
                    if isinstance(value, QVariant):
                        value = value.toPyObject()  # Convert QVariant to native Python type
                    try:
                         new_feature.SetField(field.name(), value)
                    except TypeError as e:
                        self.iface.messageBar().pushMessage("Error", f"Type error setting field {field.name()}: {e}", level=2)
                        continue # Skip to the next field

            
            # Handle the photo fields (relative or absolute paths)
            for photo_field_name in photo_field_names:
                photo_path_value = feature[photo_field_name]
                if isinstance(photo_path_value, QVariant):
                    photo_path_value = str(photo_path_value)  # Convert QVariant to string

                if not photo_path_value or len(photo_path_value) < 5:  # More robust check for empty/invalid paths
                    continue  # Skip NULL or very short values

                # Resolve relative paths
                photo_path = self.resolve_path(photo_path_value, layer)

                if photo_path:  # Check if path resolution was successful
                    photo_blob = self.convert_photo_to_blob(photo_path)
                    if photo_blob: # Only set the field if the blob was created
                       new_feature.SetField(photo_field_name, photo_blob)
                #else:  #Optionally handle unresolved paths
                    # print(f"Could not resolve path: {photo_path_value}")

            gpkg_layer.CreateFeature(new_feature)
        data_source = None



    def resolve_path(self, photo_path_value, layer):
        """Resolves a potentially relative path to an absolute path."""

        # 1. Check if the path is already absolute
        if os.path.isabs(photo_path_value):
            return photo_path_value

        # 2. Try to resolve relative to the project file
        project_path = QgsProject.instance().fileName()  # Corrected: Use fileName()
        if project_path:
            absolute_path = os.path.join(os.path.dirname(project_path), photo_path_value)
            if os.path.exists(absolute_path):
                return absolute_path

        # 3. Try to resolve relative to the layer's data source
        layer_source = layer.source()
        if layer_source:
            uri = QgsDataSourceUri(layer_source)
            layer_path = uri.uri(   )  # Get the layer's file path from the URI
            if layer_path:
                absolute_path = os.path.join(os.path.dirname(layer_path), photo_path_value)
                if os.path.exists(absolute_path):
                  return absolute_path
                    

        # 4. If none of the above work, the path cannot be resolved
        return None