from pillar import MainApplication
from PyQt6.QtWidgets import QApplication
import sys, asyncio
from qasync import QEventLoop

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        loop.run_until_complete(window.websocket_main())
        try:
            sys.exit(app.exec())
        except Exception as e:
            pass

