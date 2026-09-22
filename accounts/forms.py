from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
        }),
    )
