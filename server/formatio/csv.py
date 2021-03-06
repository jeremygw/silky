
import csv
from silky import MeasureType


def calc_dps(value, max_dp=3):
    max_dp_required = 0
    value %= 1
    as_string = '{v:.{dp}f}'.format(v=value, dp=max_dp)
    as_string = as_string[2:]

    for dp in range(max_dp, 0, -1):
        index = dp - 1
        if as_string[index] != '0':
            max_dp_required = dp
            break

    return max_dp_required


def fix_names(names):
    for i in range(1, len(names)):
        name = names[i]
        names_used = names[:i - 1]
        orig_name = name
        c = 1
        while name in names_used:
            c += 1
            name = orig_name + ' (' + str(c) + ')'
        names[i] = name
    return names


def read(dataset, path):

    with open(path) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(4096))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)

        itr = reader.__iter__()
        column_names = itr.__next__()

        column_count = 0
        column_writers = [ ]

        column_names = fix_names(column_names)

        for i in range(len(column_names)):
            column_name = column_names[i]
            dataset.append_column(column_name)
            column = dataset[i]
            column_writers.append(ColumnWriter(column, i))
            column_count += 1

        rowCount = 0

        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        first = True

        for row in reader:
            if first:
                first = False
            else:
                dataset.append_row()

                for i in range(column_count):
                    column_writers[i].examine_row(row)

                rowCount += 1

        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        first = True

        row_no = 0

        for row in reader:
            if first:
                first = False
            else:
                for i in range(column_count):
                    column_writers[i].parse_row(row, row_no)
                row_no += 1

    return dataset


class ColumnWriter:
    def __init__(self, column, column_index):
        self._column = column
        self._column_index = column_index

        self._only_integers = True
        self._only_floats = True
        self._is_empty = True
        self._unique_values = set()
        self._many_uniques = False
        self._measure_type = None
        self._examination_complete = False
        self._dps = 0

    def examine_row(self, row):

        if self._examination_complete:
            return

        if self._column_index >= len(row):
            return

        value = row[self._column_index]

        if value == "" or value == " ":
            return
        else:
            self._is_empty = False

        if self._many_uniques is False:
            if len(self._unique_values) >= 49:
                self._many_uniques = True
                self._unique_values.clear()
            else:
                self._unique_values.add(value)

        if self._only_integers:
            try:
                i = int(value)
                if i > 2147483647 or i < -2147483647:
                    self._only_integers = False
            except ValueError:
                self._only_integers = False

        if self._only_floats:
            try:
                f = float(value)
                self._dps = max(self._dps, calc_dps(f))
            except ValueError:
                self._only_floats = False

        if self._many_uniques and self._only_floats is False and self._only_integers is False:
            self._measure_type = MeasureType.MISC
            self._unique_values = None
            self._examination_complete = True

    def _ruminate(self):

        if self._measure_type is None:
            if self._only_integers and self._many_uniques is False:
                self._measure_type = MeasureType.NOMINAL
                self._unique_values = list(self._unique_values)
                self._unique_values.sort()
                for label in self._unique_values:
                    self._column.add_label(int(label), label)

            elif self._only_floats:
                self._measure_type = MeasureType.CONTINUOUS
            elif self._many_uniques:
                self._measure_type = MeasureType.MISC
            else:
                self._measure_type = MeasureType.NOMINAL_TEXT
                self._unique_values = list(self._unique_values)
                self._unique_values.sort()
                for i in range(0, len(self._unique_values)):
                    label = self._unique_values[i]
                    self._column.add_label(i, label)

        self._examination_complete = True
        self._column.type = self._measure_type
        self._column.dps = self._dps

    def parse_row(self, row, row_no):

        if self._examination_complete is False:
            self._ruminate()

        if self._column_index >= len(row):
            value = None
        else:
            value = row[self._column_index]

            if value == '' or value == ' ':
                value = None

        if self._measure_type == MeasureType.NOMINAL or self._measure_type == MeasureType.ORDINAL:
            if value is None:
                self._column[row_no] = -2147483648
            else:
                self._column[row_no] = int(value)

        elif self._measure_type == MeasureType.CONTINUOUS:
            if value is None:
                self._column[row_no] = float('nan')
            else:
                self._column[row_no] = float(value)

        elif self._measure_type == MeasureType.NOMINAL_TEXT:

            if value is None:
                self._column[row_no] = -2147483648
            else:
                self._column[row_no] = self._unique_values.index(value)

        else:
            self._column[row_no] = -2147483648
