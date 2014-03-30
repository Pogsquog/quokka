from django import forms
from django.db import models
from django.forms import ModelForm
from parsley.decorators import parsleyfy

from accounts.models import UserProfile


class Tag(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Team(models.Model):
    leader = models.ForeignKey(UserProfile, related_name='+')
    name = models.CharField(max_length=20, unique=True)
    members = models.ManyToManyField(UserProfile)

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    team = models.ForeignKey(Team, null=True, blank=True)
    authorisers = models.ManyToManyField(UserProfile)
    subscribers = models.ManyToManyField(UserProfile, related_name='+')
    img = models.ImageField(null=True, blank=True)

    @property
    def latest(self):
        tagged = []
        if self.releases:
            tagged.append({"tag": None, "release": self.releases[0]})
        for tag in Tag.objects.all().order_by("name"):
            forTag = Release.objects.filter(project=self, tag=tag).order_by("-dateTime")
            if forTag:
                tagged.append({"tag": tag, "release": forTag[0]})

        return tagged
    @property
    def releases(self):
        return Release.objects.filter(project=self).order_by("-dateTime")

    def __str__(self):
        return self.name


@parsleyfy
class ProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = []

class Release(models.Model):
    number = models.CharField(max_length=20, unique=True)
    project = models.ForeignKey(Project)
    notes = models.TextField()
    dateTime = models.DateTimeField()
    url = models.URLField()
    tag = models.ManyToManyField(Tag, null=True, blank=True)

    def __str__(self):
        return self.number

    def user_response_object(self, user):
        return Response.objects.filter(release=self).get(user=user)


@parsleyfy
class ReleaseForm(ModelForm):
    class Meta:
        model = Release
        exclude = ['dateTime']

class ResponseCodes():
    Pending = 0
    Accept = 1
    Reject = 2

class Response(models.Model):
    response = models.IntegerField(choices=(
        (ResponseCodes.Pending, "Pending"),
        (ResponseCodes.Accept, "Accept"),
        (ResponseCodes.Reject, "Reject"),
    ), default=0)

    release = models.ForeignKey(Release)
    reason = models.TextField(null=True, blank=True)
    user = models.ForeignKey(UserProfile)

    class Meta:
        unique_together = (("release", "user"),)

@parsleyfy
class AcceptResponseForm(ModelForm):
    message = "Accept the release?"
    class Meta:
        model = Response
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['response'].widget = forms.HiddenInput()
        self.fields['user'].widget = forms.HiddenInput()
        self.fields['release'].widget = forms.HiddenInput()
        self.fields['reason'].widget = forms.HiddenInput()


@parsleyfy
class RejectResponseForm(ModelForm):
    class Meta:
        model = Response
        exclude = []

        parsley_extras = {
            "reason": {
                "required": True
            }
        }
    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['response'].widget = forms.HiddenInput()
    #     self.fields['user'].widget = forms.HiddenInput()
    #     self.fields['release'].widget = forms.HiddenInput()