import wsireg
from wsireg import WsiReg2D
import os
from tifffile import TiffWriter
from tifffile import imread
from wsireg.reg_images.loader import reg_image_loader
import numpy as np 

#Initialiating registration graph
cycle_1_path = "P:\\9_Olympus_Scanner\\Frida\\scanning_test\\save as tif\\_Image_first_image_tif_\\stack10002\\frame_t_0.tif"
#"P:\\9_Olympus_Scanner\\Frida\\scanning_test\\save as tif\\Image_first_image.btf"
cycle_2_path =  "P:\\9_Olympus_Scanner\\Frida\\scanning_test\\save as tif\\_Image_first_image_tif_\\stack10005\\frame_t_0.tif"#"P:\\9_Olympus_Scanner\\Frida\\scanning_test\\save as tif\\Image_second_image.btf"
output_path = "E:\\frida\\btf files test"
pixelsize = 325

registration_path = output_path + "/tif instead of ets files test"
if not os.path.exists(registration_path): os.mkdir(registration_path)

os.path.exists(cycle_1_path)
os.path.exists(cycle_2_path)

cycle_1 = imread(cycle_1_path)
cycle_2 = imread(cycle_2_path)

reg_graph = WsiReg2D("registration_test",registration_path)

#Add image
reg_graph.add_modality(
    "cycle 1",
    cycle_1,
    image_res = 0.325,
    channel_names = ["DAPI","FITC", "Cy5", "Cy3N"],
    preprocessing= {
        "image_type" : "FL",
        "ch_indices": [0],
        "asuint8": True,
        "contrast_enhance" : True,
        "downsampling": 2,
    },
)
reg_graph.add_modality(
    "cycle 2",
    cycle_2,
    image_res = 0.325,
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
    "cycle 1", #source modality
    "cycle 2", #modality to be added
    thru_modality=None,
    reg_params=["rigid", "affine", "nl"]
)

reg_graph.add_merge_modalities("merge", ['cycle 1', 'cycle 2'])
reg_graph.register_images()
reg_graph.save_transformations()
reg_graph.transform_images(file_writer="ome.tiff")
