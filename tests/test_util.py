import io
from pathlib import Path
from unittest import mock
from uuid import uuid4

from app import util


async def test_save_image_to_media(tmpdir):
    uuid = uuid4()
    saving_bytes = io.BytesIO('check'.encode())
    frmt = 'jpg'
    with mock.patch('app.util.settings') as mock_settings:
        media_path = mock.PropertyMock(return_value=Path(tmpdir))
        type(mock_settings).MEDIA_PATH = media_path
        saved_path = await util.save_image_to_media(uuid, saving_bytes, frmt)
    assert saved_path.suffix == '.' + frmt
    assert saved_path.stem == uuid.hex
    assert saved_path.read_bytes().decode() == 'check'
