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
from pandas.core.common import flatten
import numpy as np
from shapely.geometry import Polygon, box, mapping
from shapely.ops import transform
from shapely.ops import split
from shapely.wkt import loads
from shapely.affinity import translate
import pyproj
import shutil

from dggrid4py import DGGRIDv7, dgselect, dggs_types

from h3 import h3
import io

# import rhealpixdggs as rhpix
import rhealpixdggs.dggs as rhpix_dggs

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

dggrid_exec_path = os.getenv("DGGRID", default=shutil.which("dggrid"))
data_tmp_dir = os.getenv("TMP_DIR", default="/tmp")

MAX_CELLS = 100000

outformat_default = ["GPKG", "SHAPEZIP", "FLATGEOBUF", "GEOJSON", "KML"]

# fiona_drivers = ['ESRI Shapefile', 'FlatGeobuf', 'GeoJSON', 'GPKG', 'GML'}]

format_to_driver = {
        "GPKG" : "GPKG",
        "SHAPEZIP" : "ESRI Shapefile",
        "FLATGEOBUF" : "FlatGeobuf",
        "GEOJSON" : "GeoJSON",
        "GML" : "GML",
        "KML" : "KML"
        }

format_to_ext = {
        "GPKG" : "gpkg",
        "SHAPEZIP" : "shp",
        "FLATGEOBUF" : "fgb",
        "GEOJSON" : "geojson",
        "GML" : "gml",
        "KML" : "kml"
        }

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
    # fast_app.mount("/", StaticFiles(directory="static",html = True), name="static")
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
async def grid_gen(base_dggs: str,
                   resolution: int,
                   bbox: Union[str, None] = None,
                   format: Union[str, None] = None,
                   interrupt: Union[int, None] = None,
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

    out_format = "GEOJSON"

    if not format is None and format.upper() not in outformat_default:
        raise HTTPException(status_code=501, detail=f"current formats only {','.join(outformat_default)}")

    elif not format is None:
        out_format = format.upper()

    file_ext = format_to_ext[out_format]
    driver = format_to_driver[out_format]
    present_filename = f"{base_dggs}_{resolution}.{file_ext}"
    the_file, the_driver, dggs_ops = "", driver, {}

    if not interrupt is None and interrupt == 1:
        # fast return
        raise HTTPException(status_code=501, detail="Split dateline (interrupt cells) not yet implemented.")

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

        split_dateline = True if interrupt == 1 else False
        the_file, the_driver, dggs_ops = await grid_cell_polygons_for_extent(dggrid_instance=dggrid_instance,
                                                                   dggs_type=base_dggs.upper(),
                                                                   resolution=resolution,
                                                                   clip_geom=clip_geom,
                                                                   split_dateline=split_dateline,
                                                                   format=out_format)

    elif base_dggs.upper() == "H3":
        tmp_id = uuid.uuid4()
        tmp_dir = data_tmp_dir 
        df1 = get_h3_res()
        extent = None if clip_geom is None else mapping(clip_geom)
        gdf = create_h3_geometry(get_h3_cells(resolution, extent=extent))
        cell_output_file_name = str( (Path(tmp_dir) / f"temp_{base_dggs.upper()}_{resolution}_out_{tmp_id}.{file_ext}").resolve())
        gdf.to_file(cell_output_file_name, driver=driver)
        the_file = cell_output_file_name

    elif base_dggs.upper() == "RHEALPIX":
        tmp_id = uuid.uuid4()
        tmp_dir = data_tmp_dir 
        df1 = rhpix_get_res(resolution)
        extent = None if clip_geom is None else clip_geom.bounds
        gdf = create_rhpix_geometry(get_rhpix_cells(resolution, extent))
        cell_output_file_name = str( (Path(tmp_dir) / f"temp_{base_dggs.upper()}_{resolution}_out_{tmp_id}.{file_ext}").resolve())
        gdf.to_file(cell_output_file_name, driver=driver)
        the_file = cell_output_file_name

    else:
        raise HTTPException(status_code=400, detail=f"unknown dggs.")

    if not interrupt is None and interrupt == 1:
        the_file, the_driver, dggs_ops = await post_process_split_dateline(the_file, the_driver, dggs_ops)

    if format == "SHAPEZIP":
        # zip the shape files
        pass

    return FileResponse(path=the_file, filename=present_filename, media_type='application/octet-stream')


@router.get("/grid_stats/{base_dggs}")
async def grid_stats(base_dggs:str,
                   max_resolution: Union[int, None] = 15,
                   format: Union[str, None] = None,
                   dggrid_instance: DGGRIDv7 = Depends(get_dggrid)):

    tmp_id = uuid.uuid4()
    tmp_dir = data_tmp_dir 

    df1 = pd.DataFrame()

    if base_dggs.upper() in dggs_types and base_dggs.upper() not in ["H3", "RHEALPIX", "CUSTOM"]:
        df1 = await quick_stats(dggrid_instance, base_dggs.upper(), max_resolution)

    elif base_dggs.upper() == "H3":
        df1 = get_h3_res()

    elif base_dggs.upper() == "RHEALPIX":
        df1 = rhpix_get_res(max_resolution)

    else:
        raise HTTPException(status_code=400, detail=f"unknown dggs.")

    if not format is None and format.upper() == "CSV":
        the_file = Path(tmp_dir) / f"temp_{base_dggs.upper()}_{max_resolution}_out_{tmp_id}.csv"
        df1.to_csv(the_file, index=False)
        present_filename = f"{base_dggs}_{max_resolution}.csv"
        return FileResponse(path=the_file, filename=present_filename, media_type='application/octet-stream')
    else:
        return { base_dggs.upper() : df1.to_dict() }


async def quick_stats(dggrid_instance, dggs_type, max_resolution):
    df1 = dggrid_instance.grid_stats_table(dggs_type, max_resolution)
    return df1


async def grid_cell_polygons_for_extent(dggrid_instance, dggs_type, resolution, mixed_aperture_level=None, clip_geom=None, format="GEOJSON", split_dateline=False):
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

        file_ext = format_to_ext[format]
        driver = format_to_driver[format]

        output_conf = {
            'cell_output_type': 'GDAL',
            'cell_output_gdal_format' : driver,
            'cell_output_file_name': str( (Path(tmp_dir) / f"temp_{dggs_type}_{resolution}_out_{tmp_id}.{file_ext}").resolve())
            }

        dggs_ops = dggrid_instance.dgapi_grid_gen(dggs, subset_conf, output_conf )

        the_file = Path(tmp_dir) / f"temp_{dggs_type}_{resolution}_out_{tmp_id}.{file_ext}"
        the_driver = driver

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


async def post_process_split_dateline(the_file, the_driver, dggs_ops):
    # load file
    # apply split
    # write file
    gdf = gpd.read_file(the_file)

    cellsNew = gdf.iloc[:0].copy()
    # if we get eventually binning working we will have dynamic additional column for the binned values
    # cols = dict({ (idx, field) for idx, field in enumerate(gdf.columns)})

    for row in gdf.itertuples():
        poly = row.geometry
        coords = get_geom_coords(poly)

        if crosses_interruption(coords):
            geoms = interrupt_cell(coords)

            for geom in geoms:
                cellsNew.loc[len(cellsNew)] = [row.name, geom]
        else:
            cellsNew.loc[len(cellsNew)] = [row.name, poly]

    gdf.to_file(the_file)

    return the_file, the_driver, dggs_ops


def get_geom_coords(geometry):

    wkt = geometry.wkt
    wkt = wkt.replace("POLYGON ((","")
    wkt = wkt.replace("POLYGON ))","")
    wkt = wkt.split(", ")

    return wkt


def crosses_interruption(coords):

    lat_0 = float(coords[0].split(" ")[0])

    for i in range(1, len(coords)):
        lat_1 = float(coords[i].split(" ")[0])
        if (abs(lat_0 - lat_1) > 180):
            return True

    return False


def interrupt_cell(coords):

    result = []
    
    # Translate latitudes to east of 180ª 
    for i in range(len(coords)):
        lat = float(coords[i].split(" ")[0])
        if lat < 0:
            coords[i] = str(lat + 360) + " " + coords[i].split(" ")[1]

    coords = "POLYGON((%s))" % str(coords).replace("'","").replace("[","").replace("]","")
    poly = loads(coords)
    
    result.append(intersectEast.intersection(poly))
    result.append(translate(intersectWest.intersection(poly), xoff=-360))

    return result


def get_h3_cells(res, extent=None):
    if extent:
        set_hex = list(h3.polyfill_geojson(extent, res=res))
    else:    
        set_hex_0 = list(h3.get_res0_indexes())
        set_hex = []
        if res == 0:
            set_hex = set_hex_0
        else:
            for i in set_hex_0:
                set_hex.extend(list(h3.h3_to_children(i, res)))
    df = pd.DataFrame({"cell_id": set_hex})
    return df

def create_h3_geometry(df):
    gdf = gpd.GeoDataFrame(df)
    gdf['geometry'] = df['cell_id'].apply(lambda x: Polygon(h3.h3_to_geo_boundary(x, geo_json=True)))
    gdf.crs = 'EPSG:4326'
    return gdf


def get_h3_res():
    h3_res_text = """H3 Resolution	Average Hexagon Area km2	Average Hexagon Edge Length km	Number of unique indexes
    0	4,250,546.8477000	1,107.712591000	122
    1	607,220.9782429	418.676005500	842
    2	86,745.8540347	158.244655800	5,882
    3	12,392.2648621	59.810857940	41,162
    4	1,770.3235517	22.606379400	288,122
    5	252.9033645	8.544408276	2,016,842
    6	36.1290521	3.229482772	14,117,882
    7	5.1612932	1.220629759	98,825,162
    8	0.7373276	0.461354684	691,776,122
    9	0.1053325	0.174375668	4,842,432,842
    10	0.0150475	0.065907807	33,897,029,882
    11	0.0021496	0.024910561	237,279,209,162
    12	0.0003071	0.009415526	1,660,954,464,122
    13	0.0000439	0.003559893	11,626,681,248,842
    14	0.0000063	0.001348575	81,386,768,741,882
    15	0.0000009	0.000509713	569,707,381,193,162"""

    h3_buf = io.StringIO(h3_res_text)

    h3_res = pd.read_csv(h3_buf, sep="\t", thousands=",")
    h3_res = h3_res.rename(
        columns={col: col.lower().replace(" ", "_") for col in h3_res.columns}
    ).set_index("h3_resolution")
    h3_res["average_hexagon_area_m2"] = np.float32(
        h3_res["average_hexagon_area_km2"] * 1000000
    )
    h3_res["average_hexagon_edge_length_m"] = np.float32(
        h3_res["average_hexagon_edge_length_km"] * 1000
    )
    return h3_res


def get_rhpix_geoid():
    rhpix_geoid = rhpix_dggs.WGS84_003
    return rhpix_geoid


def get_rhpix_cells(res, extent=None):
    rdggs = get_rhpix_geoid()
    if extent:
        se = (extent[1], extent[2])
        nw = (extent[3], extent[0])
        set_hex = list(flatten(rdggs.cells_from_region(res, se, nw, plane=False)))
    else:
        set_hex = [x for x in rdggs.grid(res)]

    df = pd.DataFrame({"cell_id": set_hex})

    return df


def __cell_to_geometry(cell):
    geom = None
    try:
        # geom =  Polygon(__lonlat_to_latlon(cell.boundary(n=2,plane=False)))
        # gdf['geometry'] = gdf['cell_id'].apply(lambda x: Polygon(x.boundary(n=2,plane=False)))
        geom = Polygon(cell.boundary(n=2,plane=False))
    except:
        print(f'internal rhealpix error with cell.boundary method for {str(cell)}')
    return geom


def create_rhpix_geometry(df):

    gdf = gpd.GeoDataFrame(df.copy())
    gdf['geometry'] = gdf['cell_id'].apply(__cell_to_geometry)

    gdf.crs = 'EPSG:4326'
    gdf['cell_id'] = gdf['cell_id'].apply(lambda x: str(x))

    return gdf


def rhpix_get_res(max_res=16):
    rhpix_geoid = get_rhpix_geoid()
    rhpix_resolutions = []
    for i in range(0, max_res, 1):
        rhpix_resolutions.append([i, rhpix_geoid.cell_width(i)])
    rhpix_res = (
        pd.DataFrame(rhpix_resolutions)
        .rename(columns={0: "rhpix_resolution", 1: "average_cell_width_m"})
        .set_index("rhpix_resolution")
    )
    return rhpix_res


if __name__ == '__main__':
    app = create_app()
    uvicorn.run(app=app)

