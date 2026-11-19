"""Save the actual curve window from the virtual display for visual review."""
import sys
from python_qt_binding.QtWidgets import QApplication

app = QApplication([])
image = app.primaryScreen().grabWindow(int(sys.argv[1]))
if image.isNull() or not image.save("rqt-plot.png"):
    raise RuntimeError("Could not capture the rqt plot")
