from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QListWidget, QListWidgetItem

class PhotoExporterDialog(QDialog):
    def __init__(self, layer):
        super().__init__()
        self.setWindowTitle('Export Photos to GeoPackage')
        self.layout = QVBoxLayout()

        self.label = QLabel('Select output file:')
        self.layout.addWidget(self.label)

        self.file_path_edit = QLineEdit()
        self.layout.addWidget(self.file_path_edit)

        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_file)
        self.layout.addWidget(self.browse_button)

        self.field_label = QLabel('Select photo fields:')
        self.layout.addWidget(self.field_label)

        self.field_list = QListWidget()
        self.field_list.setSelectionMode(QListWidget.MultiSelection)
        self.populate_fields(layer)
        self.layout.addWidget(self.field_list)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'GeoPackage (*.gpkg)')
        if file_path:
            self.file_path_edit.setText(file_path)

    def get_file_path(self):
        return self.file_path_edit.text()

    def get_selected_fields(self):
        selected_items = self.field_list.selectedItems()
        return [item.text() for item in selected_items]

    def populate_fields(self, layer):
        fields = [field.name() for field in layer.fields()]
        for field in fields:
            item = QListWidgetItem(field)
            self.field_list.addItem(item)