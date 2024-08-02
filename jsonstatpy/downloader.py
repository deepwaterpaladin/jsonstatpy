import time
import os
import hashlib
import requests
from .exceptions import JsonStatException


class Downloader:
    """Helper class to download json stat files.

    It has a very simple cache mechanism
    """

    def __init__(self, cache_dir="./data", time_to_live=None):
        """initialize downloader

        :param cache_dir: directory where to store downloaded files, if cache_dir is None files are not stored
        :param time_to_live: how many seconds to store file on disk, None is infinity, 0 for not to store
        """

        if cache_dir is not None:
            self.__cache_dir = os.path.abspath(cache_dir)
        else:
            self.__cache_dir = None
        self.__time_to_live = time_to_live

        self.__session = requests.session()

    def cache_dir(self):
        return self.__cache_dir

    def download(self, url, filename=None, time_to_live=None):
        """Download url from internet.

        Store the downloaded content into <cache_dir>/file.
        If <cache_dir>/file exists, it returns content from disk

        :param url: page to be downloaded
        :param filename: filename where to store the content of url, None if we want not store
        :param time_to_live: how many seconds to store file on disk,
                             None use default time_to_live,
                             0 don't use cached version if any
        :returns: the content of url (str type)
        """

        pathname = self.__build_pathname(filename, url)
        # note: html must be a str type not byte type
        if time_to_live == 0 or not self.__is_cached(pathname):
            response = self.__session.get(url)
            response.raise_for_status()
            html = response.text
            self.__write_page_to_cache(pathname, html)
        else:
            html = self.__read_page_from_file(pathname)
        return html

    def __build_pathname(self, filename, url):
        if self.__cache_dir is None:
            return None
        if filename is None:
            filename = hashlib.md5(url.encode('utf-8')).hexdigest()
        pathname = os.path.join(self.__cache_dir, filename)
        return pathname

    def __is_cached(self, pathname):
        """check if pathname exists

        :param pathname:
        :returns: True if the file can be retrieved from the disk (cache)
        """

        if pathname is None:
            return False

        if not os.path.exists(pathname):
            return False

        if self.__time_to_live is None:
            return True

        cur = time.time()
        mtime = os.stat(pathname).st_mtime
        # print("last modified: %s" % time.ctime(mtime))
        return cur - mtime < self.__time_to_live

    def __write_page_to_cache(self, pathname, content):
        """write content to pathname

        :param pathname:
        :param content:
        """
        if pathname is None:
            return

        # create cache directory only the fist time it is needed
        if not os.path.exists(self.__cache_dir):
            os.makedirs(self.__cache_dir)
        if not os.path.isdir(self.__cache_dir):
            msg = "cache_dir '{}' is not a directory".format(self.__cache_dir)
            raise JsonStatException(msg)

        # note:
        # in python 3 file must be open without b (binary) option to write string
        # otherwise the following error will be generated
        # TypeError: a bytes-like object is required, not 'str'
        with open(pathname, 'w') as f:
            f.write(content)

    @staticmethod
    def __read_page_from_file(pathname):
        """it reads content from pathname

        :param pathname:
        """
        with open(pathname, 'r') as f:
            content = f.read()
        return content
