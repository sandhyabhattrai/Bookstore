from django import forms
from .models import Order

class OrderFrom(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['quantity','address','contact_no','payment_method']

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError("Quantity should be greater than 0.")
        return quantity