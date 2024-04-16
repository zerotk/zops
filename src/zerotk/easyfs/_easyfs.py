from __future__ import unicode_literals
'''
This module contains a selection of file related functions that can be used anywhere.

Some sort of wrapper for common builtin 'os' operations with a nicer interface.

These functions abstract file location, most of them work for either local, ftp or http protocols
'''
import contextlib
import io
import os
import re
import sys
import six



#===================================================================================================
# Constants
#===================================================================================================
SEPARATOR_UNIX = '/'
SEPARATOR_WINDOWS = '\\'
EOL_STYLE_NONE = None  # Binary files
EOL_STYLE_UNIX = '\n'
EOL_STYLE_WINDOWS = '\r\n'
EOL_STYLE_MAC = '\r'

def _GetNativeEolStyle(platform=sys.platform):
    '''
    Internal function that determines EOL_STYLE_NATIVE constant with the proper value for the
    current platform.
    '''
    _NATIVE_EOL_STYLE_MAP = {
        'win32' : EOL_STYLE_WINDOWS,
        'linux2' : EOL_STYLE_UNIX,
        'linux' : EOL_STYLE_UNIX,
        'darwin' : EOL_STYLE_MAC,
    }
    result = _NATIVE_EOL_STYLE_MAP.get(platform)

    if result is None:
        from ._exceptions import UnknownPlatformError
        raise UnknownPlatformError(platform)

    return result

EOL_STYLE_NATIVE = _GetNativeEolStyle()

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364939%28v=vs.85%29.aspx
# The drive type cannot be determined.
DRIVE_UNKNOWN = 0
# The root path is invalid; for example, there is no volume mounted at the specified path.
DRIVE_NO_ROOT_DIR = 1
# The drive has removable media; for example, a floppy drive, thumb drive, or flash card reader.
DRIVE_REMOVABLE = 2
# The drive has fixed media; for example, a hard disk drive or flash drive.
DRIVE_FIXED = 3
# The drive is a remote (network) drive.
DRIVE_REMOTE = 4
# The drive is a CD-ROM drive.
DRIVE_CDROM = 5
# The drive is a RAM disk
DRIVE_RAMDISK = 6

#===================================================================================================
# Cwd
#===================================================================================================
@contextlib.contextmanager
def Cwd(directory):
    '''
    Context manager for current directory (uses with_statement)

    e.g.:
        # working on some directory
        with Cwd('/home/new_dir'):
            # working on new_dir

        # working on some directory again

    :param unicode directory:
        Target directory to enter
    '''
    old_directory = six.moves.getcwd()
    if directory is not None:
        os.chdir(directory)
    try:
        yield directory
    finally:
        os.chdir(old_directory)



#===================================================================================================
# NormalizePath
#===================================================================================================
def NormalizePath(path):
    '''
    Normalizes a path maintaining the final slashes.

    Some environment variables need the final slash in order to work.

    Ex. The SOURCES_DIR set by subversion must end with a slash because of the way it is used
    in the Visual Studio projects.

    :param unicode path:
        The path to normalize.

    :rtype: unicode
    :returns:
        Normalized path
    '''
    if path.endswith('/') or path.endswith('\\'):
        slash = os.path.sep
    else:
        slash = ''
    return os.path.normpath(path) + slash


#===================================================================================================
# CanonicalPath
#===================================================================================================
def CanonicalPath(path):
    '''
    Returns a version of a path that is unique.

    Given two paths path1 and path2:
        CanonicalPath(path1) == CanonicalPath(path2) if and only if they represent the same file on
        the host OS. Takes account of case, slashes and relative paths.

    :param unicode path:
        The original path.

    :rtype: unicode
    :returns:
        The unique path.
    '''
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    path = os.path.normcase(path)

    return path


#===================================================================================================
# StandardizePath
#===================================================================================================
def StandardizePath(path, strip=False):
    '''
    Replaces all slashes and backslashes with the target separator

    StandardPath:
        We are defining that the standard-path is the one with only back-slashes in it, either
        on Windows or any other platform.

    :param bool strip:
        If True, removes additional slashes from the end of the path.
    '''
    path = path.replace(SEPARATOR_WINDOWS, SEPARATOR_UNIX)
    if strip:
        path = path.rstrip(SEPARATOR_UNIX)
    return path



#===================================================================================================
# NormStandardPath
#===================================================================================================
def NormStandardPath(path):
    '''
    Normalizes a standard path (posixpath.normpath) maintaining any slashes at the end of the path.

    Normalize:
        Removes any local references in the path "/../"

    StandardPath:
        We are defining that the standard-path is the one with only back-slashes in it, either
        on Windows or any other platform.
    '''
    import posixpath
    if path.endswith('/'):
        slash = '/'
    else:
        slash = ''
    return posixpath.normpath(path) + slash



#===================================================================================================
# CreateMD5
#===================================================================================================
def CreateMD5(source_filename, target_filename=None):
    '''
    Creates a md5 file from a source file (contents are the md5 hash of source file)

    :param unicode source_filename:
        Path to source file

    :type target_filename: unicode or None
    :param target_filename:
        Name of the target file with the md5 contents

        If None, defaults to source_filename + '.md5'
    '''
    if target_filename is None:
        target_filename = source_filename + '.md5'

    from six.moves.urllib.parse import urlparse
    source_url = urlparse(source_filename)

    # Obtain MD5 hex
    if _UrlIsLocal(source_url):
        # If using a local file, we can give Md5Hex the filename
        md5_contents = Md5Hex(filename=source_filename)
    else:
        # Md5Hex can't handle remote files, we open it and pray we won't run out of memory.
        md5_contents = Md5Hex(contents=GetFileContents(source_filename, binary=True))

    # Write MD5 hash to a file
    CreateFile(target_filename, md5_contents)



