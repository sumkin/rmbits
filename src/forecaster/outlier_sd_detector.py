from numpy import mean, std
from outlier_detector import OutlierDetector

#
# Class implements outlier detection based on variance.
# Idea is straightforward, all observations which are 
# far from the mean measured in the number of standart
# deviations are outliers.
#

class OutlierSdDetector(OutlierDetector):

    def __init__(self,lower_std,upper_std):

        #super(self.__class__,self).__init__()
        self.lower_std = lower_std
        self.upper_std = upper_std

    def remove_outliers(self,obs):

        # remove outliers from obs list
        # and returns observations without
        # outliers.

        outliers = self.get_outliers(obs)

        for e in outliers:
            while e in obs:
                obs.remove(e)

        return obs

    def get_outliers(self,obs):

        # get outliers from obs list
        # outliers are not removed, 
        # merely returned.

        mean_ = mean(obs)
        std_ = std(obs)
   
        lower_outliers = [e for e in obs if e < mean_ - self.lower_std * std_]
        upper_outliers = [e for e in obs if e > mean_ + self.upper_std * std_]

        return lower_outliers + upper_outliers 
