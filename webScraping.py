# -*- coding: utf-8 -*-
#
from __future__ import print_function, unicode_literals
from datetime import datetime, timedelta
import os
import sys
import re
import json
import math
from termcolor import colored

# scraping y llamadas a API's
from bs4 import BeautifulSoup
import requests
from mediawiki import MediaWiki

# formularios
from whaaaaat import prompt
from whaaaaat import Validator, ValidationError

# Obtener datos de conexión y relevancia
try:
    with open("./data.json", "r") as json_data:
        data = json.load(json_data)
        posts_url = data["facebook_url"]
        if "append_data_with_band" in data:
            append_data_with_name = data["append_data_with_band"]
        else:
            append_data_with_name = ""
        if "append_data_without_band" in data:
            print()
            append_data_without_name = data["append_data_without_band"]
            append_data_without_name = append_data_without_name.encode(
                "windows-1252"
            ).decode("utf-8")
        else:
            append_data_without_name = ""
        if "link" in data:
            add_link = data["link"]
        else:
            add_link = ""
except Exception:
    print("-------------------------- Error --------------------------\n")
    print(
        'Usted no posee archivo de datos "data.json" en el directorio, consulte el readme en la sección de <<Requisitos - Datos externos>> para mas información.'
    )
    sys.exit()


# condición propia para filtrar los posts
# este caso especifico verifica si el posts comienza con una fecha (día del mes, mes)
def post_condition(isToday=True):
    now = datetime.now()
    # Meses en español
    months = (
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    )
    day = now.day
    month = months[now.month - 1]
    # En caso de pasar como parámetro "True" se entiende que la función debe retornar
    # la condición de la fecha de hoy,
    # en caso contrario, este establece la fecha de los anteriores 4 días y le pregunta al usuario
    # que fecha desea seleccionar en la condición de búsqueda.
    if isToday:
        messsage = ["{} {}".format(day, month), "{} de {}".format(day, month)]
    else:
        dateOfPastDays = [
            now - timedelta(days=1),
            now - timedelta(days=2),
            now - timedelta(days=3),
            now - timedelta(days=4),
        ]
        day = [
            day,
            dateOfPastDays[0].day,
            dateOfPastDays[1].day,
            dateOfPastDays[2].day,
            dateOfPastDays[3].day,
        ]
        month = [
            month,
            months[dateOfPastDays[0].month - 1],
            months[dateOfPastDays[1].month - 1],
            months[dateOfPastDays[2].month - 1],
            months[dateOfPastDays[3].month - 1],
        ]
        messsage = [
            ["{} {}".format(day[0], month[0]), "{} de {}".format(day[0], month[0])],
            ["{} {}".format(day[1], month[1]), "{} de {}".format(day[1], month[1])],
            ["{} {}".format(day[2], month[2]), "{} de {}".format(day[2], month[2])],
            ["{} {}".format(day[3], month[3]), "{} de {}".format(day[3], month[3])],
            ["{} {}".format(day[4], month[4]), "{} de {}".format(day[4], month[4])],
        ]
    return messsage


# Esta clase compone de los inputs que se usan a lo largo de la ejecución
class inputs_form:
    def __init__(self):
        super().__init__()

    def input_field(self, message, validation):
        input_question = [
            {
                "type": "input",
                "name": "search",
                "message": message,
                "validate": validation,
            }
        ]
        answers = prompt(input_question)
        return answers["search"]

    def confirm(self, message):
        questions = [
            {
                "type": "confirm",
                "name": "it_pass",
                "message": message,
                "default": True,
            }
        ]
        answers = prompt(questions)
        return answers["it_pass"]

    def expand(self, options, message):
        expand_from_search = [
            {
                "type": "expand",
                "name": "links",
                "message": message,
                "choices": options,
            },
        ]
        answers = prompt(expand_from_search)
        return answers["links"]

    def select(self, options, text):
        select_from_search = [
            {
                "type": "list",
                "name": "Opciones",
                "message": text,
                "choices": options,
                "filter": lambda val: val.lower(),
            },
        ]
        answers = prompt(select_from_search)
        return answers["Opciones"]


