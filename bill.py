import csv
import datetime
import os

class Entry:
    """A class for holding data from each row in a bill."""
    def __init__(self, row):
        """
        :param collections.OrderedDict row: Data stored in an OrderedDict
        """
        self.data = row

    @property
    def total(self):
        """Some line items will have a their total cost associated with the date while some have it under TotalCost."""
        today = str(datetime.date.today())
        t = self.data[today] if today in self.data else self.data['TotalCost']
        return float(t) if t else 0.0

    @property
    def id(self):
        return self.data['RecordID']

    @property
    def account(self):
        return self.data['LinkedAccountName']

    @property
    def service(self):
        return self.data['ProductCode']

    @property
    def owner(self):
        return self.data['user:Owner'] if self.data['user:Owner'] and not self.data['user:Owner'][:2] == 'i-' else 'No Owner'

    @property
    def region(self):
        return self.data['AvailabilityZone']

    def add(self, key, value, last=True):
        """
        Add an column to the entry.

        Data is stored in a collections.OrderedDict. By default new entries are moved to the end.

        :param key: The key to be associated with the value
        :param value: The value to be associated with the key.
        :param last: A bool indicating that the value should be added to the end. Otherwise its added to the front.
        :return:
        """
        self.data.update({key: value})
        self.data.move_to_end(key, last)


class Bill:
    """A class for managing daily aws-cost-allocation bills."""
    def __init__(self, sources=None):
        """
        Create a new bill from a given source.

        :param sources: A path to a .csv, a Bill or a list of Bill objects to be merged.
        """
        self.entries = dict()
        self.field_names = list()

        if isinstance(sources, str):
            self.importCSV(sources)
        elif isinstance(sources, Bill):
            self.merge(sources)
        elif isinstance(sources, list):
            for bill in sources:
                self.merge(bill)


    # return the data as a multilayered nested dictionary sorted by the given categories
    # categories is a list of Category objects, e.g. [services, usernames, accounts]
    # layers of the dictionary are in the order given in the list of categories
    def sort(self, categories):
        if len(categories) == 0:
            return self  # base case

        else:
            output = {name: {} for name in categories[0].items}
            for name in output:
                rowsToAdd = {}
                for key, row in self.items():
                    if row[categories[0].csvColumn] == name:
                        rowsToAdd[key] = row
                output[name] = sort(rowsToAdd, categories[1:])  #
            return output


    def filter(self, owners=None, services=None, accounts=None, regions=None, max=None, min=None):
        """
        Create a new Bill object that only includes specific entries.

        :param List owners: The owner's username to be included in the new Bill. (As specified by the 'user:Owner' entry in the .csv)
        :param List services: The services to be included in the new Bill. (As specified by the 'ProductCode' entry in the .csv)
        :param List accounts: The accounts to be included in the new Bill. (As specified by the 'LinkedAccounts' entry in the .csv)
        :param List regions: The regions to be included in the new Bill. (As specified by the 'AvailabilityZone' entry in the .csv)
        :param max: The maximum cost to be included in the new Bill. (As specified by the 'TotalCost' entry in the .csv)
        :param min: The minimum cost to be included in the new Bill. (As specified by the 'TotalCost' entry in the .csv)
        :return: A new Bill object that contains entries from this instances that match given criteria.
        """
        b = Bill()
        b.entries = self.entries
        b.field_names = self.field_names

        if owners:
            b.entries = {e.id: e for e in b.entries.values() if e.owner in owners}
        if services:
            b.entries = {e.id: e for e in b.entries.values() if e.service in services}
        if accounts:
            b.entries = {e.id: e for e in b.entries.values() if e.account in accounts}
        if regions:
            b.entries = {e.id: e for e in b.entries.values() if e.region in regions}
        if max:
            b.entries = {e.id: e for e in b.entries.values() if e.total < max}
        if min:
            b.entries = {e.id: e for e in b.entries.values() if e.total > min}

        return b

    def merge(self, other_bill):
        """
        Merge this bill with another Bill object.

        The actual functionality of this function has yet to be decided. My initial thoughts are:
            Each line item in the bill has a unique 'RecordID'. To merge a Bill A into Bill B is to take every row in A not
            in B, identified by its RecordID, and put it into B.

        Not sure if this should be a class method that creates a new Bill or modifies the bill calling it.

        :param other_bill: Another Bill object.
        """
        pass

    def export(self, path):
        """
        Exports the data contained in this Bill to a .csv

        All of the entries in the bill generated by AWS are surrounded by "". These must be added for consistency
        between .csvs exported by the class and .csvs from Amazon.

        :param path: The location where the .csv will be exported to.
        """
        with open(path, 'w') as f:
            quoted_headers = ['"{}"'.format(h) for h in self.field_names]  # Preserve AWS's convention of surrounding everything in quotes.
            f.write(','.join(quoted_headers) + '\n')
            for entry in self.entries.values():
                line = ','.join(['"{}"'.format(v) for v in entry.data.values()])
                f.write(line + '\n')

    def importCSV(self, path):
        """
        Overwrite currently stored data with data from a .csv

        The .csvs generated by AWS have a message at the beginning of them. However, .csv exported by this class do not
        have this message.

        :param path: The path to the source .csv
        """
        with open(path, 'r') as f:
            first_line = f.readline().rstrip('\n')

            if first_line.startswith('"Don\'t see your'):  # AWS generated bills have a message in them, throw it away.
                reader = csv.DictReader(f)
                self.field_names = reader.fieldnames
            else:  # It is the header.
                headers = first_line.split(',')
                self.field_names = [h.strip('"') for h in headers]
                reader = csv.DictReader(f, self.field_names)

            for row in reader:
                e = Entry(row)
                self.entries.update({e.id: e})

    def total(self, owners=None, services=None, accounts=None, regions=None):
        """
        Find the total cost spent given a subset of owners, service, and accounts.

        :param List owners: The owner's username to be included in the new Bill. (As specified by the 'user:Owner' entry in the .csv)
        :param List services: The services to be included in the new Bill. (As specified by the 'ProductCode' entry in the .csv)
        :param List accounts: The accounts to be included in the new Bill. (As specified by the 'LinkedAccounts' entry in the .csv)
        :param List regions: The regions to be included in the new Bill. (As specified by the 'AvailabilityZone' entry in the .csv)
        :return: The sum of the totals given the specified subsets.
        """
        subset = self.filter(owners, services, accounts, regions)
        return sum([entry.total for entry in subset.entries.values()])

    @property
    def services(self):
        return {entry.service for entry in self.entries.values()}

    @property
    def owners(self):
        return {entry.owner for entry in self.entries.values()}

    @property
    def accounts(self):
        return {entry.account for entry in self.entries.values()}


