import matplotlib.pyplot as plt
from matplotlib.figure import figaspect
import csv
import numpy as np


def draw_pie_chart(title, components, value, output_suffix):
    # print(title)
    # print(components)
    # print(value)
    color_palatte = ["#e97132","#ffd579","#97cfea","#8cb591","#156082"]
    # plt.style.use('seaborn-v0_8-colorblind')
    plt.style.use('seaborn-v0_8-pastel')

    for i in range(0, len(components)):
        if components[i] == 'hb_bonding_yield':
            components[i] = '\n\nhb\nBonding\nYield'
    for i in range(0, len(components)):
        if components[i] == 'ubump_bonding_yield':
            components[i] = 'ubump bonding yield'
    plt.rcParams.update({'font.size': 20})
    plt.rcParams["font.family"] = "Times New Roman"
    fig, ax = plt.subplots()
    explode = np.full(len(components), 0.05)
    ax.pie(value, explode=explode, labels=components, autopct='%.1f%%', colors=color_palatte)
    # plt.show()
    plt.savefig(output_suffix+'_'+title+".pdf", bbox_inches='tight')

    # print("pie done")

def pie_chart(output_suffix):
    file = output_suffix+"_output.csv"
    print("output csv file:", file)
    with open(file, 'r') as f:
        csv_file = csv.reader(f)
        i = 0
        for row in csv_file:
            # print(row)
            if i == 0:
                title = row[0]
                # print(title)
                i = 1
            elif i == 1:
                components = row
                i = 2
            elif i == 2:
                carbon = row
                # print("drawing pie chart for", title)
                draw_pie_chart(title, components, carbon, output_suffix)
                print("output pie chart:", output_suffix+'_'+title+".pdf")
                i = 0
