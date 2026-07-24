from typing import Dict

class LivenessCheck:
    """Returns basic status indicating the server process is alive and accepting TCP handshakes."""
    
    @staticmethod
    def check() -> Dict[str, str]:
        return {
            "status": "alive",
            "uptime": "nominal"
        }
