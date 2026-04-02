# # Licensed under a 3-clause BSD style license - see LICENSE.rst
# """
# ===============
# PLATO TAP tests
# ===============
#
# European Space Astronomy Centre (ESAC)
# European Space Agency (ESA)
#
# """
# import os
# import tempfile
#
# from astropy.coordinates import SkyCoord
# from astroquery.esa.plato import PlatoClass
# import pytest
# from pyvo import DALQueryError
#
#
# def data_path(filename):
#     data_dir = os.path.join(os.path.dirname(__file__), 'data')
#     return os.path.join(data_dir, filename)
#
#
# def close_file(file):
#     file.close()
#
#
# def close_files(file_list):
#     for file in file_list:
#         close_file(file['fits'])
#
#
# def create_temp_folder():
#     return tempfile.TemporaryDirectory()
#
#
# @pytest.mark.remote_data
# class TestPlatoRemote:
#
#     def test_get_table(self):
#         plato = PlatoClass()
#
#         pic_target_table = plato.get_table('pic_go.pic_target_go')
#         assert pic_target_table is not None
#
#         ehst = plato.get_table('ehst.archive')
#         assert ehst is None
#
#     def test_query_tap(self):
#         plato = PlatoClass()
#
#         # Query an existing table
#         result = plato.query_tap('select top 10 * from pic_go.pic_target_go;')
#         assert result is not None
#
#         # Query a table that does not exist
#         with pytest.raises(DALQueryError) as err:
#             plato.query_tap('select top 10 * from schema.table;')
#         assert 'Unknown table' in err.value.args[0]
#
#         # Store the result in a file
#         temp_folder = create_temp_folder()
#         filename = os.path.join(temp_folder.name, 'query_tap.votable')
#         plato.query_tap('select top 10 * from pic_go.pic_target_go;', output_file=filename)
#         assert os.path.exists(filename)
#
#         temp_folder.cleanup()
#
#     def test_search_pic_target_go(self):
#         plato = PlatoClass()
#
#         # Store the result in a file
#         temp_folder = create_temp_folder()
#         filename = os.path.join(temp_folder.name, 'query_tap.votable')
#
#         reference_magnitude = 10
#         pic_results = plato.search_pic_target_go(coordinates="90 -57", columns=['StarName', 'PlatoMagNCAM'],
#                                                  PlatoMagNCAM=('>', reference_magnitude), StarName='Gaia DR3 5%',
#                                                  output_file=filename)
#
#         assert os.path.exists(filename)
#         assert pic_results['StarName'] is not None
#
#         temp_folder.cleanup()
#
#     def test_search_pic_contaminant_go(self):
#         plato = PlatoClass()
#
#         # Store the result in a file
#         temp_folder = create_temp_folder()
#         filename = os.path.join(temp_folder.name, 'query_tap.votable')
#
#         pic_results = plato.search_pic_contaminant_go(coordinates="90 -57",
#                                                       columns=['PICcontaminantId', 'caseFlag'],
#                                                       caseFlag=('>', 1),
#                                                       output_file=filename)
#
#         assert os.path.exists(filename)
#         assert pic_results['PICcontaminantId'] is not None
#
#         temp_folder.cleanup()
