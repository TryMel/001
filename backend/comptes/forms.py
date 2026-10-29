from unfold.forms import AuthenticationForm


class FormulaireConnexionAdministration(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Adresse e-mail"
        self.fields["username"].widget.attrs["placeholder"] = "admin@akasha.app"
        self.fields["password"].label = "Mot de passe"
        self.fields["password"].widget.attrs["placeholder"] = "Votre mot de passe"
