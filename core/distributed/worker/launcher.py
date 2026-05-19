import sys
import argparse
from core.distributed.worker.agent import start_worker

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Unique worker ID")
    parser.add_argument("--master", required=True, help="Master WebSocket URL (ws://...:8765)")
    parser.add_argument("--secret", default="", help="Shared secret")
    args = parser.parse_args()
    start_worker(args.id, args.master, args.secret)