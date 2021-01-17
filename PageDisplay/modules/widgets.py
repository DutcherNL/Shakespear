from PageDisplay.module_widgets import BaseModuleWidget


class DownloadFileWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_download_file.html"


class ExternalURLWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_external_uri.html"
