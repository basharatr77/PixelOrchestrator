import pytest

from app.core.transport import Transport


class IncompleteTransport(Transport):
    pass


class CompleteTransport(Transport):
    def connect(self):
        return True

    def disconnect(self):
        return True

    def is_connected(self):
        return True

    def execute(self, command):
        return command

    def get_device_info(self):
        return {}


def test_transport_is_abstract():
    with pytest.raises(TypeError):
        IncompleteTransport()


def test_complete_transport_can_be_instantiated():
    transport = CompleteTransport()

    assert transport.connect() is True
    assert transport.disconnect() is True
    assert transport.is_connected() is True
    assert transport.execute("test") == "test"
    assert transport.get_device_info() == {}
