import os

try:
    import ctypes
    has_ctypes = True
except ImportError:
    has_ctypes = False

MAX_PATH = 260
CSIDL_APPDATA = 0x001A
CSIDL_LOCAL_APPDATA = 0x001c
CSIDL_PERSONAL = 0x0005

def get_appdata_dir():
    dir = None
    if has_ctypes:
        SHGetSpecialFolderPath = ctypes.windll.shell32.SHGetSpecialFolderPathW
        buf = ctypes.create_unicode_buffer(MAX_PATH)
        SHGetSpecialFolderPath(None, buf, CSIDL_APPDATA, 0)
        dir = buf.value
    return dir

def get_program_files_dir():
    return os.environ['ProgramFiles']

