import scrapy
import json
import re
from time import gmtime, strftime

class MedusaSpider(scrapy.Spider):
    name = "medusa"
    start_urls = ['https://www.medusashishashop.com/cachimbas/']

    def parse(self, response):
        yield {
            'name': 'Medusa',
            'logo': response.css('img.header-logo::attr(data-src)').get(),
            'lastUpdate':strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }
        marcas = response.css('div.product-category a::attr(href)').getall()
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
        precio = mainProduct.css(
            'span.woocommerce-Price-amount bdi::text')[0].get()
        divisa = mainProduct.css(
            'span.woocommerce-Price-amount bdi span::text')[0].get()
        imagen = mainProduct.css(
            '.woocommerce-product-gallery__image a::attr(href)').get()
        marca = mainProduct.css('.woocommerce-breadcrumb a::text')[-1].get()
        informacionUnidades = re.findall(
            "\d+", mainProduct.css('p.in-stock::text')[0].get())
        etiquetas = footerProduct.css(
            'div.woocommerce-Tabs-panel ul li::text').getall()
        cantidad = 0
        # significa que ha encontrado un numero en el string, hay pocas unidades
        if len(informacionUnidades) > 0:
            cantidad = int(informacionUnidades[0])
        elif len(informacionUnidades) == 0:
            cantidad = int(mainProduct.css(
                'div.quantity input.qty::attr(max)')[0].get())

        yield {
            'linkProducto': requestUrl,
            'titulo': titulo,
            'precioOriginal': precio,
            'precioRebajado': None,
            'divisa': divisa,
            'imagen': imagen,
            'marca': marca,
            'modelo': titulo.lower(),
            'agotado': False,
            'cantidad': cantidad,
            'categorias': ['cachimba'],
            'etiquetas': etiquetas}
