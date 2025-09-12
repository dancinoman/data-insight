import os
import re
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
# Import custom modules
from config import Path



def convert_poverty_files():

    path = Path("downloads", "xlsx-files", "csv-files")
    path_source = path.get_source_path()
    path_destination = path.get_destination_path()

    def fix_values_shifted(df, row_number):
        """Fix columns shifted by one row in the DataFrame."""
        # Fix the first column shifted by one row
        df.iloc[row_number,0] = str(df.iloc[row_number, 0]) + str(df.iloc[row_number, 1])

        # Fix all other columns shifted by one row
        for col in range(1, len(df.columns[1:])):
            df.iloc[row_number, col] = df.iloc[row_number, col +1]

        return df[df.columns[:-1]]  # Remove the last column which is now empty

    def remove_quotes(df):
        """Remove quotes from DataFrame column and values"""
        df.columns = [col.replace('"', '') for col in df.columns.tolist()]
        df.loc[:,"Catégorie"] = df["Catégorie"].map(lambda x: x.replace('"', '') if isinstance(x, str) else x)
        return df

    def pivot(df):
        df_melted = df.melt( id_vars='Catégorie', var_name='Région', value_name='Value')
        df_pivoted = df_melted.pivot(index='Région', columns='Catégorie', values='Value').reset_index()
        return df_pivoted

    def execute_poverty_creation():
        """Execute the conversion of Excel files to CSV format."""

        extract_duplicate_columns = True

        # Process each file in the source directory
        for i,filename in enumerate(os.listdir(path_source)):

            # Extract duplicate columns
            with open(os.path.join(path_source, filename), 'rb') as file:
                df = pd.read_excel(file, engine='openpyxl')

                df_fixed = fix_values_shifted(df, 5)
                df_fixed = remove_quotes(df_fixed)

                #Filter the DataFrame with first file and filter the relevant columns for the others
                if extract_duplicate_columns:
                    df_filtered = df_fixed.iloc[:, :-2]
                    neighbour = "city"
                    df_pivoted = pivot(df_filtered)
                    df_pivoted.to_csv(os.path.join(path_destination, f"poverty_family_structure_{neighbour}.csv"), index=False)
                    extract_duplicate_columns = False

                df_filtered = df_fixed.iloc[:, [0, -2, -1]]
                neighbour = re.search(r"_([^_.]+)\.[^.]+$", filename).group(1)

                df_pivoted = pivot(df_filtered)
                df_pivoted.to_csv(os.path.join(path_destination, f"poverty_family_structure_{neighbour}.csv"), index=False)

    # Execute the conversion process
    execute_poverty_creation()

def clean_coverage():
    # Load file
    path = Path('data','police_coverage','police_coverage')
    df = pd.read_csv(path.get_source_path() + '/police_coverage_sector.csv')

    # remove the polygon that is not closed
    df = df.drop(index=1)

    # Save cleaned file
    df.to_csv(path.get_destination_path() + '/police_coverage_sector_cleaned.csv', index=False)



def associate_points_with_districts():
    """
    Load crime with points and compare which distrcict they belong to.
    With that polygon on hand, we can calculate the centroid of each district.
    Dataset crime: new "nom_arr" column
    Dataset municipality: new "centroid_longidue" and "centroid_latitude" columns
    """
    # Centralize polygon
    def geocenter(id, points):
        centroids_projected = points.to_crs(epsg=2950)
        centroids_projected['geometry_centroid'] = centroids_projected.geometry.centroid

        # Convert the centroids back to EPSG:4326 (latitude/longitude)
        centroids_latlon =centroids_projected.set_geometry('geometry_centroid', crs=2950)
        centroids_latlon = centroids_latlon.to_crs(epsg=4326)

        # Extract the longitude and latitude from the re-projected centroids
        centroids_latlon['centroid_longitude'] = centroids_latlon.geometry.x
        centroids_latlon['centroid_latitude'] = centroids_latlon.geometry.y

        # Group by to get one row per district
        centroids_for_merge = (
            centroids_latlon
            .groupby(id, as_index= False)[['centroid_longitude', 'centroid_latitude']]
            .first()
        )

        return joined_data.drop(["geometry"], axis=1), centroids_for_merge


    path_source1 = Path("data", "crime", "crime")
    df_crime = pd.read_csv(path_source1.get_source_path() + "/crime_montreal_cleaned.csv")
    geometry_crime = [Point(xy) for xy in zip(df_crime['LONGITUDE'], df_crime['LATITUDE'])]
    #Adds geometry column
    points_gdf_crime = gpd.GeoDataFrame(df_crime, geometry=geometry_crime, crs="EPSG:4326")

    # Load the GeoJSON file
    path_source2 = Path("data","municipality", "municipality")
    geojson = path_source2.get_source_path() + "/municipality_polygon_map.geojson"
    # Load municipality
    df_municipality = pd.read_csv(path_source2.get_source_path() + "/municipality_montreal_cleaned.csv")

    gdf = gpd.read_file(geojson)
    district_gdf = gdf.to_crs(points_gdf_crime.crs)
    joined_data = gpd.sjoin(points_gdf_crime, district_gdf, how="inner", predicate="within")


    # Perform spatial join to associate points with districts
    crime_districts, crime_to_merge = geocenter('nom_arr', joined_data)

    # Remove null values in the 'nom_arr' column
    crime_districts = crime_districts.dropna(subset=["nom_arr"])

    # Ensures each municipality record receive their district centroid matched
    municipaly_center = pd.merge(df_municipality, crime_to_merge, left_on='district_name', right_on= 'nom_arr', how='left')

    # Save the result to a new CSV file
    path_destination_crime = path_source1.get_destination_path() + "/crime_montreal_district_cleaned.csv"
    path_destination_municipality = path_source2.get_destination_path() + "/municipality_montreal_centered_cleaned.csv"

    # Save results in dataframes
    pd.DataFrame(crime_districts).to_csv(path_destination_crime, index=False)
    pd.DataFrame(municipaly_center).to_csv(path_destination_municipality, index=False)
