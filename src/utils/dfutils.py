import numpy as np
import pandas as pd

def optimize_fdc(df):
    '''
    df['GEO_OD_TS_KEY'] = df.GEO_OD_TS_KEY.astype('category')
    df['BASE_OD_ORGN'] = df.BASE_OD_ORGN.astype('category')
    df['BASE_OD_DSTN'] = df.BASE_OD_DSTN.astype('category')
    df['BASE_OD_VIA'] = df.BASE_OD_VIA.astype('category')
    df['BASE_OD_ORGN_COUNTRY'] = df.BASE_OD_ORGN_COUNTRY.astype('category')
    df['BASE_OD_ORGN_REGION'] = df.BASE_OD_ORGN_REGION.astype('category')
    df['BASE_OD_DSTN_COUNTRY'] = df.BASE_OD_DSTN_COUNTRY.astype('category')
    df['BASE_OD_DSTN_REGION'] = df.BASE_OD_DSTN_REGION.astype('category')
    df['BASE_OPR_CC'] = df.BASE_OPR_CC.astype('category')
    df['BASE_MKT_CC'] = df.BASE_MKT_CC.astype('category')
    df['BASE_OD_DEPT_DATE'] = df.BASE_OD_DEPT_DATE.astype('category')
    df['BASE_SEG_DEP_DATE'] = df.BASE_SEG_DEP_DATE.astype('category')
    df['BASE_SEG_ARR_DATE'] = df.BASE_SEG_ARR_DATE.astype('category')
    df['GEO_ORGN'] = df.GEO_ORGN.astype('category')
    df['GEO_DSTN'] = df.GEO_DSTN.astype('category')
    df['PREV_VIA'] = df.PREV_VIA.astype('category')
    df['NEXT_VIA'] = df.NEXT_VIA.astype('category')
    df['PREV_OPR_CC'] = df.PREV_OPR_CC.astype('category')
    df['NEXT_OPR_CC'] = df.NEXT_OPR_CC.astype('category')
    df['PREV_MKT_CC'] = df.PREV_MKT_CC.astype('category')
    df['NEXT_MKT_CC'] = df.NEXT_MKT_CC.astype('category')
    df['PREV_SEG_DEP_DATE'] = df.PREV_SEG_DEP_DATE.astype('category')
    df['PREV_SEG_ARR_DATE'] = df.PREV_SEG_ARR_DATE.astype('category')
    df['NEXT_SEG_DEP_DATE'] = df.NEXT_SEG_DEP_DATE.astype('category')
    df['NEXT_SEG_ARR_DATE'] = df.NEXT_SEG_ARR_DATE.astype('category')
    df['POS'] = df.POS.astype('category')
    df['FF'] = df.FF.astype('category')
    df['TP'] = df.TP.astype('category')
    df['BC'] = df.BC.astype('category')
    df['SRC_DATE'] = df.SRC_DATE.astype('category')
    df['BASE_OPR_FLTNUM'] = df.BASE_OPR_FLTNUM.astype('category')
    df['BASE_MKT_FLTNUM'] = df.BASE_MKT_FLTNUM.astype('category')
    df['PREV_OPR_FLTNUM'] = df.PREV_OPR_FLTNUM.astype('category')
    df['PREV_MKT_FLTNUM'] = df.PREV_MKT_FLTNUM.astype('category')
    df['NEXT_OPR_FLTNUM'] = df.NEXT_OPR_FLTNUM.astype('category')
    df['NEXT_MKT_FLTNUM'] = df.NEXT_MKT_FLTNUM.astype('category')
    '''
    df['OPR_OD_TS_KEY'] = df.OPR_OD_TS_KEY.astype('category')
    df['GEO_OD_TS_KEY'] = df.GEO_OD_TS_KEY.astype('category')
    df['BASE_OD_DEPT_AIRPORT'] = df.BASE_OD_DEPT_AIRPORT.astype('category')
    df['BASE_OD_ARR_AIRPORT'] = df.BASE_OD_ARR_AIRPORT.astype('category')
    df['BASE_OD_DEPT_DATE'] = df.BASE_OD_DEPT_DATE.astype('category')
    df['GEO_OD_DEPT_AIRPORT'] = df.GEO_OD_DEPT_AIRPORT.astype('category')
    df['GEO_OD_ARR_AIRPORT'] = df.GEO_OD_ARR_AIRPORT.astype('category')
    df['POS'] = df.POS.astype('category')
    df['FARE_FAMILY'] = df.FARE_FAMILY.astype('category')
    df['BOOKING_CLASS'] = df.BOOKING_CLASS.astype('category')
    df['SOURCE_FILE_DATE'] = df.SOURCE_FILE_DATE.astype('category')

    df_int = df.select_dtypes(include=['int'])
    converted_int = df_int.apply(pd.to_numeric, downcast='unsigned')

    df_float = df.select_dtypes(include=['float'])
    converted_float = df_float.apply(pd.to_numeric, downcast='float')

    optimized_df = df.copy()
    optimized_df[converted_int.columns] = converted_int
    optimized_df[converted_float.columns] = converted_float
    df = optimized_df
  
    return df


def optimize_bif(df):
    df['CC'] = df.CC.astype('category')
    df['ORGN'] = df.ORGN.astype('category')
    df['DSTN'] = df.DSTN.astype('category')
    df['CABIN'] = df.CABIN.astype('category')
    df['RC'] = df.RC.astype('category')
    df['SRC_DATE'] = df.SRC_DATE.astype('category')

    df_int = df.select_dtypes(include=['int'])
    converted_int = df_int.apply(pd.to_numeric, downcast='signed')
    df_float = df.select_dtypes(include=['float'])
    converted_float = df_float.apply(pd.to_numeric, downcast='float')
    
    optimized_df = df.copy()
    optimized_df[converted_int.columns] = converted_int
    optimized_df[converted_float.columns] = converted_float
    df = optimized_df

    return df






