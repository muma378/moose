# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from os.path import join, normpath

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

import platform
IS_WINDOWS = True if platform.system()=="Windows" else False
IS_POSIX = not IS_WINDOWS

DB_CONN_MAX_TIMES = 3
DB_CONN_MAX_INTERVAL = 300
DB_CONN_TIMEOUT = 300

INSTALLED_APPS = []

# List of strings representing apps to output logs to self-defined files.
LOGGING_APPS = []

# Patterns of images to be found, not including '*.bmp', '*.gif', '*.tiff'
# cause it may bring problem in drawing pictures
IMAGE_PATTERN = ('*.jpg', '*.png', '*.jpeg')
ALL_IMAGE_PATTERN = ('*.jpg', '*.png', '*.jpeg', '*.bmp', '*.gif', '*.tiff')

AUDIO_PATTERN = ('*.wav', '*.mp3')


###########
# CONFIGS #
###########

CONF_TEMPLATE_NAME = 'template.cfg'
CONF_IN_USING_NAME = 'config.cfg'

CONFIGS_DIRNAME = 'configs'
CONFIG_CACHE_NAME = '.config'
CONFIG_EXTENSION = '.cfg'

CONFIG_META_KEYWORD = 'meta'
CONFIG_KEYS_KEYWORD = 'keys'
CONFIG_LIST_SEP = ','
CONFIG_META_SECTION_CONCATE = '_'
CONFIG_DESC_EXPR_SEP = ':'
CONFIG_DISCOVER_BY_TAG = 't'
CONFIG_DISCOVER_BY_ATTR = 'a'
CONFIG_DESC_ATTR_VAL_SEP = '='
CONFIG_DESC_SECT_OPT_SEP = '.'

DEFAULT_TIMEOUT = 60

# base settings for all connection
CONNECTION_SETTINGS = {
    "timeout": 300,
    "interval": 300,
    "retry": 3
}

###############
# CONNECTIONS #
###############

# Configs for Azure Blob Service
AZURE = {
  'ACCOUNT': '',
  'KEY': '',
  'ENDPOINT': '',
  "TIMEOUT": 300,
}

DATABASE_NAME = '[10.0.0.201].CrowdDB.dbo'

DATABASES = {
    'sqlserver': {
        'HOST': '',
        'PORT': '',
        'USER': '',
        'PASSWORD': '',
        'DATABASE': '',
        'CHARSET': 'UTF-8',
        'TABLE_ALIAS': {
            'table_result': '[10.0.0.201].CrowdDB.dbo.DataResult',
            'table_source': '[10.0.0.201].CrowdDB.dbo.DataSource',
            'table_person': '[10.0.0.201].CrowdDB.dbo.Person',
            'table_project': '[10.0.0.201].CrowdDB.dbo.Project',
            'table_person_in_project': '[10.0.0.201].CrowdDB.dbo.PersonInProject',
        },
    },
    'mongo': {
        'HOST': '',
        'PORT': '',
        'USER': '',
        'PASSWORD': '',
    },
    'mysql': {
        'HOST': '',
        'PORT': '',
        'USER': '',
        'PASSWORD': '',
        'DATABASE': '',
        'CHARSET': 'utf8',
        'TABLE_ALIAS': {
            'table_result': 'dataresult',
            'table_source': 'datasource',
            'table_person': 'person',
            'table_project': 'task',
            'table_person_in_project': 'person_in_task',
        },
    },
    'mongo-indie': {
        'HOST': '',
        'PORT': '',
        'USER': '',
        'PASSWORD': '',
        'DATABASE': '',
    },
}


##########
# DRAWER #
##########
DRAWER_RADIUS = 3
DEFAULT_THICKNESS = 3
DEFAULT_COLOR = (255, 0, 0)


# Config for Server Message Block protocol
SMB = {
    'HOST': '',
    'PORT': 139, # 139 if using NetBIOS over tcp/ip, 445 if direct hosting over tcp/ip
    'USERNAME': 'USERNAME',
    'PASSWORD': '********',
    'DOMAIN': 'DATATANG',   # workgroup, it is safe to leave it empty
    'CLIENT_NAME': 'DATATANG',  # an arbitary ASCII string
    'SERVER_NAME': 'TEST-5-11',
    # NTLMv1 or NTLMv2 authentication will be used, guess to be True for WIN7, Vista
    'NTLMv2': True,
}

WEB_SETTINGS = {
    "username": "",
    "password": "",
}

BROWSER_SIMULATOR = "Firefox"   # Firefox, Chrome, Ie, Opera


DOWNLOAD_SETTINGS = {
    "queue_buffer": 2500,
    "queue_timeout": 60,
    "download_timeout": 60,
}


# Host for sending email.
EMAIL_HOST = 'mail.datatang.com'

# Default email address to use for various automated correspondence from
# the site managers.
DEFAULT_FROM_EMAIL = 'tech@datatang.com'

# Subject-line prefix for email messages send with mail module
# Make sure to include the trailing space.
EMAIL_SUBJECT_PREFIX = '[Moose] '

# others
EDITOR = "vim" if IS_POSIX else "notepad"

DATALINK_TEMPLATE = 'http://bz.datatang.com/datalink?data={data_guid}&taskId={task_id}'
AZURE_FILELINK = 'http://crowdfile.blob.core.chinacloudapi.cn/{task_id}/{file_path}'

PREFERRED_PROJECT_NAME = u"%d第%d期图片标注任务"

TIME_ZONE = 'Asia/Shanghai'

RESERVED_FILES = [
    '.gitignore',
    ]
