"""Explicitly gated adapter for an authorized Riley challenge endpoint."""
import json
import time
import urllib.parse
import urllib.request


class RileyAdapter:
    def __init__(self, *, endpoint, approved, allowed_host, max_requests, min_interval_seconds,
                 participant, team_token, api_key, model):
        parsed = urllib.parse.urlparse(endpoint)
        if not approved:
            raise PermissionError("Track C requires explicit user approval")
        if parsed.scheme != "https" or parsed.hostname != allowed_host or not parsed.hostname:
            raise ValueError("Endpoint must be an approved HTTPS host")
        if not 0 < max_requests <= 20 or min_interval_seconds < 1:
            raise ValueError("Invalid bounded execution limits")
        self.endpoint = endpoint.rstrip("/")
        self.participant, self.team_token, self.api_key, self.model = participant, team_token, api_key, model
        self.remaining = max_requests
        self.interval = min_interval_seconds
        self.last = 0.0

    def chat(self, message, conversation_id):
        if self.remaining <= 0:
            raise RuntimeError("Request cap reached")
        if not isinstance(message, str) or len(message) > 2000:
            raise ValueError("Synthetic message must be at most 2000 characters")
        delay = self.interval - (time.monotonic() - self.last)
        if delay > 0:
            time.sleep(delay)
        body = {"participant": self.participant, "team_token": self.team_token,
                "model": self.model, "conversation_id": conversation_id, "message": message}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        request = urllib.request.Request(self.endpoint + "/chat", data=json.dumps(body).encode(), headers=headers)
        self.remaining -= 1
        self.last = time.monotonic()
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
        # Never return the authenticated request, credentials, or unrestricted response metadata.
        return {"reply": data.get("reply"), "tool_calls": data.get("tool_calls"), "turn_id": data.get("turn_id")}
