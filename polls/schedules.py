# from __future__ import absolute_import, unicode_literals
# from polls.models import RedisIns, RunningInsTime
# import redis
# import schedule
# import time



# schedule.every().second.do(RedisWatch.get_redis_ins_qps(RunningInsTime.objects.all()))
#
# if __name__ == '__main__':
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(RedisWatch(, 'interval', seconds=1)
#     scheduler.start()
#     try:
#         scheduler.start()
#     except (KeyboardInterrupt, SystemExit):
#         pass
