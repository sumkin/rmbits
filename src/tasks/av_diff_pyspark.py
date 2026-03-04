'''
Fedor Nikitin, AY, 2018, fedor.nikitin@finnair.com
'''

import sys
from datetime import datetime as dt
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.types import DateType
from pyspark.sql.functions import udf, date_format


def tmpstmp():
    '''
    Returns timestamp in readable format.
    '''
    return dt.now().strftime('%Y-%m-%d %H:%M:%S')

dtconvert = udf(lambda x: dt.strptime(x, '%Y%m%d'), DateType())


if __name__ == '__main__':
    '''
    To run:
    $ spark-submit av_diff_pyspark.py YYYY-MM-DD YYYY-MM-DD
    '''
    if len(sys.argv) != 3:
        print 'Wrong number of arguments'

    dt1 = dt.strptime(sys.argv[1], '%Y-%m-%d')
    dt2 = dt.strptime(sys.argv[2], '%Y-%m-%d')

    spark = SparkSession.builder.appName('AVDiff').getOrCreate()

    s3df1fname = 's3n://ay-rmp-home/nrm/baf/' +\
                 str(dt1.year) + '/' + str(dt1.month).zfill(2) +\
                 '/AV_OD_' + dt1.strftime('%Y%m%d') + '.json.gz'
    print tmpstmp(), 'Reading data frame ', s3df1fname
    df1 = spark.read.format('json').load(s3df1fname)


    s3df2fname = 's3n://ay-rmp-home/nrm/baf/' +\
                 str(dt2.year) + '/' + str(dt2.month).zfill(2) +\
                 '/AV_OD_' + dt2.strftime('%Y%m%d') + '.json.gz'
    print tmpstmp(), 'Reading data frame ', s3df2fname
    df2 = spark.read.format('json').load(s3df2fname)

    print tmpstmp(), 'Taking join of data frames'
    df = df1.join(df2, ['ORIG','DSTN','CC','FLTNUM','POS','POSTYPE','OD_DEPT_DATE','OD_DEPT_DOW'])


    print tmpstmp(), 'Taking class difference'
    df = df.withColumn('DPTDT',date_format(dtconvert(df['OD_DEPT_DATE']), 'dd.MM.yyyy'))
    cd_sdf = df.select(df.ORIG, df.DSTN, df.DPTDT, df.OD_DEPT_DATE, df.CC, df.POS, df.POSTYPE, df.OD_DEPT_DOW,\
                       df1.J-df2.J, df1.C-df2.C, df1.D-df2.D, df1.I-df2.I, df1.F-df2.F, df1.U-df2.U,\
                       df1.Y-df2.Y, df1.B-df2.B, df1.H-df2.H, df1.K-df2.K, df1.M-df2.M, df1.P-df2.P,\
                       df1.T-df2.T, df1.L-df2.L, df1.V-df2.V, df1.S-df2.S, df1.N-df2.N, df1.G-df2.G,\
                       df1.A-df2.A, df1.Q-df2.Q, df1.O-df2.O, df1.Z-df2.Z, df1.R-df2.R, df1.W-df2.W,\
                       df1.X-df2.X, df1.E-df2.E)

    suffix = dt1.strftime('%Y%m%d') + '-' + dt2.strftime('%Y%m%d')
    cd_csvname = 's3://ay-rmp-home/nrm/baf/'+str(dt1.year)+'/'+str(dt1.month).zfill(2) +\
                 '/AV_OD_DIFF_'+dt1.strftime('%Y%m%d')+'-'+dt2.strftime('%Y%m%d')+'.csv'
    print tmpstmp(), 'Writing class difference to s3 CSV file'
    cd_sdf.repartition(1).write.mode('overwrite').format('com.databricks.spark.csv').\
                          save(cd_csvname, header='true')
    del cd_sdf


    print tmpstmp(), 'Taking last-open-class difference'
    locd_sdf = df.select(df.ORIG, df.DSTN, df.DPTDT, df.OD_DEPT_DATE, df.CC, df.POS, df.POSTYPE, df.OD_DEPT_DOW,\
                         df1.LOCIJ_WOSC-df2.LOCIJ_WOSC, df1.LOCIY_WOSC-df2.LOCIY_WOSC)
    locd_csvname = 's3://ay-rmp-home/nrm/baf/'+str(dt1.year)+'/'+str(dt1.month).zfill(2)+\
                   '/AV_OD_LOCDIFF_'+dt1.strftime('%Y%m%d')+'-'+dt2.strftime('%Y%m%d')+'.csv'
    print tmpstmp(), 'Writing last-open-class difference s3 CSV file'
    locd_sdf.repartition(1).write.mode('overwrite').format('com.databricks.spark.csv').\
                            save(locd_csvname, header='true')
    del locd_sdf   
 
    print tmpstmp(), 'Done'

 

