from __future__ import unicode_literals
import hashlib
from django.db import models

class Cat(models.Model):
    cat_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=255, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'cats'

    def __str__(self):
        return self.label
    
class Source(models.Model):
    SOURCETYPES = (
        ('personal', 'personal website'),
        ('repo', 'repository'),
        ('journal', 'journal'),
        ('blog', 'weblog'),
    )
    source_id = models.AutoField(primary_key=True)
    sourcetype = models.CharField(max_length=16, choices=SOURCETYPES, default='personal')
    url = models.URLField(max_length=512)
    urlhash = models.CharField(unique=True, max_length=32, editable=False)
    status = models.SmallIntegerField(blank=True, default=0)
    found_date = models.DateTimeField()
    last_checked = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    default_author = models.CharField(max_length=128, blank=True, null=True)

    def save(self, *args, **kwargs):
        """set urlhash to MD5(url)"""
        self.urlhash = hashlib.md5.new(self.url).digest()
        super(Model, self).save(*args, **kwargs)
        
    def __str__(self):
        return '{}. {} ({})'.format(self.source_id, self.name, self.url[:40])

    class Meta:
        db_table = 'sources'

class Link(models.Model):
    link_id = models.AutoField(primary_key=True)
    url = models.URLField(max_length=512)
    urlhash = models.CharField(max_length=32, editable=False)
    status = models.SmallIntegerField(blank=True, default=0)
    source_id = models.IntegerField()
    found_date = models.DateTimeField()
    last_checked = models.DateTimeField(blank=True, null=True)
    etag = models.CharField(max_length=255, blank=True, null=True)
    filesize = models.IntegerField(blank=True, null=True)
    doc_id = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """set urlhash to MD5(url)"""
        self.urlhash = hashlib.md5.new(self.url).digest()
        super(Model, self).save(*args, **kwargs)

    def __str__(self):
        return '{}. Source {} -> {}'.format(self.link_id, self.source_id, self.url[:60])

    class Meta:
        db_table = 'links'
        unique_together = (('source_id', 'urlhash'),)

class Doc(models.Model):
    DOCTYPES = (
        ('article', 'article'),
        ('book', 'book'),
        ('chapter', 'book chapter'),
        ('thesis', 'thesis'),
        ('review', 'review'),
    )
    doc_id = models.AutoField(primary_key=True)
    status = models.SmallIntegerField(blank=True, default=1)
    url = models.URLField(max_length=512)
    urlhash = models.CharField(unique=True, max_length=32, editable=False)
    doctype = models.CharField(max_length=16, choices=DOCTYPES, default='article')
    filetype = models.CharField(max_length=8, blank=True, null=True)
    filesize = models.IntegerField(blank=True, null=True)
    found_date = models.DateTimeField(blank=True, null=True)
    earlier_id = models.IntegerField(blank=True, null=True)
    authors = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    numwords = models.PositiveIntegerField(blank=True, null=True)
    numpages = models.PositiveSmallIntegerField(blank=True, null=True)
    source_url = models.URLField(max_length=512, blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True, null=True)
    meta_confidence = models.IntegerField(blank=True, null=True)
    is_paper = models.IntegerField(blank=True, null=True)
    is_philosophy = models.IntegerField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    cats = models.ManyToManyField(Cat, through='Doc2Cat')
    
    def _default_cats(self):
        """
        returns list of default cats paired with strengths,
        e.g. [('Epistemology', 0.1),...]
        """
        self.cats.filter(is_default=0)
    default_cats = property(_default_cats)

    def save(self, *args, **kwargs):
        """set urlhash to MD5(url)"""
        self.urlhash = hashlib.md5.new(self.url).digest()
        super(Model, self).save(*args, **kwargs)

    def __str__(self):
        return '{}. {} ({})'.format(self.doc_id, self.title[:40], self.url[:40])
        
    class Meta:
        db_table = 'docs'

class AuthorName(models.Model):
    name_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    last_searched = models.DateTimeField(blank=True, null=True)
    is_name = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'author_names'
    
    def __str__(self):
        return '{}. {}'.format(self.name_id, self.name)

class Doc2Cat(models.Model):
    doc2cat_id = models.AutoField(primary_key=True)
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE)
    cat = models.ForeignKey(Cat, on_delete=models.CASCADE)
    strength = models.IntegerField(blank=True, null=True)
    is_training = models.BooleanField(default=0)

    class Meta:
        db_table = 'docs2cats'
        unique_together = (('doc', 'cat'),)

    def __str__(self):
        return 'Doc {} -> Cat {}'.format(self.doc_id, self.cat_id)
        
