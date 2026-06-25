from django import forms
from .models import Submission

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file', 'text_answer']
        widgets = {
            'text_answer': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Write your answer here...'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        text = cleaned_data.get('text_answer')
        
        # Student must submit either a file OR text
        if not file and not text:
            raise forms.ValidationError('Please upload a file OR write your answer in the text box.')
        
        # If file is uploaded, check file type
        if file:
            allowed_types = ['pdf', 'doc', 'docx', 'txt']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_types:
                raise forms.ValidationError(f'File type not allowed. Allowed: {", ".join(allowed_types)}')
        
        return cleaned_data