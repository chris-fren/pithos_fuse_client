import os
import sys
import errno
import tempfile
import time
import datetime
import optparse

from stat import S_IFDIR, S_IFREG
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from kamaki.clients.pithos import PithosClient
from kamaki.clients.pithos.rest_api import PithosRestClient
from kamaki.clients import ClientError

__author__ = 'Chrysostomos Nanakos, Christos Stavrakakis'
__license__ = 'LGPL'
__version__ = '0.1'
__email__ = 'cnanakos@grnet.gr, cstavr@grnet.gr'

API_URL = 'https://pithos.okeanos.grnet.gr/object-store/v1/'


class PithosAPI:
    def __init__(self, account, token):
        self.tree_children = {}
        self.tree_expire = {}
        self.tree_info_expire = {}
        self.tree_info_children = {}
        self.account = account
        self.token = token
        self.ttl = 10
        self.pithos = PithosClient(API_URL, token, account, container=None)
        self.containers = self.pithos.list_containers()
        if self.containers is None:
            raise FuseOSError(errno.EPERM)

    def get_container(self, path):
        return path.split('/')[1]

    def get_object(self, path):
        obj = path.split('/')
        del obj[1]
        return '/'.join(obj)

    def list_containers(self):
        return self.pithos.list_containers()

    def readdir(self, path):
        if path in self.tree_expire:
            if self.tree_expire[path] >= time.time():
                return self.tree_children[path]
        if path == '/':
            self.tree_children[path] = self.pithos.list_containers()
            self.tree_expire[path] = time.time() + self.ttl
            return self.tree_children[path]
        else:
            container = self.get_container(path)
            pithosPath = path.split('/')
            del pithosPath[1]
            pithosPath = "/%s" % '/'.join(pithosPath)
            pithosPath = os.path.normpath(pithosPath)
            pithos = PithosClient(API_URL, self.token, self.account, container)
            objects = pithos.list_objects_in_path(pithosPath)
            new_objs = []
            trm = pithosPath.lstrip('/')
            for obj in objects:
                obj['name'] = obj['name'][len(trm):].lstrip('/')
                new_objs.append(obj)
            self.tree_children[path] = new_objs
            self.tree_expire[path] = time.time() + self.ttl
            return self.tree_children[path]

    def getinfo(self, path):
        if path in self.tree_info_expire:
            if self.tree_info_expire[path] >= time.time():
                return self.tree_info_children[path]
        container = self.get_container(path)
        pithos = PithosClient(API_URL, self.token, self.account, container)
        try:
            objs = pithos.get_object_info('/'.join(path.split('/')[2:]))
            self.tree_info_children[path] = objs
            self.tree_info_expire[path] = time.time() + self.ttl
            return self.tree_info_children[path]
        except ClientError:
            return None

    def create_container(self, path):
        container = self.get_container(path)
        new_container = self.get_object(path)
        pithos = PithosClient(API_URL, self.token, self.account, container)
        pithos.create_container(new_container)

    def delete_container(self, path):
        container = self.get_container(path)
        unlink_container = self.get_object(path)
        pithos = PithosClient(API_URL, self.token, self.account, container)
        pithos.purge_container(unlink_container)

    def create_directory(self, path):
        container = self.get_container(path)
        new_directory = self.get_object(path)
        pithos = PithosRestClient(API_URL, self.token, self.account, container)
        pithos.object_put(new_directory, content_length=0,
                          content_type='application/directory')

    def delete_directory(self, path):
        container = self.get_container(path)
        unlink_directory = self.get_object(path)
        pithos = PithosRestClient(API_URL, self.token, self.account, container)
        pithos.object_delete(unlink_directory, delimiter='/')

    def download_object(self, path, fd):
        container = self.get_container(path)
        obj = self.get_object(path)
        pithos = PithosClient(API_URL, self.token, self.account, container)
        pithos.download_object(obj, fd)

    def unlink_object(self, path):
        container = self.get_container(path)
        obj = self.get_object(path)
        pithos = PithosClient(API_URL, self.token, self.account, container)
        pithos.del_object(obj, delimiter='/')

    def upload_object(self, path, fd):
        fd.seek(0, 2)
        size = fd.tell()
        fd.seek(0)
        container = self.get_container(path)
        obj = self.get_object(path)
        pithos = PithosClient(API_URL, self.token, self.account, container)
        pithos.upload_object(obj, fd, size=size)
        fd.seek(0)

    def rename(self, old, new):
        old_container = self.get_container(old)
        new_container = self.get_container(new)
        old_obj = self.get_object(old)
        new_obj = self.get_object(new)
        pithos = PithosClient(API_URL, self.token, self.account, old_container)
        pithos.move_object(old_container, old_obj, new_container, new_obj,
                           delimiter='/')


