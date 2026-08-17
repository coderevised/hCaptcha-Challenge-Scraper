import time
import random

class HcaptchaTelemetry:
    def __init__(self):
        self.flow_start = int(time.time() * 1000)
        self.checksiteconfig_time = None
        self.getcaptcha_time = None
        self.getcaptcha_start = None
        self.getcaptcha_end = None
        self.pointer_events = random.randint(8, 45)
        self.attempt_count = 0
        
    def record_checksiteconfig(self, duration_ms: float):
        self.checksiteconfig_time = duration_ms
        
    def record_getcaptcha(self, duration_ms: float):
        self.getcaptcha_time = duration_ms
        self.attempt_count += 1
        
    def get_pdc(self, request_type: str, solve_time_ms: int = None) -> dict:
        now = int(time.time() * 1000)
        if solve_time_ms is None:
            solve_time_ms = random.randint(2500, 12000)
            
        gcs = random.randint(50, 300)
        gce = gcs + random.randint(50, 250)
        l_time = gce + random.randint(1, 50)
        o_time = l_time + random.randint(10, 100)
        
        return {
            "s": now,
            "n": self.attempt_count,
            "p": self.pointer_events,
            "gcs": gcs,
            "gce": gce,
            "l": l_time,
            "t": request_type,
            "o": o_time,
            "c": solve_time_ms,
        }
        
    def get_pem(self, host: str = "api.hcaptcha.com") -> dict:
        csc = self.checksiteconfig_time or random.uniform(15.0, 80.0)
        gc = self.getcaptcha_time or random.uniform(80.0, 250.0)
        
        jitter_csc = random.uniform(-0.3, 0.3)
        jitter_gc = random.uniform(-0.5, 0.5)
        
        return {
            "csc": round(csc + jitter_csc, 15),
            "csch": host,
            "cscrt": 0,
            "cscft": round(csc + jitter_csc, 15),
            "gc": round(gc + jitter_gc, 15),
            "gch": host,
            "gcrt": 0,
            "gcft": round(gc + jitter_gc, 15),
        }