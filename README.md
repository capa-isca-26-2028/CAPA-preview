# CAPA (Carbon for Advanced-Packaged Architectures)


## Requirements
CAPA requires the following python packages:
- numpy
- scipy
- matplotlib

To setup a virtual environment for CAPA:
>python3 -m venv capa_venv<br>
>source capa_venv/bin/activate<br>
>pip3 install -r requirements.txt


## Input files
A directory that contains 2 files:<br>
`arch.json` which contains the topology and bondind methods<br>
and<br>
`chiplets.json` which contains the information (type, node, area/capacity, etc.) of different of chiplets appeared in arch.json


Take AMD MI300X as an example

- `arch.json`([arch_description/MI300X/arch.json](arch_description/MI300X/arch.json))
    - First key should be `Top`, with the name of the chip `MI300X`
    - Then start from the second node to the leaf node (e.g., for MI300X, this would be `SoIC`
        - An `SoIC` contains 2 `XCD` and 1 `IOD`
        - `XCD` is at "stack" `1` (first stacking on top of base), with "bonding" method of `hb` (hybrid bonding) and a "pitch" of `9` (um)
        - `IOD` is the base die, represented with a value of `0`
    - The last key would be `MI300X`, containing 4 `SoIC`, 8 `hbm3` and 1 `interposer`
        - `SoIC` is at "stack" `1`, and MI300X has `4` of them, with "bonding" method of `ubump` (micro-bump), "pitch" of `35` (um) and a die-to-die bandwidth of `10.8` (Tera Bytes per second)
        - `hbm3` is also at "stack" `1`, with `8` of them, using `ubump` of `45` (um) pitch
        - `interposer` is the base layer, so the value is `0`
- `chiplets.json`([arch_description/MI300X/chiplets.json](arch_description/MI300X/chiplets.json)) contains the information of all the leaf nodes
    - For logic dies, 
        - it should contain a `type`, the default is `hpc`
        - Technology node; we currently support {65, 45, 40, 28, 20, 14, 10, 7, 7_EUV, 5, 3, 2}
        - area in cm^2
        - binning information when applicable, with `binnable` as the fraction of binnable area [0, 1], `g` as the functional modules and `c` as binnable modules.
    - For HBM,
        - `type` has to be `hbm`
        - `node` is the hbm generation; we currently support {2e, 3, 3_low, 3e, 4}
        - `capacity` in GB
    - For EMIB or Silicon interposer,
        - `type` is {emib, interposer}
        - `area` is the area of the emib or silicon interposer

## Running
> python3 arch_parser.py <path_to_arch_descripton>

For example, to run the provided [TPUv4](arch_description/TPUv4):

> python3 arch_parser.py arch_description/TPUv4

## Output

The Terminal will print some intermediate information and raw data output.<br>
Output files (one .csv and at least one .pdf) are generated inside the input directory.<br>

Example of TPUv4 output:

>...<br>
>pieces: ['ASIC' 'hbm2' 'interposer' 'ubump_bonding_yield']<br>
>carbon(kg): [23.36964512 36.321891 13.89975659 16.66349866]<br>
>total carbon(kg): 90.2547913586063 
>
>output csv file: arch_description/TPUv4/TPUv4_output.csv
>output pie chart: arch_description/TPUv4/TPUv4_TPUv4.pdf

The raw output is shown in the terminal and the generated `TPUv4_output.csv`.<br>
A pie chart is also generated as `TPUv4_TPUv4.pdf`.

For custom 3D-stacked IC, like the `SoIC` in MI300X, CAPA will generated a breakdown for the `SoIC` as well the overall `MI300X`.
