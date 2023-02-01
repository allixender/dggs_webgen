import os
from pathlib import Path
import uuid
import logging

import uvicorn as uvicorn
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from typing import Union
import model
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from shapely.ops import transform
import pyproj
import shutil

from dggrid4py import DGGRIDv7, dgselect, dggs_types

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

dggrid_exec_path = os.getenv("DGGRID", default=shutil.which("dggrid"))
data_tmp_dir = os.getenv("TMP_DIR", default="/tmp")

MAX_CELLS = 100000

outformat_default = ["GPKG", "SHAPEZIP", "FLATGEOBUF", "GEOJSON", "KML"]

if os.path.isfile(dggrid_exec_path) == False:
    raise ValueError("Problem, dggrid_exec_path not a file")

# dependency

def get_dggrid():
    # create an inital instance that knows where the dggrid tool lives, configure temp workspace and log/stdout output
    dggrid_instance = DGGRIDv7(executable=dggrid_exec_path,
                           working_dir=data_tmp_dir,
                           capture_logs=True,
                           silent=True)

    try:
        yield dggrid_instance
    finally:
        del dggrid_instance



router = APIRouter(prefix="/api")


def create_app():
    # app = FastAPI()
    fast_app = FastAPI()
    fast_app.mount("/", StaticFiles(directory="static",html = True), name="static")
    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    fast_app.include_router(router)
    return fast_app

logger = logging.getLogger(__name__)

# @router.on_event("startup")
# async def startup_event():
#     logger = logging.getLogger("uvicorn.access")
#     handler = logging.StreamHandler()
#     handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
#     logger.addHandler(handler)


@router.get("/")
def home():
    msg = f"dggrid: {dggrid_exec_path}; tmp_dir: {data_tmp_dir} -> ready player 1"
    return model.SimpleMessage(status="OK", message=msg)


@router.get("/grid_gen/{base_dggs}/{resolution}")
async def grid_gen(base_dggs:str,
                   resolution:int,
                   bbox: Union[str, None] = None,
                   format: Union[str, None] = None,
                   dggrid_instance: DGGRIDv7 = Depends(get_dggrid)):
    clip_geom = None
    if not bbox is None:
        try:
            logger.info(f"bbox is {bbox}")
            box_arr = list( map( lambda d: float(d), bbox.split(",") ) )
            ops = dict({ (a,b) for a,b in  zip(['minx', 'miny', 'maxx', 'maxy'], list(box_arr) )})
            clip_geom = box(**ops)
        except Exception as ex:

            logger.error(ex)
            raise HTTPException(status_code=400, detail=f"bbox format must be comma-separated int or float: minx,miny,maxx,maxy")


    if not format is None and format.upper() not in outformat_default:
        raise HTTPException(status_code=501, detail=f"current formats only {','.join(outformat_default)}")


    if base_dggs.upper() in dggs_types and base_dggs.upper() not in ["H3", "RHEALPIX", "CUSTOM"]:

        reso_fits = True
        df1 = await quick_stats(dggrid_instance, base_dggs.upper(), resolution)
        num_cells = df1.loc[df1["Resolution"] == resolution]["Cells"].values[0]
        per_cell_area = df1.loc[df1["Resolution"] == resolution]["Area (km^2)"].values[0]
        if not clip_geom is None:
            target_area = await project_geom(clip_geom).area
            num_cells = int(target_area / 1000000 / per_cell_area)
            print(f"bbox target area = {target_area} / num_cells {num_cells}")

        gen_info = f"{base_dggs.upper()} - res {resolution} - has_bbox {clip_geom} - per_cell_area {per_cell_area} - est. num cells {num_cells} > MAX_CELLS {MAX_CELLS}"
        print(gen_info)

        if num_cells > MAX_CELLS:
            raise HTTPException(status_code=403, detail=f"response too big. {gen_info}")

        the_file, the_driver, dggs_ops = await grid_cell_polygons_for_extent(dggrid_instance=dggrid_instance,
                                                                   dggs_type=base_dggs.upper(),
                                                                   resolution=resolution,
                                                                   clip_geom=clip_geom)

        # return { "status":"OK", "message" : f"Seems ok, {the_file} cells produced with {the_driver}.", "dggs_ops" : dggs_ops}
        present_filename = f"{base_dggs}_{resolution}.geojson"
        return FileResponse(path=the_file, filename=present_filename, media_type='application/octet-stream')

    elif base_dggs in ["H3", "RHEALPIX"]:
        raise HTTPException(status_code=501, detail=f"not yet implemented.")
    else:
        raise HTTPException(status_code=400, detail=f"unknown dggs.")


