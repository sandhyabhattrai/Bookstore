from django import forms
from .models import Category,Book

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name']

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        exclude = ['created_at']

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Price can't be negative.") 
        return price

    def clean_name(self):
        name = self.cleaned_data['name']
        if not name[0].isupper():
            raise forms.ValidationError("Book name must start with capital letter.")
        return name
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        description = cleaned_data.get('description')
        if name.lower() == description.lower():
                raise forms.ValidationError("Book name and description can't be same.")
        return cleaned_data
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        author = cleaned_data.get('author')
        if name.lower() == author.lower():
                raise forms.ValidationError("Book name and author name can't be same.")
        return cleaned_data
