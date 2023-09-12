from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'
    extra_context = {
        'image_bg': 'img/about.png',
        'head_text': 'Немного обо мне',
    }


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'
    extra_context = {
        'image_bg': 'img/about-bg.jpg',
        'head_text': 'Набор технологий',
    }
