# -*- coding: utf-8 -*-
"""Las cuentas del panel: una pregunta en vez de cuarenta casillas.

DOS PROBLEMAS, UNO DETRÁS DE OTRO
---------------------------------
**Los campos no se veían.** `auth.User` y `auth.Group` los registra Django con
su propio admin, no con el de Unfold, y Unfold solo estiliza los formularios
que pasan por sus clases. Esos dos quedaban con los widgets de serie — y
Tailwind, que Unfold trae compilado, incluye un *reset* que deja todo `input`
con `border-width: 0` y fondo transparente. El formulario de alta se leía
entero salvo por las cajas donde había que escribir.

**Y dar permisos era inhumano.** El selector de Django enseña los cuarenta y
tantos permisos del proyecto, uno por modelo y acción, para que quien crea una
cuenta los combine bien de memoria. Aquí los papeles son dos y están definidos,
así que la pregunta correcta no es «¿qué permisos?» sino **«¿qué es esta
persona?»**.

LO QUE SE PIERDE, Y SE PIERDE A SABIENDAS
-----------------------------------------
El grano fino. Si algún día hace falta alguien que cargue preguntas pero no vea
las métricas, con esto hay que tocar código: habría que volver a los grupos. Se
eligió así porque los papeles son dos, y un formulario que pregunta lo que de
verdad se decide vale más que uno que lo puede todo y no lo usa nadie.
"""
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as GroupAdminDeDjango
from django.contrib.auth.admin import UserAdmin as UserAdminDeDjango
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .roles import GRUPO_ADMIN

# Django registra estos dos con su propio admin al arrancar; hay que soltarlos
# antes de volver a registrarlos con el de Unfold.
admin.site.unregister(User)
admin.site.unregister(Group)

PAPEL_SUPER = "super"
PAPEL_ADMIN = "admin"
PAPEL_NINGUNO = "ninguno"

PAPELES = [
    (PAPEL_ADMIN, "Administrador — gestiona el banco de preguntas y consulta las "
                  "métricas. No borra contenido ni toca las cuentas."),
    (PAPEL_SUPER, "Superadministrador — todo, incluidas las cuentas del panel y "
                  "el borrado."),
    (PAPEL_NINGUNO, "Sin acceso al panel — la cuenta existe pero no puede entrar."),
]


def papel_de(usuario) -> str:
    if usuario.is_superuser:
        return PAPEL_SUPER
    if usuario.is_staff:
        return PAPEL_ADMIN
    return PAPEL_NINGUNO


class MezclaDePapel(forms.ModelForm):
    """Añade la pregunta del papel y deduce de ella las casillas de Django.

    `is_staff`, `is_superuser` y la pertenencia al grupo dejan de pedirse: son
    consecuencia de la respuesta, no tres decisiones sueltas que haya que
    combinar sin equivocarse.
    """

    papel = forms.ChoiceField(
        choices=PAPELES,
        widget=forms.RadioSelect,
        label="Qué puede hacer",
        help_text="De esto salen los permisos. No hace falta tocar nada más.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["papel"].initial = papel_de(self.instance)
        else:
            self.fields["papel"].initial = PAPEL_ADMIN


class FormularioDeAlta(MezclaDePapel, UserCreationForm):
    pass


class FormularioDeEdicion(MezclaDePapel, UserChangeForm):
    pass


@admin.register(User)
class UserAdmin(UserAdminDeDjango, ModelAdmin):
    """El alta y la edición de cuentas.

    El orden de las clases base importa: primero el de Django, que trae el
    comportamiento —el hash de la contraseña, el alta en dos pasos—, y después
    el de Unfold, que trae el aspecto.
    """

    form = FormularioDeEdicion
    add_form = FormularioDeAlta
    change_password_form = AdminPasswordChangeForm

    list_display = ["username", "email", "primer_nombre", "que_puede_hacer", "is_active"]
    list_filter = ["is_active", "is_superuser", "is_staff"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos de la persona", {"fields": ("first_name", "last_name", "email")}),
        ("Acceso al panel", {
            "fields": ("papel", "is_active"),
            "description": "Una cuenta inactiva no puede entrar aunque tenga papel.",
        }),
        ("Fechas", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "papel"),
        }),
    )

    @admin.display(description="Nombre")
    def primer_nombre(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Qué puede hacer")
    def que_puede_hacer(self, obj):
        return dict(PAPELES)[papel_de(obj)].split(" — ")[0]

    def save_model(self, request, obj, form, change):
        """Traduce el papel a las casillas de Django y al grupo.

        **Nadie se quita a sí mismo el acceso.** Es la única forma de dejar el
        panel sin ningún superadministrador y sin manera de volver a entrar
        desde la interfaz: a partir de ahí haría falta la consola del servidor.
        Se avisa y se deja como estaba, en vez de obedecer y dejar a alguien
        fuera de su propio panel.
        """
        from django.contrib import messages

        papel = form.cleaned_data.get("papel")

        if papel and change and obj.pk == request.user.pk and papel != papel_de(request.user):
            messages.warning(
                request,
                "No puedes cambiar tu propio papel desde aquí: si te quitas el "
                "acceso, no habría forma de recuperarlo sin entrar al servidor. "
                "Pídeselo a otro superadministrador.",
            )
            papel = None

        if papel:
            obj.is_superuser = papel == PAPEL_SUPER
            obj.is_staff = papel in (PAPEL_ADMIN, PAPEL_SUPER)

        super().save_model(request, obj, form, change)

        if papel:
            grupo, _ = Group.objects.get_or_create(name=GRUPO_ADMIN)
            if papel == PAPEL_ADMIN:
                obj.groups.add(grupo)
            else:
                # El superadministrador no necesita el grupo: sus permisos no
                # salen de ahi. Dejarselo puesto solo confundiria al leerlo.
                obj.groups.remove(grupo)


@admin.register(Group)
class GroupAdmin(GroupAdminDeDjango, ModelAdmin):
    """Los grupos.

    Se dejan accesibles aunque el formulario de usuario ya no los pida: son la
    puerta de salida si algun dia hacen falta mas de dos papeles, y ahi los
    permisos se leen ya en español.
    """
