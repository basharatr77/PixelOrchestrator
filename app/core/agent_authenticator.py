"""Environment-configured authentication for remote agents."""

import hmac
import json
import os


class ConfiguredAgentAuthenticator:
    """Authenticate known agents using environment-configured bearer tokens."""

    ENV_NAME = "PIXEL_ORCHESTRATOR_AGENT_TOKENS"

    def __init__(self, tokens):
        if not isinstance(tokens, dict):
            raise ValueError("Agent tokens must be a JSON object.")

        validated = {}
        for agent_id, token in tokens.items():
            if (
                not isinstance(agent_id, str)
                or not agent_id.strip()
                or not isinstance(token, str)
                or not token.strip()
            ):
                raise ValueError("Agent IDs and tokens must be non-empty strings.")
            validated[agent_id] = token

        self._tokens = validated

    @classmethod
    def from_environment(cls):
        raw = os.environ.get(cls.ENV_NAME)
        if raw is None or not raw.strip():
            return cls({})

        try:
            tokens = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{cls.ENV_NAME} must contain valid JSON."
            ) from exc

        return cls(tokens)

    def authenticate(self, agent_id, data):
        if not isinstance(agent_id, str) or not isinstance(data, dict):
            return False

        expected = self._tokens.get(agent_id)
        supplied = data.get("token")

        if not isinstance(expected, str) or not isinstance(supplied, str):
            return False

        return hmac.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8"))
