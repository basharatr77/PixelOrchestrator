from app.agents.device_agent.detector import start_detector
from app.agents.orchestrator.core import main as orchestrator_main
import threading

if __name__ == "__main__":
    print("🚀 PixelOrchestrator Booting...")

    # run detector in background thread
    t = threading.Thread(target=start_detector, daemon=True)
    t.start()

    # run orchestrator in main thread
    orchestrator_main()
