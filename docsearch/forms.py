from django import forms
from .models import Author, Comment, Topic, Document


class AuthorForm(forms.ModelForm):

    class Meta:
        fields = ('author_name', 'country', 'citation_index')
        model = Author

class TopicForm(forms.ModelForm):

    class Meta:
        fields = ('topic', )
        model = Document

class CommentForm(forms.ModelForm):

    class Meta:
        fields = ('comment_text', )
        model = Comment


class SearchLineForm(forms.Form):
    text_request = forms.CharField(max_length=200)


class SearchFileForm(forms.Form):
    file_request = forms.FileField()