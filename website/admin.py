from django.contrib import admin
from .models import Source,Link,Doc,AuthorName,Journal,Cat,Doc2Cat

class Doc2CatInline(admin.TabularInline):
    model = Doc2Cat

class DocAdmin(admin.ModelAdmin):
    inlines = (Doc2CatInline,)
    list_display = ('doc_id', 'authors', 'title', 'found_date', 'meta_confidence')
    list_display_links = ('doc_id', 'found_date')
    list_editable = ('authors', 'title')
    list_filter = ['found_date', 'status']
    search_fields = ['authors', 'title']
    date_hierarchy = 'found_date'
    fieldsets = (
        (None, {
            'fields': ('url', 'doctype', 'authors', 'title', 'abstract')
        }),
        ('More', {
            'classes': ('collapse',),
            'fields': ('status', 'filetype', 'found_date', 'earlier_id', 'numwords', 'numpages', 
                       'source_url', 'source_name', 'meta_confidence', 'is_paper', 
                       'is_philosophy', 'content'),
        }),
    )
    
admin.site.register(Doc, DocAdmin)

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'status', 'found_date')
    list_display_links = ('name', 'url', 'found_date')
    list_filter = ['sourcetype', 'found_date']
    search_fields = ['name', 'url']
    date_hierarchy = 'found_date'
    fields = ('url', 'sourcetype', 'name', 'default_author', 'status', 'found_date')

admin.site.register(Source, SourceAdmin)

class CatAdmin(admin.ModelAdmin):
    list_display = ('label', 'num_training_pos', 'num_training_neg')
    inlines = (Doc2CatInline,)
    
admin.site.register(Cat, CatAdmin)

admin.site.register(Link)
admin.site.register(AuthorName)
admin.site.register(Journal)
