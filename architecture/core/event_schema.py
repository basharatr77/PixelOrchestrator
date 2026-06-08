class EventSchema:
    @staticmethod
    def validate(event: dict):
        if "id" not in event:
            raise ValueError("Missing id")
        return True
