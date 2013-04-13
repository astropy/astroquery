import StringIO

def download_list_of_fitsfiles(linklist, output_directory=None,
        output_prefix=None,):
    """
    Given a list of file URLs, download them and (optionally) rename them

    """
    # Loop through links and retrieve FITS images
    images = []
    for link in linklist:

        if not os.path.exists(directory):
            os.mkdir(directory)

        with aud.get_readable_fileobj(link, cache=True) as f:
            results = f.read()
        S = StringIO.StringIO(results)

        try: 
            # try to open as a fits file
            fitsfile = fits.open(S,ignore_missing_end=True)
        except IOError:
            # if that fails, try to open as a gzip'd fits file
            # have to rewind to the start
            S.seek(0)
            G = gzip.GzipFile(fileobj=S)
            fitsfile = fits.open(G,ignore_missing_end=True)

        # Get Multiframe ID from the header
        images.append(fitsfile)

        if save:
            h0 = fitsfile[0].header
            filt = str(h0['FILTER']).strip()
            obj = filt + "_" + str(h0['OBJECT']).strip().replace(":", ".")

            if savename is None:
                filename = "UKIDSS_%s_G%07.3f%+08.3f_%s.fits" % (filt,glon,glat,obj)
            else:
                filename = savename

            # Set final directory and file names
            final_file = directory + '/' + filename

            if verbose:
                print "Saving file %s" % final_file

            fitsfile.writeto(final_file, clobber=overwrite)

    return images
