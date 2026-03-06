import argparse

import numpy as np
import json

from carbon_per_die import die_carbon, hbm_carbon, interposer_carbon, emib_carbon, get_hbm_footprint
from figure import pie_chart
from d2d_phy import hbm_phy, ubump_phy

aggregate_bonding = True
aggregate_hbm = True
aggregate_logic = True

parser = argparse.ArgumentParser(description='directory containing architecture description')
parser.add_argument('dir_arg')

args=parser.parse_args()

# format the path string
dir = args.dir_arg
# print(dir)
if dir[-1] != '/':
    dir = dir + '/'
# else:
#     dir = args.dir_arg.split('/')[-2]+'/'
# print(dir)

chiplet_desc = dir+"chiplets.json"
arch_desc = dir+"arch.json"
# print(chiplet_desc)
# print(arch_desc)

with open("parameters/bonding.json", 'r') as f:
    bonding_epa = json.load(f)
with open("parameters/ci_location.json", 'r') as f:
    ci = json.load(f)
with open("parameters/d2d.json", 'r') as f:
    d2d = json.load(f)

with open(chiplet_desc, 'r') as f:
    chiplets = json.load(f)
with open(arch_desc, 'r') as f:
    arch = json.load(f)

assert "Top" in arch.keys()
top = arch["Top"]
assert top in arch.keys()
# print(arch[top].keys())

output_suffix = dir+top
outfilename = output_suffix+"_output.csv"
out_f = open(outfilename, 'w+')