MD5_SKIP = 'md5_skip'  # Returned to show that a file copy was skipped because it hasn't changed.
#===================================================================================================
# CopyFile
#===================================================================================================
def CopyFile(source_filename, target_filename, override=True, md5_check=False, copy_symlink=True):
    '''
    Copy a file from source to target.

    :param  source_filename:
        @see _DoCopyFile

    :param  target_filename:
        @see _DoCopyFile

    :param bool md5_check:
        If True, checks md5 files (of both source and target files), if they match, skip this copy
        and return MD5_SKIP

        Md5 files are assumed to be {source, target} + '.md5'

        If any file is missing (source, target or md5), the copy will always be made.

    :param  copy_symlink:
        @see _DoCopyFile

    :raises FileAlreadyExistsError:
        If target_filename already exists, and override is False

    :raises NotImplementedProtocol:
        If file protocol is not accepted

        Protocols allowed are:
            source_filename: local, ftp, http
            target_filename: local, ftp

    :rtype: None | MD5_SKIP
    :returns:
        MD5_SKIP if the file was not copied because there was a matching .md5 file

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from ._exceptions import FileNotFoundError

    # Check override
    if not override and Exists(target_filename):
        from ._exceptions import FileAlreadyExistsError
        raise FileAlreadyExistsError(target_filename)

    # Don't do md5 check for md5 files themselves.
    md5_check = md5_check and not target_filename.endswith('.md5')

    # If we enabled md5 checks, ignore copy of files that haven't changed their md5 contents.
    if md5_check:
        source_md5_filename = source_filename + '.md5'
        target_md5_filename = target_filename + '.md5'
        try:
            source_md5_contents = GetFileContents(source_md5_filename)
        except FileNotFoundError:
            source_md5_contents = None

        try:
            target_md5_contents = GetFileContents(target_md5_filename)
        except FileNotFoundError:
            target_md5_contents = None

        if source_md5_contents is not None and \
           source_md5_contents == target_md5_contents and \
           Exists(target_filename):
            return MD5_SKIP

    # Copy source file
    _DoCopyFile(source_filename, target_filename, copy_symlink=copy_symlink)

    # If we have a source_md5, but no target_md5, create the target_md5 file
    if md5_check and source_md5_contents is not None and source_md5_contents != target_md5_contents:
        CreateFile(target_md5_filename, source_md5_contents)


def _DoCopyFile(source_filename, target_filename, copy_symlink=True):
    '''
    :param unicode source_filename:
        The source filename.
        Schemas: local, ftp, http

    :param unicode target_filename:
        Target filename.
        Schemas: local, ftp

    :param  copy_symlink:
        @see _CopyFileLocal

    :raises FileNotFoundError:
        If source_filename does not exist
    '''
    from six.moves.urllib.parse import urlparse

    source_url = urlparse(source_filename)
    target_url = urlparse(target_filename)

    if _UrlIsLocal(source_url):
        if not Exists(source_filename):
            from ._exceptions import FileNotFoundError
            raise FileNotFoundError(source_filename)

        if _UrlIsLocal(target_url):
            # local to local
            _CopyFileLocal(source_filename, target_filename, copy_symlink=copy_symlink)
        elif target_url.scheme in ['ftp']:
            from ._exceptions import NotImplementedProtocol
            raise NotImplementedProtocol(target_url.scheme)
        else:
            from ._exceptions import NotImplementedProtocol
            raise NotImplementedProtocol(target_url.scheme)

    elif source_url.scheme in ['http', 'https', 'ftp']:
        if _UrlIsLocal(target_url):
            # HTTP/FTP to local
            from ._exceptions import NotImplementedProtocol
            raise NotImplementedProtocol(target_url.scheme)
        else:
            # HTTP/FTP to other ==> NotImplemented
            from ._exceptions import NotImplementedProtocol
            raise NotImplementedProtocol(target_url.scheme)
    else:
        from ._exceptions import NotImplementedProtocol  # @Reimport
        raise NotImplementedProtocol(source_url.scheme)


def _CopyFileLocal(source_filename, target_filename, copy_symlink=True):
    '''
    Copy a file locally to a directory.

    :param unicode source_filename:
        The filename to copy from.

    :param unicode target_filename:
        The filename to copy to.

    :param bool copy_symlink:
        If True and source_filename is a symlink, target_filename will also be created as
        a symlink.

        If False, the file being linked will be copied instead.
    '''
    import shutil
    try:
        # >>> Create the target_filename directory if necessary
        dir_name = os.path.dirname(target_filename)
        if dir_name and not os.path.isdir(dir_name):
            os.makedirs(dir_name)

        if copy_symlink and IsLink(source_filename):
            # >>> Delete the target_filename if it already exists
            if os.path.isfile(target_filename) or IsLink(target_filename):
                DeleteFile(target_filename)

            # >>> Obtain the relative path from link to source_filename (linkto)
            source_filename = ReadLink(source_filename)
            CreateLink(source_filename, target_filename)
        else:
            # shutil can't copy links in Windows, so we must find the real file manually
            if sys.platform == 'win32':
                while IsLink(source_filename):
                    link = ReadLink(source_filename)
                    if os.path.isabs(link):
                        source_filename = link
                    else:
                        source_filename = os.path.join(os.path.dirname(source_filename), link)

            shutil.copyfile(source_filename, target_filename)
            shutil.copymode(source_filename, target_filename)
    except Exception as e:
        raise(e, 'While executiong _filesystem._CopyFileLocal(%s, %s)' % (source_filename, target_filename))



#===================================================================================================
# CopyFiles
#===================================================================================================
def CopyFiles(source_dir, target_dir, create_target_dir=False, md5_check=False):
    '''
    Copy files from the given source to the target.

    :param unicode source_dir:
        A filename, URL or a file mask.
        Ex.
            x:\coilib50
            x:\coilib50\*
            http://server/directory/file
            ftp://server/directory/file


    :param unicode target_dir:
        A directory or an URL
        Ex.
            d:\Temp
            ftp://server/directory

    :param bool create_target_dir:
        If True, creates the target path if it doesn't exists.

    :param bool md5_check:
        .. seealso:: CopyFile

    :raises DirectoryNotFoundError:
        If target_dir does not exist, and create_target_dir is False

    .. seealso:: CopyFile for documentation on accepted protocols

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    import fnmatch

    # Check if we were given a directory or a directory with mask
    if IsDir(source_dir):
        # Yes, it's a directory, copy everything from it
        source_mask = '*'
    else:
        # Split directory and mask
        source_dir, source_mask = os.path.split(source_dir)

    # Create directory if necessary
    if not IsDir(target_dir):
        if create_target_dir:
            CreateDirectory(target_dir)
        else:
            from ._exceptions import DirectoryNotFoundError
            raise DirectoryNotFoundError(target_dir)

    # List and match files
    filenames = ListFiles(source_dir)

    # Check if we have a source directory
    if filenames is None:
        return

    # Copy files
    for i_filename in filenames:
        if md5_check and i_filename.endswith('.md5'):
            continue  # md5 files will be copied by CopyFile when copying their associated files

        if fnmatch.fnmatch(i_filename, source_mask):
            source_path = source_dir + '/' + i_filename
            target_path = target_dir + '/' + i_filename

            if IsDir(source_path):
                # If we found a directory, copy it recursively
                CopyFiles(source_path, target_path, create_target_dir=True, md5_check=md5_check)
            else:
                CopyFile(source_path, target_path, md5_check=md5_check)



