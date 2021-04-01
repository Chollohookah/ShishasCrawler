import scrapy
import json
import re
from time import gmtime, strftime
import unidecode


class MedusaSpider(scrapy.Spider):
    name = "medusa"
    metadata_set = False

    PAGINA_MAX = 100
    URL_CACHIMBAS = 'https://www.medusashishashop.com/cachimbas/'
    URL_CAZOLETAS = 'https://www.medusashishashop.com/cazoletas-para-cachimbas/'
    URL_MANGUERAS = "https://www.medusashishashop.com/mangueras-para-cachimbas/"
    URL_ACCESORIOS = "https://www.medusashishashop.com/accesorios-para-cachimbas/"
    URL_CARBON = "https://www.medusashishashop.com/carbon-para-cachimba/"

    start_urls = [URL_CAZOLETAS, URL_CACHIMBAS,
                  URL_MANGUERAS, URL_ACCESORIOS, URL_CARBON]

    def parse(self, response):
        if self.metadata_set == False:
            yield {
                'name': 'Medusa',
                'logo': response.css('img.header-logo::attr(data-src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }
            self.metadata_set = True

        indexWhile = 1
        while indexWhile < self.PAGINA_MAX:
            peticionShishasPagina = None
            if indexWhile == 1:
                peticionShishasPagina = scrapy.Request(response.urljoin(
                    response.url), callback=self.executeDescRequest)
                peticionShishasPagina.cb_kwargs['typeItem'] = response.url
            else:
                peticionShishasPagina = scrapy.Request(response.urljoin(
                    response.url+"page/"+str(indexWhile)+"/"), callback=self.executeDescRequest)
                peticionShishasPagina.cb_kwargs['typeItem'] = response.url

            yield peticionShishasPagina
            indexWhile = indexWhile + 1

    def executeDescRequest(self, response, typeItem):
        itemsUnicos = list(
            set(response.css('div.products div.col-inner a::attr(href)').getall()))
        if(len(itemsUnicos) > 0):
            for item in itemsUnicos:
                peticionShishas = scrapy.Request(response.urljoin(
                    item), callback=self.obtenerShishaDetalle)
                peticionShishas.cb_kwargs['requestUrl'] = item
                peticionShishas.cb_kwargs['typeItem'] = self.obtainTypeDependingOnUrlScrapped(
                    typeItem)
                yield peticionShishas

    def obtainTypeDependingOnUrlScrapped(self, url):
        if url == self.URL_CACHIMBAS:
            return "cachimba"
        elif url == self.URL_CAZOLETAS:
            return "cazoleta"
        elif url == self.URL_ACCESORIOS:
            return "accesorio"
        elif url == self.URL_CARBON:
            return "carbon"
        elif url == self.URL_MANGUERAS:
            return "manguera"

    def obtenerShishaDetalle(self, response, requestUrl, typeItem):
        if("cart" is not response.url):
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
                'tipo': typeItem,
                'specs': [{}],
                'colores': [],
                'fotos': mainProduct.css('.product-thumbnails div.col a img::attr(data-src)').getall(),
                'marca': self.flattenString(self.removeSpecificWordsFromString(marca.lower(), ['cachimba', 'shisha', typeItem])).strip(),
                'modelo': self.flattenString(self.removeSpecificWordsFromString(titulo.lower(), ['cachimba', 'shisha', typeItem] + marca.split())).strip(),
                'agotado': False,
                'cantidad': cantidad,
                'categorias': [typeItem],
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
