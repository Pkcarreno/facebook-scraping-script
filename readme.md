# Facebook scraping script

Script para hacer scraping de las paginas publicas de Facebook.

## Motivo

Este script fue creado con le propósito de automatizar una tarea diaria.

Dicha tarea consistía en seleccionar de una pagina de Facebook, varios posts que cumplieran cierta condición al día y pegar ese contenido en el sitio web de la misma pagina.

La condición era que el post comenzara con una fecha siguiendo la estructura de: 

```tex
[dia del mes en curso] [nombre del mes en curso] [un año variable segun el contenido del post]
```

Entendiendo que el día y el mes era constante, este se uso como filtro de entre todos los post.

De cada post tenia que tomar:

- El año
- La descripción
- Y la imagen

Una vez obtenía da imagen debía a proceder a: 

- Añadir link interno a la descripción (del propio sitio web)
- Añadir link externo a la descripción (Mayormente Wikipedia)

Al tener todo lo anterior se procedía a publicar el contenido en el sitio web.

Dado a lo repetitivo de la tarea, me di a la tarea de crear un script para optimizar el tiempo que toma dicha tarea.

## Requisitos

### Versión de Python

- Python 3.9.6 o mayor.

### Datos externos

El Script necesita de información sobre la pagina que se desea hacer el scraping, para esto necesita un archivo llamado `data.json` en la misma ruta donde se encuentra el script, este archivo debe contener:

```json
{
    "facebook_url": "",
    "link": "",
    "append_data_with_band": "",
    "append_data_without_band": ""
}
```

`facebook_url`: dato obligatorio el cual debe contener el link incluyendo `https://` de la pagina de Facebook en cuestión.

`link`: se utiliza para incrustar un link interno en la descripción del posts, esto con el fin.

`append_data_with_band`: texto que se utiliza para añadir en conjunto al link interno.

`append_data_without_band`: texto que se utiliza para añadir en conjunto al link interno.

### Scraping desde archivo local

Para poder hacer scraping sin tener que buscar directamente en la pagina de Facebook, se puede hacer una copia del elemento `html` de la pagina en cuestión con la herramienta de desarrollo del navegador y pegando esta en un archivo llamado `html.txt` en la misma ruta donde se encuentra el script.

Esta es especialmente útil cuando se requiere de buscar post que no aparecen en la primera carga de la pagina, dado que el script no puede realizar "scroll" para cargar los demás post.

A esto hay que añadir que la condición propia del script solo me permite buscar hasta 4 días antes del día en curso, por la única razón que no me es necesario buscar en días anteriores a eso (esto es editable en el script)

**IMPORTANTE**: El script analiza la pagina desde la vista de escritorio sin estar logeado en la pagina, el script es susceptible a los cambios de estructura y/o diseño que pueda tener Facebook.

### Instalar dependencias

Para instalar las librerías ejecutar comando:

```powershell
pip install -r requirements.txt
```

Pd: este código fue desarrollado en Windows, no garantizo compatibilidad en otros sistemas.

## Ejecutar Script

**IMPORTANTE**: Es obligatorio tener el archivo `data.json`.

Para ejecutar el script se requiere ejecutar comando en la terminal en el directorio en que se encuentre el script:

```powershell
python .\webScraping.py
```