#===================================================================================================
# CopyFilesX
#===================================================================================================
def CopyFilesX(file_mapping):
    '''
    Copies files into directories, according to a file mapping

    :param list(tuple(unicode,unicode)) file_mapping:
        A list of mappings between the directory in the target and the source.
        For syntax, @see: ExtendedPathMask

    :rtype: list(tuple(unicode,unicode))
    :returns:
        List of files copied. (source_filename, target_filename)

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    # List files that match the mapping
    files = []
    for i_target_path, i_source_path_mask in file_mapping:
        tree_recurse, flat_recurse, dirname, in_filters, out_filters = ExtendedPathMask.Split(i_source_path_mask)

        _AssertIsLocal(dirname)

        filenames = FindFiles(dirname, in_filters, out_filters, tree_recurse)
        for i_source_filename in filenames:
            if os.path.isdir(i_source_filename):
                continue  # Do not copy dirs

            i_target_filename = i_source_filename[len(dirname) + 1:]
            if flat_recurse:
                i_target_filename = os.path.basename(i_target_filename)
            i_target_filename = os.path.join(i_target_path, i_target_filename)

            files.append((
                StandardizePath(i_source_filename),
                StandardizePath(i_target_filename)
            ))

    # Copy files
    for i_source_filename, i_target_filename in files:
        # Create target dir if necessary
        target_dir = os.path.dirname(i_target_filename)
        CreateDirectory(target_dir)

        CopyFile(i_source_filename, i_target_filename)

    return files



#===================================================================================================
# IsFile
#===================================================================================================
def IsFile(path):
    '''
    :param unicode path:
        Path to a file (local or ftp)

    :raises NotImplementedProtocol:
        If checking for a non-local, non-ftp file

    :rtype: bool
    :returns:
        True if the file exists

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from six.moves.urllib.parse import urlparse
    url = urlparse(path)

    if _UrlIsLocal(url):
        if IsLink(path):
            return IsFile(ReadLink(path))
        return os.path.isfile(path)

    elif url.scheme == 'ftp':
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(url.scheme)
    else:
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(url.scheme)


def GetDriveType(path):
    '''
    Determine the type of drive, which can be one of the following values:
        DRIVE_UNKNOWN = 0
            The drive type cannot be determined.

        DRIVE_NO_ROOT_DIR = 1
            The root path is invalid; for example, there is no volume mounted at the specified path.

        DRIVE_REMOVABLE = 2
            The drive has removable media; for example, a floppy drive, thumb drive, or flash card reader.

        DRIVE_FIXED = 3
            The drive has fixed media; for example, a hard disk drive or flash drive.

        DRIVE_REMOTE = 4
            The drive is a remote (network) drive.

        DRIVE_CDROM = 5
            The drive is a CD-ROM drive.

        DRIVE_RAMDISK = 6
            The drive is a RAM disk

    :note:
        The implementation is valid only for Windows OS
        Linux will always return DRIVE_UNKNOWN

    :param path:
        Path to a file or directory
    '''
    if sys.platform == 'win32':
        import ctypes
        kdll = ctypes.windll.LoadLibrary("kernel32.dll")

        return kdll.GetDriveType(path + '\\')

        import win32file
        if IsFile(path):
            path = os.path.dirname(path)

        # A trailing backslash is required.
        return win32file.GetDriveType(path + '\\')

    else:
        return DRIVE_UNKNOWN




#===================================================================================================
# IsDir
#===================================================================================================
def IsDir(directory):
    '''
    :param unicode directory:
        A path

    :rtype: bool
    :returns:
        Returns whether the given path points to an existent directory.

    :raises NotImplementedProtocol:
        If the path protocol is not local or ftp

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from six.moves.urllib.parse import urlparse
    directory_url = urlparse(directory)

    if _UrlIsLocal(directory_url):
        return os.path.isdir(directory)
    elif directory_url.scheme == 'ftp':
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(target_url.scheme)
    else:
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)



#===================================================================================================
# Exists
#===================================================================================================
def Exists(path):
    '''
    :rtype: bool
    :returns:
        True if the path already exists (either a file or a directory)

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from six.moves.urllib.parse import urlparse
    path_url = urlparse(path)

    # Handle local
    if _UrlIsLocal(path_url):
        return IsFile(path) or IsDir(path) or IsLink(path)
    return IsFile(path) or IsDir(path)



#===================================================================================================
# CopyDirectory
#===================================================================================================
def CopyDirectory(source_dir, target_dir, override=False):
    '''
    Recursively copy a directory tree.

    :param unicode source_dir:
        Where files will come from

    :param unicode target_dir:
        Where files will go to

    :param bool override:
        If True and target_dir already exists, it will be deleted before copying.

    :raises NotImplementedForRemotePathError:
        If trying to copy to/from remote directories
    '''
    _AssertIsLocal(source_dir)
    _AssertIsLocal(target_dir)

    if override and IsDir(target_dir):
        DeleteDirectory(target_dir, skip_on_error=False)

    import shutil
    shutil.copytree(source_dir, target_dir)



#===================================================================================================
# DeleteFile
#===================================================================================================
def DeleteFile(target_filename):
    '''
    Deletes the given local filename.

    .. note:: If file doesn't exist this method has no effect.

    :param unicode target_filename:
        A local filename

    :raises NotImplementedForRemotePathError:
        If trying to delete a non-local path

    :raises FileOnlyActionError:
        Raised when filename refers to a directory.
    '''
    _AssertIsLocal(target_filename)

    try:
        if IsLink(target_filename):
            DeleteLink(target_filename)
        elif IsFile(target_filename):
            os.remove(target_filename)
        elif IsDir(target_filename):
            from ._exceptions import FileOnlyActionError
            raise FileOnlyActionError(target_filename)
    except Exception as e:
        raise(e, 'While executing filesystem.DeleteFile(%s)' % (target_filename))



