# This file is part of Moksha.
#
# Moksha is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Moksha is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Moksha.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2008, Red Hat, Inc.
# Authors: John (J5) Palmieri <johnp@redhat.com>

import logging
import pkg_resources

from webob import Request, Response
from pylons import config
from pylons.i18n import ugettext

from moksha.exc import ApplicationNotFound, MokshaException

log = logging.getLogger(__name__)

import shlex
import os

class Chunk(object):
    def __init__(self):
        self.consumes = []
        self.info = ""
        self.code = ""

    def parse_consumes_field(self):
        start = self.info.find('consumes') + 8
        start = self.info.find('[',start)
        end = self.info.find(']', start)

        consumes = self.info[start + 1 : end]

        self.consumes = shlex.split(consumes)

class MokshaExtensionPointMiddleware(object):
    """
    A layer of WSGI middleware that is responsible for serving
    javascript extensions.

    If a request for an extension comes in (/moksha_extension/$extension_point),
    it will serve up any extensions that consume the extension point.

    This works by searching for all extensions of a given type and creating a
    javascript array pointing to their run functions.

    All extensions should contain at least a run function which will be passed
    the data fields specified by the extension point.  They should also return
    the HTML they wish to be embedded at the extension point. e.g.:

    function run(data) {
      // data will always contain a uid field and the HTML you return
      // will be wrapped in a div with that id
      return "<div>Hello</div>";
    };

    Extensions also need a header which describes the extension as such:

    info : {'consumes':['build_message'],
            'author': 'John (J5) Palmieri <johnp@redhat.com>',
            'version': '0.1',
            'name': 'Hello World Message'}

    """
    def __init__(self, application,
                 entry_point='moksha.extension_point',
                 test_dir=None):
        """
        :application: WSGI application to wrap
        :extension_point: the python extry point which specifies modules to
                          scan for JavaScript extension_points
        :test_dir: a directory to scan for JavaScript extension_points which
                   are being tested before they are added to the module
        """

        log.info('Creating MokshaExtensionPointMiddleware')
        self.application = application

        # if debug is False condense javascript to optimize
        self.__debug = config.get('moksha.extension_points.debug')
        self.__extension_cache = {}
        self.application = application

        if test_dir:
            self.load_extension_dir(test_dir)

        for ep in pkg_resources.iter_entry_points(entry_point):
            mod = ep.load()
            dir = os.path.dirname(mod.__file__)
            self.load_extension_dir(dir)

    def chunk_code(self, js, filename):
        start = js.find('{')
        end = 0
        chunks = []
        length = len(js)

        while (start != -1):
            count = 1
            i = start + 1
            pull_info = False
            pull_info_start = 0
            pull_info_end = 0

            while(count != 0 and i < length):
                if js[i] == '{':
                    count += 1
                elif js[i] == '}':
                    count -= 1
                elif count==1 and js[i]=='i' and js.find('info',i) == i:
                    if pull_info_start != 0:
                        print "ERROR: Unexpected Info Field : extension file %s has more than on info field per extension (ignoring file)" % filename
                        return None

                    # put us on info duty
                    pull_info = True

                if pull_info:
                    if pull_info_start == 0:
                        if count > 1:
                            pull_info_start = i
                    else:
                        if count == 1:
                            pull_info_end = i
                            pull_info = False

                i += 1

            end = i

            c = Chunk()
            c.code = js[start:end]
            c.info = js[pull_info_start:pull_info_end + 1]

            c.parse_consumes_field()
            chunks.append(c)

            if i >= length:
                print "ERROR: Unexpected EOF: extension file %s has mismatched braces (ignoring file)" % filename
                return None

            start = js.find('{', end)

        return chunks

    def load_extension(self, file):
        log.info("Loading JavaScript extension %s" % file)
        f = open(file,'r')
        js = f.read()

        chunks = self.chunk_code(js, file)
        if not chunks:
            if chunks != None:
                log.warning("No Content : extension file %s doesn't have any valid extensions (ignoring file)" % filename)

            return

        for c in chunks:
            for exttype in c.consumes:
                code = self.__extension_cache.get(exttype, [])
                #TODO: run through optimizer which strips whitespace
                code.append(c.code)
                self.__extension_cache[exttype] = code

    def load_extension_dir(self, dir):
        for root, dirs, files in os.walk(dir):
            for name in files:
                if name.endswith('js'):
                    path = os.path.join(root, name)
                    self.load_extension(path)

        # compile lists in the cache down to a string so we don't have to
        # process it on each request
        for key, value in self.__extension_cache.iteritems():
            s = '[' + ','.join(value) + ']'
            self.__extension_cache[key] = s

    def __call__(self, environ, start_response):

        request = Request(environ)

        if request.path.startswith('/moksha_extension_point'):
            exttype = request.params.get('exttype')
            if not exttype:
                response = Response('')
            else:
                extensions_data = self.__extension_cache.get(exttype, "")
                extensions_str = ','.join(extensions_data)

                script = 'var mf_loaded_extensions ='
                script += extensions_data
                script += ';'
                # now run the deferred extensions queued up while the scripts
                # were being downloaded

                script += 'myfedora.extensions._extension_cache["' + exttype +'"] = mf_loaded_extensions;'
                script += 'var deferred=myfedora.extensions._extension_deferred["' + exttype +'"];'
                script += 'var d=deferred.shift();'
                script += 'while(d){'
                script +=   'myfedora.extensions.run_extensions(mf_loaded_extensions, d);'
                script +=   'd = deferred.shift();'
                script += '}'

                response = Response(script)
        else:
            response = request.get_response(self.application)

        return response(environ, start_response)