#!/usr/bin/python3

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import pyfsdb


def parse_args():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description=__doc__,
                            epilog="Exmaple Usage: ")

    parser.add_argument("-c", "--columns", type=str, nargs=2,
                        help="Columns to use")

    parser.add_argument("-v", "--value-column", default="count", type=str,
                        help="The value column to plot as the heat map")

    parser.add_argument("-i", "--invert", action="store_true",
                        help="Invert the foreground/background colors")

    parser.add_argument("-F", "--add-fractions", action="store_true",
                        help="Add text fraction labels to the grid")

    parser.add_argument("-R", "--add-raw", action="store_true",
                        help="Add text raw-value labels to the grid")

    parser.add_argument("-L", "--add-labels", action="store_true",
                        help="Add x/y axis labels")

    parser.add_argument("-fs", "--font-size", default=None, type=int,
                        help="Set the fontsize for labels")

    parser.add_argument("input_file", type=FileType('r'),
                        nargs='?', default=sys.stdin,
                        help="Input fsdb file to read")

    parser.add_argument("output_file", type=str,
                        nargs='?', default="out.png",
                        help="Where to write the png file to")

    args = parser.parse_args()

    if not args.columns or len(args.columns) != 2:
        raise ValueError("exactly 2 columns must be passed to -c")

    return args


def main():
    args = parse_args()

    # read in the input data
    f = pyfsdb.Fsdb(file_handle=args.input_file,
                    return_type=pyfsdb.RETURN_AS_DICTIONARY)

    max_value = None
    dataset = {}  # nested tree structure
    ycols = {}  # stores each unique second value
    for row in f:
        if not max_value:
            max_value = float(row[args.value_column])
        else:
            max_value = max(max_value, float(row[args.value_column]))

        if row[args.columns[0]] not in dataset:
            dataset[row[args.columns[0]]] = \
                { row[args.columns[1]]: float(row[args.value_column]) }
        else:
            dataset[row[args.columns[0]]][row[args.columns[1]]] = \
                float(row[args.value_column])
        ycols[row[args.columns[1]]] = 1

    # merge the data into a two dimensional array
    data = []
    xcols = sorted(dataset.keys())
    ycols = sorted(ycols.keys())
    for first_column in xcols:
        newrow = []
        for second_column in ycols:
            if second_column in dataset[first_column]:
                newrow.append(dataset[first_column][second_column] / max_value)
            else:
                newrow.append(0.0)
        data.append(newrow)

    grapharray = np.array(data)
    if not args.invert:
        grapharray = 1 - grapharray

    # generate the graph
    fig, ax = plt.subplots()
    ax.imshow(grapharray, vmin=0.0, vmax=1.0, cmap='gray')

    ax.set_xlabel(args.columns[1])
    ax.set_ylabel(args.columns[0])

    if args.add_labels:
        ax.set_yticks(np.arange(len(dataset)))
        ax.set_yticklabels(xcols)
        ax.set_xticks(np.arange(len(ycols)))
        ax.set_xticklabels(ycols)

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
                 rotation_mode="anchor")

    if args.add_fractions:
        for i in range(len(grapharray)):
            for j in range(len(grapharray[i])):
                text = ax.text(j, i, "{:1.1f}".format(grapharray[i][j]),
                               ha="center", va="center", color="r",
                               fontsize=args.font_size)
    elif args.add_raw:
        for i, first_column in enumerate(xcols):
            for j, second_column in enumerate(ycols):
                try:
                    value = dataset[first_column][second_column]
                    ax.text(j, i, "{}".format(int(value)),
                            ha="center", va="center", color="r",
                            fontsize=args.font_size)
                except Exception:
                    pass

    fig.tight_layout()
    plt.savefig(args.output_file,
                bbox_inches="tight", pad_inches=0)

    # import pprint
    # pprint.pprint(dataset)


if __name__ == "__main__":
    main()