#===================================================================================================
# AppendToFile
#===================================================================================================
def AppendToFile(filename, contents, eol_style=EOL_STYLE_NATIVE, encoding=None, binary=False):
    '''
    Appends content to a local file.

    :param unicode filename:

    :param unicode contents:

    :type eol_style: EOL_STYLE_XXX constant
    :param eol_style:
        Replaces the EOL by the appropriate EOL depending on the eol_style value.
        Considers that all content is using only "\n" as EOL.

    :param unicode encoding:
        Target file's content encoding.
        Defaults to sys.getfilesystemencoding()

    :param bool binary:
        If True, content is appended in binary mode. In this case, `contents` must be `bytes` and not
        `unicode`

    :raises NotImplementedForRemotePathError:
        If trying to modify a non-local path

    :raises ValueError:
        If trying to mix unicode `contents` without `encoding`, or `encoding` without
        unicode `contents`
    '''
    _AssertIsLocal(filename)

    assert isinstance(contents, six.text_type) ^ binary, 'Must always receive unicode contents, unless binary=True'

    if not binary:
        # Replaces eol on each line by the given eol_style.
        contents = _HandleContentsEol(contents, eol_style)

        # Handle encoding here, and always write in binary mode. We can't use io.open because it
        # tries to do its own line ending handling.
        contents = contents.encode(encoding or sys.getfilesystemencoding())

    oss = open(filename, 'ab')
    try:
        oss.write(contents)
    finally:
        oss.close()



#===================================================================================================
# MoveFile
#===================================================================================================
def MoveFile(source_filename, target_filename):
    '''
    Moves a file.

    :param unicode source_filename:

    :param unicode target_filename:

    :raises NotImplementedForRemotePathError:
        If trying to operate with non-local files.
    '''
    _AssertIsLocal(source_filename)
    _AssertIsLocal(target_filename)

    import shutil
    shutil.move(source_filename, target_filename)



#===================================================================================================
# MoveDirectory
#===================================================================================================
def MoveDirectory(source_dir, target_dir):
    '''
    Moves a directory.

    :param unicode source_dir:

    :param unicode target_dir:

    :raises NotImplementedError:
        If trying to move anything other than:
            Local dir -> local dir
            FTP dir -> FTP dir (same host)
    '''
    if not IsDir(source_dir):
        from ._exceptions import DirectoryNotFoundError
        raise DirectoryNotFoundError(source_dir)

    if Exists(target_dir):
        from ._exceptions import DirectoryAlreadyExistsError
        raise DirectoryAlreadyExistsError(target_dir)

    from six.moves.urllib.parse import urlparse
    source_url = urlparse(source_dir)
    target_url = urlparse(target_dir)

    # Local to local
    if _UrlIsLocal(source_url) and _UrlIsLocal(target_url):
        import shutil
        shutil.move(source_dir, target_dir)

    # FTP to FTP
    elif source_url.scheme == 'ftp' and target_url.scheme == 'ftp':
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(target_url.scheme)
    else:
        raise NotImplementedError('Can only move directories local->local or ftp->ftp')


#===================================================================================================
# GetFileContents
#===================================================================================================
def GetFileContents(filename, binary=False, encoding=None, newline=None):
    '''
    Reads a file and returns its contents. Works for both local and remote files.

    :param unicode filename:

    :param bool binary:
        If True returns the file as is, ignore any EOL conversion.

    :param unicode encoding:
        File's encoding. If not None, contents obtained from file will be decoded using this
        `encoding`.

    :param None|''|'\n'|'\r'|'\r\n' newline:
        Controls universal newlines.
        See 'io.open' newline parameter documentation for more details.

    :returns str|unicode:
        The file's contents.
        Returns unicode string when `encoding` is not None.

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    source_file = OpenFile(filename, binary=binary, encoding=encoding, newline=newline)
    try:
        contents = source_file.read()
    finally:
        source_file.close()

    return contents


#===================================================================================================
# GetFileLines
#===================================================================================================
def GetFileLines(filename, newline=None, encoding=None):
    '''
    Reads a file and returns its contents as a list of lines. Works for both local and remote files.

    :param unicode filename:

    :param None|''|'\n'|'\r'|'\r\n' newline:
        Controls universal newlines.
        See 'io.open' newline parameter documentation for more details.

    :param unicode encoding:
        File's encoding. If not None, contents obtained from file will be decoded using this
        `encoding`.

    :returns list(unicode):
        The file's lines

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    return GetFileContents(
        filename,
        binary=False,
        encoding=encoding,
        newline=newline,
    ).split('\n')


def OpenFile(filename, binary=False, newline=None, encoding=None):
    '''
    Open a file and returns it.
    Consider the possibility of a remote file (HTTP, HTTPS, FTP)

    :param unicode filename:
        Local or remote filename.

    :param bool binary:
        If True returns the file as is, ignore any EOL conversion.
        If set ignores univeral_newlines parameter.

    :param None|''|'\n'|'\r'|'\r\n' newline:
        Controls universal newlines.
        See 'io.open' newline parameter documentation for more details.

    :param unicode encoding:
        File's encoding. If not None, contents obtained from file will be decoded using this
        `encoding`.

    :returns file:
        The open file, it must be closed by the caller

    @raise: FileNotFoundError
        When the given filename cannot be found

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from six.moves.urllib.parse import urlparse
    filename_url = urlparse(filename)

    # Check if file is local
    if _UrlIsLocal(filename_url):
        if not os.path.isfile(filename):
            from ._exceptions import FileNotFoundError
            raise FileNotFoundError(filename)

        mode = 'rb' if binary else 'r'
        return io.open(filename, mode, encoding=encoding, newline=newline)

    # Not local
    from ._exceptions import NotImplementedProtocol
    raise NotImplementedProtocol(target_url.scheme)



#===================================================================================================
# ListFiles
#===================================================================================================
def ListFiles(directory):
    '''
    Lists the files in the given directory

    :type directory: unicode | unicode
    :param directory:
        A directory or URL

    :rtype: list(unicode) | list(unicode)
    :returns:
        List of filenames/directories found in the given directory.
        Returns None if the given directory does not exists.

        If `directory` is a unicode string, all files returned will also be unicode

    :raises NotImplementedProtocol:
        If file protocol is not local or FTP

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from six.moves.urllib.parse import urlparse
    directory_url = urlparse(directory)

    # Handle local
    if _UrlIsLocal(directory_url):
        if not os.path.isdir(directory):
            return None
        return os.listdir(directory)

    # Handle FTP
    elif directory_url.scheme == 'ftp':
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)
    else:
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)



