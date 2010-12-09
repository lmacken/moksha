from paver.easy import *
from paver.setuputils import setup, find_package_data, find_packages
from paver.setuputils import install_distutils_tasks
from moksha.lib.paver_tasks import *

install_distutils_tasks()

options(
    setup=Bunch(
        name="moksha.metrics",
        version="0.1",
        release="1",
        url="http://moksha.fedorahosted.org",
        description="Moksha Metrics App",
        long_description="",
        author="Luke Macken",
        author_email="lmacken@redhat.com",
        license="AGPLv3",
        rpm_name='moksha-metrics',
        packages=find_packages(),
        package_data=find_package_data(),
        namespace_packages=['moksha', 'moksha.apps'],
        install_requires=["Moksha"],
        entry_points={
            'moksha.stream': (
                'moksha_metrics = moksha.apps.metrics.streams:MokshaMetricsDataStream',
            ),
            'moksha.consumer': (
                'moksha_message_metrics = moksha.apps.metrics.consumers:MokshaMessageMetricsConsumer',
            ),
            'moksha.widget': (
                'MokshaTW2CPUUsageWidget = moksha.apps.metrics.widgets:MokshaTW2CPUUsageWidget',
                'MokshaMemoryUsageWidget = moksha.apps.metrics.widgets:MokshaMemoryUsageWidget',
                'MokshaCPUUsageWidget = moksha.apps.metrics.widgets:MokshaCPUUsageWidget',
                'MokshaMessageMetricsWidget = moksha.apps.metrics.widgets:MokshaMessageMetricsWidget',
            ),
            'moksha.global': (
                'moksha_socket = moksha.api.widgets:moksha_socket',
                'jquery_ui_draggable = tw.jquery.ui:ui_draggable_js',
                'jquery_ui_resizable = tw.jquery.ui:ui_resizable_js',
            ),
        }
    ),
)
