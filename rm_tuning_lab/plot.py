"""Start the upstream rqt_plot widget when the lesson publisher is discoverable."""
from python_qt_binding.QtCore import QTimer
from rqt_plot.plot import Plot


class LessonPlot(Plot):
    def __init__(self, context):
        super().__init__(context)
        self.pending = {"/tuning_lab/reference", "/tuning_lab/output"}
        self.discovery = QTimer(self._widget)
        self.discovery.timeout.connect(self.connect_curves)
        self.discovery.start(250)

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
