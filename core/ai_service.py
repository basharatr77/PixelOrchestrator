"""
AI Service Layer – Local LLM Integration (TinyLlama / Phi)
"""

import json
import requests
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from queue import Queue

from core.safe_logger import safe_logger

@dataclass
class AIResponse:
    success: bool
    content: str
    error: Optional[str] = None
    duration: float = 0

class AIService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model: str = "tinyllama", api_url: str = "http://localhost:11434"):
        if self._initialized:
            return
        self._initialized = True
        self.model = model
        self.api_url = api_url
        self._available = self._check_availability()
        self._request_queue = Queue()
        if self._available:
            self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._worker_thread.start()
            safe_logger.log(f"[AIService] Initialized with model: {model}")
        else:
            safe_logger.log(f"[AIService] Ollama not available. Install Ollama from https://ollama.com")
    
    def _check_availability(self) -> bool:
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=2)
            if response.status_code != 200:
                return False
            models = response.json().get("models", [])
            for m in models:
                if m.get("name", "").startswith(self.model):
                    return True
            safe_logger.log(f"[AIService] Model '{self.model}' not found. Run: ollama pull {self.model}")
            return False
        except Exception as e:
            safe_logger.log(f"[AIService] Ollama not available: {e}")
            return False
    
    def _query(self, prompt: str, timeout: int = 180) -> AIResponse:
        import time
        start = time.time()
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.3}},
                timeout=timeout
            )
            if response.status_code == 200:
                content = response.json().get("response", "")
                return AIResponse(success=True, content=content, duration=time.time()-start)
            else:
                return AIResponse(success=False, content="", error=f"HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            return AIResponse(success=False, content="", error="Timeout")
        except Exception as e:
            return AIResponse(success=False, content="", error=str(e))
    
    def _process_queue(self):
        while True:
            try:
                req = self._request_queue.get(timeout=1)
                if req is None: break
                result = self._query(req["prompt"], timeout=180)
                if req.get("callback"):
                    req["callback"](result)
            except:
                pass
    
    def query_sync(self, prompt: str, timeout: int = 180) -> AIResponse:
        if not self._available:
            return AIResponse(success=False, content="", error="Ollama not available")
        return self._query(prompt, timeout)
    
    def chat(self, user_message: str, context: str = "") -> str:
        prompt = f"You are an Android flashing expert. Answer concisely.\nContext: {context}\nUser: {user_message}\nAI:"
        response = self.query_sync(prompt, timeout=180)
        if response.success:
            return response.content
        return f"AI error: {response.error}"
    
    def is_available(self) -> bool:
        return self._available

ai_service = AIService()