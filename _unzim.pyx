from libcpp cimport bool
from libcpp.string cimport string
from cython.operator cimport dereference as deref, preincrement as incr


cdef extern from "<zim/file.h>":
    cdef cppclass _File "zim::File":
        _File(string) except +
        _FileIterator begin() except +
        _FileIterator end() except +
        _Blob getBlob(size_t clusterIdx, size_t blobIdx) except +

    bool operator==(const _FileIterator&, const _FileIterator&) except +
    bool operator!=(const _FileIterator&, const _FileIterator&) except +

cdef extern from "<zim/fileiterator.h>":
    cdef cppclass _FileIterator "zim::File::const_iterator":
        _FileIterator operator++() except +
        _Article operator*() except +

cdef extern from "<zim/article.h>":
    cdef cppclass _Article "zim::Article":
        size_t getIndex()
        string getTitle() except +
        string getUrl() except +
        string getLongUrl() except +
        bool isRedirect() except +
        bool isLinktarget() except +
        bool isDeleted() except +
        char getNamespace() except +
        _Article getRedirectArticle() except +
        size_t getRedirectIndex() except+
        _Dirent getDirent() except +
        _Blob getData() except +

cdef extern from "<zim/dirent.h>":
    cdef cppclass _Dirent "zim::Dirent":
        size_t getClusterNumber()
        size_t getBlobNumber()

cdef extern from "<zim/blob.h>":
    cdef cppclass _Blob "zim::Blob":
        const char* data()
        const char* end()
        unsigned size()


cdef class File:
    """
    Represents a ZIM file.
    """

    cdef _File *f

    def __init__(self, path):
        self.f = new _File(path)

    def __dealloc__(self):
        del self.f

    def articles(self):
        """
        Return an iterator that iterates over all articles in the archive
        (instances of the Article class).
        """
        cdef _FileIterator it = self.f.begin()
        while it != self.f.end():
            a = Article.create(deref(it))
            if a: yield a
            it = incr(it)

    def blob_data(self, cluster_id, blob_id):
        """
        Return the data of a given blob.
        """
        cdef _Blob data = self.f.getBlob(cluster_id, blob_id)
        return data.data()[:data.size()].decode('utf-8')


cdef class Article:
    """
    Represents one article.
    """

    cdef _Article a

    @property
    def index(self):
        """
        the article's index
        """
        return self.a.getIndex()

    @property
    def title(self):
        """
        the article's title
        """
        return self.a.getTitle().decode('utf-8')

    @property
    def url(self):
        """
        the article's URL
        """
        return self.a.getUrl().decode('utf-8')

    @property
    def long_url(self):
        """
        the article's long URL
        """
        return self.a.getLongUrl().decode('utf-8')

    @property
    def ns(self):
        """
        the article's namespace
        """
        return unichr(self.a.getNamespace())

    @property
    def redirect_index(self):
        """
        if the article is redirected, this is the index of the target article;
            None otherwise
        """
        if self.a.isRedirect():
            return self.a.getRedirectIndex()
        return None

    @property
    def linktarget(self):
        """
        True if this article doesn't exist, but some other article links
            to it
        """
        return self.a.isLinktarget()

    @property
    def data(self):
        """
        the contents of the article, if applicable; otherwise, an empty string
        """
        cdef _Blob data = self.a.getData()
        if not self.a.isRedirect() and not self.a.isLinktarget():
            return data.data()[:data.size()].decode('utf-8')
        return u''

    @property
    def cluster_id(self):
        """
        the number of the cluster containing the blob containing the data
        """
        return self.a.getDirent().getClusterNumber()

    @property
    def blob_id(self):
        """
        the number of the blob containing the data
        """
        return self.a.getDirent().getBlobNumber()


    @staticmethod
    cdef create(_Article _a):
        if _a.isDeleted(): return None

        a = Article()
        a.a = _a

        return a
