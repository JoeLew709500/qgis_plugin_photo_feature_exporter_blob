def classFactory(iface):
    from .photo_exporter import PhotoExporter
    return PhotoExporter(iface)