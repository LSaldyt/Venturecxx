import vehicle_program as vp
from venture.shortcuts import make_puma_church_prime_ripl


# vehicle
vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717


program_constants = """

[assume vehicle_params (list %s %s %s %s)]

""" % (vehicle_a, vehicle_b, vehicle_h, vehicle_L)

program_hypers = """

[assume fractional_xy_error_std (scope_include (quote hypers)
                                               0
                                               (gamma 1.0 100.0))]

[assume fractional_heading_error_std (scope_include (quote hypers)
                                                    1
                                                    (gamma 1.0 100.0))]

[assume additive_xy_error_std (scope_include (quote hypers)
                                             2
                                             (gamma 1.0 100.0))]

[assume additive_heading_error_std (scope_include (quote hypers)
                                                  3
                                                  (gamma 1.0 100.0))]

"""


program_assumes = """

[assume get_dt_i (mem (lambda (i) (uniform_continuous 0 100)))]

[assume _get_control_i (scope_include (quote state) 1000002
  (mem (lambda (i coord)
    (if (= coord 0)
        (gamma 1.0 1.0)
        (normal 0 0.1)
        ))))]

[assume get_control_i (lambda (i)
  (list (_get_control_i i 0)
        (_get_control_i i 1)
        ))]

[assume initial_pose (scope_include (quote state) 0 (list (uniform_continuous -1 1)
                                                          (uniform_continuous -1 1)
                                                          (uniform_continuous -1 1)))]

[assume get_pose_i (mem (lambda (i)
  (if (= i 0) initial_pose
              (scope_include (quote state) i (simulate_motion (get_dt_i (- i 1))
                                                              (get_pose_i (- i 1))
                                                              (get_control_i (- i 1))
                                                              vehicle_params
                                                              fractional_xy_error_std
                                                              fractional_heading_error_std
                                                              additive_xy_error_std
                                                              additive_heading_error_std
                                                              )))))]

"""

program = program_constants + program_hypers + program_assumes

def _wrap(val):
    def _wrap_real(val):
        return dict(type='real', value=val)
    def _wrap_list(val):
        return dict(type='vector', value=map(_wrap, val))
    is_list = isinstance(val, (list, tuple))
    return _wrap_list(val) if is_list else _wrap_real(val)

def predict(predict_str):
    return ripl.predict(predict_str)

def print_predicted((predict_str, predicted)):
    print "%s: %s" % (predict_str, predicted)
    return


def create_venture_strs(i):
    return [
            ('(get_dt_i %s)' % i),
            ('(_get_control_i %s 0)' % i),
            ('(_get_control_i %s 1)' % i),
            ('(simulate_gps (get_pose_i %s) .1 .01)' % i),
            ('(get_pose_i %s)' % i),
            ]
import operator
N_steps = 30
def get_predicts(N_steps):
    return reduce(operator.add, map(create_venture_strs, range(N_steps)))
def create_observes(i):
    venture_strs = create_venture_strs(i)
    dt = .1
    velocity = 1
    return [
            (venture_strs[0], dt),
            (venture_strs[1], velocity),
            (venture_strs[2], 0),
            (venture_strs[3], _wrap((i*dt*velocity, 0, 0))),
            ]
def get_observes(N_steps):
    return reduce(operator.add, map(create_observes, range(N_steps)))

to_observe = get_observes(N_steps)
to_predict = get_predicts(N_steps)


ripl = make_puma_church_prime_ripl()
ripl.execute_program(program)
predicted = map(predict, to_predict)
map(print_predicted, zip(to_predict, predicted))
print
map(lambda x: ripl.observe(*x), to_observe)
ripl.infer('(mh default all 4)')
predicted = map(predict, to_predict)
map(print_predicted, zip(to_predict, predicted))
print
