import hashlib
from operator import itemgetter
from django.db import models
from django.contrib.auth.models import User

class Cat(models.Model):
    cat_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cats'

    def num_training_pos(self):
        """number of positive training documents"""
        return self.doc_set.filter(doc2cat__is_training=1, doc2cat__strength=100).count()

    def num_training_neg(self):
        """number of negative training documents"""
        return self.doc_set.filter(doc2cat__is_training=1, doc2cat__strength=0).count()

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
        self.urlhash = hashlib.md5(self.url.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return '{}. {} ({})'.format(self.source_id, self.name, self.url[:40])

    def num_links(self):
        return self.link_set.count()

    def num_docs(self):
        return self.doc_set.count()
        
    class Meta:
        db_table = 'sources'
        ordering = ['name']

class Link(models.Model):
    link_id = models.AutoField(primary_key=True)
    url = models.URLField(max_length=512)
    urlhash = models.CharField(max_length=32, editable=False)
    status = models.SmallIntegerField(blank=True, default=0)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    #source_id = models.IntegerField()
    found_date = models.DateTimeField()
    last_checked = models.DateTimeField(blank=True, null=True)
    etag = models.CharField(max_length=255, blank=True, null=True)
    filesize = models.IntegerField(blank=True, null=True)
    #doc_id = models.IntegerField()
    doc = models.ForeignKey('Doc', on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        """set urlhash to MD5(url)"""
        self.urlhash = hashlib.md5(self.url.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return '{}. Source {} -> {}'.format(self.link_id, self.source, self.url[:60])

    class Meta:
        db_table = 'links'
        unique_together = (('source', 'urlhash'),)

class Doc(models.Model):
    DOCTYPES = (
        ('article', 'article'),
        ('book', 'book'),
        ('chapter', 'book chapter'),
        ('thesis', 'thesis'),
        ('review', 'review'),
        ('blogpost', 'blogpost'),
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
    # The following two fields are there for documents whose source has gone dead
    source_url = models.URLField(max_length=512, blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    hidden = models.BooleanField(default=False)
    meta_confidence = models.IntegerField(blank=True, null=True)
    is_paper = models.IntegerField(blank=True, null=True)
    is_philosophy = models.IntegerField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    cats = models.ManyToManyField(Cat, through='Doc2Cat')

    def _cats(self):
        """
        returns list of cats paired with strengths >= 50 rounded to
        multiples of 10, e.g. [('Epistemology', 70),...]
        """
        ms = self.doc2cat_set.filter(strength__gte=50)
        pairs = [(m.cat.label, int(round(m.strength, -1))) for m in ms]
        return sorted(pairs, key=itemgetter(1), reverse=True)
    topics = property(_cats)
    
    def _low_confidence(self):
        return self.meta_confidence <= 60
    low_confidence = property(_low_confidence)

    def _is_blogpost(self):
        return self.doctype == 'blogpost'
    is_blogpost = property(_is_blogpost)

    def save(self, *args, **kwargs):
        """set urlhash to MD5(url)"""
        self.urlhash = hashlib.md5(self.url.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return '{}. {} ({})'.format(self.doc_id, self.title[:40], self.url[:40])
        
    class Meta:
        db_table = 'docs'
        ordering = ['-found_date']

class AuthorName(models.Model):
    name_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    last_searched = models.DateTimeField(blank=True, null=True)
    is_name = models.BooleanField(default=True)

    class Meta:
        db_table = 'author_names'
    
    def __str__(self):
        return '{}. {}'.format(self.name_id, self.name)

class Journal(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=64)

    class Meta:
        db_table = 'journals'
    
    def __str__(self):
        return self.name
        
class Doc2Cat(models.Model):
    doc2cat_id = models.AutoField(primary_key=True)
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE)
    cat = models.ForeignKey(Cat, on_delete=models.CASCADE)
    strength = models.IntegerField(blank=True, null=True)
    is_training = models.BooleanField(default=False)

    class Meta:
        db_table = 'docs2cats'
        unique_together = (('doc', 'cat'),)

    def __str__(self):
        return 'Doc {} -> Cat {}'.format(self.doc_id, self.cat_id)
        
class Doc2User(models.Model):
    doc2user_id = models.AutoField(primary_key=True)
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    strength = models.IntegerField(blank=True, null=True)
    is_training = models.BooleanField(default=False)

    class Meta:
        db_table = 'docs2users'
        unique_together = (('doc', 'user'),)

    def __str__(self):
        return 'Doc {} -> User {}'.format(self.doc_id, self.user_id)
