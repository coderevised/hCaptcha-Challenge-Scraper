import json
import hashlib
import base64
import time

def _decode_base64_url(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _check_proof(difficulty: int, candidate: str) -> bool:
    digest = hashlib.sha1(candidate.encode()).digest()
    bits = []
    for byte in digest:
        for i in range(8):
            bits.append((byte >> i) & 1)

    if bits[0] != 0:
        return False
    if difficulty <= 1:
        return True
    for i in range(1, difficulty - 1):
        if bits[i] != 0:
            return False
    return True


def solve_hsl_local(token: str) -> str:
    try:
        payload_b64 = token.split('.')[1]
        payload = json.loads(_decode_base64_url(payload_b64))
        difficulty = payload.get('s', 2)
        challenge_d = payload.get('d', '')
    except Exception as e:
        raise ValueError(f"Failed to decode hsl token: {e}")

    if not challenge_d:
        raise ValueError("hsl token missing 'd' field")

    charset = "0123456789/:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for length in range(25):
        def gen(prefix):
            if len(prefix) == length:
                candidate_suffix = ''.join(charset[i] for i in prefix)
                if _check_proof(difficulty, challenge_d + "::" + candidate_suffix):
                    return candidate_suffix
                return None
            for idx in range(len(charset)):
                res = gen(prefix + [idx])
                if res is not None:
                    return res
            return None

        solution = gen([])
        if solution is not None:
            timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            return f"1:{difficulty}:{timestamp}:{challenge_d}::{solution}"

    raise RuntimeError("Failed to find HSL proof within length limit")