#===================================================================================================
# CheckIsFile
#===================================================================================================
def CheckIsFile(filename):
    '''
    Check if the given file exists.

    @filename: unicode
        The filename to check for existence.

    @raise: FileNotFoundError
        Raises if the file does not exist.
    '''
    if not IsFile(filename):
        from ._exceptions import FileNotFoundError
        raise FileNotFoundError(filename)



#===================================================================================================
# CheckIsDir
#===================================================================================================
def CheckIsDir(directory):
    '''
    Check if the given directory exists.

    @filename: unicode
        Path to a directory being checked for existence.

    @raise: DirectoryNotFoundError
        Raises if the directory does not exist.
    '''
    if not IsDir(directory):
        from ._exceptions import DirectoryNotFoundError
        raise DirectoryNotFoundError(directory)



#===================================================================================================
# CreateFile
#===================================================================================================
def CreateFile(filename, contents, eol_style=EOL_STYLE_NATIVE, create_dir=True, encoding=None, binary=False):
    '''
    Create a file with the given contents.

    :param unicode filename:
        Filename and path to be created.

    :param unicode contents:
        The file contents as a string.

    :type eol_style: EOL_STYLE_XXX constant
    :param eol_style:
        Replaces the EOL by the appropriate EOL depending on the eol_style value.
        Considers that all content is using only "\n" as EOL.

    :param bool create_dir:
        If True, also creates directories needed in filename's path

    :param unicode encoding:
        Target file's content encoding. Defaults to sys.getfilesystemencoding()
        Ignored if `binary` = True

    :param bool binary:
        If True, file is created in binary mode. In this case, `contents` must be `bytes` and not
        `unicode`

    :return unicode:
        Returns the name of the file created.

    :raises NotImplementedProtocol:
        If file protocol is not local or FTP

    :raises ValueError:
        If trying to mix unicode `contents` without `encoding`, or `encoding` without
        unicode `contents`

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    # Lots of checks when writing binary files
    if binary:
        if isinstance(contents, six.text_type):
            raise TypeError('contents must be str (bytes) when binary=True')
    else:
        if not isinstance(contents, six.text_type):
            raise TypeError('contents must be unicode when binary=False')

        # Replaces eol on each line by the given eol_style.
        contents = _HandleContentsEol(contents, eol_style)

        # Encode string and pretend we are using binary to prevent 'open' from automatically
        # changing Eols
        encoding = encoding or sys.getfilesystemencoding()
        contents = contents.encode(encoding)
        binary = True

    # If asked, creates directory containing file
    if create_dir:
        dirname = os.path.dirname(filename)
        if dirname:
            CreateDirectory(dirname)

    from six.moves.urllib.parse import urlparse
    filename_url = urlparse(filename)

    # Handle local
    if _UrlIsLocal(filename_url):
        # Always writing as binary (see handling above)
        with open(filename, 'wb') as oss:
            oss.write(contents)

    # Handle FTP
    elif filename_url.scheme == 'ftp':
        # Always writing as binary (see handling above)
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)
    else:
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(filename_url.scheme)

    return filename



def ReplaceInFile(filename, old, new, encoding=None):
    '''
    Replaces all occurrences of "old" by "new" in the given file.

    :param unicode filename:
        The name of the file.

    :param unicode old:
        The string to search for.

    :param unicode new:
        Replacement string.

    :return unicode:
        The new contents of the file.
    '''
    contents = GetFileContents(filename, encoding=encoding)
    contents = contents.replace(old, new)
    CreateFile(filename, contents, encoding=encoding)
    return contents



#===================================================================================================
# CreateDirectory
#===================================================================================================
def CreateDirectory(directory):
    '''
    Create directory including any missing intermediate directory.

    :param unicode directory:

    :return unicode|urlparse.ParseResult:
        Returns the created directory or url (see urlparse).

    :raises NotImplementedProtocol:
        If protocol is not local or FTP.

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from six.moves.urllib.parse import urlparse
    directory_url = urlparse(directory)

    # Handle local
    if _UrlIsLocal(directory_url):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    # Handle FTP
    elif directory_url.scheme == 'ftp':
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)
    else:
        from ._exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)



#===================================================================================================
# CreateTemporaryDirectory
#===================================================================================================
class CreateTemporaryDirectory(object):
    '''
    Context manager to create a temporary file and remove if at the context end.

    :ivar unicode dirname:
        Name of the created directory
    '''
    def __init__(self, suffix='', prefix='tmp', base_dir=None, maximum_attempts=100):
        '''
        :param unicode suffix:
            A suffix to add in the name of the created directory

        :param unicode prefix:
            A prefix to add in the name of the created directory

        :param unicode base_dir:
            A path to use as base in the created directory (if any). The temp directory will be a
            child of the given base dir

        :param int maximum_attemps:
            The maximum number of attempts to obtain the temp dir name.

        '''
        self.suffix = suffix
        self.prefix = prefix
        self.base_dir = base_dir
        self.maximum_attempts = maximum_attempts

        self.dirname = None


    def __enter__(self):
        '''
        :return unicode:
            The path to the created temp file.
        '''
        if self.base_dir is None:
            # If no base directoy was given, let us create a dir in system temp area
            import tempfile
            self.dirname = tempfile.mkdtemp(self.suffix, self.prefix)
            return self.dirname


        # Listing the files found in the base dir
        existing_files = set(ListFiles(self.base_dir))

        # If a base dir was given, let us generate a unique directory name there and use it
        for random_component in IterHashes(iterator_size=self.maximum_attempts):
            candidate_name = '%stemp_dir_%s%s' % (self.prefix, random_component, self.suffix)
            candidate_path = os.path.join(self.base_dir, candidate_name)
            if candidate_path not in existing_files:
                CreateDirectory(candidate_path)
                self.dirname = candidate_path
                return self.dirname

        raise RuntimeError(
            'It was not possible to obtain a temporary dirname from %s' % self.base_dir)


    def __exit__(self, *args):
        if self.dirname is not None:
            DeleteDirectory(self.dirname, skip_on_error=True)