# uses gCO2eq for calc
def topology(carbon, pieces, arch, chiplets, top, location="taiwan"):
    bonding = ''
    bonding_count = 0
    interposer_flag = False
    metal_area = np.array([])
    # initilize for interposer
    for key in arch[top].keys():
        if key in arch.keys(): continue
        elif key in chiplets.keys():
            if chiplets[key]['type'] == 'interposer':
                interposer_flag = True
                break
        else:
            print(key, "does NOT exist")
    # go through all the chiplets
    for key in arch[top].keys():
        # print(key, arch[top][key])
        if arch[top][key] == 0:
            # print(key, "serves as the base substrate for", top)
            pass
        else:
            bonding = arch[top][key]['bonding']
            # print(key, "uses", bonding, "bonding tech")
            # print(key, "uses", arch[top][key]['bonding'], "bonding tech")
        if key in chiplets.keys():
            # print(key, "is in chiplets")
            # print(chiplets[key])
            type = chiplets[key]['type']
            if type == 'interposer':
                # print(arch[top][key])/
                print("interposer metal area:", metal_area)
                # call interposer_carbon with metal area
                int_carbon = interposer_carbon(area=chiplets[key]['area'], metal_area=np.sum(metal_area),location=location)
                carbon = np.append(carbon, int_carbon)
                pieces = np.append(pieces, key)
            elif type == 'emib':
                # emib carbon
                bridge_carbon = emib_carbon(area=chiplets[key]['area'], location=location)
                carbon = np.append(carbon, bridge_carbon*arch[top][key]['number'])
                pieces = np.append(pieces, key)
            elif type == 'hpc':
                # print(key, "uses N", chiplets[key]['node'], "hpc node")
                # print(arch[top][key])
                # print("die area =", chiplets[key]['area'], "; node =", chiplets[key]['node'])
                # d0 for different nodes is done in carbon_per_die.py
                if 'binnable' in chiplets[key].keys():
                    # print("eta=", (1-chiplets[key]['binnable']), "; c=", chiplets[key]['c'], "; g=", chiplets[key]['g'])
                    tmp_carbon = die_carbon(die_area=chiplets[key]['area'], process_node=chiplets[key]['node'], location=location, known_yield=False, eta=(1-chiplets[key]['binnable']), c=chiplets[key]['c'], g=chiplets[key]['g'], d0=0.1, alpha=10)[0]
                else:
                    tmp_carbon = die_carbon(die_area=chiplets[key]['area'], process_node=chiplets[key]['node'], location=location, known_yield=False, d0=0.1, alpha=10)[0]
                if arch[top][key] != 0:
                    # do bonding process carbon here
                    # area * EPA * CI
                    bonding_carbon = (chiplets[key]['area']/100)*bonding_epa[arch[top][key]['bonding']]*ci[location]*1000
                    if aggregate_logic:
                        carbon = np.append(carbon, (tmp_carbon+bonding_carbon)*arch[top][key]['number'])
                        pieces = np.append(pieces, key)
                        bonding_count += arch[top][key]['number']
                    else:
                        for i in range(0, arch[top][key]['number']):
                            if aggregate_bonding:
                                carbon = np.append(carbon, tmp_carbon+bonding_carbon)
                                pieces = np.append(pieces, key)
                            else:
                                carbon = np.append(carbon, tmp_carbon)
                                pieces = np.append(pieces, key)
                                carbon = np.append(carbon, bonding_carbon)
                                pieces = np.append(pieces, key+"_bonding")
                            bonding_count += 1
                else: 
                    carbon = np.append(carbon, tmp_carbon)
                    pieces = np.append(pieces, key)
            elif type == 'hbm':
                # print(key, "is", chiplets[key]['capacity'], "GB HBM", chiplets[key]['node'])
                # print(arch[top][key])
                total_hbm_carbon = np.float64(0.0)

                num_stack = arch[top][key]['number']

                hbm_stack_carbon = hbm_carbon(type=chiplets[key]['node'], capacity=chiplets[key]['capacity'])
                bonding_area = get_hbm_footprint(type=chiplets[key]['node'])
                bonding_carbon = (bonding_area/100)*bonding_epa[arch[top][key]['bonding']]*ci[location]*1000
                if not aggregate_hbm:
                    for i in range(0, num_stack):
                        if aggregate_bonding:
                            carbon = np.append(carbon, hbm_stack_carbon*1000+bonding_carbon)
                            pieces = np.append(pieces, key)
                        else:
                            carbon = np.append(carbon, hbm_stack_carbon*1000)
                            pieces = np.append(pieces, key)
                            carbon = np.append(carbon, bonding_carbon)
                            pieces = np.append(pieces, key+"_bonding")
                else:
                # hbm.json have carbon in kgCO2eq, so *1000 to get gCO2eq
                    total_hbm_carbon += 1000*num_stack*hbm_carbon(type=chiplets[key]['node'], capacity=chiplets[key]['capacity']) + bonding_carbon*num_stack
                    carbon = np.append(carbon, total_hbm_carbon)
                    pieces = np.append(pieces, key)

                bonding_count += num_stack
                # HBM PHY
                hbm_phy_area = hbm_phy(type=chiplets[key]['node'])
                metal_area = np.append(metal_area, hbm_phy_area*2*num_stack)
            else:
                print("This type of silicon is not recognized:", type)
            
        elif key in arch.keys():
            # print(arch[key])
            tmp_carbon, tmp_pieces = topology(carbon, pieces, arch, chiplets, key, location)
            # print("sum =", np.sum(tmp_carbon)*arch[top][key]['number'])
            for die in arch[key].keys():
                if arch[key][die] == 0:
                    bonding_area = chiplets[die]['area']
            bonding_carbon = (bonding_area/100)*bonding_epa[arch[top][key]['bonding']]*ci[location]*1000
            if aggregate_logic:
                carbon = np.append(carbon, (np.sum(tmp_carbon)+bonding_carbon)*arch[top][key]['number'])
                pieces = np.append(pieces, key)
                bonding_count += arch[top][key]['number']
            else:
                for i in range(0, arch[top][key]['number']):
                    if aggregate_bonding:
                        carbon = np.append(carbon, np.sum(tmp_carbon)+bonding_carbon)
                        pieces = np.append(pieces, key)
                    else:
                        carbon = np.append(carbon, np.sum(tmp_carbon))
                        pieces = np.append(pieces, key)
                        carbon = np.append(carbon, bonding_carbon)
                        pieces = np.append(pieces, key+"_bonding")
                    bonding_count += 1

            # d2d phy
            if 'bandwidth' in arch[top][key].keys():
                if arch[top][key]['bonding'] == 'ubump':
                    d2d_phy_area = ubump_phy(bandwidth=arch[top][key]['bandwidth'], pitch=arch[top][key]['pitch'])
                    metal_area = np.append(metal_area, d2d_phy_area*arch[top][key]['number'])
        else:
            print(key, "does NOT exist")
    # print(carbon)
    print("pre-bond pieces:", pieces)
    print("bonding count =", bonding_count)

    if bonding == 'hb':
        bonding_yield = 0.95
    elif bonding == 'ubump':
        bonding_yield = 0.96
    else:
        pass

    # print("lowest aggregated bonding yield:", np.power(bonding_yield, bonding_count))
    max_yield_carbon = np.sum(carbon)*(1/np.power(bonding_yield, bonding_count))

    # bonding_test = True
    bonding_test = False
    if bonding_test and bonding == 'ubump':
        item_carbon = []
        yield_carbon_arr = []

        # GPU last: A100/H100 test
        # carbon = np.insert(carbon, -1, carbon[0])
        # carbon = np.delete(carbon, 0)
        # pieces = np.insert(pieces, -1, pieces[0])
        # pieces = np.delete(pieces, 0)
        # # print(pieces)
        # carbon = np.insert(carbon, -1, carbon[0])
        # carbon = np.delete(carbon, 0)
        # pieces = np.insert(pieces, -1, pieces[0])
        # pieces = np.delete(pieces, 0)
        # print(pieces)

        # # put HBM before:
        # carbon = np.insert(carbon, 0, carbon[8:24])
        # pieces = np.insert(pieces, 0, pieces[8:24])
        # # carbon = np.insert(carbon, 0, carbon[4:20])
        # # pieces = np.insert(pieces, 0, pieces[4:20])
        # print("post-insert hbm carbon:", carbon)
        # print("post-insert hbm pieces:", pieces)
        # for i in range(0, 16):
        #     carbon = np.delete(carbon, -2)
        #     pieces = np.delete(pieces, -2)
        # print("post-delete hbm carbon:", carbon)
        # print("post-delete hbm pieces:", pieces)

        print("interposer_flag:", interposer_flag)
        if interposer_flag:
            # put interposer from last as the first element 
            if chiplets[pieces[-1]]['type'] != 'interposer':
                print("interposer not last?!")
            carbon = np.insert(carbon, 0, carbon[-1])
            carbon = np.delete(carbon, -1)
            pieces = np.insert(pieces, 0, pieces[-1])
            pieces = np.delete(pieces, -1)
            print("post-rearrange carbon:", carbon)
            print("post-rearrange pieces:", pieces)
        
        for i in range(0, len(pieces)):
            item_carbon = np.append(item_carbon, carbon[i])
            # if it is a bonding process carbon
            if len(pieces[i].split('_bonding')) == 2:
                # print("curr piece: ", pieces[i])
                # print("item_carbon:", item_carbon)
                raised_bonding_yield = np.power(bonding_yield, bonding_count)
                curr_carbon = np.sum(item_carbon)
                curr_yield_carbon = curr_carbon*((1/raised_bonding_yield) - 1)
                yield_carbon_arr = np.append(yield_carbon_arr, curr_yield_carbon)

                # print(bonding_count)
                # print("curr bonding yield =", raised_bonding_yield)
                # print("yield_carbon_arr:", yield_carbon_arr)
                bonding_count = bonding_count - 1
                item_carbon = []
            #     item_carbon += carbon[i]
            #     continue
            # if chiplets[pieces[i]]['type'] == 'interposer':
            #     item_carbon += carbon[i]
            #     continue
            # else:
            #     pass
        # print("yield carbon array:", yield_carbon_arr)
        yield_carbon = np.sum(yield_carbon_arr)
    else:
        bonding_yield = np.power(bonding_yield, bonding_count)
        print("bonding_yield =", bonding_yield)
        yield_carbon = np.sum(carbon)*((1/bonding_yield) - 1)

    print("end testing total carbon (kg):", max_yield_carbon/1000)
    carbon = np.append(carbon, yield_carbon)
    bonding_yield_str = str(bonding)+"_bonding_yield"
    pieces = np.append(pieces, bonding_yield_str)

    out_f.write(top+"\n")
    for i in range(0, pieces.size-1):
        out_f.write(pieces[i])
        out_f.write(',')
    out_f.write(pieces[pieces.size-1])
    out_f.write('\n')

    for i in range(0, carbon.size-1):
        out_f.write(str(carbon[i]))
        out_f.write(',')
    out_f.write(str(carbon[carbon.size-1]))
    out_f.write('\n')

    print(top, "done, returning...\n")
    return carbon, pieces

carbon = np.array([])
pieces = np.array([])
carbon, pieces = topology(carbon, pieces, arch, chiplets, top, "taiwan")
out_f.close()
print("pieces:", pieces)
print("carbon(kg):", carbon/1000)
print("total carbon(kg):", np.sum(carbon)/1000, "\n")

# print("drawing pie chart")
# print(output_suffix)

pie_chart(output_suffix)
# print("pie chart drawn")

