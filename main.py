from environs import Env
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone

from scr.scheduler import scan_sheet

def load_env():
    env = Env()
    env.read_env(path="token.env")
    return {
        "vk_token": env.str("VK_TOKEN"),
        "telegram_token": env.str("TELEGRAM_TOKEN"),
        "vk_group_id": env.int("VK_GROUP_ID"),
        "telegram_channel_id": env.str("TELEGRAM_CHANNEL_ID"),
        "ok_app_key": env.str("OK_APPLICATION_KEY"),
        "ok_access_token": env.str("OK_ACCESS_TOKEN")
    }

def main() -> None:
    cfg = load_env()

    scheduler = BlockingScheduler(timezone=timezone("UTC"))

    # каждую минуту в 0 секунд
    scheduler.add_job(
        scan_sheet,
        "cron",
        minute="*",
        second=0,
        id="scan_sheet",
        args=[
            cfg["vk_token"],
            cfg["telegram_token"],
            cfg["vk_group_id"],
            cfg["telegram_channel_id"],
            cfg["ok_app_key"],
            cfg["ok_access_token"]
        ],
        max_instances=1,   # не пускать второй экземпляр, если первый ещё работает
        misfire_grace_time=30,  # если пропустили — выполнить в течение 30 с
    )

    print("Scheduler started — Ctrl-C to exit")
    scheduler.start()

if __name__ == "__main__":
    main()