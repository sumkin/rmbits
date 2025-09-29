import sqlite3 


from farm_2phase_model import FARM2PhaseModel

depdates = ["20230601","20230602","20230603","20230604","20230605","20230606","20230607",
            "20230608","20230609","20230610","20230611","20230612","20230613","20230614",
            "20230615","20230616","20230617","20230618","20230619","20230620","20230621",
            "20230622","20230623","20230624","20230625","20230626","20230627","20230628",
            "20230629","20230630"]

fcstdates = ["20220715","20220815","20220915","20221015",
             "20221115","20221215","20230115","20230215",
             "20230315","20230415","20230515"] 

costs_file = "s3://ay-emr-job/fleet_assigner/june2023/costs.csv"
fleet_file = "s3://ay-emr-job/fleet_assigner/june2023/aircraft_inventory.csv"
cap_file = "s3://ay-emr-job/fleet_assigner/june2023/subfleet_capacities.csv"
leg_distance_file = "s3://ay-emr-job/fleet_assigner/june2023/leg_distances.csv"
subfleet_ranges_file = "s3://ay-emr-job/fleet_assigner/june2023/subfleet_ranges.csv"


def create_db() -> None:
    con = sqlite3.connect("../data/compare_revenue_and_costs.db")
    cur = con.cursor()
    try:
        cur.execute("CREATE TABLE result(fcstdate TEXT, revenue_fixed REAL, costs_fixed REAL, profit_fixed REAL, "+\
                                                       "revenue_partial REAL, costs_partial REAL, profit_partial REAL, "+\
                                                       "revenue_optimized REAL, costs_optimized REAL, profit_optimized REAL)")
    except:
        pass 


def add_row(fcstdate, revenue_fixed, costs_fixed, profit_fixed,
                      revenue_partial, costs_partial, profit_partial,
                      revenue_optimized, costs_optimized, profit_optimized):
    con = sqlite3.connect("../data/compare_revenue_and_costs.db")
    cur = con.cursor()
    q = "INSERT INTO result (fcstdate, revenue_fixed, costs_fixed, profit_fixed,"+\
                                      "revenue_partial, costs_partial, profit_partial,"+\
                                      "revenue_optimized, costs_optimized, profit_optimized)"+\
                            "VALUES ('{}',{},{},{},{},{},{},{},{},{})".format(
        fcstdate,
        revenue_fixed,
        costs_fixed,
        profit_fixed,
        revenue_partial,
        costs_partial,
        profit_partial,
        revenue_optimized,
        costs_optimized,
        profit_optimized
    )
    cur.execute(q)
    con.commit()


def row_exists(fcstdate) -> bool:
    con = sqlite3.connect("../data/compare_revenue_and_costs.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM result WHERE fcstdate = '{}'".format(fcstdate))
    rows = res.fetchall()
    return len(rows) > 0 


with open("../data/compare_revenue_costs.csv", "w") as fout:
    
    create_db()
    
    for fcstdate in fcstdates:

        print("fcstdate = {}".format(fcstdate))
        if row_exists(fcstdate):
            continue

        # Fixed fleet.
        print("")
        print("FIXED")
        farm = FARM2PhaseModel(fcstdate, depdates, costs_file, 
                                                   fleet_file, 
                                                   cap_file,
                                                   leg_distance_file,
                                                   subfleet_ranges_file)
        farm.load_data()
        subfleet = []
        farm.set_subfleet_to_optimize(subfleet)
        farm.build_model_phase_1()
        farm.solve()
        num_non_cancelled_duties = farm.get_solution_phase_1()
        farm.build_model_phase_2(num_non_cancelled_duties)
        farm.solve()
        farm.get_solution_phase_2()
        revenue_fixed = farm.revenue()
        costs_fixed = farm.costs()
        profit_fixed = revenue_fixed - costs_fixed

        # Partial fleet.
        print("")
        print("PARTIAL")
        farm = FARM2PhaseModel(fcstdate, depdates, costs_file, 
                                                   fleet_file, 
                                                   cap_file,
                                                   leg_distance_file,
                                                   subfleet_ranges_file)
        farm.load_data()
        subfleet = ["319", "320", "321", "32B", "E90"]
        farm.set_subfleet_to_optimize(subfleet)
        farm.build_model_phase_1()
        farm.solve()
        num_non_cancelled_duties = farm.get_solution_phase_1()
        farm.build_model_phase_2(num_non_cancelled_duties)
        farm.solve()
        farm.get_solution_phase_2()
        revenue_partial = farm.revenue()
        costs_partial = farm.costs()
        profit_partial = revenue_partial - costs_partial

        # Optimized fleet.
        print("")
        print("OPTIMIZED")
        farm = FARM2PhaseModel(fcstdate, depdates, costs_file, 
                                                   fleet_file, 
                                                   cap_file,
                                                   leg_distance_file,
                                                   subfleet_ranges_file)
        farm.load_data()
        subfleet = farm.dr.fleet_types
        farm.set_subfleet_to_optimize(subfleet)
        farm.build_model_phase_1()
        farm.solve()
        num_non_cancelled_duties = farm.get_solution_phase_1()
        farm.build_model_phase_2(num_non_cancelled_duties)
        farm.solve()
        farm.get_solution_phase_2()
        revenue_optimized = farm.revenue()
        costs_optimized = farm.costs()
        profit_optimized = revenue_partial - costs_partial

        add_row(str(fcstdate), revenue_fixed, costs_fixed, profit_fixed,
                               revenue_partial, costs_partial, profit_partial,
                               revenue_optimized, costs_optimized, profit_optimized)