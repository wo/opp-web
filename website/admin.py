from django.contrib import admin
from .models import Source,Link,Doc,AuthorName,Cat,Doc2Cat

admin.site.register(Source)
admin.site.register(Link)
admin.site.register(Doc)
admin.site.register(AuthorName)
admin.site.register(Cat)
admin.site.register(Doc2Cat)
