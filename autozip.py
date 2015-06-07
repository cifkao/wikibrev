import os
import re
import magic
import tempfile
import gzip

class AutoZip(object):
    mime = None
    original_path = None
    _path = None
    _tmpdir = None
    _read_only = True

    def __init__(self, path, tmpdir=None, readonly=False):
        if tmpdir is None: tmpdir = '/tmp'
        self.original_path = path
        self._tmpdir = tmpdir
        self._read_only = readonly
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            self.mime = m.id_filename(path)

    def path(self):
        if self._path is None:
            if 'gzip' in self.mime:
                fname = re.sub('\.gz$', '', os.path.split(self.original_path)[-1])
                (fd_out, self._path) = tempfile.mkstemp(dir=self._tmpdir, suffix='.'+fname)
                try:
                    with os.fdopen(fd_out, 'wb') as f_out:
                        with gzip.open(self.original_path, 'rb') as f_in:
                            f_out.writelines(f_in)
                except:
                    os.remove(self._path)
                    self._path = None
                    raise
            else:
                self._path = self.original_path

        return self._path

    def close(self, commit_changes=True):
        if self._path != self.original_path:
            if commit_changes and not self._read_only:
                if 'gzip' in self.mime:
                    with open(self._path, 'rb') as f_in:
                        with gzip.open(self.original_path, 'wb') as f_out:
                            f_out.writelines(f_in)
            os.remove(self._path)
        self._path = None

    def __enter__(self):
        return self.path()

    def __exit__(self, type, value, traceback):
        self.close(type is None) # if an exception occured, keep the original file
