import scrapy
import json
from time import gmtime, strftime

class ZuloShishasPider(scrapy.Spider):
    name = 'zulo'
    start_urls = ['https://www.zuloshishas.es/cachimbas-3']
    aplicadosMetadatos = False

    def parse(self, response):
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'ZuloShishas',
                'logo': response.css('a#header_logo img.logo::attr(src)').get(),
                'lastUpdate':strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }
        contenedorProducto = response.css('div.product-container')
        loopInfo = {
            'actualIndex': 0,
            'total': len(contenedorProducto)
        }
        self.nextPageClass = response.css(
            'li#pagination_next_bottom::attr(class)')
        self.nextPageElement = response.css(
            'li#pagination_next_bottom a::attr(href)')
        for shisha in contenedorProducto:

            linkProducto = shisha.css('a.product_img_link::attr(href)').get()
            itemFinal = {
                'linkProducto': linkProducto
            }
            request = scrapy.Request(response.urljoin(
                linkProducto), callback=self.obtenerInfoProducto)
            request.cb_kwargs['itemFinal'] = itemFinal
            request.cb_kwargs['loopInfo'] = loopInfo
            yield request

    def obtenerInfoProducto(self, response, itemFinal, loopInfo):
        contenidoPrincipal = response.css('div.main_content_area')
        hayStock = self.hayStock(
            contenidoPrincipal.css('div#oosHook::attr(style)'))
        precioOriginal = contenidoPrincipal.css(
            'span#our_price_display::text').get()
        precioRebajado = contenidoPrincipal.css(
            ' p#old_price:not(.hidden) span#old_price_display::text')
        itemFinal['titulo'] = contenidoPrincipal.css('h1.heading::text').get()
        itemFinal['modelo'] = contenidoPrincipal.css('h1.heading::text').get()
        itemFinal['marca'] = contenidoPrincipal.css(
            'a#product_manufacturer_logo meta::attr(content)').get()
        itemFinal['imagen'] = contenidoPrincipal.css(
            'img#bigpic::attr(src)').get()
        itemFinal['divisa'] = precioOriginal.split(" ")[-1]
        itemFinal['precioOriginal'] = precioOriginal.split(" ")[-2] if len(
            precioRebajado) == 0 else precioRebajado.get().split(" ")[-2]
        itemFinal['precioRebajado'] = precioOriginal.split(" ")[-2] if len(
            precioRebajado) > 0 else None
        itemFinal['agotado'] = not hayStock
        itemFinal['cantidad'] = None
        itemFinal['categorias'] = 'cachimba',
        itemFinal['etiquetas'] = contenidoPrincipal.css(
            'div#idTab211 div.pa_content a::text').getall()
        yield itemFinal

        if loopInfo['actualIndex'] == (loopInfo['total'] - 1):
            if self.haySiguiente(self.nextPageClass):
                print(self.nextPageElement.get())
                request = scrapy.Request(response.urljoin(
                    self.nextPageElement.get()), callback=self.parse)
                yield request

        loopInfo['actualIndex'] += 1

    def hayStock(self, seleccionOOSstyle):
        style = seleccionOOSstyle.get()
        if style == "" or style == None or len(style) == 0:
            return False
        return True

    def haySiguiente(self, botonSiguienteClass):
        if "disabled" in botonSiguienteClass.get().split(" "):
            return False
        return True
