from pathlib import Path


def get_package_data():
    paths_test = [
        str(Path("data") / "hips_frames.vot"),
        str(Path("data") / "list_fields.json"),
        str(Path("data") / "moc.fits"),
    ]

    return {"astroquery.mocserver.tests": paths_test}
