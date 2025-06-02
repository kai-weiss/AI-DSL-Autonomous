from DSL.metamodel import Model


class UppaalVerifier:
    def __init__(self, verifyta: str = "verifyta"):
        self.verifyta = verifyta

    def check(self, model: Model, props: list[str]) -> dict:
        pass
        # build -> run -> parse, return a dict {prop_id: True/False or numeric metrics}