#===================================================================================================
# CreateTemporaryFile
#===================================================================================================
class CreateTemporaryFile(object):
    '''
    Context manager to create a temporary file and remove if at the context end.

    :ivar unicode filename:
        Name of the created file
    '''
    def __init__(
        self,
        contents,
        eol_style=EOL_STYLE_NATIVE,
        encoding=None,
        suffix='',
        prefix='tmp',
        base_dir=None,
        maximum_attempts=100):
        '''
        :param contents: .. seealso:: CreateFile
        :param eol_style: .. seealso:: CreateFile
        :param encoding: .. seealso:: CreateFile

        :param unicode suffix:
            A suffix to add in the name of the created file

        :param unicode prefix:
            A prefix to add in the name of the created file

        :param unicode base_dir:
            A path to use as base in the created file. Uses temp dir if not given.

        :param int maximum_attemps:
            The maximum number of attempts to obtain the temp file name.
        '''

        import tempfile

        self.contents = contents
        self.eol_style = eol_style
        self.encoding = encoding
        self.suffix = suffix
        self.prefix = prefix
        self.base_dir = base_dir or tempfile.gettempdir()
        self.maximum_attempts = maximum_attempts

        self.filename = None


    def __enter__(self):
        '''
        :return unicode:
            The path to the created temp file.
        '''
        from ._exceptions import FileAlreadyExistsError

        for random_component in IterHashes(iterator_size=self.maximum_attempts):
            filename = os.path.join(self.base_dir, self.prefix + random_component + self.suffix)

            try:
                CreateFile(
                    filename=filename,
                    contents=self.contents,
                    eol_style=self.eol_style,
                    encoding=self.encoding,
                )
                self.filename = filename
                return filename

            except FileAlreadyExistsError:
                pass

        raise RuntimeError('It was not possible to obtain a temporary filename in "%s"' % self.base_dir)


    def __exit__(self, *args):
        if self.filename is not None:
            DeleteFile(self.filename)



#===================================================================================================
# DeleteDirectory
#===================================================================================================
def DeleteDirectory(directory, skip_on_error=False):
    '''
    Deletes a directory.

    :param unicode directory:

    :param bool skip_on_error:
        If True, ignore any errors when trying to delete directory (for example, directory not
        found)

    :raises NotImplementedForRemotePathError:
        If trying to delete a remote directory.
    '''
    _AssertIsLocal(directory)

    import shutil
    def OnError(fn, path, excinfo):
        '''
        Remove the read-only flag and try to remove again.
        On Windows, rmtree fails when trying to remove a read-only file. This fix it!
        Another case: Read-only directories return True in os.access test. It seems that read-only
        directories has it own flag (looking at the property windows on Explorer).
        '''
        if IsLink(path):
            return

        if fn is os.remove and os.access(path, os.W_OK):
            raise

        # Make the file WRITEABLE and executes the original delete function (osfunc)
        import stat
        os.chmod(path, stat.S_IWRITE)
        fn(path)

    try:
        if not os.path.isdir(directory):
            if skip_on_error:
                return
            from ._exceptions import DirectoryNotFoundError
            raise DirectoryNotFoundError(directory)
        shutil.rmtree(directory, onerror=OnError)
    except:
        if not skip_on_error:
            raise  # Raise only if we are not skipping on error



#===================================================================================================
# GetMTime
#===================================================================================================
def GetMTime(path):
    '''
    :param unicode path:
        Path to file or directory

    :rtype: float
    :returns:
        Modification time for path.

        If this is a directory, the highest mtime from files inside it will be returned.

    @note:
        In some Linux distros (such as CentOs, or anything with ext3), mtime will not return a value
        with resolutions higher than a second.

        http://stackoverflow.com/questions/2428556/os-path-getmtime-doesnt-return-fraction-of-a-second
    '''
    _AssertIsLocal(path)

    if os.path.isdir(path):
        files = FindFiles(path)

        if len(files) > 0:
            return max(map(os.path.getmtime, files))

    return os.path.getmtime(path)



#===================================================================================================
# ListMappedNetworkDrives
#===================================================================================================
def ListMappedNetworkDrives():
    '''
    On Windows, returns a list of mapped network drives

    :return: tuple(string, string, bool)
        For each mapped netword drive, return 3 values tuple:
            - the local drive
            - the remote path-
            - True if the mapping is enabled (warning: not reliable)
    '''
    if sys.platform != 'win32':
        raise NotImplementedError
    drives_list = []
    netuse = _CallWindowsNetCommand(['use'])
    for line in netuse.split(EOL_STYLE_WINDOWS):
        match = re.match("(\w*)\s+(\w:)\s+(.+)", line.rstrip())
        if match:
            drives_list.append((match.group(2), match.group(3), match.group(1) == 'OK'))
    return drives_list



#===================================================================================================
# DeleteLink
#===================================================================================================
def DeleteLink(path):
    if sys.platform != 'win32':
        os.unlink(path)
    else:
        from ._easyfs_win32 import RemoveDirectory as _RemoveDirectory, DeleteFile as _DeleteFile
        if IsDir(path):
            _RemoveDirectory(path)
        else:
            _DeleteFile(path)



#===================================================================================================
# CreateLink
#===================================================================================================
def CreateLink(target_path, link_path, override=True):
    '''
    Create a symbolic link at `link_path` pointing to `target_path`.

    :param unicode target_path:
        Link target

    :param unicode link_path:
        Fullpath to link name

    :param bool override:
        If True and `link_path` already exists as a link, that link is overridden.
    '''
    _AssertIsLocal(target_path)
    _AssertIsLocal(link_path)

    if override and IsLink(link_path):
        DeleteLink(link_path)

    # Create directories leading up to link
    dirname = os.path.dirname(link_path)
    if dirname:
        CreateDirectory(dirname)

    if sys.platform != 'win32':
        return os.symlink(target_path, link_path)  # @UndefinedVariable
    else:
        #import ntfsutils.junction
        #return ntfsutils.junction.create(target_path, link_path)

        import jaraco.windows.filesystem
        return jaraco.windows.filesystem.symlink(target_path, link_path)

        from ._easyfs_win32 import CreateSymbolicLink
        try:
            dw_flags = 0
            if target_path and os.path.isdir(target_path):
                dw_flags = 1
            return CreateSymbolicLink(target_path, link_path, dw_flags)
        except Exception as e:
            raise(e, 'Creating link "%(link_path)s" pointing to "%(target_path)s"' % locals())



#===================================================================================================
# IsLink
#===================================================================================================
def IsLink(path):
    '''
    :param unicode path:
        Path being tested

    :returns bool:
        True if `path` is a link
    '''
    _AssertIsLocal(path)

    if sys.platform != 'win32':
        return os.path.islink(path)

    import jaraco.windows.filesystem
    return jaraco.windows.filesystem.islink(path)



