"""Use the rqt topic edit and + button once the fields exist, then capture the window."""
import os
from pathlib import Path
from PyQt5.QtTest import QTest
from python_qt_binding.QtCore import Qt, QTimer

def install(cls):
    original = cls.restore_settings
    def restore(self, *args):
        original(self, *args)
        fields = {"carriage_loops": ["speed_reference", "velocity"],
                  "cart_stop": ["effort"], "range_step": ["measurement"]}[os.environ["LESSON"]]
        paths = ["/tuning_lab/" + k for k in fields]
        out = Path(os.environ["EVIDENCE"])
        widget = self._widget
        timer = QTimer(widget)
        def update():
            if not all(self._node.count_publishers(p) for p in paths):
                return
            for topic in paths:
                field = topic + "/data"
                if field not in widget._rosdata:
                    widget.topic_edit.selectAll()
                    QTest.keyClicks(widget.topic_edit, field)
                    QTest.keyClick(widget.topic_edit, Qt.Key_Escape)
                    QTest.mouseClick(widget.subscribe_topic_button, Qt.LeftButton)
                    return
            if not all(len(self._data_plot._curves[p+"/data"]["x"]) for p in paths):
                return
            (out/"plots-ready").touch()
            if (out/"capture").exists():
                widget.window().resize(930, 540)
                QTest.qWait(350)
                widget.window().grab().save(str(out/"rqt-plot.png"))
                (out/"captured").touch()
                timer.stop()
        timer.timeout.connect(update)
        timer.start(500)
    cls.restore_settings = restore
