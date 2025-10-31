from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog, ttk
import re
import tifffile
from ome_types import from_xml

def print_image_dic(image_dictionary):
    for image_name, img_dic in image_dictionary.items():
        print(image_name)
        for fragment, fragment_dict in img_dic.items():
            print("\t", fragment)
            for cycles, cycle_dic in fragment_dict.items():
                print("\t"*2, cycles, cycle_dic)

AF_cycle = "AF"

#Pop up directory to select folder containing images 
directory_root = tk.Tk()
directory_root.title("Choose a folder in your directory for registration")
directory_root.withdraw()
folder_path = Path(filedialog.askdirectory())
directory_root.deiconify()
directory_root.destroy()

image_dictionary = {}
rescans = {}
channels = {}
#Adding all slides to the image_dictionary and all cycled images to the image dictionary
for vsi_file in list(folder_path.glob("*.vsi")):
    image_name = vsi_file.stem
    image_folder = vsi_file.parent/f"_{image_name}_"

    if image_folder.exists():
        image_dictionary[image_name] = {}

        for subfolder in image_folder.iterdir(): #iterating through all stack folders
            match = re.search(r"stack(\d+?)$",subfolder.name)

            if match and subfolder.is_dir() and int(match.group(1))>=10002: #ignoring label and overview tifs
                stack_number = match.group(1)
                stack_path = image_folder/f"stack{stack_number}"/"frame_t_0.tif"

                with tifffile.TiffFile(stack_path) as tif:

                    #Searching for fragment numbers
                    metadata = from_xml(tif.ome_metadata)
                    match = re.search(r".+?([0-9])$", metadata.images[0].name)
                    
                    if match:fragment_number = match.group(1)
                    else: fragment_number=1

                    if f"fragment-{fragment_number}" not in image_dictionary[image_name].keys():
                        image_dictionary[image_name][f"fragment-{fragment_number}"]={}
                    
                    image_dictionary[image_name][f"fragment-{fragment_number}"][stack_number]={}
                    image_dictionary[image_name][f"fragment-{fragment_number}"][stack_number]["path"]=stack_path
                    
                    #adding target cycles code from the DAPI channels to fragment images, expected to be DAPI_[code]
                    match = re.search(r"(DAPI)_(.+)$",metadata.images[0].pixels.channels[0].name)
                    if match:
                        _, target_cycle = match.groups()
                        match = re.match(r"^([A-Z]+)_([0-9])$", target_cycle)
                        if match:
                            target_cycle, rescan_index = match.groups()
                            if image_name not in rescans: rescans[image_name] = {}
                            if target_cycle not in rescans[image_name]: rescans[image_name][target_cycle]=[]

                        image_dictionary[image_name][f"fragment-{fragment_number}"][stack_number]["target cycle"] = target_cycle

                        channels[target_cycle] = {}
                        image_dictionary[image_name][f"fragment-{fragment_number}"][stack_number]["og channel names"] = []
                        for channel in metadata.images[0].pixels.channels:
                            image_dictionary[image_name][f"fragment-{fragment_number}"][stack_number]["og channel names"].append(channel.name)
                        
                        number_of_channels = len(image_dictionary[image_name][f"fragment-{fragment_number}"][stack_number]["og channel names"])
                        if  number_of_channels != len(target_cycle) +1 and target_cycle != "AF":
                            image_dictionary[image_name][f"fragment-{fragment_number}"].pop(stack_number)
                            print(f"Stack {stack_number} in scanning area {fragment_number} in {image_name} did not meet the requirements in the naming of DAPI channels: {metadata.images[0].pixels.channels[0].name}",
                                  f"\nThe number of letters in the target cycle name did not match the number of channels: {target_cycle}, number of channels: {number_of_channels}",
                                  "\nThe stack was removed from registration\n")

                    else:
                        image_dictionary[image_name][f"fragment-{fragment_number}"].pop(stack_number)
                        print(f"Stack {stack_number} in scanning area {fragment_number} in {image_name} did not meet the requirements in the naming of DAPI channels: {metadata.images[0].pixels.channels[0].name}",
                              "\nThe stack was removed from registration\n")

        #Add cycle index to each stack instead of numbering by stack
        for fragment, fragment_dict in list(image_dictionary[image_name].items()):
            if len(fragment_dict.keys()) == 0:
                image_dictionary[image_name].pop(fragment)
                print(f"Scanning area {fragment} in image {image_name} was removed from registration due to not having any images to register")

            #Add cycle indexes 
            remove_stacks = []
            for index, stack in enumerate(sorted(fragment_dict.keys())):
                fragment_dict[f"cycle {index+1}"] = fragment_dict[stack]
                remove_stacks.append(stack)
                target_cycle = fragment_dict[f"cycle {index+1}"]["target cycle"]
                
                if image_name in rescans and target_cycle in rescans[image_name] and f"cycle {index+1}" not in rescans[image_name][target_cycle]:
                    rescans[image_name][target_cycle].append(f"cycle {index+1}")
            
            #Remove stacks
            for stack in remove_stacks:
                image_dictionary[image_name][fragment].pop(stack)

        if len(list(image_dictionary[image_name].keys())) == 0:
            image_dictionary.pop(image_name)
            print(f"Image {image_name} was removed from registration due to not having any images to register")

