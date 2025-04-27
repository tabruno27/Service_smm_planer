import requests
from typing import Optional

def post_to_ok(
    app_key: str,
    access_token: str,
    group_id: str,
    message: str,
    image_url: Optional[str] = None
) -> None:
    """Публикует пост в Одноклассниках с текстом и изображением."""
    
    # Загрузка изображения
    photo_id = None
    if image_url:
        # Получаем URL для загрузки фото
        upload_url_params = {
            "method": "photosV2.getUploadUrl",
            "access_token": access_token,
            "application_key": app_key,
            "gid": group_id,
            "format": "json"
        }

        upload_url_response = requests.post("https://api.ok.ru/fb.do", data=upload_url_params)
        if upload_url_response.status_code != 200:
            raise Exception(f"Ошибка при получении URL для загрузки фото: {upload_url_response.text}")
        upload_url = upload_url_response.json().get("upload_url")
        if not upload_url:
            raise Exception("Не удалось получить URL для загрузки фото")

        # Загружаем изображение
        try:
            image_data = requests.get(image_url).content
            files = {'file': ('image.jpg', image_data)}
            upload_response = requests.post(upload_url, files=files)
            upload_result = upload_response.json()

            if 'photos' in upload_result:
                photo_data = next(iter(upload_result['photos'].values()))
                photo_id = photo_data['token']
            else:
                raise Exception(f"Ошибка при загрузке фото: {upload_result}")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке изображения: {e}")

    # Подготовка вложений
    attachments = {"media": []}
    attachments["media"].append({"type": "text", "text": message})

    if photo_id:
        attachments["media"].append({"type": "photo", "list": [{"id": photo_id}]})

    # Публикация поста
    params = {
        "method": "mediatopic.post",
        "gid": group_id,
        "type": "GROUP_THEME",
        "attachment": str(attachments).replace("'", '"'),
        "access_token": access_token,
        "application_key": app_key,
        "format": "json"
    }

    response = requests.post("https://api.ok.ru/fb.do", data=params)
    if response.status_code != 200:
        raise Exception(f"Ошибка при публикации поста: {response.text}")

    print(f"Message posted to OK group {group_id}")