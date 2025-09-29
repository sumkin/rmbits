from scipy.sparse import coo_matrix


def getA(dr):
    Adata = dr.rm_model["Adata"]
    Ai = dr.rm_model["Ai"]
    Aj = dr.rm_model["Aj"]
    cap = dr.rm_model["cap"]
    fcap = dr.rm_model["fcap"]
    d = dr.rm_model["d"]
    A = coo_matrix((Adata, (Ai, Aj)), shape = (len(cap), len(d)))
    return A


def get_E(dr):
    fcap = dr.rm_model["fcap"]
    nrows = len(fcap)
    num_duties = dr.get_num_duties()
    E = np.zeros((nrows, num_duties))
    for nrow in range(nrows):
        rsrc_name = dr.rm_model["rsrc_names"][nrow]
        i = dr.get_leg_id_by_rsrc_name(rsrc_name)
        d = dr.get_duty_id_by_leg_id(i)
        E[nrow, d] = 1 
    return E
         

def get_c():
    pass 


def get_B():
    fcap = dr.rm_model["fcap"]
    cap = dr.rm_model["cap"]
    b = fcap - cap 

    nrows = len(b)
    num_fleet_types = dr.get_num_fleet_types()
    B = np.zeros((nrows, num_fleet_types))
    for nrow in range(nrows):
        B[nrow, :] = [b] * num_fleet_types 
    return B  


def get_1():
    pass 