@router.get("/grid_stats/{base_dggs}")
async def grid_stats(base_dggs:str,
                   max_resolution: Union[int, None] = 15,
                   format: Union[str, None] = None,
                   dggrid_instance: DGGRIDv7 = Depends(get_dggrid)):

    tmp_id = uuid.uuid4()
    tmp_dir = data_tmp_dir 

    if base_dggs.upper() in dggs_types and base_dggs.upper() not in ["H3", "RHEALPIX", "CUSTOM"]:
        df1 = await quick_stats(dggrid_instance, base_dggs.upper(), max_resolution)
        if not format is None and format.upper() == "CSV":
            the_file = Path(tmp_dir) / f"temp_{base_dggs.upper()}_{max_resolution}_out_{tmp_id}.csv"
            df1.to_csv(the_file, index=False)
            present_filename = f"{base_dggs}_{max_resolution}.csv"
            return FileResponse(path=the_file, filename=present_filename, media_type='application/octet-stream')
        else:
            return { base_dggs.upper() : df1.to_dict() }

    elif base_dggs in ["H3", "RHEALPIX"]:
        raise HTTPException(status_code=501, detail=f"not yet implemented.")
    else:
        raise HTTPException(status_code=400, detail=f"unknown dggs.")


async def quick_stats(dggrid_instance, dggs_type, max_resolution):
    df1 = dggrid_instance.grid_stats_table(dggs_type, max_resolution)
    return df1


async def grid_cell_polygons_for_extent(dggrid_instance, dggs_type, resolution, mixed_aperture_level=None, clip_geom=None, split_dateline=False):
        """
        generates a DGGS grid and returns all the cells as Geodataframe with geometry type Polygon
            a) if clip_geom is empty/None: grid cell ids/seqnms for the WHOLE_EARTH
            b) if clip_geom is a shapely shape geometry, takes this as a clip area
        """
        tmp_id = uuid.uuid4()
        tmp_dir = data_tmp_dir 
        dggs = dgselect(dggs_type = dggs_type, res= resolution, mixed_aperture_level=mixed_aperture_level)

        subset_conf = { 'update_frequency': 100000, 'clip_subset_type': 'WHOLE_EARTH' }

        if not clip_geom is None and clip_geom.area > 0:

            clip_gdf = gpd.GeoDataFrame(pd.DataFrame({'id' : [1], 'geometry': [clip_geom]}), geometry='geometry', crs=4326)
            clip_gdf.to_file(Path(tmp_dir) / f"temp_clip_{tmp_id}.{dggrid_instance.tmp_geo_out['ext']}", driver=dggrid_instance.tmp_geo_out['driver'] )

            subset_conf.update({
                'clip_subset_type': 'GDAL',
                'clip_region_files': str( (Path(tmp_dir) / f"temp_clip_{tmp_id}.{dggrid_instance.tmp_geo_out['ext']}").resolve()),
                })

        output_conf = {
            'cell_output_type': 'GDAL',
            'cell_output_gdal_format' : dggrid_instance.tmp_geo_out['driver'],
            'cell_output_file_name': str( (Path(tmp_dir) / f"temp_{dggs_type}_{resolution}_out_{tmp_id}.{dggrid_instance.tmp_geo_out['ext']}").resolve())
            }

        dggs_ops = dggrid_instance.dgapi_grid_gen(dggs, subset_conf, output_conf )

        the_file = Path(tmp_dir) / f"temp_{dggs_type}_{resolution}_out_{tmp_id}.{dggrid_instance.tmp_geo_out['ext']}"
        the_driver = dggrid_instance.tmp_geo_out['driver']

        return (the_file, the_driver, dggs_ops)


async def project_geom(geom):
    minx, miny, maxx, maxy = geom.bounds
    lon_centre = maxx - minx
    lat_centre = maxy - miny
    proj4_txt = f'+proj=aeqd +lat_0={lat_centre} +lon_0={lon_centre} +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
    from_crs = pyproj.CRS(f'EPSG:4326')
    to_crs = pyproj.CRS(proj4_txt)

    transformer = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True).transform

    aeqd_geom = transform(transformer, geom)
    return aeqd_geom


if __name__ == '__main__':
    app = create_app()
    uvicorn.run(app=app)

