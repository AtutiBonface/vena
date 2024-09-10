from pillar import MainApplication
from PyQt6.QtWidgets import QApplication
import sys, asyncio
from qasync import QEventLoop



if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainapplication = MainApplication()
    mainapplication.show()
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:        
        try:
            loop.run_until_complete(mainapplication.run_all_tasks())
            sys.exit(app.exec())
        except Exception as e:
            pass

