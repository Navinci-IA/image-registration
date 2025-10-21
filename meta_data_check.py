from ome_types import from_tiff
import tifffile as tif 
image_path = "E:\\frida\\Scanning_test\\scanning_test\\registration_test-merge_merged-registered.ome.tiff"
image_path_2 = "P:\\9_Olympus_Scanner\\Frida\\scanning_test\\save as tif\\Image_first_image_Overview.btf"


with tif.TiffFile(image_path) as img:
    #print(img.pages[0].description)
    print(img)

print("\n")
with tif.TiffFile(image_path_2) as img:
    #print(img.pages[0].description)
    print(img)