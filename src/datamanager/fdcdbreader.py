from time import sleep
from db_connector import *
from yield_lookup import *


class FDCDBReader:
    '''
    Reads files from database and produces
    future demand curves.
    '''

    def __init__(self, depdate):
        self.depdate = depdate
        self.curs = DBConnector.get_rs_curs()       
        num_attempts = 5
        for i in range(num_attempts):
            if self.curs is None:
                self.curs = DBConnector.get_rs_curs()
            else:
                break
            sleep(1)
        assert self.curs is not None

        self.curs.execute("SELECT COUNT(*)\
                           FROM nrm.bff_od_dcp_current\
                           WHERE base_od_dept_date = '" + self.depdate[:4] + "-" +\
                                                          self.depdate[4:6] + "-" +\
                                                          self.depdate[6:8] + "'")
        self.empty = (self.curs.fetchone()[0] == 0)


    def rows(self):
        # FIXME: demand should be aggregated as sum.
        #        marginal profit should be aggregated as weighted average over demand.
        assert not self.empty

        num_attempts = 5
        for i in range(num_attempts):
            if self.curs is None:
                self.curs = DBConnector.get_rs_curs()
            else:
                break
            sleep(1)
        assert self.curs is not None

        self.curs.execute("SELECT opr_od_ts_key,\
                                  geo_od_ts_key,\
                                  MAX(base_od_dept_airport) AS base_od_dept_airport,\
                                  MAX(base_od_arr_airport) AS base_od_arr_airport,\
                                  MAX(base_od_dept_date) AS base_od_dept_date,\
                                  MAX(geo_od_dept_airport) AS geo_od_dept_airport,\
                                  MAX(geo_od_arr_airport) AS geo_od_arr_airport,\
                                  pos,\
                                  fare_family,\
                                  booking_class,\
                                  travel_purpose,\
                                  AVG(system_marginal_profit_curve) AS system_marginal_profit,\
                                  AVG(adjusted_marginal_profit_curve) AS adjusted_marginal_profit,\
                                  SUM(system_remaining_demand_curve) AS system_remaining_demand,\
                                  SUM(adjusted_remaining_demand_curve) AS adjusted_remaining_demand,\
                                  MAX(source_file_date) AS source_fie_date\
                           FROM nrm.bff_od_dcp_current\
                           WHERE base_od_dept_date = '" + self.depdate[:4] + "-" +\
                                                          self.depdate[4:6] + "-" +\
                                                          self.depdate[6:8] + "'\
                           GROUP BY opr_od_ts_key,\
                                    geo_od_ts_key,\
                                    pos,\
                                    fare_family,\
                                    booking_class,\
                                    travel_purpose")
        for row in self.curs:
            opr_od_ts_key = row[0]
            geo_od_ts_key = row[1]
            base_od_dept_airport = row[2]
            base_od_arr_airport = row[3]
            base_od_dept_date = row[4]
            geo_od_dept_airport = row[5]
            geo_od_arr_airport = row[6]
            pos = row[7]
            fare_family = row[8]
            booking_class = row[9]
            travel_purpose = row[10]
            system_marginal_profit = row[11]
            adjusted_marginal_profit = row[12]
            system_remaining_demand = row[13]
            adjusted_remaining_demand = row[14]
            source_file_date = row[15]
            yield opr_od_ts_key,\
                  geo_od_ts_key,\
                  base_od_dept_airport,\
                  base_od_arr_airport,\
                  base_od_dept_date,\
                  geo_od_dept_airport,\
                  geo_od_arr_airport,\
                  pos,\
                  fare_family,\
                  booking_class,\
                  travel_purpose,\
                  system_marginal_profit,\
                  adjusted_marginal_profit,\
                  system_remaining_demand,\
                  adjusted_remaining_demand,\
                  source_file_date


if __name__ == "__main__":
    reader = FDCDBReader('20190901')
    '''
    num = 0
    for r in reader.rows():
        num += 1
        print("num = ", num)
    '''