class PithosFuse(LoggingMixIn, Operations):
    def __init__(self, account, token, logfile=None):
        self.pithos_api = PithosAPI(account, token)
        self.files = {}

    def file_rename(self, old, new):
        if old in self.files:
            self.files[new] = self.files[old]
            del self.files[old]

    def file_get(self, path, download=True):
        if path in self.files:
            return self.files[path]
        f = tempfile.NamedTemporaryFile(delete=True)  # FIXME True or False
        if download is True:
            try:
                raw = self.pithos_api.download_object(path, f)
            except ClientError:
                raw = ''
                f.write(raw)
        else:
            raw = ''
            f.write(raw)
        self.files[path] = {'object': f, 'modified': False}
        return self.files[path]

    def file_close(self, path):
        if path in self.files:
            if self.files[path]['modified'] is True:
                self.file_upload(path)
            self.files[path]['object'].close()
            del self.files[path]

    def file_upload(self, path):
        if path not in self.files:
            raise FuseOSError(errno.EIO)

        fileObject = self.file_get(path)
        if fileObject['modified'] is False:
            return True

        f = fileObject['object']
        self.pithos_api.upload_object(path, f)
        fileObject['modified'] = False

    def chmod(self, path, mode):
        return 0

    def chown(self, path, uid, gid):
        return 0

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def getattr(self, path, fh=None):
        if path == '/':
            st = dict(st_mode=(S_IFDIR | 0755), st_nlink=2)
            st['st_ctime'] = st['st_atime'] = st['st_mtime'] = time.time()
        elif path.count('/') == 1:
            name = os.path.basename(path)
            st = dict(st_mode=(S_IFDIR | 0644), st_nlink=2, st_size=int(4096),
                      st_uid=os.geteuid(), st_gid=os.getgid())
            for child in self.pithos_api.list_containers():
                if child['name'] == name:
                    dt_str = "%Y-%m-%dT%H:%M:%S.%f+00:00"
                    last_modified = child['last_modified']
                    epoch_str = datetime.datetime.strptime(last_modified,
                                                           dt_str)
                    ctime = time.mktime(epoch_str.timetuple())
                    st['st_ctime'] = st['st_atime'] = st['st_mtime'] = ctime
                    return st
            raise FuseOSError(errno.ENOENT)
        else:
            name = unicode(os.path.basename(path))
            objects = self.pithos_api.getinfo(path)
            if objects is None:
                raise FuseOSError(errno.ENOENT)
            elif objects.get('content-type') != 'application/directory':
                st = dict(st_mode=(S_IFREG | 0644), st_nlink=1,
                          st_size=int(objects.get('content-length', 0)),
                          st_uid=os.geteuid(), st_gid=os.getgid())
            else:
                st = dict(st_mode=(S_IFDIR | 0755), st_nlink=2,
                          st_size=int(4096), st_uid=os.geteuid(),
                          st_gid=os.getgid())

            dt_str = "%a, %d %b %Y %H:%M:%S GMT"
            last_modified = objects.get('last-modified', None)
            if last_modified is not None:
                epoch_str = datetime.datetime.strptime(last_modified, dt_str)
                ctime = time.mktime(epoch_str.timetuple())
            else:
                ctime = 0
            st['st_ctime'] = st['st_atime'] = ctime
            st['st_mtime'] = ctime
        return st

    def mkdir(self, path, mode):
        if path.count('/') == 1:
            self.pithos_api.create_container(path)
        else:
            self.pithos_api.create_directory(path)

    def open(self, path, flags):
        self.file_get(path)
        return 0

    def flush(self, path, fh):
        if path in self.files:
            if self.files[path]['modified'] is True:
                self.file_upload(path)

    def fsync(self, path, datasync, fh):
        if path in self.files:
            if self.files[path]['modified'] is True:
                self.file_upload(path)

    def release(self, path, fh):
        self.file_close(path)

    def read(self, path, size, offset, fh):
        f = self.file_get(path)['object']
        f.seek(offset)
        return f.read(size)

    def readdir(self, path, fh):
        objects = self.pithos_api.readdir(path)
        listing = ['.', '..']
        for child in objects:
            listing.append(child['name'])
        return listing

    def rename(self, old, new):
        self.file_rename(old, new)
        self.pithos_api.rename(old, new)

    def create(self, path, mode):
        self.file_get(path, download=False)
        self.files[path]['modified'] = True
        self.file_upload(path)
        return 0

    def truncate(self, path, length, fh=None):
        f = self.file_get(path)['object']
        f.truncate(length)

    def unlink(self, path):
        self.pithos_api.unlink_object(path)

    def rmdir(self, path):
        if path.count('/') == 1:
            self.pithos_api.delete_container(path)
        else:
            self.pithos_api.delete_directory(path)

    def write(self, path, data, offset, fh):
        fileObject = self.file_get(path)
        f = fileObject['object']
        f.seek(offset)
        f.write(data)
        fileObject['modified'] = True
        return len(data)

    access = None
    getxattr = None
    listxattr = None
    opendir = None
    releasedir = None