#Make a selection for all images
def select_images(image_dictionary):
    selected_images = {}
    image_root = tk.Tk()
    image_root.title("Select images to register")

    index = 0

    def submit():
        print("\033[1m'Removing unselected images and fragments from registration'\033[0m")
        for image_name, img_dic in list(selected_images.items()):
            for fragment, var in list(img_dic.items()):
                if var.get() == False:
                    image_dictionary[image_name].pop(fragment)
                    print(f"{image_name} \t Removed {fragment}") #not printing

            for fragment in list(image_dictionary[image_name].keys()):
                if len(image_dictionary[image_name][fragment].keys()) < 2:
                    print(f"{image_name} \t Removed {fragment} due to not containing enough cycles")

            if len(image_dictionary[image_name].values()) < 1:
                image_dictionary.pop(image_name)
                print(f"Removed image {image_name} from registration due to not having any images")

        image_root.destroy()

    for image_name, img_dic in image_dictionary.items():
        selected_images[image_name] = {}

        image_label = tk.Label(image_root, text = f"{image_name}:")
        image_label.grid(row = index, column = 0, padx = 10, pady = 5, sticky = "w")
        index +=1

        for fragment in img_dic.keys():
            var = tk.BooleanVar(value = True)
            check = tk.Checkbutton(image_root, text = fragment, variable = var, onvalue=True, offvalue=False)
            check.grid(row = index, column = 1, padx = 10, pady = 5, sticky = "w")
            selected_images[image_name][fragment]=var
            index += 1
    
    submit_button = tk.Button(image_root, text = "Submit", command = submit)
    submit_button.grid(row = index, column = 0, columnspan=2, pady =10)
    image_root.mainloop()

select_images(image_dictionary)

#Select cycles of re-scans 
def select_cycles(rescans, image_dictionary):

    def submit():
        print("\n\033[1m'Removing unselected re-scans from registrations'\033[0m")
        #Remove rescan cycles from image dictionary that are not choosen
        for image_name, selected_dic in dropdown_vars.items():
            print(f"{image_name}")
            for target_cycle, var in selected_dic.items():
                unselected_cycles = [c for c in rescans[image_name][target_cycle] if c!=var.get()]

            for fragment_key, fragment_dic in image_dictionary[image_name].items():
                for scan_cycle in list(fragment_dic.keys()):
                    if scan_cycle in unselected_cycles:
                        image_dictionary[image_name][fragment_key].pop(scan_cycle)
                        print(f"\t Removed {scan_cycle} from {fragment_key}")
                        
                        if scan_cycle in rescans[image_name][target_cycle]:
                            rescans[image_name][target_cycle].remove(scan_cycle)

        rescan_root.destroy()
    
    rescan_root = tk.Tk()
    rescan_root.title("Select rescan cycle")
    dropdown_vars = {}

    index = 0
    for image_name, rescan_dic in rescans.items():
        dropdown_vars[image_name] = {}
        image_label = tk.Label(rescan_root, text = f"{image_name}:")
        image_label.grid(row = index, column = 0, padx = 10, pady = 5, sticky = "w")
        index += 1

        for target_cycle, scan_cycles in rescan_dic.items():
            targetcycle_label = tk.Label(rescan_root, text = f"{target_cycle}:")
            targetcycle_label.grid(row = index, column = 0, padx = 10, pady = 5, sticky = "w")

            var = tk.StringVar(value = scan_cycles[0])
            dropdown = ttk.Combobox(rescan_root, textvariable=var, values = scan_cycles, state = "readonly")
            dropdown.grid(row = index, column = 1, padx = 10, pady=5)
            index += 1
            dropdown_vars[image_name][target_cycle]=var

    submit_button = tk.Button(rescan_root, text = "Submit", command = submit)
    submit_button.grid(row = index, column = 0, columnspan=2, pady =10)
    rescan_root.mainloop()

select_cycles(rescans, image_dictionary)

