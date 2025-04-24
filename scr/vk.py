import vk_api


def post_to_vk(vk_token, group_id: int, message: str, image_url: str | None = None):
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()

    attachments = image_url or ""

    try:
        vk.wall.post(owner_id=-group_id, message=message, attachments=attachments)
        print(f"Message posted to VK group {group_id}")
    except vk_api.exceptions.ApiError as e:
        print(f"An error occurred while posting to VK: {e}")
