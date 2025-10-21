import wsireg
from wsireg import WsiReg2D
import os
from tifffile import TiffWriter
import numpy as np 
#Initialiating registration graph
cycle_1_path = "E:\\frida\\002_003_cycle_1_TP241b.ome.tif"
cycle_2_path = "E:\\frida\\002_003_cycle_2_TP241b.ome.tif"
cycle_3_path = "E:\\frida\\002_003_cycle_3_TP241b.ome.ome.tif"
cycle_4_path = "E:\\frida\\002_003_cycle_4_TP241b.ome.ome.tif"

output_path = "E:\\frida"
pixelsize = 325

registration_path = output_path + "/TMA_4_cycles_correctedReg"
if not os.path.exists(registration_path): os.mkdir(registration_path)

os.path.exists(cycle_1_path)
os.path.exists(cycle_2_path)
os.path.exists(cycle_3_path)
os.path.exists(cycle_4_path)

reg_graph = WsiReg2D("registration_test",registration_path)

#Add image
reg_graph.add_modality(
    "cycle 1",
    cycle_1_path,
    image_res = 0.325,
    channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
    preprocessing= {
        "image_type" : "FL",
        "ch_indices": [0],
        "asuint8": True,
        "contrast_enhance" : True,
        "downsampling": 4,
    },
)
reg_graph.add_modality(
    "cycle 2",
    cycle_2_path,
    image_res = 0.325,
    channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
    preprocessing= {
        "image_type" : "FL",
        "ch_indices": [0],
        "asuint8": True,
        "contrast_enhance" : True,
        "downsampling": 4,
    },
)

reg_graph.add_modality(
    "cycle 3",
    cycle_3_path,
    image_res = 0.325,
    channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
    preprocessing= {
        "image_type" : "FL",
        "ch_indices": [0],
        "asuint8": True,
        "contrast_enhance" : True,
        "downsampling": 4,
    },
)

reg_graph.add_modality(
    "cycle 4",
    cycle_4_path,
    image_res = 0.325,
    channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
    preprocessing= {
        "image_type" : "FL",
        "ch_indices": [0],
        "asuint8": True,
        "contrast_enhance" : True,
        "downsampling": 4,
    },
)

reg_graph.add_reg_path(
    "cycle 1", #source modality
    "cycle 2", #modality to be added
    thru_modality=None,
    reg_params=["rigid", "affine", "nl"]
)

reg_graph.add_reg_path(
    "cycle 3", #source modality
    "cycle 2", #modality to be added
    thru_modality=None,
    reg_params=["rigid", "affine", "nl"]
)

reg_graph.add_reg_path(
    "cycle 4", #source modality
    "cycle 2", #modality to be added
    thru_modality="cycle 3",
    reg_params=["rigid", "affine", "nl"]
)

reg_graph.add_merge_modalities("merge", ['cycle 1', 'cycle 2', 'cycle 3', 'cycle 4'])
reg_graph.register_images()
reg_graph.save_transformations()
reg_graph.transform_images(file_writer="ome.tiff")
