from simulator import Simulator
from demand_influences import *
from capacity_influences import *
from yield_influences import *

if __name__ == "__main__":
    sim = Simulator("20240305",
                    "partnership_sce2_",
                    "final",
                    partnership_sce2_dmd,
                    partnership_sce2_cap,
                    partnership_sce2_yld)
    sim.simulate()