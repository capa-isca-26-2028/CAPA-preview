import numpy as np
import json
from scipy.special import gamma, factorial, stirling2, binom

# mm and mm^2 in Ndie per wafer
def num_die_per_wafer(die_area):
    edge = 3
    phi_wafer = 300 - 2*edge
    kerf = 60/1000

    total_area = die_area + np.sqrt(die_area)*kerf*2+kerf*kerf

    return ((np.pi*np.power(phi_wafer/2, 2))/(total_area)) - 0.51*((np.pi*phi_wafer)/(np.sqrt(total_area)))

# cm and cm^2 in yield
# covert area from mm^2 to cm^2
def yield_model(area_critical, d0, alpha):
    area = area_critical/100
    base = 1 + ((area*d0)/(alpha))
    return np.power(base, -1*alpha)


# probability of chip having d defects
# area in cm^2
def p_defect(d, area, d0, alpha):
    beta = d0 * area / alpha
    return (gamma(d+alpha)/(factorial(d)*gamma(alpha)))*(np.power(beta, d)/(np.power(beta+1, d+alpha)))

# probability of g out of c working with d defects
def p_good(d, c, g):
    if g == 0: 
      return 1
  
    if d == 0:
      return 1
    elif d <= (c-g):
      return 1
    else:
    #   print("s2:", stirling2(d, (c-g)))
    #   print("binom:", binom(c, (c-g)))
    #   print("factorial:", factorial(c-g))
    #   print("power:", np.power(c, d))
      return stirling2(d, (c-g))*binom(c, (c-g))*factorial(c-g)/np.power(c, d)


# probability of g out of c working with d defects but eta percent critical
def p_good_eta(eta, d, c, g):
    return p_good(d, c, g)*np.power(1-eta, d)

# will convert area from mm^2 to cm^2
def yield_bin(area, eta, c, g, d0, alpha):
    sum = np.float64(0.0)
    for d in range (0, 15):
       sum += p_defect(d, area/100, d0, alpha) * p_good_eta(eta, d, c, g)
    #    print(sum)
    #    print("d:", d, ";", p_defect(d, area, d0, alpha) * p_good_eta(eta, d, c, g))
    return sum

def get_cpw(process_node, location="us_arizona"):
    # similar to ACT's .json read
    # .json are in gCO2eq
    with open("parameters/s1pw.json", 'r') as f:
        s1pw = json.load(f)
    with open("parameters/epw.json", 'r') as f:
        epw = json.load(f)
    with open("parameters/ci_location.json", 'r') as f:
        ci = json.load(f)
    with open("parameters/s3pw.json", 'r') as f:
        s3pw = json.load(f)

    process_node = "N" + str(process_node)
    assert process_node in s1pw.keys()
    assert process_node in epw.keys()
    assert location in ci.keys()
    assert process_node in s3pw.keys()

    s2pw = epw[process_node] * ci[location]

    carbon_per_wafer = s1pw[process_node] + s2pw + s3pw[process_node]
    return carbon_per_wafer, s1pw[process_node], s2pw, s3pw[process_node]


# die_area in mm^2
# carbon in gCO2eq
def die_carbon(die_area, process_node, location="us_arizona", known_yield=False, die_yield=0.875, eta=0, c=1, g=1, d0=0.1, alpha=10):
    dpw = num_die_per_wafer(die_area)

    with open("parameters/d0.json", 'r') as f:
        d0_list = json.load(f)
    d0_process_node = "N" + str(process_node)
    assert d0_process_node in d0_list.keys()
    d0 = d0_list[d0_process_node]
    # d0 = 0.1
    # alpha=10
    
    if known_yield:
        ydie = die_yield
    elif eta != 0:
        print("die_area=", die_area, "; eta=", eta, "; c=", c, "; g=", g, "; d0=", d0, "; alpha=", alpha)
        ydie = yield_bin(die_area, eta, c, g, d0, alpha)
        print("yield after binning:", ydie)
        print("yield w/o binning:", yield_model(die_area, d0, alpha))
    else:
        ydie = yield_model(die_area, d0, alpha)
        print("no binning, yield:", ydie)
    print(location)
    cpw = get_cpw(process_node, location)
    scaling = dpw*ydie
    print("scope 1 per wafer =", cpw[1])
    print("scope 2 per wafer =", cpw[2])
    print("scope 3 per wafer =", cpw[3])
    s1pd = cpw[1] / scaling
    s2pd = cpw[2] / scaling
    s3pd = cpw[3] / scaling
    carbon_per_die = cpw[0] / scaling
    return carbon_per_die, s1pd, s2pd, s3pd

