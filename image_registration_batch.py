from pathlib import Path
import re
from tkinter import ttk
import tkinter
from tkinter import filedialog

#Set up GUI
root = tkinter.Tk()
root.title("Registration")

#Ask user for directory to images 
root.withdraw()
path = filedialog.askdirectory()
root.deiconify()
root.geometry("400x200")
root.resizable(True, True)

#project folder configurations
project_folder = list(Path(path).glob("*.ome.tif")) + list(Path(path).glob("*.btf"))
image_dict = {}
pattern = re.compile(r"(.+?_.+?)_(.+?)_(.+?\.ome\.tif|.+?\.btf)$")
fixed_image_pattern = "stained"

#setting up tkinter progress bar
status_label = tkinter.Label(root, text = f"Starting registration in folder {Path(path).name}...")
status_label.grid(row=0, column=0, columnspan=2, padx=10, sticky="w")

progress_bar_fixed = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 1)
progress_bar_fixed['value']=0

progress_bar_mods = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 1)
progress_bar_mods['value']=0

progress_bar_steps = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 3)
progress_bar_steps['value']=0

cancel_button = ttk.Button(root, text = "Cancel", command = exit)

for i, (label_text, bar) in enumerate([
    ("Slides to be registered", progress_bar_fixed),
    ("Adding cycles to registration", progress_bar_mods),
    ("Registration steps", progress_bar_steps)
]):
    tkinter.Label(root, text=label_text).grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
    bar.grid(row=i+1, column=1, padx=10, pady=5)

cancel_button.grid(row=4, column=1, padx=10, pady=5)
root.update_idletasks()

#Sorting up image cycles 
for file in project_folder:
    match = pattern.match(file.name)
    slide, cycle, end = match.groups()
    if f"{slide}" not in image_dict.keys():
        image_dict[f"{slide}"] = [file]
    else: 
        image_dict[f"{slide}"].append(file)

progress_bar_fixed["maximum"] = len(image_dict.keys())

from wsireg import WsiReg2D
def run_registration():
    for slide, slide_images in image_dict.items():
        #Updating tkinter GUI
        status_label.config(text = f"Processing slide: {slide}")
        progress_bar_mods['value']=0
        progress_bar_mods["maximum"] = len(slide_images)
        root.after(20)
        root.update_idletasks()

        fixed_image = next((file for file in slide_images if fixed_image_pattern in file.name), None)
        reg_graph = WsiReg2D(slide, path)
        
        if fixed_image==None:
            continue
        cycle_list = [fixed_image_pattern]
        
        #Adding the fixed image
        reg_graph.add_modality(
            fixed_image_pattern,
            fixed_image,
            image_res=0.325,
            channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
            preprocessing= {
                "image_type" : "FL",
                "ch_indices": [0],
                "asuint8": True,
                "contrast_enhance" : True,
                "downsampling": 2,
            },
        )
        progress_bar_mods['value'] += 1

        for modality in slide_images :
            if modality != fixed_image:
                slide, cycle, end  = pattern.match(modality.name).groups()
                cycle_list.append(cycle)

                reg_graph.add_modality(
                    cycle,
                    modality,
                    image_res=0.325,
                    channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
                    preprocessing= {
                        "image_type" : "FL",
                        "ch_indices": [0],
                        "asuint8": True,
                        "contrast_enhance" : True,
                        "downsampling": 2,
                    },
                )

                reg_graph.add_reg_path(
                    cycle,
                    fixed_image_pattern,
                    thru_modality=None,
                    reg_params=["rigid", "affine", "nl"]
                )
                progress_bar_mods['value'] += 1
                root.update_idletasks()

        progress_bar_mods['value'] += 1
        root.update_idletasks()

        reg_graph.add_merge_modalities("registered", cycle_list)
        progress_bar_steps['value'] += 1
        root.update_idletasks()

        reg_graph.register_images()
        progress_bar_steps['value'] += 1
        root.update_idletasks()
        
        reg_graph.save_transformations()
        reg_graph.transform_images(file_writer="ome.tif", remove_merged=True)
        progress_bar_steps['value'] += 1
        progress_bar_fixed['value']+=1
        root.update_idletasks()

root.after(100, run_registration)
root.mainloop()
progress_bar_fixed['value']+=1
