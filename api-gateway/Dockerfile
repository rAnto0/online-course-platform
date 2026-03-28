FROM krakend:2.13.2

COPY . /etc/krakend/

# Проверяем конфигурацию (опционально)
RUN FC_ENABLE=1 \
    FC_SETTINGS="/etc/krakend/config/settings" \
    FC_TEMPLATES="/etc/krakend/config/templates" \
    krakend check -t -d -c /etc/krakend/krakend.tmpl

EXPOSE 8080

# Запускаем с включённым flexible configuration
ENTRYPOINT FC_ENABLE=1 \
    FC_SETTINGS="/etc/krakend/config/settings" \
    FC_TEMPLATES="/etc/krakend/config/templates" \
    krakend run -c /etc/krakend/krakend.tmpl