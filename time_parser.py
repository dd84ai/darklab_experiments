import unittest
import re
from typing import Tuple, Iterator
from dataclasses import dataclass

def line_reader():
    with open('time_parser_input_example.txt', 'r') as input_:
        for line in input_:
            yield line

@dataclass(frozen=True)
class ParsedDatetime:
    month: str
    day: int
    extra_number: int | None
    hours: int
    minutes: int


def parse_line(line) -> 'ParsedDatetime':
    regex_month = "([a-zA-Z]+)"
    regex_day = "([0-9]+)"
    regex_extra_thing = "(([0-9])\+)?"
    regex_hours = "([0-9]+)"
    regex_minutes = "([0-9]+)"

    regex = f"^\s*{regex_month}\s+{regex_day}\s+\({regex_extra_thing}{regex_hours}:{regex_minutes}\)$"
    result = re.search(regex, line)
    
    return ParsedDatetime(
        month=result.group(1),
        day=int(result.group(2)),
        extra_number=int(result.group(4)) if result.group(4) is not None else None,
        hours=int(result.group(5)),
        minutes=int(result.group(6)),
    )

def get_key(parsed_datetime: ParsedDatetime):
    return f"{parsed_datetime.month} {parsed_datetime.day}"

@dataclass(frozen=True)
class Time:
    hours: int
    minutes: int

@dataclass(frozen=True)
class Date:
    month: int
    day: int


class AggregatedTimeIntoDays:
    def __init__(self):
        self._storage = {}

    def add(self, parsed_datetime: ParsedDatetime):
        key = self._get_key(parsed_datetime)

        self._init_in_storage_if_not_exists(key)

        self._storage[key] = self._sum_new_and_previous_time(
            previous_time = self._storage[key],
            extra_thing = parsed_datetime.extra_number,
            new_hours = parsed_datetime.hours,
            new_minutes = parsed_datetime.minutes
        )

    @staticmethod
    def _get_key(parsed_datetime):
        return Date(parsed_datetime.month, parsed_datetime.day)
    
    def _init_in_storage_if_not_exists(self, key):
        if key not in self._storage:
            self._storage[key] = Time(hours=0, minutes=0)

    def _sum_new_and_previous_time(self, previous_time, extra_thing, new_hours, new_minutes):
        bonus_time = 24 if extra_thing is not None else 0
        summed_hours = previous_time.hours + new_hours + bonus_time
        summed_minutes = previous_time.minutes + new_minutes
        return Time(
            hours = summed_hours + int(summed_minutes / 60),
            minutes= summed_minutes % 60,
        )

    def __iter__(self) -> Iterator[Tuple[Date, Time]]:
        for date, time in self._storage.items():
            yield date, time

def main():
    aggregated_time_per_day = AggregatedTimeIntoDays()
    for line in line_reader():
        parsed_datetime = parse_line(line)
        aggregated_time_per_day.add(parsed_datetime)

    for date, time in aggregated_time_per_day:
        print(f"{date.month} {date.day}: {time.hours}:{time.minutes}")


if __name__=="__main__":
    main()

# =====================+TESTING+=======================

class TestParser(unittest.TestCase):

    def test_file_reading(self):
        self.assertTrue(len(list([line for line in line_reader()])) > 0)
    
    def test_parse_line(self):
        parsed = parse_line("Jul 2   (04:17)")
        self.assertEqual(parsed, ParsedDatetime(month='Jul', day=2, extra_number=None, hours=4, minutes=17)) 

    def test_parse_tricky_line(self):
        parsed = parse_line("Jul 2   (1+12:44)")
        self.assertEqual(parsed, ParsedDatetime(month='Jul', day=2, extra_number=1, hours=12, minutes=44)) 

    def test_aggregator(self):
        aggregated_time_per_day = AggregatedTimeIntoDays()
        aggregated_time_per_day.add(ParsedDatetime("Jul", 2, None, 22, 50))
        aggregated_time_per_day.add(ParsedDatetime("Jul", 2, None, 22, 50))

        self.assertEqual(next(iter(aggregated_time_per_day)), (Date(month='Jul', day=2), Time(hours=45, minutes=40)))

    def test_how_to_treat_extra_number(self):
        # like extra 24 hours?
        aggregated_time_per_day = AggregatedTimeIntoDays()
        aggregated_time_per_day.add(ParsedDatetime("Jul", 2, 1, 23, 50))
        self.assertEqual(next(iter(aggregated_time_per_day)), (Date(month='Jul', day=2), Time(hours=47, minutes=50)))

