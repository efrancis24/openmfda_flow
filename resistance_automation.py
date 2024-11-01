import subprocess, os, csv

# Function to create {assay}_configure.py
def configure_file(assay, num_samples, platform):
    #### PIN PLACEMENT IS NOT ROBUST ENOUGH TO HANDLE 8+ SOLUTIONS
    # Pin placement
    pin_str = ""
    for i in range(1, num_samples+1):
        pin_str += f"pins[0][{i}] = \"soln{i}\""
        if i != num_samples:
            pin_str+="\n"
    # Create configure.py file
    with open(f"{assay}_configure.py", "w") as f:
        f.write(f"""
from openmfda_flow import *

verilog_file = "{assay}.v"
design_name = "{assay}"
platform = "{platform}"
pins = [[None for i in range(0,8)] for j in range(0,4)]
{pin_str}
pins[1][7] = "out"

generate_config(verilog_file, design_name, pin_names=pins, platform=platform)

run_flow(design_name, platform=platform, mk_targets=["pnr", "render", "simulate"])
    """)

# Function for specifying solutions; used in .v file
def soln_spec(num_samples):
    soln_list = ""
    soln_str = ""
    for i in range(1, num_samples+1):
        soln_list += f"\tsoln{i},\n"
        soln_str += f"soln{i}"
        if i == num_samples:
            soln_list += f"\tout"
            soln_str += ";"
        else:
            soln_str += ", "
    return soln_list, soln_str

