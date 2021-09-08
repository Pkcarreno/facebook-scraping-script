# libraries
#
# system management
from __future__ import print_function, unicode_literals
from datetime import datetime
import os
import sys
from os.path import basename
import re
from pathlib import Path
import json
from termcolor import colored

#
# scrapping
from bs4 import BeautifulSoup
import requests
from mediawiki import MediaWiki

# import wikipedia

#
# terminal
from whaaaaat import prompt, print_json

# from whaaaaat import prompt
from whaaaaat import Validator, ValidationError

# get relevant data
f = open(
    "data.json",
)
data = json.load(f)

posts_url = data["facebook_url"]
append_data_with_name = data["append_data_with_band"]
append_data_without_name = data["append_data_without_band"]
append_data_without_name = append_data_without_name.encode("windows-1252").decode("utf-8")
add_link = data["link"]

wikipedia = MediaWiki()

# my own condition on selecting post
# it would match any post that began with string "(current day number) (current month)"
def post_condition():
    now = datetime.now()
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
    messsage = "{} {}".format(day, month)
    return messsage


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


class single_post:
    def __init__(self, description, date, img_url):
        self.description = description
        self.img_url = img_url
        self.date = date
        self.title = ""
        self.img_path = ""
        self.external_link = ""
        self.isValid = True
        self.inputs = inputs_form()

    def is_valid(self):
        print("Lo siguiente es un post valido? \n")
        print("Fecha: {}".format(self.date))
        print("Mensaje:")
        print(self.description)
        print()
        response = self.inputs.confirm("Este es un post valido?")
        if not response:
            self.isValid = False
        return response

    def get_title(self):
        class TitleValidator(Validator):
            def validate(self, document):
                less_than = len(document.text) < 16
                more_than = len(document.text) > 36
                if more_than:
                    raise ValidationError(
                        message="El titulo no puede contener mas de 36 caracteres, usted coloco {}.".format(
                            len(document.text)
                        ),
                        cursor_position=len(document.text),
                    )
                if less_than:
                    raise ValidationError(
                        message="El titulo debe contener mas de 16 caracteres, usted coloco {}.".format(
                            len(document.text)
                        ),
                        cursor_position=len(document.text),
                    )

        post_title = inputs.input_field("Titulo del post", TitleValidator)
        self.title = post_title

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

        inputs = inputs_form()
        band_name = inputs.input_field(
            "Nombre del artista o evento a reemplazar por el link externo",
            nameExternalLinkReplace,
        )
        is_author = inputs.confirm(
            "Este es el nombre de algún grupo, artista o evento destacado del rock?"
        )
        print()
        print("Por favor, espere un momento mientras se consulta a la Wikipedia...\n")
        link = False
        try:
            artist = wikipedia.search(band_name, results=3)
        except Exception:
            artist = None

        if len(artist) > 0:
            wiki_options = list()
            options = list()
            for page in artist:
                if not re.search("(disambiguation)", page):
                    try:
                        this_page_resume = wikipedia.summary(
                            page, auto_suggest=False, sentences=1
                        )
                        wiki_options.append([this_page_resume, page])
                        options.append(page)
                    except Exception:
                        pass
            for page in wiki_options:
                if not re.search("(disambiguation)", page[1]):
                    print("Entradas encontradas")
                    print("- {}".format(page[1]))
                    print("descripción: ", page[0])
                    print("---------------------")
            #
            options.append("Colocar el link")
            #
            wiki_option_selected = inputs.select(options, "Elija la opción correcta")
            if wiki_option_selected != "Colocar el link".lower():
                try:
                    wiki_url = wikipedia.page(
                        wiki_option_selected, auto_suggest=False
                    ).url
                    options2 = [
                        {
                            "key": "1",
                            "name": "{} - {}".format(band_name, wiki_url),
                            "value": wiki_url,
                        },
                        {"key": "0", "name": "Colocar el link", "value": False},
                    ]
                    link = inputs.expand(options2, "cual de estos links le funciona?")
                except Exception:
                    try:
                        newAttempt = wikipedia.search(band_name, results=3)
                        for index, name in enumerate(newAttempt):
                            if name.lower() == wiki_option_selected:
                                item_id = index
                        wiki_url = wikipedia.page(
                            newAttempt[item_id], auto_suggest=False
                        ).url
                        options2 = [
                            {
                                "key": "1",
                                "name": "{} - {}".format(band_name, wiki_url),
                                "value": wiki_url,
                            },
                            {"key": "0", "name": "Colocar el link", "value": False},
                        ]
                        link = inputs.expand(options2, "cual de estos links le funciona?")
                    except Exception:
                        print(
                            "Hubo un error al buscar la pagina de wikipedia, por favor ingrese el link manualmente\n"
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
            link = inputs.input_field("Colocar el link externo", validation)
        self.external_link = link
        self.description = self.description.replace(
            band_name, add_link.format(link, band_name), 1
        )
        if is_author:
            self.description = "".join(
                [
                    self.description,
                    append_data_with_name.format(band_name),
                ]
            )
        else:
            self.description = "".join([self.description, append_data_without_name])
        return True


class scrap_facebook_post:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"
        }
        self.posts = list()
        self.hasPost = False
        self.hasLinks = False
        self.hasImages = False
        self.hasPush = False
        requests.packages.urllib3.disable_warnings()  # turn off SSL warnings

    def get_all_post(self, url):
        print("Espere un momento mientras se busca contenido... \n")
        content = self.session.get(url, verify=False).content
        soup = BeautifulSoup(content, "lxml")
        posts_html = soup.find_all("div", class_="_427x")
        # inicia el procesado de la pagina
        for post in posts_html:
            try:
                new_content = post.find("div", {"data-testid": "post_message"})
                image = post.find("img", {"class": "scaledImageFitWidth img"})
                # comienza la busqueda de post que cumplan la condicion de iniciar con la fecha del dia
                if re.search(post_condition(), new_content.text.strip()):
                    # if re.search("29 Agosto", new_content.text.strip()):
                    print("Se encontró un post!")
                    # obtiene el texto sin la fecha
                    description = " ".join(new_content.text.strip().split(" ")[3:])
                    # obtiene el link de la imagen
                    lnk = image["src"]
                    # obtiene el año
                    numbers = []
                    for word in new_content.text.strip().split():
                        if word.isdigit():
                            numbers.append(int(word))
                    date = "{} {}".format(post_condition(), numbers[1])
                    # guarda objeto con datos del post
                    self.posts.append(single_post(description, date, lnk))
                    # informa
                    self.hasPost = True
            except Exception:
                print("Un Post Incompatible ")
        print(
            "\nHay unos {} posts que encajan con lo solicitado".format(
                self.posts_length()
            )
        )
        print()

    def set_posts_titles(self):
        if self.hasPost:
            inputs = inputs_form()
            if self.hasLinks:
                print("hay unos {} posts\n\n".format(self.posts_length()))
                # Inicia bucle de validacion de datos
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
                self.hasLinks = True
            else:
                while True:
                    posts_options = list()
                    for index, post in enumerate(self.posts):
                        if post.title != "":
                            posts_options.append(
                                {
                                    "key": index,
                                    "name": "Post sin titulo {}".format(index + 1),
                                    "value": index,
                                }
                            )
                        else:
                            posts_options.append(
                                {
                                    "key": index,
                                    "name": post.title,
                                    "value": index,
                                }
                            )
                    posts_options.append(
                        {
                            "key": 999999999,
                            "name": "Salir",
                            "value": "Salir",
                        }
                    )
                    post_selected = inputs.expand(
                        posts_options, "Seleccione el post que desea editar"
                    )
                    if post_selected != "Salir":
                        if self.posts[post_selected].is_valid():
                            self.posts[post_selected].get_title()
                            self.posts[post_selected].get_external_link()
                        print("---\n\n")
                    else:
                        break
        else:
            print("ERROR: Primero debe obtener los posts \n")

    def download_images(self):
        if self.hasLinks:
            print("Inicia Descarga de imágenes")
            print("Por favor espere...")
            print()
            for post in self.posts:
                if post.isValid:
                    # setting path
                    path = r"./imagenes_de_worpress"
                    # setting file name
                    file_extension = post.img_url.split("/")[-1].split("?")[0].split(".")
                    file_extension = file_extension[len(file_extension) - 1]
                    file_name = "".join(
                        [post.title.replace(" ", "-"), ".", file_extension]
                    )
                    file_name = file_name.replace('"', "")
                    # show data
                    # make path
                    local_filename = "".join([path, "\\", file_name])
                    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
                    # get image
                    with open(local_filename, "wb") as f:
                        print("Descargando ", file_name)
                        r = self.session.get(post.img_url, stream=True, verify=False)
                        total_length = r.headers.get("content-length")
                        dl = 0
                        total_length = int(total_length)
                        for chunk in r.iter_content(chunk_size=1024):
                            dl += len(chunk)
                            f.write(chunk)
                            done = int(50 * dl / total_length)
                            sys.stdout.write("\r[%s%s]" % ("█" * done, " " * (50 - done)))
                            sys.stdout.flush()
                    print("\n")
            print("Descarga completa")
            self.hasImages = True
        else:
            if not self.hasPost:
                print("ERROR: Primero debe obtener los posts \n")
            else:
                print("ERROR: Primero debe asignar y validar datos \n")

    def get_current_status(self):
        print("Lista de requisitos en el orden que se deben obtener")
        print(
            "1) Posts: ",
            colored(self.hasPost, "green")
            if self.hasPost
            else colored(self.hasPost, "red"),
        )
        print(
            "2) Títulos: ",
            colored(self.hasLinks, "green")
            if self.hasLinks
            else colored(self.hasLinks, "red"),
        )
        print(
            "3) Imágenes: ",
            colored(self.hasImages, "green")
            if self.hasImages
            else colored(self.hasImages, "red"),
        )
        print(
            "4) Push al servidor: ",
            colored(self.hasPush, "green")
            if self.hasPush
            else colored(self.hasPush, "red"),
        )
        print()
        print(
            "Numero de posts: {} \n".format(self.posts_length())
        ) if self.hasPost else "",

    def show_posts_details(self):
        if self.hasPost:
            for index, post in enumerate(self.posts):
                if post.isValid:
                    print("Post Numero {} \n".format((index + 1)))
                    print("Titulo: {}".format(post.title)) if self.hasLinks else "",
                    print("Fecha: {}".format(post.date))
                    print(
                        "URL externo: {}".format(post.external_link)
                    ) if self.hasLinks else "",
                    print(
                        "Dirección de la imagen guardada: {} \n".format(post.img_path)
                    ) if self.hasImages else print(),
                    print("Descripción:")
                    print(post.description)
                    print("---")
                    input()
                    print("\n \n")
        else:
            print("ERROR: Primero debe obtener los posts \n")

    def posts_length(self):
        len_posts = 0
        for post in self.posts:
            if post.isValid == True:
                len_posts += 1
        return len_posts