def hbm_carbon(type=3, capacity=24):
    with open("parameters/hbm.json", 'r') as f:
        hbm = json.load(f)
    assert str(type) in hbm.keys()
    # .json have kgCO2eq
    return hbm[str(type)]['carbon']*capacity


def interposer_carbon(area, metal_area, location="taiwan", d0=0.06, alpha=6):
    dpw = num_die_per_wafer(die_area=area)
    ydie = yield_model(metal_area, d0, alpha)
    print("interposer yield =", ydie)

    high_flag = True

    with open("parameters/ci_location.json", 'r') as f:
        ci = json.load(f)
    with open("parameters/s3pw.json", 'r') as f:
        s3pw = json.load(f)
    
    process_node = "Interposer"

    assert location in ci.keys()
    assert process_node in s3pw.keys()
    # 0.002122kWh/mm^2 for 6 metal layers
    # s2pw = epw[process_node] * ci[location]
    s3carbon_per_wafer = s3pw[process_node]

    if high_flag:
        process_node = "65"
        print("high estimate for Si Int: using N", process_node)
        cpw, s1pw, s2pw, s3pw = get_cpw(process_node, location)

    scaling = dpw*ydie

    s3carbon = s3carbon_per_wafer / scaling
    s2carbon = metal_area*0.002122*ci[location]
    # print("interposer s3carbon =", s3carbon)
    # print("interposer s2carbon =", s2carbon)
    carbon = s3carbon + s2carbon

    # high estimate:
    if high_flag:
        carbon = cpw / scaling
    return carbon

def emib_carbon(area, location="us_new_mexico", d0=0.06, alpha=6):
    dpw = num_die_per_wafer(die_area=area)
    ydie = yield_model(area, d0, alpha)
    print("emib yield =", ydie)

    high_flag = True

    if high_flag:
        process_node = "20"
        print("high estimate for EMIB: using N", process_node)
        cpw, s1pw, s2pw, s3pw = get_cpw(process_node, location)

    with open("parameters/ci_location.json", 'r') as f:
        ci = json.load(f)
    with open("parameters/s3pw.json", 'r') as f:
        s3pw = json.load(f)
    
    process_node = "Interposer"
    assert location in ci.keys()
    assert process_node in s3pw.keys()
    # 0.002122kWh/mm^2 for 6 metal layers
    # 0.001415kWh/mm^2 for 4 metal layers
    # s2pw = epw[process_node] * ci[location]
    s3carbon_per_wafer = s3pw[process_node]

    # print("interposer dpw =", dpw)
    # print("interposer metal yield =", ydie)
    scaling = dpw*ydie

    s3carbon = s3carbon_per_wafer / scaling
    s2carbon = area*0.001415*ci[location]
    # print("interposer s3carbon =", s3carbon)
    # print("interposer s2carbon =", s2carbon)
    
    carbon = s3carbon + s2carbon

    if high_flag:
        carbon = cpw / scaling
    return carbon

def get_hbm_footprint(type='2e'):
    with open("parameters/hbm.json", 'r') as f:
        hbm = json.load(f)
    
    assert str(type) in hbm.keys()

    footprint = hbm[str(type)]['x-dimension']*hbm[str(type)]['y-dimension']
    return footprint