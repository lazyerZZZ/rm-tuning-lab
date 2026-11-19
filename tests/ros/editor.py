"""Edit the stock rqt_reconfigure widget and read the gain back over DDS."""
import threading

from python_qt_binding.QtCore import Qt
from python_qt_binding.QtWidgets import QApplication, QLineEdit
from python_qt_binding import QT_BINDING
from importlib import import_module
import rclpy
from rqt_reconfigure.param_api import ParamClient
from rqt_reconfigure.param_editors import DoubleEditor


def main():
    app = QApplication([])
    # Use the QtTest module that matches the actual plugin's Qt binding.
    binding = {"pyqt": "PyQt5", "pyside": "PySide2"}[QT_BINDING]
    qtest = import_module(binding + ".QtTest").QTest
    rclpy.init()
    node = rclpy.create_node("lesson_editor_probe")
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()
    client = ParamClient(node, "/tuning_lab")
    try:
        # Each rqt client has its own DDS discovery cache on startup.
        for service in (client._get_params_client, client._set_params_client,
                        client._describe_params_client):
            if not service.wait_for_service(timeout_sec=15.0):
                raise TimeoutError(service.srv_name)
        param = client.get_parameters(["kp"])[0]
        desc = client.describe_parameters(["kp"])[0]
        widget = DoubleEditor(client, param, desc)
        widget.show()
        textbox = widget.findChild(QLineEdit)
        textbox.setFocus()
        textbox.selectAll()
        qtest.keyClicks(textbox, "3.0")
        qtest.keyClick(textbox, Qt.Key_Return)
        app.processEvents()
        actual = client.get_parameters(["kp"])[0].value
        assert actual == 3.0, f"rqt edit did not reach the node: {actual}"
        print("Confirmed rqt editor -> /tuning_lab kp = 3.0")
        widget.close()
    finally:
        client.close()
        rclpy.shutdown()
        thread.join(timeout=5)
        node.destroy_node()


if __name__ == "__main__":
    main()
