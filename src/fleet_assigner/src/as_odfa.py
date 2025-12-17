import os
import uuid

from as_farm_wo_cancellations import ASFARMWoCancellations
from as_lines_builder import ASLinesBuilder

if __name__ == "__main__":
    depdates = ["20251219", "20251220"]
    inv_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/inv2.csv"
    costs_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/costs.csv"
    fleet_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/aircraft_inventory.csv"
    cap_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/capacities.csv"
    maintenance_file = ""
    leg_pairings_file = "s3://ay-emr-job/fleet_assigner/input/FEB_Report.xlsx"
    turnaround_times_file = "s3://ay-emr-job/fleet_assigner/input/turnaround_times.csv"

    asfwoc = ASFARMWoCancellations(depdates,
                                   inv_file,
                                   costs_file,
                                   fleet_file,
                                   cap_file,
                                   maintenance_file,
                                   leg_pairings_file,
                                   turnaround_times_file)
    asfwoc.load_data()
    asfwoc.build_model(max_num_changes=100000)
    asfwoc.make_feasible()
    asfwoc.solve()
    sol = asfwoc.get_solution()
    rev = sol["rev"]
    costs = sol["costs"]
    profit = rev - costs

    '''
    asfwoc.solve_with_y_fixed()
    sol_y_fixed = asfwoc.get_solution()
    fixed_rev = sol_y_fixed["rev"]
    fixed_costs = sol_y_fixed["costs"]
    fixed_profit = fixed_rev - fixed_costs
    '''

    aslb = ASLinesBuilder(depdates,
                          asfwoc.asdr.legs,
                          asfwoc.asdr.duty_ids,
                          asfwoc.asdr.duties,
                          asfwoc.sol_y,
                          asfwoc.asdr.fleet_types,
                          asfwoc.asdr.fleet_type2fleet_ids,
                          asfwoc.asdr.leg_id2duty_id,
                          asfwoc.asdr)
    aslb.build()
    aslb.write_csv("../output/lines.csv")

    #print("Profit = {}".format(profit))
    #print("Fixed proofit = {}".format(fixed_profit))