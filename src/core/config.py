import os
import sys

def get_root_dir():
    """Returns the absolute root directory of the application, handling PyInstaller bundles."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Application Constants & Default Settings
APP_TITLE = "Manga Downloader"
APP_GEOMETRY = "1000x600"
APP_MIN_SIZE = (900, 540)
DEFAULT_DOWNLOAD_DIR = "Downloads_Manga"
CONFIG_FILENAME = "sites.json"

# Webtoon / Long Strip Threshold Ratio
WEBTOON_ASPECT_RATIO_THRESHOLD = 1.8

# Device Presets Configuration
DEVICE_PRESETS = {
    "Kindle Paperwhite 11": {
        'fmt': "epub", 
        'w': "1236", 
        'h': "1648", 
        'rtl': True, 
        'crop': True, 
        'resize': "Keep", 
        'gray': True, 
        'contrast_val': 1.2, 
        'dp_mode': "Rotacionar", 
        'qual': 85
    },
    "Galaxy Tab S10 Lite": {
        'fmt': "cbz", 
        'w': "1320", 
        'h': "2112", 
        'rtl': False, 
        'crop': False, 
        'resize': "Keep", 
        'gray': False, 
        'contrast_val': 1.0, 
        'dp_mode': "Manter", 
        'qual': 100
    },
    "Custom": {
        'fmt': "pdf", 
        'w': "1200", 
        'h': "1600", 
        'rtl': False, 
        'crop': False, 
        'resize': "Keep", 
        'gray': False, 
        'contrast_val': 1.0, 
        'dp_mode': "Manter", 
        'qual': 100
    }
}
