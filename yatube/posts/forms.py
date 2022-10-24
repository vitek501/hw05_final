from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {
            'text': forms.Textarea(
                attrs={'cols': "40",
                       'rows': "10",
                       'class': "form-control",
                       'required id': "id_text"}),
            'group': forms.Select(
                attrs={'class': "form-control",
                       'id': "id_group"})
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': _('Текст комментария'),
        }
        widgets = {
            'text': forms.Textarea(
                attrs={'cols': "40",
                       'rows': "10",
                       'class': "form-control",
                       'required id': "id_text"}),
        }
