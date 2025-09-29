import gzip
import pickle
import time

from s3utils import *

class LPModelLoader:

    def __init__(self, fcstdate, depdate):
        self.fcstdate = fcstdate
        self.depdate = depdate

    def get(self, mode="remaining"):
        fcstyear = self.fcstdate[:4]
        fcstmonth = self.fcstdate[4:6]
        fcstday = self.fcstdate[6:8]

        # Copy file.
        orig = "s3://ay-emr-job/nrm/lprdrfdcpkl/{}/{}/{}/lprdrfdcpkl_{}_{}_{}.pkl.gz".format(fcstyear,
                                                                                             fcstmonth,
                                                                                             fcstday,
                                                                                             self.fcstdate,
                                                                                             self.depdate,
                                                                                             mode)
        dstn = "/home/ay49514/tmp/{}_lprdrfdcpkl_{}_{}_{}.pkl".format(time.time(),
                                                                      self.fcstdate,
                                                                      self.depdate,
                                                                      mode)
        dstngz = dstn + '.gz'
        s3copy(orig, dstngz)

        # Load model.
        model = None
        with gzip.open(dstngz, 'rb') as fout:
            model = pickle.load(fout)
        assert model is not None

        # Remove file.
        try:
            subprocess.check_output(['rm', dstngz])
        except:
            # This can happen, if code is run in parallel.
            pass

        return model

if __name__ == "__main__":
    date = "20200323"
    fcstdate, depdate = date, date
    loader = LPModelLoader(fcstdate, depdate)
    model = loader.get()
    print("model.keys() = ", model.keys())
    print("model['d'] = ", model['d'])
    print("sum(model['d']) = ", sum(model['d']))
    print("Done")



