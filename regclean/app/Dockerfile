FROM python:3.6

# Setup for ssh 
RUN apt-get update && \
    apt-get install -y \
        openssh-server

RUN mkdir -p /root/.ssh
ADD id_rsa /root/.ssh/id_rsa
RUN	chmod 700 /root/.ssh && \
	chmod 600 /root/.ssh/id_rsa

ADD . /app
WORKDIR /app

RUN pip install flask gunicorn

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "regclean:app"]
