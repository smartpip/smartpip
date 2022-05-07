# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2017 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals

import base64
import codecs
import distutils.util
import hashlib
import imp
import logging
import os
import posixpath
import re
import sys
from email import message_from_file

from . import DistlibException
from .compat import ZipFile, sysconfig
from .metadata import (LEGACY_METADATA_FILENAME, Metadata, WHEEL_METADATA_FILENAME)
from .util import (cached_property)

logger = logging.getLogger(__name__)

cache = None  # created when needed

if hasattr(sys, 'pypy_version_info'):  # pragma: no cover
    IMP_PREFIX = 'pp'
elif sys.platform.startswith('java'):  # pragma: no cover
    IMP_PREFIX = 'jy'
elif sys.platform == 'cli':  # pragma: no cover
    IMP_PREFIX = 'ip'
else:
    IMP_PREFIX = 'cp'

VER_SUFFIX = sysconfig.get_config_var('py_version_nodot')
if not VER_SUFFIX:  # pragma: no cover
    VER_SUFFIX = '%s%s' % sys.version_info[:2]
PYVER = 'py' + VER_SUFFIX
IMPVER = IMP_PREFIX + VER_SUFFIX

ARCH = distutils.util.get_platform().replace('-', '_').replace('.', '_')

ABI = sysconfig.get_config_var('SOABI')
if ABI and ABI.startswith('cpython-'):
    ABI = ABI.replace('cpython-', 'cp')
else:
    def _derive_abi():
        parts = ['cp', VER_SUFFIX]
        if sysconfig.get_config_var('Py_DEBUG'):
            parts.append('d')
        if sysconfig.get_config_var('WITH_PYMALLOC'):
            parts.append('m')
        if sysconfig.get_config_var('Py_UNICODE_SIZE') == 4:
            parts.append('u')
        return ''.join(parts)


    ABI = _derive_abi()
    del _derive_abi

FILENAME_RE = re.compile(r'''
(?P<nm>[^-]+)
-(?P<vn>\d+[^-]*)
(-(?P<bn>\d+[^-]*))?
-(?P<py>\w+\d+(\.\w+\d+)*)
-(?P<bi>\w+)
-(?P<ar>\w+(\.\w+)*)
\.whl$
''', re.IGNORECASE | re.VERBOSE)

NAME_VERSION_RE = re.compile(r'''
(?P<nm>[^-]+)
-(?P<vn>\d+[^-]*)
(-(?P<bn>\d+[^-]*))?$
''', re.IGNORECASE | re.VERBOSE)

SHEBANG_RE = re.compile(br'\s*#![^\r\n]*')
SHEBANG_DETAIL_RE = re.compile(br'^(\s*#!("[^"]+"|\S+))\s+(.*)$')
SHEBANG_PYTHON = b'#!python'
SHEBANG_PYTHONW = b'#!pythonw'

if os.sep == '/':
    to_posix = lambda o: o
else:
    to_posix = lambda o: o.replace(os.sep, '/')


