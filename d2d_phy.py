import numpy as np
import json

def hbm_phy(type=3):
    with open("parameters/hbm.json", 'r') as f:
        hbm = json.load(f)
    assert str(type) in hbm.keys()
    # in mm
    x = hbm[str(type)]['PHY-x']
    y = hbm[str(type)]['PHY-y']
    # print("per hbm_phy area:", x*y)
    return x*y

def ubump_phy(pitch=35, bandwidth=10.8):
    with open("parameters/d2d.json", 'r') as f:
        d2d = json.load(f)
    key = str(pitch)+'u'
    assert key in d2d.keys()

    areal_bandwidth = d2d[key]

    # bandwidth in TiB/s, areal bandwdith in Tib/s
    phy_area = (bandwidth*8) / areal_bandwidth
    # print("per ubump phy area:", phy_area)
    return phy_area