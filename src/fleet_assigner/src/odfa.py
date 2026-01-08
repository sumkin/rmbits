import os
import dill
import uuid
from gurobipy import *

from s3utils import s3copy
from excel_output_writer import ExcelOutputWriter
from debug_info_writer import DebugInfoWriter
from farm_wo_cancellations import FARMWoCancellations
from lines_builder import LinesBuilder
from CsvToSsimConverter import Converter

if __name__ == "__main__":
    fcstdate = "20260107"
    month = "march2026"

    excel_fname = "fa_{}_{}.xlsx".format(fcstdate, month)
    excel_output_writer = ExcelOutputWriter("../output/{}".format(excel_fname))
    debug_info_writer = DebugInfoWriter("../output/")

    fcstyear, fcstmonth, fcstday = fcstdate[:4], fcstdate[4:6], fcstdate[6:]
    depdates = ["20260228",
                "20260301", "20260302", "20260303", "20260304", "20260305", "20260306", "20260307",
                "20260308", "20260309", "20260310", "20260311", "20260312", "20260313", "20260314",
                "20260315", "20260316", "20260317", "20260318", "20260319", "20260320", "20260321",
                "20260322", "20260323", "20260324", "20260325", "20260326", "20260327", "20260328",
                "20260329"]
    #depdates = ["20260214", "20260215", "20260216"]
    costs_file = "s3://ay-emr-job/anaplan_costs/{}/{}/{}/{}.csv".format(fcstyear, fcstmonth, fcstday, month)
    fleet_file = "s3://ay-emr-job/fleet_assigner/input/aircraft_inventory.csv"
    cap_file = "s3://ay-emr-job/fleet_assigner/input/subfleet_capacities.csv"
    leg_distance_file = "s3://ay-emr-job/fleet_assigner/input/leg_distances.csv"
    subfleet_ranges_file = "s3://ay-emr-job/fleet_assigner/input/subfleet_ranges.csv"
    maintenance_file = "s3://ay-emr-job/fleet_assigner/input/SSIMMAR08JANnolimits.ssim"
    airport_allowance_file = "s3://ay-emr-job/fleet_assigner/input/airport_allowance.csv"
    leg_pairings_file = "s3://ay-emr-job/fleet_assigner/input/report_08JAN_nolimits.xlsx"
    turnaround_times_file = "s3://ay-emr-job/fleet_assigner/input/turnaround_times.csv"
    restrictions_file = "s3://ay-emr-job/fleet_assigner/input/restrictions.csv"

    dill_fwoc_fname = "../cache/fwoc_{}_{}.dill".format(month, fcstdate)
    mps_fname = "../cache/model_{}_{}.mps".format(month, fcstdate)
    dill_sol_fname = "../cache/sol_{}_{}.dill".format(month, fcstdate)
    if os.path.exists(dill_fwoc_fname) and os.path.exists(mps_fname) and os.path.exists(dill_sol_fname):
        with open(dill_fwoc_fname, "rb") as f:
            fwoc = dill.load(f)
        fwoc.model = read(mps_fname)
        vars = fwoc.model.getVars()

        y_vars = [var for var in vars if "y" in var.VarName]
        fwoc.y_vars = {}
        for y_var in y_vars:
            var_name = y_var.VarName
            d, k = var_name.split(",")
            d, k = int(d.lstrip("y[")), int(k.rstrip("]"))
            fwoc.y_vars[(d, k)] = y_var

        z_vars = [var for var in vars if "z" in var.VarName]
        fwoc.z_vars = {}
        for z_var in z_vars:
            var_name = z_var.VarName
            j = int(var_name.strip("z[").strip("]"))
            fwoc.z_vars[j] = z_var

        s_vars = [var for var in vars if "s" in var.VarName]
        fwoc.s_vars = {}
        for s_var in s_vars:
            var_name = s_var.VarName
            d, k = var_name.split(',')
            d, k = int(d.lstrip("s[")), int(k.rstrip("]"))
            fwoc.s_vars[(d, k)] = s_var
        fwoc.obj = fwoc.model.getObjective()

        with open(dill_sol_fname, "rb") as f:
            s = dill.load(f)
            sol = s["sol"]
            sol_y_fixed = s["sol_y_fixed"]
    else:
        subfleets_to_fix = ["A7A", "A70", "33S"]
        #subfleets_to_fix = []
        fwoc = FARMWoCancellations(fcstdate,
                                   month,
                                   depdates,
                                   costs_file,
                                   fleet_file,
                                   cap_file,
                                   leg_distance_file,
                                   subfleet_ranges_file,
                                   maintenance_file,
                                   airport_allowance_file,
                                   leg_pairings_file,
                                   turnaround_times_file,
                                   restrictions_file,
                                   excel_output_writer,
                                   debug_info_writer,
                                   subfleets_to_fix)
        fwoc.load_data()
        #fwoc.build_model(max_num_changes=1000)
        fwoc.build_model()
        fwoc.model.write(mps_fname)

        model = fwoc.model
        y_vars = fwoc.y_vars
        z_vars = fwoc.z_vars
        s_vars = fwoc.s_vars
        obj = fwoc.obj

        fwoc.model = None
        fwoc.y_vars = None
        fwoc.z_vars = None
        fwoc.s_vars = None
        fwoc.obj = None
        with open(dill_fwoc_fname, "wb") as f:
            dill.dump(fwoc, f)
        fwoc.model = model

        fwoc.y_vars = y_vars
        fwoc.z_vars = z_vars
        fwoc.s_vars = s_vars
        fwoc.obj = obj

        fwoc.make_feasible()

        # Solve.
        fwoc.solve()
        sol = fwoc.get_solution()
        sol_y = fwoc.sol_y

        # Solve with current assignment fixed.
        fwoc.solve_with_y_fixed()
        sol_y_fixed = fwoc.get_solution()

        debug_info_writer.write_fa_diagram(month, fwoc.dr, sol["y"], sol["m"])

        s = {}
        s["sol"] = sol
        s["sol_y_fixed"] = sol_y_fixed
        with open(dill_sol_fname, "wb") as f:
            dill.dump(s, f)

    fwoc.write_output_excel(s["sol_y_fixed"], s["sol"], fwoc.dr)

    lb = LinesBuilder(depdates,
                      fwoc.dr.legs,
                      fwoc.dr.duties,
                      fwoc.sol_y,
                      fwoc.dr.fleet_types,
                      fwoc.dr.fleet_type2fleet_ids,
                      fwoc.dr.leg2duty,
                      fwoc.dr,
                      excel_output_writer)
    lb.build()
    lb.write_csv("../output/lines.csv")
    s3copy("../output/lines.csv", "s3://ay-emr-job/fleet_assigner/{}/output/lines.csv".format(month))

    conv = Converter("../output/lines.csv", "../output/lines.ssim")
    conv.convert()
    s3copy("../output/lines.ssim", "s3://ay-emr-job/fleet_assigner/{}/output/lines.ssim".format(month))

    s3copy("../output/{}".format(excel_fname), "s3://ay-emr-job/fleet_assigner/{}/output/{}".format(month, excel_fname))