import scrapy
import json
import re
import unidecode
from time import gmtime, strftime
from utils import Utils


class HispaCachimbas(scrapy.Spider):
    name = 'hispacachimba1'

    PAGINA_MAX = 100
    URL_CACHIMBAS = 'https://www.hispacachimba.es/cachimbas/'
    URL_CAZOLETAS = 'https://www.hispacachimba.es/cazoletas/'
    URL_MANGUERAS = 'https://www.hispacachimba.es/mangueras/'
    URL_ACCESORIOS = 'https://www.hispacachimba.es/accesorios/'
    URL_CARBON = 'https://www.hispacachimba.es/carbones/'

    start_urls = [URL_CAZOLETAS, URL_CACHIMBAS,
                  URL_MANGUERAS, URL_ACCESORIOS, URL_CARBON]

    metadatosObtenidos = False
    errorRequest = False
    executingPagesRequests = False

    def parse(self, response):
        if self.metadatosObtenidos == False:
            yield {
                'name': 'Hispacachimbaa',
                'logo': response.css('div#logo a img::attr(src)').get(),
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
                    response.url+'page/'+str(indexWhile)+'/'), callback=self.executeDescRequest)
                peticionPaginaProducto.cb_kwargs['typeItem'] = response.url

            yield peticionPaginaProducto
            indexWhile = indexWhile + 1

    def executeDescRequest(self, response, typeItem):
        productos = list(set(response.css(
            'div.main-products div.product-layout div.product-thumb div.image a::attr(href)').getall()))
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
        elif url == self.URL_CARBON:
            return "carbon"
        elif url == self.URL_MANGUERAS:
            return "manguera"

    def obtenerDetalleProducto(self, response, requestUrl, typeItem):
        contenido = response.css('div#content')
        titulo = contenido.css('.page-title::text').get()

        # PRECIOS
        # En caso de que haya ofertas se diferencian con las siguientes clases
        precioViejo = contenido.css("#product div.product-price-old::text")
        precioNuevo = contenido.css("#product div.product-price-new::text")
        precioRegular = contenido.css('.price-group .product-price::text')

        precioOriginal = None
        precioRebajado = None
        if len(precioNuevo) > 0 and len(precioViejo) > 0:
            precioOriginal = precioViejo.get()[:-1]
            precioRebajado = precioNuevo.get()[:-1]
        else:
            precioOriginal = precioRegular.get()[: -1]
            precioRebajado = None

        # FOTOS
        fotosSinParsear = response.css(
            'meta[property="og:image"]::attr(content)').getall()

        for fotoSinParsear in fotosSinParsear:
            fotoSinParsear = re.sub(
                "((0|[1-9][0-9]*)x(0|[1-9][0-9]*))\w+", "1050x1200", fotoSinParsear)

        fotos = fotoSinParsear

        # SHORT DESC
        shortDesc = response.css(
            'meta[name="description"]::attr(content)').get()

        # DIVISA
        divisa = (precioRegular if len(
            precioRegular) > 0 else precioNuevo).get()[-1]

        # IMAGEN
        imagen = response.css(
            'meta[name="twitter:image"]::attr(content)').get()

        # MARCA
        # TODO Pensar otra manera de pillar la marca, esta a veces falla porque no todas las url tienen 6 "/"
        splittedUrl = response.css(
            'meta[property="og:image"]::attr(content)').get().split("/")

        indiceCatalog = splittedUrl.index("catalog")

        marca = Utils.flattenString(self, Utils.removeSpecificWordsFromString(
            self, splittedUrl[(indiceCatalog + 1)].upper(), ['cachimba', 'shisha']))

        # MODELO
        modelo = Utils.flattenString(self, Utils.removeSpecificWordsFromString(self,
                                                                               titulo.lower(), ['cachimba']+marca.lower().split())).strip()

        # PRODUCTO AGOTADO
        agotado = True if (contenido.css(
            'd#product .in-stock span::text').get()) is None else False

        # CANTIDAD
        cantidad = 0

        # CATEGORIAS
        categorias = [typeItem]

        # ETIQUETAS
        etiquetas = contenido.css('.tags a::text').getall()

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