class Wheel(object):
    """
    Class to build and install from Wheel files (PEP 427).
    """

    wheel_version = (1, 1)
    hash_kind = 'sha256'

    def __init__(self, filename=None, sign=False, verify=False):
        """
        Initialise an instance using a (valid) filename.
        """
        self.sign = sign
        self.should_verify = verify
        self.buildver = ''
        self.pyver = [PYVER]
        self.abi = ['none']
        self.arch = ['any']
        self.dirname = os.getcwd()
        if filename is None:
            self.name = 'dummy'
            self.version = '0.1'
            self._filename = self.filename
        else:
            m = NAME_VERSION_RE.match(filename)
            if m:
                info = m.groupdict('')
                self.name = info['nm']
                # Reinstate the local version separator
                self.version = info['vn'].replace('_', '-')
                self.buildver = info['bn']
                self._filename = self.filename
            else:
                dirname, filename = os.path.split(filename)
                m = FILENAME_RE.match(filename)
                if not m:
                    raise DistlibException('Invalid name or '
                                           'filename: %r' % filename)
                if dirname:
                    self.dirname = os.path.abspath(dirname)
                self._filename = filename
                info = m.groupdict('')
                self.name = info['nm']
                self.version = info['vn']
                self.buildver = info['bn']
                self.pyver = info['py'].split('.')
                self.abi = info['bi'].split('.')
                self.arch = info['ar'].split('.')

    @property
    def filename(self):
        """
        Build and return a filename from the various components.
        """
        if self.buildver:
            buildver = '-' + self.buildver
        else:
            buildver = ''
        pyver = '.'.join(self.pyver)
        abi = '.'.join(self.abi)
        arch = '.'.join(self.arch)
        # replace - with _ as a local version separator
        version = self.version.replace('-', '_')
        return '%s-%s%s-%s-%s-%s.whl' % (self.name, version, buildver,
                                         pyver, abi, arch)

    @property
    def exists(self):
        path = os.path.join(self.dirname, self.filename)
        return os.path.isfile(path)

    @property
    def tags(self):
        for pyver in self.pyver:
            for abi in self.abi:
                for arch in self.arch:
                    yield pyver, abi, arch

    @cached_property
    def metadata(self):
        pathname = os.path.join(self.dirname, self.filename)
        name_ver = '%s-%s' % (self.name, self.version)
        info_dir = '%s.dist-info' % name_ver
        wrapper = codecs.getreader('utf-8')
        with ZipFile(pathname, 'r') as zf:
            wheel_metadata = self.get_wheel_metadata(zf)
            wv = wheel_metadata['Wheel-Version'].split('.', 1)
            file_version = tuple([int(i) for i in wv])
            # if file_version < (1, 1):
            # fns = [WHEEL_METADATA_FILENAME, METADATA_FILENAME,
            # LEGACY_METADATA_FILENAME]
            # else:
            # fns = [WHEEL_METADATA_FILENAME, METADATA_FILENAME]
            fns = [WHEEL_METADATA_FILENAME, LEGACY_METADATA_FILENAME]
            result = None
            for fn in fns:
                try:
                    metadata_filename = posixpath.join(info_dir, fn)
                    with zf.open(metadata_filename) as bf:
                        wf = wrapper(bf)
                        result = Metadata(fileobj=wf)
                        if result:
                            break
                except KeyError:
                    pass
            if not result:
                raise ValueError('Invalid wheel, because metadata is '
                                 'missing: looked in %s' % ', '.join(fns))
        return result

    def get_wheel_metadata(self, zf):
        name_ver = '%s-%s' % (self.name, self.version)
        info_dir = '%s.dist-info' % name_ver
        metadata_filename = posixpath.join(info_dir, 'WHEEL')
        with zf.open(metadata_filename) as bf:
            wf = codecs.getreader('utf-8')(bf)
            message = message_from_file(wf)
        return dict(message)

    @cached_property
    def info(self):
        pathname = os.path.join(self.dirname, self.filename)
        with ZipFile(pathname, 'r') as zf:
            result = self.get_wheel_metadata(zf)
        return result

    def process_shebang(self, data):
        m = SHEBANG_RE.match(data)
        if m:
            end = m.end()
            shebang, data_after_shebang = data[:end], data[end:]
            # Preserve any arguments after the interpreter
            if b'pythonw' in shebang.lower():
                shebang_python = SHEBANG_PYTHONW
            else:
                shebang_python = SHEBANG_PYTHON
            m = SHEBANG_DETAIL_RE.match(shebang)
            if m:
                args = b' ' + m.groups()[-1]
            else:
                args = b''
            shebang = shebang_python + args
            data = shebang + data_after_shebang
        else:
            cr = data.find(b'\r')
            lf = data.find(b'\n')
            if cr < 0 or cr > lf:
                term = b'\n'
            else:
                if data[cr:cr + 2] == b'\r\n':
                    term = b'\r\n'
                else:
                    term = b'\r'
            data = SHEBANG_PYTHON + term + data
        return data

    def get_hash(self, data, hash_kind=None):
        if hash_kind is None:
            hash_kind = self.hash_kind
        try:
            hasher = getattr(hashlib, hash_kind)
        except AttributeError:
            raise DistlibException('Unsupported hash algorithm: %r' % hash_kind)
        result = hasher(data).digest()
        result = base64.urlsafe_b64encode(result).rstrip(b'=').decode('ascii')
        return hash_kind, result

    def is_compatible(self):
        """
        Determine if a wheel is compatible with the running system.
        """
        return is_compatible(self)


def compatible_tags():
    """
    Return (pyver, abi, arch) tuples compatible with this Python.
    """
    versions = [VER_SUFFIX]
    major = VER_SUFFIX[0]
    for minor in range(sys.version_info[1] - 1, - 1, -1):
        versions.append(''.join([major, str(minor)]))

    abis = []
    for suffix, _, _ in imp.get_suffixes():
        if suffix.startswith('.abi'):
            abis.append(suffix.split('.', 2)[1])
    abis.sort()
    if ABI != 'none':
        abis.insert(0, ABI)
    abis.append('none')
    result = []

    arches = [ARCH]
    if sys.platform == 'darwin':
        m = re.match(r'(\w+)_(\d+)_(\d+)_(\w+)$', ARCH)
        if m:
            name, major, minor, arch = m.groups()
            minor = int(minor)
            matches = [arch]
            if arch in ('i386', 'ppc'):
                matches.append('fat')
            if arch in ('i386', 'ppc', 'x86_64'):
                matches.append('fat3')
            if arch in ('ppc64', 'x86_64'):
                matches.append('fat64')
            if arch in ('i386', 'x86_64'):
                matches.append('intel')
            if arch in ('i386', 'x86_64', 'intel', 'ppc', 'ppc64'):
                matches.append('universal')
            while minor >= 0:
                for match in matches:
                    s = '%s_%s_%s_%s' % (name, major, minor, match)
                    if s != ARCH:  # already there
                        arches.append(s)
                minor -= 1

    # Most specific - our Python version, ABI and arch
    for abi in abis:
        for arch in arches:
            result.append((''.join((IMP_PREFIX, versions[0])), abi, arch))

    # where no ABI / arch dependency, but IMP_PREFIX dependency
    for i, version in enumerate(versions):
        result.append((''.join((IMP_PREFIX, version)), 'none', 'any'))
        if i == 0:
            result.append((''.join((IMP_PREFIX, version[0])), 'none', 'any'))

    # no IMP_PREFIX, ABI or arch dependency
    for i, version in enumerate(versions):
        result.append((''.join(('py', version)), 'none', 'any'))
        if i == 0:
            result.append((''.join(('py', version[0])), 'none', 'any'))
    return set(result)


COMPATIBLE_TAGS = compatible_tags()

del compatible_tags


def is_compatible(wheel, tags=None):
    if not isinstance(wheel, Wheel):
        wheel = Wheel(wheel)  # assume it's a filename
    result = False
    if tags is None:
        tags = COMPATIBLE_TAGS
    for ver, abi, arch in tags:
        if ver in wheel.pyver and abi in wheel.abi and arch in wheel.arch:
            result = True
            break
    return result
