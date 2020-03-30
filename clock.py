from apscheduler.schedulers.blocking import BlockingScheduler
import bot

twische = BlockingScheduler()

@twische.scheduled_job('interval',minutes=15)
def timed_job():
    bot.tweet()

if __name__ == "__main__":
    twische.start()
