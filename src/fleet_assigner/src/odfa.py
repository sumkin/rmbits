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
    fcstdate = "20260226"
    month = "october2026"

    excel_fname = "fa_{}_{}.xlsx".format(fcstdate, month)
    excel_output_writer = ExcelOutputWriter("../output/{}".format(excel_fname))
    debug_info_writer = DebugInfoWriter("../output/")

    fcstyear, fcstmonth, fcstday = fcstdate[:4], fcstdate[4:6], fcstdate[6:]
    depdates = ["20260930",
                "20261001", "20261002", "20261003", "20261004", "20261005", "20261006", "20261007",
                "20261008", "20261009", "20261010", "20261011", "20261012", "20261013", "20261014",
                "20261015", "20261016", "20261017", "20261018", "20261019", "20261020", "20261021",
                "20261022", "20261023", "20261024"]
    costs_file = "s3://ay-rmp-home/anaplan_costs/{}/{}/{}/{}.csv".format(fcstyear, fcstmonth, fcstday, month)
    fleet_file = "s3://ay-rmp-home/fleet_assigner/input/aircraft_inventory.csv"
    cap_file = "s3://ay-rmp-home/fleet_assigner/input/subfleet_capacities.csv"
    leg_distance_file = "s3://ay-rmp-home/fleet_assigner/input/leg_distances.csv"
    subfleet_ranges_file = "s3://ay-rmp-home/fleet_assigner/input/subfleet_ranges.csv"
    maintenance_file = "s3://ay-rmp-home/fleet_assigner/input/SSIM_S26_OCT.ssim"
    airport_allowance_file = "s3://ay-rmp-home/fleet_assigner/input/airport_allowance.csv"
    leg_pairings_file = "s3://ay-rmp-home/fleet_assigner/input/OPT_Fedor_report.xlsx"
    turnaround_times_file = "s3://ay-rmp-home/fleet_assigner/input/turnaround_times.csv"
    restrictions_file = "s3://ay-rmp-home/fleet_assigner/input/restrictions.csv"

    dill_fwoc_fname = "../cache/fwoc_{}_{}.dill".format(month, fcstdate)
    dill_fwoc_fixed_fname = "../cache/fwoc_fixed_{}_{}.dill".format(month, fcstdate)
    mps_fname = "../cache/model_{}_{}.mps".format(month, fcstdate)
    dill_sol_fname = "../cache/sol_{}_{}.dill".format(month, fcstdate)

    if os.path.exists(dill_fwoc_fname) and\
       os.path.exists(dill_fwoc_fixed_fname) and\
       os.path.exists(mps_fname) and os.path.exists(dill_sol_fname):
        # Read non-fixed subfleets model.
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

        # Read fixed subfleets model.
        with open(dill_fwoc_fixed_fname, "rb") as f:
            fwoc_fixed = dill.load(f)
        fwoc_fixed.model = read(mps_fname)
        vars = fwoc_fixed.model.getVars()

        y_vars = [var for var in vars if "y" in var.VarName]
        fwoc_fixed.y_vars = {}
        for y_var in y_vars:
            var_name = y_var.VarName
            d, k = var_name.split(",")
            d, k = int(d.lstrip("y[")), int(k.rstrip("]"))
            fwoc_fixed.y_vars[(d, k)] = y_var

        z_vars = [var for var in vars if "z" in var.VarName]
        fwoc_fixed.z_vars = {}
        for z_var in z_vars:
            var_name = z_var.VarName
            j = int(var_name.strip("z[").strip("]"))
            fwoc_fixed.z_vars[j] = z_var

        s_vars = [var for var in vars if "s" in var.VarName]
        fwoc_fixed.s_vars = {}
        for s_var in s_vars:
            var_name = s_var.VarName
            d, k = var_name.split(',')
            d, k = int(d.lstrip("s[")), int(k.rstrip("]"))
            fwoc_fixed.s_vars[(d, k)] = s_var
        fwoc_fixed.obj = fwoc_fixed.model.getObjective()

        with open(dill_sol_fname, "rb") as f:
            s = dill.load(f)
            sol = s["sol"]
            sol_y = s["sol_y"]
            sol_y_fixed = s["sol_y_fixed"]
    else:
        subfleets_to_fix = ["A7A", "A70", "31E", "33S", "32I", "73Z"]

        # Optimize with fixed subfleets.
        fwoc_fixed = FARMWoCancellations(fcstdate,
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
        fwoc_fixed.load_data()
        #fwoc.build_model(max_num_changes=1000)
        fwoc_fixed.build_model()
        fwoc_fixed.model.write(mps_fname)

        model, y_vars, z_vars, s_vars, obj = fwoc_fixed.model, fwoc_fixed.y_vars, fwoc_fixed.z_vars, fwoc_fixed.s_vars, fwoc_fixed.obj
        fwoc_fixed.model, fwoc_fixed.y_vars, fwoc_fixed.z_vars, fwoc_fixed.s_vars, fwoc_fixed.obj = None, None, None, None, None
        with open(dill_fwoc_fixed_fname, "wb") as f:
            dill.dump(fwoc_fixed, f)
        fwoc_fixed.model, fwoc_fixed.y_vars, fwoc_fixed.z_vars, fwoc_fixed.s_vars, fwoc_fixed.obj = model, y_vars, z_vars, s_vars, obj

        # Solve.
        fwoc_fixed.make_feasible()
        fwoc_fixed.solve_with_y_fixed()
        sol_y_fixed = fwoc_fixed.get_solution()
        del fwoc_fixed

        # Optimize subfleets.
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

        model, y_vars, z_vars, s_vars, obj = fwoc.model, fwoc.y_vars, fwoc.z_vars, fwoc.s_vars, fwoc.obj
        fwoc.model, fwoc.y_vars, fwoc.z_vars, fwoc.s_vars, fwoc.obj = None, None, None, None, None
        with open(dill_fwoc_fname, "wb") as f:
            dill.dump(fwoc, f)
        fwoc.model, fwoc.y_vars, fwoc.z_vars, fwoc.s_vars, fwoc.obj = model, y_vars, z_vars, s_vars, obj

        # Solve.
        fwoc.make_feasible()
        fwoc.solve()

        # Get solution.
        sol = fwoc.get_solution()
        sol_y = fwoc.sol_y

        debug_info_writer.write_fa_diagram(month, fwoc.dr, sol["y"], sol["m"])

        s = {}
        s["sol"] = sol
        s["sol_y"] = sol_y
        s["sol_y_fixed"] = sol_y_fixed
        with open(dill_sol_fname, "wb") as f:
            dill.dump(s, f)

    fwoc.write_output_excel(s["sol_y_fixed"], s["sol"], s["sol_y"], fwoc.dr)

    lb = LinesBuilder(depdates,
                      fwoc.dr.legs,
                      fwoc.dr.duties,
                      s["sol_y"],
                      fwoc.dr.fleet_types,
                      fwoc.dr.fleet_type2fleet_ids,
                      fwoc.dr.leg2duty,
                      fwoc.dr,
                      excel_output_writer)
    lb.build()
    lb.write_csv("../output/lines.csv")
    s3copy("../output/lines.csv", "s3://ay-rmp-home/fleet_assigner/{}/output/lines.csv".format(month))

    conv = Converter("../output/lines.csv", "../output/lines.ssim")
    conv.convert()
    s3copy("../output/lines.ssim", "s3://ay-rmp-home/fleet_assigner/{}/output/lines.ssim".format(month))

    s3copy("../output/{}".format(excel_fname), "s3://ay-rmp-home/fleet_assigner/{}/output/{}".format(month, excel_fname))