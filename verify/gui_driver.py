from pathlib import Path
import traceback
from PyQt5.QtTest import QTest
from python_qt_binding.QtCore import Qt, QTimer
from rqt_reconfigure.param_widget import ParamWidget
from rqt_reconfigure.param_editors import DoubleEditor

import os
from stages import STAGES
OUT = Path(os.environ["EVIDENCE"])

def install():
    original = ParamWidget.restore_settings
    def restore(widget, *args):
        original(widget, *args)
        timer = QTimer(widget)
        timer.setInterval(250)
        def poll():
            command = OUT / "request"
            if not command.exists():
                return
            timer.stop()
            try:
                stage = command.read_text().strip()
                selector = widget._nodesel_widget
                if stage == "select":
                    widget.window().resize(1020, 640)
                    QTest.mouseClick(selector._refresh_button, Qt.LeftButton)
                    QTest.qWait(500)
                    view = selector._node_selector_view
                    view.expandAll()
                    model = view.model()
                    hits = model.match(model.index(0, 0), Qt.DisplayRole, "tuning_lab", 1,
                                       Qt.MatchContains | Qt.MatchRecursive)
                    assert hits, "Missing tuning_lab in node list"
                    view.scrollTo(hits[0])
                    QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view.visualRect(hits[0]).center())
                else:
                    params = STAGES[os.environ["LESSON"]][stage]
                    editors = {e.parameter.name: e for e in widget.findChildren(DoubleEditor) if e.isVisible()}
                    for key, value in params.items():
                        box = editors[key]._paramval_lineEdit
                        QTest.mouseClick(box, Qt.LeftButton)
                        QTest.keyClick(box, Qt.Key_A, Qt.ControlModifier)
                        QTest.keyClicks(box, str(value))
                        QTest.keyClick(box, Qt.Key_Return)
                        QTest.qWait(180)
                QTest.qWait(350)
                assert widget.window().grab().save(str(OUT / ("panel-"+stage+".png")))
                (OUT / ("done-"+stage)).touch()
            except Exception:
                (OUT / "error").write_text(traceback.format_exc())
            finally:
                command.unlink(missing_ok=True)
                timer.start()
        timer.timeout.connect(poll)
        timer.start()
    ParamWidget.restore_settings = restore