def main():
    usage = "usage %prog [options]"
    parser = optparse.OptionParser(description="Pithos+ FUSE Filysystem",
                                   usage=usage)
    required_group = optparse.OptionGroup(parser, "Required Options")
    required_group.add_option(
        '-u', '--username',
        dest='username',
        metavar='ACCOUNT',
        help='Pithos+ Username')
    required_group.add_option(
        '-p', '--password',
        dest='password',
        metavar='TOKEN',
        help='Pithos+ Token')
    required_group.add_option(
        '-m', '--mount_point',
        dest='mount_point',
        metavar='MOUNTDIR',
        help='Directory to mount filesystem')

    debug_group = optparse.OptionGroup(parser, "Debug Options")
    debug_group.add_option(
        '-d', '--debug',
        dest='debug',
        default=False,
        action='store_true',
        help='Turn on debug output (alomg with -f)')
    debug_group.add_option(
        '-s', '--nothreads',
        dest='nothreads',
        default=False,
        action='store_true',
        help='Disallow multi-threaded operation. Run with only one thread')
    debug_group.add_option(
        '-f', '--foreground',
        dest='foreground',
        default=False,
        action='store_true',
        help='Run in foreground')

    extra_group = optparse.OptionGroup(parser, "Extra options")
    extra_group.add_option(
        '-o', '--options',
        dest='extra_options',
        help='Comma seperated key=val options for FUSE')

    parser.add_option_group(required_group)
    parser.add_option_group(debug_group)
    parser.add_option_group(extra_group)

    options, args = parser.parse_args()

    for attr in ["username", "password", "mount_point"]:
        if getattr(options, attr) is None:
            parser.print_help()
            parser.error("Error: Option '--%s' is required!" % attr)

    fuse_kv = {
        "debug": options.debug,
        "foreground": options.foreground,
        "nothreads": options.nothreads
    }

    if options.extra_options:
        extra_options = map(lambda kv: kv.split('='),
                            options.extra_options.split(","))
        fuse_kv.update(extra_options)

    FUSE(PithosFuse(options.username, options.password),
         options.mount_point,
         **fuse_kv)

if __name__ == "__main__":
    main()
