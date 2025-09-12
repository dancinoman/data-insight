from app import download_files as df
from app import transform as trans
from app import export as ex



if __name__ == "__main__":

    # Start the process of downloading files on web

    print("Starting the download process...")
    df.download_file_from_url()
    print("Starting the conversion process...")
    trans.convert_poverty_files()
    print("Starting to upload to S3...")
    ex.upload_csv_to_s3()
    print("Uploaded CSV files to S3")
    df.download_coverage()
    trans.clean_coverage()
    print("Downloaded police coverage file from S3 and fixed bad closing")
    trans.associate_points_with_districts()

    print("Featured engineering geojson file with points associated with districts")
    print("Pipeline completed successfully!")
