import unittest
import re
from typing import Tuple, Iterator
from dataclasses import dataclass
import datetime
from collections import defaultdict

def line_reader():
    with open('time_parser_input_example.txt', 'r') as input_:
        for line in input_:
            yield line

@dataclass(frozen=True)
class Date:
    date: str

class Timedelta:
    _data: datetime.timedelta
    def __init__(self, hours = 0, minutes = 0, extra_hours = None):
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

    def __repr__(self):
        return f"Timedelta(hours={self.hours}, minutes={self.minutes}"
    

@dataclass(frozen=True)
class TimedeltaAtDate:
    date: Date
    timedelta: Timedelta

    def __repr__(self):
        return f"TimedeltaAtDate({repr(self.date)}, {repr(self.timedelta)})"

class TimedeltaAtDateFactory:
    def __new__(cls, line) -> TimedeltaAtDate:
        regex_date = "([a-zA-Z]+\s+[0-9]+)"
        regex_extra_thing = "(([0-9])\+)?"
        regex_hours = "([0-9]+)"
        regex_minutes = "([0-9]+)"

        regex = f"^\s*{regex_date}\s+\({regex_extra_thing}{regex_hours}:{regex_minutes}\)$"
        result = re.search(regex, line)

        return TimedeltaAtDate(
            date=Date(
                date=result.group(1),
            ),
            timedelta=Timedelta(
                hours=int(result.group(4)),
                minutes=int(result.group(5)),
                extra_hours=int(result.group(3)) if result.group(3) is not None else None,
            ),
        )

class AggregatedTimeIntoDays:
    def __init__(self):
        self._summed_timedelta = defaultdict(Timedelta)

    def __add__(self, other: TimedeltaAtDate):
        self._summed_timedelta[other.date] += other.timedelta
        return self

    def __iter__(self) -> Iterator[Tuple[datetime.date, datetime.timedelta]]:
        for date, time in self._summed_timedelta.items():
            yield date, time

class ActionAgregate:
    def __init__(self):
        self._aggregated_time_per_day = AggregatedTimeIntoDays()

    def run(self):
        for line in line_reader():
            parsed_datetime = TimedeltaAtDateFactory(line)
            self._aggregated_time_per_day += parsed_datetime
        return self

    @property
    def aggregated_time_per_day(self):
        return self._aggregated_time_per_day

def main():
    for date, time in ActionAgregate().run().aggregated_time_per_day:
        print(f"{date.date}: {time.hours}:{time.minutes}")

if __name__=="__main__":
    main()

# =====================+TESTING+=======================

class TestParser(unittest.TestCase):

    def test_file_reading(self):
        self.assertTrue(len(list([line for line in line_reader()])) > 0)
    
    def test_parse_line(self):
        parsed = TimedeltaAtDateFactory("Jul 2   (04:17)")
        self.assertEqual(parsed, TimedeltaAtDate(Date(date='Jul 2'), Timedelta(hours=4, minutes=17)))

    def test_parse_tricky_line(self):
        parsed = TimedeltaAtDateFactory("Jul 2   (1+12:44)")
        self.assertEqual(parsed, TimedeltaAtDate(Date(date='Jul 2'), Timedelta(hours=36, minutes=44)))

    def test_aggregator(self):
        aggregated_time_per_day = AggregatedTimeIntoDays()
        aggregated_time_per_day += TimedeltaAtDateFactory("Jul 2   (22:50)")
        aggregated_time_per_day += TimedeltaAtDateFactory("Jul 2   (22:50)")

        self.assertEqual(next(iter(aggregated_time_per_day)), (Date(date='Jul 2'), Timedelta(hours=45, minutes=40)))

    def test_how_to_treat_extra_number(self):
        # like extra 24 hours?
        aggregated_time_per_day = AggregatedTimeIntoDays()
        aggregated_time_per_day += TimedeltaAtDateFactory("Jul 2   (1+23:50)")
        self.assertEqual(next(iter(aggregated_time_per_day)), (Date(date='Jul 2'), Timedelta(hours=47, minutes=50)))

    def test_hashable_date_appears_once_in_storage(self):
        storage = {}

        storage[Date("Jul 2")] = 1
        storage[Date("Jul 2")] = 2

        self.assertEqual(len(storage.keys()), 1)

