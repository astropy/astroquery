# Licensed under a 3-clause BSD style license - see LICENSE.rst
import tempfile
import pytest

import os,tarfile

from ..core import HSAClass

spire_chksum = [10243, 10772, 9029, 11095, 3875, 3893, 3903, 3868, 3888, 3951, 3905, 3875, 3887, 3908, 3871, 3892, 3894, 3900, 3870, 3892, 3938, 3904, 3893, 3866, 3893, 3930, 3901, 3867, 3893, 3927, 3903, 3868, 3892, 3926, 3904, 3869, 3889, 3937, 3899, 3868, 3887, 3928, 3912, 3865, 3887, 3937, 3899, 3865, 3891, 3925, 3911, 3868, 3883, 3937, 3902, 3870, 3893, 3922, 3914, 3869, 3886, 3924, 3903, 3870, 3889, 3922, 3903, 3867, 3889, 3932, 3902, 3869, 3892, 3930, 3900, 3868, 3892, 3916, 3910, 3868, 3889, 3932, 3907, 3869, 3892, 3914, 3900, 3871, 3884, 3918, 3903, 3894, 3874, 3892, 3906, 3872, 3889, 3895, 9724, 10495, 9293, 11299, 12132, 10602, 11283, 9582, 10568, 11354, 11228, 11812, 11006, 11224, 11382, 10232, 11049, 11011, 3862, 9671, 10844, 10899, 3946, 3941, 3953, 3954, 3948, 3940, 3954, 3948, 3945, 9286, 11197, 3902, 10137, 11664, 12038, 3963, 3948, 11970, 3867, 11452, 3908, 3908, 3894, 3908, 3908, 3894, 3885, 3914, 3876, 11820, 3958, 3905, 3963, 3925, 3974, 3923, 12241, 3897, 3900, 12328, 11911, 3893, 3885, 3895, 3895, 3891, 11970, 12252, 3899, 12503, 12135, 11826, 3899, 3899, 3912, 3912, 11530, 11625, 11850, 10981, 3872, 3890, 3896, 3895, 3867, 3891, 10561, 10991, 11209, 3853, 3871, 3869, 11372, 10826, 10995, 3887, 3882, 3883, 3879, 3884, 3883, 3889, 3883, 3887, 3876, 3885, 3883, 3882, 3888, 3886, 3882, 3882, 3882, 3887, 3885, 3885, 3884, 3880, 3881, 3878, 3882, 3884, 3879, 3887, 3882, 3884, 3877, 3883, 3882, 3881, 3882, 3876, 3879, 3881, 3881, 3884, 3882, 3882, 3882, 3888, 3883, 3880, 3880, 3875, 3880, 3884, 3883, 3887, 3880, 3879, 3874, 3882, 3879, 3887, 3876, 3888, 3888, 3885, 3885, 3876, 3880, 3887, 3877, 3884, 3886, 3879, 3879, 3877, 3880, 3876, 3889, 3885, 3886, 3885, 3879, 3879, 12424, 10112, 10885, 3895, 3922, 3888, 3900, 3898, 3919, 3925, 3930, 3923, 3932, 3931, 3917, 3922, 3917, 3919, 3935, 3929, 3923, 3929, 3924, 3906, 3918, 3895, 3892, 11322, 10879, 3944, 11338, 3921, 11009, 10969, 11352, 10984, 3944, 11345, 11333, 11088, 11331, 11099, 11324, 11118, 10591, 11502, 6291]

