import unittest
import re
from typing import Tuple, Iterator
from dataclasses import dataclass
import datetime

def line_reader():
    with open('time_parser_input_example.txt', 'r') as input_:
        for line in input_:
            yield line

@dataclass(frozen=True)
class Date:
    month: int
    day: int

class Timedelta:
    _data: datetime.timedelta
    def __init__(self, hours, minutes, extra_hours = None):
        hours = hours
        if extra_hours:
            hours += 24

        self._data =  datetime.timedelta(
            hours=hours,
            minutes=minutes,
        )

    @property
    def hours(self):
        return int(self._data.total_seconds() / 3600)

    @property
    def minutes(self):
        return int(self._data.total_seconds() / 60) - self.hours * 60

    def __add__(self, other):
        self._data += other._data
        return self

    def __eq__(self, other):
        return (self.hours, self.minutes) == (other.hours, other.minutes)

    def __repr__(self):
        return f"Timedelta(hours={self.hours}, minutes={self.minutes}"
    

@dataclass(frozen=True)
class ParsedDatetime:
    date: Date
    time: Timedelta

    def __repr__(self):
        return f"ParsedDatetime({repr(self.date)}, {repr(self.time)})"

class ParsedDatetimeFactory:
    def __new__(cls, line) -> ParsedDatetime:
        regex_month = "([a-zA-Z]+)"
        regex_day = "([0-9]+)"
        regex_extra_thing = "(([0-9])\+)?"
        regex_hours = "([0-9]+)"
        regex_minutes = "([0-9]+)"

        regex = f"^\s*{regex_month}\s+{regex_day}\s+\({regex_extra_thing}{regex_hours}:{regex_minutes}\)$"
        result = re.search(regex, line)

        return ParsedDatetime(
            date=Date(
                month=result.group(1),
                day=int(result.group(2)),
            ),
            time=Timedelta(
                hours=int(result.group(5)),
                minutes=int(result.group(6)),
                extra_hours=int(result.group(4)) if result.group(4) is not None else None,
            ),
        )

class AggregatedTimeIntoDays:
    def __init__(self):
        self._storage = {}

    def add(self, parsed_datetime: ParsedDatetime):
        key = parsed_datetime.date
        self._init_in_storage_if_not_exists(key)

        self._storage[key] = self._sum_new_and_previous_time(
            previous_time = self._storage[key],
            newtime = parsed_datetime.time,
        )
    
    def _init_in_storage_if_not_exists(self, key):
        if key not in self._storage:
            self._storage[key] = Timedelta(hours=0, minutes=0)

    def _sum_new_and_previous_time(self, previous_time: Timedelta, newtime: Timedelta):
        return previous_time + newtime

    def __iter__(self) -> Iterator[Tuple[datetime.date, datetime.timedelta]]:
        for date, time in self._storage.items():
            yield date, time

class ActionAgregate:
    def __init__(self):
        self._aggregated_time_per_day = AggregatedTimeIntoDays()

    def run(self):
        for line in line_reader():
            parsed_datetime = ParsedDatetimeFactory(line)
            self._aggregated_time_per_day.add(parsed_datetime)
        return self

    @property
    def aggregated_time_per_day(self):
        return self._aggregated_time_per_day

def main():
    for date, time in ActionAgregate().run().aggregated_time_per_day:
        print(f"{date.month} {date.day}: {time.hours}:{time.minutes}")

if __name__=="__main__":
    main()

# =====================+TESTING+=======================

class TestParser(unittest.TestCase):

    def test_file_reading(self):
        self.assertTrue(len(list([line for line in line_reader()])) > 0)
    
    def test_parse_line(self):
        parsed = ParsedDatetimeFactory("Jul 2   (04:17)")
        self.assertEqual(repr(parsed), "ParsedDatetime(Date(month='Jul', day=2), Timedelta(hours=4, minutes=17)") 

    def test_parse_tricky_line(self):
        parsed = ParsedDatetimeFactory("Jul 2   (1+12:44)")
        self.assertEqual(repr(parsed), "ParsedDatetime(Date(month='Jul', day=2), Timedelta(hours=36, minutes=44)") 

    def test_aggregator(self):
        aggregated_time_per_day = AggregatedTimeIntoDays()
        aggregated_time_per_day.add(ParsedDatetimeFactory("Jul 2   (22:50)"))
        aggregated_time_per_day.add(ParsedDatetimeFactory("Jul 2   (22:50)"))

        self.assertEqual(next(iter(aggregated_time_per_day)), (Date(month='Jul', day=2), Timedelta(hours=45, minutes=40)))

    def test_how_to_treat_extra_number(self):
        # like extra 24 hours?
        aggregated_time_per_day = AggregatedTimeIntoDays()
        aggregated_time_per_day.add(ParsedDatetimeFactory("Jul 2   (1+23:50)"))
        self.assertEqual(next(iter(aggregated_time_per_day)), (Date(month='Jul', day=2), Timedelta(hours=47, minutes=50)))

    def test_hashable_date(self):
        storage = {}

        storage[Date(0, 0)] = 1
        storage[Date(0, 0)] = 2

        self.assertEqual(len(storage.keys()), 1)

