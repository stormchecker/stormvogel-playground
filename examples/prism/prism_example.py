from stormvogel import *
import stormpy
prism_code = stormpy.parse_prism_program("prism_example.prism")
prism_die = mapping.from_prism(prism_code)
vis3 = show(prism_die,do_init_server=False)
print(vis3.generate_html())