pacs_chksum = [10205, 10752, 8914, 3869, 9736, 3925, 3942, 11201, 10454, 11393, 10520, 11080, 3979, 11121, 3961, 9745, 10492, 9317, 11304, 12025, 10584, 11295, 9564, 10585, 11367, 11229, 11808, 11039, 11225, 11411, 10246, 11066, 11013, 10158, 3939, 3927, 3941, 3936, 3942, 3925, 9691, 10381, 10944, 3990, 10970, 3969, 9453, 10802, 3881, 11926, 3896, 12528, 3908, 11898, 3883, 3894, 3878, 11231, 3910, 3885, 3876, 3913, 3967, 3970, 3908, 3903, 3901, 3958, 3898, 3870, 3915, 3878, 3895, 3901, 3888, 3880, 3922, 3881, 3926, 3883, 12229, 3958, 3949, 3936, 3962, 3949, 3947, 3868, 13210, 3885, 3901, 11463, 3939, 3967, 3878, 3900, 3911, 3947, 3917, 3940, 3953, 3904, 3869, 3874, 3880, 3893, 3964, 3980, 3889, 3871, 3908, 3882, 3888, 3895, 3905, 3889, 13163, 3879, 11036, 12469, 3886, 3887, 3863, 3921, 3881, 3911, 3878, 3921, 11149, 13032, 3880, 3881, 3883, 3883, 3895, 3899, 3919, 12498, 3896, 3942, 3894, 11407, 3866, 11716, 3889, 3890, 3888, 3873, 9870, 10738, 3978, 10759, 3949, 10720, 3921, 10390, 3938, 10365, 11182, 3905, 10724, 3943, 10742, 3942, 10025, 3924, 3935, 10388, 11185, 11206, 6288]

@pytest.mark.remote_data
class TestHSARemote:
    tmp_dir = tempfile.TemporaryDirectory()

    def test_download_data_observation_pacs(self):
        #obs_id = "1342195355"
        obs_id = "1342191813"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, obs_id + ".tar")
        hsa = HSAClass()
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        chksum = []
        tar = tarfile.open(res)
        for m in tar.getmembers():
            chksum.append(m.chksum)
        assert chksum.sort() == pacs_chksum.sort()
        os.remove(res)

    def test_download_data_observation_pacs_filename(self):
        obs_id = "1342191813"
        fname = "output_file"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'filename': fname,
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, fname + ".tar")
        hsa = HSAClass()
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        chksum = []
        tar = tarfile.open(res)
        for m in tar.getmembers():
            chksum.append(m.chksum)
        assert chksum.sort() == pacs_chksum.sort()
        os.remove(res)

    def test_download_data_observation_pacs_compressed(self):
        obs_id = "1342191813"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'compress': 'true',
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, obs_id + ".tgz")
        hsa = HSAClass()
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        chksum = []
        tar = tarfile.open(res)
        for m in tar.getmembers():
            chksum.append(m.chksum)
        assert chksum.sort() == pacs_chksum.sort()
        os.remove(res)

    def test_download_data_observation_spire(self):
        #obs_id = "1342224960"
        obs_id = "1342191188"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "SPIRE",
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, obs_id + ".tar")
        hsa = HSAClass()
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        chksum = []
        tar = tarfile.open(res)
        for m in tar.getmembers():
            chksum.append(m.chksum)
        assert chksum.sort() == spire_chksum.sort()
        os.remove(res)

    def test_download_data_postcard_pacs(self):
        obs_id = "1342191813"
        parameters = {'retrieval_type': "POSTCARD",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, obs_id + ".jpg")
        hsa = HSAClass()
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        os.remove(res)

    def test_download_data_postcard_pacs_filename(self):
        obs_id = "1342191813"
        fname = "output_file"
        parameters = {'retrieval_type': "POSTCARD",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'filename': fname,
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, fname + ".jpg")
        hsa = HSAClass()
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        os.remove(res)

    def test_get_observation(self):
        obs_id = "1342191813"
        parameters = {'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, obs_id + ".tar")
        hsa = HSAClass()
        res = hsa.get_observation(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        chksum = []
        tar = tarfile.open(res)
        for m in tar.getmembers():
            chksum.append(m.chksum)
        assert chksum.sort() == pacs_chksum.sort()
        os.remove(res)

    def test_get_postcard(self):
        obs_id = "1342191813"
        parameters = {'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'download_dir': self.tmp_dir.name}
        expected_res = os.path.join(self.tmp_dir.name, obs_id + ".jpg")
        hsa = HSAClass()
        res = hsa.get_postcard(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        os.remove(res)