# clase que se usa para guardar y dar forma a los posts que se obtienen
# de facebook y contiene los métodos que se encargan de modificar esos datos.
class single_post:
    def __init__(self, description, date, img_url):
        self.description = description
        self.originalDescription = description
        self.img_url = img_url
        self.date = date
        self.title = ""
        self.img_path = ""
        self.external_link = ""
        self.is_valid = True
        self.inputs = inputs_form()
        self.has_image = False

    # soporte de equivalencias
    def __eq__(self, other):
        if not isinstance(other, single_post):
            return NotImplemented

        return (
            self.img_url == other.img_url
            and self.originalDescription == other.originalDescription
            and self.date == other.date
        )

    # verifica si el post cumple con los requisitos
    def is_valid(self):
        print("Lo incoming es un post valido? \n")
        print("Fecha: {}".format(self.date))
        print("Mensaje:")
        print(self.description)
        print()
        response = self.inputs.confirm("Este es un post valido?")
        if response:
            self.is_valid = True
        else:
            self.is_valid = False
        return response

    # le da titulo al post, el cual se vale para descargar la imagen
    def get_title(self):
        class TitleValidator(Validator):
            def validate(self, document):
                less_than = len(document.text) < 16
                more_than = len(document.text) > 36
                if more_than:
                    raise ValidationError(
                        message="El titulo no puede contener mas de 36 caracteres, usted escribió {}.".format(
                            len(document.text)
                        ),
                        cursor_position=len(document.text),
                    )
                if less_than:
                    raise ValidationError(
                        message="El titulo debe contener mas de 16 caracteres, usted escribió {}.".format(
                            len(document.text)
                        ),
                        cursor_position=len(document.text),
                    )

        post_title = self.inputs.input_field("Titulo del post", TitleValidator)
        self.title = post_title

    # busca un link externo en Wikipedia para añadir al post final
    def get_external_link(self):
        validation_description = self.description

        class nameExternalLinkReplace(Validator):
            def validate(self, document):
                if len(document.text) > 0:
                    ok = re.search(document.text, validation_description)
                else:
                    ok = False
                if not ok:
                    raise ValidationError(
                        message='Error: "{}" no se contempla en la descripción, por favor vuelva a intentar'.format(
                            document.text
                        ),
                        cursor_position=len(document.text),
                    )

        is_equal = self.inputs.confirm("El texto a reemplazar y el autor coinciden?")
        text_ro_replace = self.inputs.input_field(
            "Nombre del artista o evento a reemplazar en la descripción por el link externo",
            nameExternalLinkReplace,
        )
        if not is_equal:
            wikipedia_search = self.inputs.input_field(
                "Artista o evento a buscar en Wikipedia", None
            )
        is_author = self.inputs.confirm(
            "Este es el nombre de algún grupo o artista destacado del rock?"
        )
        print()
        print("Por favor, espere un momento mientras se consulta a la Wikipedia...\n")
        link = False
        try:
            wikipedia = MediaWiki()
            artist = wikipedia.search(
                wikipedia_search if not is_equal else text_ro_replace, results=3
            )
        except Exception:
            artist = None

        if artist and len(artist) > 0:
            wiki_options = list()
            options = list()
            key = "123"
            for index, page in enumerate(artist):
                if not re.search("(disambiguation)", page):
                    try:
                        this_page_resume = wikipedia.summary(
                            page, auto_suggest=False, sentences=1
                        )
                        wiki_options.append([this_page_resume, page])
                        options.append(
                            {
                                "key": key[index],
                                "name": page,
                                "value": index,
                            }
                        )
                    except Exception:
                        pass
            for page in wiki_options:
                if not re.search("(disambiguation)", page[1]):
                    print("Entradas encontradas")
                    print("- {}".format(page[1]))
                    print("descripción: ", page[0])
                    print("---------------------")
            #
            options.append(
                {
                    "key": "0",
                    "name": "Colocar el link",
                    "value": "Colocar el link",
                }
            )
            #
            wiki_option_selected = self.inputs.expand(options, "Elija la opción correcta")
            if wiki_option_selected != "Colocar el link".lower():
                try:
                    wiki_url = wikipedia.page(
                        artist[wiki_option_selected], auto_suggest=False
                    ).url
                    options2 = [
                        {
                            "key": "1",
                            "name": "{} - {}".format(text_ro_replace, wiki_url),
                            "value": wiki_url,
                        },
                        {"key": "0", "name": "Colocar el link", "value": False},
                    ]
                    link = self.inputs.expand(
                        options2, "cual de estos links le funciona?"
                    )
                except Exception:
                    print(
                        "Hubo un error al buscar la pagina de Wikipedia, por favor ingrese el link manualmente\n"
                    )
        if not link:

            class UrlValidator(Validator):
                def validate(self, document):
                    url_pattern = "https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
                    ok = re.search(
                        url_pattern,
                        document.text,
                    )
                    if not ok:
                        raise ValidationError(
                            message="Por favor, introduce un URL seguro valido",
                            cursor_position=len(document.text),
                        )

            validation = UrlValidator
            link = self.inputs.input_field("Colocar el link externo", validation)
        self.external_link = link
        newDescription = self.originalDescription.replace(
            text_ro_replace, add_link.format(link, text_ro_replace), 1
        )
        if is_author:
            self.description = "".join(
                [
                    newDescription,
                    append_data_with_name.format(text_ro_replace),
                ]
            )
        else:
            self.description = "".join([newDescription, append_data_without_name])
        return True


