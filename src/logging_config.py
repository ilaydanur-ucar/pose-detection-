"""
Loglama yapılandırması — TEK YER (DRY).

Tüm loglama kurulumu (seviye, format, çıktı) burada yapılır. Başka hiçbir
dosya logger'ı yapılandırmaz; sadece logging.getLogger(__name__) ile kendi
logger'ını alır. Böylece format/seviye tek bir yerden değişir.

Kullanım (herhangi bir üst katman modülünde):
    import logging
    logger = logging.getLogger(__name__)
    ...
    logger.info("Squat tekrarı sayıldı: toplam %d", count)

Not: Saf katmanlar (src/geometry/, src/rules/) log YAZMAZ — bkz. CLAUDE.md.
"""
import logging


def setup_logging(level: int = logging.INFO) -> None:
    """
    Uygulama genelinde loglamayı bir kez kurar. main.py başında çağrılır.

    level: varsayılan INFO. Geliştirme sırasında ayrıntı görmek için
           logging.DEBUG geçilebilir (açı değerleri vb. görünür).
    """
    logging.basicConfig(
        level=level,
        # zaman | seviye | hangi modül | mesaj — hata çıkınca kaynağı belli olsun
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
