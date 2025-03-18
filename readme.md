**QGIS Photo Feature Exporter with BLOB Photo Embedding**

This QGIS plugin streamlines the process of exporting spatial features and their associated photographs into a single, portable GeoPackage file. By converting linked photos into Binary Large Objects (BLOBs), the plugin stores them directly within the GeoPackage, eliminating the need for separate photo folders. This simplifies data distribution and management, ensuring that all relevant information is contained within a single file.

**Features:**

* **GeoPackage Export:** Exports selected features from any compatible QGIS layer to a GeoPackage.
* **BLOB Photo Conversion:** Automatically converts linked image files into BLOB data.
* **Embedded Photo Storage:** Stores BLOB data directly within the GeoPackage, eliminating external file dependencies.
* **Simplified Data Management:** Creates a self-contained GeoPackage with both spatial data and images.
* **Easy Installation:** Install the plugin from a ZIP file within QGIS.

**How to Use:**

1.  **Selection:** Select the features in your QGIS layer that you wish to export.
2.  **Plugin Execution:** Run the "Photo Feature Exporter (Blob)" plugin from the QGIS plugin menu.
3.  **Output Path:** Specify the output path and filename for your GeoPackage.
4.  **Photo Linking:** Ensure that your layer's attribute table contains a field with the correct file paths to your photos.
5.  **Enjoy:** Open the resulting GeoPackage in QGIS or any GeoPackage-compatible software to view your features and embedded photos.

**Requirements:**

* QGIS (latest stable version recommended)
* A QGIS layer with a field containing paths to image files.

**Benefits:**

* Portability: Easily share and distribute your data in a single file.
* Organization: Keep spatial data and associated photos together.
* Data Integrity: Reduce the risk of broken file links.

**Installation:**

1.  Download the `qgis_plugin_photo_feature_exporter_blob.zip` file from the release page.
2.  Open QGIS and navigate to Plugins -> Manage and Install Plugins...
3.  Select "Install from ZIP" and choose the downloaded ZIP file.
4.  Enable the plugin in the Plugins Manager.