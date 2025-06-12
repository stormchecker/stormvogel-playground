# Playground utility functions
import stormvogel
import base64
import os
import io
import matplotlib.figure

def show(something: any, something_other: any = None) -> str:
    """
    Convert the input to HTML for display in the playground.
    """
    def add_doctype(html: str) -> str:
        """Add a doctype to the HTML string."""
        return f"<!DOCTYPE html>\n<html>{html}</html>"

    if isinstance(something, stormvogel.Model):
        vis = stormvogel.show(something, something_other, do_init_server=False)
        print(vis.generate_html())
    elif str(type(something)).startswith("Sparse"):
        import stormvogel.stormpy_utils.mapping as mapping
        stormvogel_model = mapping.stormpy_to_stormvogel(something)
        vis = stormvogel.show(stormvogel_model, something_other, do_init_server=False)
        print(vis.generate_html())
    elif isinstance(something, str) and os.path.isfile(something):
        ext = os.path.splitext(something)[1].lower()
        if ext in [".png", ".gif", ".jpg", ".jpeg"]:
            with open(something, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            mime = "image/png" if ext == ".png" else "image/gif" if ext == ".gif" else "image/jpeg"
            html = f'<img src="data:{mime};base64,{encoded}" />'
            print(add_doctype(html))
    elif (hasattr(something, "figure") and callable(getattr(something, "figure", None))) or isinstance(something, matplotlib.figure.Figure):
        import matplotlib.pyplot as plt
        fig = something.figure if hasattr(something, "figure") else something
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        html = f'<img src="data:image/png;base64,{encoded}" />'
        print(add_doctype(html))
        plt.close(fig)
    else:   
        raise RuntimeError(f"I don't know how to display {something} of type {type(something)}.")
