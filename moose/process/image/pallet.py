import random

colors = (
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
    (255, 102, 102),
    (255, 255, 0),
    (0, 102, 153),
    (255, 153, 102),
    (0, 102, 204),
    (51, 153, 51),
    (255, 204, 51),
    (51, 102, 153),
    (255, 153, 0),
    (255, 255, 204),
    (204, 102, 0),
    (204, 204, 68),
    (153, 204, 51),
    (0, 153, 204),
    (153, 204, 204),
    (0, 100, 100),
    (255, 0, 51),
    (204, 204, 0),
    (51, 204, 153),
    (0, 125, 255),
    (0, 255, 100),
    (0, 51, 200),
    (125, 0, 200),
    (100, 0, 125),
    (51, 0, 153),
    (100, 125, 0),
    (0, 100, 53),
    (153, 0, 102),
    (255, 204, 0),
    (204, 0, 51),
    (51, 51, 153),
    (102, 102, 153),
)

def dip(k=1):
    '''
    choose one or mutiple random value from the pallet
    '''
    if k < len(colors):
        return random.sample(colors, k)
    else:
        raise ValueError("not support so many color")

GLOBAL_PALLET = {}
def create_pallet(datalist, is_global=True, identity=None):
    '''
    Not only choose colors, but also defines a label-color map.
    Makes it unique in global if necessary.
    '''
    if is_global:
        local_pallet = GLOBAL_PALLET
    else:
        local_pallet = {}

    for label, _ in datalist:
        if not local_pallet.get(label):
            used_colors_counter = len(local_pallet)
            local_pallet[label] = colors[used_colors_counter+1]

    return local_pallet
