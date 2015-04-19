from libcpp cimport bool
from libcpp.string cimport string
from cython.operator cimport dereference as deref, preincrement as incr

def getArticles(filename not None):
    """
    Given a path to a ZIM archive, return an iterator that iterates
    over all articles in the archive (instances of the Article class).
    """
    cdef _File *f = new _File(filename)
    cdef _FileIterator it = f.begin()
    while it != f.end():
        a = Article.create(deref(it))
        if a: yield a
        it = incr(it)

    del f

cdef class Article:
    """
    Represents one article.
    """

    cdef public object title
    """
    the article's title
    """

    cdef public object url
    """
    the article's URL
    """

    cdef public object longUrl
    """
    the article's long URL
    """

    cdef public object ns
    """
    the article's namespace
    """

    cdef public object redirect
    """
    the title of the target article, if this article is redirected;
    None otherwise
    """

    cdef public object linktarget
    """
    True if this article doesn't exist, but some other article links
    to it
    """

    cdef public object text
    """
    the contents of the article, if applicable; otherwise, an empty
    string
    """

    def __init__(self):
        self.linktarget = False
        self.text = ""

    @staticmethod
    cdef create(_Article _a):
        if _a.isDeleted(): return None

        a = Article()
        a.title = _a.getTitle()
        a.url = _a.getUrl()
        a.longUrl = _a.getLongUrl()
        a.ns = chr(_a.getNamespace())

        cdef _Blob data = _a.getData()
        if _a.isRedirect():
            a.redirect = _a.getRedirectArticle().getTitle()
        elif _a.isLinktarget():
            a.linktarget = True
        else:
            a.text = data.data()[:data.size()]

        return a


cdef extern from "<zim/file.h>":
    cdef cppclass _File "zim::File":
        _File(string) except +
        _FileIterator begin() except +
        _FileIterator end() except +

    bool operator==(const _FileIterator&, const _FileIterator&) except +
    bool operator!=(const _FileIterator&, const _FileIterator&) except +

cdef extern from "<zim/fileiterator.h>":
    cdef cppclass _FileIterator "zim::File::const_iterator":
        _FileIterator operator++() except +
        _Article operator*() except +

cdef extern from "<zim/article.h>":
    cdef cppclass _Article "zim::Article":
        string getTitle() except +
        string getUrl() except +
        string getLongUrl() except +
        bool isRedirect() except +
        bool isLinktarget() except +
        bool isDeleted() except +
        char getNamespace() except +
        _Article getRedirectArticle() except +
        _Blob getData() except +

cdef extern from "<zim/blob.h>":
    cdef cppclass _Blob "zim::Blob":
        const char* data()
        const char* end()
        unsigned size()
