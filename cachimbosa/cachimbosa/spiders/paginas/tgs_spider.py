import scrapy
import json
from time import gmtime, strftime
import time
import unidecode
from utils import Utils


class TheGoodShishaSpider(scrapy.Spider):
    name = "tgs"
    URL_CACHIMBAS = 'https://www.thegoodshisha.com/product-category/shishas/'
    URL_CAZOLETAS = 'https://www.thegoodshisha.com/product-category/cazoletas/'
    URL_MELAZAS = "https://www.thegoodshisha.com/product-category/carbones/"
    URL_ACCESORIOS = "https://www.thegoodshisha.com/product-category/accesorios/"
    URL_CARBON = "https://www.thegoodshisha.com/product-category/melazas/"
    start_urls = [URL_CACHIMBAS, URL_CAZOLETAS,
                  URL_MELAZAS, URL_ACCESORIOS, URL_CARBON]
    itemFinal = {}
    allShishasParsed = []
    aplicadosMetadatos = False
    PAGINA_MAX = 100

    def parse(self, response):
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'TheGoodShisha',
                'logo': response.css('link[rel="icon"][sizes="192x192"]::attr(href)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }

        indexWhile = 1
        while indexWhile < self.PAGINA_MAX:
            peticionShishasPagina = None
            if indexWhile == 1:
                peticionShishasPagina = scrapy.Request(response.urljoin(
                    response.url), callback=self.obtainInfoFromProductCard, method="GET", headers={"User-Agent": "Mozilla/5.0"})
                peticionShishasPagina.cb_kwargs['typeItem'] = response.url
            else:
                peticionShishasPagina = scrapy.Request(response.urljoin(
                    response.url+"page/"+str(indexWhile)+"/"), callback=self.obtainInfoFromProductCard, method="GET", headers={"User-Agent": "Mozilla/5.0"})
                peticionShishasPagina.cb_kwargs['typeItem'] = response.url

            yield peticionShishasPagina
            indexWhile = indexWhile + 1

    def obtainInfoFromProductCard(self, response, typeItem):
        shishas = response.css('li.product')
        if(len(shishas) > 0):
            for shisha in shishas:
                enlace = shisha.css("a.woocommerce-LoopProduct-link")
                enlaceHref = enlace.css("::attr(href)").get()
                precios = shisha.css('span.woocommerce-Price-amount bdi::text')
                itemFinal = {
                    'linkProducto': enlaceHref,
                    'marca': Utils.flattenString(self, Utils.removeSpecificWordsFromString(self, enlaceHref.split("/")[-3].upper(), ['cachimba', 'shisha', typeItem])),
                    'modelo': Utils.flattenString(self, Utils.removeSpecificWordsFromString(self, enlaceHref.split("/")[-2].upper(), ['cachimba', 'shisha', typeItem])),
                    'imagen': enlace.css('img::attr(src)').get(),
                    'titulo': shisha.css('h2.woocommerce-loop-product__title::text').get(),
                    'divisa': shisha.css('span.woocommerce-Price-currencySymbol::text').get(),
                    'precioOriginal': precios[0].get(),
                    'precioRebajado': precios[1].get() if len(precios) > 1 else None,
                    'colores': [],
                    'fotos': [],
                    'specs': [{}],
                    'cantidad': None,
                    'tipo': self.obtainTypeDependingOnUrlScrapped(typeItem)
                }

                if enlaceHref is not None:
                    request = scrapy.Request(response.urljoin(
                        enlaceHref), callback=self.obtenerInfoProducto, method="GET", headers={"User-Agent": "Mozilla/5.0"})
                    request.cb_kwargs['itemFinal'] = itemFinal
                    yield request

    def obtenerInfoProducto(self, response, itemFinal):
        mainData = response.css('div.inside-article')
        estaFueraDeStock = mainData.css('p.out-of-stock')
        cart = mainData.css('form.cart')
        metadatosProducto = mainData.css('div.product_meta')

        if(len(estaFueraDeStock) > 0):
            itemFinal['agotado'] = True
        else:
            itemFinal['agotado'] = False

        itemFinal['shortDesc'] = ("".join(response.css(
            'div.woocommerce-Tabs-panel--description p:nth-of-type(1) *::text').getall()))
        itemFinal['categorias'] = metadatosProducto.css(
            'span.posted_in a[rel="tag"]::text').getall()
        itemFinal['etiquetas'] = metadatosProducto.css(
            'span.tagged_as a[rel="tag"]::text').getall()
        yield itemFinal

    def obtainTypeDependingOnUrlScrapped(self, url):
        if url == self.URL_CACHIMBAS:
            return "cachimba"
        elif url == self.URL_CAZOLETAS:
            return "cazoleta"
        elif url == self.URL_ACCESORIOS:
            return "accesorio"
        elif url == self.URL_CARBON:
            return "carbon"
        elif url == self.URL_MELAZAS:
            return "melaza"