if __name__ == "__main__":
    options = [
        "Buscar Post en Facebook",
        "Asignar y validar datos",
        "Descargar imágenes",
        "Ver Detalles de los post",
        "Salir",
        "Post de prueba",
    ]
    scraper = scrap_facebook_post()
    while True:
        print("-------------------------- Inicio --------------------------\n")
        # clear()
        scraper.get_current_status()
        inputs = inputs_form()
        action = inputs.select(options, "Que acción desea realizar")
        print(
            "\n-------------------------- {} --------------------------\n".format(action)
        )
        if action == "Buscar Post en Facebook".lower():
            if not scraper.hasPost:
                scraper.get_all_post(posts_url)
            else:
                print("Nota: Usted ya posee Posts")
        elif action == "Asignar y validar datos".lower():
            if not scraper.hasLinks:
                scraper.set_posts_titles()
            else:
                print("Nota: Usted ya posee los Titulo")
        elif action == "Descargar imágenes".lower():
            if not scraper.hasImages:
                scraper.download_images()
            else:
                print("Nota: Usted ya posee las Imágenes")
        elif action == "Ver Detalles de los post".lower():
            scraper.show_posts_details()
        elif action == "Salir".lower():
            break
        elif action == "Post de prueba".lower():
            # post = single_post(
            #     "Esta es una descripción Fallece Holmes Sterling Morrison muy precisa de una banda como lo es Gun's N Roses que es muy muy buena claro que si nadie lo puede negar jejejeje lleilleilleii",
            #     "25 agosto 1998",
            #     "https://wikipedia.com",
            # )
            # post.get_title()
            # post.get_external_link()
            # print()
            # print("Titulo: {} \n".format(post.title))
            # print("Fecha: {} \n".format(post.date))
            # print("URL de la imagen: {} \n".format(post.date))
            # print("URL externo: {} \n".format(post.external_link))
            # print("Dirección de la imagen guardada: {} \n".format(post.img_path))
            # print("Descripción:")
            # print(post.description)
            # print("---")
            # print("\n \n")

            # print(wikipedia.search("Oasis", results=3))
            # # try:
            # for page in wikipedia.search("Oasis", results=3):
            #     if not re.search("(disambiguation)", page):
            #         print(wikipedia.summary(page, auto_suggest=False, sentences=1))

            # text = "Sterling Morrison"
            # newAttempt = wikipedia.search(text, results=3)
            # print(newAttempt)
            # # item_id = newAttempt.index(text)
            # for index, name in enumerate(newAttempt):
            #     if name.lower() == "sterling morrison":
            #         item_id = index
            # print(item_id)
            # wiki_url = wikipedia.page(newAttempt[item_id], auto_suggest=False).url
            # print(wiki_url)
            search = wikipedia.search("Alphaville", results=3)
            this_page_resume = list()
            indexes_list = list()
            for index, name in enumerate(search):
                try:
                    this_page_resume.append(
                        wikipedia.summary(name, auto_suggest=False, sentences=1)
                    )
                    indexes_list.append(index)
                except Exception:
                    pass
            print(search)
            print(this_page_resume)
            print(indexes_list)

        # --------- proceso de minado de texto
        # --------- subir a WordPress
        # get_external_link()
