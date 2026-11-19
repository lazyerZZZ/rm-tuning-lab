"""Start the upstream rqt_plot widget when the lesson publisher is discoverable."""
from python_qt_binding.QtCore import QTimer
from rqt_plot.plot import Plot
from .core import DT, STEPS


class LessonPlot(Plot):
    def __init__(self, context):
        super().__init__(context)
        # Keep the response visible even on a fresh rqt profile.
        self._widget.setMinimumSize(480, 300)
        self.fit_first_trial = True
        self.pending = {"/tuning_lab/reference", "/tuning_lab/output"}
        self.discovery = QTimer(self._widget)
        self.discovery.timeout.connect(self.connect_curves)
        self.discovery.start(250)

    def restore_settings(self, plugin_settings, instance_settings):
        super().restore_settings(plugin_settings, instance_settings)
        self.fit_first_trial = not instance_settings.value("x_limits", [])

    def connect_curves(self):
        for topic in self.pending.copy():
            if self._node.count_publishers(topic):
                field = topic + "/data"
                if field not in self._widget._rosdata:
                    self._widget.add_topic(field)
                if field in self._widget._rosdata:
                    self.pending.remove(topic)
        if self.pending:
            return
        if self.fit_first_trial:
            # An empty upstream redraw resets the axis to [0, 1]. Wait until
            # the plotted buffers, not just the subscriptions, contain samples.
            traces = [self._data_plot._curves[topic + "/data"]["x"]
                      for topic in ("/tuning_lab/reference", "/tuning_lab/output")]
            if any(len(trace) == 0 for trace in traces):
                return
            right = max(trace[-1] for trace in traces)
            self._data_plot.set_xlim([right - STEPS * DT - 2.0, right])
            self._data_plot.set_ylim([-0.1, 1.1])
        self.discovery.stop()

    def shutdown_plugin(self):
        self.discovery.stop()
        super().shutdown_plugin()


def main():
    from rqt_gui.main import Main
    plugin = "rm_tuning_lab.plot.LessonPlot"
    return Main(filename=plugin).main(standalone=plugin)
