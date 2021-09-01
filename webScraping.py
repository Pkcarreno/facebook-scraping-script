# libraries
#
# system management
from __future__ import print_function, unicode_literals
from datetime import datetime
import os
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

    def expand(self, options):
        expand_from_search = [
            {
                "type": "expand",
                "name": "links",
                "message": "cual de estos links le funciona?",
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
        artist = wikipedia.search(band_name, results=3)
        link = False
        if len(artist) > 0:
            wiki_options = list()
            options = list()
            for page in artist:
                if not re.search("(disambiguation)", page):
                    this_page_resume = wikipedia.summary(
                        page, auto_suggest=False, sentences=1
                    )
                    wiki_options.append(this_page_resume)
                    options.append(page)
            for index, page in enumerate(artist):
                if not re.search("(disambiguation)", page):
                    print("Entradas encontradas")
                    print("- {}".format(page))
                    print("descripción: ", wiki_options[index])
                    print("---------------------")
            #
            options.append("Colocar el link")
            #
            wiki_option_selected = inputs.select(options, "Elija la opción correcta")
            print(wiki_option_selected)
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
                    link = inputs.expand(options2)
                except:
                    try:
                        print("Espere un poco mas por favor...")
                        newAttempt = wikipedia.search(band_name, results=3)
                        item_id = newAttempt.index(wiki_option_selected)
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
                        link = inputs.expand(options2)
                    except:
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
        print("\nHay unos {} posts que encajan con lo solicitado".format(len(self.posts)))
        print()

    def set_posts_titles(self):
        if self.hasPost:
            print("hay unos {} posts\n\n".format(len(self.posts)))
            # Inicia bucle de validacion de datos
            for index, post in enumerate(self.posts):
                print(
                    "Post numero {}, {} restantes \n".format(
                        (index + 1), (len(self.posts) - (index + 1))
                    )
                )
                print("Lo siguiente es un post valido? /n")
                print("Fecha: {}".format(post.date))
                print("Mensaje:")
                print(post.description)
                print()
                inputs = inputs_form()
                if inputs.confirm("Este es un post valido?"):
                    post.get_title()
                    post.get_external_link()
                else:
                    self.posts.remove(post)
                print("---\n\n")
            self.hasLinks = True
        else:
            print("ERROR: Primero debe obtener los posts \n")

    def download_images(self):
        if self.hasLinks:
            print("Inicia Descarga de imágenes")
            print("Por favor espere...")
            print()
            for post in self.posts:
                # setting path
                path = r"./imagenes_de_worpress"
                # setting file name
                file_extension = post.img_url.split("/")[-1].split("?")[0].split(".")
                file_extension = file_extension[len(file_extension) - 1]
                file_name = "".join([post.title.replace(" ", "-"), ".", file_extension])
                file_name = file_name.replace('"', "")
                # show data
                print("path: ", path)
                print("file_extension: ", file_extension)
                print("file_name: ", file_name)
                # make path
                local_filename = "".join([path, "\\", file_name])
                os.makedirs(os.path.dirname(local_filename), exist_ok=True)
                # Path(local_filename).mkdir(parents=True, exist_ok=True)
                print("ruta: ", local_filename)
                # get image
                r = self.session.get(post.img_url, stream=True, verify=False)
                with open(local_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        f.write(chunk)
                post.img_path = local_filename
                print("---")
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
        print("Numero de posts: {} \n".format(len(self.posts))) if self.hasPost else "",

    def show_posts_details(self):
        if self.hasPost:
            for index, post in enumerate(self.posts):
                print("Post Numero {} \n".format((index + 1)))
                print("Titulo: {} \n".format(post.title)) if self.hasLinks else "",
                print("Fecha: {} \n".format(post.date))
                print("URL de la imagen: {} \n".format(post.date))
                print(
                    "URL externo: {} \n".format(post.external_link)
                ) if self.hasLinks else "",
                print(
                    "Dirección de la imagen guardada: {} \n".format(post.img_path)
                ) if self.hasImages else "",
                print("Descripción:")
                print(post.description)
                print("---")
                print("\n \n")
        else:
            print("ERROR: Primero debe obtener los posts \n")


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
            text = "Sterling Morrison"
            newAttempt = wikipedia.search(text, results=3)
            print(newAttempt)
            item_id = newAttempt.index(text)
            print(item_id)
            wiki_url = wikipedia.page(newAttempt[item_id], auto_suggest=False).url
            print(wiki_url)

        # --------- proceso de minado de texto
        # --------- subir a WordPress
        # get_external_link()
