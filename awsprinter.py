from collections import OrderedDict
import copy
import re
from bill import Bill


"""
things to fix:
- combine synonymous usernames e.g. Lon and lblauvel
- have consistent column sizing
- more flexibility in output format
- 
- remove empty entries at the top
"""

""" a category by which to search a bill """
class Category:
    csvColumn = "" # the name of the column in the bill file, e.g. "user:Owner"
    items = [] # the names in that column to search for

    def __init__(self, bill, name, items=[]):
        self.csvColumn = name
        self.items = items
        if len(self.items) == 0: # or if you don't specify, all unique items are used
            self.items = awsPrinter.list_all_unique_items(bill, name)


class awsPrinter:

    """ return the Bill as a multilayered nested dictionary sorted by the given categories
    categories is a list of Category objects, e.g. [services, usernames, accounts]
    layers of the dictionary are in the order given in the list of categories """
    def sort(dictionary, categories):
        if len(categories) == 0:
            return dictionary # base case

        else:
            output = {name: {} for name in categories[0].items}
            for name in output:
                rowsToAdd = {}
                for key, row in dictionary.items():
                    if row[categories[0].csvColumn] == name:
                        rowsToAdd[key] = row
                output[name] = awsPrinter.sort(rowsToAdd, categories[1:])
            return output

    """return a list of all unique tags in the bill"""
    def get_all_tags(bill):
        unique_tags = []
        for key, entry in bill.entries.items():
            tags = re.split("-| ", entry.data["user:Name"])
            for t in tags:
                for char in t:
                    if char.isdigit():
                        break
                else:
                    if t not in unique_tags:
                        unique_tags.append(t)
        return unique_tags

    """return a bill containing only entries that contain the given tags"""
    def filter_by_tags(bill, tags):
        filtered_bill = Bill()
        for key, entry in bill.entries.items():
            for t in tags:
                pattern = re.compile(t)
                if pattern.search(entry.data["user:Name"]): # the user:Name column has most of the tags
                    filtered_bill.entries[entry.id] = entry
                    break
        return filtered_bill

    """ make a list of all unique entries in a certain column """
    def list_all_unique_items(bill, column):
        unique_items = []

        for key, entry in bill.entries.items():
            if not entry.data[column] in unique_items:
                unique_items.append(entry.data[column])
        return unique_items

    """ in progress
    recursive printing function to work with any size/shape of dictionary """
    def write_to(dictionary, out, indent=""):
        if type(list(dictionary.values())[0]) is not dict:
            print("here")
            out.write(indent + dictionary["UsageType"] + "\n")
            return

        for key, val in dictionary.items():
            out.write(indent + "==  " + key + "  ==\n")
            awsPrinter.write_to(val, out, indent + "    ")

    """remove dictionary keys that only contain empty subdictionaries"""
    def remove_empty_keys(dictionary):
        dict_copy = copy.deepcopy(dictionary)
        is_empty = True
        for key, val in dict_copy.items():
            if type(val) is not dict:
                is_empty = False
                break
            if val:
                response = awsPrinter.remove_empty_keys(dictionary[key])
                if response == True:
                    dictionary.pop(key)
                else:
                    is_empty = False
            else:
                dictionary.pop(key)
        return is_empty

    """ format and write out the dictionary """
    def write_to_file(dictionary, out):
        dictionary = OrderedDict(sorted(dictionary.items()))

        for service in dictionary:
            out.write("\n********  " + service + "  ********\n")
            for zone in dictionary[service]:
                if zone == "":
                    out.write("    ====  Not Labelled  ====\n")
                else:
                    out.write("    ====  " + zone + "  ====\n")
                for name in dictionary[service][zone]:
                    if dictionary[service][zone][name]:
                        if name == "":
                            out.write("        ==  No Name  ==\n")
                        else:
                            out.write("        ==  " + name + "  ==\n")
                        for item in dictionary[service][zone][name]:
                            row = dictionary[service][zone][name][item]
                            out.write("            {:<25}   {:<30}   {:<40}   {:<20}\n".format(str(row["RecordID"]),
                                                                                      str(row["UsageType"]),
                                                                                      str(row["user:Name"]),
                                                                                      str(row["UsageStartDate"])))

