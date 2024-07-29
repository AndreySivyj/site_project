from django.contrib import admin
from .models import Post, Comment


# admin.site.register(Post)
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status',]
    list_filter = ['status', 'created', 'publish', 'author']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)} #предзаполнение поля на основании другого поля
    raw_id_fields = ['author'] #поле отображается в виде поискового виджета, вместо выпадающего списка (ForeignKey)
    date_hierarchy = 'publish' #навигация по иерархии дат
    ordering = ['status', 'publish']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']