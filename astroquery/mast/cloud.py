# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Cloud Access
============

This file contains functionality for accessing MAST holdings in the cloud.
"""

import os
import warnings
import threading

from astroquery import log
from astropy.utils.console import ProgressBarOrSpinner
from astropy.utils.exceptions import AstropyDeprecationWarning

from ..exceptions import NoResultsWarning, InvalidQueryError

from . import utils


__all__ = []


class CloudAccess:  # pragma:no-cover
    """
    Class encapsulating access to MAST data in the cloud.
    """

    def __init__(self, provider="AWS", profile=None, verbose=False):
        """
        Initialize class to enable downloading public files from S3
        instead of STScI servers.
        Requires the boto3 and botocore libraries to function.

        Parameters
        ----------
        provider : str
            Which cloud data provider to use. Currently only AWS S3 is supported,
            so at the moment this argument is ignored.
        profile : str
            Profile to use to identify yourself to the cloud provider (usually in ~/.aws/config).
        verbose : bool
            Default False. Display extra info and warnings if true.
        """

        # Dealing with deprecated argument
        if profile is not None:
            warnings.warn(("MAST Open Data on AWS is now free to access and does "
                           "not require an AWS account"), AstropyDeprecationWarning)

        import boto3
        import botocore

        self.supported_missions = ["mast:hst/product", "mast:tess/product", "mast:kepler", "mast:galex", "mast:ps1"]

        self.boto3 = boto3
        self.botocore = botocore
        self.config = botocore.client.Config(signature_version=botocore.UNSIGNED)

        self.pubdata_bucket = "stpubdata"

        if verbose:
            log.info("Using the S3 STScI public dataset")

    def is_supported(self, data_product):
        """
        Given a data product, determines if it is in a mission available in the cloud.

        Parameters
        ----------
        data_product : `~astropy.table.Row`
            Product to be validated.

        Returns
        -------
        response : bool
              Is the product from a supported mission.
        """

        for mission in self.supported_missions:
            if data_product['dataURI'].lower().startswith(mission):
                return True
        return False

    def get_cloud_uri(self, data_product, include_bucket=True, full_url=False):
        """
        For a given data product, returns the associated cloud URI.
        If the product is from a mission that does not support cloud access an
        exception is raised. If the mission is supported but the product
        cannot be found in the cloud, the returned path is None.

        Parameters
        ----------
        data_product : `~astropy.table.Row`
            Product to be converted into cloud data uri.
        include_bucket : bool
            Default True. When false returns the path of the file relative to the
            top level cloud storage location.
            Must be set to False when using the full_url argument.
        full_url : bool
            Default False. Return an HTTP fetchable url instead of a cloud uri.
            Must set include_bucket to False to use this option.

        Returns
        -------
        response : str or None
            Cloud URI generated from the data product. If the product cannot be
            found in the cloud, None is returned.
        """

        s3_client = self.boto3.client('s3', config=self.config)

        path = utils.mast_relative_path(data_product["dataURI"])
        if path is None:
            raise InvalidQueryError("Malformed data uri {}".format(data_product['dataURI']))

        if 'galex' in path:
            path = path.lstrip("/mast/")
        elif '/ps1/' in path:
            path = path.replace("/ps1/", "panstarrs/ps1/public/")
        else:
            path = path.lstrip("/")

        try:
            s3_client.head_object(Bucket=self.pubdata_bucket, Key=path)
            if include_bucket:
                path = "s3://{}/{}".format(self.pubdata_bucket, path)
            elif full_url:
                path = "http://s3.amazonaws.com/{}/{}".format(self.pubdata_bucket, path)
            return path
        except self.botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != "404":
                raise

        warnings.warn("Unable to locate file {}.".format(data_product['productFilename']), NoResultsWarning)
        return None

    def get_cloud_uri_list(self, data_products, include_bucket=True, full_url=False):
        """
        Takes an `~astropy.table.Table` of data products and returns the associated cloud data uris.

        Parameters
        ----------
        data_products : `~astropy.table.Table`
            Table containing products to be converted into cloud data uris.
        include_bucket : bool
            Default True. When false returns the path of the file relative to the
            top level cloud storage location.
            Must be set to False when using the full_url argument.
        full_url : bool
            Default False. Return an HTTP fetchable url instead of a cloud uri.
            Must set include_bucket to False to use this option.

        Returns
        -------
        response : list
            List of URIs generated from the data products, list way contain entries that are None
            if data_products includes products not found in the cloud.
        """

        return [self.get_cloud_uri(product, include_bucket, full_url) for product in data_products]

    def download_file(self, data_product, local_path, cache=True):
        """
        Takes a data product in the form of an  `~astropy.table.Row` and downloads it from the cloud into
        the given directory.

        Parameters
        ----------
        data_product :  `~astropy.table.Row`
            Product to download.
        local_path : str
            The local filename to which toe downloaded file will be saved.
        cache : bool
            Default is True. If file is found on disc it will not be downloaded again.
        """

        s3 = self.boto3.resource('s3', config=self.config)
        s3_client = self.boto3.client('s3', config=self.config)
        bkt = s3.Bucket(self.pubdata_bucket)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bucket_path = self.get_cloud_uri(data_product, False)
        if not bucket_path:
            raise Exception("Unable to locate file {}.".format(data_product['productFilename']))

        # Ask the webserver (in this case S3) what the expected content length is and use that.
        info_lookup = s3_client.head_object(Bucket=self.pubdata_bucket, Key=bucket_path)
        length = info_lookup["ContentLength"]

        if cache and os.path.exists(local_path):
            if length is not None:
                statinfo = os.stat(local_path)
                if statinfo.st_size != length:
                    log.warning("Found cached file {0} with size {1} that is "
                                "different from expected size {2}"
                                .format(local_path,
                                        statinfo.st_size,
                                        length))
                else:
                    log.info("Found cached file {0} with expected size {1}."
                             .format(local_path, statinfo.st_size))
                    return

        with ProgressBarOrSpinner(length, ('Downloading URL s3://{0}/{1} to {2} ...'.format(
                self.pubdata_bucket, bucket_path, local_path))) as pb:

            # Bytes read tracks how much data has been received so far
            # This variable will be updated in multiple threads below
            global bytes_read
            bytes_read = 0

            progress_lock = threading.Lock()

            def progress_callback(numbytes):
                # Boto3 calls this from multiple threads pulling the data from S3
                global bytes_read

                # This callback can be called in multiple threads
                # Access to updating the console needs to be locked
                with progress_lock:
                    bytes_read += numbytes
                    pb.update(bytes_read)

            bkt.download_file(bucket_path, local_path, Callback=progress_callback)
