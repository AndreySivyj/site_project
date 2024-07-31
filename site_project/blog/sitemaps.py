from django.contrib.sitemaps import Sitemap
from .models import Post


class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Post.published.all() # возвращает QuerySet объектов, подлежащих включению в карту сайта, 
                                    # по умолчанию вызывает метод get_absolute_url() по каждому объекту
    
    def lastmod(self, obj):
        return obj.updated  # возвращает время последнего изменения объекта