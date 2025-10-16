from pathlib import Path
import os
import re
from wsireg import WsiReg2D
from tkinter import ttk
import tkinter

path = "E:\\frida\\1012"
project_folder = list(Path(path).glob("*.ome.tif")) + list(Path(path).glob("*.btf"))
image_dict = {}

pattern = re.compile(r"(.+?_.+?)_(.+?)_(.+?\.ome\.tif|.+?\.btf)$")
fixed_image_pattern = "stained"

#Starting registration
for file in project_folder:
    match = pattern.match(file.name)
    slide, cycle, end = match.groups()
    if f"{slide}" not in image_dict.keys():
        image_dict[f"{slide}"] = [file]
    else: 
        image_dict[f"{slide}"].append(file)

#setting up tkinter progress bar
root = tkinter.Tk()
progress_bar = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum=len(image_dict.keys()))
status_label = tkinter.Label(root, text = f"Starting registration in folder {project_folder.name}...")
progress_bar['value']=0
progress_bar.pack()
status_label.pack()

for slide, slide_images in image_dict.items():
    status_label.config(text = f"Processing slide: {slide}")
    fixed_image = next((file for file in slide_images if fixed_image_pattern in file.name), None)
    reg_graph = WsiReg2D(slide, path)

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

    for modality in slide_images :
        if modality != fixed_image:
            slide, cycle, end  = pattern.match(file.name).groups()
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
    print(reg_graph.modalities())
    reg_graph.add_merge_modalities("registered", cycle_list)
    reg_graph.register_images()
    reg_graph.save_transformations()
    reg_graph.transform_images(file_writer="ome.tif", remove_merged=False)

    progress_bar['value']+=1

root.mainloop()