#Selecting target names
def select_target_names(channels):
    target_root =tk.Tk()
    target_root.title("Select target names")
    index = 0

    def get_targets():

        for target_cycle, target_dic in channel_names.items():
            if target_cycle != AF_cycle:
                for letter, target_name in target_dic.items():
                    channels[target_cycle][letter] = target_name.get() 
        target_root.destroy()

    channel_names = {}
    for target_cycle in channels:
        if target_cycle != "AF":
            label = tk.Label(target_root, text = target_cycle)
            label.grid(row = index, column =0,  padx = 10, pady=5)
            index += 1

            channel_names[target_cycle] = {}
            for letter in target_cycle:
                entry = tk.Entry(target_root)
                entry.grid(row = index, column = 1, padx = 10, pady=5)
                index += 1
                channel_names[target_cycle][letter] = entry
        
        else:
            channels[target_cycle]="Autofluorescence"

    submit_button = tk.Button(target_root, text = "Submit", command = get_targets)
    submit_button.grid(row = index, column = 0,columnspan=2, pady =10)
    target_root.mainloop()

select_target_names(channels)
#TODO: one target cycle which does not meet the requierements are in the channels list 

#Create pop-up window with all outputs before continuing 
def double_check_results(image_dictionary):
    checking_root = tk.Tk()
    checking_root.title("Double check registration output before starting registration")
    index = 0

    for img_index, (image_name, img_dic) in enumerate(image_dictionary.items()):
        Label = tk.Label(checking_root, text = f"\n{image_name}", font=("TkDefaultFont", 10, "bold"), anchor="w")
        Label.grid(row = index, column = 0, padx = 10, pady =5, sticky="w")
        Label = tk.Label(checking_root, text = f"\nNumber of scanning areas: {len(img_dic.keys())}", anchor="w")
        Label.grid(row = index, column = 1, padx = 10, pady = 5, sticky="w")
        index += 1

        if image_name in rescans:
            for target_cycle, cycle_list in rescans[image_name].items():
                Label = tk.Label(checking_root, text = f"Selected {cycle_list[0]} for targets {target_cycle} which had multiple rescans", anchor="w")
                Label.grid(row = index, column = 1, padx = 10, pady = 5, sticky="w")
                index += 1

        if (img_index == len(image_dictionary.keys())-1):
            channel_window = tk.Toplevel()
            channel_window.title(f"Channel names in image {image_name} in scanning area {scan_area}")
            text_box = tk.Text(channel_window, height = 20, width = 50)

        for scan_index, (scan_area, scan_area_dict) in enumerate(img_dic.items()):

            Label = tk.Label(checking_root,text = f"{scan_area} \t Number of cycles: {len(scan_area_dict.keys())}", anchor="w")
            Label.grid(row = index, column =1, padx = 10, pady = 5, sticky="w")
            index += 1

            for cycle, cycle_dict in list(scan_area_dict.items()):

                channel_index = 0; DAPI = cycle_dict["og channel names"][channel_index]
                channel_names = []; channel_names.append(DAPI); channel_index += 1; 

                if cycle_dict["target cycle"] == AF_cycle:
                    for channel in cycle_dict["og channel names"][1:]:
                        name = f"{channel}_{channels[cycle_dict["target cycle"]]}"
                        channel_names.append(name)

                else:
                    for letter, target_name in channels[cycle_dict["target cycle"]].items():
                        name = f"{letter}_{cycle_dict["og channel names"][channel_index]}_{target_name}"
                        channel_names.append(name)
                        channel_index += 1
                
                if scan_index == (len(img_dic.keys())-1) and (img_index == len(image_dictionary.keys())-1): 
                    text_box.insert(tk.END, f"{cycle_dict["target cycle"]}:\n")
                    for channel in channel_names:
                        text_box.insert(tk.END, f"{channel}\n")
                    text_box.insert(tk.END, "\n")

                image_dictionary[image_name][scan_area][cycle]["channel names"] = channel_names
        
    text_box.config(state="disabled")
    text_box.pack()
    close_button = tk.Button(channel_window, text = "Close", command = channel_window.destroy)
    close_button.pack(pady = 10)
    
    submit_button = tk.Button(checking_root, text = "Cancel", command = exit)
    submit_button.grid(row = index, column = 1,columnspan=2, pady =10)
    submit_button = tk.Button(checking_root, text = "Submit", command = checking_root.destroy)
    submit_button.grid(row = index, column = 0,columnspan=2, pady =10)
    checking_root.mainloop()

double_check_results(image_dictionary)

#TODO: add fixed cycles
#TODO: replace fragment with scan areas and make their name A1, A2 etc