class HistoricalBill(Bill):
    """
    A class for managing historical data from AWS bills.

    Explain RecordIDs.
    Historical data tracks how costs for given RecordIDs change over a month.
    """
    def updateTotals(self, source):
        """
        Add the new running total to the end of each row.
        :param source: A source to grab totals from. Currently only from a .csv or
        """
        today = str(datetime.date.today())
        self.field_names.append(today)

        if isinstance(source, str):
            if os.path.exists(source) and os.path.splitext(source)[1] == '.csv':
                self.update_totals_from_csv(source, today)
            else:
                print('{} does not exist.'.format(source))
        elif isinstance(source, Bill):
            self.update_totals_from_bill(source, today)
        else:
            print('Cannot update this HistoricalBill\'s totals from an object of type {}'.format(type(source)))

    def update_totals_from_bill(self, bill, date):
        """
        Update self.entries after appending them with new totals, from a Bill object, for a given date.

        :param bill: A Bill whos daily totals should be added to the historical tally.
        :param date: The date that the totals should be associated with.
        """
        for e in bill.entries.values():
            if e.id in self.entries:
                self.entries[e.id].add(date, e.total)
            else:
                historical_entry = e
                historical_entry.add(date, e.total)
                self.entries.update({e.id: historical_entry})

    def update_totals_from_csv(self, path, date):
        """
        Update self.entries after appending them with new totals, from a .csv, for a given date.

        :param path: The path to the .csv with totals from the date given by date.'
        :param date: The date that the totals should be associated with.
        """
        with open(path, 'r') as f:
            first_line = f.readline().rstrip('\n')

            if first_line.startswith('"Don\'t see your'):  # AWS generated bills have a message in them, throw it away.
                reader = csv.DictReader(f)
                self.field_names = reader.fieldnames
            else:  # It is the header.
                headers = first_line.split(',')
                self.field_names = [h.strip('"') for h in headers]
                reader = csv.DictReader(f, self.field_names)

            for row in reader:
                e = Entry(row)
                self.entries[e.id].add(date, e.total)


newbill = Bill("filterTest.csv")
print(newbill)
print(newbill.sort())