# Function for initial calculations and definitions of mixing geometry
def init_mix(input_dict, num_samples):
    # Calculate total concentration
    conc_sum = sum(input_dict.values())
    # Calculate relative ratio of each sample
    ratio_dict = {}
    for key in input_dict.keys():
        ratio_dict[key] = input_dict[key] / conc_sum
    # Calculate hydraulic resistance values for each sample
    resist_dict = {}
    for key in input_dict.keys():
        resist_dict[key] = 1 / ratio_dict[key]
    # Order resistances from greatest to smallest
    resist_sort = dict(sorted(resist_dict.items(), key=lambda item : item[1], reverse=True))
    # Calculate relative channel lengths based on largest concentration/smallest length
    length_dict = {}
    for key in resist_sort.keys():
        length_dict[key] = resist_sort[key] / resist_sort[next(reversed(resist_sort))]  

    # Determine needed mixing elements
    # Empty list for adding mixing elements based on sample concentration values
    mix_list = [[] for i in range(num_samples)]
    # Empty list for specifying serpentine type
    type_list = [[] for i in range(num_samples)]
    key_num = 0
    for key in length_dict.keys():
        # Adjust length for lowest pixel element, diffmix_25px
        # new_len = length_dict[key] * 90
        new_len = length_dict[key] * 60
        # Add serpentines for each sample/reagent based on length
        for i in range(int(new_len // 720)):
            mix_list[key_num].append(300)
            type_list[key_num].append(0)
        new_len = new_len % 720
        for i in range(int(new_len // 600)):
            mix_list[key_num].append(200)
            type_list[key_num].append(0)
        new_len = new_len % 600
        for i in range(int(new_len // 480)):
            mix_list[key_num].append(150)
            type_list[key_num].append(0)
        new_len = new_len % 480
        for i in range(int(new_len // 360)):
            mix_list[key_num].append(100)
            type_list[key_num].append(0)
        new_len = new_len % 360
        for i in range(int(new_len // 240)):
            mix_list[key_num].append(50)
            type_list[key_num].append(0)
        key_num += 1
    return mix_list, type_list, length_dict, ratio_dict

# Calculate total number of elements in mixing list
def sum_elements(list, num_samples):
    total_elements = 0
    for i in range(len(list)):
        total_elements += len(list[i])
    return total_elements

 # Function to remove elements not allowed by license
def remove_elements(mix_list, type_list, num_samples):
    i = 0
    while sum_elements(mix_list, num_samples) >= 16 - (num_samples-1):
        if i == num_samples:
            i = 0
        if mix_list[i] != []:
            mix_list[i].pop()
            type_list[i].pop()
            # Increment serpentine type if 300px (i.e. 300px_0 to 300px_1)
            if mix_list[i] != []:
                if mix_list[i][len(mix_list[i])-1] == 300:
                    if type_list[i][len(type_list[i])-1] == 3:
                        type_list[i][len(type_list[i])-1] == 0
                    else:
                        type_list[i][len(type_list[i])-1] += 1
        i += 1

# Function to assign samples to solution numbers
def solution_dict(length_dict):
    soln_dict = {}
    i = 1
    for key in length_dict.keys():
        soln_dict[key] = f"soln{i}"
        i += 1
    return soln_dict

# Function for creating verilog file based on mixing specifications
def v_file(mix_list, type_list, soln_list, soln_str, assay, num_samples):
    # Define serpentine combinations for each solution
    mix_str = ""
    k = 0
    connect_list = []
    for i in range(len(mix_list)):
        for j in range(len(mix_list[i])):
            mix_str += f"\nserpentine_{mix_list[i][j]}px_{type_list[i][j]}"
            if j == 0:
                mix_str += f"\tserp{k}\t(.in_fluid(soln{i+1}), .out_fluid(connect{k}));"
            else:
                mix_str += f"\tserp{k}\t(.in_fluid(connect{k-1}), .out_fluid(connect{k}));"
            k += 1
        mix_str += "\n"
        if mix_list[i] == []:
            connect_list.append(f"soln{i+1}")       
        else:
            connect_list.append(f"connect{k-1}")

    # Define mixing 
    for i in range(len(mix_list)- 1):
        if i == len(mix_list) - 2:
            if mix_list[num_samples-1] == []:
                if connect_list == []:
                    mix_str += f"diffmix_25px_0\tmix{i}\t(.a_fluid(soln{len(mix_list)-1}), .b_fluid(soln{len(mix_list)}), .out_fluid(out));\n"
                else:
                    mix_str += f"diffmix_25px_0\tmix{i}\t(.a_fluid(soln{len(mix_list)}), .b_fluid(connect{k-1}), .out_fluid(out));\n"
            else:
                mix_str += f"diffmix_25px_0\tmix{i}\t(.a_fluid({connect_list[i+1]}), .b_fluid(connect{k-1}), .out_fluid(out));\n"
        else:
            if i == 0:
                mix_str += f"diffmix_25px_0\tmix{i}\t(.a_fluid({connect_list[i]}), .b_fluid({connect_list[i+1]}), .out_fluid(connect{k}));\n"
            else:
                mix_str += f"diffmix_25px_0\tmix{i}\t(.a_fluid({connect_list[i+1]}), .b_fluid({connect_list[len(connect_list)-1]}), .out_fluid(connect{k}));\n"
            connect_list.append(f"connect{k}")
        k += 1

    # Connect string
    connect = ""
    for i in range(k):
        if i == k-1:
            connect += f"connect{i};"
        else:
            connect+= f"connect{i},\t"

    # Create and define .v file
    with open(f"{assay}.v", "w") as f:
        f.write(f"""module {assay} (\n{soln_list} \n);
    input\t{soln_str}
    output\tout;\n
    wire\t{connect}\n
    {mix_str}
    \nendmodule
    """)

# Function to define input, chem, and eval parameters to create simulation.config
### ASSUMES TRANSIENT AND PRESSURE OF 100k
def simulation_config(soln_dict, ratio_dict, assay, platform):
    input_str = ""
    chem_str = ""
    eval_str = ""
    for key in soln_dict.keys():
        input_str += f"input\t{soln_dict[key]}\tpressurePump\tpressure=100k\n"
        chem_str += f"chem\t{key}\t{soln_dict[key]}\t1\n"
        eval_str += f"eval\t{key}\t0\tout\t{round(ratio_dict[key]*10**3, 5)}m\n"
    # Create simulation.config
    directory = f'flow/designs/{platform}/{assay}'
    filename = 'simulation.config'
    filepath = os.path.join(directory, filename)
    os.makedirs(directory, exist_ok=True)
    with open(filepath, 'w') as file:
        file.write(f"""
# time inputs\n
transient\t1m\t0.1m\n\n
# input devices
{input_str}
# chemical definitions
{chem_str}
# eval chem time concentration node
{eval_str}
    """)

# Function for displaying concentration results from Chem_Eval.csv
def con_resutls(assay):
    error_list = []
    expect_conc = []
    eval_conc = []
    table_str = f"\n"
    table_str += "-" * 65
    table_str += f"\n|{assay.upper().center(63)}|\n"
    table_str += "-" * 65
    table_str += f"\n| SAMPLES/REAGENTS | EXPECTED CON. | EVALUATED CON. | ERROR [%] |\n"
    table_str += "-" * 65
    csv_file_path = f"flow/results/{assay}/base/Chem_Eval.csv"
    with open(csv_file_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            table_str += f"\n|{row['Chemical'].center(18)}|"\
            f"{str(round(float(row['Expected Conc']), 5)).center(15)}|"\
            f"{str(round(float(row['Eval Conc']), 5)).center(16)}|"
            percent_error = "{:.2f}".format(round(float(row['Error']), 4) * 100)
            table_str += percent_error.center(11) + "|"
            error_list.append(float(row['Error']))
            expect_conc.append(float(row['Expected Conc']))
            eval_conc.append(float(row['Eval Conc']))
    table_str += f"\n"
    table_str += "-" * 65
    return table_str, error_list, expect_conc, eval_conc 

# Recursive function for error minimization based on difference between expected and evaluated concentration values
def min_error(i, mix_list, type_list, error_list, expect_conc, eval_conc, error_condition, soln_list, soln_str, assay, num_samples, recurv_count):
    recurv_count += 1
    # print("I:", i)
    # base case
    for j in range(len(error_list)):
        if j == len(error_list) - 1:
            if error_list[j] * 100  <= error_condition:
                return
        else:
            if error_list[j] * 100 <= error_condition:
                continue
            else:
                break 
    # increase serpentine length
    if expect_conc[i] < eval_conc[i]:
        if mix_list[i] == [] or mix_list[i][len(mix_list[i])-1] == 300:
            mix_list[i].append(50)
            type_list[i].append(0)
        else:
            mix_list[i][len(mix_list[i])-1] = mix_list[i][len(mix_list[i])-1] + 50
            if mix_list[i][len(mix_list[i])-1] == 250:
                mix_list[i][len(mix_list[i])-1] = mix_list[i][len(mix_list[i])-1] + 50
    # decrease serpentine length
    elif expect_conc[i] > eval_conc[i]:
        if mix_list[i] == []:
            mix_list[i].append(50)
            type_list[i].append(0)
        elif (mix_list[i][len(mix_list[i])-1] - 50) == 0:
            mix_list[i].pop()  
            type_list[i].pop()   
        else:
            mix_list[i][len(mix_list[i])-1] = (mix_list[i][len(mix_list[i])-1] - 50)
    ########## ADDED TO ACCOUNT FOR 15+ COMPONENTS 
    # remove elements not allowed by license 
    # remove_elements(mix_list, type_list, num_samples)
    # reset iterations
    if i >= len(mix_list) - 1 and recurv_count == 6:
        i = 0
        recurv_count = 0
    # Iterate through different serp combos of all samples/reagents
    elif recurv_count >= 6:
        # print("error_list[i]", error_list[i])
        i += 1
        recurv_count = 0
    # re-run flow and exit if error
    v_file(mix_list, type_list, soln_list, soln_str, assay, num_samples)
    result = subprocess.run(["python3", f"{assay}_configure.py"])
    if result.returncode != 0:
        present = False
        for k in range(len(mix_list)):
            if 250 in mix_list[k]:
                present = True
        if not present:
            return 
    # display new concentration results
    print(con_resutls(assay)[0])
    # continue error minimization
    min_error(i, mix_list, type_list, con_resutls(assay)[1], con_resutls(assay)[2], con_resutls(assay)[3], error_condition, soln_list, soln_str, assay, num_samples, recurv_count)

# Function that deletes <assay>_configure.py and <assay>.v files from working directory after use
def delete(assay):
    files_to_delete = [f'{assay}_configure.py', f'{assay}.v']
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            os.remove(file_path)
