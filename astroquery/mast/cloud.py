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

from ..exceptions import RemoteServiceError, NoResultsWarning

from . import utils

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
try:
    import botocore
    from botocore.exceptions import ClientError, BotoCoreError
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

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
        if not HAS_BOTO3 or not HAS_BOTOCORE:
            raise ImportError("Please install the `boto3` and `botocore` packages to enable cloud dataset access.")

        # Dealing with deprecated argument
        if profile is not None:
            warnings.warn(("MAST Open Data on AWS is now free to access and does "
                           "not require an AWS account"), AstropyDeprecationWarning)

        self.boto3 = boto3
        self.botocore = botocore
        self.config = botocore.client.Config(signature_version=botocore.UNSIGNED)
        self.pubdata_bucket = "stpubdata"
        self.s3_client = self.boto3.client('s3', config=self.config)

        # Cached list of datasets available in the cloud
        self._supported_datasets = self._fetch_supported_datasets()

        if verbose:
            log.info("Using the S3 STScI public dataset")

    def _fetch_supported_datasets(self):
        """
        Returns the list of datasets that have data available in the cloud.

        Returns
        -------
        response : list
              List of supported datasets.
        """
        try:
            datasets = []

            # Top-level prefixes in the bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.pubdata_bucket,
                Delimiter='/'  # Use a delimiter to treat the S3 structure like folders
            )

            for prefix_info in response.get('CommonPrefixes', []):
                prefix = prefix_info['Prefix'].rstrip('/')

                if prefix == 'mast':
                    # 'mast/' contains sub-prefixes for different high-level science products
                    mast_response = self.s3_client.list_objects_v2(
                        Bucket=self.pubdata_bucket,
                        Prefix='mast/hlsp/',
                        Delimiter='/',
                    )
                    datasets.extend(
                        cp['Prefix'].rstrip('/')
                        for cp in mast_response.get('CommonPrefixes', [])
                    )
                else:
                    datasets.append(prefix)

            return datasets

        except (ClientError, BotoCoreError) as e:
            log.error('Failed to retrieve supported datasets from S3 bucket %s: %s', self.pubdata_bucket, e)
            return []

    def get_supported_datasets(self):
        """
        Returns the list of datasets that have data available in the cloud.

        Returns
        -------
        response : list
              List of supported datasets.
        """
        return list(self._supported_datasets)

    def get_cloud_uri(self, data_product, include_bucket=True, full_url=False):
        """
        For a given data product, returns the associated cloud URI.
        If the product is from a dataset that does not support cloud access an
        exception is raised. If the dataset is supported but the product
        cannot be found in the cloud, the returned path is None.

        Parameters
        ----------
        data_product : `~astropy.table.Row`, str
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
        # If data_product is a string, convert to a list
        data_product = [data_product] if isinstance(data_product, str) else data_product

        uri_list = self.get_cloud_uri_list(data_product, include_bucket=include_bucket, full_url=full_url)

        # Making sure we got at least 1 URI from the query above.
        if not uri_list or uri_list[0] is None:
            return
        else:
            # Output from ``get_cloud_uri_list`` is always a list even when it's only 1 URI
            return uri_list[0]

    def get_cloud_uri_list(self, data_products, *, include_bucket=True, full_url=False, verbose=True):
        """
        Takes an `~astropy.table.Table` of data products and returns the associated cloud data uris.

        Parameters
        ----------
        data_products : `~astropy.table.Table`, list
            Table containing products or list of MAST uris to be converted into cloud data uris.
        include_bucket : bool
            Default True. When false returns the path of the file relative to the
            top level cloud storage location.
            Must be set to False when using the full_url argument.
        full_url : bool
            Default False. Return an HTTP fetchable url instead of a cloud uri.
            Must set include_bucket to False to use this option.
        verbose : bool
            Default True. Whether to issue warnings if a product cannot be found in the cloud.

        Returns
        -------
        response : list
            List of URIs generated from the data products, list way contain entries that are None
            if data_products includes products not found in the cloud.
        """
        data_uris = data_products if isinstance(data_products, list) else data_products['dataURI']
        paths = utils.get_cloud_paths(data_uris, verbose=verbose)

        uri_list = []
        for path in paths:
            if path is None:
                uri_list.append(None)
            else:
                try:
                    # Use `head_object` to verify that the product is available on S3 (not all products are)
                    self.s3_client.head_object(Bucket=self.pubdata_bucket, Key=path)
                    if include_bucket:
                        s3_path = "s3://{}/{}".format(self.pubdata_bucket, path)
                        uri_list.append(s3_path)
                    elif full_url:
                        path = "http://s3.amazonaws.com/{}/{}".format(self.pubdata_bucket, path)
                        uri_list.append(path)
                    else:
                        uri_list.append(path)
                except self.botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] != "404":
                        raise
                    if verbose:
                        warnings.warn(f"Failed to retrieve cloud path for {path}", NoResultsWarning)
                    uri_list.append(None)

        return uri_list

    def download_file_from_cloud(self, data_product, local_path, cache=True, verbose=True):
        """
        Download a data product from MAST cloud storage (S3) to a local file.

        Parameters
        ----------
        data_product :  str
            MAST product URI (e.g. ``mast:JWST/product.fits``) or S3 URI (e.g. ``s3://<bucket>/path/to/product.fits``).
        local_path : str
            Local filename where the downloaded file will be saved.
        cache : bool, optional
            Default is True. If True, and the file already exists locally with the expected size,
            the download is skipped.
        verbose : bool, optional
            Default is True. Whether to show download progress in the console.
        """
        # TODO: Function that checks if a particular product, by dataURI, can be found in the cloud
        # Normalize to an S3 key (no bucket)
        if data_product.strip().startswith('s3://'):
            s3_key = data_product.replace(f's3://{self.pubdata_bucket}/', '', 1)
        else:
            s3_key = self.get_cloud_uri_list([data_product], include_bucket=False, verbose=False)[0]

        # If s3_key is None, the product was not found in the cloud
        if s3_key is None:
            raise RemoteServiceError(f'The product {data_product} was not found in the cloud.')

        # Query S3 for expected file size
        head = self.s3_client.head_object(Bucket=self.pubdata_bucket, Key=s3_key)
        expected_size = head.get('ContentLength')

        # Cache check
        if cache and os.path.exists(local_path) and expected_size is not None:
            local_size = os.path.getsize(local_path)
            if local_size == expected_size:
                log.info("Using cached file {0} with expected size {1}."
                         .format(local_path, local_size))
                return
            else:
                log.warning("Found cached file {0} with size {1} that is "
                            "different from expected size {2}"
                            .format(local_path,
                                    local_size,
                                    expected_size))

        # Proceed with download
        bucket = self.boto3.resource('s3', config=self.config).Bucket(self.pubdata_bucket)
        if not verbose:
            bucket.download_file(s3_key, local_path)
            return

        # Progress-aware download
        bytes_read = 0
        progress_lock = threading.Lock()

        def progress_callback(numbytes):
            # Boto3 calls this from multiple threads pulling the data from S3
            nonlocal bytes_read

            # This callback can be called in multiple threads
            # Access to updating the console needs to be locked
            with progress_lock:
                bytes_read += numbytes
                pb.update(bytes_read)

        with ProgressBarOrSpinner(
            expected_size,
            f'Downloading s3://{self.pubdata_bucket}/{s3_key} to {local_path} ...'
        ) as pb:
            bucket.download_file(s3_key, local_path, Callback=progress_callback)
