from django import template


register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.inclusion_tag('includes/nav.html')
def show_nav(username=None) -> list:
    menu = [
        {'title': 'Об авторе', 'url_name': 'about:author'},
        {'title': 'Технологии', 'url_name': 'about:tech'},
        {'title': 'Новая запись', 'url_name': 'posts:post_create'},
        {'title': 'Изменить пароль', 'url_name': 'users:password_change'},
        {'title': 'Выйти', 'url_name': 'users:logout'},
        {'title': 'Пользователь', 'url_name': 'posts:profile'},
        {'title': 'Войти', 'url_name': 'users:login'},
        {'title': 'Регистрация', 'url_name': 'users:signup'},
    ]
    if username is not None:
        username = username
        del (
            menu[7],
            menu[6]
        )
        m = {'menu': menu, 'username': username}
        return m
    else:
        for x in range(4):
            del menu[2]
        m = {'menu': menu}
        return m
