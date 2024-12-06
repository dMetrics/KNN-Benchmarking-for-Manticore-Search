FROM manticoresearch/manticore:6.2.12
ARG CPUTYPE
ENV CPUTYPE=${CPUTYPE}
RUN apt update && apt-get -y install wget
RUN wget https://repo.manticoresearch.com/repository/manticoresearch_bionic/dists/bionic/main/binary-${CPUTYPE}/manticore-columnar-lib_2.2.4-230822-5aec342_${CPUTYPE}.deb -O /tmp/manticore-columnar.deb
RUN dpkg -i /tmp/manticore-columnar.deb

