from  resistance_automation import * 

# # Collect platform information
# try:
#     correct = True
#     while correct:
#         correct = False
#         platform_num = int(input(f"What 3D printer platform are you using?\n1) h.r.3.3\n2)\n3)\nPlatform number: "))
#         if platform_num == 1:
#             platform = "h.r.3.3"
#         elif platform_num == 2:
#             platform = "n/a"
#         elif platform_num == 3:
#             platform = "n/a"
#         else:
#             correct = True
# except ValueError:
#     print("Error: Please enter a valid platform number.")
platform = "h.r.3.3"

# Define assay name
# assay = (str(input("What is the name of your assay?\n")).lower()).replace(" ", "")
assay = "ethyl"
# assay = "caffeine"
# assay = "cocaine"
# assay = "calcium"

# Collect number of samples/reagents 
# while True:
#     try:  
#         num_samples = int(input(f"How many samples and reagents are part of {assay}?\n"))
#         break
#     except ValueError:
#         print("Error: Please enter a valid integer.")
num_samples = 3

# Define dictionary for storing sample/reagent data
input_dict = {}

# Collect sample/reagent name(s) and concentration(s)
# for i in range(0, num_samples):
#     if i == 0:
#         name = str(input("What is the name of the first sample/reagent?\n"))
#     else:
#         name = str(input("What is the name of the next sample/reagent?\n"))
#     while True:
#         try:  
#             concentration = float(input(f"What is the concentration of {name} [uL]?\n")) * 10**(-6)
#             break
#         except ValueError:
#             print("Error: Please enter a valid concentration value.")
#     input_dict[name] = concentration
input_dict = {"sample":4*10**(-6), "R1":210*10**(-6), "R2":90*10**(-6)}
# input_dict = {"sample":3*10**(-6), "R1":162*10**(-6), "R2":162*10**(-6)}
# input_dict = {"sample":9*10**(-6), "R1":130*10**(-6), "R2":55*10**(-6)}
# input_dict = {"sample":2*10**(-6), "R1":25*10**(-6), "H2O":225*10**(-6)}

# Collect maximum acceptable error 
# while True:
#     try:  
#         error_condition = float(input(f"What is the maximum acceptable error between expected and evaluated concentration values [%]?\n"))
#         break
#     except ValueError:
#         print("Error: Please enter a valid percentage.")
error_condition = 18

# Run the flow ({assay}_configure.py)
def main(assay, num_samples, platform, input_dict, error_condition):
    # Create {assay}_configure.py
    configure_file(assay, num_samples, platform)
    # Specifying solutions; used in .v file
    soln_list, soln_str = soln_spec(num_samples)
    # Initial calculations and definitions of mixing geometry
    mix_list, type_list, length_dict, ratio_dict = init_mix(input_dict, num_samples)
    # Remove elements not allowed by license (>15)
    # remove_elements(mix_list, type_list, num_samples)
    # Assign samples to solution numbers
    soln_dict = solution_dict(length_dict)
    # Create verilog file based on mixing specifications
    v_file(mix_list, type_list, soln_list, soln_str, assay, num_samples)
    # Define input, chem, and eval parameters to create simulation.config
    simulation_config(soln_dict, ratio_dict, assay, platform)
    # Run flow
    subprocess.run(["python3", f"{assay}_configure.py"])
    # Display concentration results from Chem_Eval.csv
    print(con_resutls(assay)[0])
    # Recursive function for error minimization 
    min_error(0, mix_list, type_list, con_resutls(assay)[1], con_resutls(assay)[2], con_resutls(assay)[3], error_condition, soln_list, soln_str, assay, num_samples, 0)
    # Delete {assay}_configure.py and {assay}.v files from working directory after use
    # delete(assay)

if __name__ == "__main__":
    main(assay, num_samples, platform, input_dict, error_condition)