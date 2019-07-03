#!/usr/bin/python
# coding=utf-8
import time
import datetime

def get_last_midnight():
    today = datetime.date.today()
    mintime = datetime.time.min
    midnight = datetime.datetime.combine(today, mintime)
    return int(time.mktime(midnight.timetuple()))
    # return (int(time.time() // 86400)) * 86400

def get_last_monday():
    today = datetime.date.today()
    mon = today - datetime.timedelta(days=today.weekday())
    return int(time.mktime(mon.timetuple()))


def get_first_day_of_month():
    first_day_of_month = datetime.date.today().replace(day=1)
    return int(time.mktime(first_day_of_month.timetuple()))

def check_triggers_for_timestamp(trigger_ts):
    hform_date = datetime.date.fromtimestamp(trigger_ts)
    trigger_ts_day = hform_date.day
    trigger_ts_month = hform_date.month
    trigger_ts_week = hform_date.isocalendar()[1]
    return [trigger_ts_day, trigger_ts_week, trigger_ts_month]