#===================================================================================================
# ReadLink
#===================================================================================================
def ReadLink(path):
    '''
    Read the target of the symbolic link at `path`.

    :param unicode path:
        Path to a symbolic link

    :returns unicode:
        Target of a symbolic link
    '''
    _AssertIsLocal(path)

    if sys.platform != 'win32':
        return os.readlink(path)  # @UndefinedVariable

    if not IsLink(path):
        from ._exceptions import FileNotFoundError
        raise FileNotFoundError(path)

    import jaraco.windows.filesystem
    result = jaraco.windows.filesystem.readlink(path)
    if '\\??\\' in result:
        result = result.split('\\??\\')[1]
    return result


#===================================================================================================
# Internal functions
#===================================================================================================
def _UrlIsLocal(directory_url):
    '''
    :param ParseResult directory_url:
        A parsed url as returned by urlparse.urlparse.

    :rtype: bool
    :returns:
        Returns whether the given url refers to a local path.

    .. note:: The "directory_url.scheme" is the drive letter for a local path on Windows and an empty string
    for a local path on Linux. The other possible values are "http", "ftp", etc. So, checking if
    the length is less than 2 characters long checks that the url is local.
    '''
    return len(directory_url.scheme) < 2


def _AssertIsLocal(path):
    '''
    Checks if a given path is local, raise an exception if not.

    This is used in filesystem functions that do not support remote operations yet.

    :param unicode path:

    :raises NotImplementedForRemotePathError:
        If the given path is not local
    '''
    from six.moves.urllib.parse import urlparse
    if not _UrlIsLocal(urlparse(path)):
        from ._exceptions import NotImplementedForRemotePathError
        raise NotImplementedForRemotePathError


def _HandleContentsEol(contents, eol_style):
    '''
    Replaces eol on each line by the given eol_style.

    :param unicode contents:
    :type eol_style: EOL_STYLE_XXX constant
    :param eol_style:
    '''
    if eol_style == EOL_STYLE_NONE:
        return contents

    if eol_style == EOL_STYLE_UNIX:
        return contents.replace('\r\n', eol_style).replace('\r', eol_style)

    if eol_style == EOL_STYLE_MAC:
        return contents.replace('\r\n', eol_style).replace('\n', eol_style)

    if eol_style == EOL_STYLE_WINDOWS:
        return contents.replace('\r\n', '\n').replace('\r', '\n').replace('\n', EOL_STYLE_WINDOWS)

    raise ValueError('Unexpected eol style: %r' % (eol_style,))


