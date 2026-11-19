STAGES = {
    "carriage_loops": {
        "A": {"outer_kp": 1., "inner_kp": 1.5, "inner_ki": 0.},
        "B": {"inner_ki": 4.},
        "C": {"outer_kp": 3.},
    },
    "cart_stop": {
        "A": {"q_position": 8., "q_velocity": 2., "r_effort": 1.},
        "B": {"r_effort": 5.},
        "C": {"r_effort": 2.},
        "D": {"q_velocity": 4.},
    },
    "range_step": {
        "A": {"q_process": .02, "r_measure": .01},
        "B": {"r_measure": .0625},
        "C": {"q_process": .0002},
        "D": {"q_process": .002},
    },
}
