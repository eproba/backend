###########
# BUILDER #
###########

# pull official base image
FROM python:3.12-alpine AS builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apk update && \
    apk add gcc

#
RUN pip install --upgrade pip

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM python:3.12-alpine

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# install dependencies
RUN apk update && \
    apk add weasyprint fontconfig font-roboto dcron postgresql-client

# copy wheels from the builder stage
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# copy project files
COPY . $APP_HOME

# ensure entrypoint.sh has UNIX line endings
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.sh

# add execute permissions to entrypoint.sh
RUN chmod +x  $APP_HOME/entrypoint.sh

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# create cron log directory
RUN mkdir /var/log/cron && chown -R app:app /var/log/cron

# copy the cron file (to define the cron jobs)
COPY ./crontab /etc/crontabs/app

# make sure cron job file has appropriate permissions
RUN chmod 0644 /etc/crontabs/app

# expose port 8000
EXPOSE 8000

# start cron in the background and gunicorn as the main process
CMD ["sh", "-c", "crond -b && su -s /bin/ash app -c \"/home/app/web/entrypoint.sh\""]
