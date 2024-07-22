# 必須由ArcGIS的python環境執行
import shutil

import arcpy
import os
import glob

from PIL import Image
from arcpy.sa import ZonalStatisticsAsTable

from configs.config import workspace, SHP_Path, IMG_Path, raster_Mask_Path, Tool_box, directory, raster_PGW_Path, TIF_Path

import numpy as np

def resize_predict_img():
    preidct_IMG_Path = IMG_Path + "/*.png"
    files = glob.glob(preidct_IMG_Path)
    
    # _all_tif_paths:list[str]=glob.glob(directory + "/" + TIF_Path + "/*.tif")
    _all_tif_paths:list[str]=glob.glob(TIF_Path + "/*.tif")
    for file in files:
        # obtain img name
        file_name = format(os.path.basename(file).split('.')[0])
        imgname = file_name.split("_")

        # obtain the width and height of the corresponding tif
        _tif_img_path=None
        for t in _all_tif_paths:
            if  t.find(imgname[2] + "_" + imgname[3])>-1:
                _tif_img_path=t
                break

        _tif_img=arcpy.RasterToNumPyArray(_tif_img_path)
        _tif_img = np.transpose(_tif_img, (1, 2, 0))
        _tif_height, _tif_width, band = _tif_img.shape
        
        print(os.path.basename( _tif_img_path))
        print("_tif_width : ", _tif_width)
        print("_tif_height : ", _tif_height)
        
        # copy 2 pgw_path and resize
        new_img = directory + "/" + raster_PGW_Path + "/" + imgname[2] + "_" + imgname[3] + ".png"
        im = Image.open(file)
        im = im.resize((_tif_width, _tif_height), Image.NEAREST)
        im.save(new_img)

        # img in raster_PGW_Path is now resized to fit tif


# ## change parameter "shp" as shpPath
def __generate_average_mask(workspace, shpPath, raster_file_name, out_name):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True
    arcpy.env.qualifiedFieldNames = False
    arcpy.ImportToolbox(Tool_box)
    # Model Environment settings
    with arcpy.EnvManager(scratchWorkspace=workspace,
                          workspace=workspace):
        prediction_raster_with_pgw = arcpy.Raster(raster_file_name)

        # Process: Polygon to Raster (Polygon to Raster) (conversion)
        arcpy.CheckOutExtension("Spatial")

        # Process: Raster To Other Format (Raster To Other Format) (conversion)
        print("raster to other format")

        outZSaT = ZonalStatisticsAsTable(shpPath, "FID", prediction_raster_with_pgw, "zonalstattblout1", "NODATA", "MEAN")

        # Set local variables

        # ##inFeatures = directory + "/" + shp
        inFeatures = shpPath
        joinTable = outZSaT
        joinField = "FID"
        outFeature = out_name

        veg_joined_table = arcpy.AddJoin_management(inFeatures, joinField, joinTable, joinField)
        arcpy.management.CopyFeatures(veg_joined_table, outFeature)
        arcpy.DeleteField_management(outFeature, ["FID_1","COUNT"])
        
        # SAVE to raster
        arcpy.FeatureClassToShapefile_conversion(outFeature, raster_Mask_Path)



def generate_average_mask():
    if os.path.isdir(raster_Mask_Path):
        shutil.rmtree(raster_Mask_Path)
    os.mkdir(raster_Mask_Path)
    resize_predict_img()
    All_IMG_Path = TIF_Path + "/*.tif"
    tif_files= glob.glob(All_IMG_Path)

    for tif_file in tif_files:
        tif_file_name = format(os.path.basename(tif_file ).split('.')[0])
        out_name = "Prediction_"  + format(os.path.basename(tif_file).split('_')[0]) +"_"+format(os.path.basename(tif_file).split('_')[1])
        shp_name = SHP_Path + "/" + "PD_"+tif_file_name +  ".shp"
        raster_file_name = raster_PGW_Path + "/" + format(os.path.basename(tif_file).split('_')[0]) +"_"+format(os.path.basename(tif_file).split('_')[1])+  ".png"
        print("raster_file_name :" + raster_file_name )
        print("shp_name:" + shp_name)
        print("out_name:" + out_name)

        __generate_average_mask(workspace, shp_name, raster_file_name , out_name)
