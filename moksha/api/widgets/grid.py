# This file is part of Moksha.
# Copyright (C) 2008-2010  Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid
import simplejson as json

from tw.api import JSLink, js_callback
from tw.forms import FormField
from tw.jquery.ui_core import jquery_ui_core_js
from tw.jquery import jQuery, jquery_js

from moksha.lib.helpers import when_ready
from moksha.widgets.json import jquery_json_js
from moksha.widgets.jquery_template import jquery_template_js

moksha_ui_grid_js = JSLink(filename='public/javascript/ui/moksha.ui.grid.js',
                           modname='moksha',
                           javascript=[jquery_ui_core_js,
                                       jquery_template_js,
                                       jquery_json_js])

moksha_ui_popup_js = JSLink(filename='public/javascript/ui/moksha.ui.popup.js',
                           modname='moksha',
                           javascript=[jquery_ui_core_js])

class Grid(FormField):
    javascript=[jquery_ui_core_js, moksha_ui_grid_js, moksha_ui_popup_js]
    params= ['rows_per_page', 'page_num', 'total_rows',
            'filters', 'unique_key', 'sort_key', 'sort_order',
            'row_template', 'resource', 'resource_path',
            'loading_throbber', 'uid', 'more_link', 'alphaPager',
            'numericPager']
    hidden = True # hide from the moksha main menu

    rows_per_page = 10
    page_num = 1
    total_rows = 0
    filters = None
    unique_key = None
    sort_key = None
    sort_order = -1
    row_template = None
    resource = None
    resource_path = None
    loading_throbber = None
    more_link = None
    alphaPager = False
    numericPager = False

    def update_params(self, d):
        super(Grid, self).update_params(d)
        if not getattr(d,"id",None):
            raise ValueError, "Moksha Grid is supposed to have id"

        if not d.filters:
            d.filters = {}

        grid_d = {}
        for p in self.params:
            v = d.get(p)
            if v:
                if isinstance(v, dict):
                    v = json.dumps(v)

                grid_d[p] = v

        d['id'] += "-uuid" + str(uuid.uuid4())

        self.add_call(when_ready(jQuery("#%s" % d['id']).mokshagrid(grid_d)))
