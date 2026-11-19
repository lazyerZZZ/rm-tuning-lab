# This temporary QA hook sends Qt clicks and keystrokes in the stock rqt process.
import sys
from pathlib import Path
if Path(sys.argv[0]).name == "rqt_reconfigure":
    from gui_driver import install
    install()
