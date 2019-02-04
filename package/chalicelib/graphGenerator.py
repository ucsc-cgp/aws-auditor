import copy
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
import pprint
import shutil


class GraphGenerator:
    """
    A tool for creating graphs from data generated in a ReportGenerator object.
    """
    def __init__(self):
        pass

    @staticmethod
    def switch_names(d, old_name, new_name):
        """
        Rename or combine keys in a dictionary
        :param dict d: dictionary to use
        :param str old_name: key as it currently exists
        :param str new_name: key to replace it with
        :return: dictionary with keys replaced
        """
        data = copy.deepcopy(d)

        if new_name in data:  # combine keys
            for entry, value in data[old_name].items():
                if type(value) is dict:  # 3 layer dictionary
                    if entry in data[new_name]:  # add to already existing value
                        for date in data[old_name][entry].keys():
                            data[new_name][entry][date] += data[old_name][entry][date]
                    else:  # create new value
                        data[new_name][entry] = data[old_name][entry]
                else:  # 2 layer dictionary
                    if entry in data[new_name]:
                        data[new_name][entry] += data[old_name][entry]
                    else:
                        data[new_name][entry] = data[old_name][entry]

        else:  # rename key
            data[new_name] = {}
            for key, val in data[old_name].items():
                data[new_name][key] = val

        data.pop(old_name)  # remove old key once it's copied over

        return data

    @staticmethod
    def rename_data(data):
        """
        Combine i- data into one dictionary and rename blank names to 'unnamed'

        :param dict data: dictionary to use
        :return: renamed dictionary
        """
        renamed = data
        for tag in data:
            if tag == "":
                renamed = GraphGenerator.switch_names(renamed, "", "unnamed")
            elif tag[:2] == "i-":
                renamed = GraphGenerator.switch_names(renamed, tag, "i-")
        return renamed

    @staticmethod
    def list_data(data, name, start_date, end_date, total=False):
        """
        Convert a dictionary that maps names to their daily costs into a tuple of two lists representing x and y values

        :param dict data: the dictionary containing the specified name and desired data
        :param str name: the name to refer to in the dictionary
        :param bool total: if set to True, the cost for each day is cumulative, a month-to-date total each day
        :return: tuple in the format ([1, 2, 3, ...], [day 1 cost, day 2 cost, day 3 cost, ...])
                 for the given person
        """
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        day = datetime.timedelta(days=1)
        xvals = []
        yvals = []

        if total:
            for i in range(end_date.day - start_date.day + 1):
                xvals.append(i + 1)
                current_date = (start_date + day * i).strftime("%Y-%m-%d")
                if current_date in data[name]:
                    if len(yvals) == 0:
                        yvals.append(data[name][current_date])
                    else:
                        yvals.append(data[name][current_date] + yvals[-1])
                else:
                    if len(yvals) == 0:
                        yvals.append(0)
                    else:
                        yvals.append(yvals[-1])

        else:
            for i in range(end_date.day - start_date.day + 1):
                xvals.append(i + 1)
                current_date = (start_date + day * i).strftime("%Y-%m-%d")
                if current_date in data[name]:
                    yvals.append(data[name][current_date])
                else:
                    yvals.append(0)

        return xvals, yvals

    @staticmethod
    def merge(dic1, dic2):
        """
        Merge dictionaries by adding the values together

        :param dic1: input dictionary
        :param dic2: input dictionary
        :return: modified dic2
        """
        pp = pprint.PrettyPrinter()
        pp.pprint(dic1)

        dic2_copy = copy.deepcopy(dic2)
        for key, val in dic1.items():
            if key in dic2_copy:
                dic2_copy[key] += dic1[key]
            else:
                dic2_copy[key] = dic1[key]
        return dic2_copy

    @staticmethod
    def merge_dictionaries(dic1, dic2):
        """
        Combine two three-layer dictionaries

        :param dic1: input dictionary
        :param dic2: input dictionary
        :return: modified dic2
        """
        dic2_copy = copy.deepcopy(dic2)
        for name in dic1:
            if name in dic2_copy:
                if name == "Total":
                    dic2_copy[name] += dic1[name]
                else:
                    for service in dic1[name]:
                        if service == "Total":
                            dic2_copy[name][service] += dic1[name][service]
                        else:
                            if service in dic2[name]:
                                dic2_copy[name][service] = GraphGenerator.merge(dic1[name][service], dic2_copy[name][service])
                            else:
                                dic2_copy[name][service] = dic1[name][service]
            else:
                dic2_copy[name] = dic1[name]
        return dic2_copy

    @staticmethod
    def graph_bar(data, title, start_date, end_date, total=False, first=None):
        """
        Display a matplotlib bar graph of data.

        :param dict data: dictionary mapping names to lists of their daily costs
        :param str title: title to display above the graph
        :param bool total: if true, display data as a cumulative total cost each day
        :param str first: if specified, plot this person's data first so it is easier for them to read
        :return: matplotlib plot
        """
        # plt.style.use("~/.matplotlib/elip12.mplstyle")  # style definition
        plt.figure(figsize=(5, 5))
        axes = plt.axes()
        axes.xaxis.set_major_locator(ticker.MultipleLocator(1))  # set the tick marks to integer values

        # label axes
        plt.xlabel("date")
        plt.ylabel("cost in dollars")
        plt.title(title)

        colors = plt.cm.rainbow(np.linspace(0, 1, len(data)))  # make a unique color for each bar

        # keep track of where the top of each stacked bar is after each iteration
        prev = [0 for i in range(int(start_date[-2:]), int(end_date[-2:]) + 1)]  # each bar starts with a height of 0

        if first:  # if specified, graph this person's data first so it all appears at the bottom and is easier to read
            result = GraphGenerator.list_data(data, first, start_date, end_date, total=total)
            plt.bar(result[0], result[1], bottom=prev, label=first)
            prev = [result[1][i] for i in range(len(prev))]

        counter = 0  # iteration counter to keep track of which color to use
        for name in data:
            if name != 'Total':
                if first:
                    if name == first:
                        continue  # if the first person to graph was specified, don't graph their data again
                result = GraphGenerator.list_data(data, name, start_date, end_date, total=total)
                print(result[0], result[1], prev)
                plt.bar(result[0], result[1], bottom=prev, label=name, color=colors[counter])

                # update the value of the height of each stacked bar
                prev = [result[1][i] + prev[i] for i in range(len(prev))]

                counter += 1  # update the iteration counter

        legend = plt.legend(bbox_to_anchor=(0.5, -0.1), loc="upper center")  # place the legend outside the plot

        return plt, legend

    @staticmethod
    def graph_stack(data, title, total=False, first=None):
        """
        Return a matplotlib stack plot of data

        :param dict data: dictionary mapping names to lists of their daily costs
        :param str title: title to display above the graph
        :param bool total: if true, display data as a total cumulative cost each day
        :param str first: if specified, plot this person's data first so it is easier for them to read
        :return: matplotlib plot
        """
        # plt.style.use("~/.matplotlib/elip12.mplstyle")  # style definition

        axes = plt.axes()
        axes.xaxis.set_major_locator(ticker.MultipleLocator(1))  # set the tick marks to integer values

        # label axes
        plt.xlabel("date")
        plt.ylabel("cost")
        plt.title(title)

        y_sets = []
        for name in data:
            result = GraphGenerator.list_data(data, name, total=total)
            x = result[0]
            y_sets.append(result[1])
        y = np.vstack(y_sets)  # stack all the y data sets into a 2d array
        plt.stackplot(x, y, label=name)

        plt.legend()
        return plt

    @staticmethod
    def graph_everyone(data, title, name=None):
        """
        Make a pyplot stacked bar graph of everyone's costs

        :param dict data: data in dictionary form
        :param str title: title to display above the graph
        """
        data = GraphGenerator.rename_data(data)
        plot = GraphGenerator.graph_bar(data, title, first=name)
        return plot

    @staticmethod
    def graph_individual(data, title, start_date, end_date):
        """
        Make a pyplot stacked bar graph of a specific person's costs split up by service.

        :param str name: the name to use
        :param dict data: data in dictionary form
        :param str title: title to display above the graph
        :return: matplotlib plot
        """
        plot = GraphGenerator.graph_bar(data, title, start_date, end_date)
        return plot

    @staticmethod
    def clean():
        """Erase everything in the images directory"""

        if os.path.exists("images"):
            shutil.rmtree("images")