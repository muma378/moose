# -*- coding: utf-8 -*-
# moose.connection.cifs
# SMB(Server Message Block) was also known as CIFS(Common Internet File System),
# operates as an application-layer network protocol mainly used for providing
# shared access to files, printers, and serial ports and miscellaneous
# communications between nodes on a network.
# author: xiao yang <xiaoyang0117@gmail.com>
# date: 2016.Mar.03
import os
import re
import logging
from cStringIO import StringIO

from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure

from moose.core.exceptions import ConnectionTimeout

logger = logging.getLogger(__name__)

MAX_INTERVAL = 500
RETRY_TIME = 3

# differs from database,
# smb connection may be reset by the remote server for idling
class SMBConnProxy(object):
    """
    A proxy of the connection based on SMB protocol. Files are shared and
    transfered between computers via SMB.
    """
    def __init__(self, settings_dict):
        self.settings_dict = settings_dict
        self.smb_conn = self.__connect(settings_dict)
        self.__override()

    def __del__(self):
        try:
            self.smb_conn.close()
        except AttributeError, e:
            pass

    def __override(self):
        for key in SMBConnection.__dict__.keys():
            try:
                self.__getattribute__(key)
            except AttributeError, e:
                self.__setattr__(key, getattr(self.smb_conn, key, None))

    def __connect(self, settings_dict):
        conn_cnt = 0
        logger.debug(
            "Connecting SMB server on '%s:%s'..." % (settings_dict['HOST'], settings_dict['PORT']))
        while conn_cnt < RETRY_TIME:
            try:
                #SMB.__init__(self, username, password, my_name, remote_name, domain, use_ntlm_v2, sign_options, is_direct_tcp)
                smb_conn = SMBConnection(
                    settings_dict['USERNAME'],
                    settings_dict['PASSWORD'],
                    settings_dict['CLIENT_NAME'],
                    settings_dict['SERVER_NAME'],
                    settings_dict['DOMAIN'],
                    settings_dict['NTLMv2'],
                    )
                smb_conn.connect(settings_dict['HOST'], settings_dict['PORT'])
                logger.debug('Connection to SMB server established.')
                return smb_conn
            # TODO: add specified exceptions
            except ConnectionTimeout as e:
                conn_cnt += 1
                logger.info('Connecting failed, times to reconnect: %d.' % conn_cnt)
                return None

    def connect(self):
        while not self.is_connected:
            self.smb_conn = self.__connect(self.settings_dict)
            if not self.smb_conn:
                interval = random.randint(0, MAX_INTERVAL)
                logger.info('Connection will be established in %ss' % interval)
                time.sleep(interval)
            return self.smb_conn

    @property
    def is_connected(self):
        return self.smb_conn.sock

    def retrieve_file(self, shared_device, root_dir, file_obj, timeout=60):
        if not self.is_connected:
            logger.warn("Connection to smb was reset, reconnecting...")
            self.smb_conn = self.connect()
        self.smb_conn.retrieveFile(shared_device, root_dir, file_obj, timeout)


    # traverse the root_dir to get filelist
    def get_filelist(self, shared_device, root_dir, search=55, pattern='*'):
        shared_dirs = [root_dir]
        # extracted until no files existed
        shared_files = []
        if not self.is_connected:
            self.smb_conn = self.connect()

        while shared_dirs:
            path= shared_dirs.pop()
            # classifies files in the list,
            try:
                shared_items = self.smb_conn.listPath(shared_device, path, search, pattern)
            except OperationFailure, e:
                logger.error("Unable to access directory: %s." % root_dir)
            else:
                for item in shared_items:
                    file_path = os.path.join(path, item.filename)
                    if item.filename.startswith('.'):
                        logger.debug("Path %s starts with '.', ignored." % file_path)
                        continue
                    if item.isDirectory:
                        shared_dirs.append(file_path)
                    else:
                        shared_files.append((shared_device, file_path))

        logger.info("%d files were retrieved in the directory %s." % (len(shared_files), root_dir))
        return shared_files

    def retrieve(self, *args, **kwargs):
        dirs = kwargs.get('dirs', [])
        pattern = kwargs.get('pattern', '*')
        for dir_path in dirs:
            r = re.match('^/(?P<service_name>.+?)/(?P<path>.+)$', dir_path, re.UNICODE)
            if r:
                yield self.get_filelist(r.group('service_name'), r.group('path'), pattern=pattern)
            else:
                logger.error("Unable to parse the path: %s." % dir_path)
                continue
