import ctypes

DeleteFile = ctypes.windll.kernel32.DeleteFileW
DeleteFile.argtypes = [ctypes.c_wchar_p]
DeleteFile.restype = ctypes.wintypes.HANDLE

RemoveDirectory = ctypes.windll.kernel32.RemoveDirectoryW
RemoveDirectory.argtypes = [ctypes.c_wchar_p]
RemoveDirectory.restype = ctypes.wintypes.HANDLE