# esta clase se encarga de gestionar el scraping
# y la creación de la colección de posts
class scraping_facebook_post:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"
        }
        self.posts = list()
        self.has_post = False
        self.has_links = False
        self.has_images = False
        self.has_push = False
        requests.packages.urllib3.disable_warnings()  # turn off SSL warnings

    # busca en la pagina de facebook cuya dirección se obtiene
    # del archivo "data.json" o, se toma del archivo "html.txt"
    # añadido manualmente.
    def get_all_post(self, url):
        inputs = inputs_form()
        try:
            while True:
                search_on_internet = inputs.confirm(
                    "Desea buscar los posts por internet?"
                )
                if not search_on_internet:
                    try:

                        last_modification = datetime.fromtimestamp(
                            os.path.getmtime("./html.txt")
                        ).strftime("%d-%m-%Y %H:%M:%S")
                        confirm_last_modification = inputs.confirm(
                            "Este archivo fue modificado por ultima vez el {}, esta seguro?".format(
                                last_modification
                            )
                        )
                        if confirm_last_modification:
                            f = open("./html.txt", "r", encoding="utf8")
                            content = f.read()
                            if inputs.confirm("Desea usar la fecha de hoy?"):
                                todayCondition = post_condition()
                            else:
                                dayOptions = post_condition(False)
                                options = [
                                    dayOptions[0][1],
                                    dayOptions[1][1],
                                    dayOptions[2][1],
                                    dayOptions[3][1],
                                    dayOptions[4][1],
                                ]
                                selectedDay = inputs.select(
                                    options, "Que fecha desea buscar?"
                                )
                                for day in dayOptions:
                                    if selectedDay == day[1].lower():
                                        todayCondition = day
                            break
                    except Exception:
                        print(
                            'El archivo "html.txt" no existe, consulte el readme en la sección de <<Requisitos - Scraping desde archivo local>> para mas información.'
                        )
                else:
                    print("Espere un momento mientras se busca contenido... \n")
                    content = self.session.get(url, verify=False).content
                    todayCondition = post_condition()
                    break
            soup = BeautifulSoup(content, "lxml")
            posts_html = soup.find_all("div", class_="_427x")
            # inicia el procesado de la pagina
            for post in posts_html:
                try:
                    new_content = post.find("div", {"data-testid": "post_message"})
                    image = post.find("img", {"class": "scaledImageFitWidth img"})
                    condition = re.search(
                        todayCondition[0], new_content.text.strip()
                    ) or re.search(todayCondition[1], new_content.text.strip())
                    # comienza la búsqueda de post que cumplan la condición de iniciar con la fecha del día
                    if condition:
                        # obtiene el texto sin la fecha
                        description = " ".join(new_content.text.strip().split(" ")[3:])
                        # obtiene el link de la imagen
                        lnk = image["src"]
                        # obtiene el año
                        numbers = []
                        for word in new_content.text.strip().split():
                            if word.isdigit():
                                numbers.append(int(word))
                        date = "{} {}".format(todayCondition[0], numbers[1])
                        # guarda objeto con datos del post
                        new_post = single_post(description, date, lnk)
                        is_repeated = any(x == new_post for x in self.posts)
                        if not is_repeated:
                            print("Se encontró un post!")
                            self.posts.append(new_post)
                        # informa
                        else:
                            print("Un Post Repetido")
                        self.has_post = True
                except Exception:
                    print("Un Post Incompatible ")
            print(
                "\nHay unos {} posts que encajan con lo solicitado\n".format(
                    self.posts_length()
                )
            )
        except Exception:
            print("Hubo un error de conexión, por favor vuelva a intentar\n")

    # valida, asigna y edita información de cada post.
    def set_posts_data(self):
        if self.has_post:
            inputs = inputs_form()
            if not self.has_links:
                print("hay unos {} posts\n\n".format(self.posts_length()))
                # Inicia bucle de validación de datos
                for index, post in enumerate(self.posts):
                    print(
                        "Post numero {}, {} restantes \n".format(
                            (index + 1), (self.posts_length() - (index + 1))
                        )
                    )
                    if post.is_valid():
                        post.get_title()
                        post.get_external_link()
                    print("---\n\n")
                self.has_links = True
            else:
                key = "123456789"
                previous = 0
                incoming = 0
                if len(self.posts) > 9:
                    incoming = math.ceil(len(self.posts) / 9)
                first_value = 0
                last_value = 9 if len(self.posts) > 9 else len(self.posts)

                while True:
                    posts_options = list()
                    limited_posts = self.posts[first_value:last_value]
                    for index, post in enumerate(limited_posts):
                        if post.title == "":
                            posts_options.append(
                                {
                                    "key": key[index],
                                    "name": "Post sin titulo {}".format(index + 1),
                                    "value": index,
                                }
                            )
                        else:
                            posts_options.append(
                                {
                                    "key": key[index],
                                    "name": post.title,
                                    "value": index,
                                }
                            )
                    if previous > 0:
                        posts_options.append(
                            {
                                "key": "a",
                                "name": "previous",
                                "value": "previous",
                            }
                        )
                    if incoming > 0 and incoming < len(limited_posts):
                        posts_options.append(
                            {
                                "key": "s",
                                "name": "incoming",
                                "value": "incoming",
                            }
                        )
                    posts_options.append(
                        {
                            "key": "0",
                            "name": "Salir",
                            "value": "Salir",
                        }
                    )
                    post_selected = inputs.expand(
                        posts_options, "Seleccione el post que desea editar"
                    )
                    if post_selected == "Salir":
                        break
                    elif post_selected == "previous":
                        first_value -= 9
                        last_value -= 9
                        incoming += 1
                        previous -= 1
                    elif post_selected == "incoming":
                        first_value += 9
                        last_value += 9
                        incoming -= 1
                        previous += 1
                    else:
                        if self.posts[post_selected].is_valid():
                            self.posts[post_selected].get_title()
                            self.posts[post_selected].get_external_link()
                        print("---\n\n")
        else:
            print("ERROR: Primero debe obtener los posts \n")

    # descarga las imágenes de los posts.
    def download_images(self):
        if self.has_links:
            print("Inicia Descarga de imágenes")
            print("Por favor espere...")
            print()
            for post in self.posts:
                if post.is_valid:
                    # configura la ruta
                    path = r"./imágenes_de_posts"
                    # configura el nombre del archivo
                    file_extension = post.img_url.split("/")[-1].split("?")[0].split(".")
                    file_extension = file_extension[len(file_extension) - 1]
                    file_name = "".join(
                        [
                            post.title.replace(" ", "-").replace("/", "-"),
                            ".",
                            file_extension,
                        ]
                    )
                    file_name = file_name.replace('"', "")
                    # crea la ruta
                    local_filename = "".join([path, "\\", file_name])
                    file_exists = os.path.isfile(local_filename)
                    # valida si el archivo existe
                    if not file_exists:
                        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
                        # obtiene la imagen
                        with open(local_filename, "wb") as f:
                            print("En Descarga {}".format(file_name))
                            r = self.session.get(post.img_url, stream=True, verify=False)
                            total_length = r.headers.get("content-length")
                            dl = 0
                            total_length = int(total_length)
                            for chunk in r.iter_content(chunk_size=1024):
                                dl += len(chunk)
                                f.write(chunk)
                                done = int(50 * dl / total_length)
                                sys.stdout.write(
                                    "\r[%s%s]" % ("█" * done, " " * (50 - done))
                                )
                                sys.stdout.flush()
                        print("\n")
                    else:
                        print('"{}" ya existe \n'.format(file_name))
            print("Descarga completa")
            self.has_images = True
        else:
            if not self.has_post:
                print("ERROR: Primero debe obtener los posts \n")
            else:
                print("ERROR: Primero debe asignar y validar datos \n")

    # muestra en pantalla el estatus actual de la aplicación
    def get_current_status(self):
        print("Hoy es {}".format(post_condition()[1]))
        print()
        print("Lista de requisitos en el orden que se deben obtener")
        print(
            "1) Posts: ",
            colored(self.has_post, "green")
            if self.has_post
            else colored(self.has_post, "red"),
        )
        print(
            "2) Títulos: ",
            colored(self.has_links, "green")
            if self.has_links
            else colored(self.has_links, "red"),
        )
        print(
            "3) Imágenes: ",
            colored(self.has_images, "green")
            if self.has_images
            else colored(self.has_images, "red"),
        )
        # Aquí se complementaba una etapa para hacer push, sin embargo aun se
        # encuentra en desarrollo esta parte
        # print(
        #     "4) Push al servidor: ",
        #     colored(self.has_push, "green")
        #     if self.has_push
        #     else colored(self.has_push, "red"),
        # )
        print()
        print(
            "Numero de posts: {} \n".format(self.posts_length())
        ) if self.has_post else "",

    # muestra los detalles de cada post validado
    def show_posts_details(self):
        if self.has_post:
            for index, post in enumerate(self.posts):
                if post.is_valid:
                    print("Post Numero {} \n".format((index + 1)))
                    print("Titulo: {}".format(post.title)) if self.has_links else "",
                    print("Fecha: {}".format(post.date))
                    print(
                        "URL externo: {}".format(post.external_link)
                    ) if self.has_links else "",
                    print(
                        "Dirección de la imagen guardada: {} \n".format(post.img_path)
                    ) if self.has_images else print(),
                    print()
                    print(post.description)
                    print("---")
                    input()
                    print("\n \n")
        else:
            print("ERROR: Primero debe obtener los posts \n")

    # devuelve el numero de posts actual
    def posts_length(self):
        len_posts = 0
        for post in self.posts:
            if post.is_valid:
                len_posts += 1
        return len_posts


# menu principal de la aplicación
if __name__ == "__main__":
    options = [
        "Buscar Post en Facebook",
        "Asignar y validar datos",
        "Descargar imágenes",
        "Ver Detalles de los post",
        "Salir",
        # "Post de prueba",
    ]
    # inicializa clase de scraping de facebook
    scraper = scraping_facebook_post()
    # inicializa clase de inputs
    inputs = inputs_form()
    # comienza interfaz de trabajo
    while True:
        print("-------------------------- Inicio --------------------------\n")
        scraper.get_current_status()
        action = inputs.select(options, "Que acción desea realizar")
        print(
            "\n-------------------------- {} --------------------------\n".format(action)
        )
        if action == "Buscar Post en Facebook".lower():
            scraper.get_all_post(posts_url)
        elif action == "Asignar y validar datos".lower():
            scraper.set_posts_data()
        elif action == "Descargar imágenes".lower():
            scraper.download_images()
        elif action == "Ver Detalles de los post".lower():
            scraper.show_posts_details()
        elif action == "Salir".lower():
            break
