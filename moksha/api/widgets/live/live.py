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
#
# Authors: Luke Macken <lmacken@redhat.com>

import tg
import moksha

from tw.api import Widget

from moksha.exc import MokshaException
from moksha.api.widgets.stomp import StompWidget, stomp_subscribe, stomp_unsubscribe
from moksha.api.widgets.amqp import amqp_subscribe, amqp_unsubscribe, AMQPSocket

class LiveWidget(Widget):
    """ A live streaming widget.

    This widget handles automatically subscribing your widget to any given
    topics, and registers all of the stomp callbacks.

    The basics of the LiveWidget::

        class MyLiveWidget(LiveWidget):
            topic = 'mytopic'
            onmessage = 'console.log(json)'
            template = 'mako:myproject.templates.mylivewidget'

    """
    engine_name = 'mako'

    def __init__(self, id, *args, **kw):
        super(LiveWidget, self).__init__(*args, **kw)
        self.backend = tg.config.get('moksha.livesocket.backend', 'stomp').lower()

    def update_params(self, d):
        """ Register this widgets message topic callbacks """
        super(LiveWidget, self).update_params(d)
        topics = d.get('topic', getattr(self, 'topic', d.get('topics',
                getattr(self, 'topics', None))))
        if not topics:
            raise MokshaException('You must specify a `topic` to subscribe to')
        topics = isinstance(topics, list) and topics or [topics]
        callbacks = []
        if self.backend == 'stomp':
            callbacks = StompWidget.callbacks
        elif self.backend == 'amqp':
            callbacks = AMQPSocket.callbacks
        for callback in callbacks:
            if callback == 'onmessageframe':
                for topic in topics:
                    cb = getattr(self, 'onmessage').replace('${id}', self.id)
                    moksha.livewidgets[callback][topic].append(cb)
            elif callback == 'onconnectedframe':
                moksha.livewidgets['onconnectedframe'].append(
                        subscribe_topics(topics))
            elif callback in self.params:
                moksha.livewidgets[callback].append(getattr(self, callback))

    def get_topics(self):
        topics = []
        for key in ('topic', 'topics'):
            if hasattr(self, key):
                topic = getattr(self, key)
                if topic:
                    if isinstance(topic, basestring):
                        map(topics.append, topic.split())
                    else:
                        topics += topic
        return topics

    @classmethod
    def subscribe_topics(cls, topics):
        backend = tg.config.get('moksha.livesocket.backend', 'stomp').lower()
        if backend == 'amqp':
            return amqp_subscribe(topics)
        elif backend == 'stomp':
            return stomp_subscribe(topics)
        else:
            raise MokshaException("Unknown `moksha.livesocket.backend` %r. "
                                  "Valid backends are currently 'amqp' and "
                                  "'stomp'." % backend)

    @classmethod
    def unsubscribe_topics(cls, topics):
        backend = tg.config.get('moksha.livesocket.backend', 'stomp').lower()
        if backend == 'amqp':
            return amqp_unsubscribe(topics)
        elif backend == 'stomp':
            return stomp_unsubscribe(topics)
        else:
            raise MokshaException("Unknown `moksha.livesocket.backend` %r. "
                                  "Valid backends are currently 'amqp' and "
                                  "'stomp'." % backend)


# Moksha Topic subscription handling methods
subscribe_topics = LiveWidget.subscribe_topics
unsubscribe_topics = LiveWidget.unsubscribe_topics
