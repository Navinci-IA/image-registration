from pathlib import Path
import re
from tkinter import ttk
import tkinter
from tkinter import filedialog

#Set up GUI
root = tkinter.Tk()
root.title("Registration")

#Ask user for directory
root.withdraw()
path = filedialog.askdirectory()
root.deiconify()

#project folder configurations
project_folder = list(Path(path).glob("*.ome.tif")) + list(Path(path).glob("*.btf"))
image_dict = {}
pattern = re.compile(r"(.+?_.+?)_(.+?)_(.+?\.ome\.tif|.+?\.btf)$")
fixed_image_pattern = "stained"

#setting up tkinter progress bar
progress_bar_fixed = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 1)

progress_bar_mods = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 1)

status_label = tkinter.Label(root, text = f"Starting registration in folder {Path(path).name}...")
progress_bar_fixed['value']=0
progress_bar_mods['value']=0
progress_bar_fixed.pack()
progress_bar_mods.pack()
status_label.pack()
#Note to self: is it possible to have a cancel in the progress bar?
root.update_idletasks()

#Starting registration
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
        status_label.config(text = f"Processing slide: {slide}")
        progress_bar_mods['value']=0
        progress_bar_mods["maximum"] = len(slide_images)
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
        reg_graph.register_images()
        reg_graph.save_transformations()
        reg_graph.transform_images(file_writer="ome.tif", remove_merged=False)
        
        
        progress_bar_fixed['value']+=1
        root.update_idletasks()

progress_bar_fixed['value']+=1
root.after(100, run_registration)
root.mainloop()
