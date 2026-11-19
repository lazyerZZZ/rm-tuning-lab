"""Start the upstream rqt_plot widget when the lesson publisher is discoverable."""
from python_qt_binding.QtCore import QTimer
from rqt_plot.plot import Plot
from .core import DT, STEPS


class LessonPlot(Plot):
    def __init__(self, context):
        super().__init__(context)
        # Keep the response visible even on a fresh rqt profile.
        self._widget.setMinimumSize(480, 300)
        self.pending = {"/tuning_lab/reference", "/tuning_lab/output"}
        self.discovery = QTimer(self._widget)
        self.discovery.timeout.connect(self.connect_curves)
        self.discovery.start(250)

    def restore_settings(self, plugin_settings, instance_settings):
        super().restore_settings(plugin_settings, instance_settings)
        if not instance_settings.value("x_limits", []):
            # rqt creates its selected plotting backend while restoring settings.
            self._data_plot.set_xlim([0.0, STEPS * DT + 2.0])

    def connect_curves(self):
        for topic in self.pending.copy():
            if self._node.count_publishers(topic):
                field = topic + "/data"
                if field not in self._widget._rosdata:
                    self._widget.add_topic(field)
                if field in self._widget._rosdata:
                    self.pending.remove(topic)
        if not self.pending:
            self.discovery.stop()

    def shutdown_plugin(self):
        self.discovery.stop()
        super().shutdown_plugin()


def main():
    from rqt_gui.main import Main
    plugin = "rm_tuning_lab.plot.LessonPlot"
    return Main(filename=plugin).main(standalone=plugin)
