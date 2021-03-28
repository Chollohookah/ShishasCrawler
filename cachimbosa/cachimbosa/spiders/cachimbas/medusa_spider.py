import scrapy
import json
import re
from time import gmtime, strftime
import unidecode


class MedusaSpider(scrapy.Spider):
    name = "medusa"
    start_urls = ['https://www.medusashishashop.com/cachimbas/']

    def parse(self, response):
        yield {
            'name': 'Medusa',
            'logo': response.css('img.header-logo::attr(data-src)').get(),
            'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }
        marcas = response.css(
            'a[href*="https://www.medusashishashop.com/cachimbas/"]::attr(href)').getall()
        for marcaLink in marcas:
            peticionShishas = scrapy.Request(response.urljoin(
                marcaLink), callback=self.obtenerShishas)
            yield peticionShishas

    def obtenerShishas(self, response):
        shishas = response.css('div.col-inner > a::attr(href)').getall()

        if(len(shishas) > 0):
            for shisha in shishas:
                peticionProducto = scrapy.Request(response.urljoin(
                    shisha), callback=self.obtenerShishaDetalle)
                peticionProducto.cb_kwargs['requestUrl'] = shisha
                yield peticionProducto

    def obtenerShishaDetalle(self, response, requestUrl):
        mainProduct = response.css('div.product-main')
        footerProduct = response.css('div.product-footer')
        titulo = mainProduct.css('h1.product-title::text')[0].get()

        precioRebajadoNode = mainProduct.css('p.price-on-sale')
        precioRebajado = None
        precio = None

        if(len(precioRebajadoNode) > 0):
            precio = mainProduct.css(
                'p.price-on-sale del span bdi::text').get()
            precioRebajado = mainProduct.css(
                'p.price-on-sale ins span bdi::text').get()
        else:
            precio = mainProduct.css(
                'span.woocommerce-Price-amount bdi::text')[0].get()

        divisa = mainProduct.css(
            'span.woocommerce-Price-amount bdi span::text')[0].get()
        imagen = mainProduct.css(
            '.woocommerce-product-gallery__image a::attr(href)').get()
        marca = response.css(
            'nav.woocommerce-breadcrumb a::text').getall()[-1].lower()

        informacionUnidades = []
        if len(mainProduct.css('p.in-stock::text')) > 0:
            informacionUnidades = re.findall(
                "\d+", mainProduct.css('p.in-stock::text')[0].get())

        etiquetas = footerProduct.css(
            'div.woocommerce-Tabs-panel ul li::text').getall()
        cantidad = 0
        # significa que ha encontrado un numero en el string, hay pocas unidades
        if len(informacionUnidades) > 0:
            cantidad = int(informacionUnidades[0])
        elif len(informacionUnidades) == 0:
            if len(mainProduct.css('div.quantity input.qty::attr(max)')) > 0:
                cantidad = int(mainProduct.css(
                    'div.quantity input.qty::attr(max)')[0].get())

        yield {
            'linkProducto': requestUrl,
            'titulo': titulo.strip(),
            'shortDesc': "".join(response.css('div.product-short-description p:nth-child(1) *::text').getall()),
            'precioOriginal': precio,
            'precioRebajado': precioRebajado,
            'divisa': divisa,
            'imagen': imagen,
            'tipo':'cachimba'
            'marca': self.flattenString(self.removeSpecificWordsFromString(marca.lower(), ['cachimba', 'shisha'])).strip(),
            'modelo': self.flattenString(self.removeSpecificWordsFromString(titulo.lower(), ['cachimba', 'shisha'] + marca.split())).strip(),
            'agotado': False,
            'cantidad': cantidad,
            'categorias': ['cachimba'],
            'etiquetas': etiquetas}

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