def _CallWindowsNetCommand(parameters):
    '''
    Call Windows NET command, used to acquire/configure network services settings.

    :param parameters: list of command line parameters

    :return: command output
    '''
    import subprocess
    popen = subprocess.Popen(["net"] + parameters, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = popen.communicate()
    if stderrdata:
        raise OSError("Failed on call net.exe: %s" % stderrdata)
    return stdoutdata



#===================================================================================================
# ExtendedPathMask
#===================================================================================================
class ExtendedPathMask(object):
    '''
    This class is a place-holder for functions that handle the extended path mask.

    Extended Path Mask
    ------------------

    The extended path mask is a file search path description used to find files based on the filename.
    This extended path mask includes the following features:
        - Recursive search (prefix with a "+" sign)
        - The possibility of adding more than one filter to match files (separated by ";")
        - The possibility of negate an mask (prefix the mask with "!").

    The extended path mask has the following syntax:

        [+|-]<path>/<filter>(;<filter>)*

    Where:
        + : recursive and copy-tree flag
        - : recursive and copy-flat flag (copy files to the target directory with no tree structure)
        <path> : a usual path, using '/' as separator
        <filter> : A filename filter, as used in dir command:
            Ex:
                *.zip;*.rar
                units.txt;*.ini
                *.txt;!*-002.txt
    '''


    @classmethod
    def Split(cls, extended_path_mask):
        '''
        Splits the given path into their components: recursive, dirname, in_filters and out_filters

        :param str: extended_path_mask:
            The "extended path mask" to split

        :rtype: tuple(bool,bool,str,list(str),list(str))
        :returns:
            Returns the extended path 5 components:
            - The tree-recurse flag
            - The flat-recurse flag
            - The actual path
            - A list of masks to include
            - A list of masks to exclude
        '''
        import os.path
        r_tree_recurse = extended_path_mask[0] in '+-'
        r_flat_recurse = extended_path_mask[0] in '-'

        r_dirname, r_filters = os.path.split(extended_path_mask)
        if r_tree_recurse:
            r_dirname = r_dirname[1:]

        filters = r_filters.split(';')
        r_in_filters = [i for i in filters if not i.startswith('!')]
        r_out_filters = [i[1:] for i in filters if i.startswith('!')]

        return r_tree_recurse, r_flat_recurse, r_dirname, r_in_filters, r_out_filters



#===================================================================================================
# CheckForUpdate
#===================================================================================================
def CheckForUpdate(source, target):
    '''
    Checks if the given target filename should be re-generated because the source has changed.
    :param source: the source filename.
    :param target: the target filename.
    :return bool:
        True if the target is out-dated, False otherwise.
    '''
    return \
        not os.path.isfile(target) or \
        os.path.getmtime(source) > os.path.getmtime(target)



#===================================================================================================
# MatchMasks
#===================================================================================================
def MatchMasks(filename, masks):
    '''
    Verifies if a filename match with given patterns.

    :param str filename: The filename to match.
    :param list(str) masks: The patterns to search in the filename.
    :return bool:
        True if the filename has matched with one pattern, False otherwise.
    '''
    import fnmatch

    if not isinstance(masks, (list, tuple)):
        masks = [masks]

    for i_mask in masks:
        if fnmatch.fnmatch(filename, i_mask):
            return True
    return False



#===================================================================================================
# FindFiles
#===================================================================================================
def FindFiles(dir_, in_filters=None, out_filters=None, recursive=True, include_root_dir=True, standard_paths=False):
    '''
    Searches for files in a given directory that match with the given patterns.

    :param str dir_: the directory root, to search the files.
    :param list(str) in_filters: a list with patterns to match (default = all). E.g.: ['*.py']
    :param list(str) out_filters: a list with patterns to ignore (default = none). E.g.: ['*.py']
    :param bool recursive: if True search in subdirectories, otherwise, just in the root.
    :param bool include_root_dir: if True, includes the directory being searched in the returned paths
    :param bool standard_paths: if True, always uses unix path separators "/"
    :return list(str):
        A list of strings with the files that matched (with the full path in the filesystem).
    '''
    # all files
    if in_filters is None:
        in_filters = ['*']

    if out_filters is None:
        out_filters = []

    result = []

    # maintain just files that don't have a pattern that match with out_filters
    # walk through all directories based on dir
    for dir_root, directories, filenames in os.walk(dir_):

        for i_directory in directories[:]:
            if MatchMasks(i_directory, out_filters):
                directories.remove(i_directory)

        for filename in directories + filenames:
            if MatchMasks(filename, in_filters) and not MatchMasks(filename, out_filters):
                result.append(os.path.join(dir_root, filename))

        if not recursive:
            break

    if not include_root_dir:
        # Remove root dir from all paths
        dir_prefix = len(dir_) + 1
        result = [file[dir_prefix:] for file in result]

    if standard_paths:
        result = map(StandardizePath, result)

    return result



#===================================================================================================
# ExpandUser
#===================================================================================================
def ExpandUser(path):
    '''
    os.path.expanduser wrapper, necessary because it cannot handle unicode strings properly.

    This is not necessary in Python 3.

    :param path:
        .. seealso:: os.path.expanduser
    '''
    if six.PY2:
        encoding = sys.getfilesystemencoding()
        path = path.encode(encoding)
    result = os.path.expanduser(path)
    if six.PY2:
        result = result.decode(encoding)
    return result



#===================================================================================================
# DumpDirHashToStringIO
#===================================================================================================
def DumpDirHashToStringIO(directory, stringio, base='', exclude=None, include=None):
    '''
    Helper to iterate over the files in a directory putting those in the passed StringIO in ini
    format.

    :param unicode directory:
        The directory for which the hash should be done.

    :param StringIO stringio:
        The string to which the dump should be put.

    :param unicode base:
        If provided should be added (along with a '/') before the name=hash of file.

    :param unicode exclude:
        Pattern to match files to exclude from the hashing. E.g.: *.gz

    :param unicode include:
        Pattern to match files to include in the hashing. E.g.: *.zip
    '''
    import fnmatch
    import os

    files = [(os.path.join(directory, i), i) for i in os.listdir(directory)]
    files = [i for i in files if os.path.isfile(i[0])]
    for fullname, filename in files:
        if include is not None:
            if not fnmatch.fnmatch(fullname, include):
                continue

        if exclude is not None:
            if fnmatch.fnmatch(fullname, exclude):
                continue

        md5 = Md5Hex(fullname)
        if base:
            stringio.write('%s/%s=%s\n' % (base, filename, md5))
        else:
            stringio.write('%s=%s\n' % (filename, md5))



#===================================================================================================
# Md5Hex
#===================================================================================================
def Md5Hex(filename=None, contents=None):
    '''
    :param unicode filename:
        The file from which the md5 should be calculated. If the filename is given, the contents
        should NOT be given.

    :param unicode contents:
        The contents for which the md5 should be calculated. If the contents are given, the filename
        should NOT be given.

    :rtype: unicode
    :returns:
        Returns a string with the hex digest of the stream.
    '''
    import io
    import hashlib
    md5 = hashlib.md5()

    if filename:
        stream = io.open(filename, 'rb')
        try:
            while True:
                data = stream.read(md5.block_size * 128)
                if not data:
                    break
                md5.update(data)
        finally:
            stream.close()

    else:
        md5.update(contents)

    return six.text_type(md5.hexdigest())



#===================================================================================================
# GetRandomHash
#===================================================================================================
def GetRandomHash(length=7):
    '''
    :param length:
        Length of hash returned.

    :return unicode:
        A random hexadecimal hash of the given length
    '''
    import random
    return ('%0' + six.text_type(length) + 'x') % random.randrange(16 ** length)



#===================================================================================================
# IterHashes
#===================================================================================================
def IterHashes(iterator_size, hash_length=7):
    '''
    Iterator for random hexadecimal hashes

    :param iterator_size:
        Amount of hashes return before this iterator stops.
        Goes on forever if `iterator_size` is negative.

    :param int hash_length:
        Size of each hash returned.

    :return generator(unicode):
    '''
    if not isinstance(iterator_size, int):
        raise TypeError('iterator_size must be integer.')

    count = 0
    while count != iterator_size:
        count += 1
        yield GetRandomHash(hash_length)


#===================================================================================================
# PushPopItem
#===================================================================================================
@contextlib.contextmanager
def PushPopItem(obj, key, value):
    '''
    A context manager to replace and restore a value using a getter and setter.

    :param object obj: The object to replace/restore.
    :param object key: The key to replace/restore in the object.
    :param object value: The value to replace.

    Example::

      with PushPop2(sys.modules, 'alpha', None):
        pytest.raises(ImportError):
          import alpha
    '''
    if key in obj:
        old_value = obj[key]
        obj[key] = value
        yield value
        obj[key] = old_value

    else:
        obj[key] = value
        yield value
        del obj[key]



# class Kernel(object):
#
#     @classmethod
#     def get_file_attributes(cls, path):
#         import ctypes
#         func = ctypes.windll.kernel32.GetFileAttributesW
#         func.argtypes = [ctypes.c_wchar_p]
#         func.restype = ctypes.wintypes.DWORD
#         return func(path)
#
#     @classmethod
#     def create_file(cls, path):
#         import win32file
#         import winioctlcon
#
#         handle = win32file.CreateFile(
#             path,  # fileName
#             win32file.GENERIC_READ,  # desiredAccess
#             0,  # shareMode
#             None,  # attributes
#             win32file.OPEN_EXISTING,  # creationDisposition
#             win32file.FILE_FLAG_OPEN_REPARSE_POINT | win32file.FILE_FLAG_BACKUP_SEMANTICS,  # flagsAndAttributes
#             None  # hTemplateFile
#         )
#
#     def create_file(cls, path):
#         import ctypes
#         func = ctypes.windll.kernel32.GetFileAttributesW
#         func.argtypes = [ctypes.c_wchar_p]
#         func.restype = ctypes.wintypes.DWORD
#         return func(path)
#
#         try:
#             buf = win32file.DeviceIoControl(
#                 handle,  # hFile
#                 winioctlcon.FSCTL_GET_REPARSE_POINT,  # dwIoControlCode
#                 None,  # data
#                 1024,  # readSize
#             )
#             buf = buf[20::2].encode(sys.getfilesystemencoding(), errors='replace')
#             if '\\??\\' in buf:
#                 return StandardizePath(buf.split('\\??\\')[0])
#             else:
#                 return StandardizePath(buf[:len(buf) / 2])
#         finally:
#             handle.Close()
