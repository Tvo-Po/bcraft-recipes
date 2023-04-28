import io
from pathlib import Path
from unittest import mock
from uuid import UUID, uuid4

from app.crud import image as crud
from app.util import generate_image


async def test_get_existing_image(asession, aclient, tmpdir):
    id = uuid4()
    img_path = tmpdir / f'{id.hex}.jpg'
    img_path.write('some bytes'.encode())
    original_filename = 'testimg.jpg'
    async with asession() as session:
        await crud.create_images(
            [
                {
                    'id': id,
                    'path': str(img_path),
                    'original_filename': original_filename,
                }
            ],
            session,
        )
    response = await aclient.get(f'/api/v1/images/{id}')
    assert response.status_code == 200


async def test_create_images(aclient, tmpdir):
    byt_imgs = [io.BytesIO() for _ in range(3)]
    [generate_image().save(b, format='jpeg') for b in byt_imgs]
    with mock.patch('app.api.image.dependency.save_image_to_media') as mock_save:
        mock_save.side_effect = [
            Path(tmpdir) / '1.jpg',
            Path(tmpdir) / '2.jpg',
            Path(tmpdir) / '3.jpg',
        ]
        response = await aclient.post(
            'api/v1/images/upload',
            files=[
                ('files', (f'{i}.jpeg', image, 'image/jpeg'))
                for i, image in enumerate(byt_imgs)
            ],
        )
    assert mock_save.call_count == 3
    assert response.status_code == 201
    json_response = response.json()
    assert len(json_response) == 3
    for i, item in enumerate(json_response):
        try:
            UUID(item['id'])
        except ValueError:
            assert False, 'id not uuid'
        assert item['original_filename'] == f'{i}.jpeg'


async def test_pass_invalid_images_to_create(aclient):
    not_images = ['corrupt'.encode() for _ in range(2)]
    response = await aclient.post(
        'api/v1/images/upload',
        files=[
            ('files', (f'{i}.xls', image, 'document/xls'))
            for i, image in enumerate(not_images)
        ],
    )
    json_response = response.json()
    assert response.status_code == 422
    assert json_response['detail'][0]['msg'] == '<0.xls> is not a valid image'
    assert json_response['detail'][1]['msg'] == '<1.xls> is not a valid image'
    assert (
        json_response['detail'][0]['type']
        == json_response['detail'][1]['type']
        == 'type_error.image'
    )
