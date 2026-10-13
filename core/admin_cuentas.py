# -*- coding: utf-8 -*-
"""Las cuentas del panel, con los campos visibles.

**El fallo que arregla esto.** `auth.User` y `auth.Group` los registra Django
con su propio admin, no con el de Unfold. Unfold solo estiliza los formularios
que pasan por sus clases, así que estos dos quedaban con los widgets de serie
de Django — y Tailwind, que Unfold trae compilado, incluye un *reset* que deja
todo `input` con `border-width: 0` y fondo transparente.

El resultado era un formulario donde **los campos no se veían hasta pulsarlos**:
se leían las etiquetas, los textos de ayuda y los errores en rojo, pero las
cajas eran invisibles. Alguien que entra a crear la cuenta del administrador ve
«este campo es requerido» sin ver dónde escribir.

Es justo el formulario que hay que usar para dar de alta al administrador,
así que era el peor sitio posible para tener ese fallo.

La solución es la que documenta Unfold: volver a registrar los dos modelos
heredando a la vez del admin de Django —para no perder nada de lo suyo: el
hash de la contraseña, los permisos, el formulario de alta en dos pasos— y del
`ModelAdmin` de Unfold, que es lo que hace que los campos se dibujen.
"""
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as GroupAdminDeDjango
from django.contrib.auth.admin import UserAdmin as UserAdminDeDjango
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(UserAdminDeDjango, ModelAdmin):
    """El alta y la edición de cuentas, con los campos visibles.

    El orden de las clases base importa: primero el de Django, que trae el
    comportamiento, y después el de Unfold, que trae el aspecto. Al revés, los
    métodos de Django dejarían de encontrarse donde los busca el admin.

    Los tres formularios se sustituyen por los de Unfold porque son los que
    llevan sus widgets. Sin el de cambio de contraseña, esa pantalla se
    quedaría con el mismo problema que esto viene a arreglar.
    """

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(GroupAdminDeDjango, ModelAdmin):
    """Los grupos. Aquí es donde se mete a alguien en «Administradores»."""
