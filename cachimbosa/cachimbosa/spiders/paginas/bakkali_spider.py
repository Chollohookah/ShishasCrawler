import scrapy
import json
import re
import unidecode
from time import gmtime, strftime


class Bakkali(scrapy.Spider):
    name = "bakkali"

    PAGINA_MAX = 100
    URL_CACHIMBAS = 'https://bakkalistore.es/cachimbas/'
    URL_CAZOLETAS = 'https://bakkalistore.es/cazoletas/'
    URL_ACCESORIOS = 'https://bakkalistore.es/accesorios/'
    URL_CONSUMIBLES = 'https://bakkalistore.es/consumibles/'
    URL_BASES = 'https://bakkalistore.es/bases/'

    start_urls = [URL_CACHIMBAS, URL_CAZOLETAS,
                  URL_ACCESORIOS, URL_CONSUMIBLES, URL_BASES]

    metadatosObtenidos = False
    errorRequest = False
    executingPagesRequests = False

    def parse(self, response):
        if self.metadatosObtenidos == False:
            yield {
                'name': 'Bakkali',
                'logo': response.css('div#desktop_logo a img::attr(src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }
            self.metadatosObtenidos = True

        indexWhile = 1

        while indexWhile < self.PAGINA_MAX:
            if indexWhile == 1:
                peticionPaginaProducto = scrapy.Request(response.urljoin(
                    response.url), callback=self.executeDescRequest)
                peticionPaginaProducto.cb_kwargs['typeItem'] = response.url
            else:
                peticionPaginaProducto = scrapy.Request(response.urljoin(
                    response.url+'?page='+str(indexWhile)+'/'), callback=self.executeDescRequest)
                peticionPaginaProducto.cb_kwargs['typeItem'] = response.url

            yield peticionPaginaProducto
            indexWhile = indexWhile + 1

    def executeDescRequest(self, response, typeItem):
        productos = list(set(response.css(
            'article.product-miniature div.thumbnail-container a::attr(href)').getall()))
        # print('\n \n Productos: ' + str(len(productos)) + '\n \n')
        if(len(productos) > 0):
            for producto in productos:
                peticionProducto = scrapy.Request(response.urljoin(
                    producto), callback=self.obtenerDetalleProducto)
                peticionProducto.cb_kwargs['requestUrl'] = producto
                peticionProducto.cb_kwargs['typeItem'] = self.obtainTypeDependingOnUrlScrapped(
                    typeItem)
                yield peticionProducto

    def obtainTypeDependingOnUrlScrapped(self, url):
        if url == self.URL_CACHIMBAS:
            return "cachimba"
        elif url == self.URL_CAZOLETAS:
            return "cazoleta"
        elif url == self.URL_ACCESORIOS:
            return "accesorio"
        elif url == self.URL_CONSUMIBLES:
            return "consumible"
        elif url == self.URL_BASES:
            return "base"

    def obtenerDetalleProducto(self, response, requestUrl, typeItem):
        infoProducto = response.css('div.product-info-row')
        titulo = infoProducto.css('.page-title span::text').get()

        # PRECIOS
        # En caso de que haya ofertas se diferencian con las siguientes clases
        precioNuevo = infoProducto.css(
            'span.current-price span::attr(content)').get()

        precioMayorACero = infoProducto.css('span.regular-price::text').get()

        precioRegular = precioMayorACero if precioMayorACero else '0,00€'

        precioOriginal = None
        precioRebajado = None

        if precioNuevo and precioRegular:

            if len(precioNuevo) > 0 and len(precioRegular) > 0:
                precioOriginal = precioRegular.replace(
                    '€', '').replace('\u00a0', '')
                precioRebajado = precioNuevo.replace('€', '')
        else:
            precioOriginal = precioNuevo.replace('€', '')
            precioRebajado = None

        # FOTOS
        fotos = infoProducto.css(
            'div.product-images img.js-thumb::attr(src)').getall()

        # SHORT DESC
        shortDesc = response.css(
            'meta[name="description"]::attr(content)').get()

        # DIVISA
        if precioRegular:
            divisa = (precioRegular if len(
                precioRegular) > 0 else precioOriginal)[-1]
        else:
            divisa = '0,00'
        # IMAGEN
        imagen = response.css(
            'meta[property="og:image"]::attr(content)').get()

        # MARCA
        marca_sin_modificar = response.css(
            'meta[itemprop="brand"]::attr(content)').get()

        # TODO: Hay algunas que no tienen el meta brand, hay que pensar una alternativa
        marca = self.flattenString(self.removeSpecificWordsFromString(response.css(
            'meta[itemprop="brand"]::attr(content)').get().upper(), ['cachimba', 'shisha'])) if marca_sin_modificar else typeItem

        # TODO: Por qué se juntan todas las palabras del modelo??
        # MODELO
        modelo = self.flattenString(self.removeSpecificWordsFromString(
            titulo.lower(), ['cachimba']+marca.lower().split())).strip()

        # PRODUCTO AGOTADO
        wrapper_nodo = response.css('#product-availability::text').getall()
        agotado = False
        if any('Fuera de stock' in s for s in wrapper_nodo):
            agotado = True

        # agotado = True if (contenido.css(
        #   '#product-availability::text').get()) is None else False

        # CANTIDAD
        cantidad = 0

        # CATEGORIAS
        categorias = [typeItem]

        # ETIQUETAS
        etiquetas = ''

        # TIPO
        tipo = typeItem

        yield {
            'linkProducto': requestUrl,
            'titulo': titulo,
            'shortDesc': shortDesc,
            'precioOriginal': precioOriginal,
            'precioRebajado': precioRebajado,
            'divisa': divisa,
            'imagen': imagen,
            'tipo': tipo,
            'fotos': fotos,
            'marca': marca,
            'modelo': modelo,
            'agotado': agotado,
            'cantidad': cantidad,
            'categorias': categorias,
            'etiquetas': etiquetas
        }

    def removeSpecificWordsFromString(self, string, wordsToDelete):
        if string is not None:
            edit_string_as_list = string.lower().split()
            final_list = [
                word for word in edit_string_as_list if word not in wordsToDelete]
            final_string = ' '.join(final_list)
            return final_string
        else:
            return ""

    def flattenString(self, string):
        string = string.upper()
        string = string.replace(".", " ")
        string = string.replace(",", " ")
        string = string.replace("-", " ")
        string = string.replace(" ", "")
        string = string.strip()
        string = unidecode.unidecode(string)
        return string
