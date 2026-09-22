from django import forms
from django.core.validators import RegexValidator

from .models import Order


class OrderForm(forms.ModelForm):
    contact_no = forms.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^[+\d][\d\s\-]{6,14}$',
            message='Enter a valid contact number.',
        )],
    )

    class Meta:
        model = Order
        # payment_method is Cash on Delivery only (set in the view).
        fields = ['quantity', 'address', 'contact_no']

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError("Quantity should be greater than 0.")
        return quantity
