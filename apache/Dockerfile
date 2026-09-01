FROM httpd:2.4-alpine

# Apache 모듈 활성화
RUN sed -i 's/#LoadModule proxy_module/LoadModule proxy_module/g' /usr/local/apache2/conf/httpd.conf && \
    sed -i 's/#LoadModule proxy_http_module/LoadModule proxy_http_module/g' /usr/local/apache2/conf/httpd.conf && \
    sed -i 's/#LoadModule rewrite_module/LoadModule rewrite_module/g' /usr/local/apache2/conf/httpd.conf && \
    sed -i 's/#LoadModule headers_module/LoadModule headers_module/g' /usr/local/apache2/conf/httpd.conf

# Virtual host 설정 복사
COPY httpd-vhost.conf /usr/local/apache2/conf/extra/httpd-vhost.conf

# Virtual host 설정 포함
RUN echo 'Include /usr/local/apache2/conf/extra/httpd-vhost.conf' >> /usr/local/apache2/conf/httpd.conf
