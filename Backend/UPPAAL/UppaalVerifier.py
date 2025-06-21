from DSL.metamodel import Model
import xml.etree.ElementTree as ET
import tempfile
import subprocess
import os


class UppaalVerifier:
    def __init__(self, verifyta: str = "verifyta"):
        self.verifyta = verifyta

    def check(self, model: Model, props: list[str]) -> dict:
        """Run UPPAAL verifyta on the given model for the selected properties"""
        xml_path = self._build_model(model)

        results: dict[str, bool | None] = {}
        for prop in props:
            query = model.properties.get(prop)
            if query is None:
                results[prop] = None
                continue

            with tempfile.NamedTemporaryFile("w", suffix=".q", delete=False) as qf:
                qf.write(query)
                qfile = qf.name

            try:
                proc = subprocess.run(
                    [self.verifyta, xml_path, qfile],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                out = proc.stdout.lower()
                results[prop] = "property is satisfied" in out or "pass" in out
            except FileNotFoundError:
                results[prop] = None
            finally:
                os.remove(qfile)

        os.remove(xml_path)
        return results

    def _build_model(self, model: Model) -> str:
        """Translate the DSL model into a minimal UPPAAL XML and return its path"""
        nta = ET.Element("nta")

        system = ET.SubElement(nta, "system")
        system.text = "system " + ", ".join(model.components.keys()) + ";"

        for comp in model.components.values():
            template = ET.SubElement(nta, "template")
            ET.SubElement(template, "name").text = comp.name
            ET.SubElement(template, "declaration").text = "clock x;"
            loc = ET.SubElement(template, "location", id=f"{comp.name}_Init")
            ET.SubElement(loc, "name").text = "Init"

        with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as xf:
            xf.write(ET.tostring(nta, encoding="unicode"))
            return xf.name
