from stormvogel import *
import stormpy
from playground import show

prism_code = stormpy.parse_prism_program("prism_example.prism")
prism_die = mapping.from_prism(prism_code)
result = model_checking(prism_die, "P=? [F \"rolled1\"]")
show(prism_die, result)
