class EventSchema:
    REQUIRED_KEYS = {"type", "data"}

    @staticmethod
    def validate(event):
        if not isinstance(event, dict):
            return False, "Event must be dict"

        missing = EventSchema.REQUIRED_KEYS - set(event.keys())
        if missing:
            return False, f"Missing keys: {missing}"

        if "data" in event and not isinstance(event["data"], dict):
            return False, "data must be dict"

        return True, "OK"
