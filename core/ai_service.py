"""
AI Service Layer – Local LLM Integration for Device Detection, Flash Prediction, Error Diagnosis, and Chat Assistant
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
    """
    Local AI Service using Ollama (llama3.2:3b)
    Provides: Device Detection, Flash Prediction, Error Diagnosis, Chat Assistant
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model: str = "llama3.2:3b", api_url: str = "http://localhost:11434"):
        if self._initialized:
            return
        self._initialized = True
        
        self.model = model
        self.api_url = api_url
        self._available = self._check_availability()
        self._request_queue = Queue()
        self._response_queue = Queue()
        
        if self._available:
            # Start background worker for async requests
            self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._worker_thread.start()
            safe_logger.log(f"[AIService] Initialized with model: {model}")
        else:
            safe_logger.log(f"[AIService] Ollama not available. Install Ollama from https://ollama.com")
    
    def _check_availability(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            # Check if Ollama server is running
            response = requests.get(f"{self.api_url}/api/tags", timeout=2)
            if response.status_code != 200:
                return False
            
            # Check if model exists
            models = response.json().get("models", [])
            for m in models:
                if m.get("name", "").startswith(self.model):
                    return True
            
            safe_logger.log(f"[AIService] Model '{self.model}' not found. Run: ollama pull {self.model}")
            return False
        except Exception as e:
            safe_logger.log(f"[AIService] Ollama not available: {e}")
            return False
    
    def _query(self, prompt: str, timeout: int = 30) -> AIResponse:
        """Send prompt to AI model and get response."""
        import time
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                duration = time.time() - start_time
                return AIResponse(success=True, content=content, duration=duration)
            else:
                return AIResponse(success=False, content="", error=f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            return AIResponse(success=False, content="", error="Request timeout")
        except Exception as e:
            return AIResponse(success=False, content="", error=str(e))
    
    def _process_queue(self):
        """Background worker to process AI requests."""
        while True:
            try:
                request = self._request_queue.get(timeout=1)
                if request is None:
                    break
                
                prompt = request.get("prompt")
                callback = request.get("callback")
                result = self._query(prompt)
                
                if callback:
                    callback(result)
            except:
                pass
    
    def query_async(self, prompt: str, callback: Optional[callable] = None):
        """Send async query to AI."""
        if not self._available:
            if callback:
                callback(AIResponse(success=False, content="", error="Ollama not available"))
            return
        
        self._request_queue.put({"prompt": prompt, "callback": callback})
    
    def query_sync(self, prompt: str, timeout: int = 30) -> AIResponse:
        """Send sync query to AI."""
        if not self._available:
            return AIResponse(success=False, content="", error="Ollama not available")
        return self._query(prompt, timeout)
    
    # ========== AI FEATURES ==========
    
    def detect_device(self, adb_output: str) -> Dict[str, Any]:
        """Detect device model, chipset, Android version from ADB output."""
        prompt = f"""Analyze this ADB/fastboot device information and return ONLY a JSON object with:
- model: device model name
- chipset: processor/chipset name
- android_version: Android version number
- security_patch: security patch date if available
- codename: device codename if available

Device info:
{adb_output}

Return ONLY valid JSON. No explanation. Example: {{"model": "Pixel 7", "chipset": "Tensor G2", "android_version": "14"}}"""
        
        response = self.query_sync(prompt)
        if response.success:
            try:
                return json.loads(response.content)
            except:
                return {"model": "unknown", "chipset": "unknown", "android_version": "unknown", "error": response.content[:100]}
        return {"error": response.error}
    
    def predict_flash_success(self, device_model: str, firmware: str, battery: int = 80) -> Dict[str, Any]:
        """Predict flash success probability."""
        prompt = f"""Predict flash success probability for:
Device: {device_model}
Firmware: {firmware}
Battery: {battery}%

Return ONLY JSON with:
- success_probability: float between 0-1
- estimated_time: seconds
- risks: list of potential issues
- recommendations: list of suggestions

Example: {{"success_probability": 0.95, "estimated_time": 120, "risks": ["battery below 50%"], "recommendations": ["charge battery"]}}"""
        
        response = self.query_sync(prompt)
        if response.success:
            try:
                return json.loads(response.content)
            except:
                return {"success_probability": 0.5, "estimated_time": 60, "risks": ["unknown"], "recommendations": ["proceed with caution"]}
        return {"error": response.error}
    
    def diagnose_error(self, error_log: str, operation: str = "flash") -> Dict[str, Any]:
        """Diagnose error and suggest solutions."""
        prompt = f"""Diagnose this {operation} error and suggest solutions:

Error log:
{error_log}

Return ONLY JSON with:
- root_cause: main reason for failure
- error_type: (connection/timeout/partition/security/battery/unknown)
- severity: (high/medium/low)
- suggested_fixes: list of steps to fix
- confidence: float between 0-1

Example: {{"root_cause": "USB cable issue", "error_type": "connection", "severity": "medium", "suggested_fixes": ["change USB cable", "use USB 2.0 port"], "confidence": 0.85}}"""
        
        response = self.query_sync(prompt)
        if response.success:
            try:
                return json.loads(response.content)
            except:
                return {"root_cause": "unknown", "error_type": "unknown", "severity": "medium", "suggested_fixes": ["check device connection"], "confidence": 0.5}
        return {"error": response.error}
    
    def optimize_batch_order(self, devices: List[Dict]) -> List[str]:
        """Optimize batch flashing order."""
        devices_info = "\n".join([f"- {d.get('model', d.get('serial', 'unknown'))}" for d in devices])
        prompt = f"""Optimize the order of these devices for batch flashing to minimize total time:
{devices_info}

Consider: device type, priority, estimated flash time.

Return ONLY JSON array of device serials in optimal order.
Example: ["serial1", "serial2", "serial3"]"""
        
        response = self.query_sync(prompt)
        if response.success:
            try:
                result = json.loads(response.content)
                if isinstance(result, list):
                    return result
            except:
                pass
        return [d.get("serial", str(i)) for i, d in enumerate(devices)]
    
    def chat(self, user_message: str, context: str = "") -> str:
        """Chat assistant for device flashing help."""
        prompt = f"""You are an expert Android device flashing assistant. Help the user with their device flashing questions.

Context (current device info):
{context}

User question: {user_message}

Provide a helpful, concise, and accurate response. Focus on Android flashing, ADB, fastboot, bootloader, recovery, partitions, backups, and device-specific instructions."""
        
        response = self.query_sync(prompt, timeout=45)
        if response.success:
            return response.content
        return f"AI service error: {response.error}"
    
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self._available
    
    def get_models(self) -> List[str]:
        """Get available models."""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return [m.get("name", "") for m in response.json().get("models", [])]
        except:
            pass
        return []


# Global instance
ai_service = AIService()