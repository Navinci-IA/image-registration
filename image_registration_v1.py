from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, ttk

#Set up GUI
root = tk.Tk()
root.title("Set up registration parameters")

#Ask user for directory to images 
root.withdraw()
path = filedialog.askdirectory()
root.deiconify()
root.resizable(True, True)

#project folder configurations
project_folder = list(Path(path).glob("*.vsi"))
"""
#setting up tkinter progress bar
status_label = tk.Label(root, text = f"Starting registration in folder {Path(path).name}...")
status_label.grid(row=0, column=0, columnspan=2, padx=10, sticky="w")

progress_bar_fixed = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 1)
progress_bar_fixed['value']=0
fixed_label = tk.Label(root, text="Slides to be registered")
fixed_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
progress_bar_fixed.grid(row=1, column=1, padx=10, pady=5)

progress_bar_steps = ttk.Progressbar(root, orient="horizontal", length = 200, mode = 'determinate', takefocus=True, maximum = 4)
progress_bar_steps['value']=0
step_label = tk.Label(root, text="Performing registration step (0/4)")
step_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
progress_bar_steps.grid(row=3, column=1, padx=10, pady=5)

cancel_button = ttk.Button(root, text = "Cancel", command = exit)
cancel_button.grid(row=4, column=1, padx=10, pady=5)
root.update_idletasks()
"""
images = {}
#Sorting up image cycles 
for vsi_file in project_folder:
    img_name = vsi_file.stem
    img_folder = vsi_file.parent/f"_{img_name}_"
    
    if img_folder.exists(): #If there is a vsi image folder
        images[img_name]={} #Saving the image to the image dictionary 
        cycle_index = 0
        for f in img_folder.iterdir():
            if f.is_dir() and f.name.startswith("stack") and f.name[5:].isdigit() and int(f.name[5:])>=10002:
                images[img_name][f"Cycle {(int(f.name[5:])-10002)//3+1}"]={
                    "path":f/f"frame_t_0.tif" 
                }
                cycle_index += 1
selected = {}

def submit():
    for img_name, tif_files in selected.items():
        for tif, var in tif_files.items():
            if var.get() == False:
                images[img_name].pop(cycle,None)
            if len(images[img_name])==0:
                images.pop(img_name,None)
    root.destroy()

# Create checkboxes
#checkbox_frame = tk.Toplevel(root)
#checkbox_frame.title("Select stacks")
for img_name, tifs in images.items():
    frame = ttk.LabelFrame(root, text=img_name)
    frame.pack(fill="x", padx=10, pady=5)
    selected[img_name] = {}
    for cycle, tif_file in tifs.items():
        var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(frame, text=cycle, variable=var)  # Optional: use .name for cleaner label
        chk.pack(anchor="w")
        selected[img_name][cycle] = var

ttk.Button(root, text="Submit", command=submit).pack(pady=10)
root.mainloop()

#Make channel names 
target_names = {
                " ABC": ["DAPI", "PD-1/PD-L1", "PD-1/PD-L2", "CD8/MHC-I"],
                " DEF": ["DAPI", "CD4/MHC-II", "TIGIT/TIGIT", "B7-H3/B7-H3"],
                " GHI": ["DAPI", "LAG3/LAG3", "CD19/CD19", "Blank/Blank"]
}

channels = ["DAPI", "Cy5", "Cy3N", "FITC"]
channel_names = {}
for cycle_index, targets in target_names.items():
    channel_names[cycle_index] = [
        f"{channels[channel_index]}_{cycle_index[channel_index]}_{target}" if target != channels[channel_index].replace(" ","")
        else f"{target}_{cycle_index}".replace(" ","")
        for channel_index, target in enumerate(targets)
    ]
channel_names["Autofluorescence"] = [f"{ch}_Autofluroescence" for ch in channels]

root = tk.Tk()
root.title("Select channel lists for all cycles")

def choose_channels():
    selections = {}

    def update_display(event, combo, label):
        selected_key = combo.get()
        if selected_key:
            formatted_channels = "\n".join(f"   • {ch}" for ch in channel_names[selected_key])
            label.config(text=formatted_channels)
        else:
            label.config(text="")

    row = 0
    for img_name, cycles in images.items():
        # Image title
        img_frame = ttk.LabelFrame(root, text=f"Image: {img_name}")
        img_frame.pack(fill="x", padx=10, pady=5)

        for cycle_name in cycles:
            frame = tk.Frame(img_frame)
            frame.pack(fill="x", padx=5, pady=2)

            label = tk.Label(frame, text=f"{cycle_name}", width=20, anchor="w")
            label.pack(side="left")

            combo = ttk.Combobox(frame, values=list(channel_names.keys()), state="readonly", width=30)
            combo.pack(side="left", padx=5)

            channel_display = tk.Label(frame, text="", justify="left", anchor="w")
            channel_display.pack(side="left", padx=10)

            combo.bind("<<ComboboxSelected>>", lambda e, c=combo, l=channel_display: update_display(e, c, l))

            selections[(img_name, cycle_name)] = combo

    def submit_all():
        for img_name in images:
            used_keys = set()
            for cycle_name in images[img_name]:
                selected_key = selections[(img_name, cycle_name)].get()
                if not selected_key:
                    tk.messagebox.showerror("Missing Selection", f"No channel list selected for {img_name} - {cycle_name}")
                    return
                if selected_key in used_keys:
                    tk.messagebox.showerror("Duplicate Selection", f"Channel list '{selected_key}' is used more than once in image '{img_name}'. Please choose unique lists for each cycle.")
                    return
                used_keys.add(selected_key)
                images[img_name][cycle_name]["channel list"] = channel_names[selected_key]
        root.destroy()

    ttk.Button(root, text="Submit", command=submit_all).pack(pady=10)
    root.mainloop()

choose_channels()
"""
for im, cycles in images.items():
    print(im)
    for cs, info in cycles.items():
        print("\t", cs)
        for keys, values in info.items():
            print("\t", "\t", keys, values)
"""
