from typing import List


class APIKeyManager:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.request_counts = {key: 0 for key in api_keys}
        self.failed_keys = set()
        self.max_requests_per_key = 50

    def get_current_key(self) -> str:
        return self.api_keys[self.current_index]

    def rotate_key(self):
        attempts = 0
        while attempts < len(self.api_keys):
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            current_key = self.get_current_key()
            if current_key not in self.failed_keys:
                return True
            attempts += 1
        return False

    def mark_key_failed(self):
        current_key = self.get_current_key()
        self.failed_keys.add(current_key)

    def increment_count(self):
        current_key = self.get_current_key()
        self.request_counts[current_key] += 1
        if self.request_counts[current_key] >= self.max_requests_per_key:
            self.rotate_key()
            self.request_counts[self.get_current_key()] = 0

    def has_available_keys(self) -> bool:
        return len(self.failed_keys) < len(self.api_keys)
