class NetworkDTDecompose:


    def __init__(self, fcstdate):
        self.fcstdate = fcstdate


    def read_inv_df(self):
        fcstyear  = self.fcstdate[:4]
        fcstmonth = self.fcstdate[4:6]     
        fcstyear  = self.fcstdate[6:8]

        invcsv = 's3://ay-rmp-home/nrm/bif/'+fcstyear+'/'+fcstmonth+'/INV_'+self.fcstdate+'.csv.gz'
        self.invdf = pd.read_csv(invcsv, low_memory = False)
       

    def read_fdc_df(self):
        pass 
