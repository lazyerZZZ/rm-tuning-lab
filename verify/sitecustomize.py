# This temporary QA hook sends Qt clicks and keystrokes in the stock rqt process.
import sys
from pathlib import Path
if Path(sys.argv[0]).name == "rqt_reconfigure":
    from gui_driver import install
    install()

import os
exe = Path(sys.argv[0]).name
case = os.getenv("LESSON")
if exe == "rqt_plot" and case in ("carriage_loops", "cart_stop"):
    from rqt_plot.plot import Plot
    from plot_driver import install
    install(Plot)
if exe == "lesson_plot" and case == "range_step":
    from rm_tuning_lab.plot import LessonPlot
    from plot_driver import install
    install(LessonPlot)
