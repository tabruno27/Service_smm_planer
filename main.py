from scr.scheduler import process_schedule
from environs import Env

def main():
    env = Env()
    env.read_env(path='token.env')
    VK_TOKEN = env.str("VK_TOKEN")
    TELEGRAM_TOKEN = env.str("TELEGRAM_TOKEN")
    VK_GROUP_ID = env.int("VK_GROUP_ID")
    TELEGRAM_CHANNEL_ID = env.str("TELEGRAM_CHANNEL_ID")
    process_schedule(VK_TOKEN, TELEGRAM_TOKEN, VK_GROUP_ID, TELEGRAM_CHANNEL_ID)


if __name__ == "__main__":
    main()
